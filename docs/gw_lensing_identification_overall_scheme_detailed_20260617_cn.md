# 引力波透镜识别整体方案详细版

生成时间：2026-06-17

## 1. 总体目标

本项目的目标是做 catalog-level 的强透镜引力波事件识别：给定一个包含 lensed images 和 unlensed events 的事件 catalog，对每个可能的透镜像 query，在整个 catalog 中找出它的真实伴随像，并输出可解释的候选排序。

当前方案不是让 waveform 模型单独完成全部判断，而是采用两层结构：

```text
第一层：waveform encoder
  -> 从多通道引力波波形中学习同源事件相似度

第二层：catalog-level rerank
  -> 融合时间、天空位置、SNR/amplitude 等可观测物理信息
  -> 输出最终候选排序
```

这样设计的原因是：强透镜像之间的 waveform 应该相似，但在全量 catalog 检索中，仅靠 waveform 容易出现近邻混淆。真实透镜系统还应满足时间延迟合理、天空位置一致、幅度/SNR 比例符合透镜像放大关系等条件。因此 rerank 层用于把这些物理一致性作为辅助 prior 加进去。

## 2. 当前主线版本

当前最完整的主线是 ET 三臂数据版本：

```text
ET3 waveform encoder
+ realistic time prior
+ observed sky posterior overlap
+ extensible weighted rerank
```

本轮 ET3 使用重新生成的三臂数据，不是旧的单通道 ET 数据：

```text
raw waveform:      (N, 3, 98304)
model input:       (N, 3, 4096)
detector channels: ET1 / ET2 / ET3
```

当前推荐主结果：

```text
Stage5 weighted_sum_val_selected_extensible
overall R@1  = 0.9840
overall R@5  = 0.9973
overall R@10 = 0.9985
Top1%        = 1.0000
```

这个结果只使用真实可观测或可合理模拟的输入：waveform、trigger time、observed sky、SNR/amplitude，不使用 true sky 做主 rerank 特征。

## 3. 数据设计

### 3.1 事件类型

当前 full-catalog 实验包含三类事件：

| 类型 | 含义 | 是否有真实伴随像 |
|---|---|---|
| SIS | Singular Isothermal Sphere 透镜模型生成的双像事件 | 有 |
| PM | Point Mass 透镜模型生成的双像事件 | 有 |
| unlensed | 非透镜背景事件 | 无 |

每个 lensed family 都有两张透镜像：

```text
image 1: L1
image 2: L2
```

检索任务是：对每个 L1/L2 query，在整个 catalog 中找出它的另一张透镜像。

### 3.2 ET3 数据规模

ET3 原始数据目录：

```text
/root/autodl-tmp/createdata/et3_10000_20260616_1006
```

match-style 数据目录：

```text
/root/autodl-tmp/createdata/et3_10000_20260616_1006_match_root
```

数据规模：

| 数据集 | 事件数 | waveform shape |
|---|---:|---|
| SIS | 10000 systems | `(10000, 3, 98304)` x 2 images |
| PM | 10000 systems | `(10000, 3, 98304)` x 2 images |
| unlensed | 10000 events | `(10000, 3, 98304)` |

full-catalog test 设置：

| 项目 | 数量 |
|---|---:|
| catalog total | 9000 |
| valid lensed query | 6000 |
| SIS lensed images | 3000 |
| SIS unlensed | 1500 |
| PM lensed images | 3000 |
| PM unlensed | 1500 |
| total lensed images | 6000 |
| total unlensed | 3000 |

这个设置比只在小候选集里检索更严格，因为每个 query 都要在 9000 个 catalog event 中排序。

## 4. 多探测器/多通道适配

当前代码已经从单通道输入扩展为可适配不同 detector 数量的结构。

ET3 数据流：

```text
原始 npy:                  (N, 3, 98304)
单个事件:                  (3, 98304)
pad_or_trim + downsample:   (3, 4096)
bandpass:                  (3, 4096)
per-channel zscore:         (3, 4096)
encoder input:              in_channels = 3
```

