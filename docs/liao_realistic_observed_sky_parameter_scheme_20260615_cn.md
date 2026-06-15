# Liao realistic rerank observed sky 参数方案

生成时间：2026-06-15

## 1. 目标

本实验中的 sky 参数目标是把原始 catalog 中的真实天空位置退化为更接近真实探测器输出的 observed sky posterior，然后再用 posterior overlap 做 catalog-level rerank。

核心原则：

```text
true sky 不能直接进入主实验 rerank
true sky 只用于生成模拟观测量
rerank 只能使用 ra_obs / dec_obs / sky_area90 / sky_sigma 等 observed posterior 信息
```

完整流程：

```text
true ra/dec
  -> 根据 detector 和 SNR 生成 sky_area90_deg2
  -> 将 A90 转为二维圆形 Gaussian 的 sigma_sky
  -> 在 true sky 附近采样 observed center
  -> 得到 ra_obs / dec_obs / sky_area90_deg2 / sky_sigma_rad
  -> 对 candidate pair 计算 observed sky overlap 特征
  -> 进入 rerank
```

对应代码：

```text
scripts/experiments/88_liao_realistic_p1_p2_rerank.py
matchgw/aux_priors/feature_builder.py
```

## 2. 单事件 observed sky posterior 生成

### 2.1 输入

每个事件已有真实天空位置和观测 SNR：

```text
ra_true
dec_true
snr
```

其中 `ra_true/dec_true` 只用于模拟观测中心，不直接作为 rerank feature。

### 2.2 detector-dependent A90 baseline

当前使用 detector-specific 的 90% 天区定位面积基准：

| detector | baseline A90_ref | rho_ref | clip range | 说明 |
|---|---:|---:|---:|---|
| ET | 300 deg2 | 12 | 50-2000 deg2 | ET single-site baseline |
| LIGO | 100 deg2 | 12 | 10-500 deg2 | LIGO HL-like baseline |

代码配置：

```python
OBSERVED_SKY_CONFIG = {
    "ET": {
        "label": "ET single-site baseline A90=300 deg2",
        "a90_ref_deg2": 300.0,
        "rho_ref": 12.0,
        "clip_min_deg2": 50.0,
        "clip_max_deg2": 2000.0,
        "lognormal_sigma": 0.35,
    },
    "LIGO": {
        "label": "LIGO/2.5G HL-like baseline A90=100 deg2",
        "a90_ref_deg2": 100.0,
        "rho_ref": 12.0,
        "clip_min_deg2": 10.0,
        "clip_max_deg2": 500.0,
        "lognormal_sigma": 0.35,
    },
}
```

### 2.3 A90 与 SNR 的动态关系

每个事件的定位面积不是固定值，而是随 SNR 动态变化：

```text
A90_i = A90_ref * (rho_ref / snr_i)^2 * epsilon_i
```

其中：

```text
A90_i      : 当前事件的 90% 天空定位面积
A90_ref    : detector baseline A90
rho_ref    : 参考 SNR，当前取 12
snr_i      : 当前事件观测 SNR
epsilon_i  : lognormal 随机扰动，模拟观测定位质量波动
```

然后做 clip：

```text
ET:   A90_i = clip(A90_i, 50, 2000)
LIGO: A90_i = clip(A90_i, 10, 500)
```

这个设计体现：

```text
SNR 越高 -> A90 越小 -> sky posterior 越窄 -> 空间约束越强
SNR 越低 -> A90 越大 -> sky posterior 越宽 -> 空间约束越弱
```

### 2.4 A90 sweep

为了测试定位误差敏感性，Stage2 额外做 A90 sweep：

| detector | A90 sweep |
|---|---|
| ET | 100 / 300 / 1000 deg2 |
| LIGO | 50 / 100 / 200 deg2 |

对应问题：

```text
探测器定位面积变差时，observed sky rerank 是否仍然有效？
```

## 3. A90 到 sky sigma 的转换

`sky_area90_deg2` 表示 90% credible region 的面积，不是两个事件之间的角距离。

当前使用二维圆形 Gaussian 近似：

```text
P_i(Omega) ~ N(Omega_obs_i, sigma_i^2)
```

