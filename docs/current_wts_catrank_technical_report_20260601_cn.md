# WTS-CatRank 技术文档

日期：2026-06-01

## 1. 方法名称

推荐名称：**WTS-CatRank**

全称：**Waveform-guided Time-Sky Catalog-level Reranking**

中文名：**波形引导的时空辅助目录级重排方法**

该方法不是替换原 waveform 模型，而是在原 waveform 检索结果基础上，加入两个真实可获得辅助观测量进行 catalog-level reranking。

## 2. 研究目标

目标是在强透镜引力波候选检索任务中，从一个事件 catalog 中识别可能属于同一强透镜系统的多重像事件。

当前重点是 noisy 场景下的检索提升。原 waveform 模型在纯信号数据上表现较好，但在 noisy 数据，尤其 LIGO noisy 数据上波形相似度容易失效。因此增加两个稳健的事件级观测量：

- `delta_time`: 两个事件的触发时间差。
- `sky_sep`: 两个事件天空定位中心点的角距离。

## 3. 总体流程

完整流程分为两个阶段。

### 3.1 Waveform 阶段

该阶段使用原本的 waveform 模型，不修改主干结构。

- 模型：Siamese InceptionTime encoder
- 训练目标：NT-Xent contrastive loss
- 输入：事件 waveform strain
- 输出：L2-normalized waveform embedding
- 相似度：embedding dot product / cosine similarity

对于事件 `i` 和事件 `j`：

```text
z_i = Encoder(waveform_i)
z_j = Encoder(waveform_j)
waveform_score(i, j) = z_i · z_j
```

该阶段生成：

- `waveform_score`: 原 waveform 模型给出的相似度。
- `waveform_reciprocal_rank`: 候选在 waveform 排序中的倒数排名。

### 3.2 Catalog-level reranking 阶段

该阶段是后处理重排，不重新训练 waveform encoder。

对 catalog 中每个事件 `i`，将整个 catalog 中所有其他事件作为候选 `j`，构造 pair-level 特征：

```text
1. log1p_delta_time = log(1 + |t_i - t_j|)
2. sky_sep = angular_sep(ra_i, dec_i, ra_j, dec_j)
3. waveform_score
4. waveform_reciprocal_rank
```

然后训练一个轻量 reranker 输出 pair score，并对每个 anchor event 的所有候选按 score 从高到低排序。

当前 reranker：

```text
HistGradientBoostingClassifier
```

注意：这里 `HistGradientBoostingClassifier` 不是主 waveform 模型，而是后处理排序器。

## 4. 使用的辅助参数

当前主方案只使用两个辅助观测量：

| 参数 | 含义 | 真实场景可获得性 | 备注 |
|---|---|---|---|
| `delta_time` | 两个触发事件的时间差 | 高 | 事件触发时间可直接获得 |
| `sky_sep` | 两个事件天空定位中心点角距离 | 中-高 | 当前使用 RA/DEC 点估计；真实场景建议替换为 sky-map overlap |

当前主方案不使用：

- component mass
- chirp mass
- mass ratio
- spin
- luminosity distance
- lensing truth label

这些扩展参数只作为探索性 ablation，不作为当前主结果。

## 5. 代码入口

全量实验脚本：

```text
scripts/experiments/37_all_waveform_time_sky_rerank.py
```

核心结果：

```text
runs/all_waveform_time_sky_rerank_20260601/summary.csv
runs/all_waveform_time_sky_rerank_20260601/summary.json
```

技术总结文档：

```text
docs/all_waveform_time_sky_rerank_results_20260601_cn.md
```

## 6. 全量实验设置

实验覆盖：

- ET pure
- ET noisy
- LIGO pure
- LIGO noisy

每组分别评估：

- SIS lens model
- PM lens model

使用已有 waveform checkpoint：

| detector | data | checkpoint |
|---|---|---|
| ET | pure | `runs/et10000_full_20260527_111510/*_pure_ep20_inceptiontime` |
| ET | noisy | `runs/et10000_bandpass_full_ep50_20260528_101013/*_noisy_bandpass_n10000_ep50` |
| LIGO | pure | `runs/ligo_pure_inceptiontime_bandpass_full_ep50_20260601_103901/*_pure_inceptiontime_bandpass_n10000_ep50` |
| LIGO | noisy | `runs/ligo_inceptiontime_bandpass_full_ep50_20260601_095620/*_noisy_inceptiontime_bandpass_n10000_ep50` |

## 7. 全量结果