关键原则：

- 不把 ET1/ET2/ET3 合成一个通道；
- 不只取其中一个通道；
- 模型构建时自动推断 `in_channels`；
- checkpoint 加载时也使用同样的 channel 数，避免旧单通道模型和三通道权重不匹配。

主要适配位置：

| 文件 | 作用 |
|---|---|
| `matchgw/data.py` | 支持 `[time]` 与 `[channels, time]` 输入 |
| `matchgw/pipeline.py` | 自动推断模型输入通道数 |
| `scripts/experiments/80_mixed_sis_pm_catalog_modality_compare.py` | mixed SIS/PM encoder 支持 ET3 |
| `matchgw/aux_priors/observed_sky.py` | detector-dependent sky scenario |
| `scripts/experiments/90_et3_full_experiment_runner.py` | ET3 全量实验入口 |

## 5. Waveform encoder

### 5.1 模型定位

waveform encoder 的作用是学习两段波形是否来自同一个源事件。它输出 embedding，然后通过 embedding 相似度构造 full-catalog score matrix。

当前 ET3 使用：

| 项目 | 值 |
|---|---|
| backbone | `inceptiontime` |
| preprocess | `bandpass` |
| epochs | 50 |
| input channels | 3 |
| input length | 4096 |
| data modes | pure + noisy |

### 5.2 基线结果

ET3 noisy waveform-only：

| variant | R@1 | R@5 | R@10 | Top1% | Median rank |
|---|---:|---:|---:|---:|---:|
| waveform only | 0.6245 | 0.7978 | 0.8542 | 0.9585 | 1 |

解释：

- waveform-only 已经能提供强基线；
- R@10 达到 0.8542，说明三通道 waveform encoder 有效；
- R@1 仍只有 0.6245，说明 full-catalog 中存在大量近邻混淆；
- 因此需要时间、空间和幅度信息做 rerank。

ET3 pure waveform-only：

| variant | R@1 | R@5 | R@10 | Top1% |
|---|---:|---:|---:|---:|
| waveform only | 0.9843 | 0.9953 | 0.9973 | 0.9995 |

pure 结果说明模型结构本身没问题，但 noisy 结果更接近真实观测场景，主结论以 noisy 为准。

## 6. 时间信息方案

### 6.1 raw time

raw time 直接使用 observed trigger time 差：

```text
dt_days = abs(trigger_time_i - trigger_time_j) / 86400
score_time = -log1p(dt_days)
```

时间越近，分数越高。

ET3 noisy 中：

| variant | R@1 | R@5 | R@10 | Median rank |
|---|---:|---:|---:|---:|
| raw time only | 0.1352 | 0.4050 | 0.5298 | 9 |
| waveform + raw time | 0.8580 | 0.9438 | 0.9648 | 1 |

raw time 单独不够，但和 waveform 互补明显。

### 6.2 Liao/GW-LMC time prior

为了参考真实参数分布，当前使用 GW-LMC/Liao mock catalog 中 detected image-pair delay 分布构造 time prior。

ET3 使用：

```text
GW-LMC ET BBH Any_Detected_SNR8
detected pair delay count = 4388
median delay = 37.378 days
p90 delay = 284.698 days
```

测试两类时间 prior：

| prior | 含义 |
|---|---|
| `liao_time_step` | 根据 detected delay 分位数构造阶梯函数 |
| `liao_time_lr` | detected delay vs random catalog delay 的 likelihood-ratio 分数 |

ET3 noisy 中：

| variant | R@1 | R@5 | R@10 | Median rank |
|---|---:|---:|---:|---:|
| Liao time LR only | 0.1297 | 0.4040 | 0.5308 | 9 |
| waveform + Liao time LR | 0.8300 | 0.9310 | 0.9597 | 1 |

结论：Liao time LR 与 waveform 有稳定互补作用，但单独依赖时间无法完成高精度识别。

## 7. observed sky 方案

### 7.1 为什么不用 true sky 直接 rerank

