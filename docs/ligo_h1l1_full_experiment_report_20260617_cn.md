# LIGO H1+L1 全量实验报告

生成时间：2026-06-17

## 1. 实验目的

本轮实验重新完整跑了一份 LIGO H1+L1 版本，用于检查和修正此前“LIGO 是双探测器 H1+L1，但 sky 获取仍像单探测器方案”的问题。

本轮目标：

- 确认 LIGO waveform 数据以双通道 H1+L1 进入模型；
- 确认 observed sky 使用 `LIGO_HL` 场景，而不是旧单探测器 sky 配置；
- 重新训练/评估 LIGO pure 和 noisy fresh50 full-catalog；
- 在 LIGO noisy 上完整运行 stage0-stage7；
- 对 waveform、time、observed sky、SNR/amplitude、rerank model 做同口径比较；
- 为后续和 ET3 三臂结果放在一起比较提供完整结果。

注意：当前 LIGO sky 方案已经不是单探测器配置，但仍是 **H1+L1 network-SNR A90 approximation**，不是真实 H1-L1 timing/antenna/HEALPix localization skymap。

## 2. 实验状态

本轮已经全部完成。

完成时间：

```text
full runner exited: 2026-06-17T11:08:21+08:00
stage7 exited:      2026-06-17T11:12:53+08:00
```

总耗时：

```text
6322.84 s
约 1.76 小时
```

主流程包括：

1. LIGO pure fresh50 full-catalog
2. LIGO noisy fresh50 full-catalog
3. LIGO noisy stage0-stage6
4. watcher 自动接 stage7 modality combinations

## 3. 数据与路径

结果目录：

```text
/root/autodl-tmp/gw-catalog/runs/ligo_h1l1_fresh50_full_catalog_20260617
/root/autodl-tmp/gw-catalog/runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617
```

日志：

```text
/root/autodl-tmp/gw-catalog/logs/ligo_h1l1_full_experiment_20260617.log
/root/autodl-tmp/gw-catalog/logs/ligo_h1l1_stage7_modality_combinations_20260617.log
```

关键输出：

```text
runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh50_full_catalog_summary.csv
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage0_baseline/stage0_baseline_summary.csv
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage1_liao_time_lr/stage1_liao_time_lr_summary.csv
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage2_observed_sky/stage2_observed_sky_summary.csv
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage3_liao_time_plus_observed_sky/stage3_liao_time_plus_observed_sky_summary.csv
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage4_snr_amplitude_prior/stage4_snr_amplitude_prior_summary.csv
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage5_reranker_model_compare/stage5_reranker_model_compare_summary.csv
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage6_catalog_graph_discovery/stage6_catalog_graph_discovery_summary.csv
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage7_modality_combinations/stage7_modality_combinations_summary.csv
```

## 4. 双探测器输入确认

本轮运行前已确认 LIGO 数据以双通道进入模型：

```text
raw_l1_shape          = (10000, 2, 98304)
prepared_one_shape    = (2, 4096)
prepared_channel_count = 2
```

即：

```text
channel 0 -> H1
channel 1 -> L1
```

模型输入不是单通道，也不是把 H1/L1 合并成一条 waveform，而是保留两个 detector channel。

## 5. observed sky 配置

当前 LIGO 使用：

```text
scenario: LIGO_HL
label: LIGO H1+L1 network A90 approximation
snr_for_sky: network
sky_sampling: tangent_2d_gaussian
a90_ref_deg2: 100
```

stage2 sky diagnostics：

| 项目 | 值 |
|---|---|
| detector | LIGO |
| scenario | `LIGO_HL` |
| sky model | `detector_dependent_A90_approximation` |
| sampling | `tangent_2d_gaussian` |
| SNR mode | network |
| uses_h1l1_timing | False |
| uses_antenna_pattern_localization | False |
| uses_healpix_skymap | False |
| A90 ref | 100 deg2 |
| test A90 median | 399.20 deg2 |
| test A90 p90 | 500.00 deg2 |
| median sigma | 0.09168 rad, 约 5.25 deg |

解释：

- 当前已经使用 H1+L1 network SNR 生成 sky uncertainty；
- 但未使用真实 H1-L1 到达时间差、antenna pattern 或 HEALPix skymap；
- LIGO noisy 的 A90 明显大于 ET3，median 约 399 deg2，p90 触达 500 deg2 上限；
- 因此 LIGO observed sky 约束比 ET3 宽很多。

## 6. Catalog 与指标

full-catalog test 设置：

| 项目 | 数量 |
|---|---:|
| catalog total | 9000 |
| valid lensed query | 6000 |
| SIS lensed images | 3000 |
| SIS unlensed | 1500 |
| PM lensed images | 3000 |
| PM unlensed | 1500 |
| total lensed images | 6000 |
| total unlensed | 3000 |

主要指标：

| 指标 | 含义 |
|---|---|
| R@1 | 正确伴随像排第 1 的比例 |
| R@5 | 正确伴随像进入前 5 的比例 |
| R@10 | 正确伴随像进入前 10 的比例 |
| Top1% | 正确伴随像进入 catalog 前 1% 候选的比例 |
| median rank | 正确伴随像中位排名 |

