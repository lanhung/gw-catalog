# LIGO sky-map 预测与 catalog 检索优化总结

日期：2026-06-05

## 1. 当前研究目标

当前主要困难集中在 LIGO noisy 数据，尤其是 LIGO noisy SIS。

已有实验表明：如果使用真实 sky 信息，catalog-level rerank 的效果可以非常高；但真实场景中不能直接使用 `ra/dec`，也不能直接使用由真实 `ra/dec` 计算出的 `sky_sep`。因此当前目标是：

```text
单条事件 waveform -> 机器学习预测 sky map
两条事件 predicted sky map -> sky_map_overlap
waveform + trigger_time_obs + predicted sky_map_overlap -> catalog-level ranking
```

也就是说，真实使用阶段只依赖 waveform、观测触发时间 `trigger_time_obs`，以及由 waveform 预测出的 sky-map overlap。

## 2. 对照基线

### 2.1 真实 sky 信息上限

之前统一对比实验显示，真实 sky 信息对 LIGO 检索非常关键：

| 数据 | 方法 | R@1 | 说明 |
|---|---:|---|
| LIGO noisy SIS | real sky-overlap oracle | 0.791 | 使用真实 sky 信息，作为上限参考 |
| LIGO noisy PM | real sky-overlap oracle | 0.995 | 使用真实 sky 信息，作为上限参考 |

这说明 sky 信息本身确实能显著提升检索，但关键瓶颈是如何从 waveform 中可靠预测 sky map。

### 2.2 不使用 sky-map 预测的基线

| 数据 | 方法 | R@1 | 说明 |
|---|---:|---|
| LIGO noisy SIS | waveform only / trigger-time based baseline | 约 0.08-0.09 | SIS 很难，仅靠 waveform 和时间不够 |
| LIGO noisy PM | trigger-time / waveform baseline | 约 0.26-0.31 | PM 相对容易，时间信息贡献更大 |

## 3. 已尝试的 sky-map 优化方案

## 3.1 单点 sky direction 预测

脚本：

```text
scripts/experiments/49_ligo_cnn_sky_predictor_rerank.py
```

方法：

```text
LIGO 双通道 waveform -> CNN + attention pooling -> sky unit vector
```

然后用预测 sky direction 构造高斯近似 sky overlap。

结果：

| 数据 | sky mean error rad | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|---:|
| LIGO noisy SIS | 1.348 | 0.087 | 0.173 | 0.226 | 0.421 | 79 |
| LIGO noisy PM | 1.396 | 0.270 | 0.688 | 0.934 | 1.000 | 3 |

结论：CNN 能从 waveform 中学习到一定 sky 信息，但单点方向预测过于粗糙，尤其对 SIS 的 R@1 提升有限。

## 3.2 概率 sky-map 预测，12 x 24 网格

脚本：

```text
scripts/experiments/50_ligo_grid_skymap_predictor_rerank.py
```

方法：

```text
LIGO 双通道 waveform -> SkyMapCNN_grid_12x24 -> 12 x 24 sky probability map
```

训练标签：

```text
真实 ra/dec -> spherical Gaussian soft label
```

两事件 sky 相关性：

```text
sky_map_overlap = sum(P_event_i(pixel) * P_event_j(pixel))
```

结果：

| 数据 | sky mean error rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LIGO noisy SIS | 1.318 | 0.093 | 0.182 | 0.232 | 0.424 | 0.544 | 0.827 | 81 |
| LIGO noisy PM | 1.332 | 0.286 | 0.723 | 0.945 | 1.000 | 1.000 | 1.000 | 3 |

结论：概率 sky-map 比单点 sky direction 更合理。PM 有较明显提升，SIS 也有小幅提升，但 R@1 仍很低。

## 3.3 ResNet backbone + 18 x 36 细网格 sky-map

脚本：

```text
scripts/experiments/51_ligo_sis_resnet_grid18_skymap_rerank.py
```

改动：

1. sky-map 分辨率从 `12 x 24` 提高到 `18 x 36`。
2. soft label 宽度从 `sigma = 0.35 rad` 改为 `sigma = 0.28 rad`。
3. waveform backbone 从轻量 CNN 改为 residual Conv1D + dilation + attention pooling。
4. checkpoint 选择从最低 KL 改成最低 validation sky angular error。

结果：

| 数据 | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LIGO noisy SIS | 1.311 | 1.250 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |

结论：细网格 ResNet 进一步降低 sky 误差，并把正确候选整体往前推，median rank 从 81 改到 74。但 R@1 没有实质提升，说明目前 sky-map 精度还不足以稳定区分第一名。

## 3.4 简单后处理权重融合

脚本：

```text
scripts/experiments/52_ligo_sis_grid18_rank_fusion.py
```

方法：复用 51 号 sky-map checkpoint，不重新训练模型，只搜索以下特征的线性权重：

```text
waveform_score_z
reciprocal_rank_z
-neg_log1p_delta_time_obs_z
grid18_skymap_overlap_z
```

结果：

| 方法 | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| HistGradient rerank, grid18 sky-map | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| 简单权重融合 | 0.089 | 0.170 | 0.218 | 0.367 | 0.445 | 0.653 | 159 |

