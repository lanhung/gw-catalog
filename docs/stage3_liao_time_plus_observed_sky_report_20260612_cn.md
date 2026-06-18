# stage3_liao_time_plus_observed_sky 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage3_liao_time_plus_observed_sky` |
| 结果 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage3_liao_time_plus_observed_sky/stage3_liao_time_plus_observed_sky_summary.csv` |
| prior 诊断 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage3_liao_time_plus_observed_sky/stage3_prior_sky_diagnostics.csv` |

## 实验说明

- Stage3 只融合 Liao time-delay LR 与 observed sky posterior，不使用 SNR ratio、不使用候选图。
- 本阶段用于回答：Liao 时间先验与 observed sky 是否互补。
- 分别测试 observed sky step 与 observed sky gaussian/log-overlap 两种空间特征。
- lambda_time 与 lambda_sky 均在 validation full catalog 上网格选择，然后应用到 test full catalog。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank | lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.5117 | 0.7645 | 0.8465 | 0.977 | 0.9938 | 0.999 | 1 | 4 |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.3653 | 0.5953 | 0.6667 | 0.8367 | 0.9518 | 0.9835 | 3 | 2 |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | SIS | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.2963 | 0.5813 | 0.712 | 0.954 | 4 |
| LIGO | PM | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.727 | 0.9477 | 0.981 | 1 | 1 |
| LIGO | SIS | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.1233 | 0.2837 | 0.3693 | 0.6733 | 28 |
| LIGO | PM | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.6073 | 0.907 | 0.964 | 1 | 1 |

## Liao time + observed sky 诊断

| detector | liao_label | liao_delay_count | liao_delay_median_days | liao_delay_p90_days | sky_label | a90_ref_deg2 | test_a90_median_deg2 | test_a90_p90_deg2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | GW-LMC 2.5PLUS BBH Any_Detected_SNR1 | 4498 | 32.3848 | 269.5018 | LIGO H1+L1 network A90 approximation | 100 | 399.3517 | 500 |