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
| LIGO | pdf_sky_hard_mask_only | 0.8807 | 0.8807 | 0.8807 | 0.8883 | 1 |  |  |
| LIGO | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.5757 | 0.7308 | 0.7923 | 0.9233 | 1 | 1 | 4 |
| LIGO | liao_time_lr_only | 0.1445 | 0.4127 | 0.5273 | 0.686 | 9 |  |  |
| LIGO | waveform_plus_liao_time_lr_val_selected | 0.1705 | 0.4072 | 0.5167 | 0.7118 | 9 |  | 4 |
| LIGO | waveform_plus_pdf_sky_hard_mask_val_selected | 0.077 | 0.1995 | 0.279 | 0.811 | 35 | 0.5 |  |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | PM | liao_time_lr_only | 0.2777 | 0.7677 | 0.944 | 1 | 3 |
| LIGO | PM | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.8277 | 0.8983 | 0.933 | 0.9997 | 1 |
| LIGO | PM | waveform_plus_liao_time_lr_val_selected | 0.313 | 0.7253 | 0.884 | 1 | 3 |
| LIGO | PM | pdf_sky_hard_mask_only | 0.864 | 0.864 | 0.864 | 0.872 | 1 |
| LIGO | PM | waveform_plus_pdf_sky_hard_mask_val_selected | 0.0687 | 0.1703 | 0.234 | 0.797 | 43 |
| LIGO | SIS | pdf_sky_hard_mask_only | 0.8973 | 0.8973 | 0.8973 | 0.9047 | 1 |
| LIGO | SIS | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.3237 | 0.5633 | 0.6517 | 0.847 | 4 |
| LIGO | SIS | waveform_plus_pdf_sky_hard_mask_val_selected | 0.0853 | 0.2287 | 0.324 | 0.825 | 28 |
| LIGO | SIS | waveform_plus_liao_time_lr_val_selected | 0.028 | 0.089 | 0.1493 | 0.4237 | 144 |
| LIGO | SIS | liao_time_lr_only | 0.0113 | 0.0577 | 0.1107 | 0.372 | 176 |

## 初步解读

- PDF 原始空间规则是硬 mask，不能区分阈值内 pair 的 posterior 重叠强弱。
- 当前 realistic sky step 使用 `d_sky = theta / sqrt(sigma_i^2 + sigma_j^2)`，会考虑每个事件自身定位误差，因此物理上更合理。
- 如果 PDF hard mask 明显弱于 Stage3，说明后处理需要从固定面积阈值升级为 posterior-aware sky weighting。