# 统一方法下的 sky 辅助特征对比实验

日期：2026-06-03

## 实验目的

本实验固定同一套 catalog-level rerank 方法，只改变辅助空间特征来源，用来比较：

1. 不加辅助参数的 waveform-only 基线；
2. 当前 trigger_time_obs 时间观测基线；
3. 加真实计算的 sky_sep；
4. 加真实计算的 sky_map_overlap；
5. 加机器学习估计 sky map 后计算的 sky_map_overlap。

其中真实 sky_sep 和真实 sky_map_overlap 使用数据中的真实 ra/dec 构造，只能作为 oracle 上限实验，不应作为真实观测场景主方案。机器学习 sky-map 版本不直接读取 ra/dec，而是用 waveform embedding 预测 sky unit vector，再计算两事件的高斯近似 sky-map overlap。

## 统一实验口径

- waveform 阶段：沿用当前各组 InceptionTime / bandpass waveform embedding 结果。
- catalog reranker：统一使用 HistGradientBoostingClassifier。
- 训练采样：每个正样本配 500 个随机负样本。
- 测试方式：对每个 anchor 在整个 test catalog 中重排全部候选。
- 指标：R@1、R@5、R@10、R@50、R@100、R@500、median rank。
- 输出目录：`runs/unified_sky_aux_comparison_20260603/`
- 脚本：`scripts/experiments/43_unified_sky_aux_comparison.py`

## 特征设置

| variant | 使用特征 | 是否 oracle |
|---|---|---|
| waveform_only | waveform_score, waveform_reciprocal_rank | 否 |
| trigger_time_only | log1p_delta_time_obs, waveform_score, waveform_reciprocal_rank | 否 |
| trigger_time_plus_real_sky_sep | trigger_time_only + oracle_sky_sep_from_ra_dec | 是 |
| trigger_time_plus_real_sky_overlap | trigger_time_only + oracle_log_sky_map_overlap_from_true_ra_dec | 是 |
| trigger_time_plus_predicted_sky_overlap | trigger_time_only + predicted_log_sky_map_overlap | 否 |

## R@1 总表

| detector | mode | family | waveform_only | trigger_time_only | real_sky_sep | real_sky_overlap | predicted_sky_overlap |
|---|---|---:|---:|---:|---:|---:|---:|
| ET | pure | SIS | 0.976 | 0.874 | 0.998 | 0.998 | 0.917 |
| ET | pure | PM | 0.973 | 0.995 | 1.000 | 1.000 | 0.994 |
| ET | noisy | SIS | 0.640 | 0.568 | 0.965 | 0.963 | 0.512 |
| ET | noisy | PM | 0.539 | 0.862 | 0.998 | 0.998 | 0.860 |
| LIGO | pure | SIS | 0.983 | 0.859 | 0.996 | 0.997 | 0.889 |
| LIGO | pure | PM | 0.981 | 0.998 | 1.000 | 1.000 | 0.996 |
| LIGO | noisy | SIS | 0.083 | 0.086 | 0.809 | 0.791 | 0.080 |
| LIGO | noisy | PM | 0.053 | 0.266 | 0.998 | 0.995 | 0.254 |

## Noisy 场景 Top-k 关键结果

