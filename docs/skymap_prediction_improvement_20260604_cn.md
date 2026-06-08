# sky-map 预测模型改进实验记录

日期：2026-06-04

## 背景

上一轮统一对比实验显示：

- 真实 sky_sep 和真实 sky_map_overlap 可以显著提升 catalog-level rerank。
- 但当前机器学习预测 sky-map 的效果很弱，平均角误差约 1.52 到 1.57 rad，接近随机天区。
- 因此瓶颈不是 sky_map_overlap 指标，而是 `waveform -> sky map / sky direction` 预测模型。

本次实验尝试改进 sky-map 预测模型，验证是否可以从原始 waveform 中提取比 matching embedding 更强的天空定位信息。

## 新增代码

新增脚本：

`/root/autodl-tmp/gw-catalog/scripts/experiments/44_waveform_feature_skymap_predictor.py`

输出目录：

`/root/autodl-tmp/gw-catalog/runs/waveform_feature_skymap_predictor_20260604/`

日志：

`/root/autodl-tmp/gw-catalog/logs/waveform_feature_skymap_predictor_20260604.log`

## 方法修改

原来的 sky-map 预测方法：

```text
matching embedding -> RidgeCV -> sky unit vector -> sky_map_overlap
```

这有一个问题：matching embedding 是为透镜匹配训练的，可能已经主动丢掉了天空位置、幅度响应等不利于匹配泛化的信息。

本次新增方法：

```text
原始 waveform -> 统计特征 -> sky unit vector -> sky_map_overlap
```

waveform 统计特征包括：

- 时间分段均值；
- 时间分段标准差；
- 时间分段最大绝对值；
- 时间分段 RMS；
- 频域分段平均幅度；
- 频域分段最大幅度。

另外测试了融合版本：

```text
waveform 统计特征 + matching embedding -> sky unit vector -> sky_map_overlap
```

测试 predictor：

- `waveform_stats_ridge`
- `fusion_stats_embedding_ridge`
- `fusion_stats_embedding_mlp`

## 已完成结果

当前完成了 ET noisy SIS 和 ET noisy PM。LIGO noisy 阶段由于原始波形 IO 较重，运行被手动停止，后续需要改成更轻量的 LIGO-only 版本再跑。

### ET noisy SIS

| predictor | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 |
|---|---:|---:|---:|---:|---:|---:|
| 原 embedding-only ridge | 1.551 | 1.539 | 0.512 | 0.712 | 0.779 | 0.877 |
| waveform_stats_ridge | 1.224 | 1.164 | 0.510 | 0.719 | 0.780 | 0.875 |
| fusion_stats_embedding_ridge | 1.226 | 1.160 | 0.510 | 0.721 | 0.785 | 0.881 |
| fusion_stats_embedding_mlp | 1.328 | 1.265 | 0.511 | 0.717 | 0.769 | 0.874 |

### ET noisy PM

| predictor | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 |
|---|---:|---:|---:|---:|---:|---:|
| 原 embedding-only ridge | 1.572 | 1.569 | 0.860 | 0.966 | 0.993 | 1.000 |
| waveform_stats_ridge | 1.243 | 1.188 | 0.860 | 0.964 | 0.994 | 1.000 |
| fusion_stats_embedding_ridge | 1.244 | 1.196 | 0.861 | 0.962 | 0.992 | 1.000 |
| fusion_stats_embedding_mlp | 1.340 | 1.272 | 0.855 | 0.964 | 0.994 | 1.000 |

## 结果分析

### 1. sky direction 预测确实改进了

从 ET 两组结果看，直接使用 waveform 统计特征后，sky 角误差明显下降：

- ET noisy SIS：mean error 从约 1.55 rad 降到约 1.22 rad。
- ET noisy PM：mean error 从约 1.57 rad 降到约 1.24 rad。

这说明原始 waveform 中存在一部分与天空定位有关的信息，而 matching embedding 确实可能丢掉了这些信息。

### 2. 但改进后的 sky 预测还不足以提升 catalog rerank

虽然 sky 角误差下降了，但 predicted sky_map_overlap 对最终检索没有带来明显提升：

