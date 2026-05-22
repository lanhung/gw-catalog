from __future__ import annotations

import json
from pathlib import Path
from dataclasses import asdict

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset

from .config import MatchRunConfig
from .data import EvaluationSet, PairDataset, ground_truth_partner, load_match_arrays, split_indices
from .matching import candidate_rows, evaluate_scores, similarity_matrix, tune_matching, topk_edges
from .models import MatchEncoder1D, NTXentLoss


def _device(cpu: bool = False) -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() and not cpu else "cpu")


def build_model(cfg: MatchRunConfig) -> MatchEncoder1D:
    in_channels = 2 if cfg.use_hilbert else 1
    return MatchEncoder1D(in_channels=in_channels, d_model=cfg.d_model, emb_dim=cfg.emb_dim, width_scale=cfg.width_scale)



class HardNegativeDataset(Dataset):
    def __init__(self, eval_ds: EvaluationSet, hard_pairs: list[tuple[int, int]], cfg: MatchRunConfig) -> None:
        self.eval_ds = eval_ds
        self.hard_pairs = hard_pairs
        self.cfg = cfg

    def __len__(self) -> int:
        return len(self.hard_pairs)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        i, j = self.hard_pairs[idx]
        return self.eval_ds[i], self.eval_ds[j]


def mine_hard_negatives(scores: np.ndarray, gt: np.ndarray, cfg: MatchRunConfig) -> list[tuple[int, int]]:
    edges = topk_edges(
        scores,
        topk=cfg.hard_neg_topk,
        min_score=cfg.hard_neg_min_score,
        mutual=False,
        reciprocal_rank_max=cfg.reciprocal_rank_max,
        row_min_score=None,
        row_min_margin=None,
        edge_rank_bonus=0.0,
    )
    by_anchor: dict[int, list[tuple[int, float]]] = {}
    for i, j, score in sorted(edges, key=lambda e: e[2], reverse=True):
        if int(gt[i]) == int(j):
            continue
        by_anchor.setdefault(int(i), []).append((int(j), float(score)))
        by_anchor.setdefault(int(j), []).append((int(i), float(score)))
    hard = []
    seen: set[tuple[int, int]] = set()
    for i, js in by_anchor.items():
        for j, _ in js[: cfg.hard_neg_per_anchor]:
            e = (i, j) if i < j else (j, i)
            if e not in seen:
                seen.add(e)
                hard.append(e)
    return hard


def hard_negative_finetune(
    model: MatchEncoder1D,
    val_ds: EvaluationSet,
    hard_pairs: list[tuple[int, int]],
    cfg: MatchRunConfig,
    cpu: bool = False,
) -> list[dict]:
    if not hard_pairs or cfg.hard_neg_epochs <= 0:
        return []
    device = _device(cpu)
    model.to(device)
    dl = DataLoader(HardNegativeDataset(val_ds, hard_pairs, cfg), batch_size=cfg.batch_size, shuffle=True, num_workers=0)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.hard_neg_lr, weight_decay=cfg.weight_decay)
    history = []
    for epoch in range(1, cfg.hard_neg_epochs + 1):
        model.train()
        losses = []
        for xa, xb in dl:
            xa = xa.to(device, non_blocking=True)
            xb = xb.to(device, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            za = model(xa)
            zb = model(xb)
            sim = (za * zb).sum(dim=1)
            loss = cfg.hard_neg_weight * torch.relu(sim - cfg.hard_neg_margin).pow(2).mean()
            loss.backward()
            opt.step()
            losses.append(float(loss.detach().cpu()))
        row = {"hard_neg_epoch": epoch, "hard_neg_loss": float(np.mean(losses)) if losses else 0.0}
        history.append(row)
        print(json.dumps(row), flush=True)
    return history


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

    val_ds = EvaluationSet(arrays, splits["lensed"]["val"], splits["unlensed"]["val"], cfg)
    val_scores = similarity_matrix(embed_eval(model, val_ds, cfg, cpu=cpu))
    val_gt = ground_truth_partner(val_ds.meta)
    best_params, val_stats = tune_matching(val_scores, val_gt, default_tuning_grid(cfg), metric=cfg.tune_for)
    results["best_params"] = best_params
    results["val_before_hnm"] = val_stats

    hard_pairs = mine_hard_negatives(val_scores, val_gt, cfg) if cfg.hard_neg_enable else []
    results["hard_negatives"] = len(hard_pairs)
    hn_history = hard_negative_finetune(model, val_ds, hard_pairs, cfg, cpu=cpu)
    if hn_history:
        results["hard_negative_history"] = hn_history
        val_scores = similarity_matrix(embed_eval(model, val_ds, cfg, cpu=cpu))
        best_params, val_stats = tune_matching(val_scores, val_gt, default_tuning_grid(cfg), metric=cfg.tune_for)
        results["best_params"] = best_params
    results["val"] = val_stats

    test_ds = EvaluationSet(arrays, splits["lensed"]["test"], splits["unlensed"]["test"], cfg)
    test_scores = similarity_matrix(embed_eval(model, test_ds, cfg, cpu=cpu))
    test_gt = ground_truth_partner(test_ds.meta)
    results["test"] = evaluate_scores(test_scores, test_gt, **best_params)

    if cfg.export_candidates:
        pd.DataFrame(candidate_rows(val_scores, val_gt, best_params)).to_csv(cfg.out_dir / "val_candidates.csv", index=False)
        pd.DataFrame(candidate_rows(test_scores, test_gt, best_params)).to_csv(cfg.out_dir / "test_candidates.csv", index=False)

    torch.save({"model": model.state_dict(), "config": results["config"]}, cfg.out_dir / "model.pt")
    pd.DataFrame(train_info["history"]).to_csv(cfg.out_dir / "history.csv", index=False)
    with open(cfg.out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2), flush=True)
    return results