## 7. Fresh50 full-catalog 结果

### 7.1 LIGO pure

pure 代表理想/无噪声 waveform 条件。

| variant | R@1 | R@5 | R@10 | Top1% | median rank |
|---|---:|---:|---:|---:|---:|
| waveform only | 0.9568 | 0.9818 | 0.9898 | 0.9965 | 1 |
| time only | 0.1365 | 0.4117 | 0.5308 | 0.6778 | 9 |
| predicted sky overlap only | 0.0152 | 0.0588 | 0.1085 | 0.4475 | 115 |
| waveform + time | 0.9017 | 0.9658 | 0.9880 | 0.9978 | 1 |
| waveform + predicted sky overlap | 0.8893 | 0.9415 | 0.9683 | 0.9957 | 1 |
| waveform + time + predicted sky overlap | 0.9197 | 0.9738 | 0.9890 | 0.9975 | 1 |
| true sky overlap only | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |

pure 下 waveform encoder 表现很强，说明双通道模型结构和数据读取本身没有问题。

### 7.2 LIGO noisy

noisy 是当前更重要的真实场景。

| variant | R@1 | R@5 | R@10 | Top1% | median rank |
|---|---:|---:|---:|---:|---:|
| waveform only | 0.0040 | 0.0145 | 0.0235 | 0.0900 | 2431 |
| time only | 0.1365 | 0.4117 | 0.5308 | 0.6778 | 9 |
| predicted sky overlap only | 0.0003 | 0.0010 | 0.0015 | 0.0137 | 4184.5 |
| waveform + time | 0.0568 | 0.0932 | 0.1373 | 0.4352 | 138 |
| waveform + predicted sky overlap | 0.0033 | 0.0097 | 0.0163 | 0.0915 | 2549.5 |
| waveform + time + predicted sky overlap | 0.0450 | 0.0868 | 0.1283 | 0.4468 | 124 |
| waveform + true sky overlap | 0.2180 | 0.4395 | 0.6167 | 1.0000 | 7 |
| waveform + time + true sky overlap | 0.6103 | 0.8210 | 0.9310 | 1.0000 | 1 |

结论：

- LIGO noisy 下 waveform-only 几乎失效，R@10 只有 0.0235；
- time-only 明显强于 waveform-only；
- waveform-predicted sky 在 noisy LIGO 中不可靠；
- true sky 结果只是上界/泄漏对照，不能作为主结果。

## 8. Stage0 baseline

Stage0 只比较 waveform、raw time、waveform + raw time。

| variant | R@1 | R@5 | R@10 | Top1% | median rank | lambda |
|---|---:|---:|---:|---:|---:|---:|
| waveform only | 0.0040 | 0.0145 | 0.0235 | 0.0900 | 2431 | - |
| raw time only | 0.1365 | 0.4117 | 0.5308 | 0.6778 | 9 | - |
| waveform + raw time | 0.1893 | 0.4190 | 0.5293 | 0.7005 | 9 | 4.0 |

raw time 是 LIGO noisy 中很重要的基础信号，远强于 waveform-only。

## 9. Stage1 Liao time prior

Liao/GW-LMC time prior 使用：

```text
GW-LMC 2.5PLUS BBH Any_Detected_SNR1
detected pair delay count = 4498
median delay = 32.3848 days
p90 delay = 269.5018 days
random delay median = 1087.2168 days
```

结果：

| variant | R@1 | R@5 | R@10 | Top1% | median rank | lambda |
|---|---:|---:|---:|---:|---:|---:|
| Liao time step only | 0.5253 | 0.5253 | 0.5253 | 0.5267 | 1 | - |
| Liao time LR only | 0.1445 | 0.4127 | 0.5273 | 0.6860 | 9 | - |
| waveform + Liao time step | 0.0078 | 0.0290 | 0.0417 | 0.1455 | 1671.5 | 0.25 |
| waveform + Liao time LR | 0.1705 | 0.4072 | 0.5167 | 0.7118 | 9 | 4.0 |

结论：

- time step only 的 R@1 很高，但 R@5/R@10 不增长，说明它更像硬规则分组；
- time LR 更接近连续排序；
- waveform 与 time step 简单融合会被弱 waveform 干扰；
- waveform + time LR 与 raw time 结果接近。

## 10. Stage2 observed sky

当前 LIGO observed sky 是 H1+L1 network A90 近似，A90 较宽。

| variant | R@1 | R@5 | R@10 | Top1% | median rank | lambda |
|---|---:|---:|---:|---:|---:|---:|
| observed sky step only | 0.5113 | 0.5113 | 0.5113 | 0.9325 | 1 | - |
| observed sky log overlap only | 0.1267 | 0.2762 | 0.3672 | 0.8317 | 24 | - |
| A90=50 step | 0.1497 | 0.2712 | 0.3543 | 0.6507 | 28 | 0.25 |
| waveform + observed sky step | 0.1382 | 0.2552 | 0.3175 | 0.5767 | 45 | 0.25 |
| A90=100 step | 0.1412 | 0.2507 | 0.3152 | 0.5730 | 46 | 0.25 |
| A90=200 step | 0.1153 | 0.2265 | 0.2827 | 0.5227 | 71 | 0.25 |
| waveform + observed sky log overlap | 0.0652 | 0.1310 | 0.1688 | 0.3298 | 290 | 4.0 |

