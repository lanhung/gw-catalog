from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from lensgraph.catalog_io import load_catalog, source_ids
from lensgraph.models.encoder import MatchWindowSpectralEncoder, SpectralFeatureEncoder
from lensgraph.retrieval.ann_index import topk_neighbors, retrieval_metrics


def _encoder(name: str, dim: int):
    if name == "spectral":
        return SpectralFeatureEncoder(dim=dim)
    if name == "match-window":
        return MatchWindowSpectralEncoder(dim=dim, auto_mode=False)
    if name == "match-auto":
        return MatchWindowSpectralEncoder(dim=dim, auto_mode=True)
    raise ValueError(name)


def run(prefix: str, out_dir: str, k: int, dim: int, encoder_name: str, dataset: str = "strain") -> dict:
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.perf_counter()
    strains, meta = load_catalog(prefix, dataset=dataset)
    load_s = time.perf_counter() - t0
    sids = source_ids(meta)

    t1 = time.perf_counter()
    z = _encoder(encoder_name, dim).transform(strains, meta=meta) if encoder_name != "spectral" else _encoder(encoder_name, dim).transform(strains)
    encode_s = time.perf_counter() - t1

    t2 = time.perf_counter()
    neigh, _scores = topk_neighbors(z, max(k, 10))
    retrieval_s = time.perf_counter() - t2
    ret = retrieval_metrics(neigh, sids)

    row = {
        "catalog_prefix": prefix,
        "n": len(meta),
        "k": k,
        "dim": dim,
        "encoder": encoder_name,
        "dataset": dataset,
        "load_s": load_s,
        "encode_s": encode_s,
        "retrieval_s": retrieval_s,
        "total_runtime_s": load_s + encode_s + retrieval_s,
        **ret,
    }
    out = Path(out_dir)
    pd.DataFrame([row]).to_csv(out / "retrieval_only_summary.csv", index=False)
    with open(out / "retrieval_only_summary.json", "w", encoding="utf-8") as f:
        json.dump(row, f, indent=2)
    print(json.dumps(row, indent=2), flush=True)
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog-prefix", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--dim", type=int, default=128)
    ap.add_argument("--encoder", choices=["spectral", "match-window", "match-auto"], default="spectral")
    ap.add_argument("--dataset", default="strain", help="HDF5 dataset to load, e.g. strain or peak_strain")
    args = ap.parse_args()
    run(args.catalog_prefix, args.out_dir, args.k, args.dim, args.encoder, args.dataset)


if __name__ == "__main__":
    main()