| detector | data | family | waveform R@1 | waveform R@5 | waveform R@10 | rerank R@1 | rerank R@5 | rerank R@10 | rerank R@50 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| ET | pure | SIS | 0.9417 | 0.9807 | 0.9873 | 0.9877 | 0.9970 | 0.9983 | 0.9993 |
| ET | pure | PM | 0.9357 | 0.9740 | 0.9800 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| ET | noisy | SIS | 0.4070 | 0.5913 | 0.6577 | 0.8500 | 0.9443 | 0.9720 | 0.9973 |
| ET | noisy | PM | 0.3040 | 0.4630 | 0.5407 | 0.9900 | 0.9997 | 1.0000 | 1.0000 |
| LIGO | pure | SIS | 0.9543 | 0.9833 | 0.9887 | 0.9947 | 0.9960 | 0.9963 | 0.9977 |
| LIGO | pure | PM | 0.9547 | 0.9843 | 0.9883 | 0.9997 | 1.0000 | 1.0000 | 1.0000 |
| LIGO | noisy | SIS | 0.0103 | 0.0243 | 0.0400 | 0.4850 | 0.7413 | 0.8617 | 0.9947 |
| LIGO | noisy | PM | 0.0067 | 0.0170 | 0.0283 | 0.9647 | 1.0000 | 1.0000 | 1.0000 |

## 8. 结果解读

### 8.1 pure 数据

pure 数据中 waveform 模型本身已经较强，reranking 主要带来小幅提升：

- ET pure SIS: R@1 从 0.9417 提升到 0.9877
- ET pure PM: R@1 从 0.9357 提升到 1.0000
- LIGO pure SIS: R@1 从 0.9543 提升到 0.9947
- LIGO pure PM: R@1 从 0.9547 提升到 0.9997

### 8.2 noisy 数据

noisy 数据中提升更明显：

- ET noisy SIS: R@1 从 0.4070 提升到 0.8500
- ET noisy PM: R@1 从 0.3040 提升到 0.9900
- LIGO noisy SIS: R@1 从 0.0103 提升到 0.4850
- LIGO noisy PM: R@1 从 0.0067 提升到 0.9647

说明 noisy 场景下，单纯 waveform similarity 容易受噪声干扰；加入到达时间和天空位置后，目录级排序能显著恢复候选检索能力。

### 8.3 LIGO noisy SIS

LIGO noisy SIS 的 R@1 仍低于其他组，但：

- R@5 = 0.7413
- R@10 = 0.8617
- R@50 = 0.9947

这说明真实配对大多数已经被排到较前位置，只是 top1 仍有混淆。该组是后续优化的重点。

## 9. 为什么结果可能偏高

当前 catalog-level reranking 的效果较强，尤其 PM 任务接近满分，需要谨慎解释。可能原因包括：

1. `delta_time` 分布在模拟数据中对正负样本过于可分。
2. 当前 `sky_sep` 使用 RA/DEC 点估计，而真实场景中天空定位应为概率 sky map。
3. 正样本多重像天空位置在模拟数据中可能过于接近。
4. 训练集和测试集共享相同的数据生成规律，reranker 容易学习到模拟分布。
5. PM lens model 的时间延迟或天空分布可能比 SIS 更容易区分。

因此当前结果应表述为：

```text
在当前模拟观测假设下，WTS-CatRank 显示出强 catalog-level 检索潜力。
```

不应直接表述为真实观测场景下已经达到同等性能。

## 10. 推荐后续验证

为了增强科学可信度，建议补充以下实验：

1. Ablation：只用 waveform。
2. Ablation：waveform + delta_time。
3. Ablation：waveform + sky_sep。
4. Ablation：waveform + delta_time + sky_sep。
5. 增大 sky localization uncertainty。
6. 用 sky-map overlap 替代 sky_sep。
7. 对 `delta_time` 或 `sky_sep` 做随机打乱 sanity check。
8. 分析正负样本的 `delta_time` 和 `sky_sep` 分布。
9. 分别统计 SIS/PM 中错误 top1 的参数分布。

## 11. 当前结论

WTS-CatRank 保留原 waveform Siamese InceptionTime 模型作为主干，只在后处理阶段加入 `delta_time + sky_sep` 两个可观测辅助量进行 catalog-level reranking。

该方案在 ET/LIGO、pure/noisy、SIS/PM 全部 8 组实验中均提升原 waveform baseline，尤其 noisy 场景提升显著。当前可作为论文中“catalog-level retrieval/reranking”方向的主实验方案。
