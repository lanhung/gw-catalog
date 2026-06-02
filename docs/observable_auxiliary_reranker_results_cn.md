# 可观测辅助参数重排实验结果

目标：在不使用 lens 真值、source id、pair id 的前提下，测试真实场景中可观测/可估计的辅助参数能否提升 noisy top-1 检索。

## 使用的辅助参数

本轮只在二阶段 reranker 中使用辅助参数，不改变 waveform encoder。第一阶段仍由 waveform ensemble 召回 top50 候选，第二阶段用以下 pair-level 特征重排：

- waveform 模型分数和排名：InceptionTime、InceptionAttn、GatedTCN、ensemble。
- 触发时间差：`|geocent_time_i - geocent_time_j|`。
- 天区角距离：由 `ra/dec` 计算。
- 质量一致性：chirp mass、mass ratio、component mass 的相对差异。
- 自旋弱特征：`a_1/a_2/chi_eff_proxy` 差异。
- 距离弱特征：luminosity distance ratio。

未使用：`lens.csv` 中的 `mu_0/mu_1/t_d`、`lens_params.csv` 中的 lens 参数、source id、pair id。

## 估计误差设置

| mode | 含义 |
|---|---|
| exact | 直接使用数据表中的注入/观测字段，作为上界 |
| mild | 质量 5%、天区 0.03 rad、距离 20%、自旋 0.10 的独立扰动 |
| realistic | 质量 10%、天区 0.08 rad、距离 35%、自旋 0.20 的独立扰动 |
| rough | 质量 20%、天区 0.20 rad、距离 60%、自旋 0.35 的独立扰动 |

## 主结果：top50 二阶段辅助参数重排

| family | mode | R@1 | R@5 | R@10 | R@50 | median rank | val AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| SIS | exact | 0.8600 | 0.8600 | 0.8600 | 0.8600 | 1 | 1.000000 |
| PM | exact | 0.8103 | 0.8103 | 0.8103 | 0.8103 | 1 | 1.000000 |
| SIS | mild | 0.8600 | 0.8600 | 0.8600 | 0.8600 | 1 | 1.000000 |
| PM | mild | 0.8103 | 0.8103 | 0.8103 | 0.8103 | 1 | 1.000000 |
| SIS | realistic | 0.8527 | 0.8597 | 0.8600 | 0.8600 | 1 | 0.999999 |
| PM | realistic | 0.8100 | 0.8103 | 0.8103 | 0.8103 | 1 | 1.000000 |
| SIS | rough | 0.7993 | 0.8543 | 0.8580 | 0.8600 | 1 | 0.999958 |
| PM | rough | 0.8083 | 0.8103 | 0.8103 | 0.8103 | 1 | 1.000000 |

对比 waveform-only 当前最佳：SIS R@1=0.4657，PM R@1=0.3683。加入可观测辅助参数后，R@1 明显超过 0.7。

## 单特征消融：在同一 top50 候选内直接排序

| family | score | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---|---:|---:|---:|---:|---:|
| SIS | time_only | 0.2880 | 0.5767 | 0.7023 | 0.8590 | 4 |
| SIS | sky_only | 0.8600 | 0.8600 | 0.8600 | 0.8600 | 1 |
| SIS | mass_only | 0.8600 | 0.8600 | 0.8600 | 0.8600 | 1 |
| SIS | distance_only | 0.8600 | 0.8600 | 0.8600 | 0.8600 | 1 |
| SIS | ensemble_only_on_same_candidates | 0.4597 | 0.6327 | 0.7017 | 0.8163 | 2 |
| PM | time_only | 0.7897 | 0.8103 | 0.8103 | 0.8103 | 1 |
| PM | sky_only | 0.8103 | 0.8103 | 0.8103 | 0.8103 | 1 |
| PM | mass_only | 0.8103 | 0.8103 | 0.8103 | 0.8103 | 1 |
| PM | distance_only | 0.8103 | 0.8103 | 0.8103 | 0.8103 | 1 |
| PM | ensemble_only_on_same_candidates | 0.3593 | 0.5337 | 0.6030 | 0.7557 | 4 |

## 解释与风险

1. 辅助参数能显著提升 top1 排序，说明 waveform-only 的主要瓶颈确实是 top50 内 hard negative 排序，而不是候选完全召回不到。
2. exact/mild 结果非常高，因为模拟数据中的同源多像共享完全相同的质量、天区、距离等注入参数；真实观测中这些只能通过后验估计得到，不会是精确值。
3. `distance_only` 的 exact 消融不应被当成真实可直接使用的强特征，因为透镜放大会影响振幅和距离估计；真实场景中距离只能低权重使用。
4. 更严谨的论文实验应使用 posterior overlap 或显式参数估计误差，而不是直接使用注入真值。

## 建议论文表述

可以把本实验写成：

- `waveform-only baseline`：只用波形 embedding，SIS R@1=0.4657，PM R@1=0.3683。
- `observable-parameter assisted upper bound`：加入观测可估计参数后，SIS R@1=0.86，PM R@1=0.81。
- `noise-aware observable parameter reranking`：在参数估计误差扰动下，SIS rough R@1=0.7993，PM rough R@1=0.8083。

结论：辅助参数是把 noisy 检索从“候选召回”推进到“可靠 top1 排序”的关键方向。
