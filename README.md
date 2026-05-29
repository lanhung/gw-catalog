# GW Catalog Retrieval

This repository contains the current match-first gravitational-wave lensing catalog retrieval code, ET/LIGO-style data generation scripts, and compact experiment results.

## Main Code

- `matchgw/`: waveform dataset loading, preprocessing, models, matching, calibration, and catalog-level reporting.
- `scripts/08_match_first_train.py`: main training/evaluation entry point.
- `scripts/experiments/`: score ensemble, reranking, multiband, and cross-encoder experiments.
- `data_generation/`: current data generation scripts copied from `/root/autodl-tmp/createdata`.
- `docs/`: Chinese experiment notes and result summaries.
- `experiment_results/`: compact logs and `summary.json` files. Large candidate CSVs, model weights, and `.npy` data are intentionally excluded.

## Current Best Noisy Result

Best SIS noisy result so far:

| Method | R@1 | R@5 | R@10 | R@50 |
|---|---:|---:|---:|---:|
| score ensemble + small-weight cross-encoder blend | 0.4657 | 0.6373 | 0.7047 | 0.8190 |

Best PM noisy result so far:

| Method | R@1 | R@5 | R@10 | R@50 |
|---|---:|---:|---:|---:|
| score ensemble + waveform reranker | 0.3683 | 0.5403 | 0.6120 | 0.7530 |

See `docs/noisy_r1_optimization_summary_cn.md` and `experiment_results/experiments_noisy_r1_optimization_log.md` for detailed diagnostics.

## Test

```bash
python3 -m pytest tests/test_matchgw.py -q
```