真实观测中不会直接知道 true sky。为了避免信息泄漏，主实验不把 `ra_true/dec_true` 作为 rerank 输入。

当前流程是：

```text
true ra/dec
  -> 根据 detector scenario 和 network SNR 生成 sky_area90_deg2
  -> 在 true sky 附近采样 observed center
  -> 得到 ra_obs / dec_obs / sky_sigma_rad
  -> 只用 observed sky summary 计算 pairwise overlap
```

true sky 只用于模拟观测误差和 audit，不进入主 rerank。

### 7.2 ET3 sky scenario

ET3 使用：

```text
scenario: ET_TRIANGLE
label: ET three-arm network-SNR A90 approximation
ifos: ET1, ET2, ET3
snr_for_sky: network
sampling: tangent_2d_gaussian
```

参数：

| 参数 | 当前值 |
|---|---:|
| `a90_ref_deg2` | 100 |
| `rho_ref` | 12 |
| `clip_min_deg2` | 20 |
| `clip_max_deg2` | 1000 |
| `lognormal_sigma` | 0.35 |

当前不是 HEALPix skymap，也不是完整三臂 localization 反演，而是 network-SNR A90 近似。

### 7.3 A90 动态误差模型

定位面积随 network SNR 动态变化：

```text
A90_raw = 100 * (12 / max(network_snr, 1))^2 * lognormal_noise
A90 = clip(A90_raw, 20, 1000)
lognormal_noise ~ LogNormal(0, 0.35)
```

含义：

- network SNR 越高，A90 越小，空间约束越强；
- network SNR 越低，A90 越大，空间约束越弱；
- lognormal scatter 模拟相同 SNR 下定位质量的散布；
- clip 避免过度理想或极端长尾。

A90 转二维高斯 sigma：

```text
sigma = sqrt(A90_rad2 / (2 * pi * ln(10)))
```

observed center 在天球切平面采样：

```text
dx ~ Normal(0, sigma)
dy ~ Normal(0, sigma)
observed_direction = normalize(true_direction + dx * e1 + dy * e2)
```

### 7.4 ET3 observed sky 实际误差统计

ET3 noisy test audit：

```text
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage2_observed_sky/ET3_noisy_test_observed_sky_audit.csv
```

test catalog：9000 events。

| 指标 | min | p10 | median | mean | p90 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| network SNR | 4.8086 | 23.5245 | 67.3819 | 109.2012 | 223.7267 | 335.0055 | 684.9853 | 5192.4605 |
| A90 deg2 | 20.0000 | 20.0000 | 20.0000 | 24.8128 | 27.2626 | 47.3312 | 124.5307 | 930.4150 |
| sigma deg | 1.1758 | 1.1758 | 1.1758 | 1.2640 | 1.3727 | 1.8087 | 2.9339 | 8.0194 |
| observed center offset deg | 0.0237 | 0.5674 | 1.4521 | 1.5907 | 2.7126 | 3.1921 | 4.7003 | 11.2654 |

解释：

- ET3 network SNR 较高，大量事件触发 A90 下限 20 deg2；
- 默认误差下，sigma 中位数约 1.18 deg；
- observed center 相对 true center 的偏移中位数约 1.45 deg；
- 90% 事件偏移小于约 2.71 deg。

## 8. sky pair feature

对事件对 `(i, j)`：

```text
theta_ij = angular_sep(ra_obs_i, dec_obs_i, ra_obs_j, dec_obs_j)
sigma_ij = sqrt(sigma_i^2 + sigma_j^2)
d_sky = theta_ij / sigma_ij
```

输出三类空间分数：

| feature | 公式/含义 |
|---|---|
| `sky_norm_sep` | `d_sky`，归一化角距离 |
| `sky_step_weight` | 阶梯函数，空间越近分数越高 |
| `sky_gaussian_weight` | `exp(-0.5 * d_sky^2)` |
| `sky_log_overlap` | 二维高斯 log-density/overlap |

### 8.1 阶梯函数

当前阶梯函数：

