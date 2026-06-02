# 最小辅助参数检索实验记录

## 目的

在不大量引入辅助参数的前提下，评估少量真实观测中相对可获得的参数是否能提升 noisy catalog-level 候选检索。当前默认目标不是用全部注入真值把问题做得过于理想化，而是尽量只保留少数、物理上可解释且观测流程中较容易获得的量。

## 推荐方案

当前推荐的最小辅助参数组合是：

- `delta_time`：两个候选事件的触发/地心时间差。
- `sky_sep`：两个候选事件天空定位中心的角距离。

这两个量组合为 `time_sky`。它不使用 lens truth、source id、pair id，也不使用 `mu`、`t_d`、`z_l` 等只有仿真或透镜模型反推后才知道的量。质量、距离等参数在真实场景中也可估计，但不作为默认最小方案，因为它们对参数估计误差和透镜放大影响更敏感。

## 结果表

| family | mode | group | features | feature_count | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| SIS | realistic | time | delta_time | 1 | 0.2717 | 0.5737 | 0.7020 | 0.8590 | 4.0 |
| SIS | realistic | sky | sky_sep | 1 | 0.5733 | 0.8543 | 0.8600 | 0.8600 | 1.0 |
| SIS | realistic | time_sky | delta_time+sky_sep | 2 | 0.8020 | 0.8590 | 0.8600 | 0.8600 | 1.0 |
| SIS | realistic | mass_sky | chirp_diff+q_diff+sky_sep | 3 | 0.6950 | 0.8557 | 0.8593 | 0.8593 | 1.0 |
| PM | realistic | time | delta_time | 1 | 0.7647 | 0.8103 | 0.8103 | 0.8103 | 1.0 |
| PM | realistic | sky | sky_sep | 1 | 0.5297 | 0.8037 | 0.8103 | 0.8103 | 1.0 |
| PM | realistic | time_sky | delta_time+sky_sep | 2 | 0.8073 | 0.8103 | 0.8103 | 0.8103 | 1.0 |
| PM | realistic | mass_sky | chirp_diff+q_diff+sky_sep | 3 | 0.6510 | 0.8087 | 0.8103 | 0.8103 | 1.0 |
| SIS | rough | time | delta_time | 1 | 0.2717 | 0.5737 | 0.7020 | 0.8590 | 4.0 |
| SIS | rough | sky | sky_sep | 1 | 0.2253 | 0.6500 | 0.7970 | 0.8593 | 3.0 |
| SIS | rough | time_sky | delta_time+sky_sep | 2 | 0.6370 | 0.8347 | 0.8583 | 0.8600 | 1.0 |
| SIS | rough | mass_sky | chirp_diff+q_diff+sky_sep | 3 | 0.2590 | 0.6537 | 0.8013 | 0.8593 | 3.0 |
| PM | rough | time | delta_time | 1 | 0.7647 | 0.8103 | 0.8103 | 0.8103 | 1.0 |
| PM | rough | sky | sky_sep | 1 | 0.1997 | 0.5983 | 0.7380 | 0.8097 | 4.0 |
| PM | rough | time_sky | delta_time+sky_sep | 2 | 0.8040 | 0.8103 | 0.8103 | 0.8103 | 1.0 |
| PM | rough | mass_sky | chirp_diff+q_diff+sky_sep | 3 | 0.2590 | 0.6237 | 0.7493 | 0.8097 | 3.0 |

## 结论

1. 如果辅助参数尽量少，优先选择 `delta_time + sky_sep` 两个参数。realistic 扰动下，SIS noisy R@1 从 waveform-only 最好约 0.4657 提升到 0.8020，PM noisy R@1 从约 0.3683 提升到 0.8073。
2. 单独 `delta_time` 对 PM 很有效，但对 SIS 不够；单独 `sky_sep` 对 SIS 有提升，但也不够稳定。两个参数组合互补性明显。
3. `mass_sky` 在 realistic 和 rough 下都没有超过 `time_sky`，因此目前不建议把质量参数作为默认辅助输入。
4. rough 扰动下 SIS 的 R@1 降到 0.6370，说明如果天空定位误差很大，仅靠两个辅助参数仍不够，需要后续考虑 posterior overlap、候选簇级别评分或更强的波形编码器。

## 文件位置

- 实验脚本：`scripts/experiments/23_minimal_aux_selected.py`
- 完整结果：`runs/et10000_minimal_aux_selected/minimal_aux_selected_summary.csv`
- 日志：`logs/et10000_minimal_aux_selected_20260529_142736/selected.log`

