# Predicted sky-map 与 sky-overlap 误差分析文档

日期：2026-06-05

## 1. 研究目的

当前 LIGO noisy SIS 的 catalog 检索效果仍然较低。为了判断问题到底出在最终 reranker，还是出在 `predicted sky map -> sky_map_overlap` 这一段，本分析专门研究：

```text
单事件 predicted sky map 的质量如何
两事件 predicted sky_map_overlap 的正负样本区分能力如何
这些误差为什么会导致最终 R@10 难以提升
```

本分析基于当前主线模型：

```text
51_ligo_sis_resnet_grid18_skymap_rerank.py
```

即：

```text
LIGO waveform -> ResNet Conv1D sky-map predictor -> 18 x 36 sky probability map
两事件 sky probability maps -> overlap integral
```

## 2. 当前 predicted sky-map 是怎么得到的

### 2.1 输入

每条事件输入为 LIGO 双探测器 waveform：

```text
H1 / L1 两通道 waveform
shape = (2, time)
```

### 2.2 模型输出

模型输出一个低分辨率概率 sky-map：

```text
18 x 36 = 648 pixels
```

每个 pixel 有一个概率，所有 pixel 概率和为 1：

```text
P_i(pixel), pixel = 1 ... 648
```

### 2.3 训练标签

训练时使用数据中的真实 `ra/dec` 生成 soft sky-map label：

```text
true ra/dec -> sky unit vector -> spherical Gaussian soft label
```

### 2.4 sky_map_overlap 计算

对两条事件 `i` 和 `j`：

```text
sky_map_overlap(i, j) = sum_pixel P_i(pixel) * P_j(pixel)
```

代码中实际常用 log 形式：

```text
log_sky_map_overlap = log(sum(P_i * P_j) + eps)
```

## 3. 单事件 predicted sky-map 质量

测试集：LIGO noisy SIS test split。

### 3.1 角误差

| 指标 | 数值 |
|---|---:|
| sky error mean | 1.320 rad |
| sky error median | 1.273 rad |
| sky error 25% 分位 | 0.815 rad |
| sky error 75% 分位 | 1.771 rad |
| sky error 90% 分位 | 2.208 rad |

解释：

```text
1.320 rad 约等于 75.6 度
1.273 rad 约等于 73.0 度
```

这说明模型能学到一些粗略 sky 倾向，但定位误差仍然很大。

### 3.2 真实 sky pixel 的排名

| 指标 | 数值 |
|---|---:|
| sky pixels 总数 | 648 |
| true pixel rank median | 183 / 648 |
| true pixel rank mean | 205 / 648 |
| true pixel rank 75% 分位 | 296 / 648 |
| true pixel Top1 | 0.002 |
| true pixel Top10 | 0.031 |
| true pixel Top50 | 0.135 |

解释：

真实 sky pixel 通常排在第 `183/648`，并没有进入模型预测的高概率区域。

最关键的是：

```text
true pixel Top10 = 3.1%
```

也就是说，只有约 3.1% 的事件，真实 sky pixel 会出现在预测概率最高的前 10 个 sky pixels 中。

### 3.3 概率图是否足够尖锐

| 指标 | 数值 |
|---|---:|
| true pixel prob median | 0.00217 |
| true pixel prob mean | 0.00211 |
| entropy norm median | 0.981 |
| entropy norm mean | 0.971 |
| top10 probability mass median | 0.0276 |

均匀分布下每个 pixel 概率为：

```text
1 / 648 = 0.00154
```

当前真实 pixel 平均概率约为：

```text
0.00211
```

只比均匀概率高一点点。

归一化熵接近 1：

```text
entropy norm median = 0.981
```

说明 predicted sky-map 非常平，接近均匀分布，不是一个清晰的定位图。

### 3.4 单事件 sky-map 结论

当前 predicted sky-map 的问题不是完全随机，而是：

```text
有弱定位倾向
但概率分布太平
真实 sky 区域不够突出
真实 pixel 排名太低
```

