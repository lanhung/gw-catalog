
#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("generated_10000_20260527_091859")
OUT = ROOT / "qc_showcase_adaptive_peak"
OUT.mkdir(exist_ok=True)

LENSED = {
    ("PM", "ET"): ROOT / "PM_GW_events_ET_10000",
    ("PM", "LIGO"): ROOT / "PM_GW_events_LIGO_10000",
    ("SIS", "ET"): ROOT / "SIS_GW_events_ET_10000",
    ("SIS", "LIGO"): ROOT / "SIS_GW_events_LIGO_10000",
}
UNLENSED = {
    "ET": ROOT / "unlensed_GW_events_ET_10000",
    "LIGO": ROOT / "unlensed_GW_events_LIGO_10000",
}

plt.rcParams.update({
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.22,
    "font.size": 9,
})

def load(path):
    return np.load(path, mmap_mode="r")

def finite(a):
    a = np.asarray(a, dtype=float).ravel()
    return a[np.isfinite(a)]

def snr_main(model, detector, d, image):
    if detector == "ET":
        return np.asarray(load(d / f"{model}_optimal_SNR_{image}.npy"))
    return np.asarray(load(d / f"{model}_optimal_SNR_network_{image}.npy"))

def snr_arrays(model, detector, d):
    if detector == "ET":
        return {
            "image1": np.asarray(load(d / f"{model}_optimal_SNR_1.npy")),
            "image2": np.asarray(load(d / f"{model}_optimal_SNR_2.npy")),
        }
    single1 = np.asarray(load(d / f"{model}_optimal_SNR_single_1.npy"))
    single2 = np.asarray(load(d / f"{model}_optimal_SNR_single_2.npy"))
    return {
        "image1_network": np.asarray(load(d / f"{model}_optimal_SNR_network_1.npy")),
        "image2_network": np.asarray(load(d / f"{model}_optimal_SNR_network_2.npy")),
        "image1_H1": single1[:, 0],
        "image1_L1": single1[:, 1],
        "image2_H1": single2[:, 0],
        "image2_L1": single2[:, 1],
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

def choose_representative_index(model, detector, d):
    s1 = snr_main(model, detector, d, 1)
    s2 = snr_main(model, detector, d, 2)
    score = np.minimum(s1, s2)
    score = np.where(np.isfinite(score), score, -np.inf)
    return int(np.argmax(score))

def event_wave(model, detector, d, image, idx):
    h = load(d / f"{model}_h_strain_{image}.npy")
    data = load(d / f"{model}_data_strain_{image}.npy")
    t = load(d / f"{model}_time_array_{image}.npy")
    if detector == "LIGO":
        # Use the louder LIGO detector for the representative event so the peak is visible.
        single = load(d / f"{model}_optimal_SNR_single_{image}.npy")
        chan = int(np.argmax(single[idx]))
        chan_name = ["H1", "L1"][chan]
        return np.asarray(t[idx, chan]), np.asarray(data[idx, chan]), np.asarray(h[idx, chan]), chan_name
    return np.asarray(t[idx]), np.asarray(data[idx]), np.asarray(h[idx]), "ET"

def adaptive_window(t, y, min_half_width=0.045, max_half_width=0.35, floor_frac=0.18):
    y = np.asarray(y)
    t = np.asarray(t)
    peak = int(np.argmax(np.abs(y)))
    peak_t = float(t[peak])
    amp = np.abs(y)
    peak_amp = float(amp[peak])
    if not np.isfinite(peak_amp) or peak_amp == 0:
        return peak_t - 0.15, peak_t + 0.15, peak_t, peak_amp
    threshold = peak_amp * floor_frac
    above = np.where(amp >= threshold)[0]
    near = above[np.abs(above - peak) < int(0.8 * len(y))]
    if len(near):
        left_t = float(t[max(0, near.min())])
        right_t = float(t[min(len(t) - 1, near.max())])
        half = max(abs(peak_t - left_t), abs(right_t - peak_t)) * 1.8
    else:
        half = min_half_width
    half = min(max(half, min_half_width), max_half_width)
    return peak_t - half, peak_t + half, peak_t, peak_amp

def plot_peak_pair(ax, t1, y1, t2, y2, label1, label2, title, ylabel):
    lo1, hi1, p1, a1 = adaptive_window(t1, y1)
    lo2, hi2, p2, a2 = adaptive_window(t2, y2)
    rel1 = t1 - p1
    rel2 = t2 - p2
    half = max(p1 - lo1, hi1 - p1, p2 - lo2, hi2 - p2)
    half = min(max(half, 0.045), 0.35)
    m1 = (rel1 >= -half) & (rel1 <= half)
    m2 = (rel2 >= -half) & (rel2 <= half)
    ax.plot(rel1[m1], y1[m1], lw=0.85, label=label1)
    ax.plot(rel2[m2], y2[m2], lw=0.85, label=label2, alpha=0.78)
    ax.axvline(0, color="black", lw=0.8, ls="--", alpha=0.7)
    ax.scatter([0], [y1[np.argmax(np.abs(y1))]], s=16, color="tab:blue", zorder=3)
    ax.scatter([0], [y2[np.argmax(np.abs(y2))]], s=16, color="tab:orange", zorder=3)
    ax.set_xlim(-half, half)
    yvals = np.concatenate([y1[m1], y2[m2]])
    if len(yvals):
        ymin, ymax = np.nanpercentile(yvals, [0.5, 99.5])
        pad = 0.12 * max(abs(ymax - ymin), 1e-12)
        ax.set_ylim(ymin - pad, ymax + pad)
    ax.set_title(title)
    ax.set_xlabel("time from each image peak [s]")
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=7, loc="upper right")