结论：简单线性权重融合明显差于非线性 reranker。因此当前问题不是权重没调好，而是 sky-map 预测和 overlap 表达本身还不够强。

## 3.5 Pair-level contrastive sky-map overlap

目标：让训练更贴近 catalog 检索，不只要求单事件 sky-map 接近真实位置，还要求同一透镜对的预测 sky-map overlap 高于随机非透镜对。

核心 loss：

```text
P_a = sky map(anchor)
P_p = sky map(true partner)
P_n = sky map(random negative)

log_pos = log(sum(P_a * P_p))
log_neg = log(sum(P_a * P_n))
loss_pair = max(0, margin - log_pos + log_neg)
loss = loss_kl + lambda_pair * loss_pair
```

### 实验 53：强 pair loss，从零训练

脚本：

```text
scripts/experiments/53_ligo_sis_pair_contrastive_grid18_skymap_rerank.py
```

设置：

```text
PAIR_MARGIN = 0.20
PAIR_LAMBDA = 0.50
NEGATIVES_PER_ANCHOR = 2
```

结果：

| 方法 | sky mean error rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ResNet grid18 baseline | 1.311 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| 强 pair loss | 1.366 | 0.083 | 0.169 | 0.221 | 0.415 | 0.526 | 0.828 | 86 |

结论：强 pair loss 会破坏单事件 sky-map 定位。虽然 pair loss 自身快速下降，但泛化检索效果变差。

### 实验 54：弱 pair loss，从 baseline checkpoint 微调

脚本：

```text
scripts/experiments/54_ligo_sis_pair_finetune_grid18_skymap_rerank.py
```

设置：

```text
初始化：51 号 ResNet grid18 baseline checkpoint
PAIR_MARGIN = 0.10
PAIR_LAMBDA = 0.05
NEGATIVES_PER_ANCHOR = 1
```

结果：

| 方法 | sky mean error rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ResNet grid18 baseline | 1.311 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| 弱 pair finetune | 1.323 | 0.093 | 0.173 | 0.226 | 0.417 | 0.540 | 0.825 | 80 |

结论：弱 pair 微调没有崩，但也没有超过 baseline。说明直接把 pair loss 加到 sky-map 输出上并不是当前最优路径。

## 4. 当前最佳结果

目前 LIGO noisy SIS 最稳结果仍是 51 号实验：

```text
ResNet grid18 probability sky-map + HistGradient catalog rerank
```

| 数据 | 方法 | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| LIGO noisy SIS | ResNet grid18 sky-map | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| LIGO noisy PM | grid12 probability sky-map | 0.286 | 0.723 | 0.945 | 1.000 | 1.000 | 1.000 | 3 |

## 5. 主要原因分析

### 5.1 LIGO noisy SIS 难的核心原因

1. LIGO noisy 下 waveform 受噪声影响较大，纯波形匹配排名非常差。
2. SIS 透镜像之间的 waveform 差异不像 PM 那样容易由时间或形态区分。
3. 真实 sky 信息非常有效，但当前从 waveform 预测出的 sky-map 仍然太粗。
4. 当前 sky mean error 约 1.31 rad，仍远不足以稳定把正确伴随事件排到第一。
5. Pair-level loss 如果直接作用在 sky-map 上，容易牺牲物理定位精度，导致泛化变差。

### 5.2 为什么 PM 比 SIS 好

PM 的检索对 trigger-time / waveform ranking 更敏感，正确候选更容易被推到 Top-k 内。因此即使 sky-map 不完美，PM 的 R@5/R@10 已经比较高；SIS 则需要更精确的 sky-map 或更强的 catalog-level 区分机制。

## 6. 后续优化建议

### 6.1 不建议继续做的方向

1. 不建议继续简单加深单事件 sky 模型。已有结果显示 sky error 小幅下降不一定转化为 R@1 提升。
2. 不建议继续简单线性权重融合。52 号实验已经明显变差。
3. 不建议直接强加 pair contrastive loss。53 号实验说明它会破坏 sky 定位。

### 6.2 更建议尝试的方向

#### 方向 A：overlap calibration head

冻结 51 号 sky-map 模型，不改变 predicted sky-map，只额外训练一个小的配对校准器：

```text
输入：predicted sky_map_overlap, trigger_time_obs difference, waveform_score, waveform_rank
输出：calibrated pair score
```

这个方案的优点是不会破坏 sky-map 物理定位，只学习如何把已有信息组合成更好的 catalog ranking。

#### 方向 B：top-k hard negative pair training

pair loss 不再使用随机负样本，而是使用当前模型容易混淆的 hard negatives：

```text
对每个 anchor，先用 waveform 或当前 rerank 找 Top-k 候选
从 Top-k 里选择错误候选作为 negative
训练模型区分 true partner 与 hard negative
```

这样更接近 R@1/R@5 的实际错误来源。

#### 方向 C：checkpoint 按 retrieval 指标选择

当前主要按 sky angular error 选 checkpoint。后续可以增加 validation retrieval：

```text
每个 epoch 计算 validation R@5 / R@50 / median rank
按检索指标选择 checkpoint
```

因为 sky angular error 降低不一定等价于 catalog ranking 提升。

#### 方向 D：sky-map uncertainty calibration

