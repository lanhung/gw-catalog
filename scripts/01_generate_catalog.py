from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import h5py
import yaml
import numpy as np
import pandas as pd
from collections import Counter

from lensgraph.data.catalog_simulator import CatalogConfig, generate_catalog


def main(config_path: str) -> None:
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    output_prefix = raw.pop("output_prefix")
    cfg = CatalogConfig(**raw)
    events = generate_catalog(cfg)

    os.makedirs(os.path.dirname(output_prefix), exist_ok=True)
    h5_path = f"{output_prefix}.h5"
    meta_path = f"{output_prefix}_metadata.parquet"

    strains = np.stack([e["strain"] for e in events]).astype(np.float32, copy=False)
    with h5py.File(h5_path, "w") as h5:
        h5.create_dataset("strain", data=strains, chunks=True)
        h5.create_dataset("event_id", data=[e["event_id"].encode() for e in events])

    rows = []
    for e in events:
        row = {k: v for k, v in e.items() if k != "strain"}
        row["intrinsic_params"] = str(row["intrinsic_params"])
        rows.append(row)

    metadata = pd.DataFrame(rows)
    try:
        metadata.to_parquet(meta_path, index=False)
    except ImportError:
        meta_path = f"{output_prefix}_metadata.csv"
        metadata.to_csv(meta_path, index=False)

    n_lensed = sum(e["system_type"] != "isolated" for e in events)
    prevalence = n_lensed / len(events)
    hist = Counter(e["system_type"] for e in events)
    print(f"events={len(events)}")
    print(f"lensed_events={n_lensed}, prevalence={prevalence:.4f}")
    print(f"system_hist={dict(hist)}")
    print(f"h5={h5_path}")
    print(f"metadata={meta_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    main(args.config)
