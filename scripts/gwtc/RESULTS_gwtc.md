# GWTC real-data LensGraph physical reranker results

## Candidate reproduction

Candidate pair: `GW170104-GW170814`

| score | value | rank | total pairs |
| --- | ---: | ---: | ---: |
| sky_step_weight | -0.5000 | 717 | 1953 |
| sky_log_overlap | -79.0780 | 1703 | 1953 |
| sky_norm_sep (ascending) | 12.7280 | 1702 | 1953 |
| time_score | -1.3033 | 1361 | 1953 |
| combined_time_sky_z | -1.0378 | 1537 | 1953 |

Physical narrative check: **EXPLAIN** - time-only ranks low as expected, but this observable-only sky-center/A90 proxy does not rank the pair sky-high. The observed delay is 222.01 days and the Gaussian sky-center separation is 111.22 deg.

This means the current real-data observable-only layer correctly down-weights the long time delay, but it does not by itself reproduce the literature's parameter-consistency statement for GW170104-GW170814. That statement should be tested with posterior/parameter-overlap features such as the optional Prompt 5 baseline.

## Null catalog shortlist

| catalog | pairs | Campailla fraction equivalent count | equivalent threshold | top-185 fraction |
| --- | ---: | ---: | ---: | ---: |
| GWTC-3 PE-supported | 1953 | 99 | 1.8944 | 0.0947 |
| GWTC-5 strict BBH | 5460 | 276 | 1.8637 | 0.0339 |

Figures written under `figures_gwtc/`: `fig_gwtc_candidate_ranks`, `fig_gwtc_null_threshold`, and `fig_gwtc_score_hist` as PNG and PDF.

## Injection recovery

Synthetic lensed pairs were injected into the real GWTC observable catalogs. Source sky/A90/SNR are sampled from the real catalog distribution, time delays and SNR ratios are sampled from the Liao LIGO lensing prior, and each pair shares the same latent sky with independent 2D Gaussian observed-sky errors.

Per-seed records: `/root/autodl-tmp/gw-catalog/data/gwtc_injection_recovery_records.csv`
Averaged summary: `/root/autodl-tmp/gw-catalog/data/gwtc_injection_recovery_summary.csv`

