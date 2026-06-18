# 候选图优化实验报告

生成时间：2026-06-12

## 1. 实验目的

本次实验针对 full-catalog ranking 中 noisy 场景效果不稳定的问题，尝试在已有 fresh50 InceptionTime 波形编码器基础上优化检索与候选图排序。

核心目标：

1. 直接融合 waveform、trigger_time_obs、predicted sky_overlap 分数是否比 HGB reranker 更稳定。
2. 加入 reciprocal rank、mutual top-K、hub penalty 等候选图结构特征是否能进一步提升结果。
3. 分析 ET noisy 和 LIGO noisy 的提升来自整体方法，还是来自 SIS/PM 某个子集。

## 2. 代码与结果位置

| 项目 | 路径 |
| --- | ---: |
| 实验脚本 | `scripts/experiments/86_fast_direct_candidate_graph_fresh50.py` |
| 结果目录 | `runs/fast_direct_candidate_graph_fresh50_20260612` |
| 结果 CSV | `runs/fast_direct_candidate_graph_fresh50_20260612/fast_candidate_graph_summary.csv` |
| 运行日志 | `runs/fast_direct_candidate_graph_fresh50_20260612/run.log` |

## 3. 实验数据与评估设置

本实验只跑 noisy 场景，因为 pure 场景在 fresh50 full-catalog 实验中已经接近饱和。

| Detector | Mode | Query total | Catalog total | SIS lensed images | PM lensed images | SIS unlensed | PM unlensed | Top1% k | Top5% k | Top10% k |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | noisy | 6000 | 9000 | 3000 | 3000 | 1500 | 1500 | 90 | 450 | 900 |
| LIGO | noisy | 6000 | 9000 | 3000 | 3000 | 1500 | 1500 | 90 | 450 | 900 |

每个 detector/mode 的 full catalog 包含 9000 个 test 事件。Top1%/Top5%/Top10% 分别对应 top90/top450/top900。

## 4. 方法设计

### 4.1 第一版 HGB 全矩阵候选图

最初尝试复用 HGB reranker，对 9000 x 9000 full catalog 中所有 pair 计算 `predict_proba`，再基于全矩阵构造 reciprocal rank、mutual top-K、hub penalty。该方案因全矩阵 HGB 预测太慢被停止，脚本保留在：

`scripts/experiments/85_candidate_graph_rerank_fresh50.py`

### 4.2 当前快速候选图方案

最终采用快速可解释分数融合：

```text
score = w_waveform * z_row(waveform_score)
      + w_time     * z_row(time_score)
      + w_predsky  * z_row(predicted_sky_overlap)
```

候选图项：

```text
graph_score = base_score
            + alpha * reciprocal_rank_score
            + gamma50 * mutual_top50
            + gamma100 * mutual_top100
            - beta * hub_penalty
```

含义：

- `reciprocal_rank_score`：如果 i 把 j 排得靠前，且 j 也把 i 排得靠前，则加分。
- `mutual_top50/top100`：如果两事件互相进入 top50/top100，则加分。
- `hub_penalty`：如果某个候选被大量 query 排得很靠前，可能是噪声 hub，对其降权。

## 5. Validation 选择策略

为了避免直接在 test 上调参，本实验先在 validation full catalog 上选择配置，再应用到 test。候选融合权重包括 waveform only、time only、waveform+不同权重 time、以及 waveform+time+predicted sky。然后只对 validation 最好的前 2 个融合配置尝试图参数。

## 6. Overall 结果对比

| Detector | 方法 | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | fresh50 baseline: waveform_only | 0.3082 | 0.4842 | 0.5648 | 0.7643 | 0.87 | 0.9043 | 6 |
| ET | fresh50 baseline: time_only | 0.1365 | 0.4117 | 0.5308 | 0.6778 | 0.8387 | 0.9093 | 9 |
| ET | fresh50 baseline: waveform_plus_time | 0.3588 | 0.5932 | 0.6747 | 0.8497 | 0.9197 | 0.9493 | 4 |
| ET | fresh50 baseline: waveform_plus_time_plus_predicted_sky_overlap | 0.385 | 0.6017 | 0.6848 | 0.8547 | 0.9245 | 0.9533 | 3 |
| ET | fast direct fusion + candidate graph: waveform_time_0p5__hub_0p5 | 0.6195 | 0.7845 | 0.837 | 0.934 | 0.9772 | 0.9877 | 1 |
| LIGO | fresh50 baseline: waveform_only | 0.0052 | 0.0193 | 0.0263 | 0.0887 | 0.2158 | 0.3065 | 2513.5 |
| LIGO | fresh50 baseline: time_only | 0.1365 | 0.4117 | 0.5308 | 0.6778 | 0.8387 | 0.9093 | 9 |
| LIGO | fresh50 baseline: waveform_plus_time | 0.0532 | 0.1158 | 0.1622 | 0.4315 | 0.5833 | 0.682 | 187 |
| LIGO | fresh50 baseline: waveform_plus_time_plus_predicted_sky_overlap | 0.0455 | 0.0948 | 0.1388 | 0.4098 | 0.6062 | 0.6872 | 159 |
| LIGO | fast direct fusion + candidate graph: waveform_time_2p0__hub_0p5 | 0.166 | 0.4213 | 0.5338 | 0.7132 | 0.8593 | 0.9195 | 8 |

