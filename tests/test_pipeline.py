import numpy as np

from lensgraph.models.encoder import SpectralFeatureEncoder
from lensgraph.retrieval.ann_index import topk_neighbors, candidate_edges_from_neighbors, retrieval_metrics
from lensgraph.graph.inference import connected_components_partition, pivot_correlation_clustering
from lensgraph.metrics import edge_metrics, partition_metrics, calibration_metrics, isotonic_calibrate_scores, platt_calibrate_scores, tier_summary


def test_retrieval_and_metrics_contracts():
    rng = np.random.default_rng(0)
    base = rng.normal(size=(3, 128)).astype(np.float32)
    strains = np.vstack([base[0], np.roll(base[0], 3), base[1], np.roll(base[1], 4), base[2]])
    source = np.array(['a', 'a', 'b', 'b', 'c'])
    z = SpectralFeatureEncoder(dim=16).transform(strains)
    neigh, scores = topk_neighbors(z, 2)
    ret = retrieval_metrics(neigh, source)
    assert ret['recall_at_1'] >= 0.5
    assert 'mrr' in ret
    assert 'median_true_rank' in ret
    edges = candidate_edges_from_neighbors(neigh, scores)
    assert all(a < b for a, b in edges)
    pred = {e for e, s in edges.items() if s > 0}
    em = edge_metrics(pred, source)
    assert 0 <= em['pair_recall'] <= 1
    calibrated = platt_calibrate_scores(edges, source)
    assert set(calibrated) == set(edges)
    iso = isotonic_calibrate_scores(edges, source)
    assert set(iso) == set(edges)
    cal = calibration_metrics(calibrated, source)
    assert 0 <= cal['ece'] <= 1
    tiers = tier_summary(edges, source, p_low=0.25, p_high=0.75)
    assert {row['tier'] for row in tiers} == {'Tier 1', 'Tier 2', 'Tier 3', 'Tier 1+2'}
    cc = connected_components_partition(len(source), edges, 0.0)
    ccl = pivot_correlation_clustering(len(source), edges, 0.0)
    for part in (cc, ccl):
        flat = sorted(i for g in part for i in g)
        assert flat == list(range(len(source)))
        pm = partition_metrics(part, source)
        assert 0 <= pm['exact_recovery'] <= 1