当前 sky-map 可能过于平滑或过于尖锐。可以研究：

```text
temperature scaling
entropy regularization
soft label sigma search
```

目标是让 predicted overlap 的数值更可靠，而不只是方向均值更准。

## 7. 当前结论

当前优化已经证明：

1. 用 waveform 预测概率 sky-map 比单点 sky direction 更合理。
2. 更细网格和 ResNet backbone 可以改善 sky-map 预测，并改善 median rank。
3. 但 LIGO noisy SIS 的 R@1 仍卡在约 0.093，距离真实 sky oracle 的 0.791 很远。
4. 直接 pair contrastive loss 没有成功，原因是它会破坏单事件 sky-map 定位。
5. 下一阶段应从“继续改 sky-map 模型”转向“冻结 sky-map，学习 overlap/ranking 校准”。

推荐下一步实验：

```text
55_ligo_sis_overlap_calibration_head.py
```

目标：在不改变 51 号 sky-map 预测器的前提下，训练一个 pair-level calibration head，专门优化 catalog-level ranking。

## 8. 2026-06-05 继续优化：R@10 目标实验

用户提出新的优化目标：希望 LIGO noisy SIS 的 `R@10` 能超过 `0.5`。围绕这个目标，继续尝试了排序校准、候选召回诊断、候选集 rerank、改进 sky-map loss、双探测器交互输入等方案。

### 8.1 实验 55：hard-negative calibrated rerank

脚本：

```text
scripts/experiments/55_ligo_sis_hard_negative_calibrated_rerank.py
```

方法：冻结 51 号 sky-map 模型，不改 sky-map 预测器，只改 reranker。训练负样本不再主要使用随机负样本，而是从 waveform、sky-overlap、trigger-time 的前排候选中采 hard negatives。

结果：

| method | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| 51 baseline | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| hgb hard-negative | 0.088 | 0.183 | 0.239 | 0.314 | 0.349 | 0.598 | 343.5 |

结论：hard-negative 训练让 R@10 从 0.232 小幅升到 0.239，但整体排序明显变差，median rank 退化到 343.5。说明 hard negatives 可以稍微强化 Top10，但会损伤全局排序稳定性。

### 8.2 实验 56：候选召回上限诊断

脚本：

```text
scripts/experiments/56_ligo_sis_candidate_recall_diagnostic.py
```

单独信号源排序能力：

| signal | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| waveform | 0.011 | 0.024 | 0.040 | 0.108 | 0.158 | 0.322 | 1180.5 |
| predicted sky-overlap | 0.001 | 0.005 | 0.008 | 0.031 | 0.060 | 0.234 | 1503.5 |
| trigger-time | 0.019 | 0.109 | 0.173 | 0.378 | 0.511 | 0.839 | 94.5 |

三路候选并集 oracle 覆盖率：

| candidate set | oracle candidate recall |
|---|---:|
| waveform/sky/time 各 Top5 并集 | 0.129 |
| waveform/sky/time 各 Top10 并集 | 0.201 |
| waveform/sky/time 各 Top20 并集 | 0.280 |
| waveform/sky/time 各 Top50 并集 | 0.429 |
| waveform/sky/time 各 Top100 并集 | 0.574 |
| waveform/sky/time 各 Top200 并集 | 0.712 |
| waveform/sky/time 各 Top500 并集 | 0.895 |
| waveform/sky/time 各 Top1000 并集 | 0.977 |

关键结论：如果只看三路 Top10 并集，正确答案最多覆盖 0.201；Top50 并集也只有 0.429。要实现 `R@10 > 0.5`，必须至少从三路 Top100 并集约 300 个候选中，把真伴随事件稳定排进前 10。这说明目标非常困难，瓶颈不仅是 rerank，而是候选召回和候选内排序同时不足。

### 8.3 实验 57：union Top100 candidate-only rerank

脚本：

```text
scripts/experiments/57_ligo_sis_union_top100_candidate_rerank.py
```

方法：只在 waveform、sky-overlap、trigger-time 各 Top100 的候选并集内部重新排序。该候选集 oracle recall 为 0.574，是当前达到 R@10 > 0.5 的最低可行候选池。

结果：

| method | candidate recall | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|---:|
| hgb union Top100 | 0.574 | 0.081 | 0.183 | 0.239 | 0.436 | 75 |
| logistic union Top100 | 0.574 | 0.059 | 0.143 | 0.192 | 0.359 | 98 |

结论：即使候选池中有 57.4% 的真伴随事件，当前特征和模型也无法稳定把它们排进前 10。R@10 仍只有 0.239，说明候选内排序信息不足。

### 8.4 实验 58：KL + expected angular distance loss

脚本：

```text
scripts/experiments/58_ligo_sis_expected_angular_grid18_skymap_rerank.py
```

方法：在原 `KL(predicted sky-map, soft label)` 之外，增加 expected angular distance loss，使预测概率质量整体靠近真实方向。

```text
loss = KL + 0.35 * expected_angular_loss
```

结果：

| method | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 51 baseline | 1.311 | 1.250 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| expected angular loss | 1.309 | 1.243 | 0.087 | 0.184 | 0.234 | 0.422 | 0.540 | 0.834 | 81 |