| detector | family | variant | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---|---:|---:|---:|---:|---:|
| ET | SIS | waveform_only | 0.640 | 0.654 | 0.667 | 0.802 | 1 |
| ET | SIS | trigger_time_only | 0.568 | 0.721 | 0.780 | 0.875 | 1 |
| ET | SIS | real_sky_sep | 0.965 | 0.998 | 1.000 | 1.000 | 1 |
| ET | SIS | real_sky_overlap | 0.963 | 0.998 | 0.999 | 0.999 | 1 |
| ET | SIS | predicted_sky_overlap | 0.512 | 0.712 | 0.779 | 0.877 | 1 |
| ET | PM | waveform_only | 0.539 | 0.555 | 0.575 | 0.739 | 1 |
| ET | PM | trigger_time_only | 0.862 | 0.964 | 0.995 | 1.000 | 1 |
| ET | PM | real_sky_sep | 0.998 | 1.000 | 1.000 | 1.000 | 1 |
| ET | PM | real_sky_overlap | 0.998 | 1.000 | 1.000 | 1.000 | 1 |
| ET | PM | predicted_sky_overlap | 0.860 | 0.966 | 0.993 | 1.000 | 1 |
| LIGO | SIS | waveform_only | 0.083 | 0.086 | 0.091 | 0.124 | 1123 |
| LIGO | SIS | trigger_time_only | 0.086 | 0.171 | 0.224 | 0.408 | 81 |
| LIGO | SIS | real_sky_sep | 0.809 | 0.984 | 0.998 | 0.999 | 1 |
| LIGO | SIS | real_sky_overlap | 0.791 | 0.981 | 0.998 | 1.000 | 1 |
| LIGO | SIS | predicted_sky_overlap | 0.080 | 0.158 | 0.209 | 0.399 | 93 |
| LIGO | PM | waveform_only | 0.053 | 0.057 | 0.059 | 0.096 | 1430.5 |
| LIGO | PM | trigger_time_only | 0.266 | 0.691 | 0.943 | 1.000 | 3 |
| LIGO | PM | real_sky_sep | 0.998 | 1.000 | 1.000 | 1.000 | 1 |
| LIGO | PM | real_sky_overlap | 0.995 | 1.000 | 1.000 | 1.000 | 1 |
| LIGO | PM | predicted_sky_overlap | 0.254 | 0.677 | 0.932 | 1.000 | 4 |

## 主要结论

1. 真实 sky_sep 和真实 sky_map_overlap 的效果基本一致。
   - ET noisy SIS：real sky_sep R@1 = 0.965，real sky_overlap R@1 = 0.963。
   - LIGO noisy SIS：real sky_sep R@1 = 0.809，real sky_overlap R@1 = 0.791。
   - LIGO noisy PM：real sky_sep R@1 = 0.998，real sky_overlap R@1 = 0.995。

2. sky_map_overlap 可以作为 sky_sep 的物理替代指标，但前提是 sky map 本身可靠。
   真实 overlap 的效果很强，说明 overlap 这个判据本身是合理的。

3. 当前机器学习估计 sky-map 的效果不好，主要瓶颈是 sky-map 预测质量。
   各组 predicted sky-map 的平均角误差大约 1.52 到 1.57 rad，接近随机天区，因此 predicted_sky_overlap 没有接近 oracle overlap 上限。

4. 对 PM，trigger_time_obs 已经很强。
   ET noisy PM 中 trigger_time_only R@1 = 0.862，LIGO noisy PM 中 R@50 = 1.000。这说明 PM 的时间差特征对候选召回非常有效。

5. 对 SIS，真实空间信息非常关键。
   LIGO noisy SIS 中 trigger_time_only R@1 只有 0.086，但加入真实 sky_overlap 后 R@1 到 0.791。这说明 SIS 的第一名排序主要缺少可靠空间约束。

## 论文建议

如果论文强调真实观测可行性，主实验不应使用真实 ra/dec 直接得到的 sky_sep。更合理的写法是：

- 主方法：waveform + trigger_time_obs + catalog-level rerank。
- Oracle 上限：加入真实 sky_sep 或真实 sky_map_overlap，证明空间定位信息的潜在价值。
- 机器学习 sky-map 实验：作为可观测替代方案的初步探索，当前效果受 sky-map 预测误差限制。
- 后续工作：改进 waveform 到 sky-map 的快速估计模型，或接入真实探测器参数估计产生的 sky localization probability map。


## 结果分析与物理解释

### 1. LIGO noisy 的主要困难不是 reranker，而是波形相似度失效

在 LIGO noisy 场景中，原始 waveform 检索几乎失效：

- LIGO noisy SIS 原始 waveform R@1 = 0.010；统一 waveform-only rerank 后 R@1 = 0.083。
- LIGO noisy PM 原始 waveform R@1 = 0.007；统一 waveform-only rerank 后 R@1 = 0.053。

这说明 noisy LIGO 下，当前 waveform embedding 已经不能稳定判断两条事件是否属于同一透镜系统。catalog-level reranker 可以对 waveform score/rank 做一定校准，但在缺少可靠物理辅助信息时，提升有限。

### 2. trigger_time_obs 对 PM 有明显帮助，但对 SIS 的第一名排序不足

PM 场景中，trigger_time_obs 的贡献很明显：

