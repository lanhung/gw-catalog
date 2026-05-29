
#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path("/root/autodl-tmp/createdata/generated_10000_20260527_091859")
OUT = Path("/root/autodl-tmp/createdata/generated_10000_20260527_091859_qc_showcase")
OUT.mkdir(exist_ok=True)

LENSED = {
    ("PM", "ET"): BASE / "PM_GW_events_ET_10000",
    ("PM", "LIGO"): BASE / "PM_GW_events_LIGO_10000",
    ("SIS", "ET"): BASE / "SIS_GW_events_ET_10000",
    ("SIS", "LIGO"): BASE / "SIS_GW_events_LIGO_10000",
}
UNLENSED = {
    "ET": BASE / "unlensed_GW_events_ET_10000",
    "LIGO": BASE / "unlensed_GW_events_LIGO_10000",
}

def load(path):
    return np.load(path, mmap_mode="r")

def model_file(model, stem, image=None, ligo_network=False, ligo_single=False):
    if image is None:
        return f"{model}_{stem}.npy"
    if ligo_network:
        return f"{model}_{stem}_network_{image}.npy"
    if ligo_single:
        return f"{model}_{stem}_single_{image}.npy"
    return f"{model}_{stem}_{image}.npy"

def snr_arrays(model, detector, d):
    if detector == "ET":
        return {
            "image1": np.asarray(load(d / f"{model}_optimal_SNR_1.npy")),
            "image2": np.asarray(load(d / f"{model}_optimal_SNR_2.npy")),
        }
    return {
        "image1_network": np.asarray(load(d / f"{model}_optimal_SNR_network_1.npy")),
        "image2_network": np.asarray(load(d / f"{model}_optimal_SNR_network_2.npy")),
        "image1_H1": np.asarray(load(d / f"{model}_optimal_SNR_single_1.npy"))[:, 0],
        "image1_L1": np.asarray(load(d / f"{model}_optimal_SNR_single_1.npy"))[:, 1],
        "image2_H1": np.asarray(load(d / f"{model}_optimal_SNR_single_2.npy"))[:, 0],
        "image2_L1": np.asarray(load(d / f"{model}_optimal_SNR_single_2.npy"))[:, 1],
    }

def unlensed_snr(detector):
    d = UNLENSED[detector]
    if detector == "ET":
        return {"unlensed": np.asarray(load(d / "unlensed_optimal_SNR.npy"))}
    single = np.asarray(load(d / "unlensed_optimal_SNR_single.npy"))
    return {
        "unlensed_network": np.asarray(load(d / "unlensed_optimal_SNR_network.npy")),
        "unlensed_H1": single[:, 0],
        "unlensed_L1": single[:, 1],
    }

def flatten_for_plot(a):
    arr = np.asarray(a, dtype=float).ravel()
    return arr[np.isfinite(arr)]

def step_cdf(ax, values, label):
    values = np.sort(flatten_for_plot(values))
    if len(values) == 0:
        return
    y = np.arange(1, len(values) + 1) / len(values)
    ax.step(values, y, where="post", label=label)

