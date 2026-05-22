from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

from .config import MatchRunConfig


@dataclass(slots=True)
class MatchArrays:
    l1: np.ndarray
    l2: np.ndarray
    unlensed: np.ndarray


def _load_npy_matrix(path: Path, limit: int | None = None) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)
    x = np.load(path, allow_pickle=True, mmap_mode="r")
    if limit is not None:
        x = x[:limit]
    return np.asarray(x, dtype=np.float32)


def load_match_arrays(cfg: MatchRunConfig) -> MatchArrays:
    return MatchArrays(
        l1=_load_npy_matrix(cfg.l1_path, cfg.lensed_limit),
        l2=_load_npy_matrix(cfg.l2_path, cfg.lensed_limit),
        unlensed=_load_npy_matrix(cfg.unlensed_path, cfg.unlensed_limit),
    )


def split_indices(n_lensed: int, n_unlensed: int, cfg: MatchRunConfig) -> dict[str, dict[str, np.ndarray]]:
    rng = np.random.default_rng(cfg.seed)
    l_perm = rng.permutation(n_lensed)
    u_perm = rng.permutation(n_unlensed)

    def split(perm: np.ndarray) -> dict[str, np.ndarray]:
        n_train = int(round(len(perm) * cfg.train_frac))
        n_val = int(round(len(perm) * cfg.val_frac))
        return {
            "train": perm[:n_train],
            "val": perm[n_train:n_train + n_val],
            "test": perm[n_train + n_val:],
        }

    return {"lensed": split(l_perm), "unlensed": split(u_perm)}


def pad_or_trim(x: np.ndarray, target_len: int, stride: int = 1) -> np.ndarray:
    n = x.shape[-1]
    if n >= target_len:
        y = x[..., -target_len:]
    else:
        shape = list(x.shape)
        shape[-1] = target_len
        y = np.zeros(tuple(shape), dtype=x.dtype)
        y[..., -n:] = x
    if stride > 1:
        y = y[..., ::stride]
    return y.astype(np.float32, copy=False)


def zscore(x: np.ndarray) -> np.ndarray:
    return ((x - x.mean()) / (x.std() + 1e-8)).astype(np.float32, copy=False)


def peak_flip(x: np.ndarray) -> np.ndarray:
    return -x if x[np.argmax(np.abs(x))] < 0 else x


def augment(x: np.ndarray, cfg: MatchRunConfig, rng: np.random.Generator) -> np.ndarray:
    y = x.copy()
    if cfg.aug_flip:
        y = peak_flip(y)
    if cfg.aug_roll > 0:
        y = np.roll(y, int(rng.integers(-cfg.aug_roll, cfg.aug_roll + 1)))
    if cfg.aug_scale > 0:
        y = y * float(1.0 + rng.uniform(-cfg.aug_scale, cfg.aug_scale))
    if cfg.aug_noise > 0:
        y = y + rng.normal(0.0, cfg.aug_noise * (float(y.std()) + 1e-8), size=y.shape)
    return zscore(y)


def to_channels(x: np.ndarray, use_hilbert: bool = False) -> np.ndarray:
    if use_hilbert:
        from scipy.signal import hilbert
        z = hilbert(x)
        return np.stack([z.real, z.imag], axis=0).astype(np.float32)
    return x[None, :].astype(np.float32)


class PairDataset(Dataset):
    def __init__(self, arrays: MatchArrays, lensed_idx: np.ndarray, unlensed_idx: np.ndarray, cfg: MatchRunConfig) -> None:
        self.arrays = arrays
        self.cfg = cfg
        self.items = [("L", int(i)) for i in lensed_idx] + [("U", int(i)) for i in unlensed_idx]
        self.rng = np.random.default_rng(cfg.seed)

    def __len__(self) -> int:
        return len(self.items)

    def _prepare(self, x: np.ndarray, train: bool) -> np.ndarray:
        y = pad_or_trim(x, self.cfg.target_len, self.cfg.stride)
        y = augment(y, self.cfg, self.rng) if train else zscore(peak_flip(y) if self.cfg.aug_flip else y)
        return to_channels(y, self.cfg.use_hilbert)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        kind, src_idx = self.items[idx]
        if kind == "L":
            a = self._prepare(self.arrays.l1[src_idx], train=True)
            b = self._prepare(self.arrays.l2[src_idx], train=True)
        else:
            a = self._prepare(self.arrays.unlensed[src_idx], train=True)
            b = self._prepare(self.arrays.unlensed[src_idx], train=True)
        return torch.from_numpy(a), torch.from_numpy(b)


class EvaluationSet(Dataset):
    def __init__(self, arrays: MatchArrays, lensed_idx: np.ndarray, unlensed_idx: np.ndarray, cfg: MatchRunConfig) -> None:
        self.cfg = cfg
        self.waveforms = [arrays.l1[int(i)] for i in lensed_idx]
        self.waveforms.extend(arrays.l2[int(i)] for i in lensed_idx)
        self.waveforms.extend(arrays.unlensed[int(i)] for i in unlensed_idx)
        self.meta = []
        for local, original in enumerate(lensed_idx):
            self.meta.append({"tag": "L1", "pair_id": int(local), "source_index": int(original)})
        for local, original in enumerate(lensed_idx):
            self.meta.append({"tag": "L2", "pair_id": int(local), "source_index": int(original)})
        for local, original in enumerate(unlensed_idx):
            self.meta.append({"tag": "U", "pair_id": -1, "source_index": int(original)})

    def __len__(self) -> int:
        return len(self.waveforms)

    def __getitem__(self, idx: int) -> torch.Tensor:
        x = pad_or_trim(self.waveforms[idx], self.cfg.target_len, self.cfg.stride)
        if self.cfg.aug_flip:
            x = peak_flip(x)
        return torch.from_numpy(to_channels(zscore(x), self.cfg.use_hilbert))


def ground_truth_partner(meta: list[dict]) -> np.ndarray:
    gt = np.full(len(meta), -1, dtype=np.int64)
    l1_by_pair = {m["pair_id"]: i for i, m in enumerate(meta) if m["tag"] == "L1"}
    l2_by_pair = {m["pair_id"]: i for i, m in enumerate(meta) if m["tag"] == "L2"}
    for pair_id, i in l1_by_pair.items():
        j = l2_by_pair.get(pair_id)
        if j is not None:
            gt[i] = j
            gt[j] = i
    return gt
