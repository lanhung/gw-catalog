# PI-ResNet manuscript revision — notes for the authors

Build: `pdflatex main && bibtex main && pdflatex main && pdflatex main` (REVTeX 4.2, PRD style).
Figures: `python make_paper_figures.py` (after running
`scripts/gwtc/05_catalog_context_for_pair_verification.py` from the repo root).

## What this version is based on

The GPU server (`gpu.chzmark.com`) could not be reached from the build environment
(outbound SSH is blocked), so neither the latest manuscript nor the latest server results
were visible. This version was written from:

- the PI-ResNet project snapshot in `lanhung/gw-ampl-est`
  (`vendor/legacy_snapshot/candidate_wjx`: `docs/RESULTS.md`, `EVALUATION_PROTOCOL.md`,
  `TYPE_II_DIAGNOSTIC.md`, `LIMITATIONS.md`, model and generator code; snapshot of July 2026);
- the real-catalogue data already extracted in this repository
  (`data/gwtc3_observables.csv`, `data/gwtc5_observables.csv`) and the GWTC-3 posterior
  sky-map comparison in `runs/p2b_gwtc3_posterior_healpix_20260618/`.

**Merge this text with the current server manuscript.** Any newer numbers on the
server supersede the ones here.

## Items to complete (red in the PDF)

| Item | Where to find it |
|---|---|
| Efficiencies at FAP 1e-2 and 1e-4 (Table I) | `results/core/fixed_fpp_primary_table.csv` (PI-ResNet repo) |
| ET noise curve name (ET-D?) | ET generator scripts on the server |
| Input window length and sampling rate (2 s at 2048 Hz inferred from `config.py`: 8192 samples of 4096 Hz data, stride 2) | `src/classifier/config.py`, ET data headers |
| Optimiser name | training driver |
| Authors, acknowledgements | — |
| References marked `VERIFY` in `refs.bib` (GWTC-4.0 arXiv number, GWTC-5.0 paper, Campailla et al. "Catalog Level Lensed GW Discovery", SEMD) | arXiv/ADS |

## Adding O4a (GWTC-4.0)

O4a sky maps could not be downloaded here because Zenodo and GWOSC are blocked from the
build environment. On the server:

```bash
python scripts/gwtc/01c_extract_gwtc4_observables.py --dry-run   # check record/selection
python scripts/gwtc/01c_extract_gwtc4_observables.py --gwosc-pe-mchirp
python scripts/gwtc/05_catalog_context_for_pair_verification.py --out runs/gwtc_catalog_context_with_o4a
```

Script 05 picks up `data/gwtc4_observables.csv` automatically and adds O4a rows to every
table, including the O4a–O4b pairs (many are <1 yr apart, unlike O3–O4b pairs).
Then update Sec. VII numbers (Table II, Fig. 5–7, the budget numbers) from
`runs/.../summary.json` and `false_alarm_budget.csv`.

## New experiment added (Sec. VII), modelled on catalogue-level lensing analyses

`scripts/gwtc/05_catalog_context_for_pair_verification.py`, outputs in
`runs/gwtc_catalog_context_20261001/`:

1. Pair census: O1–O3 (63 BBHs, 1,953 pairs), O4b (105 BBHs, 5,460 pairs), combined 14,028 pairs.
2. Lens time-delay distributions (simulation priors and a galaxy-population model, with and
   without magnification bias): more than 99.9% of galaxy-lens delays are under 1 yr.
3. Physical pre-selection (delay < 1 yr, common sky at 99%, common detector-frame chirp mass at
   99%): 14,028 → 637 pairs (4.5%; Campailla et al. kept 5.1% of GWTC-3 pairs).
4. Injections of synthetic lensed pairs into the real catalogue: 98% pass; the true partner ranks
   among the top 10 survivors in 96–97% of cases.
5. False-alarm budget: at FAP 1e-3 a pair test would accept ~14 unrelated pairs out of all
   pairs, or 0.64 out of the 637 survivors, compared with ~0.17 genuine lensed pairs expected.
   A credible claim needs FAP ≲ 1.6e-4 after pre-selection.

Caveats stated in the text: the sky test uses a circular-Gaussian summary (it rejects
GW170104–GW170814, which full posterior sky maps find compatible); the O4b chirp masses are
search-template values; the chirp-mass tolerance is an assumption (sensitivity is reported).
PI-ResNet itself was **not** run on real strain: it is trained on ET Gaussian noise and needs
retraining on O4 noise first. The paper says so explicitly.

## Writing conventions used (for a physics readership)

Structure follows GW-lensing papers (Haris+2018, LVK O3 lensing searches, Çalışkan+2023):
the physics comes first (what lensing changes and preserves, Eq. 1), then the simulation,
then the method, then results interpreted physically, then the real catalogues.

| Earlier wording | Now |
|---|---|
| false-positive probability (FPP) | false-alarm probability per pair, `p_FA` |
| efficiency / TPR / recall | detection efficiency: fraction of lensed pairs recovered |
| calibration partition | threshold-setting subset (analogy: time-slide background) |
| final-evaluation partition, preregistered | measurement subset, blind analysis |
| IID holdout | independent realisation of the same simulated Universe |
| hard / easy negatives | unrelated pairs: different lensed sources / lensed + unlensed |
| source-block bootstrap CI | 95% range from resampling groups of sources |
| Siamese network, embedding fusion | same network applied to each event, outputs compared |
| AUC, McNemar, accuracy | moved to Appendix C, not used for conclusions |
| E7 type-II probe | controlled test of the Morse phase, with physical interpretation (degeneracy with orbital phase for (2,2)-dominated signals) |

Other choices: every number is given with its physical meaning; the per-pair false-alarm
probability is turned into "expected false claims in the real catalogue"; limitations are
physical (noise, lens models, y range) rather than procedural; a plain-language glossary is
included (Appendix A).

The "PI" in PI-ResNet is described as *physics-inspired design choices* (periodic activation,
channel weighting, symmetric comparison). The code imposes no lensing equations, so
"physics-informed" would invite reviewer objections. Change it back if the original paper
defines it differently.
