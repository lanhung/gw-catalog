"""Extract O4a (GWTC-4.0) BBH observables in the same format as GWTC-5.0.

Run on a machine that can reach zenodo.org and gwosc.org (the GPU server):

  python scripts/gwtc/01c_extract_gwtc4_observables.py --dry-run
  python scripts/gwtc/01c_extract_gwtc4_observables.py
  python scripts/gwtc/05_catalog_context_for_pair_verification.py \
      --out runs/gwtc_catalog_context_with_o4a

The output ``data/gwtc4_observables.csv`` has the columns of
``data/gwtc5_observables.csv`` and is picked up automatically by script 05.

GWTC-4.0 and GWTC-5.0 search-result releases share the same LVK layout
(a ``SearchSummaryTable`` HDF5 file plus an ``Archived_SearchResults`` tarball of
sky maps), so the GWTC-5 helpers are reused.  If the Zenodo record cannot be
located automatically, pass it explicitly with ``--record-url``
(``https://zenodo.org/api/records/<id>``).  Selection is identical to O4b:
p_BBH > 0.5 and FAR < 1/yr.

If ``--gwosc-pe-mchirp`` is given, the detector-frame chirp mass from the GWOSC
event API (parameter estimation) replaces the search template value when
available, and ``mc_kind`` is set to ``pe`` for those rows.
"""

from __future__ import annotations

import argparse
import importlib
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.gwtc import config

g5 = importlib.import_module("scripts.gwtc.01b_extract_gwtc5_observables")

GWTC4_RAW_DIR = config.DATA_DIR / "gwtc4_raw"
GWTC4_OBSERVABLES_CSV = config.DATA_DIR / "gwtc4_observables.csv"
ZENODO_SEARCH = "https://zenodo.org/api/records?q=%22GWTC-4.0%22%20search%20results&size=25&sort=mostrecent"
O4A_GPS = (1368921618.0 - 5 * 86400, 1389398418.0 + 5 * 86400)  # 2023-05-24 .. 2024-01-16, +-5 d margin


def find_record(explicit: str | None) -> str:
    if explicit:
        return explicit
    hits = g5.get_json(ZENODO_SEARCH).get("hits", {}).get("hits", [])
    for hit in hits:
        keys = [f.get("key", "") for f in hit.get("files", [])]
        if any("SearchSummaryTable" in k for k in keys) and any("GWTC4" in k or "GWTC-4" in k for k in keys):
            print(f"Using Zenodo record {hit['id']}: {hit['metadata']['title']}", flush=True)
            return f"https://zenodo.org/api/records/{hit['id']}"
    titles = [h.get("metadata", {}).get("title") for h in hits]
    raise SystemExit(f"Could not identify the GWTC-4.0 search-results record automatically; candidates: {titles}. Pass --record-url.")


def gwosc_pe_mchirp() -> pd.DataFrame:
    text = requests.get(config.GWOSC_ALLEVENTS_CSV, timeout=config.REQUEST_TIMEOUT).text
    ev = pd.read_csv(io.StringIO(text))
    ev = ev[ev["catalog.shortName"].astype(str).str.startswith("GWTC-4")]
    ev = ev.sort_values("version").drop_duplicates("commonName", keep="last")
    return ev[["commonName", "chirp_mass", "luminosity_distance"]].rename(columns={"commonName": "event_name"})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record-url", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--p-bbh-min", type=float, default=0.5)
    ap.add_argument("--far-per-year-max", type=float, default=1.0)
    ap.add_argument("--gwosc-pe-mchirp", action="store_true")
    args = ap.parse_args()

    GWTC4_RAW_DIR.mkdir(parents=True, exist_ok=True)
    files = g5.zenodo_files(find_record(args.record_url))
    summary_meta = next(m for k, m in files.items() if "SearchSummaryTable" in k)
    tar_meta = next(m for k, m in files.items() if k.endswith("SearchResults.tar.gz"))
    summary_path = GWTC4_RAW_DIR / summary_meta["key"]
    tar_path = GWTC4_RAW_DIR / tar_meta["key"]
    g5.download_file(summary_meta["url"], summary_path, summary_meta["size"])
    summary = g5.load_search_summary(summary_path)
    details = g5.load_pipeline_details(summary_path)

    far_hz = args.far_per_year_max / g5.SECONDS_PER_YEAR
    sel = summary[(summary["p_BBH"] > args.p_bbh_min) & (summary["far"] < far_hz)]
    sel = sel[(sel["gps_time"] >= O4A_GPS[0]) & (sel["gps_time"] <= O4A_GPS[1])].sort_values("gps_time").reset_index(drop=True)
    print(f"GWTC-4.0 search rows={len(summary)} selected O4a BBH={len(sel)} pairs={len(sel) * (len(sel) - 1) // 2}", flush=True)
    if args.dry_run:
        print(sel[["event_name", "snr", "far", "p_BBH", "skymap_file"]].head(10).to_string(index=False))
        return

    g5.download_file(tar_meta["url"], tar_path, tar_meta["size"])
    extracted = g5.extract_selected_skymaps(tar_path, set(sel["skymap_file"].astype(str)), GWTC4_RAW_DIR / "selected_skymaps")

    rows = []
    for _, row in sel.iterrows():
        detail = g5.choose_pipeline_detail(details, row["event_name"], row["pipeline"])
        m1, m2 = float(detail.get("mass1", np.nan)), float(detail.get("mass2", np.nan))
        q = min(m1, m2) / max(m1, m2) if np.isfinite(m1) and np.isfinite(m2) and max(m1, m2) > 0 else np.nan
        sky_path = extracted.get(str(row["skymap_file"]))
        sky = g5.skymap_summary(sky_path) if sky_path else {"ra_median": np.nan, "dec_median": np.nan, "sky_area_90_deg2": np.nan}
        rows.append({
            "event_name": row["event_name"], "catalog": "GWTC-4.0-search", "gps_trigger_time": float(row["gps_time"]),
            "ra_median": sky["ra_median"], "dec_median": sky["dec_median"], "sky_area_90_deg2": sky["sky_area_90_deg2"],
            "network_snr": float(row["snr"]), "chirp_mass_median": float(row["mchirp"]), "mass_ratio_median": q,
            "luminosity_distance_median": np.nan, "p_astro": float(row["p_BBH"]), "far_hz": float(row["far"]),
            "pipeline": row["pipeline"], "mc_kind": "search",
            "source_path": "SearchSummaryTable + Archived_SearchResults skymap",
            "skymap_file": str(sky_path.relative_to(config.REPO_ROOT)) if sky_path else "",
        })
    out = pd.DataFrame(rows)

    if args.gwosc_pe_mchirp:
        pe = gwosc_pe_mchirp()
        out = out.merge(pe, on="event_name", how="left")
        has = out["chirp_mass"].notna()
        out.loc[has, "chirp_mass_median"] = out.loc[has, "chirp_mass"]
        out.loc[has, "luminosity_distance_median"] = out.loc[has, "luminosity_distance"]
        out.loc[has, "mc_kind"] = "pe"
        out = out.drop(columns=["chirp_mass", "luminosity_distance"])
        print(f"Replaced search chirp mass by GWOSC PE detector-frame chirp mass for {int(has.sum())} events")

    out.sort_values("gps_trigger_time").to_csv(GWTC4_OBSERVABLES_CSV, index=False)
    print(f"Wrote {GWTC4_OBSERVABLES_CSV} rows={len(out)}; A90 median {out['sky_area_90_deg2'].median():.0f} deg2")


if __name__ == "__main__":
    main()