结论：sky 角误差进一步降低，R@10 小幅提高到 0.234，但 R@1 和 median rank 变差。说明降低平均 sky angular error 仍不足以显著提升 catalog R@10。

### 8.5 实验 59：双探测器交互输入 + expected angular loss

脚本：

```text
scripts/experiments/59_ligo_sis_detector_interaction_expected_angular.py
```

方法：仍然只使用 waveform，但不再只输入 `H, L` 两个通道，而是显式构造双探测器交互通道：

```text
H, L, H-L, |H-L|, H*L
```

训练目标继续使用 `KL + expected angular loss`。

结果：

| method | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 51 baseline | 1.311 | 1.250 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| detector interaction + expected angular | 1.305 | 1.245 | 0.088 | 0.180 | 0.231 | 0.425 | 0.551 | 0.829 | 77 |

结论：这是当前 sky mean error 最低的模型，说明双探测器交互通道确实帮助 sky 预测。但检索 R@10 没有提升，仍约 0.231。当前瓶颈已经不是单纯 sky mean error，而是 predicted sky-overlap 对“正确伴随事件 vs 前排错误候选”的区分力不足。

## 9. R@10 > 0.5 目标的当前判断

本轮实验后，LIGO noisy SIS 的最佳 R@10 仍只有约 `0.239`，未达到 `0.5`。

最关键的诊断是：

```text
waveform + predicted sky-overlap + trigger-time 各 Top100 并集 oracle recall = 0.574
```

这意味着理论上存在达到 R@10 > 0.5 的候选覆盖基础，但需要非常强的候选内排序能力。目前模型只能把这个候选池中的一部分真伴随排进前 10，说明：

1. predicted sky-overlap 单独非常弱，R@10 只有 0.008。
2. trigger-time 是目前最强单项，R@10 为 0.173，但不足以支撑 0.5。
3. waveform 单独也很弱，R@10 只有 0.040。
4. 三者组合后的排序器缺少能区分 Top100 hard negatives 的强特征。
5. sky mean error 从 1.311 降到 1.305，并没有带来 R@10 提升，说明平均角误差不是唯一关键指标。

## 10. 下一步建议

如果目标坚持为 `LIGO noisy SIS R@10 > 0.5`，下一步不建议继续只做小幅 sky-map 模型改良。更可能有效的方向是：

1. 提升候选召回：让正确伴随进入三路 Top50 并集，而不是 Top100 才超过 0.5。
2. 训练 hard-negative 专用 pair scorer：输入两条 waveform 的 cross-correlation / time-delay / amplitude-ratio 特征，而不只用单事件 sky-map overlap。
3. 让 sky-map 模型直接优化 hard-negative 区分：负样本必须来自 union Top100，而不是随机负样本。
4. 引入多任务定位 proxy：同时预测 detector time-delay、channel amplitude ratio、phase/correlation proxy，作为 sky-map backbone 的辅助监督。
5. 如果物理上允许，保存或生成更接近真实探测器定位的信息，例如每个 detector 的 trigger-time/SNR/phase proxy，用于提升 sky localization。

当前最值得新开的实验是：

```text
60_ligo_sis_hard_negative_pair_scorer.py
```

核心思想：不再只用 `predicted sky_map_overlap` 一个压缩量，而是对 anchor-candidate 两条 waveform 直接构造 pair-level 特征，专门训练 Top100 hard-negative 内部排序器。

## 11. sky-map 预测质量专项评估

为了不只看最终 catalog R@k，新增了 sky-map 预测质量报告，专门评估单事件 sky-map 本身以及两事件 predicted overlap 的区分能力。

脚本：

```text
scripts/experiments/61_ligo_sis_skymap_quality_report.py
```

输出目录：

```text
runs/ligo_sis_skymap_quality_report_20260605/summary.csv
```

### 11.1 评估指标含义

| 指标 | 含义 |
|---|---|
| sky mean/median error rad | predicted sky-map 概率均值方向与真实方向的角距离 |
| true_pixel_topK | 真实 sky pixel 是否排在预测概率前 K |
| true_pixel_rank_median | 真实 sky pixel 在 648 个 sky pixels 中的中位排名 |
| true_pixel_prob_mean | 模型分给真实 sky pixel 的平均概率 |
| entropy_norm_mean | 预测 sky-map 熵 / 最大熵，越接近 1 越接近均匀分布 |
| pair_pos_overlap_mean | 真实透镜对 predicted sky-map overlap 平均值 |
| pair_neg_overlap_mean | 随机非透镜对 predicted sky-map overlap 平均值 |
| pair_overlap_auc_sampled | 用 predicted overlap 区分真实透镜对和随机负对的采样 AUC |

### 11.2 test split 结果

| model | sky mean error rad | sky median error rad | true pixel Top1 | true pixel Top10 | true pixel Top50 | true pixel rank median | entropy norm | pos overlap mean | neg overlap mean | overlap AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 51 ResNet grid18 | 1.320 | 1.273 | 0.002 | 0.031 | 0.135 | 183 | 0.971 | 0.001850 | 0.001673 | 0.620 |
| 58 expected angular | 1.334 | 1.287 | 0.003 | 0.031 | 0.138 | 189 | 0.960 | 0.001917 | 0.001709 | 0.607 |
| 59 detector interaction | 1.349 | 1.302 | 0.002 | 0.026 | 0.142 | 185 | 0.972 | 0.001869 | 0.001742 | 0.601 |

