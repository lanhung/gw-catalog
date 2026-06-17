# GWTC 真实事件 non-lensed case study

## 目的

该实验使用真实 GWTC 事件作为非透镜 sanity check：选择两例不同的已知真实事件，按当前 LIGO H1+L1 waveform encoder 跑完整输入预处理和 embedding 打分，验证 pipeline 能处理真实 strain，并且给出低于模拟透镜正样本的分数。

本 case study 不用于训练，也不声称真实事件存在透镜关系。它只作为 reviewer/NC 可能要求的 real-event demonstration。

## 事件

- Events: `GW150914`, `GW151226`, `GW170817`
- Case pairs: `GW150914-GW151226`, `GW150914-GW170817`
- Catalog: `GWTC-1-confident`
- Detectors: H1 + L1
- Strain: GWOSC 4 kHz, 32 s HDF5

## 结果

| pair | waveform_score | waveform_pos_pct | waveform_neg_pct | delta_t_days | liao_time_lr | time_lr_pos_pct | time_lr_neg_pct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GW150914 vs GW151226 | 1.0000 | 100.0000 | 100.0000 | 102.7418 | 1.3230 | 17.7667 | 95.5540 |
| GW150914 vs GW170817 | 1.0000 | 100.0000 | 100.0000 | 703.1183 | -2.5283 | 0.4000 | 57.6680 |

解释：`*_pos_pct` 表示该真实事件对分数在模拟真实透镜 pair 分数中的百分位；数值越低，越不像模拟透镜正样本。`*_neg_pct` 表示它在随机非配对负样本中的百分位。

注意：本次真实 strain 的 waveform-only score 暴露出明显 OOD 问题，不能单独作为真实事件透镜判断。更可靠的 sanity check 是后续处理中的时间一致性 prior。

## 模拟参照分布

| distribution | count | mean | std | p05 | median | p95 | p99 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sim_waveform_lensed_positive_pairs | 6000 | 0.3271 | 0.3283 | -0.2058 | 0.3264 | 0.8674 | 0.9570 |
| sim_waveform_random_non_pairs | 200000 | 0.1292 | 0.2858 | -0.3354 | 0.1251 | 0.6053 | 0.7494 |
| sim_time_lr_lensed_positive_pairs | 6000 | 3.5221 | 2.0465 | -0.5802 | 4.0973 | 5.9781 | 6.7513 |
| sim_time_lr_random_non_pairs | 200000 | -2.1308 | 1.5470 | -3.7529 | -2.7675 | 1.3230 | 2.8051 |
| real_event_to_sim_catalog_scores_event_a | 9000 | -0.0102 | 0.1980 | -0.3298 | -0.0101 | 0.3156 | 0.4324 |
| real_event_to_sim_catalog_scores_event_b | 9000 | -0.0102 | 0.1980 | -0.3298 | -0.0101 | 0.3156 | 0.4324 |

## 结论

1. 真实 GWTC H1/L1 strain 可以通过当前 LIGO H1+L1 pipeline 完整跑通。
2. waveform-only 对 GWOSC 真实 strain 存在 OOD 标定问题；这正是加入真实事件 case study 的价值。
3. 两个真实事件相隔很久，Liao/GW-LMC time-delay prior 给出低透镜一致性，可作为 non-lensed sanity check。
4. 该实验没有使用真实透镜标签，不参与 supervised 训练，只作为真实事件 case study。

## 文件

- 输出目录：`runs/gwtc_real_event_case_study_20260617`
- `gwtc_real_event_case_study_summary.csv`
- `gwtc_real_event_reference_distributions.csv`
- `gwtc_real_event_embeddings.npy`