```text
score = -0.5, if d_sky > 3.03
score =  0.1, if d_sky <= 3.03
score =  0.5, if d_sky <= 2.15
score =  1.0, if d_sky <= 1.18
```

它的作用是明确体现：

```text
空间越近，透镜概率越高；
空间明显不一致，则降低候选优先级。
```

当前 ET3 中，`sky_step_weight` 是最稳定的空间特征。

### 8.2 二维高斯/log-overlap

连续高斯权重：

```text
sky_gaussian_weight = exp(-0.5 * d_sky^2)
```

log-overlap：

```text
var = sigma_ij^2
sky_log_overlap = -log(2 * pi * var) - theta_ij^2 / (2 * var)
```

它更接近 posterior overlap 的连续形式，但会受到 A90 标定和面积归一化项影响。当前实验显示它 Top1% 很高，但 R@1 不如 step，因此更适合作为对照或粗筛信号。

## 9. Rerank 融合模块

### 9.1 统一 score matrix

每一种辅助信息都会转换成 full-catalog score matrix：

```text
waveform_score
raw_time_score
liao_time_lr_score
observed_sky_step_score
observed_sky_log_overlap_score
raw_snr_ratio_score
amp_time_2d_lr_score
```

然后统一做 row-wise z-score：

```text
z(score_ij) = (score_ij - row_mean_i) / row_std_i
```

这样可以减少不同分数尺度不一致的问题。

### 9.2 weighted sum

基础融合形式：

```text
S_final =
    z(waveform)
  + lambda_t * z(time)
  + lambda_s * z(sky)
  + lambda_a * z(amplitude)
```

所有 lambda 都在 validation full catalog 上选择，再固定应用到 test full catalog。

权重网格：

```text
[0.25, 0.5, 1.0, 2.0, 4.0]
```

### 9.3 可拓展 reranker

Stage5 把辅助特征整理成可拓展模块，对比：

| reranker | 说明 |
|---|---|
| weighted sum stage4 lambdas | 使用前一阶段固定权重 |
| weighted sum val-selected extensible | validation 自动选权重 |
| logistic regression | 线性监督模型 |
| HistGradientBoosting | 表格树模型 |
| MLP tabular | 小型表格神经网络 |
| LightGBM | boosting 模型 |

当前结果显示：简单可解释的 validation-selected weighted sum 最稳，复杂 learned model 没有稳定超过它。

## 10. 分阶段实验设计

当前实验遵循“每次只新增一个因素”的原则，避免多个变量混在一起导致无法解释。

| Stage | 目标 | 新增信息 |
|---|---|---|
| Stage0 | baseline | waveform、raw time |
| Stage1 | 真实时间分布 | Liao/GW-LMC time prior |
| Stage2 | observed sky | A90 误差、sky step、Gaussian/log-overlap |
| Stage2b | PDF hard-mask baseline | PDF 中后处理思想的硬规则对照 |
| Stage3 | time + sky | Liao time LR + observed sky |
| Stage4 | amplitude/SNR | raw SNR ratio、amp-time 2D LR |
| Stage5 | rerank 模型比较 | weighted sum / learned reranker |
| Stage6 | catalog graph discovery | 高分候选边与候选簇 |
| Stage7 | modality ablation | waveform/time/sky 单项和组合 |

## 11. ET3 关键结果

### 11.1 Stage0 baseline

| variant | R@1 | R@5 | R@10 | Top1% |
|---|---:|---:|---:|---:|
| waveform only | 0.6245 | 0.7978 | 0.8542 | 0.9585 |
| raw time only | 0.1352 | 0.4050 | 0.5298 | 0.6778 |
| waveform + raw time | 0.8580 | 0.9438 | 0.9648 | 0.9923 |

### 11.2 Stage2 observed sky