- ET noisy SIS：R@1 仍约 0.51，低于 waveform-only rerank 的 0.640，也低于真实 sky_overlap oracle 的 0.963。
- ET noisy PM：R@1 仍约 0.86，基本等于 trigger_time_only，远低于真实 sky_overlap oracle 的 0.998。

这说明当前 sky 预测从“随机水平”进步到了“粗略方向”，但还没有精确到可以区分正确透镜伴随事件。

### 3. MLP 不如 Ridge

`fusion_stats_embedding_mlp` 的角误差和 rerank 表现都不如 ridge。当前样本量和特征下，MLP 容易过拟合或训练不稳定，不建议作为主线继续扩展。

### 4. 后续方向应从方向回归转向概率 sky map 或 pair-overlap 目标

当前模型只预测一个 sky unit vector，再用一个高斯近似 sigma 生成 overlap。这个表达太弱，不能表示真实 sky localization 的不确定区域形状。

更合理的下一步是：

1. 预测概率 sky map，而不是单点方向。
2. 直接优化两事件 sky_map_overlap，而不是只优化单事件角误差。
3. 引入 detector response / antenna pattern / 到达时间差等真实可观测定位信息。
4. 对 LIGO 单独做轻量 IO 版本，避免一次加载和处理过大的原始波形。

## 当前结论

本次改进证明：

```text
waveform 统计特征比 matching embedding 更适合预测 sky direction。
```

但也证明：

```text
仅靠单点 sky direction 回归，仍不足以让 predicted sky_map_overlap 接近真实 sky_overlap 的 oracle 效果。
```

因此下一步不应继续简单堆叠 MLP，而应改为概率 sky-map 预测或 pair-level overlap 学习。


## LIGO noisy 补充实验

由于 LIGO 是当前主要困难点，已新增轻量脚本继续完成 LIGO noisy 实验。上一版全量脚本在 LIGO train split 上会加载完整 train score matrix，内存占用接近 100GB，因此改成轻量版本：train split 只加载 waveform/embedding，不加载 train score matrix；val/test 仍加载 score matrix 用于 catalog rerank。

新增脚本：

`/root/autodl-tmp/gw-catalog/scripts/experiments/46_ligo_waveform_feature_skymap_predictor_light.py`

输出目录：

`/root/autodl-tmp/gw-catalog/runs/ligo_waveform_feature_skymap_predictor_light_20260604/`

### LIGO noisy SIS

| predictor | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| 原 embedding-only ridge | 1.550 | 1.536 | 0.080 | 0.158 | 0.209 | 0.399 | 93 |
| waveform_stats_ridge | 1.422 | 1.370 | 0.089 | 0.171 | 0.217 | 0.409 | 81 |
| fusion_stats_embedding_ridge | 1.419 | 1.375 | 0.079 | 0.163 | 0.213 | 0.410 | 86 |
| 真实 sky_overlap oracle | - | - | 0.791 | 0.981 | 0.998 | 1.000 | 1 |

### LIGO noisy PM

| predictor | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| 原 embedding-only ridge | 1.534 | 1.522 | 0.254 | 0.677 | 0.932 | 1.000 | 4 |
| waveform_stats_ridge | 1.417 | 1.379 | 0.270 | 0.709 | 0.950 | 1.000 | 3 |
| fusion_stats_embedding_ridge | 1.419 | 1.382 | 0.313 | 0.718 | 0.948 | 1.000 | 3 |
| 真实 sky_overlap oracle | - | - | 0.995 | 1.000 | 1.000 | 1.000 | 1 |

## LIGO 结果分析

1. LIGO 上 waveform 统计特征确实降低了 sky 角误差。
   - SIS：mean error 从约 1.55 rad 降到约 1.42 rad。
   - PM：mean error 从约 1.53 rad 降到约 1.42 rad。

2. LIGO noisy PM 有小幅检索提升。
   - 原 predicted sky-overlap R@1 约 0.254。
   - waveform_stats_ridge R@1 = 0.270。
   - fusion_stats_embedding_ridge R@1 = 0.313。
   说明对 PM，改进 sky predictor 可以带来一些第一名排序提升。