结论：

- observed sky step only 有较强 Top1% 和 R@1；
- log-overlap 更平滑，但精排较弱；
- 与 waveform 简单融合会下降，原因是 LIGO noisy waveform score 太弱且标定不一致；
- A90 更小的 sweep 在 R@10 上更好，但仍低于 step-only。

## 11. Stage3 time + observed sky

Stage3 融合 waveform + Liao time LR + observed sky。

| variant | R@1 | R@5 | R@10 | Top1% | median rank | lambda time | lambda sky |
|---|---:|---:|---:|---:|---:|---:|---:|
| waveform + Liao time LR + observed sky step | 0.5117 | 0.7645 | 0.8465 | 0.9770 | 1 | 4.0 | 2.0 |
| waveform + Liao time LR + observed sky log overlap | 0.3653 | 0.5953 | 0.6667 | 0.8367 | 3 | 2.0 | 4.0 |

结论：

- time + sky 明显互补；
- step 形式仍优于 log-overlap；
- Stage3 已经把 R@10 提升到 0.8465，是物理解释较清楚的强方案。

## 12. Stage4 SNR/amplitude prior

Stage4 在 time LR + sky log-overlap 基础上加入 SNR/amplitude。

| variant | R@1 | R@5 | R@10 | Top1% | median rank | lambda time | lambda sky | lambda extra |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| waveform + time LR + sky log-overlap | 0.3667 | 0.5947 | 0.6652 | 0.8385 | 3 | 2.0 | 4.0 | - |
| plus raw SNR ratio | 0.4105 | 0.6145 | 0.6835 | 0.8608 | 2 | 2.0 | 4.0 | 1.0 |
| plus amp-time 2D LR | 0.3683 | 0.6017 | 0.6685 | 0.8335 | 3 | 2.0 | 4.0 | 0.25 |

结论：

- raw SNR ratio 有小幅提升；
- amp-time 2D LR 提升有限；
- 因为 Stage4 使用 log-overlap 主线，所以不如 Stage3 的 step 主线强。

## 13. Stage5 reranker model compare

Stage5 对比 weighted sum 和 learned tabular reranker。

| variant | R@1 | R@5 | R@10 | Top1% | median rank |
|---|---:|---:|---:|---:|---:|
| weighted sum val-selected extensible | 0.5455 | 0.7495 | 0.8137 | 0.9630 | 1 |
| LightGBM | 0.4607 | 0.7013 | 0.7522 | 0.8947 | 2 |
| HGB | 0.3117 | 0.5413 | 0.6748 | 0.9392 | 4 |
| weighted sum stage4 lambdas | 0.3687 | 0.6015 | 0.6687 | 0.8338 | 3 |
| MLP tabular | 0.4473 | 0.6090 | 0.6683 | 0.8577 | 2 |
| logistic regression | 0.0815 | 0.0833 | 0.0928 | 0.2072 | 923 |

当前 LIGO noisy 的最佳 Stage5 方案：

```text
weighted_sum_val_selected_extensible
R@1  = 0.5455
R@10 = 0.8137
Top1% = 0.9630
```

对应权重：

| feature | lambda |
|---|---:|
| liao_time_lr | 1.0 |
| sky_log_overlap | 4.0 |
| amp_time_lr | 0.25 |
| sky_norm_sep | 4.0 |
| waveform reciprocal rank | 0.0 |
| waveform margin | 0.0 |

注意：当前最佳 weighted sum 自动把 waveform rank/margin 权重选为 0，说明 LIGO noisy 的 waveform score 对本轮 rerank 帮助很弱。

## 14. Stage6 graph discovery

Stage6 把 pair score 转成 catalog graph，用于后续候选系统发现。

| scorer | topk edges | system recall | system precision | mean purity | mean component size |
|---|---:|---:|---:|---:|---:|
| waveform only | 1 | 0.0087 | 0.0097 | 0.6573 | 3.20 |
| waveform only | 2 | 0.8123 | 0.0122 | 0.5056 | 100.35 |
| waveform only | 5 | 0.9667 | 1.0000 | 0.6693 | 8815.00 |
| weighted sum best features | 1 | 0.4025 | 0.4293 | 0.7076 | 2.94 |
| weighted sum best features | 2 | 0.7913 | 0.7650 | 0.6398 | 46.89 |
| weighted sum best features | 5 | 0.9990 | 1.0000 | 0.6705 | 8943.00 |
| HGB | 1 | 0.2114 | 0.3227 | 0.7020 | 4.12 |
| HGB | 2 | 0.8743 | 0.3000 | 0.4816 | 404.55 |
| HGB | 5 | 0.9607 | 1.0000 | 0.6749 | 8716.00 |

