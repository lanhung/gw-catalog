# delta_time 与 sky_sep 特征来源和计算方式说明

生成日期：2026-06-02

本文档整理当前 gw-catalog 项目中 `delta_time` 和 `sky_sep` 两个辅助参数的来源、计算方式、代码位置、单位以及论文写作时需要注意的物理含义。

## 1. 总体说明

当前 catalog-level rerank 方法中使用的两个时空辅助参数是：

```text
delta_time
sky_sep
```

它们不是从波形模型中学习出来的，也不是神经网络的隐变量，而是从每个事件的源参数表中直接读取 `geocent_time`、`ra`、`dec` 后计算得到。

当前主方法实际输入 reranker 的不是原始 `delta_time`，而是：

```text
log1p_delta_time = log(1 + |t_i - t_j|)
```

`sky_sep` 则是两个事件天空位置之间的球面角距离。

## 2. 相关代码位置

主要代码文件：

```text
scripts/experiments/21_observable_aux_reranker.py
scripts/experiments/37_all_waveform_time_sky_rerank.py
scripts/experiments/38_rerank_lens_fraction_stress.py
```

其中：

```text
21_observable_aux_reranker.py
```

负责读取事件参数表、构造 observable catalog、添加 realistic 扰动、计算天空角距离。

```text
37_all_waveform_time_sky_rerank.py
```

负责全量 ET/LIGO、pure/noisy、SIS/PM 的 waveform + time-sky catalog-level rerank 实验。

```text
38_rerank_lens_fraction_stress.py
```

负责 10% 透镜事件、90% 非透镜事件的不平衡 catalog 压力测试。

## 3. 原始数据来源

当前代码通过 `catalog_observable_frame` 读取原始事件参数表：

```python
def catalog_observable_frame(data_root: Path, family: str, lensed_idx: np.ndarray, unlensed_idx: np.ndarray) -> pd.DataFrame:
    fam = family.upper()
    lensed = pd.read_csv(data_root / f"{fam}_data_0222" / "lensed_source_samples.csv")
    unlensed = pd.read_csv(data_root / "Unlensed_data_0222" / "source_samples.csv")
    n = len(lensed) // 2
    l1 = lensed.iloc[lensed_idx].copy()
    l2 = lensed.iloc[n + lensed_idx].copy()
    u = unlensed.iloc[unlensed_idx].copy()
    out = pd.concat([l1, l2, u], ignore_index=True)
    return out
```

当前 ET 数据根目录：

```text
/root/autodl-tmp/gw_et_10000_matchstyle_20260527_091859
```

当前 LIGO 数据根目录：

```text
/root/autodl-tmp/gw_ligo_10000_matchstyle_20260527_091859
```

对应参数表路径：

```text
{data_root}/SIS_data_0222/lensed_source_samples.csv
{data_root}/PM_data_0222/lensed_source_samples.csv
{data_root}/Unlensed_data_0222/source_samples.csv
```

## 4. 使用的原始字段

`delta_time` 和 `sky_sep` 只依赖三个字段：

```text
geocent_time
ra
dec
```

含义如下：

| 字段 | 含义 | 当前单位 |
|---|---|---|
| `geocent_time` | 地心到达时间 | 秒 |
| `ra` | 赤经 | 弧度 |
| `dec` | 赤纬 | 弧度 |

当前抽样检查中，数据表中确实包含这些字段。例如：

```text
ra, dec, geocent_time, mass_1_source, mass_2_source, luminosity_distance
```

## 5. lensed 与 unlensed catalog 的构造方式

当前 `lensed_source_samples.csv` 中，前一半样本和后一半样本构成透镜重复成像对：

```python
n = len(lensed) // 2
l1 = lensed.iloc[lensed_idx].copy()
l2 = lensed.iloc[n + lensed_idx].copy()
```

然后再拼接非透镜事件：

```python
u = unlensed.iloc[unlensed_idx].copy()
out = pd.concat([l1, l2, u], ignore_index=True)
```

