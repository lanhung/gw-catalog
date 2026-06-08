# trigger_time_obs 与 sky-map 实验效果分析

生成日期：2026-06-03

## 1. 当前比较的问题

当前 catalog-level 检索主要比较三类方案：

```text
1. 纯 waveform 检索
2. waveform + trigger_time_obs
3. waveform + trigger_time_obs + predicted sky-map overlap
```

其中 `trigger_time_obs` 是为了替代原来直接使用模拟真值 `geocent_time` 计算出的 `delta_time`。真实观测中可以获得事件触发时间或合并时间估计，但不能直接获得模拟真值到达时间或真实透镜时延。因此，后续论文主实验应优先使用 `trigger_time_obs`。

当前结果显示：

```text
trigger_time_obs 基本保住了原 delta_time 的效果；
predicted sky-map overlap 当前没有带来稳定提升。
```

## 2. 时间特征定义

### 2.1 原 delta_time

原来的时间差特征为：

```text
delta_time = abs(geocent_time_i - geocent_time_j)
log1p_delta_time = log(1 + delta_time)
```

问题是 `geocent_time` 在模拟数据中是真值，真实观测中不能作为精确已知输入。

### 2.2 新 trigger_time_obs

现在使用：

```text
trigger_time_obs = geocent_time_true + timing_jitter
```

其中 timing jitter 由 SNR 控制：

```text
sigma_t = max(0.01, 1 / max(SNR, 1))
```

pair-level 时间差改为：

```text
delta_time_obs = abs(trigger_time_obs_i - trigger_time_obs_j)
log1p_delta_time_obs = log(1 + delta_time_obs)
```

模型不再直接使用真实 `geocent_time` 或 `lens.csv` 中的 `t_d`。

## 3. 原 delta_time 与 trigger_time_obs 效果对比

这里比较 noisy 数据，因为 noisy 更接近真实困难场景。

| 数据 | 原 delta_time R@1 | trigger_time_obs R@1 | 原 delta_time R@5 | trigger_time_obs R@5 | 原 delta_time R@10 | trigger_time_obs R@10 | 原 delta_time R@50 | trigger_time_obs R@50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ET noisy SIS | 0.518 | 0.525 | 0.722 | 0.723 | 0.781 | 0.780 | 0.876 | 0.876 |
| ET noisy PM | 0.874 | 0.864 | 0.969 | 0.964 | 0.996 | 0.995 | 1.000 | 1.000 |
| LIGO noisy SIS | 0.092 | 0.090 | 0.175 | 0.173 | 0.231 | 0.227 | 0.422 | 0.421 |
| LIGO noisy PM | 0.267 | 0.268 | 0.695 | 0.708 | 0.941 | 0.942 | 1.000 | 1.000 |

结论：`trigger_time_obs` 和原 `delta_time` 的效果非常接近。R@1、R@5、R@10、R@50 都没有明显下降。

这说明当前数据中的透镜时间延迟尺度远大于秒级 timing jitter，因此加入观测触发时间误差后，时间差特征仍然保留了主要区分能力。

## 4. 三种方案全量结果

结果文件：

```text
runs/trigger_time_waveform_no_skymap_20260602/three_way_comparison.csv
```

### 4.1 R@1 对比

| 数据 | 纯 waveform R@1 | waveform + trigger_time_obs R@1 | waveform + trigger_time_obs + sky-map R@1 |
|---|---:|---:|---:|
| ET pure SIS | 0.942 | 0.860 | 0.914 |
| ET pure PM | 0.936 | 0.996 | 0.991 |
| ET noisy SIS | 0.407 | 0.525 | 0.518 |
| ET noisy PM | 0.304 | 0.864 | 0.854 |
| LIGO pure SIS | 0.954 | 0.876 | 0.862 |
| LIGO pure PM | 0.955 | 0.997 | 0.997 |
| LIGO noisy SIS | 0.010 | 0.090 | 0.088 |
| LIGO noisy PM | 0.007 | 0.268 | 0.254 |

### 4.2 noisy 数据 Top-k 对比

