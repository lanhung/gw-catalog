# Realistic population workflow (reviewer request: astrophysical populations)

Three scripts replace the uniform-prior simulations of the original submission.
All three run inside the `ler` virtual environment (`/home/user/ler-venv` here;
on the server create one with `python -m venv ler-venv && ler-venv/bin/pip install ler`,
which pulls in bilby, lalsuite, pycbc, gwsnr and lenstronomy).

| Step | Script | What it does | Cost |
|---|---|---|---|
| 1 | `ler_realistic_population.py --config O4` (and `--config ET`) | Draws the LVK-like BBH population (ler defaults: GWTC-3 Power Law + Peak masses, star-formation-history merger rate with time delay, z up to 10) and EPL + shear galaxy lenses (SDSS-type velocity-dispersion function, lens redshift from the optical depth, source position uniform in the caustic). Keeps systems with two images above the SNR threshold. Writes `data/ler_population/<cfg>_lensed_pairs.csv`, `<cfg>_unlensed_events.csv`, `<cfg>_meta.json` (rates) and the full ler JSON under `--work-dir/ler_data_<cfg>/`. | first run builds lookup tables (~30 min on 4 cores); afterwards minutes |
| 2 | `analyse_ler_population.py` | Distributions of fainter-image SNR, flux ratio, delay, image types, source redshift; fraction of detectable pairs inside the original simulation domain (y <= 0.3, i.e. flux ratio <= 1.9). Figure `fig_ler_population.pdf` and `population_summary.json`. | seconds |
| 3 | `generate_strain_from_ler.py --config O4 --ler-dir <work-dir>/ler_data_O4 --out data/ler_strain_O4` | Whitened strain pairs in the layout of the original generator (peak at N-1500, Hann fade), with the two brightest detected images, Morse phase from the image type, second image injected at the delayed time. | ~1-3 s per pair with IMRPhenomXPHM on one core; run on the server for the full set |

Detector configurations: `O4` = H1, L1 (aLIGO O4 high ASD) + V1 (AdV); `ET` = bilby's
triangular Einstein Telescope with the ET-D PSD. Detection: network optimal SNR >= 8
for each of the two images.

Then retrain PI-ResNet and CQT-DeiT on the `O4` and `ET` sets with the frozen
protocol of the original submission (independent threshold-setting and
measurement catalogues: run step 1 twice with different `--seed`s, or split by
system). The point-mass lens class is not produced by `ler`; if it is kept as a
lens-profile robustness test, generate it with the original point-mass code on
the ler source population (same `mass_1_source`, `zs`, spins) with the impact
parameter sampled as p(y) ~ y.
