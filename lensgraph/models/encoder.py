from __future__ import annotations

from dataclasses import dataclass
import numpy as np


def l2_normalize(x: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    norm = np.linalg.norm(x, axis=1, keepdims=True)
    return (x / np.maximum(norm, eps)).astype(np.float32, copy=False)


@dataclass
class SpectralFeatureEncoder:
    """Deterministic encoder for the current simulator.

    The simulator creates lensed images by circularly shifting and scaling a
    shared base strain. A normalized Fourier-magnitude embedding is invariant
    to both operations, which makes it a useful non-neural reference for the
    LensGraph retrieval math while the trainable PI-ResNet encoder is added.
    """

    dim: int = 128
    log_scale: bool = True

    def transform(self, strains: np.ndarray) -> np.ndarray:
        x = strains.astype(np.float32, copy=False)
        x = x - x.mean(axis=1, keepdims=True)
        x = x / np.maximum(x.std(axis=1, keepdims=True), 1e-6)
        spec = np.abs(np.fft.rfft(x, axis=1)).astype(np.float32)
        spec[:, 0] = 0.0
        if self.log_scale:
            spec = np.log1p(spec)
        # Average contiguous frequency bins into dim features.
        edges = np.linspace(0, spec.shape[1], self.dim + 1, dtype=int)
        feats = np.empty((spec.shape[0], self.dim), dtype=np.float32)
        for i in range(self.dim):
            lo, hi = int(edges[i]), int(edges[i + 1])
            if hi <= lo:
                hi = min(lo + 1, spec.shape[1])
            feats[:, i] = spec[:, lo:hi].mean(axis=1)
        feats = feats - feats.mean(axis=1, keepdims=True)
        return l2_normalize(feats)


@dataclass
class RandomProjectionEncoder:
    """Ablation encoder: random projection of normalized strain."""

    dim: int = 128
    seed: int = 0

    def transform(self, strains: np.ndarray) -> np.ndarray:
        x = strains.astype(np.float32, copy=False)
        x = x - x.mean(axis=1, keepdims=True)
        x = x / np.maximum(x.std(axis=1, keepdims=True), 1e-6)
        rng = np.random.default_rng(self.seed)
        proj = rng.normal(0.0, 1.0 / np.sqrt(x.shape[1]), size=(x.shape[1], self.dim)).astype(np.float32)
        return l2_normalize(x @ proj)


@dataclass
class MatchWindowSpectralEncoder:
    """Spectral encoder tuned for match-derived catalogs.

    The match data-generation scripts align the merger peak near the end of the
    cropped 4096-sample window. For noisy strains, full-window Fourier magnitudes
    are dominated by detector noise. This encoder therefore uses a fixed
    peak-neighbourhood window and optionally subtracts a robust catalog-level
    background spectrum. In ``auto`` mode it keeps the original full-window
    spectral encoder for pure-signal catalogs and switches to the peak-window
    encoder for noisy catalogs.
    """

    dim: int = 128
    window_start: int = 3000
    window_stop: int = 3800
    log_scale: bool = True
    noise_subtract: bool = True
    background: str = 'catalog'
    auto_mode: bool = True

    def _is_pure_catalog(self, meta) -> bool:
        if meta is None or 'data_mode' not in meta:
            return False
        modes = set(meta['data_mode'].astype(str).str.lower().unique())
        return modes == {'pure'}

    def _spectral(self, strains: np.ndarray, meta=None) -> np.ndarray:
        # ``peak_strain`` catalogs are already cropped; full ``strain`` catalogs
        # still need the match peak-neighbourhood window.
        if strains.shape[1] <= self.window_start:
            x = strains.astype(np.float32, copy=False)
        else:
            stop = min(self.window_stop, strains.shape[1])
            x = strains[:, self.window_start:stop].astype(np.float32, copy=False)
        if x.shape[1] == 0:
            raise ValueError('empty spectral window; check input length and window settings')
        x = x - x.mean(axis=1, keepdims=True)
        x = x / np.maximum(x.std(axis=1, keepdims=True), 1e-6)
        spec = np.abs(np.fft.rfft(x, axis=1)).astype(np.float32)
        spec[:, 0] = 0.0
        if self.noise_subtract:
            if self.background == 'catalog':
                bg = np.median(spec, axis=0, keepdims=True).astype(np.float32)
                spec = np.maximum(spec - bg, 0.0)
            elif self.background == 'isolated' and meta is not None and 'system_type' in meta:
                isolated = meta['system_type'].astype(str).to_numpy() == 'isolated'
                if np.any(isolated):
                    bg = np.median(spec[isolated], axis=0, keepdims=True).astype(np.float32)
                    spec = np.maximum(spec - bg, 0.0)
            elif self.background in {'none', None}:
                pass
            else:
                raise ValueError(f'unknown background mode: {self.background!r}')
        if self.log_scale:
            spec = np.log1p(spec)
        edges = np.linspace(0, spec.shape[1], self.dim + 1, dtype=int)
        feats = np.empty((spec.shape[0], self.dim), dtype=np.float32)
        for i in range(self.dim):
            lo, hi = int(edges[i]), int(edges[i + 1])
            if hi <= lo:
                hi = min(lo + 1, spec.shape[1])
            feats[:, i] = spec[:, lo:hi].mean(axis=1)
        feats = feats - feats.mean(axis=1, keepdims=True)
        return l2_normalize(feats)

    def transform(self, strains: np.ndarray, meta=None) -> np.ndarray:
        if self.auto_mode and self._is_pure_catalog(meta):
            return SpectralFeatureEncoder(dim=self.dim, log_scale=self.log_scale).transform(strains)
        return self._spectral(strains, meta=meta)
