# trigger_time_obs 版本全量重跑结果

生成日期：2026-06-02

## 1. 本次重跑设置

本次重跑使用新的观测触发时间特征：

```text
log1p_delta_time_obs = log(1 + abs(trigger_time_obs_i - trigger_time_obs_j))
```

不再直接使用：

```text
geocent_time_i - geocent_time_j
lens.csv 中的 t_d
```

`trigger_time_obs` 由 `geocent_time_true + SNR timing jitter` 生成，误差模型为：

```text
sigma_t = max(0.01, 1 / max(SNR, 1))
```

## 2. Gaussian predicted sky-map overlap，全量 8 组

结果文件：

```text
runs/waveform_predicted_skymap_rerank_20260602/summary.csv
logs/waveform_predicted_skymap_trigger_time_full_20260602.log
```

| 数据 | waveform R@1 | waveform R@5 | waveform R@10 | rerank R@1 | rerank R@5 | rerank R@10 | rerank R@50 | sky mean error(rad) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ET pure SIS | 0.942 | 0.981 | 0.987 | 0.914 | 0.984 | 0.989 | 0.997 | 1.571 |
| ET pure PM | 0.936 | 0.974 | 0.980 | 0.991 | 0.999 | 1.000 | 1.000 | 1.570 |
| ET noisy SIS | 0.407 | 0.591 | 0.658 | 0.518 | 0.717 | 0.775 | 0.878 | 1.551 |
| ET noisy PM | 0.304 | 0.463 | 0.541 | 0.854 | 0.959 | 0.988 | 1.000 | 1.572 |
| LIGO pure SIS | 0.954 | 0.983 | 0.989 | 0.862 | 0.990 | 0.995 | 0.997 | 1.536 |
| LIGO pure PM | 0.955 | 0.984 | 0.988 | 0.997 | 0.997 | 0.997 | 0.997 | 1.525 |
| LIGO noisy SIS | 0.010 | 0.024 | 0.040 | 0.088 | 0.167 | 0.222 | 0.412 | 1.550 |
| LIGO noisy PM | 0.007 | 0.017 | 0.028 | 0.254 | 0.699 | 0.932 | 1.000 | 1.534 |

## 3. Toy HEALPix SkyMapNet overlap，noisy 4 组

结果文件：

```text
runs/toy_skymapnet_overlap_rerank_20260602/summary.csv
logs/toy_healpix_skymapnet_trigger_time_20260602.log
```

| 数据 | waveform R@1 | waveform R@5 | waveform R@10 | rerank R@1 | rerank R@5 | rerank R@10 | rerank R@50 | sky centroid mean error(rad) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ET noisy SIS | 0.407 | 0.591 | 0.658 | 0.516 | 0.714 | 0.772 | 0.871 | 1.537 |
| ET noisy PM | 0.304 | 0.463 | 0.541 | 0.852 | 0.965 | 0.993 | 1.000 | 1.571 |
| LIGO noisy SIS | 0.010 | 0.024 | 0.040 | 0.084 | 0.171 | 0.222 | 0.412 | 1.549 |
| LIGO noisy PM | 0.007 | 0.017 | 0.028 | 0.247 | 0.671 | 0.924 | 1.000 | 1.545 |

## 4. 结论

1. 换成 `trigger_time_obs` 后，整体结果和之前直接扰动 `geocent_time` 的版本接近，说明秒级触发时间误差相对当前透镜时间延迟尺度影响不大。
2. Gaussian predicted sky-map overlap 与 Toy HEALPix SkyMapNet overlap 的结果接近，Toy HEALPix 没有明显优势。
3. Sky predictor 的平均角误差仍在约 1.53 到 1.57 rad，接近随机方向量级，因此 predicted sky-map overlap 目前仍不是主要提升来源。
4. 当前有效提升主要仍来自 waveform score/rank 与 `trigger_time_obs` 派生的 `delta_time_obs`。