| variant | R@1 | R@5 | R@10 | Top1% |
|---|---:|---:|---:|---:|
| observed sky step only | 0.5342 | 0.8247 | 0.9407 | 1.0000 |
| observed sky log overlap only | 0.2370 | 0.6848 | 0.8872 | 0.9998 |
| waveform + observed sky step | 0.8963 | 0.9788 | 0.9908 | 0.9987 |
| waveform + observed sky log overlap | 0.8592 | 0.9362 | 0.9608 | 0.9898 |

结论：observed sky step 是当前最稳定的空间特征。

### 11.3 Stage3 time + sky

| variant | R@1 | R@5 | R@10 | Top1% |
|---|---:|---:|---:|---:|
| waveform + Liao time LR + observed sky step | 0.9763 | 0.9967 | 0.9980 | 0.9998 |
| waveform + Liao time LR + observed sky log overlap | 0.9455 | 0.9853 | 0.9923 | 0.9983 |

结论：时间和空间先验互补明显，Stage3 已经是物理解释很清楚的强方案。

### 11.4 Stage5 extensible reranker

| variant | R@1 | R@5 | R@10 | Top1% |
|---|---:|---:|---:|---:|
| weighted sum val-selected extensible | 0.9840 | 0.9973 | 0.9985 | 1.0000 |
| weighted sum stage4 lambdas | 0.9457 | 0.9857 | 0.9923 | 0.9983 |
| MLP tabular | 0.8302 | 0.9517 | 0.9762 | 0.9832 |
| LightGBM | 0.8548 | 0.9313 | 0.9397 | 0.9498 |
| HGB | 0.8185 | 0.8995 | 0.9187 | 0.9407 |

当前主结果采用：

```text
weighted_sum_val_selected_extensible
```

原因：

- R@1 最高；
- R@10 接近满分；
- 模块化结构方便后续加入新 detector、新 sky posterior、新物理参数；
- 比 learned tabular model 更稳定、更容易解释。

### 11.5 Stage7 modality ablation

Stage7 专门回答“只靠 waveform、只靠 time、只靠 sky、以及各种组合分别如何”。

Overall：

| variant | R@1 | R@5 | R@10 | Top1% |
|---|---:|---:|---:|---:|
| waveform + raw time + observed sky step | 0.9792 | 0.9980 | 0.9992 | 0.9997 |
| waveform + Liao time LR + observed sky step | 0.9757 | 0.9983 | 0.9990 | 0.9995 |
| waveform + observed sky step | 0.8968 | 0.9838 | 0.9932 | 0.9982 |
| waveform + raw time | 0.8580 | 0.9438 | 0.9648 | 0.9923 |
| waveform only | 0.6245 | 0.7978 | 0.8542 | 0.9585 |
| observed sky step only | 0.5422 | 0.8278 | 0.9450 | 1.0000 |
| raw time only | 0.1352 | 0.4050 | 0.5298 | 0.6778 |

SIS/PM 差异：

| 现象 | 解释 |
|---|---|
| waveform 对 SIS 略强 | SIS waveform-only R@10 高于 PM |
| time 对 PM 很强 | PM time-only R@10 接近 0.95，SIS time-only 很弱 |
| sky step 对 SIS/PM 都强 | observed sky step only 两类 R@10 都约 0.94-0.95 |
| waveform + time + sky 最稳 | 同时覆盖 waveform 形态、时间接近和空间一致性 |

## 12. 真实可用结果与上界对照

必须区分两类结果：

| 类型 | 是否可作为主结果 | 例子 |
|---|---|---|
| 真实可用结果 | 可以 | waveform、trigger time、observed sky、SNR/amplitude |
| 上界/泄漏对照 | 不可以 | true sky overlap |

true sky overlap 在实验中可以达到接近满分，但它只用于判断理论上限，不能作为部署或论文主结果。

当前主结果属于真实可用结果：

```text
waveform + observed time/sky/SNR auxiliaries
```

## 13. 当前 LIGO/H1L1 状态

LIGO 当前也已按 H1+L1 双通道数据检查并启动完整重跑。

已确认：

```text
raw LIGO waveform shape:      (10000, 2, 98304)
prepared model input shape:   (2, 4096)
sky scenario:                 LIGO_HL
snr_for_sky:                  network
```