结论：

- weighted sum best features 在 top1/top2 边上明显优于 waveform-only；
- top5 会形成过大的连通分量，后续图发现需要更细的边阈值或 component pruning；
- graph discovery 可作为后续误报分析方向。

## 15. Stage7 modality combinations

Stage7 专门比较只靠 waveform、只靠 time、只靠 sky，以及各种组合。

### 15.1 Overall 排名

| variant | R@1 | R@5 | R@10 | Top1% | median rank | weights |
|---|---:|---:|---:|---:|---:|---|
| waveform + Liao time LR + observed sky step | 0.5250 | 0.7753 | 0.8537 | 0.9763 | 1 | time=4, sky_step=2 |
| Liao time LR + observed sky step | 0.5045 | 0.7537 | 0.8470 | 0.9757 | 1 | time=0.5, sky_step=2 |
| waveform + raw time + observed sky step | 0.6008 | 0.7952 | 0.8423 | 0.9648 | 1 | raw_time=1, sky_step=2 |
| raw time + observed sky step | 0.5862 | 0.7830 | 0.8328 | 0.9647 | 1 | raw_time=1, sky_step=2 |
| Liao time LR + observed sky log-overlap | 0.5613 | 0.7203 | 0.7745 | 0.9475 | 1 | time=0.25, log=4 |
| raw time + observed sky log-overlap | 0.5538 | 0.6742 | 0.7278 | 0.9502 | 1 | raw_time=0.25, log=4 |
| raw time only | 0.1365 | 0.4117 | 0.5308 | 0.6778 | 9 | - |
| waveform + raw time | 0.1893 | 0.4190 | 0.5293 | 0.7005 | 9 | raw_time=4 |
| Liao time LR only | 0.1445 | 0.4127 | 0.5273 | 0.6860 | 9 | - |
| observed sky step only | 0.5120 | 0.5120 | 0.5120 | 0.9337 | 1 | - |
| waveform only | 0.0040 | 0.0145 | 0.0235 | 0.0900 | 2431 | - |

Stage7 结论：

- 最强 R@10 来自 time + observed sky step；
- waveform 在 LIGO noisy 下贡献很弱，加入后不一定稳定提升；
- raw time 与 Liao time 表现相近；
- observed sky step 是关键空间特征；
- log-overlap 有一定 Top1% 能力，但精排不如 step。

### 15.2 SIS / PM 分解

| variant | subset | R@1 | R@5 | R@10 | Top1% | median rank |
|---|---|---:|---:|---:|---:|---:|
| waveform only | SIS | 0.0043 | 0.0150 | 0.0257 | 0.1033 | 2026 |
| waveform only | PM | 0.0037 | 0.0140 | 0.0213 | 0.0767 | 2875 |
| raw time only | SIS | 0.0093 | 0.0530 | 0.1027 | 0.3557 | 188 |
| raw time only | PM | 0.2637 | 0.7703 | 0.9590 | 1.0000 | 3 |
| Liao time LR only | SIS | 0.0113 | 0.0577 | 0.1107 | 0.3720 | 176 |
| Liao time LR only | PM | 0.2777 | 0.7677 | 0.9440 | 1.0000 | 3 |
| observed sky step only | SIS | 0.5047 | 0.5047 | 0.5047 | 0.9347 | 1 |
| observed sky step only | PM | 0.5193 | 0.5193 | 0.5193 | 0.9327 | 1 |
| waveform + raw time | SIS | 0.0330 | 0.0853 | 0.1270 | 0.4010 | 156.5 |
| waveform + raw time | PM | 0.3457 | 0.7527 | 0.9317 | 1.0000 | 3 |
| waveform + raw time + observed sky step | SIS | 0.3360 | 0.5963 | 0.6867 | 0.9297 | 3 |
| waveform + raw time + observed sky step | PM | 0.8657 | 0.9940 | 0.9980 | 1.0000 | 1 |
| waveform + Liao time LR + observed sky step | SIS | 0.3093 | 0.6030 | 0.7223 | 0.9527 | 4 |
| waveform + Liao time LR + observed sky step | PM | 0.7407 | 0.9477 | 0.9850 | 1.0000 | 1 |

分解结论：

- PM 对时间信息极敏感，time-only 的 PM R@10 接近 0.95；
- SIS 对时间信息很弱，time-only 的 SIS R@10 只有约 0.10-0.11；
- observed sky step 对 SIS 和 PM 都有约 0.51 的 R@1，且 Top1% 很高；
- 最强组合主要由 time + sky 支撑，PM 远强于 SIS；
- LIGO noisy 的主要短板是 waveform 信号太弱，SIS 的精排也明显更难。

## 16. 当前最佳真实可用方案

按 R@10：

```text
Stage7 waveform + Liao time LR + observed sky step
R@1  = 0.5250
R@10 = 0.8537
Top1% = 0.9763
```

按可拓展 rerank 模块：

