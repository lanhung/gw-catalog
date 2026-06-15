# stage1_liao_time_lr 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/liao_realistic_p1_p2_rerank_20260612/stage1_liao_time_lr` |
| 结果 CSV | `runs/liao_realistic_p1_p2_rerank_20260612/stage1_liao_time_lr/stage1_liao_time_lr_summary.csv` |
| prior 诊断 CSV | `runs/liao_realistic_p1_p2_rerank_20260612/stage1_liao_time_lr/liao_time_prior_diagnostics.csv` |

## 实验说明

- Stage1 只新增 GW-LMC/Liao time-delay step 与 likelihood-ratio prior。
- 本阶段不使用 observed sky，不使用 SNR ratio，不使用候选图项。
- time step 使用 Liao 检测多图像时延分布的 q10-q90/q05-q95/q01-q99 分位区间。
- p(delta_t|lensed) 来自 GW-LMC ImageParams 中检测到的多图像 pair time delay；p(delta_t|random) 来自当前 validation catalog 随机 pair。
- lambda 在 validation full catalog 上选择，然后应用到 test full catalog。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank | lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | liao_time_step_only | 0.499 | 0.499 | 0.499 | 0.5002 | 0.5015 | 0.5175 | 34 |  |
| ET | liao_time_lr_only | 0.1332 | 0.4085 | 0.5282 | 0.686 | 0.845 | 0.9162 | 9 |  |
| ET | waveform_plus_liao_time_step_val_selected | 0.329 | 0.5352 | 0.614 | 0.7998 | 0.892 | 0.9202 | 4 |  |
| ET | waveform_plus_liao_time_lr_val_selected | 0.6112 | 0.7527 | 0.8015 | 0.9243 | 0.9817 | 0.9915 | 1 | 1 |
| LIGO | liao_time_step_only | 0.5253 | 0.5253 | 0.5253 | 0.5267 | 0.528 | 0.5485 | 1 |  |
| LIGO | liao_time_lr_only | 0.1445 | 0.4127 | 0.5273 | 0.686 | 0.8397 | 0.9168 | 9 |  |
| LIGO | waveform_plus_liao_time_step_val_selected | 0.0108 | 0.031 | 0.043 | 0.15 | 0.2985 | 0.3923 | 1615 |  |
| LIGO | waveform_plus_liao_time_lr_val_selected | 0.1658 | 0.4112 | 0.5197 | 0.7093 | 0.8487 | 0.918 | 9 | 4 |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | SIS | liao_time_step_only | 0.8213 | 0.8213 | 0.8213 | 0.8237 | 1 |
| ET | PM | liao_time_step_only | 0.1767 | 0.1767 | 0.1767 | 0.1767 | 1396 |
| ET | SIS | liao_time_lr_only | 0.0137 | 0.0557 | 0.1087 | 0.372 | 172 |
| ET | PM | liao_time_lr_only | 0.2527 | 0.7613 | 0.9477 | 1 | 3 |
| ET | SIS | waveform_plus_liao_time_step_val_selected | 0.481 | 0.6623 | 0.7187 | 0.849 | 2 |
| ET | PM | waveform_plus_liao_time_step_val_selected | 0.177 | 0.408 | 0.5093 | 0.7507 | 10 |
| ET | SIS | waveform_plus_liao_time_lr_val_selected | 0.4347 | 0.625 | 0.695 | 0.868 | 2 |
| ET | PM | waveform_plus_liao_time_lr_val_selected | 0.7877 | 0.8803 | 0.908 | 0.9807 | 1 |
| LIGO | SIS | liao_time_step_only | 0.8213 | 0.8213 | 0.8213 | 0.824 | 1 |
| LIGO | PM | liao_time_step_only | 0.2293 | 0.2293 | 0.2293 | 0.2293 | 1293 |
| LIGO | SIS | liao_time_lr_only | 0.0113 | 0.0577 | 0.1107 | 0.372 | 176 |
| LIGO | PM | liao_time_lr_only | 0.2777 | 0.7677 | 0.944 | 1 | 3 |
| LIGO | SIS | waveform_plus_liao_time_step_val_selected | 0.0207 | 0.0567 | 0.0783 | 0.2307 | 984 |
| LIGO | PM | waveform_plus_liao_time_step_val_selected | 0.001 | 0.0053 | 0.0077 | 0.0693 | 2361.5 |
| LIGO | SIS | waveform_plus_liao_time_lr_val_selected | 0.026 | 0.0913 | 0.15 | 0.4187 | 144.5 |
| LIGO | PM | waveform_plus_liao_time_lr_val_selected | 0.3057 | 0.731 | 0.8893 | 1 | 3 |

## Liao prior 诊断

| detector | liao_label | liao_delay_count | liao_delay_median_days | liao_delay_p90_days | random_delay_median_days |
| --- | ---: | ---: | ---: | ---: | ---: |
| ET | GW-LMC ET BBH Any_Detected_SNR8 | 4388 | 37.378 | 284.6978 | 1087.2168 |
| LIGO | GW-LMC 2.5PLUS BBH Any_Detected_SNR1 | 4498 | 32.3848 | 269.5018 | 1087.2168 |