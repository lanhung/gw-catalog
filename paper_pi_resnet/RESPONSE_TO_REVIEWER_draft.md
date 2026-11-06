# Response to the ApJS reviewer (AAS82367) — DRAFT for the authors

Status: draft written from the reviewer report and the frozen 0228 results.
Everything marked **[server]** needs a new experiment or a number from the
analysis server; everything marked **[read]** needs the cited paper to be read
first (arXiv was not reachable from the build environment; a new cloud
environment "gw-catalog" with arxiv.org/zenodo.org/gwosc.org allowed has been
created for the next session).  Text in the "Response" blocks is written in the
plain-text form the journal asks for, so it can be pasted into the resubmission
form once the placeholders are filled.

----------------------------------------------------------------------
## 0. Our reading of the report, and the strategy it implies
----------------------------------------------------------------------

The reviewer recommends rejection on three grounds. In order of weight:

1. **Novelty versus Offermans et al. (arXiv:2411.12453).** If the time-domain
   network is essentially the one of Offermans et al. and the comparison to a
   CQT-based classifier was already made there, the architecture itself cannot
   carry the paper. The reviewer is right that "turning the output into a
   search statistic" is standard practice.

2. **Unrealistic simulations.** Uniform masses in [10, 100] Msun, uniform
   comoving redshift to z = 1, lens at z_s/2, uniform y in [0.01, 0.3], and point
   masses as a lens class. Every one of these is a legitimate objection, and
   none can be answered by text changes: the datasets have to be regenerated
   and the networks retrained.

3. **The cost argument.** A posterior-overlap statistic (Barsode et al.) reaches
   the same ~54% efficiency at a per-pair false-alarm probability of 1e-6 for
   under a second per pair. Our cost model (Sec. 4 below, Fig.
   `experiments/fig_cost_model.pdf`) confirms the reviewer's arithmetic: used
   *instead of* such a statistic, PI-ResNet only wins if the downstream
   Bayesian analysis costs less than ~17 CPU-minutes per pair, which it does
   not. Used *in front of* it, PI-ResNet cuts the total compute by a factor
   90–470 (depending on its operating point) for a catalogue of any size, at a
   combined efficiency between 0.29 and 0.54.

The paper therefore cannot be resubmitted as "a better classifier". It can be
resubmitted as a **calibrated, strain-level pre-filter for a staged lensing
search, characterised on a realistic population at current and ET
sensitivity, with a quantitative cost analysis of where it belongs in the
LVK / LensingFlow workflow**. That is a smaller claim than the original, but it
is one the reviewer has effectively told us how to support. Two features of a
strain-based statistic are genuinely absent from posterior-overlap methods and
should be the backbone of the new positioning:

- it needs no parameter-estimation posteriors, so it can run as soon as two
  triggers exist (low latency, and at ET event rates where full PE for every
  event is itself the bottleneck);
- its per-event preprocessing is 0.5 ms, so the N(N-1)/2 scaling is cheap enough
  to be applied to all pairs that pass the time-delay/sky pre-selection.

Decision for the authors: this is a 4–6 week revision (new populations,
regeneration, retraining, re-evaluation), not a text revision. The AAS
six-month window is sufficient. The plain-language rewrite already in
`paper_pi_resnet/main.tex` is the base for the resubmitted text, but most of
its numbers will change.

----------------------------------------------------------------------
## 1. Distinction from Offermans et al.  **[read]**
----------------------------------------------------------------------

> Reviewer: The manuscript should clearly state the exact differences between
> it and Offermans et al., and how these differences realistically contribute
> towards the goal of identifying lensed GWs.

Before writing the response, read arXiv:2411.12453 and fill in this table.
If lines 339–341 of the submitted manuscript do say that the backbone is the
Offermans et al. network, say so plainly in the paper and the response; the
reviewer has already noticed.

| Aspect | Offermans et al. (fill in) | This work |
|---|---|---|
| Network / input | ? | 1-D residual Siamese network on peak-aligned, whitened strain; periodic (Snake) activation; SE channel weighting; symmetric product/difference comparison |
| Population | ? | (revised) LVK-like BBH population, SIE+shear galaxy lenses from `ler` |
| Detectors | ? | O4 network and ET |
| Background construction | ? | 1e5 unrelated pairs per lens class, 70% lensed-image-vs-lensed-image "hard" pairs; thresholds frozen before evaluation |
| Metrics | ROC/AUC ? | efficiency at fixed FAP (1e-2, 1e-3, 1e-4) with block-bootstrap ranges; efficiency-vs-FAP curve |
| Physical characterisation | ? | lensing selection function in fainter-image SNR, y, flux ratio; controlled Morse-phase test; time-delay invariance test; cross-lens transfer |
| Catalogue context | ? | false-alarm budget on real GWTC-3 + O4b pairs; staged-search cost model |

