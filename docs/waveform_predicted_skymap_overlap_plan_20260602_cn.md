# 用 waveform 预测 sky map 并替代 sky_sep 的方案说明

生成日期：2026-06-02

## 1. 修改原因

当前更真实的实验设定中，`ra`、`dec` 不能作为配对模型的直接输入。因此，原来的：

```text
sky_sep = angular_sep(ra_i, dec_i, ra_j, dec_j)
```

不能再作为 catalog-level rerank 特征使用。

原因是：真实观测场景下，事件不会直接给出一个可靠的精确天空点位置；更合理的是得到一个天空定位概率分布，即 sky localization probability map。因此，应把原来的 `sky_sep` 改成：

```text
sky_map_overlap
```

## 2. 新方案流程

新的流程是：

```text
单条事件 waveform
    -> 机器学习模型快速预测 sky map
两条事件的 predicted sky maps
    -> 计算 sky_map_overlap
原来的波形配对模型 + delta_time + sky_map_overlap
    -> 判断是否为强透镜重复成像候选
```

对应到当前代码实现：

```text
waveform -> 原 waveform encoder embedding
embedding -> RidgeCV sky predictor -> predicted sky unit vector + uncertainty
两个 predicted sky maps -> predicted_log_sky_map_overlap
[delta_time, predicted_log_sky_map_overlap, waveform_score, waveform_rank]
    -> catalog-level reranker
```

## 3. 新增代码

新增脚本：

```text
scripts/experiments/39_waveform_predicted_skymap_rerank.py
```

该脚本用于替代直接使用 `sky_sep` 的主实验脚本。

## 4. ra/dec 的使用边界

新方案中，`ra`、`dec` 仍然会在训练阶段出现，但用途被严格限制为 sky-map 预测器的监督标签。

允许：

```text
训练 sky-map predictor 时，用模拟数据中的 ra/dec 作为监督标签。
```

不允许：

```text
在 catalog-level reranker 中直接输入 ra、dec 或 sky_sep。
```

也就是说，配对模型最终看到的不是：

```text
sky_sep(ra_i, dec_i, ra_j, dec_j)
```

而是：

```text
sky_map_overlap(predicted_skymap_i, predicted_skymap_j)
```

## 5. 当前实现的 sky-map 近似

当前项目还没有真实 HEALPix sky map，因此新脚本先实现一个可运行的高斯近似版本。

每个事件的 sky map 被近似为：

```text
以 waveform 预测天空方向为中心的二维高斯 sky map
```

具体步骤：

```text
1. 用 waveform encoder 得到每个事件的 embedding；
2. 用 train split 的 embedding 预测天空单位向量；
3. 在 val split 上计算预测角误差；
4. 用 val median angular error 作为 sky map 的 sigma；
5. 对两条事件的 predicted sky maps 计算高斯重叠积分。
```

当前 sky predictor：

```text
RidgeCV waveform_embedding_to_sky_unit_vector
```

预测目标不是 `ra/dec` 本身，而是三维天空单位向量：

```text
x = cos(dec) cos(ra)
y = cos(dec) sin(ra)
z = sin(dec)
```

这样可以避免 `ra = 0` 和 `ra = 2π` 的周期边界问题。

## 6. sky_map_overlap 的计算

当前使用二维切平面高斯近似。对两个预测 sky map：

```text
p_i(Ω) = N(mu_i, sigma_i^2 I)
p_j(Ω) = N(mu_j, sigma_j^2 I)
```

重叠积分近似为：

```text
overlap = ∫ p_i(Ω) p_j(Ω) dΩ
```

代码中使用 log overlap：

```text
log_overlap = -log(2π(sigma_i^2 + sigma_j^2))
              - sep(mu_i, mu_j)^2 / (2(sigma_i^2 + sigma_j^2))
```

其中：

```text
sep(mu_i, mu_j)
```

是两个预测天空方向之间的球面角距离。

## 7. 新 reranker 的输入特征

新脚本中的 catalog-level reranker 输入为：

```text
1. log1p_delta_time
2. predicted_log_sky_map_overlap
3. waveform_score
4. waveform_reciprocal_rank
```

不再包含：

```text
sky_sep
ra
dec
```

## 8. 与旧方案的区别

旧方案：

```text
直接读取 ra/dec -> 计算 sky_sep -> 输入 reranker
```

新方案：

```text
waveform -> 预测 sky map -> 计算 sky_map_overlap -> 输入 reranker
```

关键区别是：新方案在推理阶段不依赖真实 `ra/dec` 点估计，而是把天空定位视为由 waveform 快速预测得到的概率信息。

## 9. 论文中建议表述

可以写作：

```text
Instead of using the true sky coordinates directly, we train a lightweight sky-localization surrogate that predicts an approximate sky probability map from the waveform embedding. The catalog-level reranker then uses the overlap between two predicted sky maps, together with the time delay and waveform similarity, to rank lensed counterpart candidates.
```

中文表述：

```text
本文不直接使用事件真实天空坐标，而是训练一个轻量级天空定位替代模型，由单事件波形表征快速预测近似 sky map。目录级重排阶段使用两事件预测 sky map 的重叠积分，并结合到达时间差和波形相似度，对强透镜候选配对进行排序。
```

## 10. 当前实现的局限和后续方向

当前实现仍是近似版本，主要局限包括：

```text
1. sky map 是高斯近似，不是真实 HEALPix posterior map；
2. sky predictor 使用 waveform embedding + RidgeCV，属于轻量 baseline；
3. 当前 sigma 由验证集预测角误差估计，不是事件级不确定度；
4. 后续应替换为专门训练的 sky-localization 网络，输出 HEALPix 概率图或多峰 posterior；
5. sky_map_overlap 可进一步替换为 posterior overlap、credible-region intersection 或 sky-map Bayes factor。
```

推荐后续升级路径：

```text
1. 当前版本：waveform embedding -> predicted unit vector + Gaussian sigma；
2. 下一步：waveform -> HEALPix probability vector；
3. 最终版本：使用真实/仿真的 detector localization posterior，直接计算 sky-map overlap statistic。
```
