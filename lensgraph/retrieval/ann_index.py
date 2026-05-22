from __future__ import annotations

import numpy as np

from lensgraph.metrics import retrieval_rank_metrics


def topk_neighbors(embeddings: np.ndarray, k: int, block_size: int = 2048) -> tuple[np.ndarray, np.ndarray]:
    """Exact inner-product top-k retrieval for normalized embeddings."""
    z = embeddings.astype(np.float32, copy=False)
    n = z.shape[0]
    k_eff = min(k, max(n - 1, 1))
    neigh = np.empty((n, k_eff), dtype=np.int32)
    scores = np.empty((n, k_eff), dtype=np.float32)
    for start in range(0, n, block_size):
        stop = min(start + block_size, n)
        sims = z[start:stop] @ z.T
        rows = np.arange(start, stop)
        sims[np.arange(stop - start), rows] = -np.inf
        idx = np.argpartition(-sims, kth=k_eff - 1, axis=1)[:, :k_eff]
        part = np.take_along_axis(sims, idx, axis=1)
        order = np.argsort(-part, axis=1)
        idx = np.take_along_axis(idx, order, axis=1)
        part = np.take_along_axis(part, order, axis=1)
        neigh[start:stop] = idx.astype(np.int32)
        scores[start:stop] = part.astype(np.float32)
    return neigh, scores


def candidate_edges_from_neighbors(neighbors: np.ndarray, scores: np.ndarray | None = None) -> dict[tuple[int, int], float]:
    edges: dict[tuple[int, int], float] = {}
    n, k = neighbors.shape
    for i in range(n):
        for r in range(k):
            j = int(neighbors[i, r])
            if i == j:
                continue
            a, b = (i, j) if i < j else (j, i)
            s = 1.0 if scores is None else float(scores[i, r])
            if (a, b) not in edges or s > edges[(a, b)]:
                edges[(a, b)] = s
    return edges


def retrieval_metrics(neighbors: np.ndarray, source_ids: np.ndarray) -> dict[str, float]:
    n, kmax = neighbors.shape
    lensed = np.zeros(n, dtype=bool)
    _, inv, counts = np.unique(source_ids, return_inverse=True, return_counts=True)
    lensed = counts[inv] >= 2
    denom = int(lensed.sum())
    out: dict[str, float] = {}
    for k in (1, 5, 10):
        kk = min(k, kmax)
        hit = np.zeros(n, dtype=bool)
        for i in range(n):
            if not lensed[i]:
                continue
            hit[i] = np.any(source_ids[neighbors[i, :kk]] == source_ids[i])
        out[f"recall_at_{k}"] = float(hit.sum() / max(denom, 1))
    edge_count = len(candidate_edges_from_neighbors(neighbors, None))
    out['candidate_edges'] = float(edge_count)
    out['edge_reduction'] = float(edge_count / max(n * (n - 1) / 2, 1))
    out.update(retrieval_rank_metrics(neighbors, source_ids))
    return out
