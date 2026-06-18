# stage0_baseline 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage0_baseline` |
| 结果 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage0_baseline/stage0_baseline_summary.csv` |

## 实验说明

- Stage0 只使用当前数据自身的 waveform similarity 与 raw trigger_time_obs 时间差。
- 该阶段不使用 GW-LMC/Liao prior、不使用 observed sky、不使用 SNR ratio。
- waveform_plus_raw_time 的 lambda 在 validation full catalog 上选择，然后应用到 test full catalog。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank | lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | waveform_only | 0.004 | 0.0145 | 0.0235 | 0.09 | 0.2163 | 0.3053 | 2431 |  |
| LIGO | raw_time_only | 0.1365 | 0.4117 | 0.5308 | 0.6778 | 0.8387 | 0.9093 | 9 |  |
| LIGO | waveform_plus_raw_time_val_selected | 0.1893 | 0.419 | 0.5293 | 0.7005 | 0.8525 | 0.9178 | 9 | 4 |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | SIS | waveform_only | 0.0043 | 0.015 | 0.0257 | 0.1033 | 2026 |
| LIGO | PM | waveform_only | 0.0037 | 0.014 | 0.0213 | 0.0767 | 2875 |
| LIGO | SIS | raw_time_only | 0.0093 | 0.053 | 0.1027 | 0.3557 | 188 |
| LIGO | PM | raw_time_only | 0.2637 | 0.7703 | 0.959 | 1 | 3 |
| LIGO | SIS | waveform_plus_raw_time_val_selected | 0.033 | 0.0853 | 0.127 | 0.401 | 156.5 |
| LIGO | PM | waveform_plus_raw_time_val_selected | 0.3457 | 0.7527 | 0.9317 | 1 | 3 |