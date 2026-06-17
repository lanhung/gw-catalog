# ET3 observed sky 模拟方案说明

生成时间：2026-06-17

## 1. 文档目的

本文档单独说明当前 ET 三臂数据中 observed sky 的模拟方案，包括：

- ET3 为什么使用独立的 `ET_TRIANGLE` sky 场景；
- `sky_area90_deg2` 如何由 network SNR 动态生成；
- true sky 如何只用于模拟观测误差，而不直接进入 rerank；
- rerank 中的 `sky_overlap`、阶梯函数和二维高斯/log-overlap 如何计算；
- 当前 ET3 实验中的实际误差统计与使用边界。

注意：本文档只描述当前代码实际实现。当前 ET3 observed sky 是 **network-SNR A90 近似模型**，不是完整参数估计得到的 HEALPix skymap，也不是真实三臂响应反演出的 Fisher/localization posterior。

## 2. 代码位置

核心实现：

```text
matchgw/aux_priors/observed_sky.py
matchgw/aux_priors/feature_builder.py
scripts/experiments/88_liao_realistic_p1_p2_rerank.py
```

ET3 全量实验结果目录：

```text
/root/autodl-tmp/gw-catalog/runs/et3_liao_realistic_p1_p2_rerank_20260616
```

关键 audit 文件：

```text
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage2_observed_sky/ET3_noisy_test_observed_sky_audit.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage2_observed_sky/observed_sky_diagnostics.csv
```

## 3. ET3 sky 场景定义

ET3 对应的 sky scenario 是：

```text
detector key: ET3
scenario: ET_TRIANGLE
label: ET three-arm network-SNR A90 approximation
ifos: ET1, ET2, ET3
n_ifos: 3
is_network: True
snr_for_sky: network
sky_model: detector_dependent_A90_approximation
```

参数：

| 参数 | 当前值 | 含义 |
|---|---:|---|
| `a90_ref_deg2` | 100 | network SNR = 12 时的参考 90% 定位面积 |
| `rho_ref` | 12 | 参考 SNR |
| `clip_min_deg2` | 20 | A90 下限，避免过度理想化 |
| `clip_max_deg2` | 1000 | A90 上限，避免极端长尾主导 |
| `lognormal_sigma` | 0.35 | 定位面积散布 |
| `sampling` | `tangent_2d_gaussian` | 天球切平面二维高斯采样 |

和旧 ET 单探测器方案的主要区别：

| detector | scenario | A90 ref | A90 clip | 通道/网络含义 |
|---|---|---:|---|---|
| `ET` | `ET_SINGLE` | 300 deg2 | 50-2000 deg2 | 旧 ET 单干涉仪近似 |
| `ET3` | `ET_TRIANGLE` | 100 deg2 | 20-1000 deg2 | ET1/ET2/ET3 三臂 network SNR 近似 |

因此，当前 ET3 的 sky 误差比旧 ET 单通道更收紧，但仍保留定位误差和随机散布。

## 4. observed sky 生成流程

每个事件先有真实注入天空位置：

```text
ra_true, dec_true
```

这些真实值只用于模拟观测过程，生成观测可用的 summary：

```text
ra_obs, dec_obs, sky_area90_deg2, sky_sigma_rad
```

rerank 模型实际看到的是 observed sky summary，不直接使用 `ra_true/dec_true`。

流程如下：

```text
raw true sky + time/SNR table
  -> select_snr_for_sky(): 取 network SNR
  -> compute_a90_from_snr(): 生成 sky_area90_deg2
  -> a90_to_sigma_rad(): A90 转二维高斯 sigma
  -> sample_observed_sky_center(): 在天球切平面采样 ra_obs/dec_obs
  -> public_observed_sky_features(): 只暴露 observed summary 给 rerank
```

## 5. A90 面积模型

当前 ET3 使用 network SNR 控制定位面积：

```text
A90_raw = a90_ref_deg2 * (rho_ref / max(network_snr, 1))^2 * lognormal_noise
A90 = clip(A90_raw, clip_min_deg2, clip_max_deg2)
```

其中：

```text
lognormal_noise ~ LogNormal(mean=0, sigma=0.35)
```

ET3 默认代入后：

```text
A90_raw = 100 * (12 / max(network_snr, 1))^2 * lognormal_noise
A90 = clip(A90_raw, 20, 1000)
```

含义：

