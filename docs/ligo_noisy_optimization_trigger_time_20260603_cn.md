# LIGO noisy 结果优化分析：trigger_time_obs 与可观测特征消融

生成日期：2026-06-03

## 1. 研究目标

当前 LIGO noisy 数据的纯 waveform 检索效果很差，尤其是 SIS：

```text
LIGO noisy SIS waveform R@1 = 0.010
LIGO noisy PM  waveform R@1 = 0.007
```

此前主线使用：

```text
waveform_score + waveform_reciprocal_rank + trigger_time_obs
```

得到：

```text
LIGO noisy SIS R@1 = 0.090
LIGO noisy PM  R@1 = 0.268
```

本轮优化目标是研究 LIGO noisy 的瓶颈，并测试哪些真实可观测特征能提升 catalog-level ranking。

## 2. 本轮测试的特征

本轮没有继续使用 predicted sky-map，因为此前已经证明 predicted sky-map overlap 不稳定，且 sky predictor 误差接近随机方向。

本轮重点测试以下可观测特征：

| 特征组 | 内容 | 说明 |
|---|---|---|
| time_only | `logdt` | 只使用 `log1p_delta_time_obs` |
| time_waveform | `logdt, score, rrank` | 旧主线：时间 + waveform score/rank |
| time_sigma | `logdt, sigma_pair, sigma_min, sigma_max` | 加入触发时间不确定度 |
| time_snr | `logdt, snr_min, snr_max, snr_logratio, snr_sum` | 加入事件 SNR 强度与比例 |
| time_sigma_snr | time + sigma + SNR | 时间、时间误差、SNR 组合 |
| all_observable | time + waveform + sigma + SNR | 当前测试的完整可观测组合 |

其中：

```text
logdt = log(1 + abs(trigger_time_obs_i - trigger_time_obs_j))
sigma_pair = sqrt(sigma_i^2 + sigma_j^2)
snr_logratio = abs(log(snr_i / snr_j))
rrank = 1 / waveform_rank
```

## 3. 结果文件

本轮结果保存于：

```text
runs/ligo_hgb_observable_sweep_20260603/summary.csv
runs/ligo_hgb_observable_sweep_20260603/best_by_family.csv
logs/ligo_hgb_observable_sweep_20260603.log
```

## 4. LIGO noisy SIS 结果

### 4.1 R@1 最优方案

| 方法 | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| time_only | 0.219 | 0.219 | 0.226 | 0.409 | 0.532 | 0.848 | 88 |
| time_waveform | 0.092 | 0.187 | 0.247 | 0.427 | 0.545 | 0.833 | 78 |
| all_observable | 0.093 | 0.204 | 0.263 | 0.472 | 0.598 | 0.882 | 60 |

SIS 如果主要看 R@1，最佳是：

```text
time_only = log1p_delta_time_obs
```

它把 R@1 从旧主线的约 0.090 提升到 0.219。

### 4.2 Top-k 最优方案

如果不只看候选第一位，而是看 Top-k，则 `all_observable` 更有价值：

```text
all_observable R@50 = 0.472
all_observable R@100 = 0.598
all_observable median rank = 60
```

相比 time_only：

```text
time_only R@50 = 0.409
time_only R@100 = 0.532
time_only median rank = 88
```

说明 SNR、时间不确定度和 waveform 分数虽然会干扰第一位排序，但能让更多真配对进入前 50/100。

## 5. LIGO noisy PM 结果

PM 的结果非常明确：只用 `trigger_time_obs` 已经达到满分。

| 方法 | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|
| time_only | 1.000 | 1.000 | 1.000 | 1.000 | 1 |
| time_waveform | 0.259 | 0.643 | 0.900 | 1.000 | 4 |
| time_snr | 0.593 | 0.819 | 0.957 | 0.999 | 1 |
| all_observable | 0.625 | 0.835 | 0.959 | 1.000 | 1 |

结论：LIGO noisy PM 中，`trigger_time_obs` 本身已经足够强；加入 waveform score/rank、SNR 或 sigma 反而破坏 R@1。