# Fig1: representative lensed pairs, full and merger zoom.
fig, axes = plt.subplots(4, 2, figsize=(13, 12), constrained_layout=True)
for row, ((model, detector), d) in enumerate(LENSED.items()):
    h1 = load(d / f"{model}_h_strain_1.npy")
    h2 = load(d / f"{model}_h_strain_2.npy")
    t1 = load(d / f"{model}_time_array_1.npy")
    t2 = load(d / f"{model}_time_array_2.npy")
    if detector == "LIGO":
        h1_plot, h2_plot = np.asarray(h1[0, 0]), np.asarray(h2[0, 0])
        t1_plot, t2_plot = np.asarray(t1[0, 0]), np.asarray(t2[0, 0])
        chan = "H1"
    else:
        h1_plot, h2_plot = np.asarray(h1[0]), np.asarray(h2[0])
        t1_plot, t2_plot = np.asarray(t1[0]), np.asarray(t2[0])
        chan = "ET"
    ax = axes[row, 0]
    ax.plot(t1_plot - t1_plot[np.argmax(np.abs(h1_plot))], h1_plot, lw=0.8, label="image 1")
    ax.plot(t2_plot - t2_plot[np.argmax(np.abs(h2_plot))], h2_plot, lw=0.8, label="image 2", alpha=0.8)
    ax.set_title(f"{model} {detector} ({chan}) full whitened h")
    ax.set_xlabel("time from peak [s]")
    ax.set_ylabel("whitened strain")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)

    ax = axes[row, 1]
    peak1 = np.argmax(np.abs(h1_plot))
    peak2 = np.argmax(np.abs(h2_plot))
    rel1 = t1_plot - t1_plot[peak1]
    rel2 = t2_plot - t2_plot[peak2]
    m1 = (rel1 >= -0.15) & (rel1 <= 0.15)
    m2 = (rel2 >= -0.15) & (rel2 <= 0.15)
    ax.plot(rel1[m1], h1_plot[m1], lw=0.9, label="image 1")
    ax.plot(rel2[m2], h2_plot[m2], lw=0.9, label="image 2", alpha=0.8)
    ax.set_title(f"{model} {detector} 0.3 s merger zoom")
    ax.set_xlabel("time from peak [s]")
    ax.grid(alpha=0.25)
fig.savefig(OUT / "Fig1_lensed_pair_example.pdf")
fig.savefig(OUT / "Fig1_lensed_pair_example.png", dpi=180)
plt.close(fig)

# Fig2: SNR histograms and CDFs.
fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
for col, detector in enumerate(["ET", "LIGO"]):
    axh = axes[0, col]
    axc = axes[1, col]
    for model in ["PM", "SIS"]:
        d = LENSED[(model, detector)]
        arrays = snr_arrays(model, detector, d)
        for key, vals in arrays.items():
            if detector == "LIGO" and not key.endswith("network"):
                continue
            label = f"{model} {key}"
            vals = flatten_for_plot(vals)
            axh.hist(vals, bins=60, histtype="step", lw=1.4, label=label)
            step_cdf(axc, vals, label)
    for key, vals in unlensed_snr(detector).items():
        if detector == "LIGO" and key != "unlensed_network":
            continue
        vals = flatten_for_plot(vals)
        axh.hist(vals, bins=60, histtype="stepfilled", alpha=0.25, label=key)
        step_cdf(axc, vals, key)
    for ax in (axh, axc):
        ax.axvline(8, color="tab:red", ls="--", lw=1, label="SNR=8")
        ax.axvline(10, color="tab:orange", ls=":", lw=1, label="SNR=10")
        ax.set_xlabel("optimal SNR")
        ax.grid(alpha=0.25)
    axh.set_title(f"{detector} SNR histogram")
    axh.set_ylabel("count")
    axc.set_title(f"{detector} SNR CDF")
    axc.set_ylabel("CDF")
    handles, labels = axh.get_legend_handles_labels()
    uniq = dict(zip(labels, handles))
    axh.legend(uniq.values(), uniq.keys(), fontsize=7)
    handles, labels = axc.get_legend_handles_labels()
    uniq = dict(zip(labels, handles))
    axc.legend(uniq.values(), uniq.keys(), fontsize=7)
fig.savefig(OUT / "Fig2_SNR_distribution.pdf")
fig.savefig(OUT / "Fig2_SNR_distribution.png", dpi=180)
plt.close(fig)

