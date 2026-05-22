# Match-first direction

This repository is now being steered by the original `match` project workflow while keeping code in `gw-catalog`. The old LensGraph MVP remains available, but new optimization should happen in the `matchgw` package.

## Primary workflow

- Read native match arrays directly from `/root/autodl-tmp/qkzhang`.
- Train a Siamese/NT-Xent waveform encoder on L1/L2 pairs plus unlensed self-pairs.
- Build cosine top-k candidates on validation/test sets.
- Tune match-style candidate rules on validation: top-k, mutual filtering, reciprocal rank, row score/margin gates, edge rank bonus.
- Evaluate final matching with maximum-weight matching and pair-level precision/recall/F1/F2.

## Entry point

```bash
python scripts/08_match_first_train.py \
  --model-type SIS \
  --data-mode noisy \
  --lensed-limit 2500 \
  --unlensed-limit 2500 \
  --epochs 20 \
  --out-dir runs/match_first_sis_noisy
```

## Current boundary

The implementation intentionally does not copy the historical notebooks, logs, checkpoints, or sweep scripts from `match`. It extracts the reusable ideas into a cleaner package surface: config, data loading, model, candidate matching, and train/eval pipeline.
