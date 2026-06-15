# stage4_snr_amplitude_prior 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/liao_realistic_p1_p2_rerank_20260612/stage4_snr_amplitude_prior` |
| 结果 CSV | `runs/liao_realistic_p1_p2_rerank_20260612/stage4_snr_amplitude_prior/stage4_snr_amplitude_prior_summary.csv` |
| prior 诊断 CSV | `runs/liao_realistic_p1_p2_rerank_20260612/stage4_snr_amplitude_prior/amp_time_prior_diagnostics.csv` |

## 实验说明

- Stage4 在 Stage3 的 waveform + Liao time LR + observed sky gaussian/log-overlap 基础上，只新增 SNR/amplitude 信息。
- A1 使用 raw SNR ratio baseline：两个事件 observed SNR 越接近，分数越高。
- A2 使用 GW-LMC/Liao 的二维 time-SNR ratio likelihood-ratio prior，即 p(delta_t, R_snr|lensed) / p(delta_t, R_snr|random)。
- 所有 lambda 都在 validation full catalog 上选择，然后应用到 test full catalog。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank | lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | waveform_plus_time_lr_plus_sky_log_overlap | 0.78 | 0.8833 | 0.9187 | 0.9862 | 0.9973 | 0.9995 | 1 |  |
| ET | plus_raw_snr_ratio | 0.782 | 0.8877 | 0.921 | 0.985 | 0.997 | 0.999 | 1 |  |
| ET | plus_amp_time_2d_lr | 0.78 | 0.8833 | 0.9187 | 0.9862 | 0.9973 | 0.9995 | 1 |  |
| LIGO | waveform_plus_time_lr_plus_sky_log_overlap | 0.3782 | 0.6048 | 0.6718 | 0.8382 | 0.9487 | 0.9837 | 3 |  |
| LIGO | plus_raw_snr_ratio | 0.3853 | 0.6075 | 0.6667 | 0.8287 | 0.9353 | 0.9735 | 3 |  |
| LIGO | plus_amp_time_2d_lr | 0.3777 | 0.607 | 0.6772 | 0.8312 | 0.9438 | 0.9818 | 3 |  |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | SIS | waveform_plus_time_lr_plus_sky_log_overlap | 0.6647 | 0.808 | 0.86 | 0.973 | 1 |
| ET | PM | waveform_plus_time_lr_plus_sky_log_overlap | 0.8953 | 0.9587 | 0.9773 | 0.9993 | 1 |
| ET | SIS | plus_raw_snr_ratio | 0.676 | 0.8213 | 0.8667 | 0.972 | 1 |
| ET | PM | plus_raw_snr_ratio | 0.888 | 0.954 | 0.9753 | 0.998 | 1 |
| ET | SIS | plus_amp_time_2d_lr | 0.6647 | 0.808 | 0.86 | 0.973 | 1 |
| ET | PM | plus_amp_time_2d_lr | 0.8953 | 0.9587 | 0.9773 | 0.9993 | 1 |
| LIGO | SIS | waveform_plus_time_lr_plus_sky_log_overlap | 0.1303 | 0.2953 | 0.3797 | 0.6763 | 26 |
| LIGO | PM | waveform_plus_time_lr_plus_sky_log_overlap | 0.626 | 0.9143 | 0.964 | 1 | 1 |
| LIGO | SIS | plus_raw_snr_ratio | 0.1177 | 0.2713 | 0.3533 | 0.6573 | 30.5 |
| LIGO | PM | plus_raw_snr_ratio | 0.653 | 0.9437 | 0.98 | 1 | 1 |
| LIGO | SIS | plus_amp_time_2d_lr | 0.1173 | 0.2793 | 0.3727 | 0.6623 | 28 |
| LIGO | PM | plus_amp_time_2d_lr | 0.638 | 0.9347 | 0.9817 | 1 | 1 |

## Liao prior 诊断

| detector | liao_label | liao_delay_count | liao_delay_median_days | liao_delay_p90_days | random_delay_median_days |
| --- | ---: | ---: | ---: | ---: | ---: |
| ET | GW-LMC ET BBH Any_Detected_SNR8 | 4388 |  |  |  |
| LIGO | GW-LMC 2.5PLUS BBH Any_Detected_SNR1 | 4498 |  |  |  |