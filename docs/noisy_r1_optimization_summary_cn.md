# Noisy R@1 优化记录汇总

目标：在不使用物理辅助参数的前提下，优化 noisy 检索 R@1，目标值 0.7。

## 当前最佳结果

| 排名 | family | 方法 | noisy R@1 | R@5 | R@10 | R@50/候选召回 | 结论 |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | SIS | score ensemble + cross-encoder 小权重混合 | 0.4657 | 0.6373 | 0.7047 | 0.8190 | 当前最高，但提升很小 |
| 2 | SIS | score ensemble + waveform reranker | 0.4627 | 0.6337 | 0.7030 | 0.8197 | 浅层波形特征重排略有提升 |
| 3 | SIS | score ensemble | 0.4597 | - | 0.7017 | - | 最稳定 baseline |
| 4 | PM | score ensemble + waveform reranker | 0.3683 | 0.5403 | 0.6120 | 0.7530 | PM 也仅小幅提升 |
| 5 | PM | score ensemble | 0.3593 | - | 0.6030 | - | PM baseline |

## 已尝试优化

| 方向 | 修改/实验 | 结果 | 判断 |
|---|---|---|---|
| 多模型融合 | InceptionTime、InceptionAttn、GatedTCN score ensemble | SIS R@1=0.4597，PM R@1=0.3593 | 目前最稳基础方案 |
| 浅层重排 | HGB reranker，使用 score/rank/margin 特征 | SIS R@1=0.4610 | 基本持平 |
| waveform-only 重排 | 加入 4 频带相关性、MSE、小平移相关性 | SIS R@1=0.4627，PM R@1=0.3683 | 小幅提升 |
| multiband 输入 | 4 通道频带输入 `(40,160)/(160,320)/(320,580)/(40,580)` | 小规模 SIS R@1=0.4533；全量 SIS R@1=0.4157 | 小规模有效，全量泛化不好 |
| train-split 大样本重排 | 用 train split 生成更多候选对训练 HGB | SIS R@1=0.4333 | 负结果 |
| pair cross-encoder | 输入两条候选波形的多频带组合直接二分类 | SIS R@1=0.0370 | 单独排序失败 |
| cross-encoder 混合 | `ensemble_z + 0.05 * cross_encoder_z` | SIS R@1=0.4657 | 当前最高，但增益有限 |

## 关键结论

当前不加辅助参数时，R@1 没有接近 0.7。问题不是候选召回完全不够：SIS 的 top50 覆盖约 0.82，PM 约 0.75；真正瓶颈是 noisy 条件下 hard negative 与真配对在波形层面太相似，导致 top candidates 内部排序不稳定。

继续提升到 0.7 更可能需要以下方向之一：

1. 改数据或任务定义：提高 noisy 数据中的可辨识信号强度、控制噪声分布，或扩大训练数据多样性。
2. 更强的 pair/cross 模型：需要带验证集选择、pairwise ranking loss、hard negative curriculum，而不是当前简单二分类 CNN。
3. 使用真实场景可获得的少量辅助观测量：例如候选时间窗口、探测器一致性、粗 SNR/质量先验等；这会改变“waveform-only”的约束。

详细逐步日志见 `experiments_noisy_r1_optimization_log.md`。