- SNR 越高，定位面积越小，空间约束越强；
- SNR 越低，定位面积越大，空间约束越弱；
- lognormal noise 模拟相同 SNR 下真实定位质量的散布；
- clip 下限 20 deg2 防止高 SNR 事件被模拟成不现实的近乎精确定位；
- clip 上限 1000 deg2 防止极低 SNR 事件产生过大的数值长尾。

## 6. A90 到二维高斯 sigma 的换算

当前把 90% credible area 近似成天球局部切平面的圆形二维高斯。

先把平方度转为 steradian 等效面积：

```text
A90_rad2 = A90_deg2 * (pi / 180)^2
```

二维各向同性高斯中，半径 `r90` 内包含 90% 概率：

```text
P(r <= r90) = 1 - exp(-r90^2 / (2 sigma^2)) = 0.9
r90^2 = 2 sigma^2 ln(10)
```

圆面积：

```text
A90 = pi * r90^2 = 2 pi sigma^2 ln(10)
```

所以：

```text
sigma = sqrt(A90_rad2 / (2 * pi * ln(10)))
```

这也是代码中的 `a90_to_sigma_rad()`。

## 7. 观测中心采样

当前采样方式是 `tangent_2d_gaussian`。

步骤：

1. 把 `ra_true/dec_true` 转成单位向量 `true_direction`。
2. 在该方向的切平面上构造两个正交基 `e1/e2`。
3. 独立采样二维偏移：

```text
dx ~ Normal(0, sigma)
dy ~ Normal(0, sigma)
```

4. 得到观测方向并归一化：

```text
observed_direction = normalize(true_direction + dx * e1 + dy * e2)
```

5. 把单位向量转回：

```text
ra_obs, dec_obs
```

这样比旧的单一径向扰动更接近二维定位误差：误差方向各向同性，误差半径服从二维高斯/Rayleigh 结构。

## 8. audit 表字段

`ET3_noisy_test_observed_sky_audit.csv` 每行对应 catalog 中一个事件，主要字段如下：

| 字段 | 是否给 rerank 使用 | 含义 |
|---|---|---|
| `event_id` | 否 | 事件索引 |
| `scenario` | 否 | 当前为 `ET_TRIANGLE` |
| `sky_model` | 否 | 当前为 `detector_dependent_A90_approximation` |
| `sky_sampling` | 否 | 当前为 `tangent_2d_gaussian` |
| `snr_for_sky_mode` | 否 | 当前为 `network` |
| `snr_for_sky` | 间接 | 生成 A90 的 network SNR |
| `a90_ref_deg2` | 否 | 参考 A90 |
| `ra_true`, `dec_true` | 否 | 注入真值，只用于生成 observed center 和 audit |
| `ra_obs`, `dec_obs` | 是 | 模拟观测到的 sky center |
| `sky_area90_deg2` | 是 | 模拟观测定位面积 |
| `sky_sigma_rad` | 是 | A90 换算出的二维高斯 sigma |
| `uses_h1l1_timing` | 否 | 当前 ET3 为 False |
| `uses_antenna_pattern_localization` | 否 | 当前为 False |
| `uses_healpix_skymap` | 否 | 当前为 False |

传给 rerank 的公开字段由 `public_observed_sky_features()` 控制：

```text
ra_obs
dec_obs
sky_area90_deg2
sky_sigma_rad
```

## 9. pairwise sky_overlap 特征

对任意事件对 `(i, j)`，先由 `ra_obs/dec_obs` 得到观测中心角距离：

```text
theta_ij = angular_sep(ra_obs_i, dec_obs_i, ra_obs_j, dec_obs_j)
```

两个事件的定位误差合并为：

```text
sigma_ij = sqrt(sigma_i^2 + sigma_j^2)
d_sky = theta_ij / sigma_ij
```

当前输出三类主要矩阵：

```text
sky_norm_sep
sky_step_weight
sky_gaussian_weight
sky_log_overlap
```

其中 `sky_norm_sep` 是归一化距离，越小代表空间越一致。

## 10. 阶梯函数

阶梯函数实现为：

```text
score = -0.5, if d_sky > 3.03
score =  0.1, if d_sky <= 3.03
score =  0.5, if d_sky <= 2.15
score =  1.0, if d_sky <= 1.18
```

这些阈值大致对应二维高斯径向概率的不同区域：

| `d_sky` 阈值 | 含义 |
|---:|---|
| 1.18 | 更近的高置信空间一致区域 |
| 2.15 | 中等空间一致区域 |
| 3.03 | 较宽松的空间一致区域 |
| > 3.03 | 空间位置明显不一致，给负分 |

