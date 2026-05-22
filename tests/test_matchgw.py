from __future__ import annotations

from pathlib import Path

import numpy as np

from matchgw.config import MatchRunConfig
from matchgw.data import EvaluationSet, ground_truth_partner, load_match_arrays, split_indices
from matchgw.matching import evaluate_scores, similarity_matrix, tune_matching
from matchgw.rerank import calibrated_candidate_report, candidate_feature_frame, fit_pair_calibrator
from matchgw.pipeline import build_model


def _write_fixture(root: Path, n_lensed: int = 8, n_unlensed: int = 6, length: int = 128) -> None:
    rng = np.random.default_rng(3)
    sis = root / "SIS_data_0222"
    unl = root / "Unlensed_data_0222"
    sis.mkdir(parents=True)
    unl.mkdir(parents=True)
    x1 = rng.normal(size=(n_lensed, length)).astype(np.float32)
    x2 = np.roll(x1, 4, axis=1) * 0.9
    u = rng.normal(size=(n_unlensed, length)).astype(np.float32)
    np.save(sis / "SIS_data_strain_1.npy", x1)
    np.save(sis / "SIS_data_strain_2.npy", x2)
    np.save(unl / "unlensed_data_strain.npy", u)


def test_match_data_contract(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    cfg = MatchRunConfig(data_root=tmp_path, model_type="SIS", data_mode="noisy", lensed_limit=8, unlensed_limit=6, target_len=64, stride=2)
    arrays = load_match_arrays(cfg)
    splits = split_indices(len(arrays.l1), len(arrays.unlensed), cfg)
    ds = EvaluationSet(arrays, splits["lensed"]["test"], splits["unlensed"]["test"], cfg)
    assert len(ds.meta) == 2 * len(splits["lensed"]["test"]) + len(splits["unlensed"]["test"])
    gt = ground_truth_partner(ds.meta)
    assert int((gt >= 0).sum()) == 2 * len(splits["lensed"]["test"])


def test_matching_tuning_recovers_obvious_pairs() -> None:
    z = np.array([
        [1, 0], [0.99, 0.01],
        [0, 1], [0.02, 0.98],
        [-1, 0], [0, -1],
    ], dtype=np.float32)
    scores = similarity_matrix(z)
    gt = np.array([1, 0, 3, 2, -1, -1])
    grid = {
        "topk": [1, 2],
        "min_score": [0.5, 0.9],
        "mutual": [False],
        "reciprocal_rank_max": [None, 1],
        "row_min_score": [None],
        "row_min_margin": [None],
        "edge_rank_bonus": [0.0],
    }
    params, stats = tune_matching(scores, gt, grid)
    assert stats["tp"] == 2
    assert stats["f1"] == 1.0
    assert evaluate_scores(scores, gt, **params)["tp"] == 2


def test_calibrated_candidate_report_adds_tiers() -> None:
    z = np.array([
        [1, 0], [0.99, 0.01],
        [0, 1], [0.02, 0.98],
        [-1, 0], [0, -1],
    ], dtype=np.float32)
    scores = similarity_matrix(z)
    gt = np.array([1, 0, 3, 2, -1, -1])
    cfg = MatchRunConfig(p_low=0.25, p_high=0.75)
    params = {
        "topk": 2,
        "min_score": 0.5,
        "mutual": False,
        "reciprocal_rank_max": None,
        "row_min_score": None,
        "row_min_margin": None,
        "edge_rank_bonus": 0.0,
    }
    frame = candidate_feature_frame(scores, gt, params)
    calibrator = fit_pair_calibrator(frame, cfg)
    report, metrics = calibrated_candidate_report(scores, gt, params, calibrator, cfg)
    assert {"p_hat", "tier", "rank_i", "rank_j"}.issubset(report.columns)
    assert metrics["candidate_pair_recall"] == 1.0
    assert 0.0 <= metrics["cal_ece"] <= 1.0
    assert metrics["followup_reduction"] > 0.0


def test_inceptiontime_backbone_outputs_normalized_embeddings() -> None:
    cfg = MatchRunConfig(backbone="inceptiontime", target_len=128, width_scale=0.5, d_model=32, emb_dim=16)
    model = build_model(cfg)
    x = np.random.default_rng(4).normal(size=(3, 1, 128)).astype(np.float32)
    import torch
    with torch.no_grad():
        z = model(torch.from_numpy(x))
    assert tuple(z.shape) == (3, 16)
    assert torch.allclose(z.norm(dim=1), torch.ones(3), atol=1e-5)