```text
Stage5 weighted_sum_val_selected_extensible
R@1  = 0.5455
R@10 = 0.8137
Top1% = 0.9630
```

建议表述：

- 如果强调最高 R@10，用 Stage7 的 `waveform + Liao time LR + observed sky step`；
- 如果强调统一可拓展 rerank 框架，用 Stage5 的 `weighted_sum_val_selected_extensible`；
- 两者都说明当前 LIGO noisy 的有效信息主要来自 time + observed sky，而不是 waveform。

## 17. 与 ET3 的主要差异

| 项目 | ET3 noisy | LIGO H1+L1 noisy |
|---|---:|---:|
| waveform-only R@10 | 0.8542 | 0.0235 |
| observed sky step-only R@10 | 0.9407 | 0.5113 |
| best Stage5 R@1 | 0.9840 | 0.5455 |
| best Stage5 R@10 | 0.9985 | 0.8137 |
| observed sky A90 median | 20 deg2 | 399 deg2 |
| input channels | 3 | 2 |
| sky scenario | ET_TRIANGLE | LIGO_HL |

解释：

- ET3 三臂数据的 waveform 和 sky 信息都明显更强；
- LIGO noisy waveform 在当前配置下几乎不能单独检索；
- LIGO sky A90 大很多，空间约束更宽；
- LIGO 结果更依赖 time + observed sky step；
- 当前 LIGO_HL 仍是 network A90 近似，不是真实 H1-L1 skymap，后续还有改进空间。

## 18. 问题与风险

当前 LIGO 结果有几个需要明确的问题：

1. LIGO noisy waveform-only 异常弱  
   R@10 只有 0.0235，和 pure 下 0.9898 差距极大。需要后续检查 noisy 数据强度、预处理、模型容量、训练目标和 H1/L1 通道归一化。

2. waveform 与辅助分数标定不一致  
   多个融合实验中，加入 waveform 后反而不稳定，Stage5 也把 waveform rank/margin 权重选为 0。

3. observed sky 不是真实 skymap  
   当前只是 H1+L1 network-SNR A90 approximation，未使用真实双站时间差、antenna pattern 或 HEALPix posterior。

4. LIGO sky A90 触达上限  
   p90 为 500 deg2，说明空间误差较宽，且 clip 上限影响明显。

5. SIS 比 PM 更难  
   time prior 对 PM 很强，但对 SIS 很弱；SIS 需要更依赖 waveform 或更真实 sky/amp prior。

## 19. 后续建议

建议按以下顺序推进：

1. 复查 LIGO noisy waveform pipeline  
   重点检查 H1/L1 两通道预处理、SNR 分布、噪声注入、bandpass、标准化、训练 loss 和 hard negative。

2. 引入真实 H1-L1 localization 特征  
   至少加入双站 arrival-time delay、antenna response、相对相位/振幅，再逐步升级到 toy HEALPix skymap。

3. 对 LIGO sky A90 做 sweep  
   当前 median 399 deg2，p90 500 deg2；建议测试更保守/更乐观 A90 和 clip 设置。

4. family-aware rerank  
   PM 和 SIS 对 time/sky/waveform 的依赖差异很大，可尝试 family-aware 或 mixture-of-experts reranker。

5. 加强 SIS 检索  
   SIS 是当前 LIGO noisy 的主要短板，需要增强 waveform 或 sky 约束。

6. 汇总 ET3 vs LIGO 对比报告  
   当前 ET3 和 LIGO 都已完整跑完，下一步可以做统一对比表和结论。

## 20. 结论

本轮 LIGO H1+L1 全量实验已经完整完成，代码确认使用双通道 waveform 输入，并使用 `LIGO_HL` observed sky 场景。

核心结论：

- LIGO pure 下 waveform encoder 有效；
- LIGO noisy 下 waveform-only 很弱；
- time prior 和 observed sky step 是主要有效信号；
- time + observed sky step 可以把 R@10 提升到约 0.85；
- Stage5 可拓展 weighted rerank 达到 R@1=0.5455、R@10=0.8137；
- Stage7 的 `waveform + Liao time LR + observed sky step` 达到 R@10=0.8537；
- 当前 LIGO sky 不是单探测器方案，但仍不是真实 H1-L1 skymap；
- 后续重点应放在 LIGO noisy waveform 修复和真实 H1-L1 localization 建模。

## 21. 复现命令

本轮完整 LIGO 实验由新 runner 启动：

```bash
cd /root/autodl-tmp/gw-catalog
/root/miniconda3/bin/python scripts/experiments/92_ligo_h1l1_full_experiment_runner.py --phase all
```

分阶段运行方式：

```bash
# 只跑 pure/noisy fresh50 full-catalog
/root/miniconda3/bin/python scripts/experiments/92_ligo_h1l1_full_experiment_runner.py --phase fresh

# 只跑 stage0-stage3
/root/miniconda3/bin/python scripts/experiments/92_ligo_h1l1_full_experiment_runner.py --phase p0

# 只跑 PDF hard-mask baseline
/root/miniconda3/bin/python scripts/experiments/92_ligo_h1l1_full_experiment_runner.py --phase pdf

# 只跑 stage4-stage6
/root/miniconda3/bin/python scripts/experiments/92_ligo_h1l1_full_experiment_runner.py --phase p1p2
```

