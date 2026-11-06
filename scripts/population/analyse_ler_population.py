"""Analyse the realistic lensed population produced by ler_realistic_population.py.

For each detector configuration (O4, ET) it reports what the reviewer asked
about: the distributions of the fainter-image SNR, the flux ratio, the
normalised impact parameter, the time delay and the image types of
detectable lensed pairs, and the fraction of those pairs that fall inside
the domain of the original simulations (y <= 0.3, i.e. flux ratio <= 1.9 for
an SIS, both images type I/II, delay < 1 yr).  It also compares the detected
unlensed population with the uniform-mass, z < 1 population used originally.

Run (any python with numpy/pandas/matplotlib):

  python scripts/population/analyse_ler_population.py --data data/ler_population
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[2]
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "legend.fontsize": 7.5, "figure.dpi": 150})
COL = {"O4": "#1f77b4", "ET": "#d62728"}
ORIG_FLUX_RATIO_MAX = (1 + 0.3) / (1 - 0.3)  # SIS with y <= 0.3


def q(x, p):
    return float(np.nanquantile(x, p))


def summarise(name: str, L: pd.DataFrame, U: pd.DataFrame | None, meta: dict | None) -> dict:
    s = {"config": name, "n_lensed_pairs": int(len(L))}
    if meta:
        s.update({k: meta.get(k) for k in ("unlensed_rate_per_yr", "lensed_rate_per_yr", "lensed_fraction", "snr_threshold")})
    s["delay_days"] = {"median": q(L.delay_days, .5), "p10": q(L.delay_days, .1), "p90": q(L.delay_days, .9),
                       "frac_lt_1min": float((L.delay_days < 1 / 1440).mean()), "frac_lt_1h": float((L.delay_days < 1 / 24).mean()),
                       "frac_lt_1d": float((L.delay_days < 1).mean()), "frac_lt_30d": float((L.delay_days < 30).mean()),
                       "frac_lt_365d": float((L.delay_days < 365.25).mean())}
    s["flux_ratio"] = {"median": q(L.flux_ratio, .5), "p90": q(L.flux_ratio, .9),
                       "frac_le_orig_max": float((L.flux_ratio <= ORIG_FLUX_RATIO_MAX).mean())}
    s["beta_over_theta_E"] = {"median": q(L.beta_over_theta_E, .5), "frac_le_0p3": float((L.beta_over_theta_E <= 0.3).mean())}
    s["snr_faint"] = {"median": q(L.snr_faint, .5), "p90": q(L.snr_faint, .9), "frac_lt_12": float((L.snr_faint < 12).mean())}
    s["snr_bright"] = {"median": q(L.snr_bright, .5), "p90": q(L.snr_bright, .9)}
    s["n_images"] = {str(k): int(v) for k, v in L.n_images.value_counts().sort_index().items()}
    s["n_detected_images"] = {str(k): int(v) for k, v in L.n_detected_images.value_counts().sort_index().items()}
    pair_types = (L.type_bright.astype(int).astype(str) + "+" + L.type_faint.astype(int).astype(str)).value_counts()
    s["pair_image_types"] = {k: int(v) for k, v in pair_types.items()}
    inside = (L.flux_ratio <= ORIG_FLUX_RATIO_MAX) & (L.delay_days < 365.25) & (L.type_bright <= 2) & (L.type_faint <= 2) & (L.delay_days >= 1 / 1440)
    s["frac_inside_original_training_domain"] = float(inside.mean())
    s["zs"] = {"median": q(L.zs, .5), "p90": q(L.zs, .9), "frac_gt_1": float((L.zs > 1).mean())}
    s["zl"] = {"median": q(L.zl, .5)}
    s["sigma_kms"] = {"median": q(L.sigma, .5), "p10": q(L.sigma, .1), "p90": q(L.sigma, .9)}
    s["mass_1_det"] = {"median": q(L.mass_1_det, .5), "p90": q(L.mass_1_det, .9)}
    if U is not None and len(U):
        s["unlensed"] = {"n": int(len(U)), "zs_median": q(U.zs, .5), "zs_p90": q(U.zs, .9), "frac_z_gt_1": float((U.zs > 1).mean()),
                         "mass_1_source_median": q(U.mass_1_source, .5), "snr_median": q(U.optimal_snr_net, .5)}
    return s


def figures(out: Path, data: dict[str, pd.DataFrame]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.0))
    ax = axes[0, 0]
    bins = np.logspace(-5.5, 2.6, 60)
    for k, L in data.items():
        ax.hist(np.clip(L.delay_days, bins[0], bins[-1]), bins=bins, histtype="step", color=COL[k], lw=1.2,
                weights=np.ones(len(L)) / len(L), label=k)
    ax.axvline(1 / 1440, color="k", ls=":", lw=0.8)
    ax.text(1 / 1440 * 1.3, ax.get_ylim()[1] * 0.9, "1 min", fontsize=6.5)
    ax.set_xscale("log")
    ax.set_xlabel("Time delay between the two images [days]")
    ax.set_ylabel("Fraction of detectable lensed pairs")
    ax.legend(frameon=False)
    ax = axes[0, 1]
    bins = np.logspace(0, 2.5, 40)
    for k, L in data.items():
        ax.hist(np.clip(L.flux_ratio, bins[0], bins[-1]), bins=bins, histtype="step", color=COL[k], lw=1.2,
                weights=np.ones(len(L)) / len(L), label=k)
    ax.axvline(ORIG_FLUX_RATIO_MAX, color="k", ls=":", lw=0.8)
    ax.text(ORIG_FLUX_RATIO_MAX * 1.1, ax.get_ylim()[1] * 0.9, "original\nsimulations\n($y\\leq0.3$)", fontsize=6.5, va="top")
    ax.set_xscale("log")
    ax.set_xlabel("Flux ratio of the two images $|\\mu_1/\\mu_2|$")
    ax = axes[1, 0]
    bins = np.logspace(np.log10(8), 3, 40)
    for k, L in data.items():
        ax.hist(np.clip(L.snr_faint, bins[0], bins[-1]), bins=bins, histtype="step", color=COL[k], lw=1.2,
                weights=np.ones(len(L)) / len(L), label=f"{k}: fainter image")
        ax.hist(np.clip(L.snr_bright, bins[0], bins[-1]), bins=bins, histtype="step", color=COL[k], lw=0.9, ls="--",
                weights=np.ones(len(L)) / len(L), label=f"{k}: brighter image")
    ax.set_xscale("log")
    ax.set_xlabel("Network SNR")
    ax.set_ylabel("Fraction of detectable lensed pairs")
    ax.legend(frameon=False, fontsize=6.5)
    ax = axes[1, 1]
    bins = np.linspace(0, 6, 40)
    for k, L in data.items():
        ax.hist(np.clip(L.zs, 0, 6), bins=bins, histtype="step", color=COL[k], lw=1.2, weights=np.ones(len(L)) / len(L), label=k)
    ax.axvline(1.0, color="k", ls=":", lw=0.8)
    ax.text(1.05, ax.get_ylim()[1] * 0.9, "original $z_{\\rm max}$", fontsize=6.5)
    ax.set_xlabel("Source redshift of detectable lensed pairs")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig_ler_population.{ext}", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/ler_population")
    args = ap.parse_args()
    d = REPO / args.data
    data, summary = {}, {}
    for cfg in ("O4", "ET"):
        f = d / f"{cfg}_lensed_pairs.csv"
        if not f.exists():
            continue
        L = pd.read_csv(f)
        uf = d / f"{cfg}_unlensed_events.csv"
        U = pd.read_csv(uf) if uf.exists() else None
        mf = d / f"{cfg}_meta.json"
        meta = json.loads(mf.read_text()) if mf.exists() else None
        data[cfg] = L
        summary[cfg] = summarise(cfg, L, U, meta)
    if data:
        figures(d, data)
    (d / "population_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
