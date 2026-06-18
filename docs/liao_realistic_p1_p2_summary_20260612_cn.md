# Liao realistic rerank P1/P2 实验总结

生成时间：2026-06-12

## 实验范围

本轮按 `gw_catalog_liao_realistic_rerank_plan.md` 继续完成 P1/P2：

- Stage4：在 `waveform + Liao time LR + observed sky log-overlap` 基础上加入 SNR/amplitude prior。
- Stage5：固定同一组特征，比较 `weighted-sum / logistic / HGB / LightGBM` reranker。
- Stage6：把 pair scorer 转成 catalog graph，评估 connected-component system discovery。

Stage5 的 weighted-sum 不重新搜索权重，而是复用 Stage4 的 validation-selected lambda，保证 Stage5 只比较 reranker 模型。

## 输出位置

| 项目 | 路径 |
|---|---|
| 脚本 | `scripts/experiments/88_liao_realistic_p1_p2_rerank.py` |
| 结果目录 | `runs/liao_realistic_p1_p2_rerank_20260612/` |
| Stage4 文档 | `docs/stage4_snr_amplitude_prior_report_20260612_cn.md` |
| Stage5 文档 | `docs/stage5_reranker_model_compare_report_20260612_cn.md` |
| Stage6 文档 | `docs/stage6_catalog_graph_discovery_report_20260612_cn.md` |

## Stage4：SNR / amplitude prior

| detector | variant | R@1 | R@5 | R@10 | Top1% | median rank |
|---|---|---:|---:|---:|---:|---:|
| ET | waveform + time LR + sky overlap | 0.7800 | 0.8833 | 0.9187 | 0.9862 | 1 |
| ET | + raw SNR ratio | 0.7820 | 0.8877 | 0.9210 | 0.9850 | 1 |
| ET | + amp-time 2D LR | 0.7800 | 0.8833 | 0.9187 | 0.9862 | 1 |
| LIGO | waveform + time LR + sky overlap | 0.3782 | 0.6048 | 0.6718 | 0.8382 | 3 |
| LIGO | + raw SNR ratio | 0.3853 | 0.6075 | 0.6667 | 0.8287 | 3 |
| LIGO | + amp-time 2D LR | 0.3777 | 0.6070 | 0.6772 | 0.8312 | 3 |

结论：SNR/amplitude prior 的增益较小。ET 上 raw SNR ratio 有轻微提升；LIGO 上 amp-time 2D LR 对 R@10 有小幅提升，但不是主要提升来源。

## Stage5：reranker 模型比较

| detector | reranker | R@1 | R@5 | R@10 | Top1% | median rank |
|---|---|---:|---:|---:|---:|---:|
| ET | weighted-sum | 0.7795 | 0.8823 | 0.9192 | 0.9870 | 1 |
| ET | logistic regression | 0.0037 | 0.0138 | 0.0198 | 0.0643 | 2633.5 |
| ET | HGB | 0.5097 | 0.6793 | 0.7228 | 0.8323 | 1 |
| ET | LightGBM | 0.5233 | 0.7182 | 0.7570 | 0.8593 | 1 |
| LIGO | weighted-sum | 0.3767 | 0.6062 | 0.6763 | 0.8327 | 3 |
| LIGO | logistic regression | 0.1737 | 0.1737 | 0.1737 | 0.1737 | 2221 |
| LIGO | HGB | 0.2790 | 0.4550 | 0.5053 | 0.6598 | 10 |
| LIGO | LightGBM | 0.3218 | 0.4198 | 0.4598 | 0.5813 | 19 |

结论：当前 full-catalog 排序下，weighted-sum 明显优于监督 reranker。监督模型可能受训练负样本采样、类别不平衡、概率校准目标与 ranking 目标不一致影响。论文主表应保留 weighted-sum 作为主方法，HGB/LightGBM 作为模型对比或补充实验。

## Stage6：catalog graph discovery

| detector | scorer | topk edges | system precision | system recall | purity | mean component size |
|---|---|---:|---:|---:|---:|---:|
| ET | waveform only | 1 | 0.4100 | 0.3631 | 0.6970 | 3.05 |
| ET | weighted-sum | 1 | 0.7565 | 0.8123 | 0.7666 | 2.58 |
| ET | HGB | 1 | 0.6421 | 0.5752 | 0.7487 | 3.20 |
| LIGO | waveform only | 1 | 0.0128 | 0.0113 | 0.6598 | 3.20 |
| LIGO | weighted-sum | 1 | 0.4439 | 0.4161 | 0.7019 | 2.95 |
| LIGO | HGB | 1 | 0.4838 | 0.3628 | 0.7102 | 3.66 |

top-k=2 或 5 的 recall 会明显升高，但会产生很大的连通分量，尤其 top-k=5 基本合并成单个大分量，不适合作为最终 catalog-level 发现结果。论文里更建议重点报告 topk_edges=1，或后续增加 edge threshold / mutual-top-k / component pruning。

## 当前判断

1. P1 中 SNR/amplitude prior 不是主要增益来源，只能作为小幅补充。
2. P2 中监督 reranker 当前不如 weighted-sum，说明简单 pair-level 分类目标不能直接替代 full-catalog ranking。
3. Catalog graph 结果显示 weighted-sum 在 ET 和 LIGO 上都显著优于 waveform-only，尤其 LIGO 从几乎不可用提升到可检索。
4. 下一步更值得做的是 graph 后处理：mutual-top-k、edge threshold、component size pruning，而不是继续堆更复杂的表格 reranker。
