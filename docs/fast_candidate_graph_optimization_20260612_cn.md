# Fast Candidate Graph Optimization 结果记录

生成时间：2026-06-12

## 实验目的

本次实验尝试优化 full-catalog 检索阶段，不再继续单纯重训波形编码器，而是在已有 fresh50 InceptionTime 编码器基础上测试候选图优化。

实验目录：

`runs/fast_direct_candidate_graph_fresh50_20260612/`

脚本：

`scripts/experiments/86_fast_direct_candidate_graph_fresh50.py`

## 方法

原计划尝试 HGB reranker 全矩阵候选图优化，但 9000 x 9000 全 catalog 上 `predict_proba` 太慢，因此切换为快速版：

1. 复用 fresh50 已训练波形编码器，不重新训练模型。
2. 使用三个可解释分数：
   - waveform similarity
   - trigger_time_obs 时间差分数
   - predicted sky_overlap
3. 在 validation full catalog 上选择融合权重。
4. 对 validation 最好的前 2 个融合配置尝试候选图特征：
   - reciprocal rank
   - mutual top50
   - mutual top100
   - hub penalty
5. 将 validation 选择出的配置用于 test full catalog。

## 关键结果

| 数据 | 方法 | R@1 | R@5 | R@10 | Top1% | Top10% |
|---|---|---:|---:|---:|---:|---:|
| ET noisy | fresh50 baseline waveform+time+pred sky | 0.3850 | 0.6017 | 0.6848 | 0.8547 | 0.9533 |
| ET noisy | direct fusion no graph | 0.6142 | 0.7803 | 0.8313 | 0.9325 | 0.9873 |
| ET noisy | direct fusion + hub graph | 0.6195 | 0.7845 | 0.8370 | 0.9340 | 0.9877 |
| LIGO noisy | fresh50 baseline waveform+time | 0.0532 | 0.1158 | 0.1622 | 0.4315 | 0.6820 |
| LIGO noisy | fresh50 baseline waveform+time+pred sky | 0.0455 | 0.0948 | 0.1388 | 0.4098 | 0.6872 |
| LIGO noisy | direct fusion no graph | 0.1653 | 0.4247 | 0.5322 | 0.7098 | 0.9158 |
| LIGO noisy | direct fusion + hub graph | 0.1660 | 0.4213 | 0.5338 | 0.7132 | 0.9195 |

## SIS / PM 分解

ET noisy 最佳配置：

`waveform_time_0p5__hub_0p5`

| 子集 | R@1 | R@5 | R@10 | Top1% |
|---|---:|---:|---:|---:|
| SIS | 0.4293 | 0.6717 | 0.7487 | 0.8900 |
| PM | 0.8097 | 0.8973 | 0.9253 | 0.9780 |

LIGO noisy 最佳配置：

`waveform_time_2p0__hub_0p5`

| 子集 | R@1 | R@5 | R@10 | Top1% |
|---|---:|---:|---:|---:|
| SIS | 0.0220 | 0.0920 | 0.1470 | 0.4263 |
| PM | 0.3100 | 0.7507 | 0.9207 | 1.0000 |

## 分析

这次提升主要来自 direct score fusion，而不是候选图项本身。

候选图项带来的增益较小：

- ET noisy：direct fusion no graph R@10 = 0.8313，加入 hub graph 后 R@10 = 0.8370，提升 0.0057。
- LIGO noisy：direct fusion no graph R@10 = 0.5322，加入 hub graph 后 R@10 = 0.5338，提升 0.0016。

但是 direct fusion 明显优于之前的 HGB reranker：

- ET noisy 从 0.6848 提升到 0.8370。
- LIGO noisy 从 0.1622 提升到 0.5338。

这说明当前 HGB reranker 在 noisy full catalog 中可能把波形、时间、sky 特征组合坏了；简单的 row-z 标准化分数融合反而更稳定。

## 重要限制

LIGO noisy 的 overall 提升很大，但主要来自 PM 子集：

- LIGO noisy PM R@10 达到 0.9207。
- LIGO noisy SIS R@10 只有 0.1470。

因此不能简单说 LIGO noisy 已经解决。当前方法主要改善了 overall 排名和 PM，SIS 仍然困难。

## 后续建议

1. 把 direct fusion 作为新的 noisy baseline，与 HGB reranker 并列比较。
2. 后续重点优化 LIGO noisy SIS，而不是只看 overall。
3. 候选图项目前增益较小，可以继续尝试更强的 graph hard negative 或 top-K 局部图特征。
4. predicted sky_overlap 在本轮最佳配置中没有被选中，说明当前 predicted sky 仍然不稳定。