因此它不足以作为强 sky localization 特征。

## 4. sky_map_overlap 的误差表现

### 4.1 true partner overlap 与 best false overlap

对每个 anchor，计算它与 test catalog 中所有 candidate 的 predicted sky-map overlap。

| 指标 | 数值 |
|---|---:|
| true partner overlap mean | 0.001850 |
| true partner overlap median | 0.001781 |
| best false overlap mean | 0.002266 |
| best false overlap median | 0.002054 |
| best false - true log overlap median | 0.103 |

最关键的问题：

```text
best false overlap mean = 0.002266
true partner overlap mean = 0.001850
```

也就是说，对很多 anchor 来说，最高 overlap 的错误候选反而比真实 partner overlap 更高。

这说明 `predicted sky_map_overlap` 的排序信号本身已经很弱，甚至经常把错误候选排在真实 partner 前面。

### 4.2 true partner 的 sky-overlap 排名

| 指标 | 数值 |
|---|---:|
| true partner overlap rank median | 1503 / 4500 |
| true partner overlap rank 75% 分位 | 2882 / 4500 |
| true partner overlap rank 90% 分位 | 3804 / 4500 |

解释：

如果只用 predicted sky_map_overlap 排序，真实 partner 的中位排名是：

```text
1503 / 4500
```

这几乎无法直接支撑 Top10 检索。

### 4.3 positive / negative overlap 随机区分能力

| 指标 | 数值 |
|---|---:|
| positive overlap mean | 0.001850 |
| negative overlap mean | 0.001673 |
| overlap ratio | 1.106 |
| overlap AUC sampled | 0.620 |

解释：

随机正负样本之间的 overlap 只差约 10%。

```text
positive / negative ratio = 1.106
```

AUC 只有：

```text
0.620
```

这说明 predicted sky_map_overlap 对随机负样本也只是弱区分；面对 Top100 hard negatives 时会更弱。

## 5. 哪些 pair 能被 sky-overlap 排好

按真实 partner 的 sky-overlap rank 分箱：

| true overlap rank bin | 数量 | true overlap mean | best false overlap mean | anchor sky error mean | partner sky error mean | anchor true pixel rank median | partner true pixel rank median |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1-10 | 24 | 0.002782 | 0.002817 | 0.885 | 0.901 | 123.5 | 105.0 |
| 10-50 | 69 | 0.002670 | 0.002804 | 0.775 | 0.782 | 135.0 | 134.0 |
| 50-100 | 86 | 0.002535 | 0.002712 | 0.818 | 0.820 | 117.0 | 112.5 |
| 100-500 | 524 | 0.002269 | 0.002479 | 0.987 | 0.973 | 138.0 | 140.0 |
| 500-1000 | 437 | 0.001969 | 0.002246 | 1.190 | 1.194 | 175.0 | 173.0 |
| 1000-5000 | 1860 | 0.001631 | 0.002162 | 1.420 | 1.422 | 196.0 | 198.0 |

规律：

1. 当 anchor 和 partner 的 sky error 都低于约 `0.9 rad` 时，true partner 才比较可能进入 sky-overlap Top10/Top50。
2. 大多数样本落在 `1000-5000` 这个 rank 区间。
3. 这些样本的 anchor / partner sky error 平均约 `1.42 rad`。
4. 真实 pixel rank 越靠后，true partner overlap 越低，错误候选越容易超过真实 partner。

## 6. 为什么导致最终 catalog 结果不好

最终 catalog reranker 输入包括：

```text
trigger_time_obs difference
predicted sky_map_overlap
waveform score
waveform rank
```

其中 `predicted sky_map_overlap` 本应提供 sky localization 约束。但现在它的问题是：

```text
true partner overlap rank median = 1503 / 4500
best false overlap mean > true partner overlap mean
```

因此它不是强特征，而是一个弱且噪声很大的特征。

误差传导链条：