3. LIGO noisy SIS 仍然困难。
   - 原 predicted sky-overlap R@1 约 0.080。
   - waveform_stats_ridge R@1 = 0.089。
   - fusion_stats_embedding_ridge R@1 = 0.079。
   提升很小，说明 SIS 的 LIGO noisy 场景不能靠当前单点 sky direction 回归解决。

4. 真实 sky_overlap oracle 仍然远高于预测版本。
   - LIGO noisy SIS oracle R@1 = 0.791。
   - LIGO noisy PM oracle R@1 = 0.995。
   当前最佳预测版本分别只有 0.089 和 0.313，差距仍然很大。

## 更新后的结论

当前最可靠的判断是：

```text
LIGO 的困难没有被解决，但已经验证出一个有效方向：原始 waveform 统计特征比 matching embedding 更能保留 sky 信息。
```

不过，这种改进还只是把 sky 预测从接近随机提升到粗略方向估计，仍不足以替代真实 sky localization map。下一步应优先研究：

1. 概率 sky-map 预测，而不是单点方向回归；
2. pair-level sky-overlap 直接学习；
3. 引入真实可观测定位信息，如探测器响应、到达时间差、SNR/相位跨探测器差异；
4. 针对 LIGO noisy SIS 单独分析为什么真实 sky_overlap 能到 0.791，而当前 predicted overlap 只能到 0.089。


## pair-level sky_overlap 直接学习实验

根据前面的分析，又尝试了直接学习 pair-level sky_overlap，而不是先预测单事件 sky direction。

新增脚本：

`/root/autodl-tmp/gw-catalog/scripts/experiments/47_ligo_pair_sky_overlap_predictor.py`

输出目录：

`/root/autodl-tmp/gw-catalog/runs/ligo_pair_sky_overlap_predictor_20260604/`

### 方法

事件级特征：

```text
waveform_stats + matching_embedding -> StandardScaler -> PCA(64)
```

pair-level overlap predictor 输入：

```text
abs(z_i - z_j), z_i * z_j
```

训练标签：

```text
由真实 ra/dec 计算的 oracle log_sky_map_overlap
```

然后将预测得到的 `pair_predicted_log_sky_overlap` 接入统一 catalog rerank：

```text
log1p_delta_time_obs,
pair_predicted_log_sky_overlap,
waveform_score,
waveform_reciprocal_rank
```

### LIGO noisy 结果

| family | method | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---:|---:|---:|---:|---:|
| SIS | pair-level predicted overlap | 0.084 | 0.174 | 0.220 | 0.412 | 85 |
| SIS | best single-event sky direction | 0.089 | 0.171 | 0.217 | 0.409 | 81 |
| SIS | real sky_overlap oracle | 0.791 | 0.981 | 0.998 | 1.000 | 1 |
| PM | pair-level predicted overlap | 0.275 | 0.705 | 0.949 | 0.995 | 3 |
| PM | best single-event sky direction | 0.313 | 0.718 | 0.948 | 1.000 | 3 |
| PM | real sky_overlap oracle | 0.995 | 1.000 | 1.000 | 1.000 | 1 |

### 结论

pair-level overlap 直接学习没有带来预期提升：

- LIGO noisy SIS：R@1 = 0.084，低于 waveform_stats_ridge 的 0.089。
- LIGO noisy PM：R@1 = 0.275，低于 fusion_stats_embedding_ridge 的 0.313。

这说明当前瓶颈不是“单事件方向回归 vs pair-level overlap 目标”的形式问题，而是当前 waveform / matching embedding 中可恢复的 sky 信息仍然不足。真实 sky_overlap oracle 很强，但当前模型无法从现有输入中恢复出足够准确的空间定位信息。

### 后续判断

短期内继续调 HGB、MLP 或 pair regressor 的收益可能有限。更值得做的是引入更物理的 LIGO 定位特征：

1. 两个探测器的峰值到达时间差；
2. 两个探测器的幅度比 / RMS 比 / SNR proxy；
3. 两个探测器的互相关延迟；
4. 多频带能量比；
5. 如果数据生成阶段可控，显式保存 detector response 或 antenna pattern 相关量。