先将 deg2 转为 steradian-equivalent：

```text
A90_rad2 = A90_deg2 * (pi / 180)^2
```

然后计算等效 Gaussian sigma：

```text
sigma_sky = sqrt(A90_rad2 / (2 * pi * ln(10)))
```

来源：二维 Gaussian 中，半径 r 内累计概率为：

```text
P(<r) = 1 - exp(-r^2 / (2 sigma^2))
```

90% 区域满足：

```text
r90^2 = 2 sigma^2 ln(10)
A90 = pi * r90^2 = 2 pi sigma^2 ln(10)
```

因此：

```text
sigma = sqrt(A90 / (2 pi ln(10)))
```

## 4. observed sky center 采样

### 4.1 true sky 转 unit vector

先把真实 `ra_true/dec_true` 转为三维单位向量：

```text
v_true = [cos(dec) cos(ra), cos(dec) sin(ra), sin(dec)]
```

### 4.2 在切平面生成随机扰动方向

生成随机三维 noise，并投影到 true sky 的切平面：

```text
noise = normal(0, 1)
noise_tangent = noise - dot(noise, v_true) * v_true
noise_tangent = normalize(noise_tangent)
```

### 4.3 按 sky sigma 采样角向偏移

当前使用：

```text
radial_offset ~ Normal(0, sigma_sky)
```

然后在球面上旋转：

```text
v_obs = v_true * cos(radial_offset) + noise_tangent * sin(radial_offset)
v_obs = normalize(v_obs)
```

最后转回：

```text
ra_obs = atan2(v_obs_y, v_obs_x)
dec_obs = arcsin(v_obs_z)
```

输出单事件 observed sky posterior summary：

```text
ra_obs
dec_obs
sky_area90_deg2
sky_sigma_rad
```

## 5. pair-level sky 特征

对任意 candidate pair `(i, j)`，只使用 observed posterior：

```text
ra_obs_i, dec_obs_i, sigma_i
ra_obs_j, dec_obs_j, sigma_j
```

### 5.1 observed angular separation

计算两个 observed center 的角距离：

```text
theta_ij = angular_sep((ra_obs_i, dec_obs_i), (ra_obs_j, dec_obs_j))
```

输出：

```text
sky_sep_obs = theta_ij
```

### 5.2 合并定位误差

两个独立 Gaussian posterior 的相对位置误差为：

```text
sigma_ij = sqrt(sigma_i^2 + sigma_j^2)
```

### 5.3 归一化天空距离

```text
d_sky = theta_ij / sigma_ij
```

输出：

```text
sky_norm_sep = d_sky
```

直观解释：

```text
d_sky 越小，两个事件的 observed posterior 越一致，透镜概率越高。
```

## 6. sky step 阶梯函数

当前 step feature 使用 `d_sky` 分段：

| 条件 | sky_step_weight | 解释 |
|---|---:|---|
| d_sky <= 1.18 | 1.0 | 很一致，约 50% Gaussian 区域 |
| 1.18 < d_sky <= 2.15 | 0.5 | 较一致，约 90% Gaussian 区域 |
| 2.15 < d_sky <= 3.03 | 0.1 | 勉强一致，约 99% Gaussian 区域 |
| d_sky > 3.03 | -0.5 | 不一致 |

这个 feature 的优点：

```text
可解释性强
对 A90 面积标定不太敏感
直接体现“空间越近，透镜概率越高”
```

当前结果中，sky step 是最有效的空间特征。

## 7. 二维 Gaussian 权重

连续 Gaussian 权重定义为：

```text
sky_gaussian_weight = exp(-0.5 * d_sky^2)
```

含义：

```text
d_sky = 0      -> weight = 1
d_sky 越大    -> weight 平滑衰减
```

这个 feature 比 step 平滑，但当前实验中不如 step 稳定。

## 8. sky log-overlap

两个二维圆形 Gaussian posterior 的 overlap 可以近似为：

```text
sky_log_overlap =
    -log(2 * pi * sigma_ij^2)
    -theta_ij^2 / (2 * sigma_ij^2)
```

其中：