# Fig3: magnification distributions.
fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
for row, model in enumerate(["PM", "SIS"]):
    d = LENSED[(model, "ET")]
    lens = pd.read_csv(d / "lens.csv")
    mu0 = lens["mu_0"].to_numpy()
    mu1 = np.abs(lens["mu_1"].to_numpy())
    mut = mu0 + mu1
    for ax, vals, title in zip(axes[row], [mu0, mu1, mut], ["mu_0", "abs(mu_1)", "mu_total"]):
        ax.hist(vals, bins=60, color="tab:blue", alpha=0.7)
        ax.set_title(f"{model} {title}")
        ax.grid(alpha=0.25)
        ax.set_ylabel("count")
        ax.text(0.02, 0.95, f"frac > 1: {np.mean(vals > 1):.2f}" if title != "mu_total" else f"frac > 2: {np.mean(vals > 2):.2f}", transform=ax.transAxes, va="top", fontsize=9)
fig.savefig(OUT / "Fig3_magnification_distribution.pdf")
fig.savefig(OUT / "Fig3_magnification_distribution.png", dpi=180)
plt.close(fig)

# Fig4: time delay distributions and trends.
fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
for row, model in enumerate(["PM", "SIS"]):
    d = LENSED[(model, "ET")]
    lens = pd.read_csv(d / "lens.csv")
    params = pd.read_csv(d / "lens_params.csv")
    dt = lens["t_d"].to_numpy()
    axes[row, 0].hist(dt, bins=60, color="tab:green", alpha=0.75)
    axes[row, 0].set_title(f"{model} delta_t")
    axes[row, 0].set_xlabel("delta_t [s]")
    xcol = "m_l" if model == "PM" else "sigma_v"
    axes[row, 1].scatter(params[xcol], dt, s=30)
    axes[row, 1].set_title(f"{model} delta_t vs {xcol}")
    axes[row, 1].set_xlabel(xcol)
    axes[row, 1].set_ylabel("delta_t [s]")
    axes[row, 2].scatter(params["y"], dt, s=30, color="tab:purple")
    axes[row, 2].set_title(f"{model} delta_t vs y")
    axes[row, 2].set_xlabel("y")
    for ax in axes[row]:
        ax.grid(alpha=0.25)
fig.savefig(OUT / "Fig4_time_delay_distribution.pdf")
fig.savefig(OUT / "Fig4_time_delay_distribution.png", dpi=180)
plt.close(fig)

# Fig5: lens parameter distributions.
fig, axes = plt.subplots(2, 4, figsize=(14, 7), constrained_layout=True)
for row, model in enumerate(["PM", "SIS"]):
    d = LENSED[(model, "ET")]
    params = pd.read_csv(d / "lens_params.csv")
    cols = ["m_l" if model == "PM" else "sigma_v", "y", "z_l", "z_s"]
    for ax, col in zip(axes[row], cols):
        ax.hist(params[col], bins=60, color="tab:cyan", alpha=0.75)
        ax.set_title(f"{model} {col}")
        ax.grid(alpha=0.25)
fig.savefig(OUT / "Fig5_lens_parameter_distribution.pdf")
fig.savefig(OUT / "Fig5_lens_parameter_distribution.png", dpi=180)
plt.close(fig)

# Tables.
rep_rows = []
for (model, detector), d in LENSED.items():
    lens = pd.read_csv(d / "lens.csv")
    params = pd.read_csv(d / "lens_params.csv")
    src = pd.read_csv(d / "lensed_source_samples.csv")
    row = {"model": model, "detector": detector, "event_index": 0}
    for col in ["mass_1_source", "mass_2_source", "luminosity_distance", "geocent_time"]:
        row[col] = src.loc[0, col]
    for col in params.columns:
        row[col] = params.loc[0, col]
    for col in lens.columns:
        row[col] = lens.loc[0, col]
    row["mu_total"] = abs(row["mu_0"]) + abs(row["mu_1"])
    if detector == "ET":
        row["SNR_image1"] = float(load(d / f"{model}_optimal_SNR_1.npy")[0])
        row["SNR_image2"] = float(load(d / f"{model}_optimal_SNR_2.npy")[0])
    else:
        row["SNR_image1_network"] = float(load(d / f"{model}_optimal_SNR_network_1.npy")[0])
        row["SNR_image2_network"] = float(load(d / f"{model}_optimal_SNR_network_2.npy")[0])
        single1 = load(d / f"{model}_optimal_SNR_single_1.npy")
        single2 = load(d / f"{model}_optimal_SNR_single_2.npy")
        row["SNR_image1_H1"] = float(single1[0, 0])
        row["SNR_image1_L1"] = float(single1[0, 1])
        row["SNR_image2_H1"] = float(single2[0, 0])
        row["SNR_image2_L1"] = float(single2[0, 1])
    rep_rows.append(row)
