# Liao realistic catalog-level rerank 整体方案与当前结果

生成时间：2026-06-15

## 1. 实验目标

本轮实验的目标不是继续堆叠更多辅助特征，而是把 catalog-level rerank 改造成更接近真实观测流程的 physical prior layer：

```text
waveform score
+ realistic time-delay prior
+ observed sky posterior overlap
+ amplitude / SNR-ratio prior
+ extensible rerank module
-> catalog-level lensed-system retrieval
```

核心约束来自 `gw_catalog_liao_realistic_rerank_plan.md`：

1. 时间和 SNR ratio 要参考 Liao / GW-LMC 真实 mock catalog 参数分布。
2. true sky 只能用于生成模拟观测量，不能直接进入主 rerank。
3. 空间信息使用 observed sky posterior overlap，并显式带有 `sky_area90_deg2` 定位误差。
4. 时间和空间先验必须体现 pair 越物理一致，透镜概率越高。
5. 同时测试阶梯函数和二维高斯/log-overlap。
6. rerank 辅助参数模块要可扩展，便于后续替换 SIS/SIE/PM/ET/LIGO/ET+CE 等先验。
7. 实验必须分阶段，每一阶段只新增一个因素，避免混合变量导致不可解释。

## 2. 总体方法

### 2.1 冻结 waveform encoder

本轮不重训 waveform encoder，固定已有 fresh50 mixed SIS/PM encoder、split、catalog size 和评价脚本，只替换或新增 catalog-level auxiliary prior。

这样可以单独回答：

```text
在 waveform 模型不变时，更真实的时间、空间、SNR prior 是否能提升 catalog-level retrieval？
```

### 2.2 主实验输入

主 rerank 输入只允许使用真实观测中可获得或可模拟获得的信息：

| 类型 | 主实验输入 | 说明 |
|---|---|---|
| waveform | waveform similarity / rank / margin | 来自冻结 encoder |
| time | Liao time-delay step / likelihood ratio | 来自 GW-LMC detected image-pair delay 分布 |
| sky | `ra_obs`, `dec_obs`, `sky_area90_deg2` | true sky 只用于生成 observed sky |
| sky pair | `sky_norm_sep`, `sky_step_weight`, `sky_gaussian_weight`, `sky_log_overlap` | 由 observed sky posterior 计算 |
| amplitude | raw SNR ratio, amp-time 2D likelihood ratio | 来自 Liao delay-SNR ratio 联合分布 |

### 2.3 true sky 的使用边界

主实验不直接使用 true `ra/dec`。流程为：

```text
true ra/dec
  -> 按 detector/SNR 生成 sky_area90_deg2
  -> 从 true sky 附近扰动得到 ra_obs/dec_obs
  -> 使用 observed posterior overlap 做 rerank
```

其中：

```text
A90_i = A90_ref * (rho_ref / SNR_i)^2 * lognormal_noise
sigma_sky = sqrt(A90 / (2*pi*ln(10)))
```

本轮 A90 设置：

| detector | baseline A90 | sweep |
|---|---:|---|
| ET single-site | 300 deg2 | 100 / 300 / 1000 deg2 |
| LIGO HL-like | 100 deg2 | 50 / 100 / 200 deg2 |

## 3. 可扩展辅助 prior 模块

新增模块：

```text
matchgw/aux_priors/
    __init__.py
    feature_builder.py
    scorer.py
```

### 3.1 `feature_builder.py`

负责构造可复用 pair-level feature matrix：

| 函数 | 作用 |
|---|---|
| `observed_sky_pair_features` | 从 `ra_obs/dec_obs/sky_sigma_rad` 生成 sky pair 特征 |
| `time_step_score_matrix` | 从 Liao 时延分布分位数生成 time step baseline |
| `rank_feature_matrices` | 从 waveform score 生成 rank / reciprocal rank / margin |

输出空间特征包括：

```text
sky_sep_obs
sky_norm_sep
sky_step_weight
sky_gaussian_weight
sky_log_overlap
```

### 3.2 `scorer.py`

负责 validation set 上的 weighted-sum 权重搜索：

```text
S_final =
    z(waveform)
  + lambda_t z(time)
  + lambda_s z(sky)
  + lambda_a z(amplitude)
```

当特征数较少时做精确网格搜索；特征数较多时做 coordinate search，避免 full-catalog validation 过慢。

## 4. 分阶段实验设计

实验脚本：

```text
scripts/experiments/88_liao_realistic_p1_p2_rerank.py
```

结果目录：

```text
runs/liao_realistic_p1_p2_rerank_20260612/
```

文档目录：

```text
docs/stage*_report_20260612_cn.md
```

### Stage1：真实时间分布

只改时间 prior，不引入 sky、不引入 SNR、不比较监督模型。

| variant | 含义 |
|---|---|
| `liao_time_step_only` | Liao 时延分位数阶梯函数 |
| `liao_time_lr_only` | Liao time-delay likelihood ratio |
| `waveform_plus_liao_time_step_val_selected` | waveform + time step，lambda 从 validation 选 |
| `waveform_plus_liao_time_lr_val_selected` | waveform + time LR，lambda 从 validation 选 |