这个特征的优点是鲁棒：它不直接依赖 log-density 的面积归一化项，能稳定表达“空间越近，透镜概率越高”。

## 11. 二维高斯与 log-overlap

连续二维高斯权重：

```text
sky_gaussian_weight = exp(-0.5 * d_sky^2)
```

log-overlap / log-density 形式：

```text
var = sigma_ij^2
sky_log_overlap = -log(2 * pi * var) - theta_ij^2 / (2 * var)
```

含义：

- `theta_ij` 越小，分数越高；
- `sigma_ij` 越小，空间约束越严格；
- `sky_log_overlap` 带有面积归一化项，因此会受 A90 标定影响；
- `sky_gaussian_weight` 只看归一化距离，数值更平滑但不含面积惩罚。

在当前 ET3 结果中，`sky_step_weight` 通常比 `sky_log_overlap` 更稳定，作为主空间特征更合适；`sky_log_overlap` 保留为连续 posterior-overlap 对照。

## 12. 当前 ET3 实测误差统计

统计文件：

```text
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage2_observed_sky/ET3_noisy_test_observed_sky_audit.csv
```

test catalog 规模：9000 个事件。

场景检查：

| 项目 | 值 |
|---|---|
| `scenario` | `ET_TRIANGLE`，9000/9000 |
| `sky_sampling` | `tangent_2d_gaussian`，9000/9000 |
| `snr_for_sky_mode` | `network` |
| `uses_healpix_skymap` | False |
| `uses_antenna_pattern_localization` | False |

实际统计：

| 指标 | min | p10 | median | mean | p90 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| network SNR | 4.8086 | 23.5245 | 67.3819 | 109.2012 | 223.7267 | 335.0055 | 684.9853 | 5192.4605 |
| A90 deg2 | 20.0000 | 20.0000 | 20.0000 | 24.8128 | 27.2626 | 47.3312 | 124.5307 | 930.4150 |
| sigma deg | 1.1758 | 1.1758 | 1.1758 | 1.2640 | 1.3727 | 1.8087 | 2.9339 | 8.0194 |
| observed center offset deg | 0.0237 | 0.5674 | 1.4521 | 1.5907 | 2.7126 | 3.1921 | 4.7003 | 11.2654 |

解释：

- ET3 的 network SNR 普遍较高，所以大量事件被 A90 下限 20 deg2 截断；
- 默认误差下，多数事件的 `sigma` 约为 1.18 deg；
- 实际 observed center 相对 true center 的偏移中位数约 1.45 deg，90% 在 2.71 deg 内；
- 少量低 SNR 或 lognormal 长尾事件会达到更大的 A90 和 offset。

## 13. rerank 中如何使用 observed sky

### 13.1 Stage2：只新增 observed sky

Stage2 的目标是单独测试 observed sky 的贡献：

```text
observed_sky_step_only
observed_sky_log_overlap_only
waveform + observed_sky_step
waveform + observed_sky_log_overlap
A90 sweep: 50 / 100 / 300 deg2
```

组合方式：

```text
score = row_z(waveform_score) + lambda_sky * row_z(sky_score)
```

`lambda_sky` 在 validation full catalog 上从以下网格选择：

```text
[0.25, 0.5, 1.0, 2.0, 4.0]
```

再固定应用到 test catalog。

### 13.2 Stage3：Liao time + observed sky

Stage3 同时融合时间和空间：

```text
score = waveform + lambda_time * liao_time_lr + lambda_sky * observed_sky
```

分别测试：

```text
waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected
waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected
```

`lambda_time` 和 `lambda_sky` 都在 validation 上网格选择。

### 13.3 Stage4/Stage5/Stage7

后续阶段把 observed sky 作为可拓展辅助模块的一部分：

```text
waveform
raw_time
liao_time_lr
observed_sky_step
observed_sky_log_overlap
raw_snr_ratio
amp_time_2d_lr
```

这些分数统一转成 full-catalog matrix，并做 row-wise z-score，再进入 weighted sum 或小模型 reranker。

## 14. 当前 ET3 结果中的作用

从 ET3 Stage2/Stage3/Stage7 结果看：

