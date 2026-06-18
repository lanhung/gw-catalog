# LIGO noisy SIS 只靠波形优化尝试记录（2026-06-09）

本次实验只评估 waveform-only，不使用 time、sky、catalog rerank 等辅助信息。目标是验证 LIGO noisy SIS 的纯波形检索能否通过工程修正或输入表示优化明显提升。

## 实验位置

- 脚本：`scripts/experiments/79_ligo_noisy_sis_waveform_ablation.py`
- 结果目录：`runs/ligo_noisy_sis_waveform_ablation_20260609/`
- 汇总表：`runs/ligo_noisy_sis_waveform_ablation_20260609/waveform_ablation_summary.csv`

## 结果表

| 方案 | 修改内容 | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | Top 1% | Top 5% | Top 10% | 中位rank |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_reproduce | 复现当前 bandpass 方案 | 0.0083 | 0.0237 | 0.0397 | 0.0930 | 0.1390 | 0.3420 | 0.0873 | 0.2230 | 0.3227 | 1079.5 |
| fix_roll | `np.roll(..., axis=-1)`，避免跨 detector channel | 0.0107 | 0.0270 | 0.0400 | 0.1143 | 0.1630 | 0.3553 | 0.1073 | 0.2457 | 0.3387 | 1006.0 |
| fix_roll_per_channel_zscore | 修复 roll + 每 detector 通道独立 zscore | 0.0103 | 0.0287 | 0.0420 | 0.1100 | 0.1537 | 0.3433 | 0.1053 | 0.2337 | 0.3277 | 1084.0 |
| fix_roll_no_peak_flip | 修复 roll + 关闭 peak flip | 0.0043 | 0.0207 | 0.0360 | 0.1037 | 0.1430 | 0.3307 | 0.0980 | 0.2147 | 0.3140 | 1106.5 |
| multiband | 多频带输入，4 组频段通道 | 0.0047 | 0.0197 | 0.0340 | 0.1017 | 0.1480 | 0.3303 | 0.0933 | 0.2267 | 0.3147 | 1163.0 |
| fix_roll_per_channel_zscore_pure_aux | 修复 roll + per-channel zscore + noisy-to-pure 辅助训练 | 0.0047 | 0.0087 | 0.0120 | 0.0353 | 0.0537 | 0.1767 | 0.0337 | 0.1050 | 0.1657 | 1906.0 |

## 主要结论

1. `fix_roll` 有轻微正向作用，但不是主要瓶颈。
   - R@10 从 `0.0397` 到 `0.0400`，几乎不变。
   - Top 1% 从 `0.0873` 到 `0.1073`，有小幅改善。
   - 说明跨 channel roll 是工程风险，应该修复，但它不能解释 LIGO noisy SIS waveform-only 的整体失败。

2. `per_channel_zscore` 只带来很小提升。
   - R@10 到 `0.0420`，是本组最高。
   - 但 Top 1%、Top 5%、Top 10% 没有继续提升。
   - 说明通道归一化方向合理，但不足以解决噪声主导问题。

3. 关闭 `peak_flip` 会变差。
   - R@10 降到 `0.0360`。
   - 当前 peak flip 虽然有物理风险，但在当前训练设置下仍提供了稳定化作用。

4. 简单 multiband 输入没有改善，反而变差。
   - R@10 降到 `0.0340`。
   - 说明只是拆频段并不能让模型自动找到 LIGO noisy 下的稳定特征，可能还需要更强的频域/时频结构模型。

5. 当前 naive pure auxiliary 方案明显失败。
   - R@10 降到 `0.0120`，中位 rank 到 `1906`。
   - 训练 loss 很快接近 0，说明辅助样本过强，模型可能过度学习 noisy-clean 自身对齐，破坏了 lensed pair catalog retrieval 的全局结构。

## 判断

当前尝试没有把 LIGO noisy SIS 的 waveform-only 结果实质性提高。最好的方案是：

```text
fix_roll_per_channel_zscore
R@10 = 0.0420
Top 1% = 0.1053
```

相比 baseline：

```text
baseline R@10 = 0.0397
baseline Top 1% = 0.0873
```

提升很小。因此目前可以判断：LIGO noisy SIS 只靠波形的瓶颈主要不是这些简单工程修正，而是 noisy waveform 本身的信息提取能力不足。

## 后续建议

1. 保留 `fix_roll` 修复，因为它是明确工程问题。
2. 可以保留 per-channel zscore 作为 LIGO 专用预处理候选，但需要和 ET/PM 全量验证。
3. 暂不采用当前 naive pure_aux；如果继续做，需要降低 auxiliary 权重，而不是直接把 pure/noisy pair 大量加入同一个 contrastive 训练池。
4. 下一步如果还要提升 waveform-only，应尝试更结构化的方法：
   - 时频图或 CWT/spectrogram 模型；
   - detector cross-correlation / coherent feature；
   - noise-aware denoising encoder；
   - supervised pair classifier 或 hard negative pair ranking；
   - 按 SNR、time delay、magnification ratio 做重采样或加权训练。

