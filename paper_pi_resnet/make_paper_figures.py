"""Figures for the revised PI-ResNet manuscript that are built from published numbers.

Simulation-result values are copied from docs/RESULTS.md of the PI-ResNet
repository (frozen 0228 evaluation).  Catalogue figures are produced by
scripts/gwtc/05_catalog_context_for_pair_verification.py and copied here.
"""

from pathlib import Path
import shutil

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import hilbert

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
REPO = HERE.parent
CTX = REPO / "runs" / "gwtc_catalog_context_20261001"
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "legend.fontsize": 7.5, "figure.dpi": 150})


def schematic():
    """Two images of one chirp: brighter type-I image and fainter, delayed type-II image."""
    fs = 2048
    t = np.arange(-1.6, 0.05, 1 / fs)
    tau = np.clip(-t, 1e-3, None)
    # leading-order (Newtonian) chirp, chirp mass ~ 30 Msun detector frame; truncated at merger
    f = 134.0 * (1.21 / 1.21) * (tau / 1.0) ** (-3 / 8) * (30 / 30) ** (-5 / 8) / 8.0
    f = np.clip(f, 15, 400)
    phase = 2 * np.pi * np.cumsum(f) / fs
    amp = (f / f.max()) ** (2 / 3) * np.where(t < 0, 1, np.exp(-t / 0.004))
    h = amp * np.cos(phase)
    mu1, mu2 = 4.0, 2.0
    h1 = np.sqrt(mu1) * h
    h2 = np.sqrt(mu2) * np.imag(hilbert(h))  # Morse phase n=1/2: Hilbert transform of h
    h2_naive = np.sqrt(mu2) * h

    fig, axes = plt.subplots(3, 1, figsize=(3.4, 3.6), sharex=True)
    axes[0].plot(t, h1, color="#1f77b4", lw=0.8)
    axes[0].set_title("Image I (arrives first): $\\sqrt{\\mu_1}\\,h(t)$  [illustrative chirp]", fontsize=8, loc="left")
    axes[1].plot(t, h2, color="#d62728", lw=0.8)
    axes[1].plot(t, h2_naive, color="0.6", lw=0.6, ls="--")
    axes[1].set_title("Image II (days later, fainter, type II): phase shifted by $\\pi/2$", fontsize=8, loc="left")
    rng = np.random.default_rng(3)
    axes[2].plot(t, h2 + 1.3 * rng.normal(size=t.size), color="0.35", lw=0.4)
    axes[2].plot(t, h2, color="#d62728", lw=0.8)
    axes[2].set_title("What the detector records: image II plus noise", fontsize=8, loc="left")
    for a in axes:
        a.set_yticks([])
        a.set_xlim(-0.5, 0.04)
    axes[2].set_xlabel("Time relative to merger peak [s]")
    fig.tight_layout(h_pad=0.4)
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"fig_lensing_schematic.{ext}", bbox_inches="tight")
    plt.close(fig)


def efficiency_bars():
    # efficiency at per-pair false-alarm probability 1e-3 (95% intervals), frozen 0228 evaluation
    vals = {
        ("SIS", "PI-ResNet"): (0.5354, 0.5097, 0.5629),
        ("SIS", "CQT-DeiT"): (0.3771, 0.3589, 0.3949),
        ("Point mass", "PI-ResNet"): (0.2274, 0.2109, 0.2457),
        ("Point mass", "CQT-DeiT"): (0.0926, 0.0817, 0.1040),
    }
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    lenses = ["SIS", "Point mass"]
    models = [("PI-ResNet", "#1f77b4"), ("CQT-DeiT", "#ff7f0e")]
    w = 0.36
    for k, (m, c) in enumerate(models):
        x = np.arange(2) + (k - 0.5) * w
        y = [vals[(l, m)][0] for l in lenses]
        lo = [vals[(l, m)][0] - vals[(l, m)][1] for l in lenses]
        hi = [vals[(l, m)][2] - vals[(l, m)][0] for l in lenses]
        ax.bar(x, y, w, color=c, label=m, yerr=[lo, hi], capsize=3, error_kw={"lw": 0.8})
        for xi, yi in zip(x, y):
            ax.text(xi, yi + 0.04, f"{yi:.2f}", ha="center", fontsize=7)
    ax.set_xticks(range(2))
    ax.set_xticklabels(["Galaxy-like lens\n(SIS)", "Compact lens\n(point mass)"])
    ax.set_ylabel("Fraction of lensed pairs found")
    ax.set_ylim(0, 0.7)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("Threshold: 1 unrelated pair in 1000 accepted", fontsize=8)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"fig_efficiency_1e-3.{ext}", bbox_inches="tight")
    plt.close(fig)


def transfer():
    # efficiency at 1e-3 on each lens family's test pairs, with matched vs swapped training
    data = {
        "PI-ResNet": {"SIS test": (0.535, 0.221), "PM test": (0.227, 0.398)},
        "CQT-DeiT": {"SIS test": (0.377, 0.170), "PM test": (0.093, 0.314)},
    }
    fig, axes = plt.subplots(1, 2, figsize=(3.4, 2.2), sharey=True)
    for ax, (model, d) in zip(axes, data.items()):
        x = np.arange(2)
        same = [d["SIS test"][0], d["PM test"][0]]
        swap = [d["SIS test"][1], d["PM test"][1]]
        ax.bar(x - 0.18, same, 0.36, color="#1f77b4", label="trained on same lens")
        ax.bar(x + 0.18, swap, 0.36, color="#9467bd", label="trained on other lens")
        ax.set_xticks(x)
        ax.set_xticklabels(["SIS pairs", "PM pairs"])
        ax.set_title(model, fontsize=8)
    axes[0].set_ylabel("Fraction found (FAP $10^{-3}$)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=7, loc="lower center", bbox_to_anchor=(0.55, 0.98), ncol=2)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"fig_transfer.{ext}", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True)
    schematic()
    efficiency_bars()
    transfer()
    for name in ("fig_time_delays", "fig_catalog_funnel", "fig_false_alarm_budget", "fig_real_pairs_plane"):
        for ext in ("pdf", "png"):
            shutil.copy(CTX / f"{name}.{ext}", FIG / f"{name}.{ext}")
    print("figures written to", FIG)
