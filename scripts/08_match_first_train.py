from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from matchgw import MatchRunConfig
from matchgw.pipeline import run_train_eval


def main() -> None:
    ap = argparse.ArgumentParser(description="Train match-first Siamese GW matcher in the gw-catalog repo.")
    ap.add_argument("--data-root", type=Path, default=Path("/root/autodl-tmp/qkzhang"))
    ap.add_argument("--model-type", choices=["SIS", "PM"], default="SIS")
    ap.add_argument("--data-mode", choices=["pure", "noisy"], default="noisy")
    ap.add_argument("--out-dir", type=Path, default=Path("runs/match_first"))
    ap.add_argument("--lensed-limit", type=int, default=2500)
    ap.add_argument("--unlensed-limit", type=int, default=2500)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--target-len", type=int, default=8192)
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--width-scale", type=float, default=2.0)
    ap.add_argument("--use-hilbert", action="store_true")
    ap.add_argument("--hard-neg-epochs", type=int, default=4)
    ap.add_argument("--hard-neg-min-score", type=float, default=0.70)
    ap.add_argument("--enable-hard-neg", action="store_true")
    ap.add_argument("--no-export-candidates", action="store_true")
    ap.add_argument("--cpu", action="store_true")
    args = ap.parse_args()

    cfg = MatchRunConfig(
        data_root=args.data_root,
        model_type=args.model_type,
        data_mode=args.data_mode,
        out_dir=args.out_dir,
        lensed_limit=args.lensed_limit,
        unlensed_limit=args.unlensed_limit,
        epochs=args.epochs,
        batch_size=args.batch_size,
        target_len=args.target_len,
        stride=args.stride,
        lr=args.lr,
        width_scale=args.width_scale,
        use_hilbert=args.use_hilbert,
        hard_neg_enable=args.enable_hard_neg,
        hard_neg_epochs=args.hard_neg_epochs,
        hard_neg_min_score=args.hard_neg_min_score,
        export_candidates=not args.no_export_candidates,
    )
    run_train_eval(cfg, cpu=args.cpu)


if __name__ == "__main__":
    main()