### 11.3 关键解释

这些指标说明，当前 sky-map 预测质量并不只是“最终 R@k 不好”，sky-map 本身也有明显问题：

1. 真实 sky pixel 的 Top10 命中率只有约 `2.6% - 3.1%`。
2. 真实 sky pixel 的中位排名约 `183 / 648`，说明真实位置通常没有被模型排到前面。
3. 预测 sky-map 的归一化熵约 `0.96 - 0.97`，非常接近均匀分布。
4. 真实 pixel 平均概率只有约 `0.0021`，而均匀分布概率为 `1 / 648 = 0.00154`，提升很小。
5. 正样本 overlap 和负样本 overlap 非常接近，例如 51 号 test：

```text
positive overlap mean = 0.001850
negative overlap mean = 0.001673
ratio = 1.106
AUC = 0.620
```

这说明 predicted sky_map_overlap 对真实透镜对和随机非透镜对只有弱区分能力。对于 catalog-level ranking 来说，随机负对都已经难以分开，更不用说 Top100 hard negatives。

### 11.4 为什么 sky mean error 和检索结果不一致

58/59 号实验降低了 validation sky mean error，但 test 上 pair overlap AUC 没有提升，甚至下降。这说明：

```text
sky angular mean error 低
不等于
predicted sky_map_overlap 对配对检索有强排序能力
```

原因是当前 sky-map 很平，概率质量分散。即使均值方向稍微更接近真实方向，整张概率图之间的 overlap 差异仍然很小，导致 pair-level ranking 难以使用。

### 11.5 下一步 sky-map 预测应优化什么

后续不能只盯 `sky mean error`，应该同时优化：

1. 提高真实 pixel / 邻域 pixel 的 TopK 命中率。
2. 降低无效高熵，让 sky-map 不要接近均匀分布。
3. 提高 positive pair overlap 与 negative pair overlap 的间隔。
4. 特别提高 hard negative 下的 overlap AUC，而不是随机 negative AUC。
5. 将 checkpoint 选择指标改为：

```text
sky angular error
+ true_pixel_top50
+ pair_overlap_auc
+ validation catalog R@10
```

当前最直接的新优化方向是：

```text
temperature / entropy regularization + hard-negative overlap AUC validation
```

也就是让 sky-map 更有峰值、更可区分，同时用 pair overlap AUC 而不是单纯 angular error 选择模型。

## 12. predicted sky-map 与 sky-overlap 误差机制分析

用户进一步要求明确：模型输出的 `predicted sky map` 和由它计算出的 `sky_map_overlap` 到底误差怎么样，为什么会导致最终检索结果不好。

新增分析脚本：

```text
scripts/experiments/62_ligo_sis_skymap_overlap_error_analysis.py
```

输出目录：

```text
runs/ligo_sis_skymap_overlap_error_analysis_20260605/
```

核心输出文件：

```text
event_skymap_errors.csv          # 每条事件的 sky-map 预测误差
pair_overlap_errors.csv          # 每个真实透镜配对的 overlap 排名误差
distribution_summary.csv         # 分布统计
pair_by_overlap_rank_bins.csv    # 按 overlap 排名分箱分析
```

### 12.1 单事件 predicted sky-map 误差分布

以当前主线模型 `51_resnet_grid18` 的 LIGO noisy SIS test split 为例：

| 指标 | 数值 |
|---|---:|
| sky error mean | 1.320 rad |
| sky error median | 1.273 rad |
| sky error 25% 分位 | 0.815 rad |
| sky error 75% 分位 | 1.771 rad |
| sky error 90% 分位 | 2.208 rad |
| true pixel rank median | 183 / 648 |
| true pixel rank 75% 分位 | 296 / 648 |
| true pixel Top10 | 0.031 |
| true pixel Top50 | 0.135 |
| true pixel prob median | 0.00217 |
| entropy norm median | 0.981 |
| top10 probability mass median | 0.0276 |

解释：

1. 真实 sky pixel 通常排在第 `183/648` 左右，远没有进入高概率区域。
2. 真实 pixel Top10 命中率只有 `3.1%`。
3. Top10 pixels 总概率质量中位数只有 `2.76%`，说明模型没有形成清晰峰值。
4. 归一化熵中位数 `0.981`，非常接近均匀分布。
5. 因此 predicted sky-map 更像“弱偏置的宽分布”，不是可定位的 sky map。

### 12.2 sky_map_overlap 误差分布

对每个 anchor，计算它与所有 candidate 的 predicted sky-map overlap，并观察真实 partner 的排名。

| 指标 | 数值 |
|---|---:|
| true partner overlap mean | 0.001850 |
| true partner overlap median | 0.001781 |
| best false overlap mean | 0.002266 |
| best false overlap median | 0.002054 |
| best false - true log overlap median | 0.103 |
| true partner overlap rank median | 1503 / 4500 |
| true partner overlap rank 75% 分位 | 2882 / 4500 |
| true partner overlap rank 90% 分位 | 3804 / 4500 |

