from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lensgraph.catalog_io import load_catalog, source_ids
from lensgraph.retrieval.ann_index import topk_neighbors, candidate_edges_from_neighbors, retrieval_metrics
from lensgraph.rerank import lensgraph_scores
from lensgraph.graph.inference import pivot_correlation_clustering
from lensgraph.metrics import edge_metrics, partition_metrics, auprc_from_scores


class WaveformMetricNet(nn.Module):
    def __init__(self, dim: int = 128) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=15, stride=2, padding=7),
            nn.BatchNorm1d(32),
            nn.GELU(),
            nn.Conv1d(32, 64, kernel_size=11, stride=2, padding=5),
            nn.BatchNorm1d(64),
            nn.GELU(),
            nn.Conv1d(64, 128, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm1d(128),
            nn.GELU(),
            nn.Conv1d(128, 192, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm1d(192),
            nn.GELU(),
            nn.Conv1d(192, 192, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm1d(192),
            nn.GELU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(192, dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.net(x[:, None, :])
        return nn.functional.normalize(z, dim=1)


class PairBatchDataset(Dataset):
    def __init__(self, lensed_groups: list[np.ndarray], singleton_indices: np.ndarray, steps: int, pairs_per_batch: int, singles_per_batch: int, seed: int) -> None:
        self.lensed_groups = lensed_groups
        self.singleton_indices = singleton_indices
        self.steps = steps
        self.pairs_per_batch = min(pairs_per_batch, len(lensed_groups))
        self.singles_per_batch = min(singles_per_batch, len(singleton_indices))
        self.rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return self.steps

    def __getitem__(self, idx: int) -> np.ndarray:
        group_ids = self.rng.choice(len(self.lensed_groups), size=self.pairs_per_batch, replace=False)
        chosen = []
        for gid in group_ids:
            group = self.lensed_groups[int(gid)]
            if len(group) >= 2:
                chosen.extend(self.rng.choice(group, size=2, replace=False).tolist())
        if self.singles_per_batch > 0:
            chosen.extend(self.rng.choice(self.singleton_indices, size=self.singles_per_batch, replace=False).tolist())
        return np.asarray(chosen, dtype=np.int64)


def collate_index_batches(batch: list[np.ndarray]) -> np.ndarray:
    return batch[0]


def normalize_waveforms(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32, copy=False)
    x = x - x.mean(axis=1, keepdims=True)
    x = x / np.maximum(x.std(axis=1, keepdims=True), 1e-6)
    return x.astype(np.float32, copy=False)


def split_sources(sids: np.ndarray, train_frac: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    unique = np.unique(sids)
    rng.shuffle(unique)
    n_train = int(round(len(unique) * train_frac))
    train_sources = set(unique[:n_train].tolist())
    train_mask = np.array([sid in train_sources for sid in sids], dtype=bool)
    return train_mask, ~train_mask


def build_groups(sids: np.ndarray, mask: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
    groups = []
    singles = []
    idx = np.flatnonzero(mask)
    by_sid: dict[str, list[int]] = {}
    for i in idx:
        by_sid.setdefault(str(sids[i]), []).append(int(i))
    for vals in by_sid.values():
        arr = np.asarray(vals, dtype=np.int64)
        if len(arr) >= 2:
            groups.append(arr)
        else:
            singles.append(arr[0])
    return groups, np.asarray(singles, dtype=np.int64)


def supcon_loss(z: torch.Tensor, labels: torch.Tensor, temperature: float) -> torch.Tensor:
    sim = z @ z.T / temperature
    eye = torch.eye(len(z), dtype=torch.bool, device=z.device)
    same = labels[:, None].eq(labels[None, :]) & ~eye
    logits = sim.masked_fill(eye, -1e9)
    log_prob = logits - torch.logsumexp(logits, dim=1, keepdim=True)
    pos_count = same.sum(dim=1)
    valid = pos_count > 0
    if not torch.any(valid):
        return z.sum() * 0.0
    return -(log_prob.masked_fill(~same, 0.0).sum(dim=1)[valid] / pos_count[valid]).mean()


@torch.no_grad()
def embed(model: nn.Module, x: np.ndarray, indices: np.ndarray, batch_size: int, device: torch.device) -> np.ndarray:
    model.eval()
    out = []
    for start in range(0, len(indices), batch_size):
        batch_idx = indices[start:start + batch_size]
        xb = torch.from_numpy(x[batch_idx]).to(device, non_blocking=True)
        out.append(model(xb).cpu().numpy())
    return np.concatenate(out, axis=0).astype(np.float32)


def best_system(scores: dict[tuple[int, int], float], sids: np.ndarray, n: int) -> dict:
    best = None
    grid = np.unique(np.concatenate([np.linspace(0.05, 0.95, 91), np.linspace(0.95, 0.999, 50)]))
    for thr in grid:
        pred = {e for e, score in scores.items() if score >= float(thr)}
        part = pivot_correlation_clustering(n, scores, float(thr))
        row = {'threshold': float(thr), **edge_metrics(pred, sids), **partition_metrics(part, sids)}
        key = (row['exact_recovery'], -row['catalog_fdr'], row['pair_f1'])
        if best is None or key > best[0]:
            best = (key, row)
    assert best is not None
    return best[1]


def run(args: argparse.Namespace) -> dict:
    os.makedirs(args.out_dir, exist_ok=True)
    strains, meta = load_catalog(args.catalog_prefix, dataset=args.dataset)
    x = normalize_waveforms(strains)
    sids = source_ids(meta)
    train_mask, test_mask = split_sources(sids, args.train_frac, args.seed)
    train_groups, train_singles = build_groups(sids, train_mask)
    test_indices = np.flatnonzero(test_mask)
    if not train_groups:
        raise ValueError('no lensed training groups found')

    device = torch.device('cuda' if torch.cuda.is_available() and not args.cpu else 'cpu')
    torch.manual_seed(args.seed)
    model = WaveformMetricNet(dim=args.dim).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ds = PairBatchDataset(train_groups, train_singles, args.steps_per_epoch * args.epochs, args.pairs_per_batch, args.singles_per_batch, args.seed)
    dl = DataLoader(ds, batch_size=1, shuffle=False, num_workers=0, collate_fn=collate_index_batches)

    t0 = time.perf_counter()
    losses = []
    model.train()
    for step, batch_idx in enumerate(dl, start=1):
        xb = torch.from_numpy(x[batch_idx]).to(device, non_blocking=True)
        labels_np = sids[batch_idx]
        _, label_ids = np.unique(labels_np, return_inverse=True)
        yb = torch.from_numpy(label_ids.astype(np.int64)).to(device)
        opt.zero_grad(set_to_none=True)
        z = model(xb)
        loss = supcon_loss(z, yb, args.temperature)
        loss.backward()
        opt.step()
        losses.append(float(loss.detach().cpu()))
        if args.log_every and step % args.log_every == 0:
            print(json.dumps({'step': step, 'loss': float(np.mean(losses[-args.log_every:]))}), flush=True)
    train_s = time.perf_counter() - t0

    z_test = embed(model, x, test_indices, args.eval_batch_size, device)
    sids_test = sids[test_indices]
    neigh, neigh_scores = topk_neighbors(z_test, max(args.k, 10))
    ret = retrieval_metrics(neigh, sids_test)
    cand = candidate_edges_from_neighbors(neigh[:, :args.k], neigh_scores[:, :args.k])
    scores = lensgraph_scores(cand, z_test)
    system = best_system(scores, sids_test, len(test_indices))
    system.update({'auprc': auprc_from_scores(scores, sids_test), 'candidate_edges': len(scores)})

    summary = {
        'catalog_prefix': args.catalog_prefix,
        'dataset': args.dataset,
        'n_total': int(len(sids)),
        'n_train': int(train_mask.sum()),
        'n_test': int(test_mask.sum()),
        'train_lensed_sources': int(len(train_groups)),
        'train_singletons': int(len(train_singles)),
        'epochs': args.epochs,
        'steps_per_epoch': args.steps_per_epoch,
        'dim': args.dim,
        'train_s': train_s,
        'loss_final': float(np.mean(losses[-min(len(losses), args.steps_per_epoch):])),
        **ret,
    }
    pd.DataFrame([summary]).to_csv(Path(args.out_dir) / 'retrieval_summary.csv', index=False)
    pd.DataFrame([system]).to_csv(Path(args.out_dir) / 'system_summary.csv', index=False)
    with open(Path(args.out_dir) / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump({'retrieval': summary, 'system': system}, f, indent=2)
    torch.save({'model': model.state_dict(), 'args': vars(args)}, Path(args.out_dir) / 'model.pt')
    print(json.dumps({'retrieval': summary, 'system': system}, indent=2), flush=True)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description='Waveform-only supervised metric baseline with source-held-out evaluation.')
    ap.add_argument('--catalog-prefix', required=True)
    ap.add_argument('--dataset', default='peak_strain')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--train-frac', type=float, default=0.7)
    ap.add_argument('--epochs', type=int, default=8)
    ap.add_argument('--steps-per-epoch', type=int, default=120)
    ap.add_argument('--pairs-per-batch', type=int, default=96)
    ap.add_argument('--singles-per-batch', type=int, default=64)
    ap.add_argument('--eval-batch-size', type=int, default=1024)
    ap.add_argument('--dim', type=int, default=128)
    ap.add_argument('--k', type=int, default=10)
    ap.add_argument('--lr', type=float, default=3e-4)
    ap.add_argument('--weight-decay', type=float, default=1e-4)
    ap.add_argument('--temperature', type=float, default=0.08)
    ap.add_argument('--log-every', type=int, default=50)
    ap.add_argument('--cpu', action='store_true')
    args = ap.parse_args()
    run(args)


if __name__ == '__main__':
    main()