```text
sigma_ij^2 = sigma_i^2 + sigma_j^2
```

该特征同时考虑：

```text
1. 两个 observed centers 的距离 theta_ij
2. 两个 posterior 的定位面积 sigma_i / sigma_j
```

优点：

```text
连续可导
更接近 posterior overlap 的概率形式
适合 logistic / HGB / LightGBM
```

缺点：

```text
包含 -log(area) 归一化项
对 A90 标定较敏感
当前圆形 Gaussian 是简化近似
```

当前实验中，sky log-overlap 明显弱于 sky step。

## 9. 当前 sky feature 输出

当前 `observed_sky_pair_features` 输出 5 个 pair-level feature matrix：

| feature | 含义 | 用途 |
|---|---|---|
| `sky_sep_obs` | observed centers 的角距离 | 诊断 |
| `sky_norm_sep` | theta / sqrt(sigma_i^2 + sigma_j^2) | 通用空间一致性特征 |
| `sky_step_weight` | 阶梯函数权重 | 当前主实验推荐 |
| `sky_gaussian_weight` | exp(-0.5 d_sky^2) | 连续空间权重对照 |
| `sky_log_overlap` | Gaussian posterior log overlap | learned reranker / 对照 |

## 10. 实验中如何使用 sky feature

### Stage2：只测 sky

Stage2 不使用 time prior 和 SNR prior，只测 sky：

```text
waveform + observed sky step
waveform + observed sky log-overlap
A90 sweep + step
A90 sweep + log-overlap
```

最佳结果：

| detector | best sky-only / sky-fusion variant | R@1 | R@5 | R@10 |
|---|---|---:|---:|---:|
| ET | A90=100 step | 0.7900 | 0.9132 | 0.9457 |
| LIGO | observed sky step only | 0.7710 | 0.7710 | 0.7713 |

### Stage3：time + sky

Stage3 使用：

```text
waveform + Liao time LR + observed sky step
waveform + Liao time LR + observed sky log-overlap
```

最佳结果：

| detector | best variant | R@1 | R@5 | R@10 | median rank |
|---|---|---:|---:|---:|---:|
| ET | time LR + sky step | 0.8960 | 0.9708 | 0.9825 | 1 |
| LIGO | time LR + sky step | 0.6580 | 0.8567 | 0.9073 | 1 |

这说明：

```text
observed sky 本身有效；
与 Liao time LR 融合后更稳定；
sky step 是当前最强空间辅助参数。
```

## 11. 当前方案的近似与局限

当前 sky posterior 是轻量近似，不等价于真实 skymap：

1. 使用圆形 Gaussian，未建模椭圆误差。
2. 未使用 detector antenna pattern 生成真实 skymap。
3. 未使用 HEALPix posterior map。
4. radial offset 使用 Gaussian 近似，真实 posterior 可能非 Gaussian、多峰或长尾。
5. ET/LIGO A90 是合理 baseline，不是严格 detector-localization pipeline 输出。

因此论文中应表述为：

```text
realistic observed-sky posterior approximation
```

而不是：

```text
真实 detector skymap reconstruction
```

## 12. 后续改进方向

1. 椭圆 Gaussian posterior：加入 major/minor axis 和 position angle。
2. HEALPix skymap overlap：用真实二维 posterior map 计算 overlap integral。
3. detector-network localization model：按 ET、LIGO、LVK、ET+CE 分别建模。
4. A90 calibration：用真实注入恢复或公开 skymap catalog 标定 A90-SNR 关系。
5. sky feature calibration：解决 LIGO 中 sky-only 强但 waveform+sky 简单融合下降的问题。
6. learned reranker 中加入 calibration loss 或 group-wise ranking loss，而不是简单 pair classification。

## 13. 当前建议

当前主实验建议使用：

```text
observed sky step weight
```

作为主要空间辅助参数。

保留以下作为消融和补充：

```text
sky_gaussian_weight
sky_log_overlap
A90 sweep
```

主线组合：

```text
waveform + Liao time LR + observed sky step
```

这是当前最强、最稳定、最可解释，并且符合“不直接使用 true sky”约束的方案。