结论：

| detector | 最佳 Stage1 variant | R@1 | R@5 | R@10 | median rank |
|---|---|---:|---:|---:|---:|
| ET | waveform + Liao time LR | 0.6112 | 0.7527 | 0.8015 | 1 |
| LIGO | Liao time LR only | 0.1445 | 0.4127 | 0.5273 | 9 |

说明：ET 中 time LR 与 waveform 互补明显；LIGO 中 time step 单独 top1 很高，但和 waveform 融合不稳定，说明需要分阶段保留诊断。

### Stage2：observed sky posterior

只改空间 prior，不引入 Liao time、不引入 SNR。

| variant | 含义 |
|---|---|
| `observed_sky_step_only` | 只用 observed sky step |
| `observed_sky_log_overlap_only` | 只用 observed sky Gaussian/log-overlap |
| `waveform_plus_observed_sky_step_val_selected` | waveform + sky step |
| `waveform_plus_observed_sky_log_overlap_val_selected` | waveform + sky log-overlap |
| `a90_*_step_val_selected` | A90 sweep + step |
| `a90_*_gaussian_log_overlap_val_selected` | A90 sweep + Gaussian/log-overlap |

结论：

| detector | 最佳 Stage2 variant | R@1 | R@5 | R@10 | median rank |
|---|---|---:|---:|---:|---:|
| ET | A90=100 step | 0.7900 | 0.9132 | 0.9457 | 1 |
| LIGO | observed sky step only | 0.7710 | 0.7710 | 0.7713 | 1 |

说明：observed sky step 非常强；Gaussian/log-overlap 更平滑但当前不如 step。LIGO 中 sky-only 很强，但与 waveform 简单融合会下降，说明 waveform 与 sky score 的标定不一致，需要后续通过 time+sky 或 learned reranker 处理。

### Stage3：time + observed sky 融合

只融合 Liao time LR 与 observed sky，不加入 SNR。

| variant | 含义 |
|---|---|
| `waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected` | time LR + sky step |
| `waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected` | time LR + sky Gaussian/log-overlap |

结论：

| detector | 最佳 Stage3 variant | R@1 | R@5 | R@10 | median rank |
|---|---|---:|---:|---:|---:|
| ET | time LR + sky step | 0.8960 | 0.9708 | 0.9825 | 1 |
| LIGO | time LR + sky step | 0.6580 | 0.8567 | 0.9073 | 1 |

说明：Stage3 是当前最强、最可解释的主线。时间和空间先验互补明显，尤其 LIGO noisy 从单独 time 或单独 waveform 融合不稳定，提升到 R@10=0.9073。

### Stage4：SNR ratio / amplitude prior

在 time + observed sky Gaussian/log-overlap 基础上，只新增 amplitude/SNR prior。

| variant | 含义 |
|---|---|
| `waveform_plus_time_lr_plus_sky_log_overlap` | Stage4 基础项 |
| `plus_raw_snr_ratio` | 加 raw observed SNR ratio |
| `plus_amp_time_2d_lr` | 加 Liao delay-SNR ratio 2D likelihood ratio |

结论：

| detector | 最佳 Stage4 variant | R@1 | R@5 | R@10 | median rank |
|---|---|---:|---:|---:|---:|
| ET | plus raw SNR ratio | 0.7820 | 0.8877 | 0.9210 | 1 |
| LIGO | plus amp-time 2D LR | 0.3777 | 0.6070 | 0.6772 | 3 |

说明：SNR prior 在当前配置下没有超过 Stage3 的 time+sky step 主线。ET 中 amp-time 2D LR 被 validation 选为 0；LIGO 有小幅收益，但仍低于 Stage3 step 方案。

### Stage5：rerank 模型比较与加权修正

固定同一组 feature，只比较 reranker：

```text
waveform
waveform_reciprocal_rank
waveform_margin
liao_time_lr
sky_norm_sep
sky_log_overlap
amp_time_lr
```

比较模型：

| model | 说明 |
|---|---|
| `weighted_sum_stage4_lambdas` | 使用 Stage4 权重 |
| `weighted_sum_val_selected_extensible` | 使用新模块在 validation 上自动选权重 |
| `logistic_regression` | 线性监督校准 |
| `hgb` | sklearn HistGradientBoosting |
| `mlp_tabular` | 轻量 tabular MLP |
| `lightgbm` | LightGBM 表格 boosting |

RandomForest/ExtraTrees 曾尝试作为 full-catalog 补充模型，但 O(N^2) `predict_proba` 成本过高，跑了 34 分钟仍卡在 ET，因此不作为默认模型。

结论：

| detector | 最佳 Stage5 variant | R@1 | R@5 | R@10 | median rank |
|---|---|---:|---:|---:|---:|
| ET | weighted-sum val-selected | 0.8928 | 0.9640 | 0.9805 | 1 |
| LIGO | weighted-sum val-selected | 0.6035 | 0.7842 | 0.8393 | 1 |

