from __future__ import annotations

from itertools import product

import numpy as np


def similarity_matrix(z: np.ndarray) -> np.ndarray:
    z = z.astype(np.float32, copy=False)
    z = z / np.maximum(np.linalg.norm(z, axis=1, keepdims=True), 1e-8)
    s = z @ z.T
    np.fill_diagonal(s, -np.inf)
    return s


def topk_edges(
    scores: np.ndarray,
    topk: int = 10,
    min_score: float | None = None,
    mutual: bool = False,
    reciprocal_rank_max: int | None = 3,
    row_min_score: float | None = None,
    row_min_margin: float | None = None,
    edge_rank_bonus: float = 0.0,
) -> list[tuple[int, int, float]]:
    n = scores.shape[0]
    k = max(1, min(int(topk), n - 1))
    order = np.argsort(-scores, axis=1)[:, :k]
    row_scores = np.take_along_axis(scores, order, axis=1)
    row_best = row_scores[:, 0]
    row_second = row_scores[:, 1] if k > 1 else np.full(n, -np.inf, dtype=np.float32)
    active = np.ones(n, dtype=bool)
    if row_min_score is not None:
        active &= row_best >= float(row_min_score)
    if row_min_margin is not None:
        active &= (row_best - row_second) >= float(row_min_margin)

    top_sets = [set(row.tolist()) for row in order]
    rr_sets = None
    if reciprocal_rank_max is not None and reciprocal_rank_max > 0:
        rr = max(1, min(int(reciprocal_rank_max), n - 1))
        rr_sets = [set(row.tolist()) for row in np.argsort(-scores, axis=1)[:, :rr]]
    rank_maps = [{int(j): r + 1 for r, j in enumerate(row)} for row in order]

    edge_map: dict[tuple[int, int], float] = {}
    for i in range(n):
        if not active[i]:
            continue
        for j in order[i]:
            j = int(j)
            if i == j or not active[j]:
                continue
            score = float(scores[i, j])
            if min_score is not None and score < float(min_score):
                continue
            if mutual and i not in top_sets[j]:
                continue
            if rr_sets is not None and i not in rr_sets[j]:
                continue
            rank_i = rank_maps[i].get(j, k + 1)
            rank_j = rank_maps[j].get(i, k + 1)
            weight = score + float(edge_rank_bonus) * (1.0 / rank_i + 1.0 / rank_j)
            a, b = (i, j) if i < j else (j, i)
            edge_map[(a, b)] = max(edge_map.get((a, b), -np.inf), weight)
    return [(a, b, w) for (a, b), w in edge_map.items()]


def max_weight_pairs(edges: list[tuple[int, int, float]], n: int) -> list[tuple[int, int]]:
    try:
        import networkx as nx
        g = nx.Graph()
        g.add_nodes_from(range(n))
        for i, j, w in edges:
            g.add_edge(int(i), int(j), weight=float(w))
        return [(int(i), int(j)) for i, j in nx.algorithms.matching.max_weight_matching(g, maxcardinality=False)]
    except Exception:
        used: set[int] = set()
        pairs = []
        for i, j, _ in sorted(edges, key=lambda e: e[2], reverse=True):
            if i not in used and j not in used:
                pairs.append((int(i), int(j)))
                used.add(int(i)); used.add(int(j))
        return pairs


def retrieval_metrics(scores: np.ndarray, gt_partner: np.ndarray, ks: tuple[int, ...] = (1, 5, 10)) -> dict[str, float]:
    order = np.argsort(-scores, axis=1)
    valid = np.flatnonzero(gt_partner >= 0)
    out: dict[str, float] = {}
    for k in ks:
        kk = min(k, max(scores.shape[1] - 1, 1))
        hits = [int(gt_partner[i]) in order[i, :kk] for i in valid]
        out[f"r@{k}"] = float(np.mean(hits)) if hits else 0.0
    ranks = []
    for i in valid:
        loc = np.where(order[i] == int(gt_partner[i]))[0]
        if len(loc):
            ranks.append(int(loc[0]) + 1)
    out["mrr"] = float(np.mean([1.0 / r for r in ranks])) if ranks else 0.0
    out["median_true_rank"] = float(np.median(ranks)) if ranks else float("nan")
    return out


def pair_metrics(pairs: list[tuple[int, int]], gt_partner: np.ndarray) -> dict[str, float]:
    true_pairs = {tuple(sorted((i, int(j)))) for i, j in enumerate(gt_partner) if j >= 0 and i < j}
    pred_pairs = {tuple(sorted((int(i), int(j)))) for i, j in pairs}
    tp = len(true_pairs & pred_pairs)
    fp = len(pred_pairs - true_pairs)
    fn = len(true_pairs - pred_pairs)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    f2 = 5 * precision * recall / max(4 * precision + recall, 1e-12)
    return {"pairs": len(pred_pairs), "tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1, "f2": f2}


def evaluate_scores(scores: np.ndarray, gt_partner: np.ndarray, **params) -> dict[str, float]:
    edges = topk_edges(scores, **params)
    pairs = max_weight_pairs(edges, len(scores))
    out = {**retrieval_metrics(scores, gt_partner), **pair_metrics(pairs, gt_partner)}
    out["candidate_edges"] = len(edges)
    return out


def candidate_rows(scores: np.ndarray, gt_partner: np.ndarray, params: dict) -> list[dict]:
    edges = topk_edges(scores, **params)
    pairs = {tuple(sorted((i, j))) for i, j in max_weight_pairs(edges, len(scores))}
    rows = []
    for i, j, w in sorted(edges, key=lambda x: x[2], reverse=True):
        e = tuple(sorted((i, j)))
        rows.append({
            "i": int(i),
            "j": int(j),
            "score": float(w),
            "selected": e in pairs,
            "is_true": int(gt_partner[i]) == int(j),
        })
    return rows


def tune_matching(scores: np.ndarray, gt_partner: np.ndarray, grid: dict[str, list], metric: str = "f1") -> tuple[dict, dict]:
    names = list(grid)
    best_params: dict | None = None
    best_stats: dict | None = None
    best_score = -1.0
    for values in product(*(grid[name] for name in names)):
        params = dict(zip(names, values))
        stats = evaluate_scores(scores, gt_partner, **params)
        score = float(stats.get(metric, stats["f1"]))
        if score > best_score:
            best_score = score
            best_params = params
            best_stats = stats
    assert best_params is not None and best_stats is not None
    return best_params, best_stats
