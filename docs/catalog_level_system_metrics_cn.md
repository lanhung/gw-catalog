# Catalog-Level 强透镜系统检索指标说明

## 为什么要加 catalog-level

之前的评估主要停留在两层：

- retrieval：单个事件的真实 partner 是否在 Top-K 里。
- pair-level：候选边或匹配边是否是正确的强透镜 pair。

这还不能完整回答“整个 catalog 里找出了哪些强透镜系统”。Catalog-level 评估把 pair candidates 进一步组织成系统级候选，用来衡量全目录发现能力、全局误报和系统污染情况。

## 当前实现

新增模块：

```text
matchgw/catalog.py
```

pipeline 中新增输出：

```text
val_catalog_tier1
val_catalog_tier12
test_catalog_tier1
test_catalog_tier12
```

如果开启 `export_candidates=True`，还会导出：

```text
val_catalog_systems_tier1.csv
val_catalog_systems_tier12.csv
test_catalog_systems_tier1.csv
test_catalog_systems_tier12.csv
val_catalog_tier1_summary.csv
val_catalog_tier12_summary.csv
test_catalog_tier1_summary.csv
test_catalog_tier12_summary.csv
```

## 方法

1. 先使用现有 pair-level calibrated candidates。
2. 按 `p_hat` 阈值筛选边：
   - `tier1`: `p_hat >= p_high`
   - `tier12`: `p_hat >= p_low`
3. 把事件作为节点、候选 pair 作为边构图。
4. 每个连通分量视作一个 catalog-level candidate lens system。
5. 用真实 `pair_id` 判断该系统是否恢复了真实强透镜系统、是否混入 unlensed 事件或多个真实系统。

## 新增核心指标

- `catalog_true_systems`：真实强透镜系统数量。
- `catalog_predicted_systems`：预测出的系统候选数量。
- `catalog_recovered_true_systems`：被任一预测系统完整覆盖的真实系统数量。
- `catalog_system_recall` / `catalog_completeness`：真实系统召回率。
- `catalog_system_precision`：预测系统中至少包含一个完整真实系统的比例。
- `catalog_system_f1`：system-level precision 和 recall 的 F1。
- `catalog_purity`：预测系统中完全纯净系统的比例。
- `catalog_false_alarm_systems`：不包含完整真实系统的预测系统数量。
- `catalog_false_alarm_rate_per_event`：按事件数归一化的系统级误报率。
- `catalog_merged_or_contaminated_systems`：包含真实系统但不纯净的系统数量。
- `catalog_impure_systems`：所有非纯净预测系统数量。
- `catalog_mean_system_size` / `catalog_max_system_size`：预测系统规模，用于发现过度合并问题。

## 如何解读 tier1 和 tier12

`tier1` 更严格，通常 precision/purity 更高，但 recall 较低。

`tier12` 更宽松，通常 recall/completeness 更高，但可能把多个系统或 unlensed 事件连成较大的 component，因此需要同时看：

- `catalog_purity`
- `catalog_merged_or_contaminated_systems`
- `catalog_mean_system_size`
- `catalog_max_system_size`

如果 `catalog_system_recall` 很高但 `catalog_purity` 很低，说明它适合做 follow-up 候选池，不适合直接作为最终系统发现结果。

## 和 pair-level 的区别

Pair-level 指标关心边是否正确：

```text
candidate_pair_recall
pair precision / recall / F1
```

Catalog-level 指标关心系统是否被发现：

```text
catalog_system_recall
catalog_system_precision
catalog_purity
catalog_false_alarm_systems
```

一个 catalog system 可以包含多条边，也可能包含多张像。当前数据主要是 doublet，因此 catalog-level 与 pair-level 会有相关性；但这个实现已经为后续 triplet/quadruplet 或更真实的 catalog 检索留下接口。