pd.DataFrame(rep_rows).to_csv(OUT / "Table1_representative_event_parameters.csv", index=False)

summary_rows = []
def add_summary(dataset, metric, values):
    values = flatten_for_plot(values)
    summary_rows.append({
        "dataset": dataset,
        "metric": metric,
        "n": int(len(values)),
        "finite": int(np.isfinite(values).sum()),
        "nan": int(np.isnan(values).sum()),
        "min": float(np.min(values)) if len(values) else np.nan,
        "p05": float(np.percentile(values, 5)) if len(values) else np.nan,
        "median": float(np.median(values)) if len(values) else np.nan,
        "mean": float(np.mean(values)) if len(values) else np.nan,
        "p95": float(np.percentile(values, 95)) if len(values) else np.nan,
        "max": float(np.max(values)) if len(values) else np.nan,
        "frac_gt_1": float(np.mean(values > 1)) if len(values) else np.nan,
        "frac_gt_2": float(np.mean(values > 2)) if len(values) else np.nan,
        "frac_gt_8": float(np.mean(values > 8)) if len(values) else np.nan,
        "frac_gt_10": float(np.mean(values > 10)) if len(values) else np.nan,
    })

for (model, detector), d in LENSED.items():
    lens = pd.read_csv(d / "lens.csv")
    params = pd.read_csv(d / "lens_params.csv")
    src = pd.read_csv(d / "source_samples.csv")
    prefix = f"{model}_{detector}"
    for col in ["mass_1_source", "mass_2_source", "luminosity_distance", "geocent_time"]:
        add_summary(prefix, col, src[col])
    for col in params.columns:
        add_summary(prefix, col, params[col])
    add_summary(prefix, "mu_0", lens["mu_0"])
    add_summary(prefix, "abs_mu_1", np.abs(lens["mu_1"]))
    add_summary(prefix, "mu_total", np.abs(lens["mu_0"]) + np.abs(lens["mu_1"]))
    add_summary(prefix, "delta_t", lens["t_d"])
    for key, vals in snr_arrays(model, detector, d).items():
        add_summary(prefix, f"SNR_{key}", vals)
for detector, d in UNLENSED.items():
    src = pd.read_csv(d / "source_samples.csv")
    prefix = f"unlensed_{detector}"
    for col in ["mass_1_source", "mass_2_source", "luminosity_distance", "geocent_time"]:
        add_summary(prefix, col, src[col])
    for key, vals in unlensed_snr(detector).items():
        add_summary(prefix, f"SNR_{key}", vals)
pd.DataFrame(summary_rows).to_csv(OUT / "Table2_population_summary.csv", index=False)

# Compact markdown notes for quick review.
notes = ["# QC showcase", "", "Generated files:"]
for p in sorted(OUT.iterdir()):
    notes.append(f"- {p.name}")
notes.append("")
notes.append("Key checks:")
for model in ["PM", "SIS"]:
    d = LENSED[(model, "ET")]
    lens = pd.read_csv(d / "lens.csv")
    mut = np.abs(lens["mu_0"]) + np.abs(lens["mu_1"])
    notes.append(f"- {model}: fraction(mu_total > 2) = {np.mean(mut > 2):.3f}; delta_t range = {lens['t_d'].min():.6g} to {lens['t_d'].max():.6g} s")
notes.append("- LIGO figures use network SNR for the main comparison; H1/L1 SNR values are included in Table1/Table2.")
(OUT / "QC_summary.md").write_text("\n".join(notes) + "\n")
print(f"Wrote showcase to {OUT.resolve()}")