| 数据 | 方法 | R@1 | R@5 | R@10 | R@50 |
|---|---|---:|---:|---:|---:|
| ET noisy SIS | waveform | 0.407 | 0.591 | 0.658 | - |
| ET noisy SIS | waveform + trigger_time_obs | 0.525 | 0.723 | 0.780 | 0.876 |
| ET noisy SIS | waveform + trigger_time_obs + sky-map | 0.518 | 0.717 | 0.775 | 0.878 |
| ET noisy PM | waveform | 0.304 | 0.463 | 0.541 | - |
| ET noisy PM | waveform + trigger_time_obs | 0.864 | 0.964 | 0.995 | 1.000 |
| ET noisy PM | waveform + trigger_time_obs + sky-map | 0.854 | 0.959 | 0.988 | 1.000 |
| LIGO noisy SIS | waveform | 0.010 | 0.024 | 0.040 | - |
| LIGO noisy SIS | waveform + trigger_time_obs | 0.090 | 0.173 | 0.227 | 0.421 |
| LIGO noisy SIS | waveform + trigger_time_obs + sky-map | 0.088 | 0.167 | 0.222 | 0.412 |
| LIGO noisy PM | waveform | 0.007 | 0.017 | 0.028 | - |
| LIGO noisy PM | waveform + trigger_time_obs | 0.268 | 0.708 | 0.942 | 1.000 |
| LIGO noisy PM | waveform + trigger_time_obs + sky-map | 0.254 | 0.699 | 0.932 | 1.000 |

注：纯 waveform 的 R@50 没有在该三方案表中统一列出；如需要，可从原 waveform summary 继续补充。

## 5. sky-map 当前效果分析

当前 sky-map 方案为：

```text
单事件 waveform -> 预测 sky map 或 sky direction
两个事件 predicted sky maps -> 计算 sky_map_overlap
waveform + trigger_time_obs + predicted sky_map_overlap -> rerank
```

但 predicted sky-map 没有稳定提升。主要原因是 sky predictor 本身没有学好。

当前 sky-map 预测误差大约为：

```text
1.53 到 1.57 rad
```

这个量级接近随机天空方向，因此由它计算出来的 `sky_map_overlap` 不够可靠，可能向 reranker 引入噪声。

noisy 数据中，加入 sky-map 后 R@1 的变化为：

| 数据 | trigger_time_obs R@1 | trigger_time_obs + sky-map R@1 | 变化 |
|---|---:|---:|---:|
| ET noisy SIS | 0.525 | 0.518 | -0.007 |
| ET noisy PM | 0.864 | 0.854 | -0.010 |
| LIGO noisy SIS | 0.090 | 0.088 | -0.002 |
| LIGO noisy PM | 0.268 | 0.254 | -0.014 |

所以当前 predicted sky-map overlap 不能作为主提升点。

## 6. 论文主线建议

目前更合理的主线是：

```text
waveform Siamese retrieval + trigger_time_obs catalog-level reranking
```

理由：

1. 纯 waveform 是必要 baseline。
2. `trigger_time_obs` 是真实观测中可获得的事件级时间估计，不直接泄漏模拟真值。
3. `trigger_time_obs` 基本保持了原 `delta_time` 的效果，真实化后性能没有明显损失。
4. predicted sky-map 当前效果不稳定，不宜作为主结果核心贡献。

建议论文中保留以下实验组：

| 实验组 | 用途 |
|---|---|
| waveform only | 基础检索能力 baseline |
| waveform + trigger_time_obs | 当前 realistic 主结果 |
| waveform + trigger_time_obs + predicted sky-map | 探索性实验，说明当前 sky-map 预测仍是瓶颈 |
| waveform + oracle sky_sep / oracle sky overlap | upper bound，只用于说明天空定位信息理论上有价值 |

## 7. 后续改进方向

如果继续优化 sky-map，重点不应只是换 reranker，而是提高 sky localization predictor 的输入信息质量。

建议方向：

```text
1. 使用多探测器通道间到达时间差
2. 使用通道间相位差或互相关 lag
3. 使用通道间振幅比
4. 使用 network SNR / detector SNR
5. 用 BAYESTAR 或 PE posterior map 作为 teacher，而不是 toy sky map
6. 将 sky-map 作为校准后的 posterior，而不是单纯从 waveform embedding 回归
```

只有当 sky-map 预测明显优于随机方向时，`sky_map_overlap` 才可能稳定提升 catalog-level ranking。

## 8. 当前结论

当前实验结论可以概括为：

```text
trigger_time_obs 替代原 delta_time 是成功的；
predicted sky-map overlap 当前还不成功。
```

因此，当前论文和汇报中建议把 `waveform + trigger_time_obs` 作为主结果，把 predicted sky-map overlap 作为方法探索和未来工作。
