# stage1_liao_time_lr 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage1_liao_time_lr` |
| 结果 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage1_liao_time_lr/stage1_liao_time_lr_summary.csv` |
| prior 诊断 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage1_liao_time_lr/liao_time_prior_diagnostics.csv` |

## 实验说明

- Stage1 只新增 GW-LMC/Liao time-delay step 与 likelihood-ratio prior。
- 本阶段不使用 observed sky，不使用 SNR ratio，不使用候选图项。
- time step 使用 Liao 检测多图像时延分布的 q10-q90/q05-q95/q01-q99 分位区间。
- p(delta_t|lensed) 来自 GW-LMC ImageParams 中检测到的多图像 pair time delay；p(delta_t|random) 来自当前 validation catalog 随机 pair。
- lambda 在 validation full catalog 上选择，然后应用到 test full catalog。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank | lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | liao_time_step_only | 0.5253 | 0.5253 | 0.5253 | 0.5267 | 0.528 | 0.5485 | 1 |  |
| LIGO | liao_time_lr_only | 0.1445 | 0.4127 | 0.5273 | 0.686 | 0.8397 | 0.9168 | 9 |  |
| LIGO | waveform_plus_liao_time_step_val_selected | 0.0078 | 0.029 | 0.0417 | 0.1455 | 0.289 | 0.3825 | 1671.5 |  |
| LIGO | waveform_plus_liao_time_lr_val_selected | 0.1705 | 0.4072 | 0.5167 | 0.7118 | 0.8515 | 0.9155 | 9 | 4 |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | SIS | liao_time_step_only | 0.8213 | 0.8213 | 0.8213 | 0.824 | 1 |
| LIGO | PM | liao_time_step_only | 0.2293 | 0.2293 | 0.2293 | 0.2293 | 1293 |
| LIGO | SIS | liao_time_lr_only | 0.0113 | 0.0577 | 0.1107 | 0.372 | 176 |
| LIGO | PM | liao_time_lr_only | 0.2777 | 0.7677 | 0.944 | 1 | 3 |
| LIGO | SIS | waveform_plus_liao_time_step_val_selected | 0.0143 | 0.0523 | 0.0733 | 0.217 | 1062.5 |
| LIGO | PM | waveform_plus_liao_time_step_val_selected | 0.0013 | 0.0057 | 0.01 | 0.074 | 2372.5 |
| LIGO | SIS | waveform_plus_liao_time_lr_val_selected | 0.028 | 0.089 | 0.1493 | 0.4237 | 144 |
| LIGO | PM | waveform_plus_liao_time_lr_val_selected | 0.313 | 0.7253 | 0.884 | 1 | 3 |

## Liao prior 诊断

| detector | liao_label | liao_delay_count | liao_delay_median_days | liao_delay_p90_days | random_delay_median_days |
| --- | ---: | ---: | ---: | ---: | ---: |
| LIGO | GW-LMC 2.5PLUS BBH Any_Detected_SNR1 | 4498 | 32.3848 | 269.5018 | 1087.2168 |