- ET noisy PM：waveform-only R@1 = 0.539，trigger_time_only R@1 = 0.862。
- LIGO noisy PM：waveform-only R@1 = 0.053，trigger_time_only R@1 = 0.266，R@10 = 0.943，R@50 = 1.000。

这说明 PM 数据中的时间延迟结构更有辨识度，trigger_time_obs 可以显著提升候选召回。

但 SIS 场景不同：

- ET noisy SIS：waveform-only R@1 = 0.640，trigger_time_only R@1 = 0.568，但 R@50 从 0.802 提升到 0.875。
- LIGO noisy SIS：waveform-only R@1 = 0.083，trigger_time_only R@1 = 0.086，但 R@50 从 0.124 提升到 0.408，median rank 从 1123 降到 81。

也就是说，trigger_time_obs 对 SIS 主要改善候选召回和排序范围，但不足以稳定决定第一名。原因可能是 SIS 的时间延迟分布不如 PM 唯一，不同系统之间的时间差更容易重叠。

### 3. 真实空间定位信息是解决 LIGO noisy 的关键

真实 sky_sep 和真实 sky_map_overlap 的效果都非常强：

- LIGO noisy SIS：real sky_sep R@1 = 0.809，real sky_overlap R@1 = 0.791。
- LIGO noisy PM：real sky_sep R@1 = 0.998，real sky_overlap R@1 = 0.995。
- ET noisy SIS：real sky_sep R@1 = 0.965，real sky_overlap R@1 = 0.963。
- ET noisy PM：real sky_sep R@1 = 0.998，real sky_overlap R@1 = 0.998。

这说明如果能获得可靠的 sky localization probability map，空间重叠信息可以显著缓解 noisy LIGO 下 waveform embedding 失效的问题，尤其是 SIS。

### 4. sky_map_overlap 可以替代 sky_sep，但当前 ML sky-map 预测还不够

真实 sky_sep 和真实 sky_map_overlap 的结果非常接近，说明 sky_map_overlap 作为 sky_sep 的替代指标是合理的，而且更贴近真实观测流程：真实场景中通常获得的是天区概率图，而不是可直接当作精确输入的真实 ra/dec。

但是当前机器学习估计 sky-map 的版本没有接近 oracle 上限：

- LIGO noisy SIS：real sky_overlap R@1 = 0.791，predicted sky_overlap R@1 = 0.080。
- LIGO noisy PM：real sky_overlap R@1 = 0.995，predicted sky_overlap R@1 = 0.254。
- ET noisy SIS：real sky_overlap R@1 = 0.963，predicted sky_overlap R@1 = 0.512。

主要原因是当前 sky-map 预测模型的平均角误差大约为 1.52 到 1.57 rad，接近随机天区。因此问题不在 sky_map_overlap 指标本身，而在 waveform 到 sky-map 的快速估计模型还不够可靠。

### 5. 对论文的实验组织建议

为了保持方法一致性，论文中不建议针对 SIS、PM、ET、LIGO 分别换不同方法。更合理的实验结构是：

1. 统一主方法：waveform embedding + trigger_time_obs + catalog-level rerank。
2. 无辅助基线：waveform-only catalog-level rerank。
3. 空间信息 oracle 上限：加入真实 sky_sep 或真实 sky_map_overlap。
4. 可观测替代探索：用机器学习预测 sky map 后计算 predicted sky_map_overlap。

其中真实 sky_sep 和真实 sky_map_overlap 应明确标注为 oracle upper bound，不能作为真实观测主方法。predicted sky_map_overlap 可以作为未来可观测方案的初步探索，但当前结果说明它还不是有效主方案。

### 6. 后续优化方向

后续优化不应主要集中在继续调 HGB 参数，而应集中在以下方向：

1. 改进 sky-map 预测模型，使 predicted sky_map_overlap 更接近 real sky_map_overlap。
2. 接入更真实的参数估计或快速定位流程，直接生成 sky localization probability map。
3. 针对 LIGO noisy 训练更抗噪的 waveform encoder。
4. 对 SIS 使用 contrastive learning 或 ranking loss，因为 SIS 的时间差信息不足以唯一确定匹配对象。
5. 保留统一 catalog-level rerank 框架，只改变可观测输入特征，避免方法按透镜模型或探测器特调。

