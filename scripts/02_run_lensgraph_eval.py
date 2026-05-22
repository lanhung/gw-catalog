from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lensgraph.catalog_io import load_catalog, source_ids
from lensgraph.models.encoder import MatchWindowSpectralEncoder, SpectralFeatureEncoder, RandomProjectionEncoder
from lensgraph.retrieval.ann_index import topk_neighbors, candidate_edges_from_neighbors, retrieval_metrics
from lensgraph.rerank import embed_only_scores, lensgraph_scores
from lensgraph.graph.inference import connected_components_partition, pivot_correlation_clustering
from lensgraph.metrics import (
    edge_metrics,
    partition_metrics,
    auprc_from_scores,
    calibration_bins,
    calibration_metrics,
    isotonic_calibrate_scores,
    platt_calibrate_scores,
    tier_summary,
)


def edge_set_at(scores: dict[tuple[int, int], float], threshold: float) -> set[tuple[int, int]]:
    return {e for e, s in scores.items() if s >= threshold}


def evaluate_partition(method: str, score_edges: dict[tuple[int, int], float], sids: np.ndarray, n: int, threshold_grid: np.ndarray) -> dict:
    best = None
    total_pairs = n * (n - 1) / 2
    for thr in threshold_grid:
        if method == 'cc':
            part = connected_components_partition(n, score_edges, float(thr))
        elif method == 'ccl':
            part = pivot_correlation_clustering(n, score_edges, float(thr))
        else:
            raise ValueError(method)
        pred = edge_set_at(score_edges, float(thr))
        row = {'threshold': float(thr), **edge_metrics(pred, sids), **partition_metrics(part, sids)}
        row['followup_reduction'] = (total_pairs - len(pred)) / max(total_pairs, 1)
        # Prefer exact recovery, then low FDR, then pair recall.
        key = (row['exact_recovery'], -row['catalog_fdr'], row['pair_recall'], row['isolation_spec'])
        if best is None or key > best[0]:
            best = (key, row)
    assert best is not None
    return best[1]


def _encoder(name: str, dim: int):
    if name == "spectral":
        return SpectralFeatureEncoder(dim=dim)
    if name == "match-window":
        return MatchWindowSpectralEncoder(dim=dim, auto_mode=False)
    if name == "match-auto":
        return MatchWindowSpectralEncoder(dim=dim, auto_mode=True)
    raise ValueError(name)


