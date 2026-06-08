# Toy HEALPix SkyMapNet 替代 sky_sep 的实验记录

生成日期：2026-06-02

## 1. 背景

当前更真实的论文设定中，不应直接使用事件的真实 `ra`、`dec`，也不应直接使用由真实 `ra/dec` 计算得到的 `sky_sep`。原因是：真实引力波事件的天空定位不是一个精确点，而是一个 sky localization posterior map。

因此，本轮实验目标是把原来的：

```text
waveform + delta_time + sky_sep
```

替换为：

```text
waveform + delta_time + predicted sky_map_overlap
```

其中 `predicted sky_map_overlap` 必须由单事件 waveform 预测出的 sky map 计算得到，而不能直接读取真实 `ra/dec`。

## 2. 本轮实现方案

按照本地文档《机器学习快速估计 sky_map_overlap 的方案》的建议，本轮实现了第一版 toy HEALPix SkyMapNet 链路：

```text
单个事件 waveform embedding
    -> SkyMapNet
    -> predicted toy HEALPix sky map

两个事件 predicted sky maps
    -> O_min / O_BC overlap

waveform_score + delta_time + predicted O_min + predicted O_BC
    -> catalog-level reranker
```

新增/修改脚本：

```text
scripts/experiments/41_toy_skymapnet_overlap_rerank.py
```

安装依赖：

```text
healpy 1.19.0
```

输出结果：

```text
runs/toy_skymapnet_overlap_rerank_20260602/summary.csv
runs/toy_skymapnet_overlap_rerank_20260602/summary.json
logs/toy_healpix_skymapnet_overlap_rerank_20260602.log
```

## 3. SkyMapNet 输入和输出

### 3.1 输入

当前第一版 SkyMapNet 输入为已有 waveform encoder 输出的 embedding：

```text
waveform -> InceptionTime Siamese encoder -> embedding -> SkyMapNet
```

注意：本轮没有直接把 `ra`、`dec`、`sky_sep` 输入 SkyMapNet 或 reranker。

### 3.2 输出

SkyMapNet 输出一个 HEALPix sky map 概率向量：

```text
Nside = 8
Npix = 768
```

输出经过 softmax 归一化：

```text
Σ_k p_k = 1
```

其中 `p_k` 表示事件位于第 `k` 个 HEALPix pixel 的概率。

## 4. Toy sky map 标签构造

由于当前还没有 BAYESTAR 或 PE 生成的真实 sky localization posterior map，本轮使用 toy sky map 标签。

对每个事件，使用模拟注入的 `ra/dec` 作为训练标签中心，但仅用于训练 SkyMapNet，不进入 reranker。

标签形式为球面高斯近似：

```text
p_k ∝ exp(-theta_k^2 / (2 sigma^2))
```

其中：

```text
theta_k = 真实天空方向与第 k 个 HEALPix pixel 中心之间的角距离
sigma = 0.35 rad
```

本轮设置：

```text
TOY_SIGMA_RAD = 0.35
NSIDE = 8
NPIX = 768
```

## 5. sky_map_overlap 特征

对两个事件的 predicted sky maps：

```text
p_i,k
p_j,k
```

计算两个 overlap 特征。

### 5.1 最小概率重叠 O_min

```text
O_min = Σ_k min(p_i,k, p_j,k)
```

范围：

```text
0 到 1
```

含义：两个概率分布的直接重叠面积。

### 5.2 Bhattacharyya overlap O_BC

```text
O_BC = Σ_k sqrt(p_i,k * p_j,k)
```

范围：

```text
0 到 1
```

含义：两个概率分布的平滑相似度。

## 6. Reranker 输入特征

当前 catalog-level reranker 的输入特征为：

```text
1. log1p_delta_time
2. predicted_O_min
3. predicted_O_BC
4. waveform_score
5. waveform_reciprocal_rank
```

其中：

```text
log1p_delta_time = log(1 + |t_i - t_j|)
waveform_score = 原 waveform embedding 相似度
waveform_reciprocal_rank = waveform 初始排序名次倒数
```

不再包含：

```text
ra
dec
sky_sep
```

## 7. 实验数据范围

本轮先跑 noisy 四组，用于检验更真实场景下 predicted sky_map_overlap 的作用：

```text
ET noisy SIS
ET noisy PM
LIGO noisy SIS
LIGO noisy PM
```

pure 数据暂未作为重点，因为 pure 下 waveform-only 已经较强，noisy 场景更能反映实际难度。

## 8. 结果表

| 数据 | waveform R@1 | 不加 sky map R@1 | toy HEALPix sky map R@1 | R@5 | R@10 | R@50 | SkyMapNet mean error(rad) |
|---|---:|---:|---:|---:|---:|---:|---:|
| ET noisy SIS | 0.407 | 0.518 | 0.528 | 0.719 | 0.774 | 0.875 | 1.537 |
| ET noisy PM | 0.304 | 0.874 | 0.853 | 0.956 | 0.994 | 0.999 | 1.557 |
| LIGO noisy SIS | 0.010 | 0.092 | 0.078 | 0.164 | 0.220 | 0.403 | 1.534 |
| LIGO noisy PM | 0.007 | 0.267 | 0.286 | 0.711 | 0.932 | 1.000 | 1.552 |

其中“不加 sky map”指：

```text
waveform_score + waveform_reciprocal_rank + delta_time
```

即不使用 `sky_sep`，也不使用 predicted sky_map_overlap。

## 9. 结果解读

### 9.1 正向结果

本轮实验已经跑通了完整链路：

```text
event -> predicted sky map -> sky_map_overlap -> catalog-level rerank
```

