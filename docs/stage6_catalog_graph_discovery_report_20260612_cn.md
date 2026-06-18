# stage6_catalog_graph_discovery 实验报告

生成时间：2026-06-12

> **投稿口径更新（2026-06-18）**：本报告保留为历史记录。下表中的
> `system_precision` 是旧的宽松 connected-component 指标；giant component
> 会被错误地评为高 precision，因此不能再用于论文主表或摘要结论。投稿时应
> 改用 `scripts/server_experiments/exp3_graph.py` 重新计算的 exact-match
> precision/recall、B-cubed precision/recall、over-merge、fragmentation、
> singleton precision/recall 和 maximum-weight matching 对照。

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage6_catalog_graph_discovery` |
| 结果 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage6_catalog_graph_discovery/stage6_catalog_graph_discovery_summary.csv` |

## 实验说明

- Stage6 不再只看 pair-level R@K，而是把 pair scorer 生成的高分边转成 catalog graph。
- 每个 query 连接 top-k candidate，形成无向图连通分量，用于近似 catalog-level lensed-system discovery。
- 当前实现比较 waveform_only、weighted_sum_best_features 和 HGB 三种 pair scorer。
- system_recall 表示真实双像是否落在同一连通分量；system_precision 表示预测连通分量中有多少包含真实双像。
- 上述 system_precision 是宽松定义，不要求 predicted component 与真实双像系统 exact match；对于 top-k connected components 过度合并的情形会显著高估性能。

## 投稿应使用的 graph 指标

新版脚本：

```bash
python scripts/server_experiments/exp3_graph.py
```

应报告的列：

| 指标 | 含义 |
| --- | --- |
| `exact_precision` | 预测 multi-component 中，完全等于一个真实双像系统的比例 |
| `exact_recall` | 真实双像系统被 exact component 恢复的比例 |
| `bcubed_precision` / `bcubed_recall` | lensed events 上的 B-cubed component quality |
| `overmerge_rate` | multi-component 混入多个真实系统或 unlensed contaminants 的比例 |
| `fragmentation_rate` | 真实双像系统被拆到多个 predicted components 的比例 |
| `singleton_precision` / `singleton_recall` | unlensed singleton 识别质量 |
| `max_component_size` | 检查 giant component 过度合并 |

结论口径：catalog graph 部分应写成 retrieval/triage 的结构化分组尝试；当前结果不能声称已经高精度重建完整 lens systems。maximum-weight matching 是更合理的 doublet-optimal 后处理，但 exact precision/recall 仍应作为限制报告。

2026-06-18 复跑 `exp3_graph.py`（3 seeds，mean）得到的关键对照；CSV 已归档到
`runs/graph_metrics_exact_20260618/`：

| method | exact P | exact R | B3 P | B3 R | overmerge | fragmentation | singleton P | singleton R | max comp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CC top-1 | 0.184 | 0.226 | 0.776 | 0.867 | 0.816 | 0.266 | NA | 0.000 | 13.3 |
| CC top-5 giant | 0.000 | 0.000 | 0.002 | 1.000 | 1.000 | 0.000 | NA | 0.000 | 1851 |
| MWM tau q0.995 | 0.163 | 0.342 | 0.879 | 0.671 | 0.837 | 0.658 | 0.768 | 0.019 | 2 |
| MWM tau q0.999 | 0.191 | 0.328 | 0.909 | 0.664 | 0.809 | 0.672 | 0.585 | 0.222 | 2 |

解释：CC top-5 的 B3 recall 为 1.000 只是因为 giant component 覆盖了所有 lensed events；exact precision/recall 与 overmerge 才揭示它不可用。MWM 将最大组件限制为 2，但 exact P/R 仍不高，因此应定位为候选分组后处理，而非完整 lens-system reconstruction。

## Catalog Graph 结果

| detector | pair_scorer | topk_edges | true_systems | pred_components | system_precision | system_recall | purity | mean_size |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | waveform_only | 1 | 2999 | 2364 | 0.0097 | 0.0087 | 0.6573 | 3.2026 |
| LIGO | waveform_only | 2 | 2999 | 82 | 0.0122 | 0.8123 | 0.5056 | 100.3537 |
| LIGO | waveform_only | 5 | 2999 | 1 | 1 | 0.9667 | 0.6693 | 8815 |
| LIGO | weighted_sum_best_features | 1 | 2999 | 2723 | 0.4293 | 0.4025 | 0.7076 | 2.9416 |
| LIGO | weighted_sum_best_features | 2 | 2999 | 183 | 0.765 | 0.7913 | 0.6398 | 46.8852 |
| LIGO | weighted_sum_best_features | 5 | 2999 | 1 | 1 | 0.999 | 0.6705 | 8943 |
| LIGO | hgb | 1 | 2999 | 1816 | 0.3227 | 0.2114 | 0.702 | 4.1151 |
| LIGO | hgb | 2 | 2999 | 20 | 0.3 | 0.8743 | 0.4816 | 404.55 |
| LIGO | hgb | 5 | 2999 | 1 | 1 | 0.9607 | 0.6749 | 8716 |