补充观察：

| detector | model | R@1 | R@10 | 说明 |
|---|---|---:|---:|---|
| ET | MLP | 0.7083 | 0.9343 | 低于 weighted-sum |
| ET | HGB | 0.5712 | 0.8842 | 低于 weighted-sum |
| LIGO | LightGBM | 0.6455 | 0.7958 | R@1 高于 weighted-sum，但 R@10 低 |
| LIGO | HGB | 0.5340 | 0.7728 | 低于 weighted-sum |

说明：当前 full-catalog 主力仍应选择 validation-selected weighted-sum。监督 reranker 不稳定，尤其 logistic regression 在当前 hard-negative 采样下泛化很差。

## 5. 当前推荐主线

### 5.1 主结果推荐

当前最优、最可解释、最符合真实观测约束的主结果是：

```text
waveform
+ Liao time-delay likelihood ratio
+ observed sky step weight
+ validation-selected weighted fusion
```

对应 Stage3：

| detector | R@1 | R@5 | R@10 | top 1% | median rank |
|---|---:|---:|---:|---:|---:|
| ET noisy | 0.8960 | 0.9708 | 0.9825 | 0.9972 | 1 |
| LIGO noisy | 0.6580 | 0.8567 | 0.9073 | 0.9903 | 1 |

### 5.2 为什么不是 Stage5 learned reranker

Stage5 的 learned models 没有稳定超过 weighted-sum：

1. full-catalog 排序对 score calibration 极敏感；
2. validation hard-negative 采样与 test full-catalog 分布仍有偏移；
3. HGB/LightGBM 更容易学习局部判别，但 R@10 不一定最优；
4. weighted-sum 更稳定、可解释，也更符合论文主方法叙述。

### 5.3 为什么 sky step 优于 Gaussian/log-overlap

当前 observed sky 是圆形 Gaussian 近似，`sky_log_overlap` 包含面积归一化项，容易被不同 A90 标定影响。阶梯函数只看归一化距离区间，更鲁棒，也更符合“空间一致性”解释：

```text
d_sky <= 1.18          strong match
1.18 < d_sky <= 2.15   moderate match
2.15 < d_sky <= 3.03   weak match
d_sky > 3.03           mismatch
```

## 6. 文件索引

### 6.1 代码

| 文件 | 说明 |
|---|---|
| `matchgw/aux_priors/feature_builder.py` | 可扩展 pair feature 构造 |
| `matchgw/aux_priors/scorer.py` | validation weighted-sum 权重搜索 |
| `scripts/experiments/88_liao_realistic_p1_p2_rerank.py` | Stage1-5 主实验 |
| `scripts/experiments/80_mixed_sis_pm_catalog_modality_compare.py` | mixed SIS/PM catalog 基础加载 |
| `scripts/experiments/81_time_matched_hard_negative_mixed_catalog.py` | hard-negative 与有效 query 工具 |
| `scripts/experiments/84_fresh50_full_catalog_ranking.py` | full-catalog ranking metrics |

### 6.2 结果

| 阶段 | CSV |
|---|---|
| Stage1 | `runs/liao_realistic_p1_p2_rerank_20260612/stage1_liao_time_lr/stage1_liao_time_lr_summary.csv` |
| Stage2 | `runs/liao_realistic_p1_p2_rerank_20260612/stage2_observed_sky/stage2_observed_sky_summary.csv` |
| Stage3 | `runs/liao_realistic_p1_p2_rerank_20260612/stage3_liao_time_plus_observed_sky/stage3_liao_time_plus_observed_sky_summary.csv` |
| Stage4 | `runs/liao_realistic_p1_p2_rerank_20260612/stage4_snr_amplitude_prior/stage4_snr_amplitude_prior_summary.csv` |
| Stage5 | `runs/liao_realistic_p1_p2_rerank_20260612/stage5_reranker_model_compare/stage5_reranker_model_compare_summary.csv` |

### 6.3 阶段报告

```text
docs/stage1_liao_time_lr_report_20260612_cn.md
docs/stage2_observed_sky_report_20260612_cn.md
docs/stage3_liao_time_plus_observed_sky_report_20260612_cn.md
docs/stage4_snr_amplitude_prior_report_20260612_cn.md
docs/stage5_reranker_model_compare_report_20260612_cn.md
```

## 7. 后续建议

1. 将 Stage3 `time LR + observed sky step` 作为论文主表主方法。
2. 将 Stage5 `weighted_sum_val_selected_extensible` 作为可扩展模块版本和强 baseline。
3. 将 `sky_log_overlap` 保留为连续 posterior overlap 对照，但当前不作为主结果。
4. 对 LIGO learned reranker 做 calibration 研究，重点解决 validation hard-negative 与 test full-catalog 分布偏移。
5. 后续扩展到椭圆 Gaussian / HEALPix skymap overlap，替代当前圆形 Gaussian 近似。
6. 若加入 cross-encoder，应只在 Top-K 上精排，并单独报告 candidate recall@K，不能与 full-catalog rerank 混表。
