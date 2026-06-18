# Stage2b PDF 原始空间/时间赋权 baseline

生成时间：2026-06-15

## 实验目的

本阶段专门测试 `透镜识别流程.pdf` 第三部分“后续处理”中的原始赋权思路，作为 naive baseline：

- 空间位置赋权：按探测器数量给一个硬面积阈值，阈值内权重 1，否则 0。
- 时间差赋权：用 Liao / GW-LMC time-delay prior 对照。

注意：该阶段不是当前推荐主方法。推荐主方法仍是 Stage3 `waveform + Liao time LR + observed sky step`。

## PDF 规则映射

| detector | PDF detector-count mapping | area threshold | implementation |
|---|---:|---:|---|
| ET | 1 detector | 5000 deg2 | observed center angular area `pi theta^2 <= 5000` |
| LIGO | 2 detectors | 500 deg2 | observed center angular area `pi theta^2 <= 500` |

这里仍然不直接使用 true sky 做 pair feature；先生成 `ra_obs/dec_obs/sky_area90`，再对 observed center 计算硬阈值 mask。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Median rank | lambda_sky | lambda_time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET3 | pdf_sky_hard_mask_only | 1 | 1 | 1 | 1 | 1 |  |  |
| ET3 | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.972 | 0.9953 | 0.997 | 1 | 1 | 1 | 1 |
| ET3 | waveform_plus_pdf_sky_hard_mask_val_selected | 0.8968 | 0.9755 | 0.9852 | 0.9977 | 1 | 1 |  |
| ET3 | waveform_plus_liao_time_lr_val_selected | 0.83 | 0.931 | 0.9597 | 0.9918 | 1 |  | 1 |
| ET3 | liao_time_lr_only | 0.1297 | 0.404 | 0.5308 | 0.683 | 9 |  |  |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET3 | PM | pdf_sky_hard_mask_only | 1 | 1 | 1 | 1 | 1 |
| ET3 | PM | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.9893 | 0.9993 | 0.9997 | 1 | 1 |
| ET3 | PM | waveform_plus_liao_time_lr_val_selected | 0.94 | 0.9797 | 0.9863 | 0.9983 | 1 |
| ET3 | PM | waveform_plus_pdf_sky_hard_mask_val_selected | 0.8693 | 0.9643 | 0.9783 | 0.9977 | 1 |
| ET3 | PM | liao_time_lr_only | 0.2473 | 0.751 | 0.9507 | 1 | 3 |
| ET3 | SIS | pdf_sky_hard_mask_only | 1 | 1 | 1 | 1 | 1 |
| ET3 | SIS | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.9547 | 0.9913 | 0.9943 | 1 | 1 |
| ET3 | SIS | waveform_plus_pdf_sky_hard_mask_val_selected | 0.9243 | 0.9867 | 0.992 | 0.9977 | 1 |
| ET3 | SIS | waveform_plus_liao_time_lr_val_selected | 0.72 | 0.8823 | 0.933 | 0.9853 | 1 |
| ET3 | SIS | liao_time_lr_only | 0.012 | 0.057 | 0.111 | 0.366 | 172 |

## 初步解读

- PDF 原始空间规则是硬 mask，不能区分阈值内 pair 的 posterior 重叠强弱。
- 当前 realistic sky step 使用 `d_sky = theta / sqrt(sigma_i^2 + sigma_j^2)`，会考虑每个事件自身定位误差，因此物理上更合理。
- 如果 PDF hard mask 明显弱于 Stage3，说明后处理需要从固定面积阈值升级为 posterior-aware sky weighting。