换句话说，下一步应从“更复杂的机器学习模型”转向“更物理的可观测定位特征”。


## LIGO 双探测器物理定位特征实验

又尝试了直接从 LIGO 双探测器 waveform 中提取定位相关物理特征，而不是预测 sky map。

新增脚本：

`/root/autodl-tmp/gw-catalog/scripts/experiments/48_ligo_detector_localization_features.py`

输出目录：

`/root/autodl-tmp/gw-catalog/runs/ligo_detector_localization_features_20260604/`

### 特征来源

当前 LIGO 单事件 waveform 已确认是双通道：

```text
(2, 98304)
```

因此每个事件从两个探测器通道中提取 17 个定位相关特征：

- 两探测器峰值时间差；
- 局部互相关延迟；
- 峰值幅度比；
- RMS 比；
- 总能量比；
- SNR proxy 比；
- 通道相关系数；
- 多频带能量比；
- 多频带相位差 proxy。

pair-level 输入使用：

```text
abs(f_i - f_j), f_i * f_j
```

并接入统一 rerank：

```text
log1p_delta_time_obs,
waveform_score,
waveform_reciprocal_rank,
detector_localization_pair_features
```

### 结果

| family | variant | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---:|---:|---:|---:|---:|
| SIS | baseline time+waveform | 0.089 | 0.171 | 0.223 | 0.416 | 82 |
| SIS | + detector localization features | 0.071 | 0.153 | 0.214 | 0.412 | 85 |
| PM | baseline time+waveform | 0.269 | 0.682 | 0.931 | 1.000 | 3 |
| PM | + detector localization features | 0.265 | 0.704 | 0.945 | 0.998 | 3 |

### 结论

这些简单双探测器定位特征没有解决 LIGO noisy SIS：

- SIS R@1 从 0.089 降到 0.071。
- PM R@1 基本不变，从 0.269 到 0.265，但 R@5/R@10 有小幅提升。

这说明：

1. 简单峰值时间差、互相关延迟、幅度比、频带能量比等手工特征，对 PM 的候选召回略有帮助，但对 SIS 不稳定。
2. 当前 LIGO noisy SIS 的困难不是单靠这些低维 detector-localization proxy 就能解决的。
3. 如果要继续利用物理定位信息，更可能需要数据生成阶段保存更真实的定位中间量，例如 detector response、antenna pattern、各探测器真实到达时间、各探测器 SNR/phase，而不是只从 noisy waveform 后验提取简单统计量。

## 当前综合判断

到目前为止，围绕 sky / localization 的几类尝试结果如下：

| 方法 | LIGO noisy SIS R@1 | LIGO noisy PM R@1 | 判断 |
|---|---:|---:|---|
| predicted sky-overlap, embedding-only | 0.080 | 0.254 | 接近随机 sky 预测，效果弱 |
| waveform_stats sky direction | 0.089 | 0.270 | sky 角误差下降，但检索提升小 |
| fusion_stats_embedding sky direction | 0.079 | 0.313 | PM 有提升，SIS 无提升 |
| pair-level predicted sky-overlap | 0.084 | 0.275 | 未超过单事件方向方案 |
| detector localization hand features | 0.071 | 0.265 | SIS 下降，PM Top-k 小幅提升 |
| real sky-overlap oracle | 0.791 | 0.995 | 说明真实空间定位信息非常有效 |

最终结论：真实 sky localization 对任务非常有价值，但当前从 noisy waveform 中后验恢复 sky/localization 信息的能力还不够。下一步如果继续做 sky 方向，重点应转向数据生成和可观测物理量保存，而不是继续增加普通机器学习模型复杂度。


## LIGO 双通道 CNN sky predictor 实验

为了真正提高 sky 预测模型，又尝试了直接从 LIGO 双探测器 waveform 训练监督神经网络，而不是使用表格统计特征或 matching embedding。

新增脚本：

`/root/autodl-tmp/gw-catalog/scripts/experiments/49_ligo_cnn_sky_predictor_rerank.py`

