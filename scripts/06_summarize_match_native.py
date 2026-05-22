from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def summarize(base_dir: Path, out: Path) -> pd.DataFrame:
    items = [
        ("SIS pure", "sis_pure_system"),
        ("SIS noisy", "sis_noisy_system"),
        ("PM pure", "pm_pure_system"),
        ("PM noisy", "pm_noisy_system"),
    ]
    rows = []
    for dataset, subdir in items:
        result_dir = base_dir / subdir
        ret = pd.read_csv(result_dir / "retrieval_summary.csv").iloc[0]
        system = pd.read_csv(result_dir / "system_summary.csv")
        ccl = system[system["method"].eq("LensGraph (CCl)")].iloc[0]
        row = {
            "dataset": dataset,
            "R@1": ret["recall_at_1"],
            "R@5": ret["recall_at_5"],
            "R@10": ret["recall_at_10"],
            "MRR": ret.get("mrr", 0.0),
            "MedianTrueRank": ret.get("median_true_rank", 0.0),
            "Precision": ccl["pair_precision"],
            "Recall": ccl["pair_recall"],
            "F1": ccl["pair_f1"],
            "ExactRecovery": ccl["exact_recovery"],
            "CatalogFDR": ccl["catalog_fdr"],
            "threshold": ccl["threshold"],
            "candidate_edges": ccl["candidate_edges"],
        }
        cal_path = result_dir / "calibration_summary.csv"
        if cal_path.exists():
            cal = pd.read_csv(cal_path).iloc[0]
            row.update({
                "ECE": cal["ece"],
                "Brier": cal["brier"],
                "NLL": cal["nll"],
            })
        tier_path = result_dir / "tier_summary.csv"
        if tier_path.exists():
            tier = pd.read_csv(tier_path)
            tier1 = tier[tier["tier"].eq("Tier 1")]
            tier12 = tier[tier["tier"].eq("Tier 1+2")]
            if not tier1.empty:
                row["Tier1Precision"] = tier1.iloc[0]["pair_precision"]
                row["Tier1Edges"] = tier1.iloc[0]["candidate_edges"]
            if not tier12.empty:
                row["Tier12Recall"] = tier12.iloc[0]["pair_recall"]
                row["Tier12Edges"] = tier12.iloc[0]["candidate_edges"]
        rows.append(row)
    df = pd.DataFrame(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    df = summarize(args.base_dir, args.out)
    print(df.to_string(index=False))
    print(f"WROTE {args.out}")


if __name__ == "__main__":
    main()