- `observed_sky_step_only` 已经有较强检索能力，说明空间一致性在 ET3 catalog 中是有效信号；
- `sky_log_overlap_only` 更连续，但受 A90 标定影响，当前整体不如 step 稳定；
- waveform + raw_time + observed_sky_step 是当前真实可用组合里的强结果；
- true sky overlap 只作为上界对照，不能作为真实可用结果；
- observed sky 的主结果应使用 `ra_obs/dec_obs/A90/sigma`，而不是 true sky。

已完成 ET3 stage7 中，真实可用最优组合之一：

```text
waveform + raw_time + observed_sky_step
overall R@1 = 0.9792
overall R@10 = 0.9992
```

Stage5 中 weighted extensible rerank 的最好结果：

```text
weighted_sum_val_selected_extensible
overall R@1 = 0.9840
overall R@10 = 0.9985
top_1pct = 1.0000
```

这些结果说明：当前 ET3 中 observed sky step 与时间/波形互补，作为 rerank 辅助参数是有效的。

## 15. 当前方案的局限

当前方案的边界必须明确：

1. 不是真实 PE skymap  
   当前没有运行 Bayesian parameter estimation，也没有生成 HEALPix posterior。

2. 不是真实 ET 三臂定位反演  
   `ET_TRIANGLE` 使用 network SNR 改变 A90，而不是通过三臂 antenna pattern、到达时间、相位和振幅响应做定位。

3. posterior 形状是圆形二维高斯  
   真实 skymap 往往是非高斯、非圆形、多峰或有长尾结构。

4. A90 与 SNR 的关系是经验近似  
   当前使用 `A90 ∝ SNR^-2` 和 lognormal scatter，适合做工程级 rerank 实验，不等同于真实探测器 localization pipeline。

5. ET3 高 SNR 事件大量触发 A90 下限  
   当前 median A90 为 20 deg2，说明 clip 下限对主分布影响较大；后续如果要更保守，可以提高 `clip_min_deg2` 或扩大 `a90_ref_deg2`。

## 16. 可复现实验入口

生成 observed sky audit 与 Stage2 结果：

```bash
cd /root/autodl-tmp/gw-catalog
/root/miniconda3/bin/python scripts/experiments/90_et3_full_experiment_runner.py --phase p0
```

完整 ET3 rerank：

```bash
cd /root/autodl-tmp/gw-catalog
/root/miniconda3/bin/python scripts/experiments/90_et3_full_experiment_runner.py --phase all
```

单独在代码中生成 ET3 observed sky：

```python
import importlib

exp = importlib.import_module("scripts.experiments.88_liao_realistic_p1_p2_rerank")

sky = exp.make_observed_sky(
    detector="ET3",
    raw_obs=raw_obs,
    time_obs=time_obs,
    seed=302001,
    sampling="tangent_2d_gaussian",
)
```

## 17. 后续可扩展方向

建议按风险和收益分层扩展：

1. A90 sweep 更系统化  
   当前已测 50/100/300 deg2。后续可加入 `clip_min_deg2` sweep，特别检查 ET3 高 SNR 下限对结果的影响。

2. 椭圆二维高斯  
   用 major/minor axis 和 position angle 替代圆形 sigma，更接近真实 skymap。

3. HEALPix toy skymap  
   先生成简化 HEALPix posterior，再用积分 overlap 替代当前解析 log-overlap。

4. detector response localization  
   引入 ET 三臂 antenna pattern、相对到达时间、相对相位/振幅，生成更接近真实 ET3 的 sky posterior。

5. learned calibration  
   保留 `sky_step` 的鲁棒性，同时用 validation 学习 `sky_log_overlap`、time、SNR、waveform 的标定关系，避免简单加权时不同分数尺度互相干扰。

## 18. 当前结论

当前 ET3 observed sky 方案是：

```text
ET_TRIANGLE network-SNR A90 approximation
+ lognormal A90 scatter
+ A90 clip [20, 1000] deg2
+ tangent-plane 2D Gaussian observed center sampling
+ pairwise step / Gaussian / log-overlap sky features
```

它满足当前任务对“参考真实参数分布”“空间信息带平方度范围误差”“空间越近透镜概率越高”“阶梯函数与二维高斯”“rerank 辅助参数可拓展”的工程要求。

但它仍是可控近似，不应表述成真实 ET 三臂 skymap。论文或汇报中建议表述为：

```text
We simulate an observed-sky posterior summary for ET3 using a detector-dependent network-SNR A90 approximation, convert the 90% sky area into a local tangent-plane Gaussian uncertainty, and use only the resulting observed center and uncertainty to build pairwise sky-overlap reranking features.
```