Response (plain text, to complete):

    We thank the reviewer for pointing to Offermans et al. (2024), which we
    now cite and discuss explicitly (Sec. 1 and Sec. 4.x). [State the exact
    relationship of the networks.] We agree that architectural differences
    alone do not constitute a contribution, and we have removed language
    suggesting otherwise. The revised manuscript makes a different claim: it
    characterises a strain-level pair statistic as one stage of a staged
    lensing search. Its contributions relative to Offermans et al. are (i)
    [...], (ii) a lensing selection function measured on a realistic
    population at O4 and ET sensitivity, (iii) a quantitative cost model
    (new Sec. X, Fig. Y) that shows where a strain-level pre-filter reduces
    the total cost of a search that ends in posterior-overlap and Bayesian
    stages, and (iv) a false-alarm budget on the real GWTC-3 and O4 pairs.

----------------------------------------------------------------------
## 2. Realistic simulation settings  **[server]**
----------------------------------------------------------------------

> Reviewer: uniform source masses and uniform source redshifts ... incompatible
> with the observed population; limiting z_s to 1 is questionable; point masses
> and uniform impact parameters (should be linear) are inappropriate.

We agree on every point. Regenerate both catalogues (training and the
independent threshold-setting/measurement catalogue) with `ler`
(https://ler.hemantaph.com/), which implements exactly what the reviewer asks
for. Settings to use and to state in the paper:

- **Sources:** BBH masses from the GWTC-3 Power Law + Peak model; merger-rate
  density following the Madau–Dickinson star-formation history with time
  delay (ler default, Oguri 2018 form), z_s up to ~10 (the lensed population
  peaks at z_s ~ 1–3); spins from GWTC-3 defaults; isotropic sky and
  orientation.
- **Lenses:** elliptical power-law (or SIE) + external shear, velocity
  dispersion from the SDSS velocity-dispersion function with the ler
  redshift-dependent option, lens redshift from the optical depth, source
  position sampled uniformly inside the caustic (this is the "linear in y"
  prior the reviewer asks for). Keep only systems in which at least two images
  are detectable; record image types (I/II/III) and the number of images, so
  that quads enter the pair sample naturally.
- **Point-mass lenses:** no longer a benchmark population. Kept only as a
  lens-profile robustness test on the same realistic BBH population, with the
  source position sampled linearly in y (see Sec. 2b below for the reasoning).
- **Detectors:** two configurations. (a) O4 sensitivity (aLIGO O4 PSDs for
  H1/L1, AdV, KAGRA as appropriate) so that numbers can be compared with
  Barsode et al. and Offermans et al. (b) ET-D as the forecast. Detection
  threshold: network optimal SNR > 8 for each image (state it). Report the
  fainter-image SNR distribution of the resulting pairs; this is the
  quantity that drives the efficiency.
- **Population mismatch test** (this answers Cheung et al. 2023 in the ML
  setting): train on the PL+Peak population and evaluate on a second
  population with a different mass model (e.g. broken power law) and a
  different VDF normalisation; report the change in efficiency at fixed FAP.
  This replaces the lens-redshift sanity check (old Sec. 5.2), which the
  reviewer rightly says is redundant once z_l/z_s is sampled physically.
- **What will change in the results:** y is no longer bounded at 0.3, so flux
  ratios extend to ~10 and more; fainter images are typically much fainter;
  efficiency at fixed FAP will drop. Report it honestly and give the selection
  function so that the reader can see where the method works.

Budget: population + waveform generation (IMRPhenomXPHM, 3-detector ET and
4-detector O4) for ~10^4 lensed systems and ~10^4 unlensed events: 1–2 days
CPU; retraining 2 lens-configurations × 2 detector-configurations × 300
epochs: a few GPU-days; evaluation and bootstrap: hours.

Response (plain text, to complete after the runs):

    We have regenerated all simulated catalogues with the `ler` package
    (Phurailatpam et al.), using the GWTC-3 Power Law + Peak mass model, a
    Madau-Dickinson merger-rate density with sources up to z = [..], an
    SDSS-based velocity-dispersion function, elliptical power-law lenses with
    external shear, lens redshifts drawn from the lensing optical depth, and
    source positions sampled uniformly within the caustic. The point-mass lens
    class has been removed from the main analysis. All networks were
    retrained and re-evaluated with the same frozen protocol at O4 and at ET
    sensitivity. The new efficiencies at FAP 1e-3 are [..] (O4) and [..] (ET),
    compared with [..] in the original submission. Section 5.2 has been removed.

### 2a. Results of the realistic population (`ler` 1.0.2), O4 and ET

`scripts/population/ler_realistic_population.py --config O4|ET` (LVK-like BBH
population: GWTC-3 Power Law + Peak masses, star-formation-history merger rate
with time delay, sources to z = 10; EPL + shear galaxy lenses with an SDSS-type
velocity-dispersion function, lens redshift from the optical depth, source
position uniform in the caustic; detection = observed network SNR above 8 for
each of two images, within ler's one-year time window). O4 = H1 + L1 at the
aLIGO O4 ASD and V1 at the AdV ASD; ET = bilby's triangular Einstein Telescope
at ET-D. 5,000 detectable lensed systems and 5,000 unlensed detections per
configuration; tables in `data/ler_population/`, figure
`fig_ler_population.pdf`, LaTeX table `experiments/population_table.tex`.

| quantity | O4 | ET |
|---|---|---|
| Detected BBH rate [per yr] | 738 | 65034 |
| Lensed systems with two detected images [per yr] | 0.28 | 32.58 |
| Lensed fraction among detections | 3.8e-04 | 5.0e-04 |
| Median source redshift of lensed pairs | 1.90 | 2.72 |
| Lensed pairs with z_s > 1 | 89% | 98% |
| Median detector-frame primary mass [Msun] | 79 | 43 |
| Quadruply imaged systems | 63% | 19% |
| Type I + type II image pairs | 93% | 93% |
| Median flux ratio |mu1/mu2| | 1.20 | 2.16 |
| Flux ratio below 1.9 (original y <= 0.3 range) | 85% | 43% |
| Median fainter-image optimal SNR | 9.7 | 13.7 |
| Fainter-image SNR below 12 | 73% | 40% |
| Median time delay [days] | 0.22 | 22.72 |
| Delay below 1 min (overlapping signals) | 8% | 0% |
| Delay below 1 day | 62% | 12% |
| Delay below 30 days | 90% | 56% |
| Pairs inside the original simulation domain | 77% | 43% |

What this means for the response:

- **Sources.** The reviewer is right: realistic detected lensed pairs sit at
  z ~ 2 (O4) to z ~ 3 (ET), 89-98% beyond the original z_max = 1, with
  detector-frame masses and fainter-image SNRs that differ from the original
  catalogue. The efficiencies must be re-measured on these populations.
- **Image-pair geometry.** The effect of the impact-parameter prior depends on
  the detector. At O4 sensitivity, detected pairs are dominated by highly
  magnified, nearly symmetric images (63% quads, median flux ratio 1.2): 85% of
  realistic pairs have flux ratios inside the range of the original y <= 0.3
  simulations, and 77% fall inside the original domain altogether. At ET
  sensitivity the lens no longer needs to magnify strongly for both images to
  be detected, so pairs are more asymmetric (median flux ratio 2.2, only 19%
  quads) and only 43% fall inside the original domain. Since the original
  paper's headline numbers were for ET, this is exactly where the reviewer's
  objection bites hardest, and the revision must say so.
- **Delays.** At O4, 8% of detectable pairs arrive within a minute of each
  other (merging image pairs near the caustic) and 35% within an hour; these
  belong to overlapping-signal or same-segment searches, not to a catalogue
  pair search. At ET the median delay is 23 days and 44% exceed a month, so
  the one-year catalogue window used in Sec. VII loses nothing (ler's own
  one-year window is applied in both cases; pairs with longer delays are not
  counted in the rates above).
- **Rates.** Lensed fractions of 3.8e-4 (O4) and 5.0e-4 (ET) support the
  range used in the false-alarm budget of Sec. VII.
- Spins: ler draws aligned spin components; `generate_strain_from_ler.py`
  converts negative components to magnitude + anti-aligned tilt for bilby.
  Validation on four O4 pairs gives bilby (IMRPhenomXPHM, spins) optimal SNRs
  within 10-40% of ler's no-spin IMRPhenomD interpolation, as expected; the
  strain files carry the bilby values.

----------------------------------------------------------------------
## 2b. What to do with the point-mass lens class (decision memo)
----------------------------------------------------------------------

The question is whether to remove the point-mass (PM) results at the revision
stage. Three facts frame it:

1. What the reviewer objected to is PM *as a realistic benchmark population*
   ("lens model choices such as the inclusion of point masses ... are
   inappropriate", in the paragraph about realistic datasets). The reviewer did
   not say the PM results are wrong, and did not comment on the cross-lens
   transfer result that uses them.
2. Physically, an isolated 1e8-1e10 Msun point mass is not an astrophysical
   lens population for separated GW images: objects of that mass sit inside
   galaxies, whose extended mass dominates the lensing cross-section at the
   Einstein radius; lighter point masses (< 1e5 Msun) produce overlapping,
   wave-optics-distorted images (microlensing), which is a different search.
   So PM pairs cannot be defended as a target population, and keeping them as
   one would draw the same objection again.
3. The PM data nevertheless support one result that *does* answer a reviewer
   concern: a network trained on galaxy-like lenses recovers PM pairs better
   than a network trained on PM pairs (Sec. 4.x of the submission). That is
   evidence of robustness to a lens profile the network never saw, which is
   relevant to the population-dependence concern (Cheung et al. 2023).

Recommendation: **demote, do not delete.**

- Primary results: galaxy lenses only (EPL + shear from `ler`), at O4 and ET.
- Keep PM as a short "robustness to the lens profile" test (one paragraph plus
  one row in the transfer table, or an appendix): regenerate PM pairs on the
  *same* realistic BBH population and detector noise, with y sampled linearly
  (p(y) ~ y) instead of uniformly, and evaluate the galaxy-trained network on
  them. No PM-specific training is required, which also removes the PM-only
  analyses the reviewer found hard to follow (the SNR/y re-weighting of the
  SIS-PM gap, the PM-trained transfer row, the PM Morse-phase probe).
- Remove PM from the abstract, the headline table, the conclusions and the
  title-level claims.
- State in the response that the reviewer's objection is accepted and explain
  the retained role in one sentence: "point-mass lenses are retained only as
  a controlled test of robustness to a lens profile outside the training set,
  not as an astrophysical population".

Why not delete outright: the transfer result is the only part of the PM work
with lasting value, deleting it loses a robustness argument the revision
needs, and the reduced form costs little (data generation plus inference,
no training). Why not keep as is: the reviewer has already called the
population unrealistic, and a second round on the same point would be fatal.

If the authors prefer the simplest path, deleting PM entirely is defensible
and should be explained as above; it is not evasive, because the reviewer
asked for it. The demoted form is recommended because it keeps one useful
result at small cost.

----------------------------------------------------------------------
## 3. Apples-to-apples comparison  **[server]** **[read]**
----------------------------------------------------------------------

> Reviewer: use settings as close as possible to existing approaches, so that
> metrics can be compared without re-running other pipelines.

Match the O4 configuration above to the settings of Barsode et al.
(2412.01278, 2605.10333) and Offermans et al. (PSDs, population, SNR
threshold, FAP definition). Then quote their efficiency at FAP 1e-6 / 1e-3
directly against ours at the same FAP and the same population. Keep ET as a
separate forecast and never compare an ET number with an O4 number (the
reviewer's "worse still" paragraph).

Response (plain text, to complete):

    The O4-sensitivity catalogue now follows the population and detector
    settings of Barsode et al. (2024, 2026) as closely as the public
    descriptions allow [list the matched settings]. Table X compares the
    efficiency at fixed FAP of PI-ResNet, the posterior-overlap statistic
    of Barsode et al. and the classifiers of Goyal et al. and Offermans et al.
    at O4 sensitivity. ET results are presented separately as a forecast and
    are no longer used in any comparison with methods benchmarked at current
    sensitivity.

----------------------------------------------------------------------
## 4. A proper justification of advantages — the cost model
----------------------------------------------------------------------

> Reviewer: consider FPP, false-dismissal probability, single-event
> preprocessing cost and pairwise cost together; show which role the method
> fills in existing workflows (LensingFlow, LVK O4 search); support the claim
> quantitatively.

`experiments/cost_model.py` (figure `fig_cost_model.pdf`, tables
`cost_model_table.csv`, `cost_model_catalogue_scale.csv`) computes the expected
compute per candidate pair for three chains, with the downstream Bayesian
joint analysis costing C_PE per forwarded pair:

    A. posterior overlap only:      c_B + p_B C_PE
    B. PI-ResNet only:              c_P + p_P C_PE
    C. PI-ResNet, then overlap:     c_P + p_P c_B + p_P p_B C_PE

with c_P = 1.24 ms, c_B = 1 s, p_B = 1e-6, e_B = 0.54 (Barsode et al. as
summarised by the reviewer; **replace by the published values**), and the
PI-ResNet operating points.

Results (C_PE = 1 CPU-day):

| PI-ResNet FAP | B vs A break-even C_PE | cost A | cost B | cost C | pairs to PE per input pair (A / B / C) | speed-up C vs A |
|---|---|---|---|---|---|---|
| 1e-2 | 100 s | 1.09 s | 864 s | 12 ms | 1e-6 / 1e-2 / 1e-8 | 90× |
| 1e-3 | 17 min | 1.09 s | 86 s | 2.3 ms | 1e-6 / 1e-3 / 1e-9 | 470× |
| 1e-4 | 2.8 h | 1.09 s | 8.6 s | 1.3 ms | 1e-6 / 1e-4 / 1e-10 | 800× |

For one ET year (~5e9 pairs) chain A costs ~170 CPU-years and chain C ~0.4
CPU-years; for an O5-like year (~5e5 pairs) 6 CPU-days versus 20 CPU-minutes.
Combined efficiency of chain C is e_P e_B = 0.29 if the two statistics are
independent and up to min(e_P, e_B) = 0.54 if the overlap statistic recovers
every pair PI-ResNet recovers; since both are limited by the fainter image's
SNR, the truth is nearer the upper end, and **this must be measured** on the
new population by running a posterior-overlap statistic on the same pairs
**[server]** (a KDE overlap of the detector-frame chirp mass, mass ratio, sky
and inclination posteriors is enough for the purpose; a full re-implementation
of Barsode et al. is not required, but say which statistic was used).

Consequences for the paper:

- The reviewer's conclusion for "PI-ResNet instead of the overlap statistic"
  is correct and we should say so.
- The right figure of merit for a pre-filter is efficiency at FAP 1e-2 to
  1e-1, not 1e-3. Report the full efficiency–FAP curve and quote the
  high-efficiency end (e.g. the FAP at which 90% and 95% of lensed pairs are
  kept).
- Add single-event preprocessing cost to the comparison: strain-based 0.5
  ms/event; CQT 66 ms/pair; posterior-overlap methods require PE posteriors for
  both events (zero marginal cost when PE exists for every event, as in O4, but
  not guaranteed at ET event rates or in low latency).
- Place the method in the workflow explicitly **[read]**: after the
  catalogue-level time-delay/sky pre-selection (our Sec. VII) and before the
  posterior-overlap / Bayes-factor stage of LensingFlow (arXiv:2507.20256) and
  the LVK O4 search (arXiv:2512.16347). Use their stage names once read.

Response (plain text):

    We agree with the reviewer that per-pair speed and efficiency are not
    meaningful in isolation. The revised manuscript adds a cost model (new
    Sec. X, Fig. Y) that combines the per-pair false-alarm probability,
    the efficiency, the per-pair and per-event costs, and the cost of the
    downstream Bayesian analysis for three search chains. The model confirms
    the reviewer's point: used instead of a posterior-overlap statistic with
    the performance reported by Barsode et al., PI-ResNet reduces the total
    cost only if the downstream analysis costs less than about 17 CPU-minutes
    per pair, which is not the case. Used as a strain-level pre-filter in
    front of that statistic, however, it reduces the total compute of the
    search by a factor of [90-470] at a combined efficiency of [measured
    value] (Table Z). We have therefore repositioned the method as a
    pre-filter stage between the catalogue-level pre-selection and the
    posterior-overlap stage of the LensingFlow / LVK workflow, and we report
    the efficiency-FAP curve over the range relevant to that role (FAP
    1e-1 to 1e-4) rather than a single operating point. We also note two
    properties that posterior-overlap statistics do not have: the pre-filter
    needs no parameter-estimation posteriors, so it can run as soon as two
    triggers exist, and its per-event preprocessing cost is 0.5 ms.

----------------------------------------------------------------------
## 5. Conciseness and clarity
----------------------------------------------------------------------

- Remove the repeated descriptions of blinding/locking and of the
  architecture; keep one paragraph each (the rewrite in `main.tex` already does
  this: Sec. IV.C and Appendix B).
- Define every metric in Table 3 in the caption or a short list. Definitions
  to use (plain words first, symbol second):
  - efficiency, eps: fraction of genuine lensed pairs with score above the
    threshold;
  - false-alarm probability per pair, p_FA: fraction of unrelated pairs with
    score above the threshold (the threshold is set from the threshold-setting
    subset; the "achieved" value is re-measured on the measurement subset);
  - 95% range: 2.5th–97.5th percentile of 10,000 block-bootstrap resamples
    over 10 groups of sources;
  - AUC: probability that a random lensed pair scores above a random unrelated
    pair (reported for completeness only);
  - average precision: area under the precision–recall curve;
  - accuracy at 0.5 and the McNemar test: fraction of correctly classified
    pairs at a fixed score of 0.5, and the exact paired test of whether two
    methods disagree more often in one direction than the other.
- Delete old Sec. 5.2 (lens-redshift / z_l/z_s check) once the realistic
  population is in; keep one sentence stating that the time delay cannot enter
  a peak-aligned statistic.

----------------------------------------------------------------------
## 6. Minor comments
----------------------------------------------------------------------

- Cite Barsode et al. (2412.01278; 2605.10333) in the introduction and in the
  cost-model section. Added to `refs.bib` as VERIFY entries.
- Line 83: Ezquiaga et al. (2023) is a phase-consistency test, not a Bayesian
  classifier. Rewrite as "the phase-consistency test of Ezquiaga et al.
  (2023)". **[check the submitted text]**
- Rename "selection function" to "lensing selection function" throughout
  (done in `main.tex`).
- Figure 6: use a common x-axis for relative magnification and impact
  parameter, or plot efficiency against the fainter-image SNR only and move
  the y / flux-ratio panels to the appendix, since the three are tightly
  linked.

----------------------------------------------------------------------
## 7. Data editor
----------------------------------------------------------------------

1. Add a LICENSE to the GitHub repository (MIT or BSD-3-Clause), deposit a
   tagged release on Zenodo with real author names and ORCIDs, a title
   specific to the software (e.g. "PI-ResNet: calibrated time-domain pair
   verification for strongly lensed gravitational waves, v1.0"), cite the DOI
   in the text (\software{}) and the reference list, and join the AAS Journals
   Zenodo community with the requested statement.
2. Lines 896–897: provide the data behind Figure 6 as CSV at revision: the
   files `results/core/selection_functions_*.csv` and
   `selection_rho1_rho2_*.csv` of the PI-ResNet repository (regenerated for the
   new population). State in the caption that the data are available as
   machine-readable tables.

----------------------------------------------------------------------
## 8. Checklist for the resubmission
----------------------------------------------------------------------

- [ ] Read Offermans+ 2411.12453, Barsode+ 2412.01278 and 2605.10333, Cheung+
      2308.12182, LensingFlow 2507.20256, LVK O4 lensing 2512.16347, Li+ 2025
      ApJS (SEMD). Fill the VERIFY entries in `refs.bib`.
- [ ] Regenerate catalogues with `ler` (Sec. 2 settings), O4 and ET.
- [ ] Retrain PI-ResNet and CQT-DeiT; re-run the frozen protocol.
- [ ] Run a posterior-overlap statistic on the same evaluation pairs; measure
      the joint efficiency of chain C.
- [ ] Population-mismatch test.
- [ ] Update `experiments/cost_model.py` with the published Barsode numbers
      and the new PI-ResNet efficiency-FAP curve.
- [ ] Re-run `scripts/gwtc/05_catalog_context_for_pair_verification.py` with
      O4a included (`01c_extract_gwtc4_observables.py` on the server).
- [ ] Revise (not rewrite) the abstract/introduction/conclusions around the
      pre-filter role; demote point-mass lenses to a lens-profile robustness
      test (Sec. 2b); remove old Sec. 5.2.
- [ ] Fig. 6 common axis; Table 3 metric definitions; "lensing selection
      function"; Ezquiaga wording.
- [ ] LICENSE, Zenodo DOI, CSV behind Fig. 6, \software{} list.
- [ ] Mark changes in colour in the resubmitted PDF (journal request).
