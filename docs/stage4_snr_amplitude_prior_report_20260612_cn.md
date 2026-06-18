# stage4_snr_amplitude_prior 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage4_snr_amplitude_prior` |
| 结果 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage4_snr_amplitude_prior/stage4_snr_amplitude_prior_summary.csv` |
| prior 诊断 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage4_snr_amplitude_prior/amp_time_prior_diagnostics.csv` |

## 实验说明

- Stage4 在 Stage3 的 waveform + Liao time LR + observed sky gaussian/log-overlap 基础上，只新增 SNR/amplitude 信息。
- A1 使用 raw SNR ratio baseline：两个事件 observed SNR 越接近，分数越高。
- A2 使用 GW-LMC/Liao 的二维 time-SNR ratio likelihood-ratio prior，即 p(delta_t, R_snr|lensed) / p(delta_t, R_snr|random)。
- 所有 lambda 都在 validation full catalog 上选择，然后应用到 test full catalog。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank | lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | waveform_plus_time_lr_plus_sky_log_overlap | 0.3667 | 0.5947 | 0.6652 | 0.8385 | 0.9522 | 0.9843 | 3 |  |
| LIGO | plus_raw_snr_ratio | 0.4105 | 0.6145 | 0.6835 | 0.8608 | 0.9615 | 0.9875 | 2 |  |
| LIGO | plus_amp_time_2d_lr | 0.3683 | 0.6017 | 0.6685 | 0.8335 | 0.9483 | 0.9822 | 3 |  |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | SIS | waveform_plus_time_lr_plus_sky_log_overlap | 0.1207 | 0.2797 | 0.3653 | 0.677 | 28.5 |
| LIGO | PM | waveform_plus_time_lr_plus_sky_log_overlap | 0.6127 | 0.9097 | 0.965 | 1 | 1 |
| LIGO | SIS | plus_raw_snr_ratio | 0.175 | 0.3333 | 0.4123 | 0.722 | 21 |
| LIGO | PM | plus_raw_snr_ratio | 0.646 | 0.8957 | 0.9547 | 0.9997 | 1 |
| LIGO | SIS | plus_amp_time_2d_lr | 0.1103 | 0.2713 | 0.356 | 0.667 | 29 |
| LIGO | PM | plus_amp_time_2d_lr | 0.6263 | 0.932 | 0.981 | 1 | 1 |

## Liao prior 诊断

| detector | liao_label | liao_delay_count | liao_delay_median_days | liao_delay_p90_days | random_delay_median_days |
| --- | ---: | ---: | ---: | ---: | ---: |
| LIGO | GW-LMC 2.5PLUS BBH Any_Detected_SNR1 | 4498 |  |  |  |