Stage7 单独入口：

```bash
cd /root/autodl-tmp/gw-catalog
/root/miniconda3/bin/python scripts/experiments/93_ligo_h1l1_modality_combinations.py
```

本轮使用 watcher 自动在 full runner 结束后启动 stage7：

```bash
scripts/experiments/run_ligo_h1l1_stage7_watch.sh
```

## 22. 结果文件完整清单

主 manifest：

```text
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/ligo_h1l1_run_outputs_manifest.csv
```

manifest 中记录的 summary：

| 文件 | 行数 | 说明 |
|---|---:|---|
| `runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh50_full_catalog_summary.csv` | 72 | pure + noisy fresh50 总表 |
| `runs/ligo_h1l1_fresh50_full_catalog_20260617/ligo_pure_full_catalog/fresh50_full_catalog_summary.csv` | 36 | pure full-catalog |
| `runs/ligo_h1l1_fresh50_full_catalog_20260617/ligo_noisy_full_catalog/fresh50_full_catalog_summary.csv` | 36 | noisy full-catalog |
| `stage0_baseline_summary.csv` | 12 | waveform/raw time baseline |
| `stage1_liao_time_lr_summary.csv` | 16 | Liao time prior |
| `stage2_observed_sky_summary.csv` | 40 | observed sky + A90 sweep |
| `stage2b_pdf_rule_time_sky_baseline_summary.csv` | - | PDF hard-mask baseline |
| `stage3_liao_time_plus_observed_sky_summary.csv` | 8 | time + observed sky |
| `stage4_snr_amplitude_prior_summary.csv` | 12 | SNR/amplitude prior |
| `stage5_reranker_model_compare_summary.csv` | 24 | weighted/learned reranker |
| `stage6_catalog_graph_discovery_summary.csv` | 9 | catalog graph discovery |
| `stage7_modality_combinations_summary.csv` | 68 | waveform/time/sky 全组合 |

模型和缓存：

```text
runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh_mixed_encoders/ligo_pure_mixed_sis_pm_ep50/model.pt
runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh_mixed_encoders/ligo_noisy_mixed_sis_pm_ep50/model.pt
runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh_mixed_encoders/ligo_*_mixed_sis_pm_ep50/train_embeddings.npy
runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh_mixed_encoders/ligo_*_mixed_sis_pm_ep50/val_embeddings.npy
runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh_mixed_encoders/ligo_*_mixed_sis_pm_ep50/test_embeddings.npy
runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh_mixed_encoders/ligo_*_mixed_sis_pm_ep50/val_scores.npy
runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh_mixed_encoders/ligo_*_mixed_sis_pm_ep50/test_scores.npy
```

Observed sky audit：

```text
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage2_observed_sky/LIGO_noisy_val_observed_sky_audit.csv
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage2_observed_sky/LIGO_noisy_test_observed_sky_audit.csv
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage2_observed_sky/observed_sky_diagnostics.csv
```

## 23. 实验配置细节

### 23.1 Runner 配置

本轮 runner 强制设置：

```text
fresh.OUT_ROOT    = runs/ligo_h1l1_fresh50_full_catalog_20260617
fresh.ENCODER_ROOT = runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh_mixed_encoders
fresh.JOBS        = [("LIGO", "pure"), ("LIGO", "noisy")]

liao.OUT_ROOT     = runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617
liao.ENCODER_ROOT = fresh.ENCODER_ROOT
liao.JOBS         = [("LIGO", "noisy")]
```

因此这次是独立新目录，不覆盖旧结果。

### 23.2 模型配置

| 项目 | 值 |
|---|---|
| detector | LIGO |
| data modes | pure / noisy |
| waveform channels | 2 |
| model input shape | `(2, 4096)` |
| backbone | `inceptiontime` |
| preprocess | `bandpass` |
| epochs | 50 |
| catalog kind | full-catalog |
| families | SIS + PM + unlensed |

### 23.3 训练耗时

从 fresh summary 读取：

| mode | train_s | mean_epoch_s |
|---|---:|---:|
| LIGO pure | 919.46 | 18.39 |
| LIGO noisy | 916.31 | 18.33 |

## 24. Stage2b PDF hard-mask baseline 说明

Stage2b 是为了对照本地 `透镜识别流程.pdf` 中“后续处理”的硬规则思想：对空间位置和时间差做 hard-mask / hard-weight，而不是完整 posterior overlap。

本轮 Stage2b 已跑完并落盘：

```text
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage2b_pdf_rule_time_sky_baseline/stage2b_pdf_rule_time_sky_baseline_summary.csv
```

它的作用不是替代主 rerank，而是回答：

- PDF 中的空间位置赋权、时间差赋权在当前 catalog-level 任务中是否有效；
- 硬阈值规则和 observed sky step/log-overlap 的行为是否一致；
- 是否存在规则过硬导致的精排失真。

