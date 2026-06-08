# LIGO noisy SIS 性能较差的原因分析与 trigger_time_obs 误差鲁棒性方案

生成日期：2026-06-03

## 1. 研究背景

当前项目已经从直接使用模拟真值 `geocent_time` 计算 `delta_time`，改为使用更接近真实观测的触发时间估计值：

```text
trigger_time_obs = geocent_time_true + timing_jitter
```

再由两个事件的观测触发时间差得到 pair-level 时间特征：

```text
delta_time_obs = abs(trigger_time_obs_i - trigger_time_obs_j)
log1p_delta_time_obs = log(1 + delta_time_obs)
```

该方案避免了直接把模拟真值 `geocent_time` 或 `lens.csv` 中的真实时延 `t_d` 输入模型，更符合真实 catalog 检索设定。

当前 LIGO noisy 数据中，PM 和 SIS 的表现差异非常明显：

```text
LIGO noisy PM  使用 time_only 可以达到 R@1 = 1.000
LIGO noisy SIS 使用 time_only 只能达到 R@1 = 0.219
```

因此需要分析 LIGO noisy SIS 为什么较差，以及后续如果加大 `trigger_time_obs` 观测误差，当前方案是否仍然合理。

## 2. 当前 LIGO noisy SIS 的结果现象

### 2.1 纯 waveform 几乎失效

LIGO SIS 从 pure 到 noisy 的 waveform 检索结果变化如下：

| 数据 | waveform R@1 | R@5 | R@10 | median rank |
|---|---:|---:|---:|---:|
| LIGO pure SIS | 0.954 | 0.983 | 0.989 | 1 |
| LIGO noisy SIS | 0.010 | 0.024 | 0.040 | 1180 |

这个下降非常大，说明 LIGO noisy SIS 中，加噪后 waveform similarity 被严重破坏。原本同一透镜系统的两张像在 pure 数据中非常相似，但 noisy 后在 embedding 空间中不再靠近。

### 2.2 waveform score/rank 在 LIGO noisy 中是负贡献

此前主线使用：

```text
log1p_delta_time_obs + waveform_score + waveform_reciprocal_rank
```

但消融实验发现，在 LIGO noisy SIS 中加入 waveform score/rank 反而降低 R@1：

| 方法 | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|
| time_only | 0.219 | 0.219 | 0.226 | 0.409 | 88 |
| time_waveform | 0.092 | 0.187 | 0.247 | 0.427 | 78 |
| all_observable | 0.093 | 0.204 | 0.263 | 0.472 | 60 |

结论：

```text
LIGO noisy SIS 的 waveform score/rank 当前不可靠，会误导第一位排序。
```

如果目标是 R@1，应该优先使用 `time_only`；如果目标是 R@50/R@100，`all_observable` 可以让更多真配对进入前排，但会牺牲 R@1。

### 2.3 SIS 和 PM 的时间延迟可分性不同

LIGO noisy PM 的 time_only 结果为：

| 方法 | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|
| PM time_only | 1.000 | 1.000 | 1.000 | 1.000 | 1 |

而 LIGO noisy SIS 的 time_only 结果为：

| 方法 | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|
| SIS time_only | 0.219 | 0.219 | 0.226 | 0.409 | 88 |

这说明当前模拟数据中：

```text
PM 的时间延迟分布非常强、非常可分；
SIS 的时间延迟分布与负样本候选重叠更多，单靠时间不能稳定排第一。
```

因此 SIS 更依赖 waveform 或其他物理特征补充；但当前 LIGO noisy waveform 又失效，所以 SIS 最终效果较差。

## 3. LIGO noisy SIS 差的主要原因

综合现有结果，LIGO noisy SIS 较差主要由以下因素叠加造成。

### 3.1 加噪后 waveform 变化过大

LIGO pure SIS waveform R@1 为 0.954，而 noisy SIS 只有 0.010。这说明噪声加入后，同一透镜系统两张像之间的 waveform 相似性被严重破坏。

可能原因包括：

```text
1. LIGO noisy 数据噪声强，真实透镜像的共同 waveform 结构被噪声淹没；
2. 当前 InceptionTime encoder 对 LIGO 多通道 noisy 数据不够鲁棒；
3. 当前预处理如 bandpass、whitening、alignment 还不足以恢复 SIS 的稳定形态；
4. LIGO 多探测器之间的到达时间差、相位差、振幅比没有被充分建模。
```

### 3.2 SIS 时间先验不如 PM 强

PM 的时间差特征几乎可以单独解决检索问题，但 SIS 不行。这说明 SIS 的时间延迟分布更容易和随机负样本重叠。

因此，对于 SIS：

```text
trigger_time_obs 是有用的弱物理先验，但不是充分条件。
```

### 3.3 predicted sky-map 当前不可用

当前 predicted sky-map 的平均角误差约为：

```text
1.53 到 1.57 rad
```

接近随机天空方向。因此由 predicted sky-map 计算的 overlap 不能稳定提升 LIGO noisy SIS。

现有结果也显示：

```text
LIGO noisy SIS trigger_time_obs R@1 = 0.090 或 0.219（取决于是否加入 waveform）
LIGO noisy SIS trigger_time_obs + predicted sky-map R@1 = 0.088
```

sky-map 没有解决问题。

## 4. 当前新的 trigger_time_obs 方案

### 4.1 当前误差模型

当前触发时间观测误差模型为：