def step_cdf(ax, values, label):
    values = np.sort(finite(values))
    if len(values) == 0:
        return
    ax.step(values, np.arange(1, len(values) + 1) / len(values), where="post", label=label)

# Fig1: adaptive peak-centered waveform/data display.
fig, axes = plt.subplots(4, 2, figsize=(14, 12), constrained_layout=True)
rep_rows = []
for row, ((model, detector), d) in enumerate(LENSED.items()):
    idx = choose_representative_index(model, detector, d)
    t1, data1, h1, ch1 = event_wave(model, detector, d, 1, idx)
    t2, data2, h2, ch2 = event_wave(model, detector, d, 2, idx)
    s1 = snr_main(model, detector, d, 1)[idx]
    s2 = snr_main(model, detector, d, 2)[idx]
    title = f"{model} {detector} event {idx} ({ch1}/{ch2}); SNR {s1:.1f}, {s2:.1f}"
    plot_peak_pair(axes[row, 0], t1, data1, t2, data2, "image 1 data", "image 2 data", title + " data", "whitened data")
    plot_peak_pair(axes[row, 1], t1, h1, t2, h2, "image 1 h", "image 2 h", title + " signal h", "whitened h")
    rep_rows.append({"model": model, "detector": detector, "event_index": idx, "channel_image1": ch1, "channel_image2": ch2, "SNR_image1_main": float(s1), "SNR_image2_main": float(s2)})
fig.savefig(OUT / "Fig1_lensed_pair_example_adaptive_peak.pdf")
fig.savefig(OUT / "Fig1_lensed_pair_example_adaptive_peak.png", dpi=180)
plt.close(fig)

# Fig2: auto-scaled SNR hist/CDF, no shared x-axis.
fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
for col, detector in enumerate(["ET", "LIGO"]):
    axh, axc = axes[0, col], axes[1, col]
    for model in ["PM", "SIS"]:
        arrays = snr_arrays(model, detector, LENSED[(model, detector)])
        for key, vals in arrays.items():
            if detector == "LIGO" and not key.endswith("network"):
                continue
            vals = finite(vals)
            axh.hist(vals, bins=60, histtype="step", lw=1.3, label=f"{model} {key}")
            step_cdf(axc, vals, f"{model} {key}")
    for key, vals in unlensed_snr(detector).items():
        if detector == "LIGO" and key != "unlensed_network":
            continue
        vals = finite(vals)
        axh.hist(vals, bins=60, histtype="stepfilled", alpha=0.22, label=key)
        step_cdf(axc, vals, key)
    for ax in [axh, axc]:
        ax.axvline(8, color="tab:red", ls="--", lw=1, label="SNR=8")
        ax.axvline(10, color="tab:orange", ls=":", lw=1, label="SNR=10")
        ax.set_xlabel("optimal SNR")
    axh.set_title(f"{detector} SNR histogram (auto x-axis)")
    axh.set_ylabel("count")
    axc.set_title(f"{detector} SNR CDF (auto x-axis)")
    axc.set_ylabel("CDF")
    for ax in [axh, axc]:
        handles, labels = ax.get_legend_handles_labels()
        uniq = dict(zip(labels, handles))
        ax.legend(uniq.values(), uniq.keys(), fontsize=7)
fig.savefig(OUT / "Fig2_SNR_distribution_adaptive_axis.pdf")
fig.savefig(OUT / "Fig2_SNR_distribution_adaptive_axis.png", dpi=180)
plt.close(fig)

# Fig3: magnification distributions.
fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
for row, model in enumerate(["PM", "SIS"]):
    lens = pd.read_csv(LENSED[(model, "ET")] / "lens.csv")
    vals = [lens["mu_0"].to_numpy(), np.abs(lens["mu_1"].to_numpy()), np.abs(lens["mu_0"].to_numpy()) + np.abs(lens["mu_1"].to_numpy())]
    titles = ["mu_0", "abs(mu_1)", "mu_total"]
    for ax, v, title in zip(axes[row], vals, titles):
        ax.hist(v, bins=70, color="tab:blue", alpha=0.72)
        ax.axvline(np.median(v), color="black", ls="--", lw=1, label="median")
        txt = f"frac > 2: {np.mean(v > 2):.3f}" if title == "mu_total" else f"frac > 1: {np.mean(v > 1):.3f}"
        ax.text(0.02, 0.95, txt, transform=ax.transAxes, va="top")
        ax.set_title(f"{model} {title}")
        ax.set_ylabel("count")
        ax.legend(fontsize=7)