输出目录：

`/root/autodl-tmp/gw-catalog/runs/ligo_cnn_sky_predictor_rerank_20260604/`

### 方法

输入：

```text
LIGO 双通道 waveform, shape = (2, time)
```

模型：

```text
Conv1D downsampling backbone + attention/avg/max pooling + Linear -> sky unit vector
```

监督标签：

```text
ra/dec -> 3D sky unit vector
```

训练损失：

```text
1 - cosine(pred, true) + 0.05 * MSE(pred, true)
```

然后用预测 sky direction 构造高斯近似 sky-overlap，并接入统一 rerank：

```text
log1p_delta_time_obs,
cnn_predicted_log_sky_overlap,
waveform_score,
waveform_reciprocal_rank
```

### LIGO noisy 结果

| family | sky model | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| SIS | embedding-only ridge | 1.550 | 1.536 | 0.080 | 0.158 | 0.209 | 0.399 | 93 |
| SIS | waveform_stats_ridge | 1.422 | 1.370 | 0.089 | 0.171 | 0.217 | 0.409 | 81 |
| SIS | CNN sky predictor | 1.348 | 1.285 | 0.087 | 0.173 | 0.226 | 0.421 | 79 |
| SIS | real sky-overlap oracle | - | - | 0.791 | 0.981 | 0.998 | 1.000 | 1 |
| PM | embedding-only ridge | 1.534 | 1.522 | 0.254 | 0.677 | 0.932 | 1.000 | 4 |
| PM | fusion_stats_embedding_ridge | 1.419 | 1.382 | 0.313 | 0.718 | 0.948 | 1.000 | 3 |
| PM | CNN sky predictor | 1.396 | 1.372 | 0.270 | 0.688 | 0.934 | 1.000 | 3 |
| PM | real sky-overlap oracle | - | - | 0.995 | 1.000 | 1.000 | 1.000 | 1 |

### 结论

CNN 确实进一步提高了 sky direction 预测质量：

- LIGO noisy SIS：mean error 从 1.550 降到 1.348 rad。
- LIGO noisy PM：mean error 从 1.534 降到 1.396 rad。

但最终检索提升仍有限：

- SIS：R@1 = 0.087，没有超过 waveform_stats_ridge 的 0.089，但 R@10/R@50/median rank 略有改善。
- PM：R@1 = 0.270，低于 fusion_stats_embedding_ridge 的 0.313。

这说明 CNN 已经能从双通道 waveform 中恢复更多 sky 信息，但预测精度仍然远低于真实 sky-overlap oracle 所需水平。当前问题已经不是“模型完全学不到 sky”，而是“学到的 sky 仍然太粗，不能稳定区分正确透镜伴随事件”。

### 下一步建议

如果继续以提高 LIGO SIS/PM 为目标，下一步应转向概率 sky map 或多任务学习：

1. 输出 HEALPix/grid sky probability map，而不是单个 sky unit vector。
2. 使用 soft sky label，避免单点方向回归对不确定区域建模不足。
3. 同时训练 sky direction、detector delay、amplitude ratio 等多任务目标。
4. 在 rerank 中使用 map overlap integral，而不是单点高斯 overlap。
5. 如果数据生成阶段可改，保存每个 detector 的真实到达时间/SNR/phase 作为监督标签，先训练可观测 proxy，再用于 sky-map 预测。


## 2026-06-04 追加实验：概率 sky-map 预测 + overlap integral

新增脚本：

`/root/autodl-tmp/gw-catalog/scripts/experiments/50_ligo_grid_skymap_predictor_rerank.py`

输出目录：

`/root/autodl-tmp/gw-catalog/runs/ligo_grid_skymap_predictor_rerank_20260604/`

日志文件：

`/root/autodl-tmp/gw-catalog/logs/ligo_grid_skymap_predictor_rerank_20260604.log`

### 方法

这一版不再让 sky 模型只输出一个 sky direction 点估计，而是输出一个低分辨率概率 sky map：

```text
LIGO 双通道 waveform -> SkyMapCNN_grid_12x24 -> 12 x 24 sky probability map
```

