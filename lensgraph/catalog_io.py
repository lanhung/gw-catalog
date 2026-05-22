from __future__ import annotations

from pathlib import Path
import h5py
import numpy as np
import pandas as pd


def load_catalog(prefix: str | Path, dataset: str = 'strain') -> tuple[np.ndarray, pd.DataFrame]:
    """Load a strain matrix and metadata written by catalog builders.

    Parameters
    ----------
    prefix:
        Catalog prefix without suffix.
    dataset:
        HDF5 dataset name to load. Standard catalogs use ``strain``;
        match-native catalogs also provide ``peak_strain``.
    """
    prefix = Path(prefix)
    h5_path = prefix.with_suffix('.h5')
    parquet_path = prefix.parent / f"{prefix.name}_metadata.parquet"
    csv_path = prefix.parent / f"{prefix.name}_metadata.csv"
    if not h5_path.exists():
        raise FileNotFoundError(h5_path)
    if parquet_path.exists():
        meta = pd.read_parquet(parquet_path)
    elif csv_path.exists():
        meta = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(f"metadata not found for prefix {prefix}")
    with h5py.File(h5_path, 'r') as h5:
        if dataset not in h5:
            raise KeyError(f"dataset {dataset!r} not found in {h5_path}; available={list(h5.keys())}")
        strains = h5[dataset][:].astype(np.float32, copy=False)
    return strains, meta


def source_ids(meta: pd.DataFrame) -> np.ndarray:
    return meta['source_id'].astype(str).to_numpy()


def lensed_mask(meta: pd.DataFrame) -> np.ndarray:
    sizes = meta.groupby('source_id')['event_id'].transform('size').to_numpy()
    return sizes >= 2
