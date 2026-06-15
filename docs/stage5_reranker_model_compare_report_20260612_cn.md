# stage5_reranker_model_compare 实验报告

生成时间：2026-06-12

## 输出位置

| 项目 | 路径 |
| --- | ---: |
| 结果目录 | `runs/liao_realistic_p1_p2_rerank_20260612/stage5_reranker_model_compare` |
| 结果 CSV | `runs/liao_realistic_p1_p2_rerank_20260612/stage5_reranker_model_compare/stage5_reranker_model_compare_summary.csv` |

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
| ET | weighted_sum_stage4_lambdas | 0.7795 | 0.8823 | 0.9192 | 0.987 | 0.9972 | 0.9995 | 1 |  |
| ET | weighted_sum_val_selected_extensible | 0.8928 | 0.964 | 0.9805 | 0.9977 | 1 | 1 | 1 |  |
| ET | logistic_regression | 0.0065 | 0.015 | 0.0192 | 0.0585 | 0.1067 | 0.1505 | 3036 |  |
| ET | hgb | 0.5712 | 0.8127 | 0.8842 | 0.9503 | 0.9668 | 0.9733 | 1 |  |
| ET | mlp_tabular | 0.7083 | 0.8935 | 0.9343 | 0.9778 | 0.9817 | 0.9835 | 1 |  |
| ET | lightgbm | 0.5568 | 0.7723 | 0.864 | 0.957 | 0.9638 | 0.9703 | 1 |  |
| LIGO | weighted_sum_stage4_lambdas | 0.3767 | 0.6062 | 0.6763 | 0.8327 | 0.9433 | 0.9827 | 3 |  |
| LIGO | weighted_sum_val_selected_extensible | 0.6035 | 0.7842 | 0.8393 | 0.9682 | 0.9982 | 0.9998 | 1 |  |
| LIGO | logistic_regression | 0.183 | 0.183 | 0.183 | 0.184 | 0.2732 | 0.3852 | 1518 |  |
| LIGO | hgb | 0.534 | 0.7152 | 0.7728 | 0.9315 | 0.9623 | 0.9705 | 1 |  |
| LIGO | mlp_tabular | 0.4323 | 0.5702 | 0.6287 | 0.7778 | 0.8547 | 0.8883 | 3 |  |
| LIGO | lightgbm | 0.6455 | 0.746 | 0.7958 | 0.9403 | 0.9693 | 0.977 | 1 |  |

## SIS / PM 分解

| detector | subset | variant | R@1 | R@5 | R@10 | Top1% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | SIS | weighted_sum_stage4_lambdas | 0.6643 | 0.8073 | 0.86 | 0.9743 | 1 |
| ET | PM | weighted_sum_stage4_lambdas | 0.8947 | 0.9573 | 0.9783 | 0.9997 | 1 |
| ET | SIS | weighted_sum_val_selected_extensible | 0.828 | 0.9367 | 0.964 | 0.9953 | 1 |
| ET | PM | weighted_sum_val_selected_extensible | 0.9577 | 0.9913 | 0.997 | 1 | 1 |
| ET | SIS | logistic_regression | 0.0013 | 0.0037 | 0.005 | 0.021 | 4156.5 |
| ET | PM | logistic_regression | 0.0117 | 0.0263 | 0.0333 | 0.096 | 2140 |
| ET | SIS | hgb | 0.3287 | 0.6967 | 0.818 | 0.9173 | 3 |
| ET | PM | hgb | 0.8137 | 0.9287 | 0.9503 | 0.9833 | 1 |
| ET | SIS | mlp_tabular | 0.527 | 0.8077 | 0.878 | 0.9563 | 1 |
| ET | PM | mlp_tabular | 0.8897 | 0.9793 | 0.9907 | 0.9993 | 1 |
| ET | SIS | lightgbm | 0.277 | 0.625 | 0.7863 | 0.9273 | 4 |
| ET | PM | lightgbm | 0.8367 | 0.9197 | 0.9417 | 0.9867 | 1 |
| LIGO | SIS | weighted_sum_stage4_lambdas | 0.118 | 0.2783 | 0.3723 | 0.6653 | 27 |
| LIGO | PM | weighted_sum_stage4_lambdas | 0.6353 | 0.934 | 0.9803 | 1 | 1 |
| LIGO | SIS | weighted_sum_val_selected_extensible | 0.3787 | 0.5937 | 0.685 | 0.9363 | 3 |
| LIGO | PM | weighted_sum_val_selected_extensible | 0.8283 | 0.9747 | 0.9937 | 1 | 1 |
| LIGO | SIS | logistic_regression | 0.1173 | 0.1173 | 0.1173 | 0.118 | 2521 |
| LIGO | PM | logistic_regression | 0.2487 | 0.2487 | 0.2487 | 0.25 | 921.5 |
| LIGO | SIS | hgb | 0.3117 | 0.4993 | 0.601 | 0.8987 | 6 |
| LIGO | PM | hgb | 0.7563 | 0.931 | 0.9447 | 0.9643 | 1 |
| LIGO | SIS | mlp_tabular | 0.3313 | 0.4807 | 0.545 | 0.7093 | 7 |
| LIGO | PM | mlp_tabular | 0.5333 | 0.6597 | 0.7123 | 0.8463 | 1 |
| LIGO | SIS | lightgbm | 0.4793 | 0.5893 | 0.6597 | 0.9077 | 2 |
| LIGO | PM | lightgbm | 0.8117 | 0.9027 | 0.932 | 0.973 | 1 |