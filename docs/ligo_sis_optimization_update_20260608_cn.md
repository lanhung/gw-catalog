# LIGO noisy SIS 优化进展记录（2026-06-08）

## 当前最佳结果

当前仍以 `66_ligo_sis_best_skymap_overlap_full_compare.py` 为最好结果：

| 方法 | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| 51 baseline grid18 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| 63 alpha=2 sharpening | 0.089 | 0.184 | 0.241 | 0.425 | 0.549 | 0.839 | 75 |
| 66 best skymap overlap rerun | 0.092 | 0.189 | 0.245 | 0.440 | 0.566 | 0.848 | 71 |

使用特征：

- `trigger_time_obs`
- predicted `sky_map_overlap`
- waveform score
- waveform reciprocal rank

结论：目前 LIGO noisy SIS 的最佳 full-catalog R@10 仍为 `0.2453`。

## 2026-06-08 新尝试

### 68. 直接 pair CNN

脚本：

- `scripts/experiments/68_ligo_sis_siamese_pair_cnn_top100.py`

思路：

- 候选池保持不变：waveform Top100、trigger_time Top100、predicted sky overlap Top100 并集。
- 模型直接输入两条事件的双探测器波形，以及差分、绝对差分。
- 目标是在候选池内重排 true partner。

结果：

| 方法 | candidate recall | R@1 | R@5 | R@10 | R@50 | R@100 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| siamese_pair_cnn_top100_union | 0.575 | 0.002 | 0.015 | 0.027 | 0.112 | 0.219 | 250 |

分析：

- 结果明显低于当前最佳。
- 直接对齐两条波形做差分不适合透镜像，因为透镜像存在到达时间差、放大率差、相位/噪声扰动。
- 模型很容易把真实同源关系误学成局部波形差异。

### 69. Siamese embedding + softmax ranking loss

脚本：

- `scripts/experiments/69_ligo_sis_siamese_embedding_ranker_top100.py`

思路：

- 两条事件分别经过同一个 waveform encoder。
- 使用 `|za-zb|`、`za*zb` 与 catalog 特征做候选内排序。
- 用每个 anchor 的候选列表做 softmax ranking loss，直接优化候选内排序。

结果：

| 方法 | candidate recall | R@1 | R@5 | R@10 | R@50 | R@100 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| siamese_embedding_softmax_ranker_top100_union | 0.575 | 0.003 | 0.021 | 0.044 | 0.194 | 0.323 | 191 |

训练现象：

- train R@10 接近 1.0。
- test R@10 只有 0.044。

分析：

- 这是明显过拟合。
- 只用 val split 的 3000 个 anchor 训练深度 pair 模型不够。
- 当前 noisy SIS 的波形层面泛化信号很弱，直接新训练 pair encoder 风险较高。

### 70. match embedding pair reranker

脚本：

- `scripts/experiments/70_ligo_sis_embedding_pair_reranker_trainval.py`

思路：

- 不重新训练底层波形 encoder。
- 使用已有 match waveform embedding。
- 特征为 embedding pair 统计量、waveform score/rank、trigger_time_obs、predicted sky overlap。
- 使用 train+val 训练候选内 reranker。

结果：

| 方法 | candidate recall | R@1 | R@5 | R@10 | R@50 | R@100 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| HGB embedding pair | 0.575 | 0.002 | 0.008 | 0.011 | 0.041 | 0.109 | 267 |
| SGD embedding pair | 0.575 | 0.000 | 0.000 | 0.000 | 0.006 | 0.061 | 279 |
| ExtraTrees embedding pair | 0.575 | 0.015 | 0.020 | 0.023 | 0.052 | 0.124 | 273 |

分析：

- match embedding 的 pair distance/统计量没有提供可泛化的 LIGO noisy SIS 透镜对判别信息。
- 加入这些 embedding pair 特征反而破坏候选排序。

### 71. 当前最佳 4 特征 + train+val full-catalog rerank

脚本：

- `scripts/experiments/71_ligo_sis_trainval_full_catalog_rerank.py`

思路：

- 回到当前最佳 4 个稳定特征。
- 不引入 embedding pair 或深度 pair 模型。
- 将 reranker 训练数据从 val 扩大到 train+val。
- 在 test 上做 full-catalog ranking。