训练标签由真实 `ra/dec` 生成 soft sky map：

```text
true ra/dec -> sky unit vector -> spherical Gaussian soft label on 12 x 24 grid
```

训练损失：

```text
KLDiv(predicted sky probability map, soft sky label)
```

两条事件之间的 sky 相关性不再用单点高斯近似，而是直接计算概率图重叠积分：

```text
sky_map_overlap = sum(P_event_i(pixel) * P_event_j(pixel))
```

最终 rerank 输入仍保持和前面实验一致的 catalog-level 框架：

```text
log1p_delta_time_obs,
predicted_grid_skymap_overlap,
waveform_score,
waveform_reciprocal_rank
```

### LIGO noisy 结果

| family | sky model | sky best epoch | sky mean error rad | sky median error rad | sky err < 1 rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SIS | SkyMapCNN_grid_12x24 | 3 | 1.318 | 1.258 | 0.354 | 0.093 | 0.182 | 0.232 | 0.424 | 0.544 | 0.827 | 81 |
| PM | SkyMapCNN_grid_12x24 | 3 | 1.332 | 1.289 | 0.342 | 0.286 | 0.723 | 0.945 | 1.000 | 1.000 | 1.000 | 3 |

### 与上一版 CNN direction 对比

| family | method | sky mean error rad | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---:|---:|---:|---:|---:|---:|
| SIS | CNN direction + gaussian overlap | 1.348 | 0.087 | 0.173 | 0.226 | 0.421 | 79 |
| SIS | grid sky-map + overlap integral | 1.318 | 0.093 | 0.182 | 0.232 | 0.424 | 81 |
| PM | CNN direction + gaussian overlap | 1.396 | 0.270 | 0.688 | 0.934 | 1.000 | 3 |
| PM | grid sky-map + overlap integral | 1.332 | 0.286 | 0.723 | 0.945 | 1.000 | 3 |

### 结论

概率 sky-map 方案是有提升的：

- SIS：sky mean error 从 1.348 降到 1.318 rad，R@1 从 0.087 提升到 0.093。
- PM：sky mean error 从 1.396 降到 1.332 rad，R@1 从 0.270 提升到 0.286，R@5 从 0.688 提升到 0.723。

但提升幅度仍然有限，尤其是 LIGO noisy SIS。真实 sky-overlap oracle 在 SIS 上可以达到 R@1 = 0.791，而当前预测 sky-map 只有 R@1 = 0.093，说明主要瓶颈仍然是 sky-map 预测精度不足，而不是 catalog-level rerank 框架本身。

### 当前判断

这一版证明了“从 waveform 预测概率 sky map，再计算两事件 sky_map_overlap”这条路线比单点 sky direction 更合理，也更贴近真实流程。但 12 x 24 粗网格 + 单任务 KL 训练还不足以支撑 LIGO SIS 的高精度检索。

后续如果继续优化，应优先尝试：

1. 更细 sky 网格，例如 18 x 36 或 HEALPix 低阶网格。
2. 多任务训练，同时预测 sky map、trigger-time proxy、detector time delay proxy。
3. 对 SIS 单独调参，因为 SIS 当前比 PM 更受 waveform 混淆影响。
4. 用 validation retrieval R@1/R@5 选择 checkpoint，而不是只按 sky-map KL 选择。
5. 在不新增不可观测物理参数的前提下，增强 waveform backbone，例如 InceptionTime/TCN + attention 替代当前轻量 CNN。

## 2026-06-04 追加实验：SIS 细网格 ResNet sky-map

新增脚本：

`/root/autodl-tmp/gw-catalog/scripts/experiments/51_ligo_sis_resnet_grid18_skymap_rerank.py`

输出目录：

`/root/autodl-tmp/gw-catalog/runs/ligo_sis_resnet_grid18_skymap_rerank_20260604/`

日志文件：

`/root/autodl-tmp/gw-catalog/logs/ligo_sis_resnet_grid18_skymap_rerank_20260604.log`

### 修改内容

相对 50 号概率 sky-map 实验，这一版只针对 LIGO noisy SIS 做验证，主要改动为：

