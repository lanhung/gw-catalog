# 10% 透镜 / 90% 非透镜 Catalog 压力测试结果

日期：2026-06-01

## 1. 实验目的

原始评估 catalog 中透镜事件比例较高，不够贴近真实观测场景。为了更接近真实情况，本实验将 catalog 调整为：

```text
约 10% 透镜事件 + 约 90% 非透镜事件
```

用于测试当前主方案在更稀疏的强透镜候选场景下是否仍然有效。

## 2. 方法

使用当前主方案：

```text
原 waveform 模型 + delta_time + sky_sep catalog-level reranking
```

特征仍然只有：

```text
waveform_score
waveform_reciprocal_rank
delta_time
sky_sep
```

没有使用质量、spin、距离等扩展参数。

## 3. Catalog 抽样设置

每个 test catalog 中：

- 透镜源对数：83 对
- 透镜事件数：166 个
- 非透镜事件数：1500 个
- 总事件数：1666 个
- 透镜事件比例：0.09964

每组实验跑 10 个随机种子，表中报告 mean ± std。

## 4. 结果

| detector | data | family | waveform R@1 | waveform R@5 | rerank R@1 | rerank R@5 | rerank R@10 | rerank R@50 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| ET | pure | SIS | 0.9494 ± 0.0262 | 0.9855 ± 0.0114 | 0.9837 ± 0.0156 | 0.9928 ± 0.0089 | 0.9940 ± 0.0085 | 0.9952 ± 0.0084 |
| ET | pure | PM | 0.9476 ± 0.0220 | 0.9825 ± 0.0112 | 0.9994 ± 0.0019 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| ET | noisy | SIS | 0.5060 ± 0.0515 | 0.6639 ± 0.0547 | 0.8645 ± 0.0353 | 0.9482 ± 0.0254 | 0.9639 ± 0.0158 | 0.9759 ± 0.0120 |
| ET | noisy | PM | 0.3687 ± 0.0501 | 0.5367 ± 0.0637 | 0.9940 ± 0.0075 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| LIGO | pure | SIS | 0.9639 ± 0.0150 | 0.9880 ± 0.0133 | 0.9880 ± 0.0075 | 0.9976 ± 0.0042 | 0.9976 ± 0.0042 | 0.9982 ± 0.0041 |
| LIGO | pure | PM | 0.9687 ± 0.0165 | 0.9880 ± 0.0120 | 0.9994 ± 0.0019 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| LIGO | noisy | SIS | 0.0440 ± 0.0156 | 0.0886 ± 0.0275 | 0.4994 ± 0.0588 | 0.8380 ± 0.0233 | 0.9289 ± 0.0223 | 0.9669 ± 0.0169 |
| LIGO | noisy | PM | 0.0205 ± 0.0103 | 0.0620 ± 0.0188 | 0.9747 ± 0.0192 | 0.9988 ± 0.0025 | 0.9988 ± 0.0025 | 0.9988 ± 0.0025 |

## 5. 结果解读

1. 在 10% 透镜比例下，reranking 仍然显著优于原 waveform 排序。
2. ET noisy SIS 从 waveform R@1=0.5060 提升到 rerank R@1=0.8645。
3. ET noisy PM 从 waveform R@1=0.3687 提升到 rerank R@1=0.9940。
4. LIGO noisy SIS 从 waveform R@1=0.0440 提升到 rerank R@1=0.4994，同时 R@5=0.8380、R@10=0.9289，说明虽然 top1 仍有混淆，但真实配对大多进入前 5/10。
5. LIGO noisy PM 从 waveform R@1=0.0205 提升到 rerank R@1=0.9747。

## 6. 注意事项

该实验每个随机抽样只有 83 个透镜源对，即 166 个有真实 partner 的透镜事件，因此结果会比全量评估有更明显随机波动。表中已使用 10 个随机种子报告均值和标准差。

此外，当前 `sky_sep` 仍基于 RA/DEC 点估计。真实场景中建议进一步用 sky map overlap 或 sky localization posterior overlap 替代。

## 7. 文件位置

脚本：

```text
scripts/experiments/38_rerank_lens_fraction_stress.py
```

结果：

```text
runs/rerank_lens_fraction_10pct_20260601/trials.csv
runs/rerank_lens_fraction_10pct_20260601/summary.csv
```

日志：

```text
logs/rerank_lens_fraction_10pct_20260601.log
```
