# LIGO noisy 检索优化记录（2026-06-01）

## 数据与基线

- 数据：`/root/autodl-tmp/gw_ligo_10000_matchstyle_20260527_091859`
- 每类样本：SIS / PM / Unlensed 各 10000，LIGO 双探测器输入形状为 `(N, 2, 98304)`。
- 基线模型：`InceptionTime + bandpass 40-580 + 50 epoch + waveform retrieval`。

| family | 方法 | R@1 | R@5 | R@10 | 备注 |
|---|---:|---:|---:|---:|---|
| SIS | waveform baseline | 0.0103 | 0.0243 | 0.0400 | noisy 纯波形检索很弱 |
| PM | waveform baseline | 0.0067 | 0.0170 | 0.0283 | noisy 纯波形检索很弱 |
| SIS | pure waveform baseline | 0.9543 | 0.9833 | 0.9887 | 证明代码和双通道读取正常，问题来自 noisy |
| PM | pure waveform baseline | 0.9547 | 0.9843 | 0.9883 | 同上 |

## 方法 1：增大 waveform topK 后做 `delta_time + sky_sep` 重排

脚本：`scripts/experiments/29_ligo_time_sky_aux_large_topk.py`

| family | topK | waveform R@1 | waveform R@1000 | aux R@1 | aux R@5 | aux R@10 | 结论 |
|---|---:|---:|---:|---:|---:|---:|---|
| SIS | 50 | 0.0107 | 0.1077 | 0.1043 | 0.1077 | 0.1077 | top50 候选太小 |
| SIS | 500 | 0.0107 | 0.3223 | 0.2397 | 0.3137 | 0.3223 | 有提升但受候选覆盖限制 |
| SIS | 1000 | 0.0107 | 0.4577 | 0.2970 | 0.4203 | 0.4490 | 仍不到 0.7 |
| SIS | 2000 | 0.0107 | 0.4577 | 0.3493 | 0.5533 | 0.6083 | 候选覆盖上限约 0.65 |
| PM | 50 | 0.0067 | 0.0780 | 0.0780 | 0.0780 | 0.0780 | top50 候选太小 |
| PM | 1000 | 0.0067 | 0.4047 | 0.3970 | 0.4047 | 0.4047 | 有提升但受候选覆盖限制 |
| PM | 2000 | 0.0067 | 0.4047 | 0.5753 | 0.6023 | 0.6023 | 仍被 waveform 候选覆盖卡住 |

结论：topK 重排不能作为最终方案，因为真配对大量不在 noisy waveform 的前 K 候选中。

## 方法 2：catalog-level `delta_time + sky_sep`

脚本：`scripts/experiments/30_ligo_time_sky_catalog_aux.py`

不再依赖 waveform topK，直接在整个 catalog 内用两个真实可获得辅助量排序。

| family | 特征 | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---:|---:|---:|---:|---:|
| SIS | `delta_time`, `sky_sep` | 0.4547 | 0.7270 | 0.8527 | 0.9963 | 2 |
| PM | `delta_time`, `sky_sep` | 0.9580 | 1.0000 | 1.0000 | 1.0000 | 1 |

结论：catalog-level 排序明显优于 topK 重排；PM 已经非常好，SIS top1 仍需更多事件可观测参数。

## 方法 3：catalog-level `delta_time + sky_sep + waveform score`

脚本：`scripts/experiments/32_ligo_catalog_fusion_aux_waveform.py`

| family | 特征 | R@1 | R@5 | R@10 | 结论 |
|---|---|---:|---:|---:|---|
| SIS | 两个辅助量 + waveform score/rank | 0.4380 | 0.7420 | 0.8497 | waveform 对 top1 没帮助，只略增 R@5 |
| PM | 两个辅助量 + waveform score/rank | 0.9523 | 0.9970 | 0.9970 | 不如纯辅助参数稳定 |

结论：当前 noisy waveform embedding 本身质量太低，不适合当作强排序特征。

## 方法 4：扩展真实可观测参数（v1）

脚本：`scripts/experiments/33_ligo_catalog_extended_observable_aux.py`

增加：`chirp_mass_diff`, `mass_ratio_diff`, `chi_eff_diff`, `luminosity_distance_ratio`。

| family | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|
| SIS | 0.6807 | 0.9203 | 0.9743 | 0.9973 | 1 |
| PM | 0.9867 | 1.0000 | 1.0000 | 1.0000 | 1 |

结论：SIS 已接近 0.7，说明事件参数差异对 noisy 场景很关键。

## 方法 5：扩展真实可观测参数（v2，当前最好）

脚本：`scripts/experiments/34_ligo_catalog_extended_observable_v2.py`

在 v1 基础上增加：`mass_1_diff`, `mass_2_diff`, `a_1_diff`, `a_2_diff`。

| family | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|
| SIS | 0.8533 | 0.9890 | 0.9987 | 1.0000 | 1 |
| PM | 0.9947 | 0.9993 | 0.9993 | 0.9993 | 1 |

结论：该方案已经超过 noisy R@1 > 0.7 的目标。SIS 从 waveform baseline 的 0.0103 提升到 0.8533；PM 从 0.0067 提升到 0.9947。

## waveform-only 对照

脚本：`scripts/experiments/31_ligo_noisy_waveform_methods.py`

已完成的第一项中等规模 waveform-only 对照：

| family | 方法 | R@1 | R@5 | R@10 | median rank |
|---|---|---:|---:|---:|---:|
| SIS | InceptionTime bandpass, n=5000, ep25 | 0.0173 | 0.0507 | 0.0780 | 525 |

结论：继续堆 waveform 模型不是最高优先级；noisy LIGO 下单纯波形形态已经被噪声严重破坏。

## 当前建议