1. sky-map 分辨率从 `12 x 24` 提高到 `18 x 36`。
2. soft label 的角宽度从 `sigma = 0.35 rad` 改为 `sigma = 0.28 rad`。
3. waveform backbone 从轻量 CNN 改成 residual Conv1D + dilation + attention pooling。
4. checkpoint 选择从最低 KL 改成最低 validation sky angular error。

### LIGO noisy SIS 结果

| method | sky model | sky best epoch | sky mean error rad | sky median error rad | sky err < 1 rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid sky-map 12x24 | SkyMapCNN_grid_12x24 | 3 | 1.318 | 1.258 | 0.354 | 0.093 | 0.182 | 0.232 | 0.424 | 0.544 | 0.827 | 81 |
| ResNet grid sky-map 18x36 | SkyMapCNN_grid_18x36 | 2 | 1.311 | 1.250 | 0.360 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |

### 结论

细网格 ResNet 确实继续提高了 sky-map 预测质量：

- sky mean error：1.318 -> 1.311 rad。
- sky median error：1.258 -> 1.250 rad。
- sky error < 1 rad：0.354 -> 0.360。

检索层面的变化更复杂：

- R@1 基本没有变化，仍约为 0.093。
- R@50/R@100/R@500 提升，median rank 从 81 改到 74。

这说明新的 sky-map 预测把正确事件整体往前推了一些，但还没有解决“第一名判别”问题。对 LIGO noisy SIS 来说，仅仅把 sky angular error 从 1.32 rad 降到 1.31 rad 还不够，必须进一步提升 sky-map 的可分辨性，或者让 rerank 更直接优化 top-1 排序。

### 下一步判断

当前最值得继续尝试的方向不是单纯加深模型，而是让训练目标更接近最终检索：

1. 在 validation 上按 R@1/R@5 选择 checkpoint，而不是只按 sky 角误差。
2. 用 pair-level contrastive loss 约束同一透镜系统的两个 sky-map overlap 大于随机负样本。
3. 保持不使用不可观测参数，只从 waveform 预测 sky-map，但训练时加入 paired overlap 监督。
4. 对 rerank 分数做 top-k calibrated ranking，使 sky overlap 主要作用在 waveform 候选前若干百名内，减少全 catalog 噪声候选干扰。

## 2026-06-04 追加实验：Grid18 sky-map 后处理权重搜索

新增脚本：

`/root/autodl-tmp/gw-catalog/scripts/experiments/52_ligo_sis_grid18_rank_fusion.py`

输出目录：

`/root/autodl-tmp/gw-catalog/runs/ligo_sis_grid18_rank_fusion_20260604/`

日志文件：

`/root/autodl-tmp/gw-catalog/logs/ligo_sis_grid18_rank_fusion_20260604.log`

### 目的

复用 51 号实验训练好的 `18 x 36` sky-map checkpoint，不重新训练 sky 模型，只在 validation catalog 上搜索排序融合权重，检查是否是原来的 HistGradient reranker 没有充分利用 sky-map overlap。

参与融合的特征为：

```text
waveform_score_z,
reciprocal_rank_z,
-neg_log1p_delta_time_obs_z,
grid18_skymap_overlap_z
```

权重选择标准：

```text
validation R@1 优先，其次 R@5/R@10/median rank
```

### 最优权重

| waveform | reciprocal rank | time | sky overlap |
|---:|---:|---:|---:|
| 1.0 | 0.0 | 0.5 | 0.5 |

### LIGO noisy SIS 结果

| method | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| HistGradient rerank, grid18 sky-map | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| rank-fusion weight search | 0.089 | 0.170 | 0.218 | 0.367 | 0.445 | 0.653 | 159 |

### 结论

简单线性权重融合没有超过 HistGradient reranker，反而明显降低了中高 Top-k 和 median rank。因此当前瓶颈不是“权重没有调好”，而是预测 sky-map 本身的可分辨性仍然不足，或者需要更贴近 pair/retrieval 目标的训练方式。

后续应避免继续在简单后处理权重上消耗时间，优先尝试：