当前 LIGO 的 sky 方案是 H1+L1 network-SNR A90 approximation，不是单探测器 sky 配置；但它仍不是真实 H1-L1 timing/antenna/HEALPix skymap localization。

后台 full run 包含：

```text
LIGO pure fresh50 full-catalog
LIGO noisy fresh50 full-catalog
stage0-stage6 realistic rerank
stage7 modality combinations watcher
```

结果完成后应单独生成 LIGO/H1L1 对应报告，再和 ET3 放在同一总表中比较。

## 14. 代码与结果路径

ET3 主结果：

```text
runs/et3_fresh50_full_catalog_20260616
runs/et3_liao_realistic_p1_p2_rerank_20260616
```

ET3 关键文档：

```text
docs/et3_full_experiment_report_20260616_cn.md
docs/et3_observed_sky_simulation_scheme_20260617_cn.md
docs/et3_stage7_modality_combinations_report_20260616_cn.md
```

关键代码：

```text
matchgw/aux_priors/observed_sky.py
matchgw/aux_priors/feature_builder.py
matchgw/aux_priors/scorer.py
scripts/experiments/88_liao_realistic_p1_p2_rerank.py
scripts/experiments/90_et3_full_experiment_runner.py
scripts/experiments/92_ligo_h1l1_full_experiment_runner.py
scripts/experiments/93_ligo_h1l1_modality_combinations.py
```

## 15. 当前方案结论

当前方案可以概括为：

```text
多通道 waveform encoder
+ 参考真实 mock catalog 的 time-delay prior
+ 带平方度误差的 observed sky posterior summary
+ step / Gaussian / log-overlap 空间赋权
+ validation-selected extensible weighted rerank
```

在 ET3 noisy full-catalog 中：

- waveform-only 已有较强基线，但 R@1 不够；
- time 信息主要对 PM 特别强；
- observed sky step 对 SIS 和 PM 都稳定有效；
- waveform + time + observed sky 显著提升检索；
- Stage5 可拓展 weighted rerank 是当前推荐主结果；
- learned tabular reranker 当前没有稳定超过 weighted sum；
- sky log-overlap 有价值，但当前更适合作为对照或补充，不如 sky step 稳定。

## 16. 后续优化方向

建议后续按以下顺序推进：

1. 完成 LIGO/H1L1 全量结果整理  
   当前后台正在跑，完成后需要和 ET3 做同口径对比。

2. 扩展 observed sky 模型  
   从圆形二维高斯扩展到椭圆 Gaussian，再到 toy HEALPix skymap，最终替换为真实 localization posterior。

3. 系统 sweep A90 和 clip_min  
   ET3 当前大量事件被 A90=20 deg2 下限截断，需要评估更保守定位误差下的稳健性。

4. 优化 learned reranker  
   当前 tabular model 未超过 weighted sum，后续需要更严格的负样本构造、校准和 family-aware 验证。

5. graph discovery 后处理  
   把 pair rank 转换成 catalog graph，分析候选簇、误报边、多像系统扩展能力。

6. 统一文档和复现实验入口  
   对 ET3/LIGO/后续 ET+CE 统一 runner、summary schema、report 模板，方便长期比较。

## 17. 推荐表述

对外介绍当前方案时，建议使用以下表述：

```text
We formulate strongly lensed gravitational-wave identification as a full-catalog retrieval and reranking problem. A multi-channel waveform encoder first provides neural similarity scores, and a catalog-level physical reranker then incorporates realistic time-delay priors, simulated observed-sky posterior overlap with finite sky-localization uncertainty, and amplitude/SNR-related auxiliary features. All auxiliary scores are validated on held-out catalog splits and fused through an extensible weighted reranking module. For ET3, the observed-sky summary is simulated with a network-SNR-dependent A90 model and tangent-plane Gaussian localization errors, ensuring that true sky positions are used only to generate realistic observed quantities rather than as direct reranking inputs.
```