| catalog | injected pairs | score | median rank | MRR | R@1 | R@5 | R@10 | R@50 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gwtc3 | 10 | combined_time_sky | 1.65+/-0.71 | 0.6091+/-0.0766 | 0.470+/-0.116 | 0.775+/-0.118 | 0.835+/-0.116 | 0.990+/-0.021 |
| gwtc3 | 10 | sky_log_overlap | 4.20+/-3.12 | 0.3668+/-0.0996 | 0.100+/-0.088 | 0.640+/-0.179 | 0.755+/-0.162 | 1.000+/-0.000 |
| gwtc3 | 10 | sky_step | 2.80+/-2.20 | 0.6206+/-0.1330 | 0.550+/-0.149 | 0.690+/-0.176 | 0.855+/-0.126 | 1.000+/-0.000 |
| gwtc3 | 10 | time_lr | 2.85+/-2.01 | 0.5335+/-0.0564 | 0.400+/-0.067 | 0.685+/-0.123 | 0.790+/-0.149 | 0.960+/-0.039 |
| gwtc3 | 20 | combined_time_sky | 1.80+/-0.82 | 0.6077+/-0.0961 | 0.467+/-0.118 | 0.802+/-0.090 | 0.890+/-0.064 | 0.990+/-0.013 |
| gwtc3 | 20 | sky_log_overlap | 4.75+/-2.96 | 0.3310+/-0.0708 | 0.113+/-0.050 | 0.600+/-0.134 | 0.725+/-0.115 | 0.997+/-0.008 |
| gwtc3 | 20 | sky_step | 2.90+/-2.46 | 0.5935+/-0.1045 | 0.530+/-0.111 | 0.625+/-0.135 | 0.850+/-0.104 | 1.000+/-0.000 |
| gwtc3 | 20 | time_lr | 2.80+/-0.82 | 0.4868+/-0.0909 | 0.325+/-0.103 | 0.700+/-0.110 | 0.812+/-0.075 | 0.975+/-0.024 |
| gwtc3 | 50 | combined_time_sky | 3.40+/-0.70 | 0.4558+/-0.0260 | 0.302+/-0.033 | 0.640+/-0.064 | 0.769+/-0.047 | 0.967+/-0.015 |
| gwtc3 | 50 | sky_log_overlap | 5.70+/-1.40 | 0.2937+/-0.0228 | 0.113+/-0.026 | 0.507+/-0.069 | 0.655+/-0.071 | 0.964+/-0.018 |
| gwtc3 | 50 | sky_step | 2.00+/-1.63 | 0.5996+/-0.0713 | 0.556+/-0.079 | 0.592+/-0.072 | 0.747+/-0.059 | 0.998+/-0.004 |
| gwtc3 | 50 | time_lr | 5.40+/-1.13 | 0.3457+/-0.0331 | 0.203+/-0.052 | 0.510+/-0.054 | 0.642+/-0.051 | 0.933+/-0.027 |
| gwtc5 | 10 | combined_time_sky | 14.80+/-8.76 | 0.2616+/-0.1059 | 0.155+/-0.114 | 0.370+/-0.144 | 0.500+/-0.175 | 0.830+/-0.127 |
| gwtc5 | 10 | sky_log_overlap | 4.25+/-1.27 | 0.3304+/-0.0542 | 0.085+/-0.063 | 0.615+/-0.147 | 0.785+/-0.082 | 0.990+/-0.032 |
| gwtc5 | 10 | sky_step | 2.90+/-1.61 | 0.6030+/-0.1324 | 0.515+/-0.156 | 0.700+/-0.122 | 0.910+/-0.077 | 1.000+/-0.000 |
| gwtc5 | 10 | time_lr | 26.00+/-14.85 | 0.1834+/-0.0785 | 0.100+/-0.078 | 0.260+/-0.141 | 0.335+/-0.131 | 0.720+/-0.125 |
| gwtc5 | 20 | combined_time_sky | 12.25+/-5.07 | 0.2429+/-0.0644 | 0.133+/-0.064 | 0.323+/-0.096 | 0.512+/-0.129 | 0.850+/-0.093 |
| gwtc5 | 20 | sky_log_overlap | 3.55+/-1.04 | 0.3647+/-0.0623 | 0.140+/-0.064 | 0.628+/-0.074 | 0.787+/-0.073 | 0.993+/-0.017 |
| gwtc5 | 20 | sky_step | 2.55+/-1.77 | 0.5989+/-0.1154 | 0.512+/-0.138 | 0.695+/-0.113 | 0.903+/-0.075 | 1.000+/-0.000 |
| gwtc5 | 20 | time_lr | 24.60+/-10.00 | 0.1781+/-0.0613 | 0.092+/-0.058 | 0.230+/-0.086 | 0.312+/-0.092 | 0.738+/-0.110 |
| gwtc5 | 50 | combined_time_sky | 15.85+/-3.04 | 0.2135+/-0.0355 | 0.123+/-0.041 | 0.281+/-0.040 | 0.410+/-0.044 | 0.758+/-0.050 |
| gwtc5 | 50 | sky_log_overlap | 5.05+/-0.96 | 0.3097+/-0.0340 | 0.123+/-0.032 | 0.529+/-0.060 | 0.716+/-0.058 | 0.977+/-0.021 |
| gwtc5 | 50 | sky_step | 2.55+/-1.80 | 0.5755+/-0.0649 | 0.511+/-0.075 | 0.615+/-0.071 | 0.803+/-0.064 | 0.993+/-0.011 |
| gwtc5 | 50 | time_lr | 33.65+/-6.77 | 0.1530+/-0.0301 | 0.084+/-0.025 | 0.201+/-0.053 | 0.265+/-0.062 | 0.612+/-0.049 |

Figure written under `figures_gwtc/fig_gwtc_injection_recovery.{png,pdf}`.