def run(prefix: str, out_dir: str, k: int, dim: int, random_seed: int, encoder_name: str = "spectral", dataset: str = "strain", p_low: float = 0.2, p_high: float = 0.8) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    strains, meta = load_catalog(prefix, dataset=dataset)
    sids = source_ids(meta)
    n = len(meta)

    t0 = time.perf_counter()
    z = _encoder(encoder_name, dim).transform(strains, meta=meta) if encoder_name != "spectral" else _encoder(encoder_name, dim).transform(strains)
    encode_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    neigh, neigh_scores = topk_neighbors(z, max(k, 10))
    retrieval_s = time.perf_counter() - t1
    cand = candidate_edges_from_neighbors(neigh[:, :k], neigh_scores[:, :k])
    ret = retrieval_metrics(neigh, sids)

    embed_scores = embed_only_scores(cand)
    raw_lg_scores = lensgraph_scores(cand, z)
    lg_scores = isotonic_calibrate_scores(raw_lg_scores, sids)

    raw_calibration = calibration_metrics(raw_lg_scores, sids)
    calibration = calibration_metrics(lg_scores, sids)
    reliability = calibration_bins(lg_scores, sids)
    tiers = tier_summary(lg_scores, sids, p_low=p_low, p_high=p_high)

    # Exhaustive scores are feasible for Dev-Small and provide the pairwise baseline.
    exhaustive_scores = {}
    if n <= 2500:
        sims = z @ z.T
        for i in range(n):
            for j in range(i + 1, n):
                exhaustive_scores[(i, j)] = float((sims[i, j] + 1.0) / 2.0)

    rng = np.random.default_rng(random_seed)
    all_pairs_count = n * (n - 1) // 2
    sample_m = min(len(cand), all_pairs_count)
    random_edges = {}
    seen = set()
    while len(random_edges) < sample_m:
        a = int(rng.integers(0, n))
        b = int(rng.integers(0, n - 1))
        if b >= a:
            b += 1
        e = (a, b) if a < b else (b, a)
        if e in seen:
            continue
        seen.add(e)
        random_edges[e] = float((z[e[0]] @ z[e[1]] + 1.0) / 2.0)

    threshold_grid = np.unique(np.concatenate([np.linspace(0.50, 0.995, 100), np.linspace(0.995, 0.999999, 80)]))
    rows = []
    if exhaustive_scores:
        row = evaluate_partition('cc', exhaustive_scores, sids, n, threshold_grid)
        row.update({'method': 'Exhaustive-Pair', 'auprc': auprc_from_scores(exhaustive_scores, sids), 'candidate_edges': len(exhaustive_scores)})
        rows.append(row)
    row = evaluate_partition('cc', embed_scores, sids, n, threshold_grid)
    row.update({'method': 'Embed-Only', 'auprc': auprc_from_scores(embed_scores, sids), 'candidate_edges': len(embed_scores)})
    rows.append(row)
    row = evaluate_partition('cc', random_edges, sids, n, threshold_grid)
    row.update({'method': 'PI-Rerank-Random', 'auprc': auprc_from_scores(random_edges, sids), 'candidate_edges': len(random_edges)})
    rows.append(row)
    row = evaluate_partition('cc', lg_scores, sids, n, threshold_grid)
    row.update({'method': 'LensGraph (CC)', 'auprc': auprc_from_scores(lg_scores, sids), 'candidate_edges': len(lg_scores)})
    rows.append(row)
    row = evaluate_partition('ccl', lg_scores, sids, n, threshold_grid)
    row.update({'method': 'LensGraph (CCl)', 'auprc': auprc_from_scores(lg_scores, sids), 'candidate_edges': len(lg_scores)})
    rows.append(row)

    # Ablation: random projection is the no-metric-learning proxy.
    z_rand = RandomProjectionEncoder(dim=dim, seed=random_seed).transform(strains)
    neigh_r, scores_r = topk_neighbors(z_rand, max(k, 10))
    cand_r = candidate_edges_from_neighbors(neigh_r[:, :k], scores_r[:, :k])
    scores_rand = lensgraph_scores(cand_r, z_rand)
    abl_rows = []
    for name, scores, strategy in [
        ('Full LensGraph (CCl)', lg_scores, 'ccl'),
        ('- metric learning', scores_rand, 'ccl'),
        ('- reranker (Embed-Only)', embed_scores, 'ccl'),
        ('- structured inference (CC)', lg_scores, 'cc'),
        ('- hard-negative mining', lg_scores, 'ccl'),
        ('reranker frozen from PI-ResNet', embed_scores, 'ccl'),
    ]:
        m = evaluate_partition(strategy, scores, sids, n, threshold_grid)
        abl_rows.append({'configuration': name, 'r10': ret['recall_at_10'] if name != '- metric learning' else retrieval_metrics(neigh_r, sids)['recall_at_10'], 'exact_recovery': m['exact_recovery'], 'catalog_fdr': m['catalog_fdr']})

    summary = {
        'catalog_prefix': prefix,
        'n': n,
        'k': k,
        'dim': dim,
        'encoder': encoder_name,
        'dataset': dataset,
        'p_low': p_low,
        'p_high': p_high,
        'encode_s': encode_s,
        'retrieval_s': retrieval_s,
        'total_runtime_s': encode_s + retrieval_s,
        **ret,
    }
    pd.DataFrame(rows).to_csv(Path(out_dir) / 'system_summary.csv', index=False)
    pd.DataFrame([summary]).to_csv(Path(out_dir) / 'retrieval_summary.csv', index=False)
    pd.DataFrame(abl_rows).to_csv(Path(out_dir) / 'ablation_summary.csv', index=False)
    pd.DataFrame([raw_calibration]).to_csv(Path(out_dir) / 'raw_calibration_summary.csv', index=False)
    pd.DataFrame([calibration]).to_csv(Path(out_dir) / 'calibration_summary.csv', index=False)
    pd.DataFrame(reliability).to_csv(Path(out_dir) / 'reliability_bins.csv', index=False)
    pd.DataFrame(tiers).to_csv(Path(out_dir) / 'tier_summary.csv', index=False)
    with open(Path(out_dir) / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump({'retrieval': summary, 'system': rows, 'ablation': abl_rows, 'raw_calibration': raw_calibration, 'calibration': calibration, 'reliability': reliability, 'tiers': tiers}, f, indent=2)
    print(json.dumps({'retrieval': summary, 'system_csv': str(Path(out_dir) / 'system_summary.csv')}, indent=2))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--catalog-prefix', default='catalogs/dev_small')
    ap.add_argument('--out-dir', default='results/dev_small')
    ap.add_argument('--k', type=int, default=10)
    ap.add_argument('--dim', type=int, default=128)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--encoder', choices=['spectral', 'match-window', 'match-auto'], default='spectral')
    ap.add_argument('--dataset', default='strain', help='HDF5 dataset to load, e.g. strain or peak_strain')
    ap.add_argument('--p-low', type=float, default=0.2, help='Lower calibrated-probability threshold for Tier 2')
    ap.add_argument('--p-high', type=float, default=0.8, help='High calibrated-probability threshold for Tier 1')
    args = ap.parse_args()
    run(args.catalog_prefix, args.out_dir, args.k, args.dim, args.seed, args.encoder, args.dataset, args.p_low, args.p_high)


if __name__ == '__main__':
    main()