因此最终 catalog 结构是：

```text
lensed image 1
lensed image 2
unlensed events
```

真实配对关系不是由 `delta_time` 或 `sky_sep` 决定，而是由数据集 metadata 中的 partner 关系给出：

```python
gt = ground_truth_partner(ds.meta)
```

## 6. realistic 模式下的观测扰动

当前主实验使用：

```python
MODE = "realistic"
```

在 `perturb_observables` 中，`realistic` 模式对应：

```python
mass_frac, sky_sigma, dist_frac, spin_sigma, time_sigma = 0.10, 0.08, 0.35, 0.20, 0.05
```

其中与 `delta_time` 和 `sky_sep` 有关的是：

```text
sky_sigma = 0.08
time_sigma = 0.05
```

具体扰动方式：

```python
x["ra"] = np.mod(x["ra"] + rng.normal(0.0, sky_sigma, size=len(x)), 2 * np.pi)
x["dec"] = np.clip(x["dec"] + rng.normal(0.0, sky_sigma, size=len(x)), -np.pi / 2, np.pi / 2)
x["geocent_time"] = x["geocent_time"] + rng.normal(0.0, time_sigma, size=len(x))
```

也就是说，在计算最终特征前：

```text
ra  加入 N(0, 0.08) 弧度扰动，并限制到 [0, 2π)
dec 加入 N(0, 0.08) 弧度扰动，并限制到 [-π/2, π/2]
geocent_time 加入 N(0, 0.05) 秒扰动
```

换算为角度：

```text
0.08 rad ≈ 4.58 degree
```

因此当前 `sky_sep` 不是完全理想的真实坐标差，而是在点估计坐标上加入了简化观测误差后的角距离。

## 7. delta_time 的计算方式

在当前主实验中，`delta_time` 的计算位于：

```text
scripts/experiments/37_all_waveform_time_sky_rerank.py
```

对应代码：

```python
def feature_matrix(obs, scores, ranks, anchors, cands):
    ra = obs['ra'].to_numpy()
    dec = obs['dec'].to_numpy()
    t = obs['geocent_time'].to_numpy()
    return np.column_stack([
        np.log1p(np.abs(t[anchors] - t[cands])),
        aux.angular_sep(ra[anchors], dec[anchors], ra[cands], dec[cands]),
        scores[anchors, cands],
        1.0 / np.maximum(ranks[anchors, cands], 1),
    ]).astype(np.float32)
```

其中：

```text
t_i = 第 i 个事件的 geocent_time
t_j = 第 j 个候选事件的 geocent_time
```

原始时间差是：

```text
delta_time = |t_i - t_j|
```

最终输入 reranker 的特征是：

```text
log1p_delta_time = log(1 + delta_time)
```

这样做的原因是 `geocent_time` 的绝对值很大，不同事件之间的时间差跨度也可能很大。使用 `log1p` 可以压缩动态范围，使树模型更稳定。

如果需要从模型输入特征反推原始时间差：

```text
delta_time = exp(log1p_delta_time) - 1
```

## 8. sky_sep 的计算方式

`sky_sep` 的计算函数位于：

```text
scripts/experiments/21_observable_aux_reranker.py
```

代码如下：

```python
def angular_sep(ra1, dec1, ra2, dec2):
    sin1, cos1 = np.sin(dec1), np.cos(dec1)
    sin2, cos2 = np.sin(dec2), np.cos(dec2)
    cosd = sin1 * sin2 + cos1 * cos2 * np.cos(ra1 - ra2)
    return np.arccos(np.clip(cosd, -1.0, 1.0))
```

对应的球面余弦公式是：

```text
cos(theta) = sin(dec1) sin(dec2) + cos(dec1) cos(dec2) cos(ra1 - ra2)
```

因此：

```text
sky_sep = theta = arccos(cos(theta))
```

单位是：

```text
弧度
```

如果需要换算为角度：

```text
sky_sep_degree = sky_sep * 180 / π
```

## 9. 当前主 rerank 特征顺序