最关键的问题是：

```text
best false overlap mean = 0.002266
true partner overlap mean = 0.001850
```

也就是说，在每个 anchor 的候选集中，最高的错误候选 overlap 通常比真实 partner 的 overlap 更高。

这不是 reranker 的小问题，而是 `predicted sky_map_overlap` 自身的排序信号已经错了。真实 partner 在 sky-overlap 单独排序中的中位排名是 `1503/4500`，所以它很难帮助 catalog-level R@10。

### 12.3 哪些 pair 能被 sky-overlap 排好

按真实 partner 的 sky-overlap 排名分箱：

| true overlap rank bin | 数量 | true overlap mean | best false overlap mean | anchor sky error mean | partner sky error mean | anchor true pixel rank median | partner true pixel rank median |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1-10 | 24 | 0.002782 | 0.002817 | 0.885 | 0.901 | 123.5 | 105.0 |
| 10-50 | 69 | 0.002670 | 0.002804 | 0.775 | 0.782 | 135.0 | 134.0 |
| 50-100 | 86 | 0.002535 | 0.002712 | 0.818 | 0.820 | 117.0 | 112.5 |
| 100-500 | 524 | 0.002269 | 0.002479 | 0.987 | 0.973 | 138.0 | 140.0 |
| 500-1000 | 437 | 0.001969 | 0.002246 | 1.190 | 1.194 | 175.0 | 173.0 |
| 1000-5000 | 1860 | 0.001631 | 0.002162 | 1.420 | 1.422 | 196.0 | 198.0 |

规律很清楚：

1. 当 anchor 和 partner 的 sky error 都低于约 `0.9 rad` 时，true partner 才有可能排进 Top10/Top50。
2. 大部分样本落在 rank `1000-5000`，这些样本的 anchor/partner sky error 平均约 `1.42 rad`。
3. 真实 pixel rank 越靠后，真实 pair overlap 越低，错误候选越容易超过真实 partner。

### 12.4 为什么最终 catalog 结果不好

根本原因链条是：

```text
LIGO noisy waveform 定位信息弱
-> 单事件 predicted sky-map 很平，真实 pixel 排名低
-> 正确透镜对的 predicted overlap 不够高
-> 错误候选经常有更高 overlap
-> sky_overlap 单独排序中真实 partner 中位 rank = 1503/4500
-> catalog reranker 只能把它作为弱特征，无法把 R@10 推高
```

所以当前最终结果不好，不是因为 catalog-level reranker 没有使用 sky_overlap，而是因为输入给它的 predicted sky_overlap 本身区分力太弱。

### 12.5 直接结论

当前 predicted sky-map 的主要误差不是单纯“角误差大”，而是：

1. 概率图过平，接近均匀分布。
2. 真实 sky pixel 不在高概率区域，Top10 命中只有约 3%。
3. 两个真实透镜像的 predicted sky maps 没有形成足够高 overlap。
4. 错误候选中的某些 sky maps 反而与 anchor 更相似。
5. 因此 sky_map_overlap 对 hard negatives 没有足够判别力。

下一步若继续优化 sky-map，应把目标从：

```text
降低 sky mean angular error
```

改成：

```text
提高真实 sky 区域 TopK 概率
降低无效高熵
提高 true partner overlap 相对 best false overlap 的 margin
提高 hard-negative pair overlap AUC
```

## 13. 针对 sky-map 过平问题的优化尝试

基于第 12 节诊断，当前 predicted sky-map 的主要问题是概率图过平、真实位置不突出、true partner overlap 经常低于 best false overlap。因此继续尝试了两类“让 sky-map 更尖、更可区分”的方案。

### 13.1 实验 63：post-hoc temperature sharpening

脚本：

```text
scripts/experiments/63_ligo_sis_skymap_temperature_sharpening.py
```

方法：不重新训练模型，对 51 号模型输出的 sky-map 做后处理：

```text
P_sharp(pixel) = P(pixel)^alpha / sum(P^alpha)
```

`alpha > 1` 时，概率图会变尖。

结果：

| alpha | entropy norm | overlap ratio | overlap AUC | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.00 | 0.971 | 1.105 | 0.619 | 0.091 | 0.172 | 0.227 | 0.416 | 0.546 | 0.830 | 79 |
| 1.25 | 0.963 | 1.123 | 0.618 | 0.090 | 0.178 | 0.237 | 0.426 | 0.554 | 0.832 | 77 |
| 1.50 | 0.956 | 1.138 | 0.617 | 0.088 | 0.180 | 0.239 | 0.428 | 0.555 | 0.836 | 76 |
| 2.00 | 0.942 | 1.163 | 0.615 | 0.089 | 0.184 | 0.241 | 0.425 | 0.549 | 0.839 | 75 |
| 3.00 | 0.918 | 1.205 | 0.613 | 0.085 | 0.181 | 0.239 | 0.429 | 0.553 | 0.844 | 74 |

结论：适度 sharpening 有小幅帮助，最佳 `alpha=2.0` 时：

```text
R@10: 0.227 -> 0.241
median rank: 79 -> 75
```

