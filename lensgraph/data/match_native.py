from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Literal

import h5py
import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt

MatchFamily = Literal['SIS', 'PM']
MatchMode = Literal['pure', 'noisy']


@dataclass(frozen=True)
class MatchNativeConfig:
    """Configuration for converting match-generated arrays to gw-catalog.

    The match generation scripts create 24 s, 4096 Hz arrays with the merger
    peak aligned close to the end of the record. The gw-catalog representation
    keeps a full 4096-sample strain view for compatibility and a shorter
    peak-window view for noisy retrieval/model training.
    """

    data_root: Path = Path('/root/autodl-tmp/qkzhang')
    family: MatchFamily = 'SIS'
    mode: MatchMode = 'noisy'
    output_prefix: Path = Path('catalogs/match_native/match_sis_noisy')
    n_lensed: int | None = None
    n_unlensed: int | None = None
    sample_rate: float = 4096.0
    bandpass_low_hz: float = 20.0
    bandpass_high_hz: float = 500.0
    target_len: int = 8192
    stride: int = 2
    peak_start: int = 3000
    peak_stop: int = 3800
    chunk_size: int = 64
    compression: str | None = 'gzip'
    compression_opts: int | None = 4

    @property
    def full_len(self) -> int:
        return int(math.ceil(self.target_len / self.stride))

    @property
    def peak_len(self) -> int:
        return self.peak_stop - self.peak_start


def match_paths(data_root: Path, family: str, mode: str) -> dict[str, Path]:
    family = family.upper()
    mode = mode.lower()
    if family not in {'SIS', 'PM'}:
        raise ValueError(f'family must be SIS or PM, got {family}')
    if mode not in {'pure', 'noisy'}:
        raise ValueError(f'mode must be pure or noisy, got {mode}')

    strain_tag = 'h_strain' if mode == 'pure' else 'data_strain'
    unl_tag = 'unlensed_h_strain' if mode == 'pure' else 'unlensed_data_strain'
    family_dir = data_root / f'{family}_data_0222'
    unlensed_dir = data_root / 'Unlensed_data_0222'
    return {
        'l1': family_dir / f'{family}_{strain_tag}_1.npy',
        'l2': family_dir / f'{family}_{strain_tag}_2.npy',
        'u': unlensed_dir / f'{unl_tag}.npy',
        'lens': family_dir / 'lens.csv',
        'lens_params': family_dir / 'lens_params.csv',
        'source': family_dir / 'source_samples.csv',
        'unlensed_source': unlensed_dir / 'source_samples.csv',
    }


