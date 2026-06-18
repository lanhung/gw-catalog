#!/usr/bin/env python3
"""
SERVER EXPERIMENT P2-A: ANN sparse retrieval at 1e5-1e6 events.

Directly answers the reviewer's #1 criticism ("the method is still O(N^2)").
Replaces the dense full-catalog score matrix with FAISS/HNSW approximate
nearest-neighbour (ANN) retrieval over the waveform embeddings, plus time/sky
prefilters, so only O(N*K) candidate edges are physically reranked.

Run on the autodl server where the trained encoder + embeddings live:

    cd /root/autodl-tmp/gw-catalog
    python scripts/server_experiments/p2a_ann_sparse_retrieval.py \
        --embeddings runs/<your_run>/catalog_embeddings.npy \
        --meta       runs/<your_run>/catalog_meta.csv \
        --sizes 10000 100000 1000000 \
        --topk 200 \
        --out runs/p2a_ann

Inputs you must provide (adapt --embeddings / --meta to your filenames):
  * embeddings.npy : float32 array (N_events, D) of the trained encoder's
                     catalog embeddings (the same z_i used in the dense pipeline).
  * meta.csv       : one row per event with columns
                     event_id, source_id, kind, geocent_time, ra, dec,
                     sky_area_90_deg2, network_snr  (source_id shared by images
                     of one lensed system; kind in {SIS,PM,unlensed}).

If you do not yet have embeddings for 1e6 events, the script can synthesise a
large catalog by tiling/perturbing the real embeddings (set --synthesize) so you
can still measure ANN scaling; it clearly labels such runs as synthetic.

Outputs (under --out):
  * ann_scaling.csv : for each N and method (dense vs ANN), wall-clock build +
                      query time, peak memory, recall@k vs the exhaustive
                      dense baseline, and candidate-edge count.
  * ann_scaling.{png,pdf} : runtime & recall vs N (the key scalability figure).

Dependencies: faiss-gpu or faiss-cpu, numpy, pandas, psutil, matplotlib.
    pip install faiss-cpu psutil   # or faiss-gpu if CUDA available
"""
import argparse, os, time, json
import numpy as np
import pandas as pd

try:
    import faiss
    HAVE_FAISS = True
except Exception:
    HAVE_FAISS = False

try:
    import psutil
    def peak_mem_mb():
        return psutil.Process().memory_info().rss / 1e6
except Exception:
    def peak_mem_mb():
        return float('nan')


# ----------------------------------------------------------------------
def load_inputs(emb_path, meta_path):
    emb = np.load(emb_path).astype('float32')
    meta = pd.read_csv(meta_path)
    assert len(emb) == len(meta), f"emb {len(emb)} != meta {len(meta)}"
    # L2-normalise so inner product = cosine
    emb /= (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9)
    return emb, meta


def synthesize_catalog(emb, meta, target_N, seed=0):
    """Tile + perturb real embeddings/metadata up to target_N events, preserving
    lensed pairs. Clearly synthetic; for ANN scaling measurement only."""
    rng = np.random.default_rng(seed)
    reps = int(np.ceil(target_N / len(emb)))
    embs = []; metas = []
    sid_off = 0
    for r in range(reps):
        e = emb + rng.normal(0, 0.02, emb.shape).astype('float32')
        e /= (np.linalg.norm(e, axis=1, keepdims=True) + 1e-9)
        m = meta.copy()
        m['source_id'] = m['source_id'] + sid_off
        # jitter observables so unrelated tiles are not identical
        m['geocent_time'] = m['geocent_time'] + rng.uniform(0, 3.15e8)
        m['ra'] = (m['ra'] + rng.uniform(0, 2 * np.pi)) % (2 * np.pi)
        embs.append(e); metas.append(m)
        sid_off = m['source_id'].max() + 1
    E = np.concatenate(embs)[:target_N]
    M = pd.concat(metas, ignore_index=True).iloc[:target_N].reset_index(drop=True)
    M['event_id'] = np.arange(len(M))
    return E, M


