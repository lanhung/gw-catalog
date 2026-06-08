# 当前 sky_map_overlap 方案与实验结果整理

生成日期：2026-06-02

## 1. 当前研究目标

当前项目从原来的 pair-level 检索逐步转向更接近真实观测场景的 catalog-level ranking。核心目标是：在一个事件 catalog 中，对每个候选事件检索其可能的强透镜对应像，并评估真实配对能否排到前面。

原先较强的一版方案使用：

```text
waveform 相似度 + delta_time + sky_sep -> catalog-level rerank
```

但现在需要修正：`ra`、`dec` 在真实观测中不能作为已知精确参数直接使用，因此由真实 `ra/dec` 计算出的 `sky_sep` 也不能作为 realistic 输入。`sky_sep` 只能作为 oracle upper bound 或诊断对照，不能作为主实验结果写成真实可用方法。

因此当前新方案改为：

```text
单事件 waveform -> 机器学习快速预测 sky map
两条事件 predicted sky maps -> 计算 sky_map_overlap
原始配对模型 + delta_time + sky_map_overlap -> 判断是否透镜像
```

## 2. 当前可用与不可用信息

### 2.1 不再作为 realistic 输入的信息

```text
ra
dec
由真实 ra/dec 直接计算的 sky_sep
```

这些量在模拟数据中存在，但真实探测时不能当作精确已知输入。当前代码只允许在训练 sky map predictor 的监督标签阶段使用注入的 `ra/dec`，不能直接输入 reranker。

### 2.2 当前仍可作为 realistic 输入的信息

```text
waveform
waveform encoder 相似度
waveform 初始排序 rank
delta_time
由 waveform 预测出的 sky map overlap
```

其中 `delta_time = |t_i - t_j|` 是事件时间差，在真实 catalog 中可以获得。

## 3. 当前代码结构

### 3.1 Gaussian 近似版 predicted sky map overlap

```text
scripts/experiments/39_waveform_predicted_skymap_rerank.py
```

流程：

```text
waveform -> InceptionTime Siamese encoder -> embedding
embedding -> RidgeCV -> sky unit vector
两个预测 sky unit vectors -> Gaussian log sky_map_overlap
waveform_score + waveform_rank + delta_time + predicted overlap -> HistGradientBoosting reranker
```

结果目录：

```text
runs/waveform_predicted_skymap_rerank_20260602/summary.csv
logs/waveform_predicted_skymap_rerank_20260602.log
```

### 3.2 Sky predictor sweep

```text
scripts/experiments/40_skymap_predictor_sweep.py
```

测试了多种从 waveform embedding 预测天空方向的模型：

```text
ridge
knn32
extratrees
randomforest
mlp
```

结果目录：

```text
runs/skymap_predictor_sweep_20260602/summary.csv
runs/skymap_predictor_sweep_20260602/best_by_group.csv
logs/skymap_predictor_sweep_20260602.log
```

### 3.3 Toy HEALPix SkyMapNet 版 sky_map_overlap

```text
scripts/experiments/41_toy_skymapnet_overlap_rerank.py
```

这是目前更符合“sky map overlap”概念的版本，已经安装并使用：

```text
healpy 1.19.0
HEALPix NSIDE = 8
NPIX = 768
```

流程：

```text
单事件 waveform embedding -> SkyMapNet -> HEALPix sky probability map
两条事件 predicted sky maps -> O_min / O_BC
waveform_score + waveform_rank + delta_time + O_min + O_BC -> catalog-level reranker
```

其中 overlap 定义为：

```text
O_min = sum_k min(p_i,k, p_j,k)
O_BC  = sum_k sqrt(p_i,k * p_j,k)
```

结果目录：

```text
runs/toy_skymapnet_overlap_rerank_20260602/summary.csv
logs/toy_healpix_skymapnet_overlap_rerank_20260602.log
```

## 4. 当前主要结果

### 4.1 Gaussian 近似 predicted sky map overlap，全量 8 组

| 数据 | waveform R@1 | rerank R@1 | R@5 | R@10 | R@50 | sky 预测平均角误差(rad) |
|---|---:|---:|---:|---:|---:|---:|
| ET pure SIS | 0.942 | 0.919 | 0.988 | 0.992 | 0.996 | 1.571 |
| ET pure PM | 0.936 | 0.995 | 0.998 | 0.998 | 0.998 | 1.570 |
| ET noisy SIS | 0.407 | 0.517 | 0.716 | 0.777 | 0.876 | 1.551 |
| ET noisy PM | 0.304 | 0.866 | 0.967 | 0.996 | 1.000 | 1.572 |
| LIGO pure SIS | 0.954 | 0.882 | 0.990 | 0.996 | 0.997 | 1.536 |
| LIGO pure PM | 0.955 | 0.996 | 0.997 | 0.999 | 0.999 | 1.525 |
| LIGO noisy SIS | 0.010 | 0.077 | 0.161 | 0.217 | 0.418 | 1.550 |
| LIGO noisy PM | 0.007 | 0.276 | 0.727 | 0.948 | 1.000 | 1.534 |

### 4.2 不使用 sky map，只使用 waveform + delta_time 的对照