fig.savefig(OUT / "Fig3_magnification_distribution_adaptive_axis.pdf")
fig.savefig(OUT / "Fig3_magnification_distribution_adaptive_axis.png", dpi=180)
plt.close(fig)

# Fig4: time delay distributions and trends.
fig, axes = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
for row, model in enumerate(["PM", "SIS"]):
    d = LENSED[(model, "ET")]
    lens = pd.read_csv(d / "lens.csv")
    params = pd.read_csv(d / "lens_params.csv")
    dt = lens["t_d"].to_numpy()
    axes[row, 0].hist(dt, bins=70, color="tab:green", alpha=0.72)
    axes[row, 0].axvline(np.median(dt), color="black", ls="--", lw=1)
    axes[row, 0].set_title(f"{model} delta_t histogram")
    axes[row, 0].set_xlabel("delta_t [s]")
    xcol = "m_l" if model == "PM" else "sigma_v"
    axes[row, 1].scatter(params[xcol], dt, s=4, alpha=0.35)
    axes[row, 1].set_title(f"{model} delta_t vs {xcol}")
    axes[row, 1].set_xlabel(xcol)
    axes[row, 1].set_ylabel("delta_t [s]")
    axes[row, 2].scatter(params["y"], dt, s=4, alpha=0.35, color="tab:purple")
    axes[row, 2].set_title(f"{model} delta_t vs y")
    axes[row, 2].set_xlabel("y")
fig.savefig(OUT / "Fig4_time_delay_distribution_adaptive_axis.pdf")
fig.savefig(OUT / "Fig4_time_delay_distribution_adaptive_axis.png", dpi=180)
plt.close(fig)

# Fig5: lens parameters.
fig, axes = plt.subplots(2, 4, figsize=(14, 7), constrained_layout=True)
for row, model in enumerate(["PM", "SIS"]):
    params = pd.read_csv(LENSED[(model, "ET")] / "lens_params.csv")
    cols = ["m_l" if model == "PM" else "sigma_v", "y", "z_l", "z_s"]
    for ax, col in zip(axes[row], cols):
        ax.hist(params[col], bins=70, color="tab:cyan", alpha=0.75)
        ax.axvline(params[col].median(), color="black", ls="--", lw=1)
        ax.set_title(f"{model} {col}")
fig.savefig(OUT / "Fig5_lens_parameter_distribution_adaptive_axis.pdf")
fig.savefig(OUT / "Fig5_lens_parameter_distribution_adaptive_axis.png", dpi=180)
plt.close(fig)

# Tables.
rep_detail = []
for base in rep_rows:
    model, detector, idx = base["model"], base["detector"], base["event_index"]
    d = LENSED[(model, detector)]
    lens = pd.read_csv(d / "lens.csv")
    params = pd.read_csv(d / "lens_params.csv")
    src = pd.read_csv(d / "lensed_source_samples.csv")
    row = dict(base)
    for col in ["mass_1_source", "mass_2_source", "luminosity_distance", "geocent_time"]:
        row[col] = src.loc[idx, col]
    for col in params.columns:
        row[col] = params.loc[idx, col]
    for col in lens.columns:
        row[col] = lens.loc[idx, col]
    row["mu_total"] = abs(row["mu_0"]) + abs(row["mu_1"])
    rep_detail.append(row)
pd.DataFrame(rep_detail).to_csv(OUT / "Table1_representative_event_parameters_adaptive_peak.csv", index=False)

summary_rows = []
def add_summary(dataset, metric, values):
    values = finite(values)
    summary_rows.append({
        "dataset": dataset,
        "metric": metric,
        "n": int(len(values)),
        "nan": int(np.isnan(values).sum()),
        "min": float(np.min(values)) if len(values) else np.nan,
        "p01": float(np.percentile(values, 1)) if len(values) else np.nan,
        "p05": float(np.percentile(values, 5)) if len(values) else np.nan,
        "median": float(np.median(values)) if len(values) else np.nan,
        "mean": float(np.mean(values)) if len(values) else np.nan,
        "p95": float(np.percentile(values, 95)) if len(values) else np.nan,
        "p99": float(np.percentile(values, 99)) if len(values) else np.nan,
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
pd.DataFrame(summary_rows).to_csv(OUT / "Table2_population_summary_adaptive_peak.csv", index=False)

notes = [
    "# Adaptive peak QC showcase",
    "",
    f"Input root: {ROOT}",
    "",
    "Fig1 changes:",
    "- Representative event is chosen by max min(image1 SNR, image2 SNR).",
    "- Each row uses its own peak-centered x-axis window.",
    "- x=0 is the peak of each plotted image; peak markers are drawn explicitly.",
    "- LIGO uses the louder detector channel per image for the representative plot.",
    "",
    "Generated files:",
]
for p in sorted(OUT.iterdir()):
    notes.append(f"- {p.name}")
(OUT / "QC_summary_adaptive_peak.md").write_text("\n".join(notes) + "\n")
print(f"Wrote adaptive showcase to {OUT.resolve()}")
