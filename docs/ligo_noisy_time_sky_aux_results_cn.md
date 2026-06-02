# LIGO Noisy Delta Time + Sky Sep 辅助参数实验

生成时间：2026-06-01

## 实验目的

在 LIGO noisy 的首版 waveform-only 基线很低的情况下，加入两个辅助参数：

- `delta_time`：两个候选事件的 geocent_time 差，输入为 `log1p(abs(t_i - t_j))`。
- `sky_sep`：两个候选事件天空位置中心的角距离。

实验目标是判断这两个辅助参数能否像 ET 数据中一样显著提升 noisy catalog-level 检索。

## 实验流程

1. 使用已训练的 LIGO noisy InceptionTime + bandpass checkpoint 计算 val/test similarity score。
2. 对每个 query 取 waveform top-50 候选。
3. 在 val split 上用 `HistGradientBoostingClassifier` 学习 `delta_time + sky_sep` reranker。
4. 在 test split 上评价 catalog-level R@K。

注意：这里不是重新训练 waveform encoder，而是在已有 noisy waveform top-50 候选内重排。因此最终性能上限受 waveform top-50 recall 限制。

## 使用的 waveform checkpoint

```text
runs/ligo_inceptiontime_bandpass_full_ep50_20260601_095620/SIS_noisy_inceptiontime_bandpass_n10000_ep50
runs/ligo_inceptiontime_bandpass_full_ep50_20260601_095620/PM_noisy_inceptiontime_bandpass_n10000_ep50
```

## 结果表

| family | mode | waveform R@1 | waveform R@5 | waveform R@10 | waveform R@50 | aux R@1 | aux R@5 | aux R@10 | aux R@50 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SIS | exact | 0.0107 | 0.0243 | 0.0397 | 0.1077 | 0.1053 | 0.1060 | 0.1060 | 0.1077 |
| SIS | realistic | 0.0107 | 0.0243 | 0.0397 | 0.1077 | 0.1043 | 0.1077 | 0.1077 | 0.1077 |
| SIS | rough | 0.0107 | 0.0243 | 0.0397 | 0.1077 | 0.0933 | 0.1070 | 0.1070 | 0.1077 |
| PM | exact | 0.0067 | 0.0170 | 0.0280 | 0.0780 | 0.0780 | 0.0780 | 0.0780 | 0.0780 |
| PM | realistic | 0.0067 | 0.0170 | 0.0280 | 0.0780 | 0.0777 | 0.0780 | 0.0780 | 0.0780 |
| PM | rough | 0.0067 | 0.0170 | 0.0280 | 0.0780 | 0.0777 | 0.0780 | 0.0780 | 0.0780 |

## 关键结论

1. `delta_time + sky_sep` 对 LIGO noisy 是有效的：SIS realistic R@1 从 0.0107 提升到 0.1043，PM realistic R@1 从 0.0067 提升到 0.0777。
2. 但是提升后的上限仍然很低，因为 waveform top-50 召回本身很低：SIS R@50=0.1077，PM R@50=0.0780。
3. reranker 已经几乎把 top-50 中能找到的真实匹配排到了第 1 位；当前瓶颈不是 `delta_time + sky_sep`，而是第一阶段 noisy waveform 召回。
4. 这与 LIGO pure 结果形成鲜明对比：pure 的 SIS/PM R@1 都约为 0.955，说明训练流程和双通道输入没问题，noisy 波形预处理/召回才是核心问题。

## 下一步建议

LIGO noisy 后续优化优先级：

1. 提高 waveform top-50 recall，而不是继续强化 reranker。
2. 先做 LIGO noisy 预处理 sweep：`whiten`、`whiten_bandpass`、不同 bandpass 频段。
3. 尝试 detector 通道融合，例如 network-combined 单通道、SNR 加权组合、或 detector-wise embedding fusion。
4. 尝试 noisy-to-pure 辅助训练，因为 LIGO pure 可达到很高结果。
5. 如果 top-50 recall 提升后，再重新加 `delta_time + sky_sep`，预计 R@1 会随之明显提升。

## 文件位置

- 脚本：`scripts/experiments/26_ligo_time_sky_aux_full.py`
- 结果表：`runs/ligo_noisy_time_sky_aux_full/ligo_noisy_time_sky_aux_summary.csv`
- JSON：`runs/ligo_noisy_time_sky_aux_full/summary.json`
- 日志：`logs/ligo_noisy_time_sky_aux_full_20260601_111106/ligo_noisy_time_sky_aux_full.log`