但 overlap AUC 没有提升，反而从 `0.619` 降到 `0.615`。这说明后处理变尖能让 reranker 更容易利用数值差异，但没有真正解决正负 overlap 排序问题。

### 13.2 实验 64：训练时加入低熵/尖峰约束

脚本：

```text
scripts/experiments/64_ligo_sis_entropy_sharp_grid18_skymap_rerank.py
```

方法：重新训练 sky-map 模型，使用更窄 soft label，并在 loss 中加入 entropy penalty：

```text
SOFT_SIGMA = 0.22
loss = KL + 0.30 * expected_angular_loss + 0.035 * entropy
```

目标是让模型在训练阶段就输出更集中的 sky-map。

结果：

| method | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 51 baseline | 1.311 | 1.250 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| 64 entropy sharp | 1.309 | 1.260 | 0.090 | 0.180 | 0.231 | 0.426 | 0.547 | 0.834 | 77 |
| 63 post-hoc alpha=2 | - | - | 0.089 | 0.184 | 0.241 | 0.425 | 0.549 | 0.839 | 75 |

结论：训练时强行低熵没有提升 catalog 检索，R@10 仍为 `0.231`。这说明“让图变尖”本身不是充分条件，关键是峰值必须变尖到正确 sky 区域，或者让 true partner overlap 相对 hard false candidate 有更大 margin。

### 13.3 当前优化结论

本轮优化说明：

1. sky-map 过平确实是问题，post-hoc sharpening 可以带来小幅 R@10 提升。
2. 但简单 sharpening 只改变分布形状，不改变错误峰值位置。
3. 如果真实 sky pixel 本来排名在 183/648，变尖可能会把错误区域也一起变尖。
4. 因此后续不能只做 entropy regularization，而要直接优化：

```text
真实 sky 区域 TopK 命中
true partner overlap > best false overlap
hard-negative pair overlap margin
```

下一步更合理的训练目标应该是 hard-negative overlap margin，而不是随机 pair contrastive。负样本应来自当前模型 overlap / waveform / trigger-time 的 Top100 hard candidates。

## 14. hard-negative overlap margin 微调实验

基于前面结论，继续尝试直接优化：

```text
true partner overlap > hard false overlap
```

与之前随机 pair contrastive 不同，这一版 hard negative 来自当前 sky-map 模型中 overlap 最高的一批错误候选。

脚本：

```text
scripts/experiments/65_ligo_sis_hard_negative_overlap_finetune.py
```

方法：

1. 从 51 号 baseline checkpoint 初始化。
2. 用 baseline sky-map 在 train split 上为每个 anchor 找 overlap 最高的错误候选。
3. 微调 sky-map 模型，loss 包含：

```text
KL sky-map loss
+ expected angular loss
+ hard-negative overlap margin loss
```

其中：

```text
PAIR_MARGIN = 0.12
PAIR_LAMBDA = 0.035
LR = 1.5e-4
EPOCHS = 6
```

结果：

| method | sky val mean error | entropy norm | overlap ratio | overlap AUC | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 51 baseline | 1.311 | 0.971 | 1.106 | 0.620 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| 63 post-hoc alpha=2 | - | 0.942 | 1.163 | 0.615 | 0.089 | 0.184 | 0.241 | 0.425 | 0.549 | 0.839 | 75 |
| 65 hard-neg overlap finetune | 1.328 | 0.963 | 1.103 | 0.606 | 0.091 | 0.180 | 0.234 | 0.412 | 0.542 | 0.831 | 80 |

训练过程显示：

1. hard-negative pair loss 会下降。
2. entropy 会下降，sky-map 会变尖。
3. 但 validation sky error 变差，从约 1.31 退到 1.33 以上。
4. test overlap AUC 从 baseline 的 0.620 降到 0.606。
5. R@10 只有 0.234，没有超过 post-hoc sharpening 的 0.241。

结论：即使 hard negative 来自 overlap 前排，直接微调 sky-map 仍然容易破坏单事件定位和泛化 overlap。当前问题不是简单加一个 pair loss 能解决的。

### 14.1 新判断

到目前为止，三类直接改 sky-map 的方法都遇到同一问题：

| 方法 | 问题 |
|---|---|
| entropy sharpening | 图变尖，但可能尖到错误位置 |
| random pair contrastive | pair loss 下降，但 sky 定位变差 |
| hard-negative overlap finetune | hard pair loss 下降，但 overlap AUC 泛化变差 |

因此下一步不应继续直接改 sky-map 主干。更合理的是：

```text
冻结 sky-map predictor
保留 predicted sky-map 作为一个弱定位信息源
另训练 pair-level scorer 直接处理两条 waveform 的相对信息
```

也就是把问题从：

```text
单事件 waveform -> 更好的 sky-map
```

转为：

```text
两条 waveform + trigger_time + predicted sky-map features
-> hard-negative pair scorer
```

这个 pair scorer 可以直接学习 Top100 hard negatives 中 true partner 与 false candidate 的差异，而不会破坏 sky-map 本身。

## 15. 当前最佳 sky_map_overlap 全量复跑对比

用户要求使用目前最好的 `sky_map_overlap` 方案跑一次 full-catalog，并比较优化幅度。

当前最好的方案是：

