"""Write the realistic-population table (LaTeX) from population_summary.json.

Produces paper_pi_resnet/experiments/population_table.tex, a ``table`` ready
to be \\input into the manuscript, plus a Markdown copy for the response.

  python paper_pi_resnet/experiments/make_population_table.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUMMARY = REPO / "data" / "ler_population" / "population_summary.json"
OUT = Path(__file__).resolve().parent


def fmt(x, nd=1):
    return "--" if x is None else f"{x:.{nd}f}"


def pct(x):
    return "--" if x is None else f"{100 * x:.0f}\\%"


def main() -> None:
    s = json.loads(SUMMARY.read_text())
    cfgs = [c for c in ("O4", "ET") if c in s]
    rows = [
        ("Detected BBH rate [yr$^{-1}$]", lambda d: fmt(d.get("unlensed_rate_per_yr"), 0)),
        ("Lensed systems with two detected images [yr$^{-1}$]", lambda d: fmt(d.get("lensed_rate_per_yr"), 2)),
        ("Lensed fraction among detections", lambda d: "--" if d.get("lensed_fraction") is None else f"{d['lensed_fraction']:.1e}"),
        ("Median source redshift of lensed pairs", lambda d: fmt(d["zs"]["median"], 2)),
        ("Lensed pairs with $z_s>1$", lambda d: pct(d["zs"]["frac_gt_1"])),
        ("Median detector-frame primary mass [$M_\\odot$]", lambda d: fmt(d["mass_1_det"]["median"], 0)),
        ("Quadruply imaged systems", lambda d: pct(int(d["n_images"].get("4", 0)) / d["n_lensed_pairs"])),
        ("Type I + type II image pairs", lambda d: pct((d["pair_image_types"].get("1+2", 0) + d["pair_image_types"].get("2+1", 0)) / d["n_lensed_pairs"])),
        ("Median flux ratio $|\\mu_1/\\mu_2|$", lambda d: fmt(d["flux_ratio"]["median"], 2)),
        ("Flux ratio below 1.9 (original $y\\le0.3$ range)", lambda d: pct(d["flux_ratio"]["frac_le_orig_max"])),
        ("Median fainter-image optimal SNR", lambda d: fmt(d["snr_faint"]["median"], 1)),
        ("Fainter-image SNR below 12", lambda d: pct(d["snr_faint"]["frac_lt_12"])),
        ("Median time delay [days]", lambda d: fmt(d["delay_days"]["median"], 2)),
        ("Delay below 1 min (overlapping signals)", lambda d: pct(d["delay_days"]["frac_lt_1min"])),
        ("Delay below 1 day", lambda d: pct(d["delay_days"]["frac_lt_1d"])),
        ("Delay below 30 days", lambda d: pct(d["delay_days"]["frac_lt_30d"])),
        ("Pairs inside the original simulation domain", lambda d: pct(d["frac_inside_original_training_domain"])),
    ]
    head = " & ".join(cfgs)
    tex = ["\\begin{table}[t]",
           "\\caption{Detectable strongly lensed binary black-hole pairs for an LVK-like source population and a galaxy lens population (\\texttt{ler}), at O4 and Einstein Telescope sensitivity. Detection requires an observed network SNR above 8 for each of the two images; the two brightest detected images of each system form the pair. Based on 5\\,000 detectable systems per configuration.}",
           "\\label{tab:population}",
           "\\begin{ruledtabular}",
           f"\\begin{{tabular}}{{l{'c' * len(cfgs)}}}",
           f" & {head} \\\\", "\\hline"]
    md = ["| quantity | " + " | ".join(cfgs) + " |", "|---|" + "---|" * len(cfgs)]
    for label, f in rows:
        vals = [f(s[c]) for c in cfgs]
        tex.append(f"{label} & " + " & ".join(vals) + " \\\\")
        plain = (label.replace("[yr$^{-1}$]", "[per yr]").replace("$M_\\odot$", "Msun").replace("$|\\mu_1/\\mu_2|$", "|mu1/mu2|")
                 .replace("$y\\le0.3$", "y <= 0.3").replace("$z_s>1$", "z_s > 1"))
        md.append(f"| {plain} | " + " | ".join(v.replace("\\%", "%") for v in vals) + " |")
    tex += ["\\end{tabular}", "\\end{ruledtabular}", "\\end{table}"]
    (OUT / "population_table.tex").write_text("\n".join(tex) + "\n")
    (OUT / "population_table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