结果：

| 方法 | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| train+val random negatives | 0.085 | 0.160 | 0.214 | 0.418 | 0.534 | 0.835 | 82 |
| train+val hard negatives | 0.001 | 0.007 | 0.015 | 0.037 | 0.057 | 0.168 | 1188 |

分析：

- train+val 没有提升，反而低于 val-only 当前最佳。
- hard negative 训练严重破坏 full-catalog 排序。
- 说明问题不是 reranker 训练数据不够，而是 train split 和 val/test 的检索难度分布不一致。

## 关键诊断：train 与 val/test 分布偏移

诊断输出：

- `runs/ligo_sis_feature_distribution_diagnostic_20260608/feature_distribution_summary.csv`

采样每个 split 的 3000 个正样本和 60000 个随机负样本，统计 4 个核心特征的正负分离能力。

| split | feature | pos mean | neg mean | AUC |
|---|---|---:|---:|---:|
| train | trigger_time_obs | 14.824 | 18.096 | 0.055 |
| val | trigger_time_obs | 14.758 | 18.090 | 0.053 |
| test | trigger_time_obs | 14.811 | 18.086 | 0.055 |
| train | predicted sky overlap | -6.191 | -6.421 | 0.638 |
| val | predicted sky overlap | -6.207 | -6.419 | 0.615 |
| test | predicted sky overlap | -6.230 | -6.415 | 0.617 |
| train | waveform score | 0.729 | 0.192 | 0.961 |
| val | waveform score | 0.364 | 0.194 | 0.656 |
| test | waveform score | 0.371 | 0.196 | 0.662 |
| train | waveform reciprocal rank | 0.040 | 0.00047 | 0.964 |
| val | waveform reciprocal rank | 0.0227 | 0.00201 | 0.647 |
| test | waveform reciprocal rank | 0.0222 | 0.00201 | 0.657 |

最重要现象：

- `trigger_time_obs` 和 predicted `sky_map_overlap` 在 train/val/test 上比较接近。
- `waveform_score` 与 `waveform_recip_rank` 在 train 上异常强，但在 val/test 上弱很多。
- train 的 waveform 正负分离 AUC 约 0.96，而 val/test 只有约 0.66。

解释：

- train split 对 waveform 检索更容易。
- reranker 加入 train 后，会过度相信 waveform score/rank。
- 到 test 上，waveform score/rank 的真实区分能力下降，因此 train+val reranker 泛化变差。

## 当前结论

1. 当前最佳仍是 66：predicted sky overlap alpha=2 + full-catalog HGB rerank，R@10=0.245。
2. 深度 pair CNN 和 Siamese embedding ranker 在当前数据规模下严重过拟合，不适合作为下一步主线。
3. match embedding pair 统计特征不能提升 LIGO noisy SIS，说明已有 waveform embedding 没有稳定编码透镜同源关系。
4. 单纯扩大 reranker 训练集到 train+val 反而变差，原因是 train split waveform score/rank 太强，和 val/test 分布不一致。
5. LIGO noisy SIS 的主要瓶颈仍然是 predicted sky_map_overlap 质量不足，以及 waveform 检索信号在 noisy test 上较弱。

## 后续建议

优先方向：

1. 不再直接用 train split 训练 reranker，除非先做分布重加权或只采样 train 中“接近 val/test 难度”的样本。
2. 继续优化 sky-map 预测，但应以最终 overlap ranking 为目标，同时监控真实 pixel rank、entropy、overlap AUC。
3. 数据生成阶段保存更接近真实可观测的探测器级定位代理量，例如每个探测器的 trigger time、SNR proxy、相位/幅度 proxy；这些比从 noisy waveform 反推 sky map 更符合定位物理。
4. 如果继续做 pair model，应使用更多训练样本或跨 split 难度匹配，并避免逐点波形差分。

短期可做实验：

- 对 train 样本按 waveform_score/rank 分布做重采样，使 train 正样本分布接近 val/test，再训练 4 特征 reranker。
- 对 predicted sky-map 模型加入定位质量校准，目标不是只降低角误差，而是提高 true partner overlap 相对 false overlap 的 AUC。
- 在数据表中加入探测器级 arrival-time difference proxy，作为 sky localization 的物理中间量，再统一用于 SIS/PM。
