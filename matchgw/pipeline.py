from __future__ import annotations

import json
from pathlib import Path
from dataclasses import asdict

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from .config import MatchRunConfig
from .data import EvaluationSet, PairDataset, ground_truth_partner, load_match_arrays, split_indices
from .matching import evaluate_scores, similarity_matrix, tune_matching
from .models import MatchEncoder1D, NTXentLoss


def _device(cpu: bool = False) -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() and not cpu else "cpu")


def build_model(cfg: MatchRunConfig) -> MatchEncoder1D:
    in_channels = 2 if cfg.use_hilbert else 1
    return MatchEncoder1D(in_channels=in_channels, d_model=cfg.d_model, emb_dim=cfg.emb_dim, width_scale=cfg.width_scale)


def train_encoder(cfg: MatchRunConfig, cpu: bool = False) -> tuple[MatchEncoder1D, dict, dict]:
    arrays = load_match_arrays(cfg)
    splits = split_indices(len(arrays.l1), len(arrays.unlensed), cfg)
    train_ds = PairDataset(arrays, splits["lensed"]["train"], splits["unlensed"]["train"], cfg)
    train_dl = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True, num_workers=0, drop_last=True)
    device = _device(cpu)
    model = build_model(cfg).to(device)
    loss_fn = NTXentLoss(cfg.tau)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    history = []
    for epoch in range(1, cfg.epochs + 1):
        model.train()
        losses = []
        for xa, xb in train_dl:
            xa = xa.to(device, non_blocking=True)
            xb = xb.to(device, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            loss = loss_fn(model(xa), model(xb))
            loss.backward()
            opt.step()
            losses.append(float(loss.detach().cpu()))
        row = {"epoch": epoch, "loss": float(np.mean(losses)) if losses else float("nan")}
        history.append(row)
        print(json.dumps(row), flush=True)
    return model, {"splits": splits, "arrays": arrays}, {"history": history}


@torch.no_grad()
def embed_eval(model: MatchEncoder1D, ds: EvaluationSet, cfg: MatchRunConfig, cpu: bool = False) -> np.ndarray:
    device = _device(cpu)
    model.eval().to(device)
    dl = DataLoader(ds, batch_size=cfg.eval_batch_size, shuffle=False, num_workers=0)
    chunks = []
    for x in dl:
        chunks.append(model(x.to(device, non_blocking=True)).cpu().numpy())
    return np.concatenate(chunks, axis=0).astype(np.float32)


def default_tuning_grid(cfg: MatchRunConfig) -> dict[str, list]:
    return {
        "topk": [5, 10, 20],
        "min_score": [None, 0.70, 0.80, 0.85, 0.90],
        "mutual": [False, True],
        "reciprocal_rank_max": [None, 1, 3, 5],
        "row_min_score": [None, 0.60, 0.70, 0.80],
        "row_min_margin": [None, 0.0, 0.03, 0.06],
        "edge_rank_bonus": [0.0, 0.01],
    }


def run_train_eval(cfg: MatchRunConfig, cpu: bool = False) -> dict:
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    model, state, train_info = train_encoder(cfg, cpu=cpu)
    arrays = state["arrays"]
    splits = state["splits"]

    results = {"config": {k: str(v) if isinstance(v, Path) else v for k, v in asdict(cfg).items()}, "history": train_info["history"]}
    for split in ("val", "test"):
        ds = EvaluationSet(arrays, splits["lensed"][split], splits["unlensed"][split], cfg)
        z = embed_eval(model, ds, cfg, cpu=cpu)
        scores = similarity_matrix(z)
        gt = ground_truth_partner(ds.meta)
        if split == "val":
            best_params, stats = tune_matching(scores, gt, default_tuning_grid(cfg), metric=cfg.tune_for)
            results["best_params"] = best_params
            results["val"] = stats
        else:
            params = results.get("best_params", {
                "topk": cfg.coarse_topk,
                "min_score": cfg.coarse_min_score,
                "mutual": cfg.coarse_mutual,
                "reciprocal_rank_max": cfg.reciprocal_rank_max,
                "row_min_score": cfg.row_min_score,
                "row_min_margin": cfg.row_min_margin,
                "edge_rank_bonus": cfg.edge_rank_bonus,
            })
            results["test"] = evaluate_scores(scores, gt, **params)

    torch.save({"model": model.state_dict(), "config": results["config"]}, cfg.out_dir / "model.pt")
    pd.DataFrame(train_info["history"]).to_csv(cfg.out_dir / "history.csv", index=False)
    with open(cfg.out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2), flush=True)
    return results
