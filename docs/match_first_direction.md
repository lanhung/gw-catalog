# Match-first direction

This repository is now being steered by the original `match` project workflow while keeping code in `gw-catalog`. The old LensGraph MVP remains available, but new optimization should happen in the `matchgw` package.

## Scientific target

The local task framework redefines strong-lensed GW image pairing as calibrated Top-K candidate retrieval for large event catalogs. The model should not claim a final astrophysical match by itself. It should return a compact ranked counterpart list for each event, attach calibrated neural compatibility probabilities, and reduce the expensive Bayesian/posterior-overlap follow-up from near `O(N^2)` exhaustive pairs to roughly `O(KN)` candidate pairs.

The main success criteria are therefore retrieval and follow-up metrics: `Recall@5`, `Recall@10`, `MRR`, median true rank, candidate edge volume, follow-up reduction, calibration quality (`ECE`, Brier, NLL), and Tier 1/2/3 follow-up statistics. Graph matching precision/F1 is now kept as optional secondary context rather than the central paper claim.

## Primary workflow

- Read native match arrays directly from `/root/autodl-tmp/qkzhang` with source-level train/val/test splits.
- Train a Siamese/NT-Xent waveform encoder on L1/L2 pairs plus unlensed self-pairs.
- Build cosine Top-K candidates on validation/test sets.
- Tune match-style candidate rules on validation: top-k, mutual filtering, reciprocal rank, row score/margin gates, edge rank bonus.
- Fit a lightweight pair reranker/calibrator on validation candidate edges using cosine score, reciprocal ranks, mutual-top1 state, and row margins.
- Export calibrated candidate lists with `p_hat` and `tier`, plus follow-up reduction and calibration summaries.
- Keep maximum-weight graph matching as an optional global-consistency readout, not as the primary scientific objective.

## Entry point

```bash
python scripts/08_match_first_train.py \
  --model-type SIS \
  --data-mode noisy \
  --lensed-limit 2500 \
  --unlensed-limit 2500 \
  --epochs 20 \
  --p-low 0.20 \
  --p-high 0.80 \
  --out-dir runs/match_first_sis_noisy
```

The run writes:

- `summary.json`: training history, retrieval metrics, graph-matching context, candidate-calibration metrics, and calibrator parameters.
- `val_candidates.csv` / `test_candidates.csv`: candidate edges with ranks, margins, `p_hat`, and `tier`.
- `val_candidate_summary.csv` / `test_candidate_summary.csv`: follow-up reduction, compression factor, calibration metrics, and tier metrics.

## Current boundary

The implementation intentionally does not copy the historical notebooks, logs, checkpoints, or broad auto scripts from `match`. It extracts the reusable ideas into a cleaner package surface: config, data loading, model, candidate retrieval, pair calibration, train/eval pipeline, and a small sweep runner.

The next match-native improvement should target noisy-data retrieval: better waveform encoder/backbone, stronger augmentation, explicit hard-negative mining after a stable baseline, and eventually richer pair features such as GCC-PHAT, estimated time delay, SNR ratio, and lightweight parameter-consistency signals.

## Hard negatives

Hard-negative mining is available but disabled by default because it can hurt when the validation embedding is still weak. Enable it explicitly after a baseline run:

```bash
python scripts/08_match_first_train.py \
  --model-type SIS \
  --data-mode noisy \
  --enable-hard-neg \
  --hard-neg-epochs 4 \
  --hard-neg-min-score 0.70 \
  --out-dir runs/match_first_sis_noisy_hnm
```

## Sweeps

```bash
python scripts/09_match_first_sweep.py \
  --model-types SIS PM \
  --data-modes pure noisy \
  --epochs 20 40 \
  --lr 0.001 0.0003 \
  --width-scale 1.0 2.0
```
