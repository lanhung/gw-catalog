# Time-Sky 两辅助参数全量实验结果

## 实验设置

本实验固定只使用两个辅助参数：

- `delta_time`：两个候选事件的触发/地心时间差，实际输入为 `log1p(abs(t_i - t_j))`。
- `sky_sep`：两个候选事件天空定位中心的角距离。

流程为 catalog-level 两阶段检索：

1. 使用当前 noisy 波形模型 ensemble 召回 top-50 候选：`InceptionTime + InceptionAttn_lr5e4 + GatedTCN`。
2. 使用 `HistGradientBoostingClassifier` 基于 `delta_time + sky_sep` 对 top-50 候选重排。

本次跑的是完整 test split，每个 family 有 3000 个有效 query。

## 全量结果

| family | mode | feature_count | topk | train_examples | train_positive | Val AUC | R@1 | R@5 | R@10 | R@50 | median rank | valid |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SIS | exact | 2 | 50 | 482512 | 2619 | 0.999983 | 0.8577 | 0.8600 | 0.8600 | 0.8600 | 1.0 | 3000 |
| SIS | mild | 2 | 50 | 482512 | 2619 | 0.999876 | 0.8473 | 0.8600 | 0.8600 | 0.8600 | 1.0 | 3000 |
| SIS | realistic | 2 | 50 | 482512 | 2619 | 0.999309 | 0.7997 | 0.8560 | 0.8560 | 0.8573 | 1.0 | 3000 |
| SIS | rough | 2 | 50 | 482512 | 2619 | 0.996553 | 0.6320 | 0.8320 | 0.8577 | 0.8600 | 1.0 | 3000 |
| PM | exact | 2 | 50 | 500078 | 2387 | 1.000000 | 0.8103 | 0.8103 | 0.8103 | 0.8103 | 1.0 | 3000 |
| PM | mild | 2 | 50 | 500078 | 2387 | 0.999998 | 0.8100 | 0.8103 | 0.8103 | 0.8103 | 1.0 | 3000 |
| PM | realistic | 2 | 50 | 500078 | 2387 | 0.999989 | 0.8087 | 0.8103 | 0.8103 | 0.8103 | 1.0 | 3000 |
| PM | rough | 2 | 50 | 500078 | 2387 | 0.999961 | 0.8077 | 0.8103 | 0.8103 | 0.8103 | 1.0 | 3000 |

## 结论

1. 只加 `delta_time + sky_sep` 两个辅助参数后，SIS realistic 的 R@1 为 0.7997，PM realistic 的 R@1 为 0.8087。
2. SIS 对参数扰动更敏感：从 exact 的 0.8577 降到 rough 的 0.6320；PM 基本稳定在 0.808 左右。
3. 这说明两个辅助参数已经足以把 realistic 场景提升到约 0.8，但如果 SIS 的天空定位误差非常粗糙，还需要后续用 posterior overlap、簇级别评分或更强波形模型补强。
4. 本实验不使用 lens truth、source id、pair id、`mu`、`t_d`、`z_l` 等仿真真值，也不默认使用质量和距离参数。

## 文件位置

- 脚本：`scripts/experiments/24_time_sky_aux_full.py`
- 汇总表：`runs/et10000_time_sky_aux_full/time_sky_aux_full_summary.csv`
- JSON：`runs/et10000_time_sky_aux_full/summary.json`
- 日志：`logs/et10000_time_sky_aux_full_20260529_145926/time_sky_aux_full.log`

