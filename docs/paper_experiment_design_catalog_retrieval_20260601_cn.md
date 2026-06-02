# 强透镜引力波目录级检索论文实验设计方案

生成日期：2026-06-01

本文档整理当前 gw-catalog 项目后续论文实验的推荐设置。核心目标是把任务从简单的 pair-level 二分类，明确转为更接近真实观测场景的 catalog-level retrieval：在大量非透镜引力波事件中，检索少量可能的强透镜重复成像事件。

## 1. 研究任务定位

真实观测中，系统不会提前给定两条事件并询问它们是否成对，而是面对一个观测事件目录，需要从大量候选事件中寻找可能的强透镜配对。因此论文中应重点描述为：

```text
给定一个引力波事件 catalog，对每个 query 事件，在整个 catalog 中检索最可能与其构成强透镜重复成像的候选事件。
```

这对应的是 catalog-level ranking / catalog-level retrieval，而不是单纯的 pair-level binary classification。

## 2. 需要对比的四类方法

论文中建议保留四组核心消融实验，用来拆分波形模型、时空辅助参数和目录级重排各自的贡献。

| 编号 | 方法名称 | Waveform | Catalog-level ranking | delta_time + sky_sep | 目的 |
|---:|---|---:|---:|---:|---|
| 1 | Waveform only | 是 | 否 | 否 | 最基础 baseline，检验仅靠波形相似度的检索能力 |
| 2 | Time-Sky only ranking | 否 | 是 | 是 | 检验 delta_time 与 sky_sep 本身是否过强 |
| 3 | Waveform-only catalog rerank | 是 | 是 | 否 | 检验 catalog rerank 框架本身是否带来提升 |
| 4 | Waveform + Time-Sky catalog rerank | 是 | 是 | 是 | 主方法，检验波形与可观测时空信息结合后的最终效果 |

推荐在论文表格中按上述顺序展示，从最简单 baseline 逐步过渡到完整方法。

### 2.1 Waveform only

该方法只使用波形模型输出的 embedding 相似度进行排序。

```text
waveform -> Siamese InceptionTime encoder -> embedding -> cosine similarity -> ranking
```

该实验回答的问题是：如果不使用任何外部可观测参数，仅凭波形形态，模型能否从 catalog 中找回真实透镜配对。

### 2.2 Time-Sky only ranking

该方法不使用波形分数，只使用两个可观测辅助参数：

```text
log1p_delta_time = log(1 + |t_i - t_j|)
sky_sep = angular separation between two sky positions
```

该实验回答的问题是：时间差和天空角距离本身是否已经可以强区分透镜与非透镜事件。如果该实验结果很高，说明模拟数据中的时空参数区分度很强，论文解释时必须谨慎，不能把提升全部归因于波形模型。

### 2.3 Waveform-only catalog rerank

该方法保留 catalog-level rerank 框架，但不输入 delta_time 与 sky_sep，只使用：

```text
waveform_score
waveform_reciprocal_rank
```

该实验回答的问题是：目录级后处理排序器本身是否能通过 waveform score 与原始排序名次带来校准收益。如果该方法只比 waveform only 小幅提升，说明主要提升不是来自 rerank 结构本身；如果提升明显，则需要进一步解释 score calibration 的作用。

### 2.4 Waveform + Time-Sky catalog rerank

这是当前推荐主方法。

```text
waveform_score
waveform_reciprocal_rank
log1p_delta_time
sky_sep
        -> catalog-level reranker -> final ranking
```

它的物理含义是：强透镜重复成像事件不仅应具有相似波形，还应在到达时间差和天空定位上具有一定一致性。

## 3. 真实物理场景下的数据比例设置

真实观测中强透镜事件是稀有事件，因此不应只使用 50% 透镜 / 50% 非透镜的平衡数据作为最终结论。建议设置三层 catalog 组成。

| 实验场景 | 透镜事件比例 | 非透镜事件比例 | 推荐用途 |
|---|---:|---:|---|
| Balanced benchmark | 50% | 50% | 受控验证，比较模型上限 |
| Main imbalanced catalog | 10% | 90% | 主论文实验，体现不平衡检索 |
| Low-rate stress test | 1% | 99% | 补充实验，更接近低发生率场景 |
| Extreme low-rate test | 0.1% | 99.9% | 可选压力测试，计算量大、方差高 |

### 3.1 Balanced benchmark

该设置用于方法开发与受控比较。例如：

```text
5000 个透镜事件 + 5000 个非透镜事件
或
10000 个透镜事件 + 10000 个非透镜事件
```

该设置不代表真实发生率，只用于回答模型是否学到了基本判别规律。

### 3.2 10% 透镜事件主实验

建议作为论文主 catalog 检索实验。

示例设置：

```text
83 对透镜系统 = 166 个透镜事件
1500 个非透镜事件
总事件数 = 1666
透镜事件比例约为 10%
```

该设置的优点是：

```text
1. 比 50%/50% 更接近真实目录检索任务；
2. 每个 catalog 中仍有足够多透镜对，可以稳定计算 R@K；
3. 计算量可控，适合 ET/LIGO、pure/noisy、SIS/PM 全量对比。
```

### 3.3 1% 透镜事件压力测试

建议作为补充实验或鲁棒性实验。

示例设置：

```text
50 对透镜系统 = 100 个透镜事件
9900 个非透镜事件
总事件数 = 10000
透镜事件比例 = 1%
```