## 7. 最佳配置

| Detector | 最佳 variant | w_waveform | w_time | w_predsky | graph_alpha | graph_gamma50 | graph_gamma100 | graph_beta | Val R@10 | Test R@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | waveform_time_0p5__hub_0p5 | 1 | 0.5 | 0 | 0.5 | 0.5 | 0.25 | 0.5 | 0.8552 | 0.837 |
| LIGO | waveform_time_2p0__hub_0p5 | 1 | 2 | 0 | 0.5 | 0.5 | 0.25 | 0.5 | 0.5365 | 0.5338 |

两个 detector 的最佳配置都没有使用 predicted sky_overlap，说明当前 predicted sky_overlap 在 noisy 场景下仍然不稳定。

## 8. SIS / PM 分解

### ET noisy: waveform_time_0p5__hub_0p5

| Subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| overall | 0.6195 | 0.7845 | 0.837 | 0.934 | 0.9772 | 0.9877 | 1 |
| SIS | 0.4293 | 0.6717 | 0.7487 | 0.89 | 0.9593 | 0.977 | 2 |
| PM | 0.8097 | 0.8973 | 0.9253 | 0.978 | 0.995 | 0.9983 | 1 |
| macro | 0.6195 | 0.7845 | 0.837 | 0.934 | 0.9772 | 0.9877 | 1.5 |

### LIGO noisy: waveform_time_2p0__hub_0p5

| Subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| overall | 0.166 | 0.4213 | 0.5338 | 0.7132 | 0.8593 | 0.9195 | 8 |
| SIS | 0.022 | 0.092 | 0.147 | 0.4263 | 0.7187 | 0.839 | 133 |
| PM | 0.31 | 0.7507 | 0.9207 | 1 | 1 | 1 | 3 |
| macro | 0.166 | 0.4213 | 0.5338 | 0.7132 | 0.8593 | 0.9195 | 68 |

## 9. 图结构带来的实际增益

| Detector | No graph R@10 | Graph R@10 | Delta R@10 | No graph Top1% | Graph Top1% | Delta Top1% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | 0.8313 | 0.837 | 0.0057 | 0.9325 | 0.934 | 0.0015 |
| LIGO | 0.5322 | 0.5338 | 0.0017 | 0.7098 | 0.7132 | 0.0033 |

图结构项有增益，但增益较小。主要提升来自 direct score fusion，而不是 graph term 本身。

## 10. 主要结论

1. 对 noisy full catalog，直接分数融合明显优于此前 HGB reranker。
2. ET noisy overall R@10 从 fresh50 baseline 的 0.6848 提升到 0.8370。
3. LIGO noisy overall R@10 从 fresh50 waveform+time 的 0.1622 提升到 0.5338。
4. 但是 LIGO noisy 的提升主要来自 PM 子集，SIS 仍然困难：最佳配置下 LIGO noisy SIS R@10 只有 0.1470，而 PM R@10 为 0.9207。
5. 当前最佳配置没有使用 predicted sky_overlap，说明机器学习 sky-map 预测在 noisy 场景中还不能稳定提供有效排序信息。
6. candidate graph 的 reciprocal/mutual/hub 项只带来小幅提升，说明图结构方向有价值，但当前实现还比较浅。

## 11. 后续优化方向

1. 将 direct score fusion 作为新的 noisy baseline，后续实验不要只依赖 HGB reranker。
2. 对 LIGO noisy SIS 单独优化，因为 overall 已经被 PM 拉高，不能代表 SIS 问题解决。
3. 继续改进 sky-map 预测质量，尤其要看 predicted sky_overlap 与 true sky_overlap 的 pair-level 误差。
4. 候选图方向可以继续做 top-K 局部图，而不是 full 9000x9000 全矩阵，这样可以更快加入更复杂的图特征。
5. 可以尝试 graph hard negative mining：选择互相排名高、时间接近、但非同源的 pair 作为更难负样本。
