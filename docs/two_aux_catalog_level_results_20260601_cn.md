# 两个辅助参数与 Catalog-level Ranking 结果汇总

日期：2026-06-01

## 1. 只添加两个辅助参数的方案

方案名称：**Waveform + Time-Sky Catalog-level Reranking**

该方案保留原 waveform 模型作为主模型，在 catalog-level reranking 阶段只添加两个辅助参数：

- `delta_time`: `log1p(|t_i - t_j|)`
- `sky_sep`: 两个事件天空位置 RA/DEC 的角距离

最终 reranking 使用的特征为：

```text
waveform_score
waveform_reciprocal_rank
delta_time
sky_sep
```

也就是说，这个方案是：

```text
原 waveform 模型 + 两个辅助参数 + catalog-level reranking
```

### 全量结果

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

结果文件：

```text
runs/all_waveform_time_sky_rerank_20260601/summary.csv
```

脚本：

```text
scripts/experiments/37_all_waveform_time_sky_rerank.py
```

## 2. 只使用两个辅助参数的 Catalog-level Ranking 方案

该方案不使用 waveform score，只用两个辅助参数直接对整个 catalog 排序：

```text
delta_time
sky_sep
```

也就是说，这个方案是：

```text
仅 delta_time + sky_sep 的 catalog-level ranking
```

### LIGO noisy 结果

| detector | data | family | features | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---|---|---:|---:|---:|---:|---:|
| LIGO | noisy | SIS | `delta_time + sky_sep` | 0.4547 | 0.7270 | 0.8527 | 0.9963 | 2 |
| LIGO | noisy | PM | `delta_time + sky_sep` | 0.9580 | 1.0000 | 1.0000 | 1.0000 | 1 |

结果文件：

```text
runs/ligo_noisy_time_sky_catalog_aux_20260601/summary.csv
```

脚本：

```text
scripts/experiments/30_ligo_time_sky_catalog_aux.py
```

### ET noisy 结果

| detector | data | family | features | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---|---|---:|---:|---:|---:|---:|
| ET | noisy | SIS | `delta_time + sky_sep` | 0.4163 | 0.7383 | 0.8450 | 0.9943 | 2 |
| ET | noisy | PM | `delta_time + sky_sep` | 0.9713 | 1.0000 | 1.0000 | 1.0000 | 1 |

结果文件：

```text
runs/et_noisy_time_sky_catalog_aux_20260601/summary.csv
```

脚本：

```text
scripts/experiments/35_et_time_sky_catalog_aux.py
```

## 3. 两类结果的区别

| 方案 | 是否使用 waveform 原模型 | 是否使用 `delta_time + sky_sep` | 排序范围 | 适合作为 |
|---|---|---|---|---|
| 原 waveform baseline | 是 | 否 | catalog | baseline |
| 仅两个辅助参数 catalog-level ranking | 否 | 是 | catalog | 辅助参数有效性验证 |
| 原 waveform + 两个辅助参数 reranking | 是 | 是 | catalog | 当前主方案 |

## 4. 结论

1. 只用 `delta_time + sky_sep` 的 catalog-level ranking 已经能显著提升 noisy 场景，尤其 PM。
2. 将原 waveform score/rank 与 `delta_time + sky_sep` 结合后，ET noisy SIS 从 0.4163 提升到 0.8500，说明 waveform 信息对 SIS 仍有明显帮助。
3. 当前主结果建议使用：

```text
原 waveform 模型 + delta_time + sky_sep 的 catalog-level reranking
```

4. 单独的 `delta_time + sky_sep` catalog-level ranking 可作为 ablation，用来证明两个辅助参数本身具有较强区分能力。