后续整理 ET3/LIGO 总对比时，建议把 Stage2b 单独放在“规则 baseline”小节，不和 Stage5 主结果混为一类。

## 25. Stage7 完整组合解读

Stage7 的 17 个组合可以分成四类。

### 25.1 单项信号

| variant | R@1 | R@10 | Top1% | 结论 |
|---|---:|---:|---:|---|
| waveform only | 0.0040 | 0.0235 | 0.0900 | noisy waveform 基本失效 |
| raw time only | 0.1365 | 0.5308 | 0.6778 | 有效，主要来自 PM |
| Liao time LR only | 0.1445 | 0.5273 | 0.6860 | 与 raw time 接近 |
| observed sky step only | 0.5120 | 0.5120 | 0.9337 | Top1% 很强，精排像硬规则 |
| observed sky log-overlap only | 0.1333 | 0.3617 | 0.8353 | 粗筛有效，精排不如 step |

### 25.2 waveform + 单项辅助

| variant | R@1 | R@10 | Top1% | 结论 |
|---|---:|---:|---:|---|
| waveform + raw time | 0.1893 | 0.5293 | 0.7005 | 比 raw time R@1 高，但 R@10 相近 |
| waveform + Liao time LR | 0.1705 | 0.5167 | 0.7118 | 与 time-only 接近 |
| waveform + observed sky step | 0.1415 | 0.3115 | 0.5757 | 低于 sky step only，waveform 干扰 |
| waveform + observed sky log-overlap | 0.0640 | 0.1675 | 0.3298 | 明显不稳 |

### 25.3 time + sky，无 waveform

| variant | R@1 | R@10 | Top1% | 结论 |
|---|---:|---:|---:|---|
| raw time + observed sky step | 0.5862 | 0.8328 | 0.9647 | 强组合 |
| Liao time LR + observed sky step | 0.5045 | 0.8470 | 0.9757 | R@10 略高 |
| raw time + observed sky log-overlap | 0.5538 | 0.7278 | 0.9502 | 可用但低于 step |
| Liao time LR + observed sky log-overlap | 0.5613 | 0.7745 | 0.9475 | log-overlap 中较好 |

### 25.4 waveform + time + sky

| variant | R@1 | R@10 | Top1% | 结论 |
|---|---:|---:|---:|---|
| waveform + raw time + observed sky step | 0.6008 | 0.8423 | 0.9648 | R@1 最高 |
| waveform + Liao time LR + observed sky step | 0.5250 | 0.8537 | 0.9763 | R@10 最高 |
| waveform + raw time + observed sky log-overlap | 0.3707 | 0.6667 | 0.8548 | 低于 step |
| waveform + Liao time LR + observed sky log-overlap | 0.3652 | 0.6663 | 0.8373 | 低于 step |

Stage7 给出的最清楚结论是：LIGO noisy 中 `time + observed sky step` 是核心组合，waveform 不是主要贡献项。

## 26. SIS 与 PM 行为差异

### 26.1 PM

PM 对时间信息极强：

| variant | PM R@1 | PM R@10 | PM Top1% |
|---|---:|---:|---:|
| raw time only | 0.2637 | 0.9590 | 1.0000 |
| Liao time LR only | 0.2777 | 0.9440 | 1.0000 |
| waveform + raw time | 0.3457 | 0.9317 | 1.0000 |
| waveform + raw time + observed sky step | 0.8657 | 0.9980 | 1.0000 |
| waveform + Liao time LR + observed sky step | 0.7407 | 0.9850 | 1.0000 |

PM 结果说明：当前 PM 的时间延迟分布与背景随机时间差差异明显，所以 time prior 很强。

### 26.2 SIS

SIS 对时间信息弱：

| variant | SIS R@1 | SIS R@10 | SIS Top1% |
|---|---:|---:|---:|
| raw time only | 0.0093 | 0.1027 | 0.3557 |
| Liao time LR only | 0.0113 | 0.1107 | 0.3720 |
| observed sky step only | 0.5047 | 0.5047 | 0.9347 |
| waveform + raw time + observed sky step | 0.3360 | 0.6867 | 0.9297 |
| waveform + Liao time LR + observed sky step | 0.3093 | 0.7223 | 0.9527 |

SIS 的主要可用信号是 observed sky step，而不是 time。由于 waveform noisy 很弱，SIS 精排仍是当前 LIGO 的短板。

### 26.3 对模型设计的影响

后续 LIGO rerank 不宜对 SIS/PM 使用完全相同的权重：

- PM：time 权重可以更高；
- SIS：sky 权重更关键；
- waveform：需要先修复 noisy waveform 表征，否则不应在 rerank 中赋予过高权重；
- learned reranker 需要 family-aware 或 mixture-of-experts，否则容易被 PM 的强 time 信号主导。

## 27. 为什么 noisy waveform 弱需要单独排查

LIGO pure 和 noisy 的差距非常大：

