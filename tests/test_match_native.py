from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from lensgraph.catalog_io import load_catalog
from lensgraph.data.match_native import MatchNativeConfig, build_match_native_catalog


def _write_match_fixture(root: Path, n: int = 4, length: int = 256) -> None:
    rng = np.random.default_rng(7)
    sis = root / 'SIS_data_0222'
    unl = root / 'Unlensed_data_0222'
    sis.mkdir(parents=True)
    unl.mkdir(parents=True)
    x = rng.normal(size=(n, length)).astype(np.float64)
    y = np.roll(x, 5, axis=1) * 0.8
    u = rng.normal(size=(n, length)).astype(np.float64)
    np.save(sis / 'SIS_data_strain_1.npy', x)
    np.save(sis / 'SIS_data_strain_2.npy', y)
    np.save(unl / 'unlensed_data_strain.npy', u)
    pd.DataFrame({'mu_0': np.ones(n) * 2, 'mu_1': np.ones(n), 't_d': np.arange(n)}).to_csv(sis / 'lens.csv', index=False)
    pd.DataFrame({'sigma_v': np.ones(n) * 220}).to_csv(sis / 'lens_params.csv', index=False)
    pd.DataFrame({'mass_1_source': np.ones(n) * 30, 'mass_2_source': np.ones(n) * 25}).to_csv(sis / 'source_samples.csv', index=False)
    pd.DataFrame({'mass_1_source': np.ones(n) * 35, 'mass_2_source': np.ones(n) * 20}).to_csv(unl / 'source_samples.csv', index=False)


def test_build_match_native_catalog(tmp_path: Path) -> None:
    data_root = tmp_path / 'qkzhang'
    _write_match_fixture(data_root)
    cfg = MatchNativeConfig(
        data_root=data_root,
        family='SIS',
        mode='noisy',
        output_prefix=tmp_path / 'out' / 'match_sis_noisy',
        n_lensed=3,
        n_unlensed=2,
        sample_rate=256.0,
        bandpass_low_hz=5.0,
        bandpass_high_hz=60.0,
        target_len=128,
        stride=2,
        peak_start=30,
        peak_stop=50,
        chunk_size=2,
    )
    h5_path, meta_path = build_match_native_catalog(cfg)
    assert h5_path.exists()
    assert meta_path.exists()

    full, meta = load_catalog(tmp_path / 'out' / 'match_sis_noisy')
    peak, _ = load_catalog(tmp_path / 'out' / 'match_sis_noisy', dataset='peak_strain')
    assert full.shape == (8, 64)
    assert peak.shape == (8, 20)
    assert meta.groupby('source_id').size().value_counts().to_dict() == {2: 3, 1: 2}
    assert list(meta.iloc[[0, 3, 6]]['image_index']) == [0, 1, 0]
