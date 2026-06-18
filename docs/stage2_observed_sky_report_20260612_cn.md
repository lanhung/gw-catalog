# stage2_observed_sky 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage2_observed_sky` |
| 结果 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage2_observed_sky/stage2_observed_sky_summary.csv` |
| prior 诊断 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage2_observed_sky/observed_sky_diagnostics.csv` |

## 实验说明

- Stage2 只新增 observed sky posterior，不使用 Liao time LR、不使用 SNR ratio、不使用候选图。
- true ra/dec 只用于模拟观测中心 ra_obs/dec_obs 和 sky_area90；rerank 输入只使用 observed sky posterior 特征。
- 分别测试 observed sky step 和 observed sky gaussian/log-overlap。
- A90 sweep 按任务文档测试 ET=100/300/1000 deg2 与 LIGO=50/100/200 deg2。
- lambda 在 validation full catalog 上选择，然后应用到 test full catalog。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank | lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | observed_sky_step_only | 0.5113 | 0.5113 | 0.5113 | 0.9325 | 1 | 1 | 1 |  |
| LIGO | observed_sky_log_overlap_only | 0.1267 | 0.2762 | 0.3672 | 0.8317 | 0.998 | 1 | 24 |  |
| LIGO | waveform_plus_observed_sky_step_val_selected | 0.1382 | 0.2552 | 0.3175 | 0.5767 | 0.73 | 0.8022 | 45 |  |
| LIGO | waveform_plus_observed_sky_log_overlap_val_selected | 0.0652 | 0.131 | 0.1688 | 0.3298 | 0.5897 | 0.7552 | 290 |  |
| LIGO | a90_50_step_val_selected | 0.1497 | 0.2712 | 0.3543 | 0.6507 | 0.788 | 0.849 | 28 |  |
| LIGO | a90_50_gaussian_log_overlap_val_selected | 0.0638 | 0.1302 | 0.1663 | 0.322 | 0.5602 | 0.7168 | 331 |  |
| LIGO | a90_100_step_val_selected | 0.1412 | 0.2507 | 0.3152 | 0.573 | 0.7255 | 0.803 | 46 |  |
| LIGO | a90_100_gaussian_log_overlap_val_selected | 0.064 | 0.1313 | 0.1693 | 0.3307 | 0.5887 | 0.7505 | 290.5 |  |
| LIGO | a90_200_step_val_selected | 0.1153 | 0.2265 | 0.2827 | 0.5227 | 0.6843 | 0.7685 | 71 |  |
| LIGO | a90_200_gaussian_log_overlap_val_selected | 0.0628 | 0.1298 | 0.1688 | 0.3415 | 0.6125 | 0.7807 | 258 |  |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | SIS | observed_sky_step_only | 0.512 | 0.512 | 0.512 | 0.9333 | 1 |
| LIGO | PM | observed_sky_step_only | 0.5107 | 0.5107 | 0.5107 | 0.9317 | 1 |
| LIGO | SIS | observed_sky_log_overlap_only | 0.148 | 0.323 | 0.4227 | 0.8563 | 17 |
| LIGO | PM | observed_sky_log_overlap_only | 0.1053 | 0.2293 | 0.3117 | 0.807 | 31 |
| LIGO | SIS | waveform_plus_observed_sky_step_val_selected | 0.159 | 0.2987 | 0.3683 | 0.629 | 30 |
| LIGO | PM | waveform_plus_observed_sky_step_val_selected | 0.1173 | 0.2117 | 0.2667 | 0.5243 | 71 |
| LIGO | SIS | waveform_plus_observed_sky_log_overlap_val_selected | 0.076 | 0.1487 | 0.1903 | 0.3787 | 218.5 |
| LIGO | PM | waveform_plus_observed_sky_log_overlap_val_selected | 0.0543 | 0.1133 | 0.1473 | 0.281 | 356.5 |
| LIGO | SIS | a90_50_step_val_selected | 0.1747 | 0.323 | 0.4137 | 0.6877 | 20 |
| LIGO | PM | a90_50_step_val_selected | 0.1247 | 0.2193 | 0.295 | 0.6137 | 40 |
| LIGO | SIS | a90_50_gaussian_log_overlap_val_selected | 0.0723 | 0.1483 | 0.186 | 0.3707 | 254 |
| LIGO | PM | a90_50_gaussian_log_overlap_val_selected | 0.0553 | 0.112 | 0.1467 | 0.2733 | 406.5 |
| LIGO | SIS | a90_100_step_val_selected | 0.1667 | 0.289 | 0.3587 | 0.6137 | 31 |
| LIGO | PM | a90_100_step_val_selected | 0.1157 | 0.2123 | 0.2717 | 0.5323 | 68 |
| LIGO | SIS | a90_100_gaussian_log_overlap_val_selected | 0.0737 | 0.148 | 0.191 | 0.38 | 225.5 |
| LIGO | PM | a90_100_gaussian_log_overlap_val_selected | 0.0543 | 0.1147 | 0.1477 | 0.2813 | 360 |
| LIGO | SIS | a90_200_step_val_selected | 0.132 | 0.262 | 0.325 | 0.5683 | 45 |
| LIGO | PM | a90_200_step_val_selected | 0.0987 | 0.191 | 0.2403 | 0.477 | 117.5 |
| LIGO | SIS | a90_200_gaussian_log_overlap_val_selected | 0.0737 | 0.1473 | 0.1913 | 0.3903 | 198.5 |
| LIGO | PM | a90_200_gaussian_log_overlap_val_selected | 0.052 | 0.1123 | 0.1463 | 0.2927 | 324.5 |

## Observed sky 诊断

| detector | sky_label | a90_ref_deg2 | test_a90_median_deg2 | test_a90_p90_deg2 | test_sigma_median_rad |
| --- | ---: | ---: | ---: | ---: | ---: |
| LIGO | LIGO H1+L1 network A90 approximation | 100 | 399.2011 | 500 | 0.0917 |