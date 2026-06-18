# GW Catalog Retrieval

Catalog-level strong-lensed gravitational-wave candidate retrieval for ET and
LIGO-style data. The current pipeline uses waveform embeddings for candidate
generation, then reranks candidates with observable time, sky-localization and
amplitude/SNR information.

## Repository layout

- `matchgw/`: datasets, preprocessing, waveform models, matching, calibration,
  catalog reporting and reusable auxiliary-prior modules.
- `scripts/08_match_first_train.py`: original match-first training/evaluation
  entry point.
- `scripts/experiments/`: numbered research runners. The current ET3 and LIGO
  full-catalog flows are `90_*` through `95_*`.
- `scripts/server_experiments/`: sparse ANN retrieval, posterior-skymap overlap
  and noise/null experiments.
- `scripts/gwtc/`: real GWTC data extraction and case-study analysis.
- `data_generation/`: ET/LIGO-style simulation helpers and generation scripts.
- `docs/`: experiment reports and a curated index in `docs/README.md`.
- `experiment_results/`: compact logs and summaries. Large arrays, checkpoints,
  catalogs and run directories are intentionally excluded from version control.

## Current validated results

- ET3 noisy full-catalog waveform-only: R@1 0.6245, R@10 0.8542.
- ET3 noisy observable reranking: R@1 0.9840, R@10 0.9985.
- Native 9,000-event ET3 HNSW retrieval preserves exact partner recall and
  recovers 99.895% of exact dense top-10 neighbors.
- The million-event ANN result is an engineering scaling stress test; its full
  query time is extrapolated and it is not evidence of scientific recall at
  that catalog size.
- GWTC real-event analyses are null/case-study tests of observable triage and
  posterior-sample sky overlap. They do not claim any GWTC pair is lensed.
- Graph-reconstruction claims should use exact-match, B-cubed,
  over-merge/fragmentation and singleton metrics from
  `scripts/server_experiments/exp3_graph.py`; older connected-component
  `system_precision` summaries are deprecated for manuscript use.

## Manuscript caution flags

- Say "the three-interferometer triangular Einstein Telescope configuration",
  not an independent three-site detector network.
- Say "ANN candidate generation was benchmarked at one million embeddings",
  not that scientific retrieval was validated at one million events.
- Say "tested classification-based fusion models" for logistic/HGB/LightGBM
  comparisons unless a ranking objective is actually used.
- Say "posterior-sample HEALPix overlap restores the sky consistency of a
  previously discussed candidate pair", not that the real catalog validates a
  lensing detection.

See `docs/gw_lensing_identification_overall_scheme_detailed_20260617_cn.md` and
`docs/server_experiments_p2_final_assessment_20260618_cn.md` for definitions,
provenance and limitations.

## Development checks

```bash
python -m pytest tests/test_matchgw.py -q
python -m compileall -q matchgw scripts
```

Run scripts from the repository root so relative paths and local imports resolve
consistently. Most experiment runners require external datasets and existing run
artifacts under the server paths documented in their corresponding reports.