1. 论文/实验主线应从“pair-level waveform retrieval”改成“catalog-level ranking”。
2. noisy LIGO 场景推荐保留两套结果：
   - 最少辅助量：`delta_time + sky_sep`，用于证明少量真实可获得信息也能显著提升。
   - 当前最佳：`delta_time + sky + mass/spin/distance observable differences`，用于展示完整 catalog-level 检索能力。
3. waveform 模型仍可作为辅助或候选生成模块，但不应作为 noisy LIGO 的唯一排序依据。

## 主方案口径更新：辅助参数只使用两个

后续主实验和论文主结果只使用以下两个辅助参数：

1. `delta_time`：两个事件触发时间差，特征形式为 `log1p(|t_i - t_j|)`。
2. `sky_sep`：两个事件天空定位中心点的角距离，由 RA/DEC 计算得到。

扩展参数 v1/v2（质量、spin、距离等）只作为探索性 ablation 记录，不作为主方案。这样做的原因是这两个量在真实触发 catalog 中最直接、最稳定，也最容易解释；质量、spin、距离参数虽然能显著提高指标，但会引入参数估计误差、透镜放大导致的距离偏差等额外假设。

当前两参数 catalog-level 主结果如下：

| family | auxiliary features | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---:|---:|---:|---:|---:|
| SIS | `delta_time + sky_sep` | 0.4547 | 0.7270 | 0.8527 | 0.9963 | 2 |
| PM | `delta_time + sky_sep` | 0.9580 | 1.0000 | 1.0000 | 1.0000 | 1 |

对应脚本：`scripts/experiments/30_ligo_time_sky_catalog_aux.py`。

## ET noisy 同方案结果：只用 `delta_time + sky_sep`

脚本：`scripts/experiments/35_et_time_sky_catalog_aux.py`

数据：`/root/autodl-tmp/gw_et_10000_matchstyle_20260527_091859`

| family | 方法 | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---:|---:|---:|---:|---:|
| SIS | ET waveform baseline | 0.4333 | 0.6150 | 0.6830 | - | - |
| PM | ET waveform baseline | 0.2987 | 0.4500 | 0.5257 | - | - |
| SIS | ET catalog-level `delta_time + sky_sep` | 0.4163 | 0.7383 | 0.8450 | 0.9943 | 2 |
| PM | ET catalog-level `delta_time + sky_sep` | 0.9713 | 1.0000 | 1.0000 | 1.0000 | 1 |

结论：在 ET noisy 数据上，两参数 catalog-level 排序对 PM 提升非常明显；SIS 的 top1 与 waveform baseline 接近，但 top5/top10/top50 明显更好，说明该方法能把真实配对稳定压到很靠前的位置。

## 模型口径更新：主模型使用原 waveform 模型

后续表述中，主模型仍使用原本的 waveform Siamese encoder，例如 ET noisy baseline 中的 `InceptionTime + bandpass + NT-Xent`。该模型负责从波形中得到 embedding / waveform similarity。

`delta_time + sky_sep` 不作为替代主模型，而作为 catalog-level ranking 或 reranking 的辅助排序信息。也就是说：

- 原模型：处理 waveform，输出事件间波形相似度。
- 辅助参数：只使用 `delta_time + sky_sep`，用于在 catalog 层帮助排序候选。
- 不把质量、spin、距离等扩展参数作为主方案。
- 不把扩展参数 v1/v2 的高分结果作为主模型结果，只作为 ablation/探索记录。

因此论文/汇报时建议把方法写成：

`waveform Siamese retrieval + two-observable catalog-level reranking (delta_time, sky_sep)`。

ET noisy 原模型 baseline 与两参数 catalog/rerank 结果对比：

| family | waveform 原模型 R@1 | waveform 原模型 R@5 | 两参数 catalog/rerank R@1 | 两参数 catalog/rerank R@5 |
|---|---:|---:|---:|---:|
| SIS | 0.4333 | 0.6150 | 0.4163 | 0.7383 |
| PM | 0.2987 | 0.4500 | 0.9713 | 1.0000 |

LIGO noisy 原模型 baseline 与两参数 catalog/rerank 结果对比：

| family | waveform 原模型 R@1 | waveform 原模型 R@5 | 两参数 catalog/rerank R@1 | 两参数 catalog/rerank R@5 |
|---|---:|---:|---:|---:|
| SIS | 0.0103 | 0.0243 | 0.4547 | 0.7270 |
| PM | 0.0067 | 0.0170 | 0.9580 | 1.0000 |

## ET noisy：原 waveform 模型 + `delta_time + sky_sep` catalog-level reranking

脚本：`scripts/experiments/36_et_waveform_time_sky_rerank.py`

该实验保留原 waveform 模型作为主模型，使用已有 ET noisy waveform checkpoint 计算 `waveform_score` 和 `waveform_reciprocal_rank`，再只加入两个辅助参数 `delta_time + sky_sep` 做 catalog-level reranking。

| family | 方法 | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---:|---:|---:|---:|---:|
| SIS | waveform 原模型 baseline | 0.4333 | 0.6150 | 0.6830 | - | - |
| SIS | 原模型 + `delta_time + sky_sep` reranking | 0.8427 | 0.9457 | 0.9690 | 0.9977 | 1 |
| PM | waveform 原模型 baseline | 0.2987 | 0.4500 | 0.5257 | - | - |
| PM | 原模型 + `delta_time + sky_sep` reranking | 0.9897 | 0.9963 | 0.9970 | 0.9970 | 1 |

结论：使用原 waveform 模型并仅加入两个真实可获得辅助参数后，ET noisy 的 SIS 和 PM 都显著提升。该结果比“只用两个辅助参数、完全不使用 waveform score”的 catalog-level 排序更适合作为主结果。
