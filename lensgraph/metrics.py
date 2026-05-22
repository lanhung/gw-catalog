from __future__ import annotations

import numpy as np


def true_groups(source_ids: np.ndarray) -> list[set[int]]:
    groups: dict[str, set[int]] = {}
    for i, sid in enumerate(source_ids):
        groups.setdefault(str(sid), set()).add(i)
    return list(groups.values())


def true_edge_set(source_ids: np.ndarray) -> set[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    for group in true_groups(source_ids):
        g = sorted(group)
        if len(g) < 2:
            continue
        for x in range(len(g)):
            for y in range(x + 1, len(g)):
                edges.add((g[x], g[y]))
    return edges


def edge_metrics(pred_edges: set[tuple[int, int]], source_ids: np.ndarray) -> dict[str, float]:
    truth = true_edge_set(source_ids)
    tp = len(pred_edges & truth)
    fp = len(pred_edges - truth)
    fn = len(truth - pred_edges)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    return {'pair_precision': precision, 'pair_recall': recall, 'pair_f1': f1, 'tp': tp, 'fp': fp, 'fn': fn}


def partition_metrics(partition: list[set[int]], source_ids: np.ndarray) -> dict[str, float]:
    truth = true_groups(source_ids)
    truth_sets = {frozenset(g) for g in truth}
    pred_sets = [frozenset(g) for g in partition]
    pred_lookup = set(pred_sets)
    lensed_truth = [g for g in truth if len(g) >= 2]
    exact = sum(1 for g in lensed_truth if frozenset(g) in pred_lookup)

    event_to_pred_id: dict[int, int] = {}
    event_to_pred_size: dict[int, int] = {}
    for pred_id, pg in enumerate(partition):
        size = len(pg)
        for i in pg:
            event_to_pred_id[i] = pred_id
            event_to_pred_size[i] = size

    # For each true system, count members by assigned predicted group. This is
    # equivalent to the previous max-over-partitions overlap, but linear in the
    # number of events instead of len(truth) * len(partition).
    sys_rec_terms = []
    for g in lensed_truth:
        overlap_by_pred: dict[int, int] = {}
        for i in g:
            pred_id = event_to_pred_id.get(i, -1)
            overlap_by_pred[pred_id] = overlap_by_pred.get(pred_id, 0) + 1
        best = max(overlap_by_pred.values(), default=0)
        sys_rec_terms.append(best / max(len(g), 1))

    isolated = [next(iter(g)) for g in truth if len(g) == 1]
    iso_ok = sum(1 for i in isolated if event_to_pred_size.get(i, 1) == 1)

    pred_lensed = [p for p in pred_sets if len(p) >= 2]
    false_groups = sum(1 for p in pred_lensed if p not in truth_sets)
    return {
        'exact_recovery': exact / max(len(lensed_truth), 1),
        'system_recall': float(np.mean(sys_rec_terms)) if sys_rec_terms else 0.0,
        'isolation_spec': iso_ok / max(len(isolated), 1),
        'catalog_fdr': false_groups / max(len(pred_lensed), 1),
        'pred_lensed_systems': float(len(pred_lensed)),
        'true_lensed_systems': float(len(lensed_truth)),
    }


def auprc_from_scores(edge_scores: dict[tuple[int, int], float], source_ids: np.ndarray) -> float:
    if not edge_scores:
        return 0.0
    truth = true_edge_set(source_ids)
    items = sorted(edge_scores.items(), key=lambda kv: -kv[1])
    total_pos = len(truth)
    if total_pos == 0:
        return 0.0
    tp = 0
    fp = 0
    prev_recall = 0.0
    area = 0.0
    for edge, _ in items:
        if edge in truth:
            tp += 1
        else:
            fp += 1
        recall = tp / total_pos
        precision = tp / max(tp + fp, 1)
        area += precision * max(recall - prev_recall, 0.0)
        prev_recall = recall
    return float(area)



def retrieval_rank_metrics(neighbors: np.ndarray, source_ids: np.ndarray) -> dict[str, float]:
    """Rank metrics for the first true counterpart in each lensed event list."""
    n, _ = neighbors.shape
    _, inv, counts = np.unique(source_ids, return_inverse=True, return_counts=True)
    lensed = counts[inv] >= 2
    ranks: list[float] = []
    for i in range(n):
        if not lensed[i]:
            continue
        hits = np.flatnonzero(source_ids[neighbors[i]] == source_ids[i])
        ranks.append(float(hits[0] + 1) if len(hits) else float('inf'))

    if not ranks:
        return {
            'mrr': 0.0,
            'mean_true_rank': 0.0,
            'median_true_rank': 0.0,
            'true_rank_found_fraction': 0.0,
        }

    rank_arr = np.array(ranks, dtype=np.float64)
    finite = rank_arr[np.isfinite(rank_arr)]
    reciprocal = np.where(np.isfinite(rank_arr), 1.0 / rank_arr, 0.0)
    return {
        'mrr': float(np.mean(reciprocal)),
        'mean_true_rank': float(np.mean(finite)) if len(finite) else 0.0,
        'median_true_rank': float(np.median(finite)) if len(finite) else 0.0,
        'true_rank_found_fraction': float(len(finite) / len(rank_arr)),
    }


def _score_labels(edge_scores: dict[tuple[int, int], float], source_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    truth = true_edge_set(source_ids)
    scores = np.array([float(s) for s in edge_scores.values()], dtype=np.float64)
    scores = np.clip(scores, 0.0, 1.0)
    labels = np.array([1.0 if e in truth else 0.0 for e in edge_scores], dtype=np.float64)
    return scores, labels




def isotonic_calibrate_scores(edge_scores: dict[tuple[int, int], float], source_ids: np.ndarray, smooth: float = 1e-3) -> dict[tuple[int, int], float]:
    """Return monotone isotonic-calibrated candidate probabilities."""
    if not edge_scores:
        return {}
    scores, labels = _score_labels(edge_scores, source_ids)
    order = np.argsort(scores, kind='mergesort')
    y = labels[order]
    blocks: list[dict[str, float]] = []
    for idx, label in enumerate(y):
        blocks.append({'start': float(idx), 'end': float(idx + 1), 'weight': 1.0, 'sum': float(label)})
        while len(blocks) >= 2:
            left = blocks[-2]
            right = blocks[-1]
            left_rate = (left['sum'] + smooth) / (left['weight'] + 2.0 * smooth)
            right_rate = (right['sum'] + smooth) / (right['weight'] + 2.0 * smooth)
            if left_rate <= right_rate:
                break
            merged = {
                'start': left['start'],
                'end': right['end'],
                'weight': left['weight'] + right['weight'],
                'sum': left['sum'] + right['sum'],
            }
            blocks[-2:] = [merged]

    calibrated_sorted = np.empty_like(scores, dtype=np.float64)
    for block in blocks:
        start = int(block['start'])
        end = int(block['end'])
        prob = (block['sum'] + smooth) / (block['weight'] + 2.0 * smooth)
        calibrated_sorted[start:end] = prob
    calibrated = np.empty_like(calibrated_sorted)
    calibrated[order] = calibrated_sorted
    return {edge: float(prob) for edge, prob in zip(edge_scores.keys(), calibrated)}


def platt_calibrate_scores(edge_scores: dict[tuple[int, int], float], source_ids: np.ndarray, max_iter: int = 1000, lr: float = 0.1, l2: float = 1e-3) -> dict[tuple[int, int], float]:
    """Fit a Platt-style sigmoid and return calibrated candidate probabilities.

    In paper experiments this should be fitted on a validation simulation split
    and applied to held-out catalogs. The single-catalog CLI mode fits on the
    current catalog labels so the reporting path can exercise the full
    calibration and tiering interface.
    """
    if not edge_scores:
        return {}
    scores, labels = _score_labels(edge_scores, source_ids)
    eps = 1e-6
    x = np.log(np.clip(scores, eps, 1.0 - eps) / np.clip(1.0 - scores, eps, 1.0))
    x_mean = float(np.mean(x))
    x_std = float(np.std(x) + 1e-6)
    x = (x - x_mean) / x_std
    pos = float(labels.sum())
    neg = float(len(labels) - pos)
    if pos == 0.0 or neg == 0.0:
        prior = (pos + 0.5) / (len(labels) + 1.0)
        return {edge: float(prior) for edge in edge_scores}

    a = 1.0
    b = float(np.log((pos + 0.5) / (neg + 0.5)))
    for _ in range(max_iter):
        logits = np.clip(a * x + b, -40.0, 40.0)
        pred = 1.0 / (1.0 + np.exp(-logits))
        err = pred - labels
        grad_a = float(np.mean(err * x) + l2 * a)
        grad_b = float(np.mean(err))
        a -= lr * grad_a
        b -= lr * grad_b
        if abs(grad_a) + abs(grad_b) < 1e-8:
            break

    calibrated = 1.0 / (1.0 + np.exp(-np.clip(a * x + b, -40.0, 40.0)))
    return {edge: float(prob) for edge, prob in zip(edge_scores.keys(), calibrated)}


def calibration_metrics(edge_scores: dict[tuple[int, int], float], source_ids: np.ndarray, n_bins: int = 10) -> dict[str, float]:
    """Probability-calibration metrics over candidate-pair scores."""
    if not edge_scores:
        return {
            'brier': 0.0,
            'nll': 0.0,
            'ece': 0.0,
            'positive_rate': 0.0,
            'candidate_edges': 0.0,
        }
    scores, labels = _score_labels(edge_scores, source_ids)
    eps = 1e-12
    clipped = np.clip(scores, eps, 1.0 - eps)
    brier = np.mean((scores - labels) ** 2)
    nll = -np.mean(labels * np.log(clipped) + (1.0 - labels) * np.log(1.0 - clipped))
    ece = 0.0
    for row in calibration_bins(edge_scores, source_ids, n_bins=n_bins):
        ece += row['fraction'] * abs(row['mean_score'] - row['empirical_positive_rate'])
    return {
        'brier': float(brier),
        'nll': float(nll),
        'ece': float(ece),
        'positive_rate': float(np.mean(labels)),
        'candidate_edges': float(len(scores)),
    }


def calibration_bins(edge_scores: dict[tuple[int, int], float], source_ids: np.ndarray, n_bins: int = 10) -> list[dict[str, float]]:
    """Reliability-diagram bins for candidate-pair probabilities."""
    if not edge_scores:
        return []
    scores, labels = _score_labels(edge_scores, source_ids)
    rows: list[dict[str, float]] = []
    total = len(scores)
    for b in range(n_bins):
        lo = b / n_bins
        hi = (b + 1) / n_bins
        if b == n_bins - 1:
            mask = (scores >= lo) & (scores <= hi)
        else:
            mask = (scores >= lo) & (scores < hi)
        count = int(mask.sum())
        rows.append({
            'bin': float(b),
            'p_min': float(lo),
            'p_max': float(hi),
            'count': float(count),
            'fraction': float(count / max(total, 1)),
            'mean_score': float(np.mean(scores[mask])) if count else 0.0,
            'empirical_positive_rate': float(np.mean(labels[mask])) if count else 0.0,
        })
    return rows


def tier_summary(edge_scores: dict[tuple[int, int], float], source_ids: np.ndarray, p_low: float = 0.2, p_high: float = 0.8) -> list[dict[str, float | str]]:
    """Tiered follow-up summary for calibrated candidate-pair probabilities."""
    truth = true_edge_set(source_ids)
    total_truth = max(len(truth), 1)
    total_candidates = max(len(edge_scores), 1)
    n = len(source_ids)
    total_pairs = max(n * (n - 1) / 2, 1)

    def row(name: str, selected: set[tuple[int, int]], p_min: float, p_max: float) -> dict[str, float | str]:
        tp = len(selected & truth)
        count = len(selected)
        return {
            'tier': name,
            'p_min': float(p_min),
            'p_max': float(p_max),
            'candidate_edges': float(count),
            'candidate_fraction': float(count / total_candidates),
            'pair_precision': float(tp / max(count, 1)),
            'pair_recall': float(tp / total_truth),
            'true_edges': float(tp),
            'followup_reduction': float((total_pairs - count) / total_pairs),
        }

    tier1 = {e for e, s in edge_scores.items() if float(s) >= p_high}
    tier2 = {e for e, s in edge_scores.items() if p_low <= float(s) < p_high}
    tier3 = {e for e, s in edge_scores.items() if float(s) < p_low}
    return [
        row('Tier 1', tier1, p_high, 1.0),
        row('Tier 2', tier2, p_low, p_high),
        row('Tier 3', tier3, 0.0, p_low),
        row('Tier 1+2', tier1 | tier2, p_low, 1.0),
    ]
