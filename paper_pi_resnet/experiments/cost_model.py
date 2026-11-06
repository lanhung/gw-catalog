"""Cost-benefit model for a staged lensed-pair search.

Answers the reviewer's main objection: a per-pair method must be judged by the
combination of efficiency, false-alarm probability per pair, per-pair cost and
the cost of the downstream analysis it feeds, not by speed or efficiency alone.

Three ways of handling the N_pair candidate pairs of a catalogue are compared:

  A. posterior-overlap statistic only   (Barsode et al.: eff e_B at FAP p_B, cost c_B per pair)
  B. PI-ResNet only                     (eff e_P at FAP p_P, cost c_P per pair)
  C. PI-ResNet as a pre-filter in front of A

Every pair that survives the last fast stage is assumed to go to a full
Bayesian joint analysis at cost C_PE per pair.  The total expected compute per
input pair is

  A:  c_B + p_B * C_PE
  B:  c_P + p_P * C_PE
  C:  c_P + p_P * c_B + p_P * p_B * C_PE          (stages assumed independent)

and the efficiencies are e_B, e_P and e_P * e_B (independence; a lower bound if
the two statistics respond to the same pairs, which they should, since both are
limited by the fainter image's SNR).

Numbers for the posterior-overlap method are taken from the reviewer's summary
("~54% efficiency at FPP 1e-6, under a second per pair") and MUST be replaced
by the values quoted in Barsode et al. (arXiv:2412.01278, 2605.10333) once
those papers have been read.  PI-ResNet numbers are the frozen 0228 results.

Run:  python paper_pi_resnet/experiments/cost_model.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "legend.fontsize": 7.5, "figure.dpi": 150})

# --- operating points ----------------------------------------------------------
# PI-ResNet (SIS, frozen 0228 evaluation).  eff at 1e-2 is not in the docs
# snapshot: EFF_P_1E2 is a placeholder to be replaced from
# results/core/fixed_fpp_primary_table.csv on the server.
PI = {
    1e-2: {"eff": None, "note": "fill from fixed_fpp_primary_table.csv"},
    1e-3: {"eff": 0.535},
    1e-4: {"eff": None, "note": "fill from fixed_fpp_primary_table.csv"},
}
C_P = 1.24e-3  # s per pair, end-to-end serial (GPU inference + preprocessing)

# Posterior-overlap statistic (Barsode et al.), as summarised by the reviewer.
E_B, P_B, C_B = 0.54, 1e-6, 1.0  # efficiency, FAP per pair, s per pair (upper bound "under a second")

# Downstream full Bayesian joint analysis cost per pair (CPU-seconds).  Joint
# parameter estimation of a lensed pair typically takes hours to days of CPU.
C_PE_GRID = np.logspace(0, 6, 400)  # 1 s .. 1e6 s (~12 days)
C_PE_REF = 3600.0 * 24  # one CPU-day, used for the table

# Catalogue scales: number of candidate pairs per year.
N_PAIRS = {
    "O4-like year (~200 BBH)": 200 * 199 / 2,
    "O5-like year (~1000 BBH)": 1000 * 999 / 2,
    "ET year (~1e5 BBH)": 1e5 * (1e5 - 1) / 2,
}


def cost_per_pair(p_p: float, c_pe: np.ndarray | float) -> dict[str, np.ndarray | float]:
    return {
        "A_overlap_only": C_B + P_B * c_pe,
        "B_piresnet_only": C_P + p_p * c_pe,
        "C_prefilter_then_overlap": C_P + p_p * C_B + p_p * P_B * c_pe,
    }


def main() -> None:
    rows = []
    for p_p, d in PI.items():
        e_p = d["eff"]
        c = cost_per_pair(p_p, C_PE_REF)
        rows.append({
            "piresnet_fap": p_p,
            "piresnet_eff": e_p,
            "cost_A_overlap_only_s": c["A_overlap_only"],
            "cost_B_piresnet_only_s": c["B_piresnet_only"],
            "cost_C_prefilter_s": c["C_prefilter_then_overlap"],
            "eff_A": E_B,
            "eff_B": e_p,
            "eff_C_independent": (e_p * E_B) if e_p is not None else None,
            "eff_C_nested_upper": min(e_p, E_B) if e_p is not None else None,
            # downstream pairs per input pair
            "downstream_A": P_B,
            "downstream_B": p_p,
            "downstream_C": p_p * P_B,
            # break-even downstream cost: B cheaper than A when C_PE below this
            "break_even_C_PE_B_vs_A_s": (C_B - C_P) / (p_p - P_B),
            "speedup_C_vs_A_at_1_CPU_day": c["A_overlap_only"] / c["C_prefilter_then_overlap"],
        })
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "cost_model_table.csv", index=False)

    # catalogue-scale totals at the primary PI-ResNet point and one CPU-day PE
    scale_rows = []
    for name, n in N_PAIRS.items():
        c = cost_per_pair(1e-3, C_PE_REF)
        scale_rows.append({
            "catalogue": name, "n_pairs": n,
            "A_overlap_only_CPU_years": n * c["A_overlap_only"] / 3.156e7,
            "B_piresnet_only_CPU_years": n * c["B_piresnet_only"] / 3.156e7,
            "C_prefilter_CPU_years": n * c["C_prefilter_then_overlap"] / 3.156e7,
            "A_pairs_to_PE": n * P_B, "B_pairs_to_PE": n * 1e-3, "C_pairs_to_PE": n * 1e-3 * P_B,
        })
    scale = pd.DataFrame(scale_rows)
    scale.to_csv(OUT / "cost_model_catalogue_scale.csv", index=False)

    # figure: total cost per pair versus downstream cost
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    c = cost_per_pair(1e-3, C_PE_GRID)
    ax.plot(C_PE_GRID, c["A_overlap_only"], color="#9467bd", lw=1.3, label="posterior overlap only (FAP $10^{-6}$)")
    ax.plot(C_PE_GRID, c["B_piresnet_only"], color="#1f77b4", lw=1.3, label="PI-ResNet only (FAP $10^{-3}$)")
    ax.plot(C_PE_GRID, c["C_prefilter_then_overlap"], color="#d62728", lw=1.3, label="PI-ResNet pre-filter, then overlap")
    be = (C_B - C_P) / (1e-3 - P_B)
    ax.axvline(be, color="0.5", lw=0.7, ls=":")
    ax.text(be * 0.75, 3e-2, f"break-even: {be/60:.0f} min", fontsize=6.5, color="0.3", ha="right")
    for x, lab in ((3600, "1 hour"), (86400, "1 day")):
        ax.axvline(x, color="0.8", lw=0.6, ls="--")
        ax.text(x * 1.15, 3e-3, lab, fontsize=6.5, color="0.4", rotation=90, va="bottom")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Cost of full Bayesian follow-up per pair [CPU s]")
    ax.set_ylabel("Expected compute per candidate pair [CPU s]")
    ax.legend(frameon=False, loc="upper left", fontsize=6.8)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig_cost_model.{ext}", bbox_inches="tight")
    plt.close(fig)

    print(table.to_string(index=False))
    print()
    print(scale.to_string(index=False))
    (OUT / "cost_model_params.json").write_text(json.dumps(
        {"PI": PI, "C_P_s": C_P, "overlap": {"eff": E_B, "fap": P_B, "cost_s": C_B}, "C_PE_ref_s": C_PE_REF}, indent=2))


if __name__ == "__main__":
    main()