```text
LIGO noisy waveform 定位信息弱
-> predicted sky-map 接近均匀分布
-> 真实 sky pixel 排名低
-> true partner 的 sky maps overlap 不够高
-> best false candidate overlap 经常更高
-> sky-overlap 单独排序很差
-> catalog reranker 无法用它稳定提升 Top10
```

这解释了为什么当前最佳 full-catalog 结果只到：

```text
R@10 = 0.245
```

而不是接近真实 sky oracle 的水平。

## 7. 已尝试优化及效果

### 7.1 temperature sharpening

方法：

```text
P_sharp = P^alpha / sum(P^alpha)
```

最佳 `alpha=2`：

| 指标 | baseline | alpha=2 |
|---|---:|---:|
| entropy norm | 0.971 | 0.942 |
| overlap ratio | 1.105 | 1.163 |
| overlap AUC | 0.619 | 0.616 |
| R@10 | 0.232 | 0.245 |
| median rank | 74 | 71 |

结论：

sharpening 有小幅提升，但没有解决本质问题。因为如果真实 sky pixel 原本不在高概率区，变尖可能也只是把错误区域变得更尖。

### 7.2 entropy sharp training

方法：

```text
SOFT_SIGMA = 0.22
loss = KL + expected angular loss + entropy penalty
```

结果：

```text
R@10 = 0.231
```

没有超过 baseline。

### 7.3 hard-negative overlap finetune

方法：

```text
true partner overlap > hard false overlap
```

结果：

```text
R@10 = 0.234
overlap AUC = 0.606
```

pair loss 下降，但 sky 定位和 overlap AUC 泛化变差。

### 7.4 pair waveform hand-crafted scorer

方法：

使用 waveform pair cross-correlation、幅度比、RMS 比等手工特征，在 Top100 候选池里排序。

结果：

```text
HGB pair waveform R@10 = 0.206
Logistic pair waveform R@10 = 0.179
```

低于原候选 rerank。

## 8. 核心原因总结

当前结果不好，核心不是最终 reranker 没有利用 sky-overlap，而是：

```text
predicted sky-map 本身定位质量不足
predicted sky_map_overlap 对 true partner 和 hard false candidate 区分力不足
```

最关键的证据：

```text
true pixel Top10 = 0.031
true pixel rank median = 183 / 648
entropy norm median = 0.981
true partner overlap rank median = 1503 / 4500
best false overlap mean > true partner overlap mean
```

这说明 sky-overlap 当前只是弱辅助特征，不能承担强定位排序任务。

## 9. 后续优化方向

后续不应只盯 `sky mean angular error`，而应优化以下指标：

```text
true sky region TopK probability
sky-map entropy / calibration
true partner overlap > best false overlap margin
hard-negative overlap AUC
validation catalog R@10
```

更实际的下一步有两个方向：

### 方向 A：深度 pair model

手工 pair waveform 特征不够，应尝试：

```text
Siamese 1D-CNN
InceptionTime pair encoder
cross-attention pair model
```

目标是在 Top100 hard candidates 中直接学习 true partner 与 false candidate 的区别。

### 方向 B：增加 detector-level observable proxy

如果数据生成阶段允许，建议保存：

```text
每个 detector 的 trigger time
每个 detector 的 SNR proxy
每个 detector 的 phase / amplitude proxy
arrival-time difference proxy
```

这些比从 noisy waveform 中间接恢复 sky-map 更接近真实 sky localization 所需信息。

## 10. 直接结论

当前 predicted sky-map 不是完全无效，但质量不足：

```text
它能提供一点粗定位倾向
但概率图太平
真实位置不突出
正负 overlap 差距太小
hard false candidate 经常超过 true partner
```

因此最终 catalog 检索中，`sky_map_overlap` 只能带来小幅提升：

```text
R@10: 0.232 -> 0.245
```

要获得大幅提升，必须增强 pair-level 区分能力或引入更强的物理可观测定位特征。