```text
sigma_t = max(0.01, 1 / max(SNR, 1))
trigger_time_obs = geocent_time_true + Normal(0, sigma_t)
```

其中：

```text
sigma_t 表示触发时间估计不确定度，单位为秒；
SNR 越高，时间估计越准；
最小误差不低于 0.01 秒。
```

### 4.2 当前 time_only 方法

`time_only` 不是直接使用 `geocent_time`，而是只使用：

```text
log1p_delta_time_obs = log(1 + abs(trigger_time_obs_i - trigger_time_obs_j))
```

它不使用：

```text
waveform_score
waveform_rank
sky-map
sky_sep
ra / dec
SNR
trigger_time_sigma
```

当前 LIGO noisy 中，time_only 的效果为：

| 数据 | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|
| LIGO noisy SIS | 0.219 | 0.219 | 0.226 | 0.409 | 88 |
| LIGO noisy PM | 1.000 | 1.000 | 1.000 | 1.000 | 1 |

## 5. 如果后续加大观测误差，这个方案是否还能用

可以继续用，但必须把它作为一个鲁棒性研究，而不是假设时间永远准确。

当前误差是秒级，而很多透镜时间延迟可能是天、月甚至更长，因此现在 `trigger_time_obs` 非常接近真实时间差，效果很强。后续如果加大观测误差，性能会逐渐下降。

这不是问题，反而可以形成一个重要实验：

```text
observed trigger-time uncertainty robustness study
```

即研究当触发时间估计越来越不准时，catalog-level ranking 的性能如何退化。

## 6. 建议的新实验方案：trigger_time_obs 误差鲁棒性实验

### 6.1 实验变量

在当前误差模型基础上引入误差放大系数：

```text
sigma_t_scaled = sigma_scale * max(0.01, 1 / max(SNR, 1))
trigger_time_obs = geocent_time_true + Normal(0, sigma_t_scaled)
```

建议测试：

| 实验组 | sigma_scale | 含义 |
|---|---:|---|
| T1 | 1 | 当前设置 |
| T2 | 10 | 中等触发时间误差 |
| T3 | 100 | 强触发时间误差 |
| T4 | 1000 | 极强触发时间误差 |
| T5 | 10000 | 接近时间信息失效 |
| T6 | randomized_time | 时间特征随机化 sanity check |

也可以测试固定最小误差：

| 实验组 | min_sigma | 含义 |
|---|---:|---|
| M1 | 0.01 s | 当前设置 |
| M2 | 1 s | 秒级误差 |
| M3 | 10 s | 十秒级误差 |
| M4 | 100 s | 百秒级误差 |
| M5 | 1000 s | 千秒级误差 |
| M6 | 1 day | 天级误差 |

### 6.2 对比方法

每个误差强度下，建议比较：

| 方法 | 输入特征 | 目的 |
|---|---|---|
| waveform only | waveform embedding similarity | 基础 waveform baseline |
| time_only | log1p_delta_time_obs | 时间先验鲁棒性 |
| time_waveform | logdt + waveform score/rank | 检查 waveform 是否仍为负贡献 |
| all_observable | logdt + waveform + sigma + SNR | Top-k 检索是否更稳 |

### 6.3 评价指标

不要只看 R@1，必须同时看：

```text
R@1
R@5
R@10
R@50
R@100
R@500
median true rank
```

原因是强透镜候选检索中，把真配对排进 Top-50 或 Top-100 也有实际价值，后续可交给更精细的物理检验或参数估计流程。

## 7. 预期结果

### 7.1 PM 的预期

PM 当前 time_only 已经达到 R@1=1.000。加大误差后，PM 应该明显下降。

如果下降很快，说明：

```text
PM 当前结果高度依赖时间差分布。
```

这可以作为论文中的一个重要诊断：PM 的时间先验过强，不能单独证明 waveform 检索能力。

### 7.2 SIS 的预期

SIS 当前 time_only R@1=0.219，R@50=0.409。加大误差后，R@1 预计下降，但 Top-k 可能仍保留部分信息。

如果在较大误差下 SIS 的 R@50/R@100 仍高于 waveform baseline，说明：

```text
trigger_time_obs 即使不精确，也能作为弱物理先验帮助缩小候选集合。
```

如果所有指标都接近 waveform baseline，则说明时间信息已经基本失效。

## 8. 推荐的论文表述

建议在论文中不要说时间特征是准确答案，而应表述为：

```text
We use observed trigger-time differences as a physically motivated ranking prior and evaluate its robustness under increasing timing uncertainty.
```

中文表述：

```text
我们将观测触发时间差作为一种物理启发的排序先验，并通过逐步增大触发时间测量误差来评估该先验的鲁棒性。
```

## 9. 当前结论

LIGO noisy SIS 较差的核心原因是：

```text
1. 加噪后 waveform similarity 被严重破坏；
2. SIS 的时间延迟分布不如 PM 可分；
3. predicted sky-map 当前接近随机，不能补救；
4. noisy waveform score/rank 会误导 reranker。
```

当前最有效的短期方案是：

```text
R@1 目标：LIGO noisy SIS 使用 time_only；
Top-k 目标：LIGO noisy SIS 使用 all_observable；
PM：使用 time_only。
```

后续必须做 `trigger_time_obs` 误差鲁棒性实验，检验当观测时间误差变大时，当前方法的性能退化曲线。
