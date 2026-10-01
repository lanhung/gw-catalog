"""Real-catalogue context for strain-level lensed-pair verification (PI-ResNet).

This script places the simulated per-pair operating points of a pair verifier
(e.g. PI-ResNet at false-positive probability 1e-2, 1e-3, 1e-4) in the context
of the real LIGO-Virgo-KAGRA catalogues.  It answers four physical questions:

1. How many event pairs does each catalogue contain (O1-O3, O4a, O4b, combined)?
2. How long are galaxy-lens time delays, and what fraction of lensed pairs can
   have both images inside one observing run?
3. How many real pairs remain after requiring the three things lensing must
   preserve: an allowed time delay, a common sky position, and a common
   detector-frame chirp mass?
4. Given those survivors, how many unrelated pairs would a verifier with a
   given per-pair false-positive probability wrongly accept, compared with the
   expected number of genuine lensed pairs?

Inputs (repository ``data/``):
  gwtc3_observables.csv   O1-O3 BBHs with PE summaries (GWTC-2.1/GWTC-3)
  gwtc4_observables.csv   O4a BBHs (optional; produced by 01c on the server)
  gwtc5_observables.csv   O4b BBHs from the GWTC-5.0 search release

Only numpy/pandas/scipy/matplotlib are required.  Run from the repo root:

  python scripts/gwtc/05_catalog_context_for_pair_verification.py \
      --out runs/gwtc_catalog_context_20261001
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import gamma as gamma_fn

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"

# --- constants -------------------------------------------------------------
C_KM_S = 299792.458
C_M_S = 299792458.0
G_SI = 6.67430e-11
MSUN = 1.98847e30
MPC_M = 3.0856775814913673e22
DAY_S = 86400.0
YEAR_DAYS = 365.25
H0 = 67.66  # Planck 2018
OM0 = 0.30966

# Observing-run boundaries (UTC dates; GPS conversion below ignores leap-second
# changes, which is irrelevant at the day-level precision used here).
RUNS = {
    "O1": ("2015-09-12", "2016-01-19"),
    "O2": ("2016-11-30", "2017-08-25"),
    "O3a": ("2019-04-01", "2019-10-01"),
    "O3b": ("2019-11-01", "2020-03-27"),
    "O4a": ("2023-05-24", "2024-01-16"),
    "O4b": ("2024-04-10", "2025-01-28"),
}
GPS_EPOCH = pd.Timestamp("1980-01-06")


def utc_to_gps(date: str) -> float:
    return (pd.Timestamp(date) - GPS_EPOCH).total_seconds() + 18.0


RUN_GPS = {k: (utc_to_gps(a), utc_to_gps(b)) for k, (a, b) in RUNS.items()}

# Per-pair false-positive probabilities at which PI-ResNet was calibrated.
FPP_LEVELS = (1e-2, 1e-3, 1e-4)
# Fraction of detected BBHs with a detectable strongly lensed counterpart
# (order-of-magnitude range from LIGO/Virgo lensing-rate forecasts).
LENSED_PAIR_FRACTION = (3e-4, 1e-3, 3e-3)

# Fractional (1-sigma, in ln Mc) uncertainty of the detector-frame chirp mass.
SIGMA_LNMC = {"pe": 0.07, "search": 0.15}
CHI2_2DOF_99 = 9.2103  # 99% point of chi^2 with 2 degrees of freedom
Z_99 = 2.5758  # two-sided 99% point of a unit Gaussian


# --- cosmology ---------------------------------------------------------------
_ZGRID = np.linspace(0.0, 6.0, 6001)
_EZ = np.sqrt(OM0 * (1 + _ZGRID) ** 3 + 1 - OM0)
_CHI = np.concatenate([[0.0], np.cumsum(0.5 * (1 / _EZ[1:] + 1 / _EZ[:-1]) * np.diff(_ZGRID))]) * C_KM_S / H0  # Mpc


def comoving_mpc(z):
    return np.interp(z, _ZGRID, _CHI)


def z_from_dl(dl_mpc):
    return np.interp(dl_mpc, _CHI * (1 + _ZGRID), _ZGRID)


def z_from_chi(chi):
    return np.interp(chi, _CHI, _ZGRID)


# --- lens time-delay models -------------------------------------------------
def sis_delay_days(sigma_kms, z_l, z_s, y):
    chi_l, chi_s = comoving_mpc(z_l), comoving_mpc(z_s)
    d_l = chi_l / (1 + z_l)
    d_s = chi_s / (1 + z_s)
    d_ls = (chi_s - chi_l) / (1 + z_s)
    dist_m = d_l * d_ls / d_s * MPC_M
    dt = 32 * math.pi ** 2 * (np.asarray(sigma_kms) * 1e3 / C_M_S) ** 4 * (1 + z_l) * dist_m * y / C_M_S
    return dt / DAY_S


def pm_delay_days(m_lens_msun, z_l, y):
    s = np.sqrt(y ** 2 + 4)
    dt = 4 * G_SI * m_lens_msun * MSUN * (1 + z_l) / C_M_S ** 3 * (0.5 * y * s + np.log((s + y) / (s - y)))
    return dt / DAY_S


def sample_uniform_comoving_z(rng, n, zmin=0.01, zmax=1.0):
    chi3 = rng.uniform(comoving_mpc(zmin) ** 3, comoving_mpc(zmax) ** 3, n)
    return z_from_chi(np.cbrt(chi3))


def simulation_prior_delays(rng, n):
    """Delays under the priors used to build the PI-ResNet training/test catalogues."""
    z_s = sample_uniform_comoving_z(rng, n)
    z_l = z_s / 2
    y = rng.uniform(0.01, 0.3, n)
    sis = sis_delay_days(rng.uniform(100, 500, n), z_l, z_s, y)
    pm = pm_delay_days(rng.uniform(1e8, 1e10, n), z_l, y)
    return sis, pm


def astrophysical_sis_delays(rng, z_sources, n, magnification_bias=True):
    """Galaxy-lens delays with a velocity-dispersion function and magnification bias.

    sigma: SDSS velocity-dispersion function (Choi et al. 2007) weighted by the
    SIS lensing cross-section ~ sigma^4.  Lens distance: optical-depth weight
    (chi_l (chi_s-chi_l)/chi_s)^2 for a constant comoving lens density.  Impact
    parameter: geometric weight 2y on [0,1] times the probability that the
    fainter image (|mu_-| = 1/y - 1) is detectable for an SNR distribution
    p(>rho) ~ rho^-3, i.e. a factor |mu_-|^{3/2}.
    """
    sig_grid = np.linspace(40, 450, 4000)
    alpha, beta, sig_star = 2.32, 2.67, 161.0
    vdf = (sig_grid / sig_star) ** alpha * np.exp(-((sig_grid / sig_star) ** beta)) * beta / gamma_fn(alpha / beta) / sig_grid
    w = vdf * sig_grid ** 4
    sigma = rng.choice(sig_grid, size=n, p=w / w.sum())

    z_s = rng.choice(z_sources, size=n)
    chi_s = comoving_mpc(z_s)
    u = np.linspace(1e-4, 1 - 1e-4, 2000)
    pu = (u * (1 - u)) ** 2
    frac = rng.choice(u, size=n, p=pu / pu.sum())
    z_l = z_from_chi(frac * chi_s)

    y_grid = np.linspace(1e-3, 0.999, 4000)
    py = y_grid * (1 / y_grid - 1) ** 1.5 if magnification_bias else y_grid.copy()
    y = rng.choice(y_grid, size=n, p=py / py.sum())
    return sis_delay_days(sigma, z_l, z_s, y)


# --- catalogue loading --------------------------------------------------------
def run_of(gps: float) -> str:
    for name, (a, b) in RUN_GPS.items():
        if a - 5 * DAY_S <= gps <= b + 5 * DAY_S:
            return name
    return "other"


def load_catalogue() -> pd.DataFrame:
    frames = []
    g3 = pd.read_csv(DATA / "gwtc3_observables.csv")
    z = z_from_dl(g3["luminosity_distance_median"].to_numpy())
    frames.append(pd.DataFrame({
        "event": g3["event_name"], "release": "GWTC-2.1/3 (PE)", "gps": g3["gps_trigger_time"],
        "ra": g3["ra_median"], "dec": g3["dec_median"], "a90": g3["sky_area_90_deg2"],
        "snr": g3["network_snr"], "mc_det": g3["chirp_mass_median"] * (1 + z),
        "z": z, "mc_kind": "pe",
    }))
    for fname, label in (("gwtc4_observables.csv", "GWTC-4.0 (search)"), ("gwtc5_observables.csv", "GWTC-5.0 (search)")):
        path = DATA / fname
        if not path.exists():
            continue
        d = pd.read_csv(path)
        kind = d["mc_kind"].fillna("search").to_numpy() if "mc_kind" in d.columns else "search"
        frames.append(pd.DataFrame({
            "event": d["event_name"], "release": label, "gps": d["gps_trigger_time"],
            "ra": d["ra_median"], "dec": d["dec_median"], "a90": d["sky_area_90_deg2"],
            "snr": d["network_snr"], "mc_det": d["chirp_mass_median"],
            "z": np.nan, "mc_kind": kind,
        }))
    cat = pd.concat(frames, ignore_index=True)
    cat = cat.dropna(subset=["gps", "ra", "dec", "a90", "mc_det"]).sort_values("gps").reset_index(drop=True)
    cat["run"] = [run_of(g) for g in cat["gps"]]
    cat["epoch"] = cat["run"].str[:2]  # O1, O2, O3, O4
    cat["sigma_sky"] = np.sqrt(np.radians(1) ** 2 * cat["a90"] / (2 * math.pi * math.log(10)))
    cat["sigma_lnmc"] = cat["mc_kind"].map(SIGMA_LNMC)
    return cat


def all_pairs(cat: pd.DataFrame) -> pd.DataFrame:
    i, j = np.triu_indices(len(cat), k=1)
    ra, dec = cat["ra"].to_numpy(), cat["dec"].to_numpy()
    cos_sep = np.sin(dec[i]) * np.sin(dec[j]) + np.cos(dec[i]) * np.cos(dec[j]) * np.cos(ra[i] - ra[j])
    sep = np.arccos(np.clip(cos_sep, -1, 1))
    sig = cat["sigma_sky"].to_numpy()
    lnmc = np.log(cat["mc_det"].to_numpy())
    slm = cat["sigma_lnmc"].to_numpy()
    p = pd.DataFrame({
        "event_i": cat["event"].to_numpy()[i], "event_j": cat["event"].to_numpy()[j],
        "run_i": cat["run"].to_numpy()[i], "run_j": cat["run"].to_numpy()[j],
        "delta_t_days": np.abs(cat["gps"].to_numpy()[j] - cat["gps"].to_numpy()[i]) / DAY_S,
        "sep_deg": np.degrees(sep),
        "chi2_sky": sep ** 2 / (sig[i] ** 2 + sig[j] ** 2),
        "z_mc": np.abs(lnmc[i] - lnmc[j]) / np.sqrt(slm[i] ** 2 + slm[j] ** 2),
        "mc_i": cat["mc_det"].to_numpy()[i], "mc_j": cat["mc_det"].to_numpy()[j],
    })
    p["same_epoch"] = cat["epoch"].to_numpy()[i] == cat["epoch"].to_numpy()[j]
    p["chi2_total"] = p["chi2_sky"] + p["z_mc"] ** 2
    return p


def funnel(p: pd.DataFrame, tmax_days: float, mc_scale: float = 1.0) -> dict:
    s0 = np.ones(len(p), bool)
    s1 = p["delta_t_days"].to_numpy() <= tmax_days
    s2 = s1 & (p["chi2_sky"].to_numpy() <= CHI2_2DOF_99)
    s3 = s2 & (p["z_mc"].to_numpy() <= Z_99 * mc_scale)
    return {"all": int(s0.sum()), "time": int(s1.sum()), "time+sky": int(s2.sum()), "time+sky+mass": int(s3.sum()), "mask": s3}


# --- injections ----------------------------------------------------------------
def inject(cat: pd.DataFrame, delays_days: np.ndarray, rng, n_inj: int, tmax_days: float, subset: pd.Index | None = None):
    """Inject synthetic second images of real events and test the funnel/rank."""
    idx_pool = np.asarray(subset if subset is not None else cat.index)
    gps = cat["gps"].to_numpy()
    sig = cat["sigma_sky"].to_numpy()
    lnmc = np.log(cat["mc_det"].to_numpy())
    slm = cat["sigma_lnmc"].to_numpy()
    ra, dec = cat["ra"].to_numpy(), cat["dec"].to_numpy()
    rows = []
    for _ in range(n_inj):
        e = rng.choice(idx_pool)
        dt = rng.choice(delays_days)
        t2 = gps[e] + dt * DAY_S
        in_run = any(a <= t2 <= b for a, b in RUN_GPS.values())
        same_run = run_of(t2) == cat.loc[e, "run"]
        # second image: localisation width and Mc error drawn from the catalogue itself
        k = rng.choice(idx_pool)
        sig2, slm2 = sig[k], slm[k]
        # relative sky offset between the two (independent) localisation errors
        off = rng.normal(0, 1, 2) * np.hypot(sig[e], sig2)
        dec2 = np.clip(dec[e] + off[0], -math.pi / 2, math.pi / 2)
        ra2 = ra[e] + off[1] / max(math.cos(dec[e]), 0.05)
        lnmc2 = lnmc[e] + rng.normal(0, math.hypot(slm[e], slm2))
        # compare to every catalogue event (the injected image versus the real catalogue)
        cos_sep = np.sin(dec2) * np.sin(dec) + np.cos(dec2) * np.cos(dec) * np.cos(ra2 - ra)
        sep = np.arccos(np.clip(cos_sep, -1, 1))
        chi2_sky = sep ** 2 / (sig ** 2 + sig2 ** 2)
        z_mc = np.abs(lnmc2 - lnmc) / np.sqrt(slm ** 2 + slm2 ** 2)
        dts = np.abs(t2 - gps) / DAY_S
        ok = (dts <= tmax_days) & (chi2_sky <= CHI2_2DOF_99) & (z_mc <= Z_99)
        chi2_tot = np.where(dts <= tmax_days, chi2_sky + z_mc ** 2, np.inf)
        rank = int(np.sum(chi2_tot < chi2_tot[e])) + 1
        rows.append({
            "delay_days": dt, "second_image_in_any_run": in_run, "second_image_same_run": same_run,
            "pass_time": dts[e] <= tmax_days, "pass_sky": chi2_sky[e] <= CHI2_2DOF_99, "pass_mass": z_mc[e] <= Z_99,
            "pass_all": bool(ok[e]), "n_false_partners_passing": int(ok.sum() - ok[e]), "rank_true_partner": rank,
        })
    return pd.DataFrame(rows)


# --- plotting ----------------------------------------------------------------
def make_figures(out: Path, delays: dict, p: pd.DataFrame, budget: pd.DataFrame, survivors_by: dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "legend.fontsize": 7.5, "figure.dpi": 150})
    colors = {"sis_sim": "#1f77b4", "pm_sim": "#d62728", "sis_astro": "#2ca02c"}
    labels = {
        "sis_sim": "SIS, simulation prior ($y\\leq0.3$)",
        "pm_sim": "Point mass, simulation prior",
        "sis_astro": "SIS, galaxy population + magnification bias",
    }

    # Figure A: time-delay distributions
    fig, ax = plt.subplots(figsize=(3.4, 2.9))
    bins = np.logspace(-3, 3.2, 63)
    styles = {"sis_sim": "-", "pm_sim": "-", "sis_astro": "-", "sis_astro_no_mag_bias": "--"}
    colors["sis_astro_no_mag_bias"] = "#2ca02c"
    labels["sis_astro_no_mag_bias"] = "SIS, galaxy population, no magnification bias"
    for k in ("pm_sim", "sis_astro", "sis_astro_no_mag_bias", "sis_sim"):
        ax.hist(np.clip(delays[k], bins[0], bins[-1]), bins=bins, histtype="step",
                weights=np.ones(len(delays[k])) / len(delays[k]), color=colors[k], ls=styles[k], label=labels[k], lw=1.2)
    ax.set_ylim(0, 0.135)
    for x, lab in ((1, "1 day"), (30, "1 month"), (YEAR_DAYS, "1 year")):
        ax.axvline(x, color="0.6", ls=":", lw=0.8)
        ax.text(x * 0.85, 0.104, lab, fontsize=6.5, color="0.35", rotation=90, ha="right", va="bottom")
    ax.set_xscale("log")
    ax.set_xlabel("Time delay between the two images [days]")
    ax.set_ylabel("Fraction of lensed pairs per bin")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.3), frameon=False, fontsize=6.5, ncol=1)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig_time_delays.{ext}", bbox_inches="tight")
    plt.close(fig)

    # Figure B: the funnel per catalogue
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    stages = ["all", "time", "time+sky", "time+sky+mass"]
    stage_lab = ["all pairs", "+ delay\n< 1 yr", "+ same\nsky", "+ same\nchirp mass"]
    markers = ["o", "s", "^", "D"]
    for (name, f), m in zip(survivors_by.items(), markers):
        ax.plot(range(4), [max(f[s], 0.8) for s in stages], marker=m, label=name, lw=1.2)
    ax.set_yscale("log")
    ax.set_xticks(range(4))
    ax.set_xticklabels(stage_lab)
    ax.set_ylabel("Number of event pairs")
    ax.legend(frameon=False)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig_catalog_funnel.{ext}")
    plt.close(fig)

    # Figure C: false-alarm budget vs per-pair FPP
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    fpp = np.logspace(-7, -1, 200)
    for _, r in budget.iterrows():
        ax.plot(fpp, fpp * r["n_pairs"], lw=1.2, label=r["label"])
    lo, mid, hi = (budget["expected_lensed_pairs_low"].max(), budget["expected_lensed_pairs_mid"].max(),
                   budget["expected_lensed_pairs_high"].max())
    ax.axhspan(lo, hi, color="0.85", zorder=0)
    ax.axhline(mid, color="0.5", lw=0.8, ls="--")
    ax.text(1.5e-7, hi * 1.4, "expected genuine lensed pairs", fontsize=7, color="0.3")
    for x in FPP_LEVELS:
        ax.axvline(x, color="k", lw=0.6, ls=":")
    for x, lab in zip(FPP_LEVELS, ("$10^{-2}$", "$10^{-3}$\n(primary)", "$10^{-4}$")):
        ax.text(x * 1.12, 2e4, lab, fontsize=6.5, va="top")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(1e-4, 1e5)
    ax.set_xlabel("False-positive probability per pair")
    ax.set_ylabel("Expected unrelated pairs accepted")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig_false_alarm_budget.{ext}", bbox_inches="tight")
    plt.close(fig)

    # Figure D: survivors on the (delta t, sky chi2) plane for the combined catalogue
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    same = p["same_epoch"].to_numpy()
    ax.scatter(p.loc[~same, "delta_t_days"], np.clip(p.loc[~same, "chi2_sky"], 1e-3, 1e4), s=1, c="0.75", label="different observing epochs", rasterized=True)
    ax.scatter(p.loc[same, "delta_t_days"], np.clip(p.loc[same, "chi2_sky"], 1e-3, 1e4), s=1, c="#1f77b4", label="same observing epoch", rasterized=True)
    surv = p["survives"].to_numpy()
    ax.scatter(p.loc[surv, "delta_t_days"], np.clip(p.loc[surv, "chi2_sky"], 1e-3, 1e4), s=6, c="#d62728", label="pass all three tests")
    ax.axhline(CHI2_2DOF_99, color="k", lw=0.7, ls="--")
    ax.axvline(YEAR_DAYS, color="k", lw=0.7, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Time between the two events [days]")
    ax.set_ylabel("Sky mismatch $\\chi^2_{\\rm sky}$")
    ax.legend(frameon=False, markerscale=3, fontsize=6.5, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out / f"fig_real_pairs_plane.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/gwtc_catalog_context_20261001")
    ap.add_argument("--tmax-days", type=float, default=YEAR_DAYS)
    ap.add_argument("--n-delay", type=int, default=200000)
    ap.add_argument("--n-inj", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20261001)
    args = ap.parse_args()
    out = REPO / args.out
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    cat = load_catalogue()
    cat.to_csv(out / "combined_catalogue.csv", index=False)
    summary: dict = {"tmax_days": args.tmax_days, "seed": args.seed, "sigma_lnmc": SIGMA_LNMC}

    # 1. census
    census = cat.groupby(["run", "release"]).size().rename("n_events").reset_index()
    summary["census"] = census.to_dict(orient="records")
    summary["n_events_total"] = int(len(cat))

    # 2. delays
    sis_sim, pm_sim = simulation_prior_delays(rng, args.n_delay)
    z_src = cat["z"].dropna().to_numpy()
    sis_astro = astrophysical_sis_delays(rng, z_src, args.n_delay)
    sis_astro_nobias = astrophysical_sis_delays(rng, z_src, args.n_delay, magnification_bias=False)
    delays = {"sis_sim": sis_sim, "pm_sim": pm_sim, "sis_astro": sis_astro, "sis_astro_no_mag_bias": sis_astro_nobias}
    dstats = {}
    for k, v in delays.items():
        dstats[k] = {
            "median_days": float(np.median(v)), "p90_days": float(np.quantile(v, 0.9)), "p99_days": float(np.quantile(v, 0.99)),
            "frac_lt_1d": float(np.mean(v < 1)), "frac_lt_30d": float(np.mean(v < 30)),
            "frac_lt_1yr": float(np.mean(v < YEAR_DAYS)), "frac_lt_4yr": float(np.mean(v < 4 * YEAR_DAYS)),
        }
    summary["delays"] = dstats
    summary["median_source_redshift"] = float(np.median(z_src))
    pd.DataFrame(dstats).T.to_csv(out / "time_delay_stats.csv")

    # 3. pairs and funnel
    p = all_pairs(cat)
    f_all = funnel(p, args.tmax_days)
    p["survives"] = f_all.pop("mask")
    p.to_csv(out / "all_pairs.csv.gz", index=False)
    subsets = {
        "O1-O3": p["run_i"].str.startswith(("O1", "O2", "O3")) & p["run_j"].str.startswith(("O1", "O2", "O3")),
        "O4a": (p["run_i"] == "O4a") & (p["run_j"] == "O4a"),
        "O4b": (p["run_i"] == "O4b") & (p["run_j"] == "O4b"),
    }
    survivors_by = {}
    for name, m in subsets.items():
        if m.sum() == 0:
            continue
        f = funnel(p[m], args.tmax_days)
        f.pop("mask")
        survivors_by[name] = f
    survivors_by["all runs combined"] = f_all
    summary["funnel"] = survivors_by
    pd.DataFrame(survivors_by).T.to_csv(out / "funnel_counts.csv")

    # mass-tolerance sensitivity
    sens = {}
    for scale in (0.5, 1.0, 2.0):
        f = funnel(p, args.tmax_days, mc_scale=scale)
        f.pop("mask")
        sens[f"mc_tolerance_x{scale}"] = f["time+sky+mass"]
    for tmax in (30.0, 90.0, YEAR_DAYS, 2 * YEAR_DAYS):
        f = funnel(p, tmax)
        f.pop("mask")
        sens[f"tmax_{int(tmax)}d"] = f["time+sky+mass"]
    summary["sensitivity_survivors"] = sens

    # surviving pairs (most consistent first)
    surv = p[p["survives"]].sort_values("chi2_total")
    surv.to_csv(out / "surviving_pairs.csv", index=False)
    summary["n_survivors"] = int(len(surv))
    summary["top_survivors"] = surv.head(15)[["event_i", "event_j", "delta_t_days", "sep_deg", "chi2_sky", "z_mc", "mc_i", "mc_j"]].round(3).to_dict(orient="records")

    # known historically discussed pair
    hist = p[((p.event_i == "GW170104") & (p.event_j == "GW170814")) | ((p.event_i == "GW170814") & (p.event_j == "GW170104"))]
    if len(hist):
        r = hist.iloc[0]
        summary["GW170104_GW170814"] = {k: (float(r[k]) if isinstance(r[k], (float, np.floating)) else (bool(r[k]) if isinstance(r[k], (bool, np.bool_)) else str(r[k])))
                                        for k in ["delta_t_days", "sep_deg", "chi2_sky", "z_mc", "survives"]}

    # 4. injections into the real catalogue (galaxy-population delays)
    inj_rows = {}
    for name, runs in (("O1-O3", ("O1", "O2", "O3a", "O3b")), ("O4b", ("O4b",)), ("O4a", ("O4a",))):
        sub = cat.index[cat["run"].isin(runs)]
        if len(sub) == 0:
            continue
        inj = inject(cat, sis_astro, rng, args.n_inj, args.tmax_days, subset=sub)
        inj.to_csv(out / f"injections_{name}.csv", index=False)
        observed = inj[inj["second_image_same_run"]]
        inj_rows[name] = {
            "n_injected": int(len(inj)),
            "frac_second_image_same_run": float(inj["second_image_same_run"].mean()),
            "frac_second_image_any_run": float(inj["second_image_in_any_run"].mean()),
            "funnel_efficiency_given_observed": float(observed["pass_all"].mean()),
            "pass_time_given_observed": float(observed["pass_time"].mean()),
            "pass_sky_given_observed": float(observed["pass_sky"].mean()),
            "pass_mass_given_observed": float(observed["pass_mass"].mean()),
            "median_false_partners_passing": float(observed["n_false_partners_passing"].median()),
            "mean_false_partners_passing": float(observed["n_false_partners_passing"].mean()),
            "recall_at_1": float((observed["pass_all"] & (observed["rank_true_partner"] <= 1)).mean()),
            "recall_at_5": float((observed["pass_all"] & (observed["rank_true_partner"] <= 5)).mean()),
            "recall_at_10": float((observed["pass_all"] & (observed["rank_true_partner"] <= 10)).mean()),
        }
    summary["injections"] = inj_rows
    pd.DataFrame(inj_rows).T.to_csv(out / "injection_summary.csv")

    # 5. false-alarm budget
    brow = []
    for name, f in survivors_by.items():
        n_ev = int(len(cat)) if name == "all runs combined" else int(cat["run"].isin({"O1-O3": ["O1", "O2", "O3a", "O3b"], "O4a": ["O4a"], "O4b": ["O4b"]}[name]).sum())
        for stage_name, n_pairs in (("all pairs", f["all"]), ("after physical tests", f["time+sky+mass"])):
            row = {"label": f"{name}: {stage_name}", "catalogue": name, "stage": stage_name, "n_events": n_ev, "n_pairs": int(n_pairs)}
            for q in FPP_LEVELS:
                row[f"false_accepts_fpp_{q:.0e}"] = n_pairs * q
            row["expected_lensed_pairs_low"] = n_ev * LENSED_PAIR_FRACTION[0]
            row["expected_lensed_pairs_mid"] = n_ev * LENSED_PAIR_FRACTION[1]
            row["expected_lensed_pairs_high"] = n_ev * LENSED_PAIR_FRACTION[2]
            row["fpp_for_0p1_false_accepts"] = 0.1 / max(n_pairs, 1)
            brow.append(row)
    budget = pd.DataFrame(brow)
    budget.to_csv(out / "false_alarm_budget.csv", index=False)
    summary["false_alarm_budget"] = budget.drop(columns=["label"]).to_dict(orient="records")

    plot_budget = budget[budget["catalogue"] == "all runs combined"]
    make_figures(out, delays, p, plot_budget, survivors_by)

    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps({k: summary[k] for k in ("n_events_total", "funnel", "sensitivity_survivors", "injections", "delays")}, indent=1, default=float))
    print(budget.drop(columns=["label"]).to_string(index=False))
    print(surv.head(15)[["event_i", "event_j", "delta_t_days", "sep_deg", "chi2_sky", "z_mc", "mc_i", "mc_j"]].to_string(index=False))
    if "GW170104_GW170814" in summary:
        print("GW170104-GW170814:", summary["GW170104_GW170814"])


if __name__ == "__main__":
    main()