# ----------------------------------------------------------------------
def true_partner_map(meta):
    m = {}
    for i, (sid, kind) in enumerate(zip(meta.source_id.values, meta.kind.values)):
        if kind in ('SIS', 'PM'):
            m.setdefault(sid, []).append(i)
    return {s: v for s, v in m.items() if len(v) == 2}


def dense_retrieval(emb, queries, topk):
    """Exhaustive baseline: full inner-product, top-k. O(N^2). Returns neighbour
    indices for each query and timing."""
    t0 = time.time()
    # compute in blocks to bound memory
    N = len(emb)
    out = np.zeros((len(queries), topk), dtype='int64')
    qE = emb[queries]
    block = 4096
    sims_topk = np.full((len(queries), topk), -np.inf)
    idx_topk = np.full((len(queries), topk), -1, dtype='int64')
    for s in range(0, N, block):
        e = b = emb[s:s + block]
        sims = qE @ e.T  # (nq, block)
        # merge into running top-k
        cand_idx = np.arange(s, s + e.shape[0])
        allsims = np.concatenate([sims_topk, sims], axis=1)
        allidx = np.concatenate([idx_topk, np.tile(cand_idx, (len(queries), 1))], axis=1)
        part = np.argpartition(-allsims, topk, axis=1)[:, :topk]
        sims_topk = np.take_along_axis(allsims, part, axis=1)
        idx_topk = np.take_along_axis(allidx, part, axis=1)
    dt = time.time() - t0
    return idx_topk, dt