当前主方法 `waveform + time-sky catalog rerank` 中，输入 reranker 的特征顺序是：

```text
1. log1p_delta_time
2. sky_sep
3. waveform_score
4. waveform_reciprocal_rank
```

在代码中对应：

```python
np.column_stack([
    np.log1p(np.abs(t[anchors] - t[cands])),
    aux.angular_sep(ra[anchors], dec[anchors], ra[cands], dec[cands]),
    scores[anchors, cands],
    1.0 / np.maximum(ranks[anchors, cands], 1),
])
```

其中：

```text
waveform_score = 波形 embedding 的相似度分数
waveform_reciprocal_rank = 波形初始排序名次的倒数
```

## 10. only time-sky 实验中的特征

在只使用两个辅助参数的实验中，例如：

```text
scripts/experiments/35_et_time_sky_catalog_aux.py
scripts/experiments/30_ligo_time_sky_catalog_aux.py
```

特征只有：

```text
log1p_delta_time
sky_sep
```

对应代码：

```python
return np.column_stack([
    np.log1p(np.abs(t[anchors] - t[cands])),
    aux.angular_sep(ra[anchors], dec[anchors], ra[cands], dec[cands]),
]).astype(np.float32)
```

该实验用于消融分析，检验 `delta_time + sky_sep` 本身的区分能力。

## 11. 物理解释

强透镜重复成像事件在物理上具有以下特点：

```text
1. 来源于同一个天体物理事件，因此天空位置应当一致或高度重叠；
2. 不同像会因为引力透镜路径差和势阱延迟，在到达时间上存在时间延迟；
3. 波形形态应高度相似，但振幅、相位、到达时间等可能发生变化。
```

因此在 catalog-level rerank 中使用：

```text
delta_time
sky_sep
```

具有物理动机。

不过，当前实现中的 `sky_sep` 是基于 `ra/dec` 点估计的角距离，不是真实 sky localization posterior map 的 overlap。因此论文中建议表述为：

```text
sky_sep is used as a lightweight proxy for sky-localization consistency.
```

中文可以写作：

```text
本文使用两事件天空位置点估计之间的角距离 sky_sep，作为天空定位一致性的轻量近似指标。
```

## 12. 当前实现的局限性

当前 `delta_time` 和 `sky_sep` 的实现有以下局限：

```text
1. sky_sep 使用 RA/DEC 点估计，没有使用完整 sky localization probability map；
2. realistic 扰动是简化高斯扰动，不等价于真实参数估计 posterior；
3. time_sigma = 0.05 s 远小于透镜延迟尺度，因此 geocent_time 扰动对 delta_time 的影响很小；
4. 如果模拟数据中正样本 sky_sep 很小、负样本 sky_sep 很大，time-sky only 方法可能得到过高结果；
5. 当前 delta_time 只看绝对时间差，没有显式建模不同透镜模型下的 time-delay 分布先验。
```

## 13. 后续更真实的改进方向

为了进一步接近真实观测，可以考虑：

```text
1. 用 sky_map_overlap 替代或补充 sky_sep；
2. 使用两事件 sky localization probability maps 的重叠积分；
3. 检查 90% credible region 是否相交；
4. 使用 posterior overlap score；
5. 使用 sky-map Bayes factor / overlap statistic；
6. 对 delta_time 引入透镜模型相关的 time-delay prior；
7. 对 positive / negative 样本绘制 delta_time 和 sky_sep 分布，检查是否存在过强可分性。
```

## 14. 总结

当前代码中：

```text
delta_time 来自两个事件 geocent_time 的绝对差，并最终以 log1p_delta_time 形式输入 reranker。
sky_sep 来自两个事件 ra/dec 的球面角距离，单位为弧度。
```

二者都先经过 `realistic` 模式下的简化观测扰动，再用于 catalog-level rerank。它们是有物理动机的可观测辅助特征，但当前实现仍是轻量近似，论文中需要明确说明其近似性质，并通过消融实验展示它们对最终结果的贡献。