| 数据 | waveform R@1 | delta_time rerank R@1 | R@5 | R@10 | R@50 |
|---|---:|---:|---:|---:|---:|
| ET noisy SIS | 0.407 | 0.518 | 0.722 | 0.781 | 0.876 |
| ET noisy PM | 0.304 | 0.874 | 0.969 | 0.996 | 1.000 |
| LIGO noisy SIS | 0.010 | 0.092 | 0.175 | 0.231 | 0.422 |
| LIGO noisy PM | 0.007 | 0.267 | 0.695 | 0.941 | 1.000 |

### 4.3 Toy HEALPix SkyMapNet overlap，noisy 4 组

| 数据 | waveform R@1 | 不加 sky map R@1 | Toy HEALPix overlap R@1 | R@5 | R@10 | R@50 | SkyMapNet 平均角误差(rad) |
|---|---:|---:|---:|---:|---:|---:|---:|
| ET noisy SIS | 0.407 | 0.518 | 0.528 | 0.719 | 0.774 | 0.875 | 1.537 |
| ET noisy PM | 0.304 | 0.874 | 0.853 | 0.956 | 0.994 | 0.999 | 1.557 |
| LIGO noisy SIS | 0.010 | 0.092 | 0.078 | 0.164 | 0.220 | 0.403 | 1.534 |
| LIGO noisy PM | 0.007 | 0.267 | 0.286 | 0.711 | 0.932 | 1.000 | 1.552 |

## 5. 结果解读

### 5.1 已经完成的工作

当前已经跑通了完整的 realistic sky_map_overlap 链路：

```text
event waveform -> predicted sky map -> sky_map_overlap -> catalog-level rerank
```

这比直接使用 `sky_sep` 更符合真实物理观测，因为真实事件通常只能得到天空定位概率图，而不是精确天空坐标。

### 5.2 当前最重要的问题

当前 SkyMapNet 的天空定位能力还很弱，平均角误差约为：

```text
1.53 到 1.57 rad
```

这个误差接近随机天空方向的量级。因此目前 predicted sky_map_overlap 对排序提升不稳定：

```text
ET noisy SIS: 0.518 -> 0.528，小幅提升
ET noisy PM:  0.874 -> 0.853，下降
LIGO noisy SIS: 0.092 -> 0.078，下降
LIGO noisy PM:  0.267 -> 0.286，小幅提升
```

所以当前不能声称 sky_map_overlap 已经稳定提升模型，只能说该链路已经实现，但 sky map 预测器仍是瓶颈。

### 5.3 当前真正稳定有效的部分

目前最稳定的提升主要来自：

```text
waveform embedding similarity
waveform reciprocal rank
delta_time
catalog-level reranker
```

也就是说，catalog-level rerank 本身是有效的；但 predicted sky_map_overlap 还没有达到能稳定贡献信息的程度。

## 6. 论文实验建议

如果放进论文，建议把实验分成四类：

| 实验组 | waveform | delta_time | sky 信息 | catalog-level rerank | 论文定位 |
|---|---|---|---|---|---|
| A | 是 | 否 | 否 | 否 | waveform-only baseline |
| B | 是 | 是 | 否 | 是 | realistic catalog baseline |
| C | 是 | 是 | predicted sky_map_overlap | 是 | 当前主推 realistic sky-map 方法 |
| D | 是 | 是 | oracle sky_sep 或 oracle sky overlap | 是 | upper bound，不作为真实可用方法 |

其中 D 只能写成上限实验，用来说明如果天空定位足够准确，sky 信息理论上能带来多少帮助；不能把 D 当成真实场景主结果。

真实 catalog 设定建议加入透镜比例压力测试，例如：

```text
10% lensed systems + 90% unlensed events
```

原因是实际观测中非透镜事件远多于透镜事件，仅在平衡数据上报告结果会过于乐观。

## 7. 下一步优化方向

当前最值得继续做的不是直接把 HEALPix 分辨率从 NSIDE=8 提到 32，而是先提高 sky map predictor 的可学习信息量。

建议下一步增加 detector-level 可观测特征：

```text
每个探测器通道的峰值时间
探测器间到达时间差
探测器间互相关 lag
每个通道的 RMS / peak / energy
通道间振幅比
网络 SNR 或近似 SNR
```

原因是天空定位主要依赖多探测器之间的到达时间差、相位差和振幅响应差。只用 waveform embedding 学 sky map，信息可能不足。

对 ET 单通道或等效单通道数据，sky localization 本身会更困难；对 LIGO 多通道数据，detector-level 特征理论上更可能提升 sky map 预测。

## 8. 当前结论

当前项目已经完成从 `sky_sep` 到 `sky_map_overlap` 的方法替换，并跑通了第一版基于 waveform 预测 sky map 的 catalog-level ranking 实验。

但实验结果显示：当前 predicted sky map 的定位误差较大，sky_map_overlap 的收益不稳定。论文中应该把当前 predicted sky_map_overlap 作为 realistic 方法探索，把 oracle sky_sep/sky overlap 作为 upper bound，把 waveform + delta_time + catalog rerank 作为当前最稳的 realistic baseline。
