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
| ET | pdf_sky_hard_mask_only | 1 | 1 | 1 | 1 | 1 |  |  |
| ET | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.7648 | 0.8808 | 0.919 | 0.9907 | 1 | 2 | 1 |
| ET | waveform_plus_liao_time_lr_val_selected | 0.6112 | 0.7527 | 0.8015 | 0.9243 | 1 |  | 1 |
| ET | waveform_plus_pdf_sky_hard_mask_val_selected | 0.5078 | 0.6943 | 0.7548 | 0.8972 | 1 | 1 |  |
| ET | liao_time_lr_only | 0.1332 | 0.4085 | 0.5282 | 0.686 | 9 |  |  |
| LIGO | pdf_sky_hard_mask_only | 0.955 | 0.955 | 0.955 | 0.958 | 1 |  |  |
| LIGO | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.6268 | 0.7995 | 0.8637 | 0.9558 | 1 | 2 | 2 |
| LIGO | liao_time_lr_only | 0.1445 | 0.4127 | 0.5273 | 0.686 | 9 |  |  |
| LIGO | waveform_plus_liao_time_lr_val_selected | 0.1658 | 0.4112 | 0.5197 | 0.7093 | 9 |  | 4 |
| LIGO | waveform_plus_pdf_sky_hard_mask_val_selected | 0.081 | 0.2002 | 0.2855 | 0.7085 | 33 | 0.25 |  |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | PM | pdf_sky_hard_mask_only | 1 | 1 | 1 | 1 | 1 |
| ET | PM | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.8857 | 0.956 | 0.977 | 1 | 1 |
| ET | PM | liao_time_lr_only | 0.2527 | 0.7613 | 0.9477 | 1 | 3 |
| ET | PM | waveform_plus_liao_time_lr_val_selected | 0.7877 | 0.8803 | 0.908 | 0.9807 | 1 |
| ET | PM | waveform_plus_pdf_sky_hard_mask_val_selected | 0.449 | 0.647 | 0.7153 | 0.8693 | 2 |
| ET | SIS | pdf_sky_hard_mask_only | 1 | 1 | 1 | 1 | 1 |
| ET | SIS | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.644 | 0.8057 | 0.861 | 0.9813 | 1 |
| ET | SIS | waveform_plus_pdf_sky_hard_mask_val_selected | 0.5667 | 0.7417 | 0.7943 | 0.925 | 1 |
| ET | SIS | waveform_plus_liao_time_lr_val_selected | 0.4347 | 0.625 | 0.695 | 0.868 | 2 |
| ET | SIS | liao_time_lr_only | 0.0137 | 0.0557 | 0.1087 | 0.372 | 172 |
| LIGO | PM | pdf_sky_hard_mask_only | 0.944 | 0.944 | 0.944 | 0.948 | 1 |
| LIGO | PM | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.867 | 0.9427 | 0.944 | 0.9463 | 1 |
| LIGO | PM | liao_time_lr_only | 0.2777 | 0.7677 | 0.944 | 1 | 3 |
| LIGO | PM | waveform_plus_liao_time_lr_val_selected | 0.3057 | 0.731 | 0.8893 | 1 | 3 |
| LIGO | PM | waveform_plus_pdf_sky_hard_mask_val_selected | 0.065 | 0.1627 | 0.2363 | 0.6733 | 40 |
| LIGO | SIS | pdf_sky_hard_mask_only | 0.966 | 0.966 | 0.966 | 0.968 | 1 |
| LIGO | SIS | waveform_plus_pdf_sky_hard_mask_plus_liao_time_lr_val_selected | 0.3867 | 0.6563 | 0.7833 | 0.9653 | 3 |
| LIGO | SIS | waveform_plus_pdf_sky_hard_mask_val_selected | 0.097 | 0.2377 | 0.3347 | 0.7437 | 26 |
| LIGO | SIS | waveform_plus_liao_time_lr_val_selected | 0.026 | 0.0913 | 0.15 | 0.4187 | 144.5 |
| LIGO | SIS | liao_time_lr_only | 0.0113 | 0.0577 | 0.1107 | 0.372 | 176 |

## 初步解读

- PDF 原始空间规则是硬 mask，不能区分阈值内 pair 的 posterior 重叠强弱。
- 当前 realistic sky step 使用 `d_sky = theta / sqrt(sigma_i^2 + sigma_j^2)`，会考虑每个事件自身定位误差，因此物理上更合理。
- 如果 PDF hard mask 明显弱于 Stage3，说明后处理需要从固定面积阈值升级为 posterior-aware sky weighting。