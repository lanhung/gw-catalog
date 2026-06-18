# stage6_catalog_graph_discovery 实验报告

生成时间：2026-06-12

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