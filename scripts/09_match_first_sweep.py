from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Small match-first sweep runner.")
    ap.add_argument("--out-root", type=Path, default=Path("runs/match_first_sweep"))
    ap.add_argument("--model-types", nargs="+", default=["SIS", "PM"])
    ap.add_argument("--data-modes", nargs="+", default=["pure", "noisy"])
    ap.add_argument("--lensed-limit", type=int, default=2500)
    ap.add_argument("--unlensed-limit", type=int, default=2500)
    ap.add_argument("--epochs", nargs="+", type=int, default=[20])
    ap.add_argument("--lr", nargs="+", type=float, default=[1e-3])
    ap.add_argument("--width-scale", nargs="+", type=float, default=[2.0])
    ap.add_argument("--enable-hard-neg", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = Path(__file__).resolve().parent / "08_match_first_train.py"
    args.out_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for model_type, data_mode, epochs, lr, width in itertools.product(
        args.model_types, args.data_modes, args.epochs, args.lr, args.width_scale
    ):
        name = f"{model_type.lower()}_{data_mode}_ep{epochs}_lr{lr:g}_w{width:g}".replace(".", "p")
        out_dir = args.out_root / name
        cmd = [
            sys.executable,
            str(base),
            "--model-type", model_type,
            "--data-mode", data_mode,
            "--lensed-limit", str(args.lensed_limit),
            "--unlensed-limit", str(args.unlensed_limit),
            "--epochs", str(epochs),
            "--lr", str(lr),
            "--width-scale", str(width),
            "--out-dir", str(out_dir),
        ]
        if args.enable_hard_neg:
            cmd.append("--enable-hard-neg")
        print(" ".join(cmd), flush=True)
        if not args.dry_run:
            subprocess.run(cmd, check=True)
            summary_path = out_dir / "summary.json"
            if summary_path.exists():
                summary = json.loads(summary_path.read_text())
                row = {
                    "run": name,
                    "model_type": model_type,
                    "data_mode": data_mode,
                    "epochs": epochs,
                    "lr": lr,
                    "width_scale": width,
                    **{f"test_{k}": v for k, v in summary.get("test", {}).items()},
                    **{f"val_{k}": v for k, v in summary.get("val", {}).items()},
                }
                rows.append(row)
    if rows:
        import pandas as pd
        pd.DataFrame(rows).to_csv(args.out_root / "summary.csv", index=False)


if __name__ == "__main__":
    main()