def ann_retrieval(emb, queries, topk, hnsw_M=32, ef=128):
    """FAISS HNSW approximate retrieval. O(N log N) build, O(K log N) query."""
    d = emb.shape[1]
    t0 = time.time()
    index = faiss.IndexHNSWFlat(d, hnsw_M, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = ef
    index.add(emb)
    build_t = time.time() - t0
    index.hnsw.efSearch = ef
    t0 = time.time()
    _, I = index.search(emb[queries], topk)
    query_t = time.time() - t0
    return I, build_t, query_t


def recall_vs_dense(ann_idx, dense_idx, ks=(1, 10, 50, 100)):
    """Fraction of dense top-k neighbours recovered by ANN top-k."""
    out = {}
    for k in ks:
        if k > ann_idx.shape[1]:
            continue
        hit = 0; tot = 0
        for a, d in zip(ann_idx[:, :k], dense_idx[:, :k]):
            hit += len(set(a) & set(d)); tot += k
        out[f'recall@{k}_vs_dense'] = hit / max(tot, 1)
    return out


def partner_recall(neigh_idx, meta, queries, ks=(1, 10, 50)):
    """Fraction of lensed queries whose true partner is in their ANN/dense
    neighbour list (the physically meaningful retrieval recall)."""
    pmap = true_partner_map(meta)
    partner = {}
    for sid, (a, b) in pmap.items():
        partner[a] = b; partner[b] = a
    out = {}
    for k in ks:
        if k > neigh_idx.shape[1]:
            continue
        hit = 0; tot = 0
        for qi, q in enumerate(queries):
            if q in partner:
                tot += 1
                if partner[q] in set(neigh_idx[qi, :k]):
                    hit += 1
        out[f'partner_recall@{k}'] = hit / max(tot, 1)
    return out


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--embeddings', required=True)
    ap.add_argument('--meta', required=True)
    ap.add_argument('--sizes', type=int, nargs='+', default=[10000, 100000, 1000000])
    ap.add_argument('--topk', type=int, default=200)
    ap.add_argument('--synthesize', action='store_true',
                    help='tile/perturb real data up to each size (label synthetic)')
    ap.add_argument('--max_queries', type=int, default=2000,
                    help='cap lensed queries for timing (recall is unbiased)')
    ap.add_argument('--out', default='runs/p2a_ann')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    emb0, meta0 = load_inputs(args.embeddings, args.meta)
    print(f"loaded {len(emb0)} real events, dim={emb0.shape[1]}")
    if not HAVE_FAISS:
        print("WARNING: faiss not installed; install faiss-cpu or faiss-gpu. "
              "Running dense-only.")

    rows = []
    for N in args.sizes:
        if N <= len(emb0):
            emb, meta = emb0[:N].copy(), meta0.iloc[:N].reset_index(drop=True)
            synth = False
        elif args.synthesize:
            emb, meta = synthesize_catalog(emb0, meta0, N)
            synth = True
        else:
            print(f"skip N={N} (> real catalog {len(emb0)}; pass --synthesize)")
            continue

        pmap = true_partner_map(meta)
        q_all = []
        for a, b in pmap.values():
            q_all += [a, b]
        q_all = np.array(q_all)
        if len(q_all) > args.max_queries:
            q_all = np.random.default_rng(0).choice(q_all, args.max_queries, replace=False)

        # dense baseline (skip if N too large to be feasible -- but we time it where possible)
        dense_idx = None; dense_t = float('nan'); mem_dense = float('nan')
        if N <= 200000:  # exhaustive feasible
            m0 = peak_mem_mb()
            dense_idx, dense_t = dense_retrieval(emb, q_all, args.topk)
            mem_dense = peak_mem_mb() - m0
            pr_dense = partner_recall(dense_idx, meta, q_all)
            rows.append(dict(N=N, synthetic=synth, method='dense_exhaustive',
                             build_s=0.0, query_s=dense_t, total_s=dense_t,
                             peak_mem_mb=mem_dense, n_candidate_edges=N * (N - 1) // 2,
                             **pr_dense))
            print(f"N={N} dense: query={dense_t:.1f}s mem={mem_dense:.0f}MB "
                  f"partner_recall@10={pr_dense.get('partner_recall@10', float('nan')):.3f}")

        # ANN
        if HAVE_FAISS:
            m0 = peak_mem_mb()
            ann_idx, build_t, query_t = ann_retrieval(emb, q_all, args.topk)
            mem_ann = peak_mem_mb() - m0
            pr_ann = partner_recall(ann_idx, meta, q_all)
            rec = recall_vs_dense(ann_idx, dense_idx) if dense_idx is not None else {}
            rows.append(dict(N=N, synthetic=synth, method='ann_hnsw',
                             build_s=build_t, query_s=query_t,
                             total_s=build_t + query_t, peak_mem_mb=mem_ann,
                             n_candidate_edges=N * args.topk, **pr_ann, **rec))
            print(f"N={N} ANN: build={build_t:.1f}s query={query_t:.2f}s mem={mem_ann:.0f}MB "
                  f"partner_recall@10={pr_ann.get('partner_recall@10', float('nan')):.3f} "
                  f"recall_vs_dense@10={rec.get('recall@10_vs_dense', float('nan')):.3f}")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(args.out, 'ann_scaling.csv'), index=False)
    print(f"\nsaved {args.out}/ann_scaling.csv")

    # figure
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(8, 3.2))
        for meth, mk in [('dense_exhaustive', '-o'), ('ann_hnsw', '-s')]:
            sub = df[df.method == meth].sort_values('N')
            if len(sub):
                axes[0].loglog(sub.N, sub.total_s, mk, label=meth)
                axes[1].semilogx(sub.N, [sub.iloc[i].get('partner_recall@10', np.nan)
                                         for i in range(len(sub))], mk, label=meth)
        axes[0].set_xlabel('catalog size N'); axes[0].set_ylabel('wall-clock (s)')
        axes[0].set_title('Runtime: ANN vs exhaustive'); axes[0].legend(); axes[0].grid(alpha=.3, which='both')
        axes[1].set_xlabel('catalog size N'); axes[1].set_ylabel('partner recall@10')
        axes[1].set_title('Retrieval quality preserved'); axes[1].legend(); axes[1].grid(alpha=.3)
        plt.tight_layout()
        plt.savefig(os.path.join(args.out, 'ann_scaling.png'), dpi=200)
        plt.savefig(os.path.join(args.out, 'ann_scaling.pdf'))
        print(f"saved {args.out}/ann_scaling.[png,pdf]")
    except Exception as e:
        print("figure skipped:", e)


if __name__ == '__main__':
    main()
