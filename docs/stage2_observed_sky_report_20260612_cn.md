# stage2_observed_sky 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/liao_realistic_p1_p2_rerank_20260612/stage2_observed_sky` |
| 结果 CSV | `runs/liao_realistic_p1_p2_rerank_20260612/stage2_observed_sky/stage2_observed_sky_summary.csv` |
| prior 诊断 CSV | `runs/liao_realistic_p1_p2_rerank_20260612/stage2_observed_sky/observed_sky_diagnostics.csv` |

## 实验说明

- Stage2 只新增 observed sky posterior，不使用 Liao time LR、不使用 SNR ratio、不使用候选图。
- true ra/dec 只用于模拟观测中心 ra_obs/dec_obs 和 sky_area90；rerank 输入只使用 observed sky posterior 特征。
- 分别测试 observed sky step 和 observed sky gaussian/log-overlap。
- A90 sweep 按任务文档测试 ET=100/300/1000 deg2 与 LIGO=50/100/200 deg2。
- lambda 在 validation full catalog 上选择，然后应用到 test full catalog。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank | lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | observed_sky_step_only | 0.7497 | 0.752 | 0.778 | 0.9943 | 0.9998 | 1 | 1 |  |
| ET | observed_sky_log_overlap_only | 0.2357 | 0.5878 | 0.7532 | 0.9862 | 0.9993 | 1 | 4 |  |
| ET | waveform_plus_observed_sky_step_val_selected | 0.7738 | 0.888 | 0.9152 | 0.9615 | 0.9817 | 0.988 | 1 |  |
| ET | waveform_plus_observed_sky_log_overlap_val_selected | 0.6225 | 0.7543 | 0.793 | 0.8977 | 0.9563 | 0.9815 | 1 |  |
| ET | a90_100_step_val_selected | 0.79 | 0.9132 | 0.9457 | 0.9837 | 0.9918 | 0.9943 | 1 |  |
| ET | a90_100_gaussian_log_overlap_val_selected | 0.6312 | 0.7585 | 0.8005 | 0.904 | 0.961 | 0.9863 | 1 |  |
| ET | a90_300_step_val_selected | 0.78 | 0.8895 | 0.916 | 0.9647 | 0.982 | 0.9872 | 1 |  |
| ET | a90_300_gaussian_log_overlap_val_selected | 0.6253 | 0.7535 | 0.7935 | 0.898 | 0.9563 | 0.9812 | 1 |  |
| ET | a90_1000_step_val_selected | 0.6902 | 0.835 | 0.8718 | 0.9653 | 0.9888 | 0.9945 | 1 |  |
| ET | a90_1000_gaussian_log_overlap_val_selected | 0.6125 | 0.744 | 0.786 | 0.8927 | 0.9548 | 0.9785 | 1 |  |
| LIGO | observed_sky_step_only | 0.771 | 0.771 | 0.7713 | 0.986 | 1 | 1 | 1 |  |
| LIGO | observed_sky_log_overlap_only | 0.1958 | 0.3827 | 0.4925 | 0.9387 | 1 | 1 | 11 |  |
| LIGO | waveform_plus_observed_sky_step_val_selected | 0.171 | 0.2958 | 0.3895 | 0.853 | 0.9812 | 0.9898 | 17 |  |
| LIGO | waveform_plus_observed_sky_log_overlap_val_selected | 0.0735 | 0.1375 | 0.1752 | 0.3503 | 0.607 | 0.7558 | 259 |  |
| LIGO | a90_50_step_val_selected | 0.1908 | 0.322 | 0.4358 | 0.9123 | 0.9877 | 0.9925 | 13 |  |
| LIGO | a90_50_gaussian_log_overlap_val_selected | 0.0713 | 0.1365 | 0.1735 | 0.3372 | 0.5772 | 0.7237 | 293 |  |
| LIGO | a90_100_step_val_selected | 0.1707 | 0.2977 | 0.386 | 0.8577 | 0.9768 | 0.9847 | 18 |  |
| LIGO | a90_100_gaussian_log_overlap_val_selected | 0.0728 | 0.1375 | 0.1748 | 0.3507 | 0.6072 | 0.7592 | 259 |  |
| LIGO | a90_200_step_val_selected | 0.1425 | 0.2603 | 0.3448 | 0.8078 | 0.9745 | 0.9862 | 23 |  |
| LIGO | a90_200_gaussian_log_overlap_val_selected | 0.0722 | 0.1382 | 0.1753 | 0.3593 | 0.6307 | 0.7882 | 235.5 |  |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | SIS | observed_sky_step_only | 0.746 | 0.7487 | 0.7757 | 0.9977 | 1 |
| ET | PM | observed_sky_step_only | 0.7533 | 0.7553 | 0.7803 | 0.991 | 1 |
| ET | SIS | observed_sky_log_overlap_only | 0.246 | 0.61 | 0.7817 | 0.9937 | 4 |
| ET | PM | observed_sky_log_overlap_only | 0.2253 | 0.5657 | 0.7247 | 0.9787 | 4 |
| ET | SIS | waveform_plus_observed_sky_step_val_selected | 0.81 | 0.921 | 0.9443 | 0.9773 | 1 |
| ET | PM | waveform_plus_observed_sky_step_val_selected | 0.7377 | 0.855 | 0.886 | 0.9457 | 1 |
| ET | SIS | waveform_plus_observed_sky_log_overlap_val_selected | 0.6777 | 0.796 | 0.8283 | 0.928 | 1 |
| ET | PM | waveform_plus_observed_sky_log_overlap_val_selected | 0.5673 | 0.7127 | 0.7577 | 0.8673 | 1 |
| ET | SIS | a90_100_step_val_selected | 0.829 | 0.935 | 0.964 | 0.9877 | 1 |
| ET | PM | a90_100_step_val_selected | 0.751 | 0.8913 | 0.9273 | 0.9797 | 1 |
| ET | SIS | a90_100_gaussian_log_overlap_val_selected | 0.683 | 0.8007 | 0.8363 | 0.9343 | 1 |
| ET | PM | a90_100_gaussian_log_overlap_val_selected | 0.5793 | 0.7163 | 0.7647 | 0.8737 | 1 |
| ET | SIS | a90_300_step_val_selected | 0.8157 | 0.92 | 0.9397 | 0.9787 | 1 |
| ET | PM | a90_300_step_val_selected | 0.7443 | 0.859 | 0.8923 | 0.9507 | 1 |
| ET | SIS | a90_300_gaussian_log_overlap_val_selected | 0.679 | 0.7947 | 0.8287 | 0.9283 | 1 |
| ET | PM | a90_300_gaussian_log_overlap_val_selected | 0.5717 | 0.7123 | 0.7583 | 0.8677 | 1 |
| ET | SIS | a90_1000_step_val_selected | 0.7277 | 0.8727 | 0.903 | 0.9773 | 1 |
| ET | PM | a90_1000_step_val_selected | 0.6527 | 0.7973 | 0.8407 | 0.9533 | 1 |
| ET | SIS | a90_1000_gaussian_log_overlap_val_selected | 0.665 | 0.786 | 0.8207 | 0.9227 | 1 |
| ET | PM | a90_1000_gaussian_log_overlap_val_selected | 0.56 | 0.702 | 0.7513 | 0.8627 | 1 |
| LIGO | SIS | observed_sky_step_only | 0.7767 | 0.7767 | 0.7773 | 0.988 | 1 |
| LIGO | PM | observed_sky_step_only | 0.7653 | 0.7653 | 0.7653 | 0.984 | 1 |
| LIGO | SIS | observed_sky_log_overlap_only | 0.2377 | 0.4477 | 0.565 | 0.9567 | 8 |
| LIGO | PM | observed_sky_log_overlap_only | 0.154 | 0.3177 | 0.42 | 0.9207 | 15 |
| LIGO | SIS | waveform_plus_observed_sky_step_val_selected | 0.204 | 0.3513 | 0.4473 | 0.8767 | 14 |
| LIGO | PM | waveform_plus_observed_sky_step_val_selected | 0.138 | 0.2403 | 0.3317 | 0.8293 | 22 |
| LIGO | SIS | waveform_plus_observed_sky_log_overlap_val_selected | 0.092 | 0.165 | 0.2093 | 0.4017 | 194.5 |
| LIGO | PM | waveform_plus_observed_sky_log_overlap_val_selected | 0.055 | 0.11 | 0.141 | 0.299 | 331.5 |
| LIGO | SIS | a90_50_step_val_selected | 0.2273 | 0.371 | 0.4853 | 0.9277 | 11 |
| LIGO | PM | a90_50_step_val_selected | 0.1543 | 0.273 | 0.3863 | 0.897 | 16 |
| LIGO | SIS | a90_50_gaussian_log_overlap_val_selected | 0.0887 | 0.1633 | 0.2057 | 0.388 | 221.5 |
| LIGO | PM | a90_50_gaussian_log_overlap_val_selected | 0.054 | 0.1097 | 0.1413 | 0.2863 | 367.5 |
| LIGO | SIS | a90_100_step_val_selected | 0.201 | 0.3483 | 0.4397 | 0.8773 | 14 |
| LIGO | PM | a90_100_step_val_selected | 0.1403 | 0.247 | 0.3323 | 0.838 | 22 |
| LIGO | SIS | a90_100_gaussian_log_overlap_val_selected | 0.0893 | 0.1643 | 0.2073 | 0.4027 | 193.5 |
| LIGO | PM | a90_100_gaussian_log_overlap_val_selected | 0.0563 | 0.1107 | 0.1423 | 0.2987 | 329 |
| LIGO | SIS | a90_200_step_val_selected | 0.174 | 0.3113 | 0.3977 | 0.827 | 19 |
| LIGO | PM | a90_200_step_val_selected | 0.111 | 0.2093 | 0.292 | 0.7887 | 28 |
| LIGO | SIS | a90_200_gaussian_log_overlap_val_selected | 0.0897 | 0.1647 | 0.2103 | 0.4103 | 174.5 |
| LIGO | PM | a90_200_gaussian_log_overlap_val_selected | 0.0547 | 0.1117 | 0.1403 | 0.3083 | 298.5 |

## Observed sky 诊断

| detector | sky_label | a90_ref_deg2 | test_a90_median_deg2 | test_a90_p90_deg2 | test_sigma_median_rad |
| --- | ---: | ---: | ---: | ---: | ---: |
| ET | ET single-site baseline A90=300 deg2 | 300 | 50 | 344.5647 | 0.0324 |
| LIGO | LIGO/2.5G HL-like baseline A90=100 deg2 | 100 | 399.2011 | 500 | 0.0917 |