或在计算资源有限时使用：

```text
25 对透镜系统 = 50 个透镜事件
4950 个非透镜事件
总事件数 = 5000
透镜事件比例 = 1%
```

该设置更接近稀有事件搜索，但结果方差会更大，需要多个随机种子重复实验。

### 3.4 0.1% 极低比例实验

该设置更接近二代探测器中强透镜事件非常稀有的情况，但不建议作为唯一主实验。

示例：

```text
50 对透镜系统 = 100 个透镜事件
99900 个非透镜事件
总事件数 = 100000
透镜事件比例 = 0.1%
```

问题是计算量明显增加，并且如果透镜对数量太少，R@K 的统计方差会很大。因此该设置更适合作为可选附录实验。

## 4. 探测器分组建议

建议主实验按以下 8 组报告：

```text
ET pure SIS
ET pure PM
ET noisy SIS
ET noisy PM
LIGO pure SIS
LIGO pure PM
LIGO noisy SIS
LIGO noisy PM
```

其中 pure 数据用于观察算法上限，noisy 数据用于观察真实噪声影响。论文主讨论应重点看 noisy，尤其是 LIGO noisy SIS，因为这是目前最困难的一组。

## 5. 推荐评价指标

catalog-level retrieval 中不能只看 pair-level accuracy。建议报告：

```text
R@1
R@5
R@10
R@50
MRR
median true rank
Precision@K
平均 top-K 误报数量
```

其中 R@K 表示真实配对事件是否出现在前 K 个候选中。对于真实搜索任务，R@10 与 R@50 也有重要意义，因为后续可以交给更精确的 Bayesian posterior overlap、sky-map overlap 或人工审查。

对于 1% 或 0.1% 低比例实验，建议额外报告：

```text
每个 catalog 的候选事件总数
每个 catalog 的真实透镜对数量
每个 query 平均产生的 false positives
不同随机种子下的均值和标准差
```

## 6. 随机种子与统计稳定性

不平衡 catalog 中透镜事件数量较少，单次采样可能不稳定。建议：

```text
10% 透镜实验：至少 5 个随机种子，推荐 10 个。
1% 透镜实验：至少 10 个随机种子。
0.1% 透镜实验：至少 20 个随机种子，或增加 catalog 总规模。
```

最终表格中报告：

```text
mean ± std
```

这样可以避免某一次 catalog 采样偶然偏易或偏难。

## 7. 物理真实性注意事项

当前实验中使用的 sky_sep 是由事件的 RA/DEC 点估计计算的角距离。真实引力波事件的天空定位通常是不确定的概率分布，因此更真实的版本应逐步替换为：

```text
sky-map overlap
90% credible region intersection
posterior overlap score
sky-map Bayes factor / overlap statistic
```

论文中可以先使用 sky_sep 作为轻量近似，但需要说明这是 sky localization consistency 的近似指标。若后续能加入 sky-map overlap，则物理解释会更强。

同时需要注意：如果模拟数据中正样本的 sky_sep 过小、负样本的 sky_sep 过大，则 time-sky only ranking 可能取得过高结果。这种情况需要通过消融实验和分布图说明。

建议额外绘制：

```text
正负样本 delta_time 分布
正负样本 sky_sep 分布
waveform_score 分布
rerank score 分布
```

## 8. 推荐论文结果表结构

每个 detector / data mode / lens family 下，建议表格包含四种方法：

| Method | Waveform | Time-Sky | Catalog rerank | R@1 | R@5 | R@10 | R@50 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Waveform only | Yes | No | No | - | - | - | - | - |
| Time-Sky only | No | Yes | Yes | - | - | - | - | - |
| Waveform-only catalog rerank | Yes | No | Yes | - | - | - | - | - |
| Waveform + Time-Sky catalog rerank | Yes | Yes | Yes | - | - | - | - | - |

对于不平衡实验，推荐再增加：

```text
lensed_event_fraction
catalog_size
number_of_lensed_pairs
number_of_unlensed_events
```

## 9. 推荐论文表述

英文表述：

```text
We evaluate the proposed method under three catalog compositions: a balanced benchmark for controlled model comparison, a 10% lensed-event catalog for imbalanced retrieval, and a 1% lensed-event catalog as a low-rate stress test. The final ranking is evaluated at the catalog level by retrieving the true lensed counterpart of each query event from a mixed event catalog.
```

中文表述：

```text
本文设置三类目录组成：平衡基准实验用于受控比较，10% 透镜事件目录用于模拟不平衡检索，1% 透镜事件目录用于低发生率压力测试。评价过程在目录级完成，即对每个 query 事件，从混合事件目录中检索其真实强透镜对应事件。
```

## 10. 当前推荐结论

论文中最合理的主线是：

```text
1. 先用 waveform only 证明波形模型具备基础检索能力；
2. 再用 time-sky only 检查辅助参数是否过强；
3. 用 waveform-only catalog rerank 检查后处理排序框架本身的贡献；
4. 最后用 waveform + time-sky catalog rerank 作为完整方法；
5. 在 10% 和 1% 透镜比例下验证方法能否适应大量非透镜背景。
```

这样可以把论文贡献讲清楚：本文不是简单地做 pair-level 二分类，而是构建了一个更接近真实观测目录的强透镜引力波候选检索框架，并系统评估波形信息、时空可观测参数和目录级重排机制的贡献。
