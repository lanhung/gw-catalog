# stage5_reranker_model_compare 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage5_reranker_model_compare` |
| 结果 CSV | `runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage5_reranker_model_compare/stage5_reranker_model_compare_summary.csv` |

## 实验说明

- Stage5 固定同一组可扩展 pair features，只比较 rerank 模型。
- 特征为 waveform、waveform reciprocal rank、waveform margin、Liao time LR、sky norm sep、observed sky log-overlap、amp-time 2D LR。
- weighted_sum_val_selected_extensible 使用统一辅助参数模块，并在 validation full catalog 上自动搜索加权修正。
- 模型比较默认包括 weighted-sum、logistic regression、HGB、MLP，以及环境中可用的 LightGBM；RandomForest/ExtraTrees 不作为 full-catalog 默认项，避免 O(N^2) 推理成本过高。
- 监督 reranker 在 validation catalog 上用正样本加 hard negatives 训练，然后在 test full catalog 上逐块推理。
- 该阶段用于回答：固定物理特征后，线性/非线性表格 reranker 是否优于可解释 weighted-sum。

## Overall 结果

| detector | variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank | lambda |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | weighted_sum_stage4_lambdas | 0.3687 | 0.6015 | 0.6687 | 0.8338 | 0.9488 | 0.9823 | 3 |  |
| LIGO | weighted_sum_val_selected_extensible | 0.5455 | 0.7495 | 0.8137 | 0.963 | 0.9987 | 0.9997 | 1 |  |
| LIGO | logistic_regression | 0.0815 | 0.0833 | 0.0928 | 0.2072 | 0.3895 | 0.496 | 923 |  |
| LIGO | hgb | 0.3117 | 0.5413 | 0.6748 | 0.9392 | 0.9722 | 0.9783 | 4 |  |
| LIGO | mlp_tabular | 0.4473 | 0.609 | 0.6683 | 0.8577 | 0.9255 | 0.941 | 2 |  |
| LIGO | lightgbm | 0.4607 | 0.7013 | 0.7522 | 0.8947 | 0.9738 | 0.982 | 2 |  |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGO | SIS | weighted_sum_stage4_lambdas | 0.113 | 0.273 | 0.355 | 0.6677 | 29 |
| LIGO | PM | weighted_sum_stage4_lambdas | 0.6243 | 0.93 | 0.9823 | 1 | 1 |
| LIGO | SIS | weighted_sum_val_selected_extensible | 0.3213 | 0.54 | 0.6443 | 0.9263 | 4 |
| LIGO | PM | weighted_sum_val_selected_extensible | 0.7697 | 0.959 | 0.983 | 0.9997 | 1 |
| LIGO | SIS | logistic_regression | 0.0397 | 0.0413 | 0.048 | 0.129 | 1845 |
| LIGO | PM | logistic_regression | 0.1233 | 0.1253 | 0.1377 | 0.2853 | 423.5 |
| LIGO | SIS | hgb | 0.2517 | 0.4667 | 0.586 | 0.908 | 7 |
| LIGO | PM | hgb | 0.3717 | 0.616 | 0.7637 | 0.9703 | 3 |
| LIGO | SIS | mlp_tabular | 0.182 | 0.3867 | 0.4857 | 0.783 | 12 |
| LIGO | PM | mlp_tabular | 0.7127 | 0.8313 | 0.851 | 0.9323 | 1 |
| LIGO | SIS | lightgbm | 0.223 | 0.4783 | 0.5663 | 0.8377 | 6 |
| LIGO | PM | lightgbm | 0.6983 | 0.9243 | 0.938 | 0.9517 | 1 |