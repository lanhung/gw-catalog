# stage3_liao_time_plus_observed_sky 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/liao_realistic_p1_p2_rerank_20260612/stage3_liao_time_plus_observed_sky` |
| 结果 CSV | `runs/liao_realistic_p1_p2_rerank_20260612/stage3_liao_time_plus_observed_sky/stage3_liao_time_plus_observed_sky_summary.csv` |
| prior 诊断 CSV | `runs/liao_realistic_p1_p2_rerank_20260612/stage3_liao_time_plus_observed_sky/stage3_prior_sky_diagnostics.csv` |

## 实验说明

- Stage3 只融合 Liao time-delay LR 与 observed sky posterior，不使用 SNR ratio、不使用候选图。
- 本阶段用于回答：Liao 时间先验与 observed sky 是否互补。
- 分别测试 observed sky step 与 observed sky gaussian/log-overlap 两种空间特征。
- lambda_time 与 lambda_sky 均在 validation full catalog 上网格选择，然后应用到 test full catalog。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank | lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.896 | 0.9708 | 0.9825 | 0.9972 | 0.9997 | 0.9997 | 1 | 1 |
| ET | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.7795 | 0.8827 | 0.9177 | 0.9865 | 0.9975 | 0.9995 | 1 | 1 |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.658 | 0.8567 | 0.9073 | 0.9903 | 0.9985 | 0.9993 | 1 | 4 |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.3792 | 0.6062 | 0.6742 | 0.839 | 0.9478 | 0.9833 | 3 | 2 |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | SIS | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.843 | 0.9553 | 0.9717 | 0.995 | 1 |
| ET | PM | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.949 | 0.9863 | 0.9933 | 0.9993 | 1 |
| ET | SIS | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.6653 | 0.8077 | 0.8573 | 0.974 | 1 |
| ET | PM | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.8937 | 0.9577 | 0.978 | 0.999 | 1 |
| LIGO | SIS | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.4327 | 0.7263 | 0.8197 | 0.9807 | 2 |
| LIGO | PM | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.8833 | 0.987 | 0.995 | 1 | 1 |
| LIGO | SIS | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.131 | 0.2963 | 0.3823 | 0.678 | 26 |
| LIGO | PM | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.6273 | 0.916 | 0.966 | 1 | 1 |

## Liao time + observed sky 诊断

| detector | liao_label | liao_delay_count | liao_delay_median_days | liao_delay_p90_days | sky_label | a90_ref_deg2 | test_a90_median_deg2 | test_a90_p90_deg2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | GW-LMC ET BBH Any_Detected_SNR8 | 4388 | 37.378 | 284.6978 | ET single-site baseline A90=300 deg2 | 300 | 50 | 354.4461 |
| LIGO | GW-LMC 2.5PLUS BBH Any_Detected_SNR1 | 4498 | 32.3848 | 269.5018 | LIGO/2.5G HL-like baseline A90=100 deg2 | 100 | 399.3517 | 500 |