这说明当前 PM 数据的时间延迟分布非常可分，可能需要在论文中作为一个风险点讨论：PM 的时间特征过强，可能导致模型主要依赖时间分布，而不是 waveform similarity。

## 6. 关键诊断结论

### 6.1 LIGO noisy 的 waveform score/rank 是负贡献

在 LIGO noisy 中，纯 waveform 模型的召回极低：

```text
SIS waveform R@1 = 0.010
PM  waveform R@1 = 0.007
```

把这样的 waveform score/rank 输入 reranker，会误导排序。

典型例子：

| 数据 | time_only R@1 | time_waveform R@1 | 变化 |
|---|---:|---:|---:|
| LIGO noisy SIS | 0.219 | 0.092 | -0.128 |
| LIGO noisy PM | 1.000 | 0.259 | -0.741 |

所以当前 LIGO noisy 不应默认融合 waveform score/rank。除非先显著提高 waveform 模型本身，否则 waveform 分数不是可靠特征。

### 6.2 SIS 和 PM 应采用不同排序策略

当前最优策略不是统一模型，而是分 family：

| family | 推荐 R@1 主策略 | 推荐 Top-k 策略 |
|---|---|---|
| SIS | time_only | all_observable |
| PM | time_only | time_only |

SIS 中 `all_observable` 能改善 Top-k，但会降低 R@1；PM 中 time_only 全指标最好。

### 6.3 sky-map 不是当前优化方向

此前结果显示 predicted sky-map error 大约：

```text
1.53 到 1.57 rad
```

接近随机方向。因此 predicted sky-map overlap 在当前阶段不能提升 LIGO noisy。

当前优化重点应放在：

```text
1. LIGO noisy waveform 模型本身
2. trigger_time_obs 的时间先验建模
3. 按 SIS/PM 分别设计 catalog-level ranking 策略
```

## 7. 推荐下一步实验

### 7.1 论文主结果策略

建议 LIGO noisy 的主结果暂时使用：

```text
PM: waveform baseline + time_only catalog ranking
SIS: waveform baseline + time_only catalog ranking
```

并补充一个 Top-k 版本：

```text
SIS: all_observable ranking 用于提高 R@50/R@100
```

### 7.2 继续提升 SIS 的方向

SIS 的 R@1 目前从 0.090 提到 0.219，但仍不高。后续可尝试：

```text
1. 对 SIS 建立 time-delay prior，而不是让 HGB 自己学习 logdt
2. 使用 pairwise/listwise ranking loss，优化 rank 而不是二分类概率
3. 重新训练 LIGO noisy waveform 模型，重点提升 waveform Top-50 recall
4. 引入更稳的可观测质量参数，如 chirp mass、duration、band energy
5. 对 LIGO 多通道做 arrival-time lag / cross-correlation 特征
```

### 7.3 需要注意的论文风险

PM 使用 time_only 达到 R@1=1.000，结果过强。论文中需要解释：

```text
PM 数据的时间延迟分布在当前模拟设置中过于可分；
因此 PM 的 catalog ranking 主要验证时间先验是否有效，不能单独证明 waveform 模型能力。
```

对 SIS，则更能体现真实检索困难。

## 8. 当前结论

本轮 LIGO 优化的核心结论是：

```text
LIGO noisy 当前不是 sky-map 问题，而是 waveform score/rank 在 noisy 场景下不可靠。
```

实际提升最明显的修改是：

```text
去掉 noisy waveform score/rank，只用 trigger_time_obs 进行 catalog-level ranking。
```

效果：

```text
LIGO noisy SIS R@1: 0.090 -> 0.219
LIGO noisy PM  R@1: 0.268 -> 1.000
```

如果关注 Top-k 而不是第一位，SIS 可以使用 `all_observable`：

```text
LIGO noisy SIS R@50: 0.421 -> 0.472
LIGO noisy SIS median rank: 80 -> 60
```