| mode | waveform-only R@1 | waveform-only R@10 |
|---|---:|---:|
| pure | 0.9568 | 0.9898 |
| noisy | 0.0040 | 0.0235 |

这说明问题不是双通道模型无法学习，而更可能来自 noisy 数据或 noisy 训练设置。

建议排查项：

1. H1/L1 noisy strain 的 SNR 分布  
   检查 noisy waveform 是否低到模型无法识别。

2. 每通道标准化  
   确认 H1/L1 没有被错误 broadcast、错误 zscore 或通道顺序错位。

3. bandpass 和裁剪窗口  
   检查信号是否在裁剪窗口内，bandpass 是否对 LIGO 参数过强。

4. hard negative 采样  
   当前 hard negative 可能在 noisy 下太难或不稳定。

5. pure/noisy label 与 split 对齐  
   检查 noisy 的 L1/L2 是否和 meta/gt 正确对应。

6. H1/L1 单通道消融  
   分别训练 H1-only、L1-only、H1+L1，确认是某一通道问题还是双通道融合问题。

7. waveform 可视化与 embedding 分布  
   抽样看同源 pair 的 embedding cosine 是否显著高于随机 pair。

## 28. LIGO 与 ET3 的解释差异

ET3 和 LIGO 的差异不能只归因于 detector 数量，也和当前模拟方式有关。

### 28.1 waveform

ET3 noisy waveform-only R@10=0.8542，LIGO noisy waveform-only R@10=0.0235。说明 ET3 的三臂 noisy waveform 在当前生成/预处理下仍保留可学习同源特征，而 LIGO noisy 基本没有。

### 28.2 sky

ET3 observed sky median A90=20 deg2，LIGO median A90=399 deg2。LIGO sky posterior 更宽，所以 sky log-overlap 的精排能力较弱，但 step 仍能提供较强粗筛。

### 28.3 time

LIGO PM 的 time-only R@10 接近 0.95，说明 PM time-delay 与背景时间差区分很强。SIS time-only 很弱，说明需要 family-specific prior。

### 28.4 rerank

ET3 Stage5 R@10=0.9985，LIGO Stage5 R@10=0.8137。差距主要来自：

- LIGO waveform noisy 弱；
- LIGO sky A90 宽；
- LIGO SIS time prior 弱；
- 当前 LIGO sky 不是真实双站 localization。

## 29. 推荐后续实验矩阵

### 29.1 LIGO waveform 修复实验

| 实验 | 目的 |
|---|---|
| H1-only noisy | 检查 H1 单通道是否可学 |
| L1-only noisy | 检查 L1 单通道是否可学 |
| H1+L1 no bandpass | 检查 bandpass 是否损伤信号 |
| H1+L1 different crop | 检查窗口是否错过 merger |
| lower noise / higher SNR subset | 判断是否 SNR 太低 |
| larger encoder / longer training | 判断模型容量是否不足 |

### 29.2 LIGO sky 修复实验

| 实验 | 目的 |
|---|---|
| A90 ref sweep 50/100/200/500 | 检查 sky uncertainty 标定 |
| clip max sweep 300/500/1000 | 检查 A90 上限影响 |
| elliptical Gaussian | 替代圆形 posterior |
| H1-L1 time delay localization | 加入真实双站几何约束 |
| toy HEALPix posterior | 更接近真实 skymap overlap |

### 29.3 Rerank 修复实验

| 实验 | 目的 |
|---|---|
| family-aware weighted sum | SIS/PM 分开选权重 |
| PM/SIS independent reranker | 避免 PM time 信号主导 |
| calibrated waveform score | 修正 waveform 与 time/sky 标定不一致 |
| candidate prefilter + rerank | 先用 time/sky 缩小候选，再做 waveform |
| graph pruning | 防止 top5 形成巨大连通分量 |

## 30. 报告口径建议

对外汇报 LIGO 结果时建议这样表述：

```text
We reran the full LIGO H1+L1 experiment with two-channel waveform inputs and the LIGO_HL observed-sky scenario. The sky module now uses a network-SNR-dependent A90 approximation for H1+L1, rather than a single-detector sky configuration. In the noisy LIGO setting, waveform-only retrieval is weak, while time-delay and observed-sky step features dominate the useful signal. The best interpretable modality combination reaches R@10=0.8537, and the extensible validation-selected weighted reranker reaches R@1=0.5455 and R@10=0.8137. These results indicate that the H1+L1 rerank pipeline is functional, but the noisy waveform representation and the approximate sky-localization model need further improvement before LIGO can match the ET3 performance.
```

中文简述：

```text
本轮 LIGO H1+L1 已经完整跑通，并确认使用双通道输入和 LIGO_HL observed-sky 场景。结果显示 noisy LIGO 中 waveform-only 很弱，主要有效信息来自时间差和 observed sky step。当前最佳可解释组合 R@10 约 0.85，说明 rerank 流程有效，但后续必须重点修复 noisy waveform 表征，并将 H1+L1 sky 从 network A90 近似升级到更真实的双站 localization/skymap。
```