```text
51 号 ResNet grid18 predicted sky-map
+ post-hoc temperature sharpening, alpha = 2.0
+ HistGradient catalog rerank
```

新增复跑脚本：

```text
scripts/experiments/66_ligo_sis_best_skymap_overlap_full_compare.py
```

输出目录：

```text
runs/ligo_sis_best_skymap_overlap_full_compare_20260605/summary.csv
```

### full-catalog test 结果

| method | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| 51 baseline grid18 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| 63 alpha=2 previous | 0.089 | 0.184 | 0.241 | 0.425 | 0.549 | 0.839 | 75 |
| 66 alpha=2 full rerun | 0.092 | 0.189 | 0.245 | 0.440 | 0.566 | 0.848 | 71 |

### 相对 51 baseline 的提升

| metric | baseline | best alpha=2 full rerun | absolute delta | relative change |
|---|---:|---:|---:|---:|
| R@1 | 0.093 | 0.092 | -0.001 | -1.1% |
| R@5 | 0.176 | 0.189 | +0.013 | +7.2% |
| R@10 | 0.232 | 0.245 | +0.013 | +5.7% |
| R@50 | 0.433 | 0.440 | +0.007 | +1.7% |
| R@100 | 0.560 | 0.566 | +0.006 | +1.0% |
| R@500 | 0.832 | 0.848 | +0.016 | +2.0% |
| median rank | 74 | 71 | -3 | 改善 3 名 |

### sky-overlap 本身变化

| metric | alpha=2 full rerun |
|---|---:|
| entropy norm mean | 0.942 |
| positive overlap mean | 0.002138 |
| negative overlap mean | 0.001838 |
| overlap ratio | 1.163 |
| overlap AUC sampled | 0.616 |

### 结论

当前最佳 `sky_map_overlap` 方案确实有小幅优化：

```text
R@10: 0.232 -> 0.245
median rank: 74 -> 71
```

但提升幅度有限，主要原因仍然是 predicted sky-map 本身定位不够准，overlap AUC 只有约 `0.616`。后处理 sharpening 能让概率图更尖，让 reranker 更容易利用 overlap 数值，但没有改变错误峰值位置，因此无法带来大幅提升。

如果要继续追求 `R@10 > 0.5`，下一步需要引入独立 pair-level waveform scorer 或更多真实可观测定位 proxy，而不是继续只改 `sky_map_overlap`。

## 16. pair-level hard-candidate waveform scorer 实验

基于前面结论，尝试不再继续微调 sky-map，而是冻结 sky-map，把问题转成候选池内部的 pair-level 排序。

脚本：

```text
scripts/experiments/67_ligo_sis_pair_waveform_hard_candidate_scorer.py
```

输出目录：

```text
runs/ligo_sis_pair_waveform_hard_candidate_scorer_20260605/summary.csv
```

### 方法

候选池仍使用：

```text
waveform score Top100
+ trigger_time Top100
+ predicted sky-overlap Top100
```

使用当前最佳 `alpha=2` sharpened sky-overlap。

对 anchor-candidate 两条 waveform 提取 26 维 pair-level 手工特征，包括：

```text
H/L 两通道 cross-correlation peak
cross-correlation lag
zero-lag correlation
correlation peak contrast
两事件 waveform L1/L2 差异
peak amplitude ratio
RMS ratio
双探测器差分通道相关性
waveform score / rank
predicted sky-overlap
trigger_time score
sky-time interaction
```

训练：

```text
positive = true partner
negative = Top100 candidate union 中的 false candidates
```

评估：candidate-only ranking。

### 结果

| method | candidate recall | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|---:|
| 57 hgb union Top100, no waveform pair features | 0.574 | 0.081 | 0.183 | 0.239 | 0.436 | 75 |
| 67 HGB pair waveform features | 0.575 | 0.079 | 0.159 | 0.206 | 0.396 | 91 |
| 67 Logistic pair waveform features | 0.575 | 0.036 | 0.120 | 0.179 | 0.381 | 93 |

### 结论

手工 pair-level waveform 特征没有提升，反而低于原来的 candidate rerank。说明简单 cross-correlation、幅度比、RMS 比等统计特征不足以区分 LIGO noisy SIS 的 Top100 hard negatives。

这进一步说明：

1. 当前 Top100 候选池有理论空间，candidate recall 约 0.575。
2. 但手工特征无法把 true partner 稳定排到前 10。
3. 如果继续 pair-level scorer，需要使用学习型模型，例如 Siamese 1D-CNN / cross-attention，而不是手工统计特征。
4. 也可能需要更接近物理定位的可观测 proxy，例如 detector-level trigger time、SNR、phase proxy，否则 waveform 中的可分辨信息太弱。

### 下一步判断

到目前为止：

```text
最佳 full-catalog R@10 = 0.245
最佳 candidate-only R@10 = 0.239
手工 pair waveform scorer R@10 = 0.206
```

如果继续优化，建议两个方向二选一：

1. 上深度 pair model：Siamese/InceptionTime pair encoder，对 Top100 hard candidates 直接学习排序。
2. 回到数据生成/特征层：保存 detector-level observable proxy，如每个 detector 的 trigger time、SNR、phase/amplitude proxy，用物理上更强的定位特征提升 sky localization。