def _read_csv(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def _row_value(frame: pd.DataFrame | None, idx: int, key: str, default=None):
    if frame is None or key not in frame.columns or idx >= len(frame):
        return default
    value = frame.iloc[idx][key]
    if pd.isna(value):
        return default
    return value.item() if isinstance(value, np.generic) else value


def _intrinsic_json(frame: pd.DataFrame | None, idx: int) -> str:
    if frame is None or idx >= len(frame):
        return '{}'
    clean = {}
    for key, value in frame.iloc[idx].to_dict().items():
        if pd.isna(value):
            continue
        clean[key] = value.item() if isinstance(value, np.generic) else value
    return json.dumps(clean, sort_keys=True)


def _bandpass_sos(cfg: MatchNativeConfig):
    nyq = cfg.sample_rate / 2.0
    return butter(
        4,
        [cfg.bandpass_low_hz / nyq, cfg.bandpass_high_hz / nyq],
        btype='band',
        output='sos',
    )


def preprocess_match_chunk(raw: np.ndarray, cfg: MatchNativeConfig, sos) -> tuple[np.ndarray, np.ndarray]:
    """Return full 4096-sample and peak-window views for one chunk."""
    x = np.asarray(raw, dtype=np.float32)
    x = sosfiltfilt(sos, x, axis=1).astype(np.float32, copy=False)
    x = x[:, -cfg.target_len:]
    if cfg.stride > 1:
        x = x[:, ::cfg.stride]
    x = x - x.mean(axis=1, keepdims=True)
    peak = x[:, cfg.peak_start:cfg.peak_stop]
    return x.astype(np.float32, copy=False), peak.astype(np.float32, copy=False)


def _metadata_rows(cfg: MatchNativeConfig, n_lensed: int, n_unlensed: int, paths: dict[str, Path]) -> pd.DataFrame:
    lens = _read_csv(paths['lens'])
    lens_params = _read_csv(paths['lens_params'])
    source = _read_csv(paths['source'])
    unlensed_source = _read_csv(paths['unlensed_source'])
    family = cfg.family.upper()
    mode = cfg.mode.lower()
    strain_tag = 'h_strain' if mode == 'pure' else 'data_strain'
    prefix = f'MATCH-{family}-{mode.upper()}'

    common = []
    for idx in range(n_lensed):
        common.append({
            'source_id': f'{prefix}-LENS-{idx:08d}',
            'system_type': 'doublet',
            'lens_family': family,
            'lens_mass_msun': _row_value(lens_params, idx, 'm_l', None),
            'sigma_v_km_s': _row_value(lens_params, idx, 'sigma_v', None),
            'match_index': idx,
            'data_mode': mode,
            'intrinsic_params': _intrinsic_json(source, idx),
            'mu0': float(abs(_row_value(lens, idx, 'mu_0', 1.0))),
            'mu1': float(abs(_row_value(lens, idx, 'mu_1', 1.0))),
            'td': float(_row_value(lens, idx, 't_d', 0.0)),
        })

    rows = []
    for idx, row in enumerate(common):
        base = {k: v for k, v in row.items() if k not in {'mu0', 'mu1', 'td'}}
        rows.append({
            **base,
            'event_id': f'{prefix}-EVT-L1-{idx:08d}',
            'image_index': 0,
            'magnification': row['mu0'],
            'time_delay': 0.0,
            'morse_phase': 0.0,
            'origin_file': f'{family}_{strain_tag}_1.npy',
        })
    for idx, row in enumerate(common):
        base = {k: v for k, v in row.items() if k not in {'mu0', 'mu1', 'td'}}
        rows.append({
            **base,
            'event_id': f'{prefix}-EVT-L2-{idx:08d}',
            'image_index': 1,
            'magnification': row['mu1'],
            'time_delay': row['td'],
            'morse_phase': math.pi / 2,
            'origin_file': f'{family}_{strain_tag}_2.npy',
        })
    for idx in range(n_unlensed):
        rows.append({
            'event_id': f'{prefix}-EVT-U-{idx:08d}',
            'source_id': f'{prefix}-UNL-{idx:08d}',
            'system_type': 'isolated',
            'image_index': 0,
            'magnification': 1.0,
            'time_delay': 0.0,
            'morse_phase': 0.0,
            'lens_family': 'none',
            'lens_mass_msun': None,
            'sigma_v_km_s': None,
            'match_index': idx,
            'data_mode': mode,
            'origin_file': f'unlensed_{strain_tag}.npy',
            'intrinsic_params': _intrinsic_json(unlensed_source, idx),
        })
    return pd.DataFrame(rows)


def _write_source(src: np.ndarray, full_ds, peak_ds, src_start: int, out_start: int, count: int, cfg: MatchNativeConfig, sos) -> int:
    written = 0
    while written < count:
        n = min(cfg.chunk_size, count - written)
        full, peak = preprocess_match_chunk(src[src_start + written:src_start + written + n], cfg, sos)
        full_ds[out_start + written:out_start + written + n] = full
        peak_ds[out_start + written:out_start + written + n] = peak
        written += n
    return out_start + count


def build_match_native_catalog(cfg: MatchNativeConfig) -> tuple[Path, Path]:
    paths = match_paths(cfg.data_root, cfg.family, cfg.mode)
    for key in ('l1', 'l2', 'u'):
        if not paths[key].exists():
            raise FileNotFoundError(paths[key])

    l1 = np.load(paths['l1'], mmap_mode='r')
    l2 = np.load(paths['l2'], mmap_mode='r')
    u = np.load(paths['u'], mmap_mode='r')
    n_lensed = min(l1.shape[0], l2.shape[0], cfg.n_lensed if cfg.n_lensed is not None else l1.shape[0])
    n_unlensed = min(u.shape[0], cfg.n_unlensed if cfg.n_unlensed is not None else u.shape[0])
    n_total = 2 * n_lensed + n_unlensed

    cfg.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    h5_path = cfg.output_prefix.with_suffix('.h5')
    meta_path = cfg.output_prefix.parent / f'{cfg.output_prefix.name}_metadata.parquet'
    sos = _bandpass_sos(cfg)

    with h5py.File(h5_path, 'w') as h5:
        kwargs = {}
        if cfg.compression:
            kwargs.update(compression=cfg.compression, compression_opts=cfg.compression_opts, shuffle=True)
        chunk_n = min(cfg.chunk_size, n_total)
        full_ds = h5.create_dataset('strain', shape=(n_total, cfg.full_len), dtype='float32', chunks=(chunk_n, cfg.full_len), **kwargs)
        peak_ds = h5.create_dataset('peak_strain', shape=(n_total, cfg.peak_len), dtype='float32', chunks=(chunk_n, cfg.peak_len), **kwargs)
        pos = 0
        pos = _write_source(l1, full_ds, peak_ds, 0, pos, n_lensed, cfg, sos)
        pos = _write_source(l2, full_ds, peak_ds, 0, pos, n_lensed, cfg, sos)
        pos = _write_source(u, full_ds, peak_ds, 0, pos, n_unlensed, cfg, sos)
        h5.create_dataset('event_id', data=[f'{cfg.output_prefix.name}-{i:08d}'.encode() for i in range(n_total)])
        h5.attrs.update({
            'builder': 'lensgraph.data.match_native',
            'source_data_root': str(cfg.data_root),
            'family': cfg.family.upper(),
            'mode': cfg.mode.lower(),
            'sample_rate': cfg.sample_rate,
            'bandpass_low_hz': cfg.bandpass_low_hz,
            'bandpass_high_hz': cfg.bandpass_high_hz,
            'target_len': cfg.target_len,
            'stride': cfg.stride,
            'peak_start': cfg.peak_start,
            'peak_stop': cfg.peak_stop,
        })

    meta = _metadata_rows(cfg, n_lensed, n_unlensed, paths)
    meta.to_parquet(meta_path, index=False)
    return h5_path, meta_path
