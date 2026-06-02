# Delta Time + Sky Map Overlap 实验结果

生成时间：2026-05-29

## 实验目的

将此前的 `delta_time + sky_sep` 两辅助参数方案，替换为：

- `delta_time`
- `log_sky_map_overlap`

用于检验 sky map overlap 形式是否能替代天空中心角距离 `sky_sep`。

## 重要说明

当前 ET10000 数据表只有 `ra/dec`，没有真实 HEALPix sky map、posterior samples 或天空定位协方差。因此本实验不是严格的真实 skymap overlap，而是高斯近似版本：

```text
log_overlap = -log(2*pi*(sigma1^2+sigma2^2)) - sky_sep^2 / (2*(sigma1^2+sigma2^2))
```

其中 `sky_sep` 是两个天空定位中心的角距离，`sigma` 按扰动模式指定：

| mode | sigma(rad) |
|---|---:|
| exact | 0.03 |
| mild | 0.03 |
| realistic | 0.08 |
| rough | 0.20 |

由于当前所有事件在同一 mode 下使用相同 sigma，这个近似 overlap 本质上仍然是 `sky_sep` 的单调变换。因此它主要用于验证代码路径和论文表述方向，不能替代真实 skymap 后验重叠实验。

## 实验流程

1. 使用 `InceptionTime + InceptionAttn_lr5e4 + GatedTCN` noisy waveform ensemble 召回 top-50 候选。
2. 使用 `HistGradientBoostingClassifier` 基于 `delta_time + log_sky_map_overlap` 对候选重排。
3. 在完整 test split 上评价 catalog-level R@K，每个 family 有 3000 个有效 query。

## 结果表

| family | mode | R@1 | R@5 | R@10 | R@50 | valid |
|---|---|---:|---:|---:|---:|---:|
| SIS | exact | 0.8487 | 0.8600 | 0.8600 | 0.8600 | 3000 |
| SIS | mild | 0.8460 | 0.8600 | 0.8600 | 0.8600 | 3000 |
| SIS | realistic | 0.7887 | 0.8600 | 0.8600 | 0.8600 | 3000 |
| SIS | rough | 0.6350 | 0.8423 | 0.8587 | 0.8600 | 3000 |
| PM | exact | 0.8100 | 0.8103 | 0.8103 | 0.8103 | 3000 |
| PM | mild | 0.8100 | 0.8103 | 0.8103 | 0.8103 | 3000 |
| PM | realistic | 0.8080 | 0.8103 | 0.8103 | 0.8103 | 3000 |
| PM | rough | 0.8047 | 0.8103 | 0.8103 | 0.8103 | 3000 |

## 与 delta_time + sky_sep 的对比

| family | mode | delta_time + sky_sep R@1 | delta_time + log_sky_map_overlap R@1 | 变化 |
|---|---|---:|---:|---:|
| SIS | exact | 0.8577 | 0.8487 | -0.0090 |
| SIS | mild | 0.8473 | 0.8460 | -0.0013 |
| SIS | realistic | 0.7997 | 0.7887 | -0.0110 |
| SIS | rough | 0.6320 | 0.6350 | +0.0030 |
| PM | exact | 0.8103 | 0.8100 | -0.0003 |
| PM | mild | 0.8100 | 0.8100 | +0.0000 |
| PM | realistic | 0.8087 | 0.8080 | -0.0007 |
| PM | rough | 0.8077 | 0.8047 | -0.0030 |

## 结论

1. 在当前只有 `ra/dec`、没有真实 skymap 的数据条件下，高斯近似 `sky_map_overlap` 与 `sky_sep` 效果非常接近。
2. SIS realistic 从 0.7997 降到 0.7887，略低于直接使用 `sky_sep`。PM realistic 从 0.8087 到 0.8080，基本不变。
3. 由于当前 overlap 是由 `sky_sep` 单调变换得到的，不应把它表述为真实 skymap posterior overlap。
4. 论文中可以写成：当前实验用高斯近似 sky-map overlap 验证了天空定位一致性特征的有效性；真正的 sky-map overlap 需要在数据生成阶段输出 HEALPix skymap 或 posterior samples。

## 文件位置

- 脚本：`scripts/experiments/25_delta_time_skymap_overlap_full.py`
- 汇总表：`runs/et10000_delta_time_skymap_overlap_full/delta_time_skymap_overlap_full_summary.csv`
- 日志：`logs/et10000_delta_time_skymap_overlap_full_20260529_152654/delta_time_skymap_overlap_full.log`