1. sky-map 训练中加入 pair-level contrastive overlap loss。
2. 训练时直接让同一透镜对的 predicted overlap 高于随机非透镜对。
3. 保持输入只用 waveform，辅助量仍只使用可观测 trigger_time_obs 和预测 sky-map overlap。

## 2026-06-05 追加实验：pair-level contrastive sky-map overlap

本轮目标是验证一个更贴近 catalog 检索的训练目标：不只要求单事件 sky-map 接近真实 `ra/dec` soft label，还要求同一透镜系统两条事件的预测 sky-map overlap 高于随机非透镜对。

核心 pair loss：

```text
P_a = sky map(anchor)
P_p = sky map(true partner)
P_n = sky map(random negative)

log_pos = log(sum(P_a * P_p))
log_neg = log(sum(P_a * P_n))
loss_pair = max(0, margin - log_pos + log_neg)
loss = loss_kl + lambda_pair * loss_pair
```

### 实验 53：从零训练，较强 pair loss

脚本：

`/root/autodl-tmp/gw-catalog/scripts/experiments/53_ligo_sis_pair_contrastive_grid18_skymap_rerank.py`

输出目录：

`/root/autodl-tmp/gw-catalog/runs/ligo_sis_pair_contrastive_grid18_skymap_rerank_20260605/`

设置：

```text
PAIR_MARGIN = 0.20
PAIR_LAMBDA = 0.50
NEGATIVES_PER_ANCHOR = 2
EPOCHS = 12
```

结果：

| method | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ResNet grid18 baseline | 1.311 | 1.250 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| pair contrastive from scratch | 1.366 | 1.314 | 0.083 | 0.169 | 0.221 | 0.415 | 0.526 | 0.828 | 86 |

现象：pair loss 很快下降，但 validation sky angular error 明显变差。说明强 pair loss 会让模型牺牲单事件 sky 定位，学到训练配对上的 overlap 偏好，但泛化到 test catalog 后检索效果下降。

### 实验 54：从 baseline checkpoint 微调，弱 pair loss

脚本：

`/root/autodl-tmp/gw-catalog/scripts/experiments/54_ligo_sis_pair_finetune_grid18_skymap_rerank.py`

输出目录：

`/root/autodl-tmp/gw-catalog/runs/ligo_sis_pair_finetune_grid18_skymap_rerank_20260605/`

设置：

```text
初始化：加载 51 号 ResNet grid18 baseline checkpoint
PAIR_MARGIN = 0.10
PAIR_LAMBDA = 0.05
NEGATIVES_PER_ANCHOR = 1
EPOCHS = 6
```

结果：

| method | sky mean error rad | sky median error rad | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ResNet grid18 baseline | 1.311 | 1.250 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| pair finetune weak | 1.323 | 1.257 | 0.093 | 0.173 | 0.226 | 0.417 | 0.540 | 0.825 | 80 |

弱 pair 微调没有崩掉，但也没有超过 baseline。R@1 基本持平，Top-k 和 median rank 略差。

### 当前结论

pair-level contrastive overlap 的方向是合理的，但不能直接裸加到 sky-map 训练里。当前两组实验说明：

1. 强 pair loss 会破坏单事件 sky 定位，导致检索下降。
2. 弱 pair finetune 能保持 R@1，但没有带来额外提升。
3. 对 LIGO noisy SIS 来说，sky-map 预测误差从 1.31 rad 到 1.32/1.36 rad 的变化会明显影响 catalog ranking。
4. 当前最稳的 LIGO noisy SIS 结果仍是 51 号 ResNet grid18 baseline：R@1 = 0.093，median rank = 74。

后续如果继续研究 pair-level 方法，应该改成更稳的训练设计：

1. 冻结 backbone，只微调 sky-map head 或单独训练 overlap calibration head。
2. pair loss 只作用于 top-k 难负样本，而不是完全随机负样本。
3. 使用 validation retrieval R@5/R@50 或 median rank 选择 checkpoint，而不是只按 sky angular error。
4. 将 pair loss 改为 calibration loss：不改变 sky-map 形状，只校准 predicted overlap 的排序分数。
