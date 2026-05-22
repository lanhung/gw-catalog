from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import h5py
import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt


FAMILIES = ("SIS", "PM")
MODES = ("pure", "noisy")


def _paths(data_root: Path, family: str, mode: str) -> dict[str, Path]:
    family = family.upper()
    mode = mode.lower()
    strain_tag = "h_strain" if mode == "pure" else "data_strain"
    unl_tag = "unlensed_h_strain" if mode == "pure" else "unlensed_data_strain"
    fam_dir = data_root / f"{family}_data_0222"
    unl_dir = data_root / "Unlensed_data_0222"
    return {
        "l1": fam_dir / f"{family}_{strain_tag}_1.npy",
        "l2": fam_dir / f"{family}_{strain_tag}_2.npy",
        "u": unl_dir / f"{unl_tag}.npy",
        "lens": fam_dir / "lens.csv",
        "lens_params": fam_dir / "lens_params.csv",
        "source": fam_dir / "source_samples.csv",
        "unl_source": unl_dir / "source_samples.csv",
    }


def _read_optional_csv(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def _make_sos(sample_rate: float, low_hz: float, high_hz: float):
    nyq = sample_rate / 2.0
    return butter(4, [low_hz / nyq, high_hz / nyq], btype="band", output="sos")


def _preprocess_chunk(
    chunk: np.ndarray,
    *,
    target_len: int,
    stride: int,
    sos,
    bandpass: bool,
) -> np.ndarray:
    x = np.asarray(chunk, dtype=np.float32)
    if bandpass:
        x = sosfiltfilt(sos, x, axis=1).astype(np.float32, copy=False)
    if target_len > 0:
        x = x[:, -target_len:]
    if stride > 1:
        x = x[:, ::stride]
    x = x - x.mean(axis=1, keepdims=True)
    return x.astype(np.float32, copy=False)


def _write_chunks(
    out_ds,
    src: np.ndarray,
    src_start: int,
    out_start: int,
    count: int,
    *,
    chunk_size: int,
    target_len: int,
    stride: int,
    sos,
    bandpass: bool,
) -> int:
    written = 0
    while written < count:
        n = min(chunk_size, count - written)
        raw = src[src_start + written: src_start + written + n]
        out = _preprocess_chunk(raw, target_len=target_len, stride=stride, sos=sos, bandpass=bandpass)
        out_ds[out_start + written: out_start + written + n] = out
        written += n
    return out_start + count


def _row_value(frame: pd.DataFrame | None, idx: int, key: str, default=None):
    if frame is None or key not in frame.columns or idx >= len(frame):
        return default
    value = frame.iloc[idx][key]
    if pd.isna(value):
        return default
    if isinstance(value, np.generic):
        return value.item()
    return value


def _intrinsic_json(frame: pd.DataFrame | None, idx: int) -> str:
    if frame is None or idx >= len(frame):
        return "{}"
    row = frame.iloc[idx].to_dict()
    clean = {}
    for k, v in row.items():
        if pd.isna(v):
            continue
        clean[k] = v.item() if isinstance(v, np.generic) else v
    return json.dumps(clean, sort_keys=True)


def _metadata_rows(
    *,
    family: str,
    mode: str,
    n_lensed: int,
    n_unlensed: int,
    lens: pd.DataFrame | None,
    lens_params: pd.DataFrame | None,
    source: pd.DataFrame | None,
    unl_source: pd.DataFrame | None,
) -> list[dict]:
    rows: list[dict] = []
    prefix = f"MATCH-{family.upper()}-{mode.upper()}"
    strain_tag = "h_strain" if mode == "pure" else "data_strain"

    common_rows = []
    for idx in range(n_lensed):
        mu0 = float(abs(_row_value(lens, idx, "mu_0", 1.0)))
        mu1 = float(abs(_row_value(lens, idx, "mu_1", 1.0)))
        td = float(_row_value(lens, idx, "t_d", 0.0))
        lens_mass = _row_value(lens_params, idx, "m_l", None)
        sigma_v = _row_value(lens_params, idx, "sigma_v", None)
        common_rows.append({
            "source_id": f"{prefix}-LENS-{idx:08d}",
            "system_type": "doublet",
            "lens_family": family.upper(),
            "lens_mass_msun": lens_mass,
            "sigma_v_km_s": sigma_v,
            "match_index": idx,
            "data_mode": mode.lower(),
            "intrinsic_params": _intrinsic_json(source, idx),
            "mu0": mu0,
            "mu1": mu1,
            "td": td,
        })

    # Metadata order must match HDF5 strain order exactly: all L1, then all L2, then all unlensed.
    for idx, common in enumerate(common_rows):
        rows.append({
            **{k: v for k, v in common.items() if k not in ("mu0", "mu1", "td")},
            "event_id": f"{prefix}-EVT-L1-{idx:08d}",
            "image_index": 0,
            "magnification": common["mu0"],
            "time_delay": 0.0,
            "morse_phase": 0.0,
            "origin_file": f"{family.upper()}_{strain_tag}_1.npy",
        })
    for idx, common in enumerate(common_rows):
        rows.append({
            **{k: v for k, v in common.items() if k not in ("mu0", "mu1", "td")},
            "event_id": f"{prefix}-EVT-L2-{idx:08d}",
            "image_index": 1,
            "magnification": common["mu1"],
            "time_delay": common["td"],
            "morse_phase": math.pi / 2,
            "origin_file": f"{family.upper()}_{strain_tag}_2.npy",
        })
    for idx in range(n_unlensed):
        rows.append({
            "event_id": f"{prefix}-EVT-U-{idx:08d}",
            "source_id": f"{prefix}-UNL-{idx:08d}",
            "system_type": "isolated",
            "image_index": 0,
            "magnification": 1.0,
            "time_delay": 0.0,
            "morse_phase": 0.0,
            "lens_family": "none",
            "lens_mass_msun": None,
            "sigma_v_km_s": None,
            "match_index": idx,
            "data_mode": mode.lower(),
            "origin_file": f"unlensed_{strain_tag}.npy",
            "intrinsic_params": _intrinsic_json(unl_source, idx),
        })
    return rows

def convert_one(
    *,
    data_root: Path,
    out_prefix: Path,
    family: str,
    mode: str,
    limit: int | None,
    unlensed_limit: int | None,
    target_len: int,
    stride: int,
    sample_rate: float,
    bandpass: bool,
    chunk_size: int,
) -> None:
    p = _paths(data_root, family, mode)
    for key in ("l1", "l2", "u"):
        if not p[key].exists():
            raise FileNotFoundError(p[key])

    l1 = np.load(p["l1"], mmap_mode="r")
    l2 = np.load(p["l2"], mmap_mode="r")
    u = np.load(p["u"], mmap_mode="r")
    n_lensed = min(l1.shape[0], l2.shape[0], limit if limit is not None else l1.shape[0])
    n_unlensed = min(u.shape[0], unlensed_limit if unlensed_limit is not None else u.shape[0])
    out_len = int(math.ceil(target_len / stride)) if target_len > 0 else int(math.ceil(l1.shape[1] / stride))
    n_total = 2 * n_lensed + n_unlensed

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    h5_path = out_prefix.with_suffix(".h5")
    meta_path = out_prefix.parent / f"{out_prefix.name}_metadata.parquet"

    sos = _make_sos(sample_rate, 20.0, 500.0)
    print(f"[convert] {family} {mode}: lensed={n_lensed}, unlensed={n_unlensed}, out=({n_total},{out_len}), bandpass={bandpass}", flush=True)

    with h5py.File(h5_path, "w") as h5:
        strain = h5.create_dataset(
            "strain",
            shape=(n_total, out_len),
            dtype="float32",
            chunks=(min(chunk_size, n_total), out_len),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )
        pos = 0
        pos = _write_chunks(strain, l1, 0, pos, n_lensed, chunk_size=chunk_size, target_len=target_len, stride=stride, sos=sos, bandpass=bandpass)
        pos = _write_chunks(strain, l2, 0, pos, n_lensed, chunk_size=chunk_size, target_len=target_len, stride=stride, sos=sos, bandpass=bandpass)
        pos = _write_chunks(strain, u, 0, pos, n_unlensed, chunk_size=chunk_size, target_len=target_len, stride=stride, sos=sos, bandpass=bandpass)

        event_ids = [f"{out_prefix.name}-{i:08d}".encode() for i in range(n_total)]
        h5.create_dataset("event_id", data=event_ids)
        h5.attrs["source_data_root"] = str(data_root)
        h5.attrs["family"] = family.upper()
        h5.attrs["mode"] = mode.lower()
        h5.attrs["target_len"] = target_len
        h5.attrs["stride"] = stride
        h5.attrs["bandpass_20_500_hz"] = bool(bandpass)

    meta = pd.DataFrame(_metadata_rows(
        family=family,
        mode=mode,
        n_lensed=n_lensed,
        n_unlensed=n_unlensed,
        lens=_read_optional_csv(p["lens"]),
        lens_params=_read_optional_csv(p["lens_params"]),
        source=_read_optional_csv(p["source"]),
        unl_source=_read_optional_csv(p["unl_source"]),
    ))
    meta.to_parquet(meta_path, index=False)
    print(f"[done] h5={h5_path} metadata={meta_path}", flush=True)


def _expand(value: str, allowed: Iterable[str]) -> list[str]:
    value = value.lower()
    allowed_list = list(allowed)
    if value == "all":
        return allowed_list
    for item in allowed_list:
        if value == item.lower():
            return [item]
    raise ValueError(f"expected one of {allowed_list} or all, got {value}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert match qkzhang .npy arrays into gw-catalog HDF5/parquet catalogs.")
    ap.add_argument("--data-root", default="/root/autodl-tmp/qkzhang")
    ap.add_argument("--out-dir", default="catalogs")
    ap.add_argument("--family", default="all", choices=["SIS", "PM", "sis", "pm", "all"])
    ap.add_argument("--mode", default="all", choices=["pure", "noisy", "all"])
    ap.add_argument("--limit", type=int, default=None, help="number of lensed pairs to include")
    ap.add_argument("--unlensed-limit", type=int, default=None, help="number of isolated events to include")
    ap.add_argument("--target-len", type=int, default=8192)
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--sample-rate", type=float, default=4096.0)
    ap.add_argument("--no-bandpass", action="store_true")
    ap.add_argument("--chunk-size", type=int, default=64)
    args = ap.parse_args()

    data_root = Path(args.data_root)
    out_dir = Path(args.out_dir)
    for family in _expand(args.family, FAMILIES):
        for mode in _expand(args.mode, MODES):
            name = f"match_{family.lower()}_{mode.lower()}"
            convert_one(
                data_root=data_root,
                out_prefix=out_dir / name,
                family=family,
                mode=mode,
                limit=args.limit,
                unlensed_limit=args.unlensed_limit,
                target_len=args.target_len,
                stride=args.stride,
                sample_rate=args.sample_rate,
                bandpass=not args.no_bandpass,
                chunk_size=args.chunk_size,
            )


if __name__ == "__main__":
    main()