并且在两个组上有小幅提升：

```text
ET noisy SIS: 0.518 -> 0.528
LIGO noisy PM: 0.267 -> 0.286
```

这说明 predicted sky_map_overlap 作为结构化特征是可以接入当前 pipeline 的。

### 9.2 负向结果

在另外两个组上，加入 predicted sky_map_overlap 反而下降：

```text
ET noisy PM: 0.874 -> 0.853
LIGO noisy SIS: 0.092 -> 0.078
```

因此当前版本不能说 sky_map_overlap 已经稳定提升了效果。

### 9.3 SkyMapNet 仍然很弱

四组 SkyMapNet 的平均天空角误差约为：

```text
1.53 - 1.56 rad
```

这接近随机天空方向，说明当前仅用 waveform embedding 预测 sky map 的能力很弱。

这与之前 Ridge/KNN/ExtraTrees/RandomForest/MLP sky predictor sweep 的结论一致：

```text
当前 waveform embedding 中几乎没有足够可恢复的天空定位信息，或者当前输入特征不足以支持天空定位。
```

## 10. 重要结论

当前最稳妥的结论是：

```text
1. 直接使用 sky_sep 的结果属于 oracle / upper-bound，不适合作为真实部署主结果。
2. 用 waveform 预测 sky map 再计算 overlap 的方案更合理，已经实现了可运行版本。
3. 但当前 SkyMapNet 仅用 waveform embedding，天空定位误差接近随机，因此 predicted sky_map_overlap 贡献有限且不稳定。
4. 在当前版本下，更稳的主结果仍是 waveform + delta_time；predicted sky_map_overlap 应作为探索性实验或未来工作。
```

## 11. 为什么当前 SkyMapNet 效果弱

主要原因可能是输入信息不足。

当前输入：

```text
waveform embedding
```

文档中推荐的正式输入还包括：

```text
多探测器 whitened strain
每个探测器的 optimal SNR 或 matched-filter SNR
探测器间到达时间差
探测器间相位差
探测器间幅度比
network SNR
detector ID
detector response 相关元数据
chirp mass / duration / frequency content 等观测估计特征
```

尤其是天空定位本质上依赖多探测器之间的时间延迟、相位差和幅度响应，仅靠单个 waveform embedding 很难恢复可靠 sky map。

## 12. 后续优化方向

### 12.1 增强 SkyMapNet 输入

下一步应优先加入 detector-level features：

```text
1. 每个 detector 的 SNR
2. detector 间峰值到达时间差
3. detector 间互相关峰值与 lag
4. detector 间幅度比
5. detector 间相位差或频域相位特征
6. network SNR
```

这些特征比单纯 waveform embedding 更接近真实天空定位所需的信息。

### 12.2 提高 sky map 标签真实性

当前 toy sky map 只是围绕注入 `ra/dec` 的高斯标签。正式论文中更理想的是：

```text
BAYESTAR-like teacher sky maps
或
真实/仿真的 detector localization posterior maps
```

然后用 SkyMapNet 做 teacher distillation。

### 12.3 提高 sky map 分辨率

当前使用：

```text
Nside = 8, Npix = 768
```

如果 SkyMapNet 能学到有效定位，再提升到：

```text
Nside = 16, Npix = 3072
Nside = 32, Npix = 12288
```

但在当前 sky error 接近随机的情况下，盲目提高分辨率意义不大。

### 12.4 加入 calibration 检查

后续需要检查：

```text
50% credible region 覆盖率
90% credible region 覆盖率
credible area 与 SNR 的关系
positive / negative pair 的 predicted overlap 分布
```

否则 predicted sky map 即使提高配对性能，也可能存在过度自信或校准不良。

## 13. 论文表述建议

可以写作：

```text
To avoid directly using point-estimated sky separation, we implemented a preliminary SkyMapNet module that predicts a toy HEALPix sky-localization probability map from single-event waveform embeddings. Pairwise sky consistency is then represented by overlap statistics between the two predicted maps, including the minimum-probability overlap and the Bhattacharyya coefficient. This experiment validates the feasibility of the event-to-skymap-to-overlap pipeline. However, with waveform embeddings alone, the predicted sky maps remain weakly localized, leading to only limited and unstable gains. This motivates future extensions using detector-level timing, phase, amplitude-ratio and SNR features, or distillation from rapid Bayesian sky localizers.
```

中文表述：

```text
为避免直接使用点估计天空角距离，本文实现了一个初步的 SkyMapNet 模块，由单事件波形表征预测 toy HEALPix 天空定位概率图，并通过两个预测 sky map 的最小概率重叠和 Bhattacharyya overlap 表征候选事件对的天空一致性。实验验证了 event-to-skymap-to-overlap 链路的可行性。然而，仅使用 waveform embedding 时，预测 sky map 的定位能力仍然较弱，因此带来的性能提升有限且不稳定。后续需要引入探测器级到达时间差、相位差、幅度比、SNR 等特征，或使用快速贝叶斯定位器输出的 teacher sky map 进行蒸馏训练。
```

## 14. 当前建议

当前不建议把 toy SkyMapNet 结果作为主性能结果。更合理的论文安排是：

```text
主结果：waveform only、waveform + delta_time、waveform + delta_time + sky_sep oracle upper bound
探索实验：waveform + delta_time + predicted toy HEALPix sky_map_overlap
未来工作：detector-level SkyMapNet / BAYESTAR teacher distillation
```

这样既能避免直接使用 `sky_sep` 被质疑，也能说明我们已经搭建了更真实 sky_map_overlap 路线，但当前还需要更强的天空定位模型。
