"""Realistic lensed and unlensed BBH populations with ``ler``.

Answers the reviewer's request for astrophysically motivated simulation
settings.  For each detector configuration the script

  1. builds a LeR object with an LVK-like BBH population (ler defaults:
     GWTC-3 Power Law + Peak masses, merger-rate density from a
     star-formation history with time delay, sources to z = 10) and a galaxy
     lens population (elliptical power-law + external shear; velocity
     dispersion from an SDSS-based velocity-dispersion function; lens redshift
     from the lensing optical depth; source position sampled uniformly inside
     the caustic);
  2. draws ``--n-lensed`` lensed systems in which at least two images have
     network optimal SNR above the detection threshold, and ``--n-unlensed``
     detectable unlensed events;
  3. writes flat CSV tables with one row per lensed system (parameters of the
     two brightest detected images) and one row per unlensed event, plus the
     ler rate estimates.

Detector configurations:
  O4  : H1, L1 (aLIGO O4 high ASD) and V1 (AdV ASD)
  ET  : the triangular Einstein Telescope, ET-D sensitivity (three arms)

Run inside the ler virtual environment, from the repository root:

  /home/user/ler-venv/bin/python scripts/population/ler_realistic_population.py \
      --config O4 --n-lensed 5000 --n-unlensed 5000 --out data/ler_population

The ler interpolation tables are cached under ``--work-dir`` and are built on
first use (tens of minutes); subsequent runs reuse them.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

CONFIGS = {
    "O4": dict(ifos=["L1", "H1", "V1"],
               psds={"L1": "aLIGO_O4_high_asd.txt", "H1": "aLIGO_O4_high_asd.txt", "V1": "AdV_asd.txt"}),
    "ET": dict(ifos=["ET"], psds={"ET": "ET_D_psd.txt"}),
}


def build_ler(config: str, work_dir: Path, npool: int, snr_th: float, mtot_max: float):
    from ler.rates import LeR

    det = CONFIGS[config]
    return LeR(
        npool=npool,
        z_min=0.0,
        z_max=10.0,
        event_type="BBH",
        lens_type="epl_shear_galaxy",
        interpolator_directory=str(work_dir / "interpolator_json"),
        ler_directory=str(work_dir / f"ler_data_{config}"),
        verbose=False,
        include_redundant_parameters=True,  # keep theta_E, n_images, luminosity_distance in the output
        # gwsnr settings: no-spin interpolation is accurate enough for the
        # population statistics used here and builds its tables in minutes.
        snr_method="interpolation_no_spins",
        waveform_approximant="IMRPhenomD",
        minimum_frequency=20.0,
        mtot_min=2.0,
        mtot_max=mtot_max,
        mtot_resolution=400,
        ratio_resolution=40,
        ifos=det["ifos"],
        psds=det["psds"],
        pdet_kwargs=dict(
            snr_th=snr_th, snr_th_net=snr_th, pdet_type="boolean",
            distribution_type="noncentral_chi2",
            include_optimal_snr=True, include_observed_snr=False,
            return_only_net_results=True,
        ),
    )


def _col(d: dict, key: str):
    v = d.get(key)
    return None if v is None else np.asarray(v)


def lensed_to_table(lp: dict, snr_th: float) -> pd.DataFrame:
    """One row per lensed system: the two brightest *detected* images."""
    mu = np.asarray(lp["magnifications"], dtype=float)          # (n, n_max_images)
    dt = np.asarray(lp["time_delays"], dtype=float)             # s
    itype = np.asarray(lp["image_type"], dtype=float)
    snr = np.asarray(lp["optimal_snr_net"], dtype=float)
    n = mu.shape[0]
    rows = []
    for i in range(n):
        det = np.where(np.nan_to_num(snr[i]) >= snr_th)[0]
        if len(det) < 2:
            continue
        order = det[np.argsort(-np.abs(mu[i, det]))]
        a, b = order[0], order[1]
        rows.append({
            "zs": lp["zs"][i], "zl": lp["zl"][i], "sigma": lp["sigma"][i], "q": lp["q"][i],
            "gamma": lp["gamma"][i], "theta_E_rad": lp.get("theta_E", [np.nan] * n)[i] if "theta_E" in lp else np.nan,
            "shear": float(np.hypot(lp["gamma1"][i], lp["gamma2"][i])),
            "mass_1_source": lp["mass_1_source"][i], "mass_2_source": lp["mass_2_source"][i],
            "mass_1_det": lp["mass_1_source"][i] * (1 + lp["zs"][i]),
            "mass_2_det": lp["mass_2_source"][i] * (1 + lp["zs"][i]),
            "luminosity_distance_Mpc": lp["luminosity_distance"][i] if "luminosity_distance" in lp else np.nan,
            "n_images": lp["n_images"][i],
            "n_detected_images": len(det),
            "beta_over_theta_E": float(np.hypot(lp["x_source"][i], lp["y_source"][i]) / lp["theta_E"][i]) if "theta_E" in lp else np.nan,
            "mu_bright": mu[i, a], "mu_faint": mu[i, b],
            "type_bright": itype[i, a], "type_faint": itype[i, b],
            "snr_bright": snr[i, a], "snr_faint": snr[i, b],
            "delay_days": abs(dt[i, b] - dt[i, a]) / 86400.0,
            "flux_ratio": abs(mu[i, a] / mu[i, b]),
        })
    return pd.DataFrame(rows)


def unlensed_to_table(up: dict) -> pd.DataFrame:
    keys = ["zs", "mass_1_source", "mass_2_source", "luminosity_distance", "optimal_snr_net", "ra", "dec", "theta_jn", "a_1", "a_2"]
    out = {k: np.asarray(up[k]) for k in keys if k in up}
    df = pd.DataFrame(out)
    df["mass_1_det"] = df["mass_1_source"] * (1 + df["zs"])
    df["mass_2_det"] = df["mass_2_source"] * (1 + df["zs"])
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", choices=list(CONFIGS), required=True)
    ap.add_argument("--n-lensed", type=int, default=5000)
    ap.add_argument("--n-unlensed", type=int, default=5000)
    ap.add_argument("--snr-th", type=float, default=8.0)
    ap.add_argument("--mtot-max", type=float, default=500.0)
    ap.add_argument("--npool", type=int, default=4)
    ap.add_argument("--batch-size", type=int, default=50000)
    ap.add_argument("--work-dir", default="/tmp/claude-0/lertest")
    ap.add_argument("--out", default="data/ler_population")
    ap.add_argument("--skip-rates", action="store_true")
    args = ap.parse_args()

    work = Path(args.work_dir)
    work.mkdir(parents=True, exist_ok=True)
    out = REPO / args.out
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ler = build_ler(args.config, work, args.npool, args.snr_th, args.mtot_max)
    print(f"[{args.config}] LeR ready after {time.time() - t0:.0f} s", flush=True)

    meta = {"config": args.config, "ifos": CONFIGS[args.config]["ifos"], "psds": CONFIGS[args.config]["psds"],
            "snr_threshold": args.snr_th, "detectable_lensed_condition": "two images with network optimal SNR >= threshold",
            "time_window_days": 365.0, "ler_version": __import__("ler").__version__}

    if not args.skip_rates:
        t1 = time.time()
        ler.unlensed_cbc_statistics(size=args.batch_size, resume=False, output_jsonfile=f"unlensed_param_{args.config}.json")
        rate_u = ler.unlensed_rate(output_jsonfile=f"unlensed_param_detectable_{args.config}.json")
        rate_u = float(rate_u[0]) if isinstance(rate_u, (tuple, list)) else float(rate_u)
        ler.lensed_cbc_statistics(size=args.batch_size, resume=False, output_jsonfile=f"lensed_param_{args.config}.json")
        rate_l = ler.lensed_rate(output_jsonfile=f"lensed_param_detectable_{args.config}.json",
                                 pdet_threshold=[0.5, 0.5], num_img=[1, 1])
        rate_l = float(rate_l[0]) if isinstance(rate_l, (tuple, list)) else float(rate_l)
        meta.update({"unlensed_rate_per_yr": float(rate_u), "lensed_rate_per_yr": float(rate_l),
                     "lensed_fraction": float(rate_l / rate_u) if rate_u > 0 else None,
                     "rate_wall_s": time.time() - t1})
        print(f"[{args.config}] rates: unlensed {rate_u:.1f}/yr, lensed (2 detected images) {rate_l:.3f}/yr, fraction {rate_l / rate_u:.2e}", flush=True)

    t2 = time.time()
    lp = ler.selecting_n_lensed_detectable_events(
        size=args.n_lensed, batch_size=args.batch_size, pdet_threshold=[0.5, 0.5], num_img=[1, 1],
        resume=False, output_jsonfile=f"n_lensed_detectable_{args.config}.json", meta_data_file=f"meta_lensed_{args.config}.json",
        trim_to_size=True)
    lensed = lensed_to_table(lp, args.snr_th)
    lensed.to_csv(out / f"{args.config}_lensed_pairs.csv", index=False)
    print(f"[{args.config}] {len(lensed)} lensed systems with two detected images in {time.time() - t2:.0f} s", flush=True)

    t3 = time.time()
    up = ler.selecting_n_unlensed_detectable_events(
        size=args.n_unlensed, batch_size=args.batch_size, pdet_threshold=0.5, resume=False,
        output_jsonfile=f"n_unlensed_detectable_{args.config}.json", meta_data_file=f"meta_unlensed_{args.config}.json",
        trim_to_size=True)
    unlensed = unlensed_to_table(up)
    unlensed.to_csv(out / f"{args.config}_unlensed_events.csv", index=False)
    print(f"[{args.config}] {len(unlensed)} unlensed detectable events in {time.time() - t3:.0f} s", flush=True)

    meta["n_lensed_rows"] = int(len(lensed))
    meta["n_unlensed_rows"] = int(len(unlensed))
    meta["total_wall_s"] = time.time() - t0
    (out / f"{args.config}_meta.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
