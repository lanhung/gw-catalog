# gw-catalog 当前研究工作与结果总结

生成时间：2026-05-29

## 1. 当前研究目标

本项目当前从原始 gw 代码转向以 match 项目的数据组织、训练流程和候选检索方式为主体，在此基础上加入 gw 项目中与强透镜引力波检索相关的特点。当前核心任务不是单纯做二分类，而是做 catalog-level 的强透镜候选检索：给定一个事件，在候选星表/目录中找出最可能与其成对的透镜像。

当前关注的主要指标是 Recall@K，尤其是 R@1，即真实匹配候选是否排在第 1 位。

## 2. 当前数据与任务形式

当前主要使用 ET 10000 规模数据进行实验，包含 SIS 和 PM 两类透镜模型，并重点关注 noisy 数据。

任务形式为 catalog-level retrieval：

1. 数据中包含 lensed event 与 unlensed event。
2. 对每个 query event，在整个候选集合中排序。
3. 如果真实 partner 排在前 K 位，则计入 R@K。

这和早期 pair-level 二分类不同。pair-level 是判断两个事件是否匹配；catalog-level 是在一批候选中检索正确匹配，更接近真实强透镜候选搜索场景。

## 3. 已完成的主要代码工作

### 3.1 以 match 流程为主体重构

项目已经更多依据 match 项目的数据加载、训练和检索流程：

- 使用 match 风格的 lensed/unlensed split。
- 使用 embedding 相似度矩阵进行候选排序。
- 用 Recall@K 评价 catalog-level 检索性能。
- 原 gw 中不适合当前 catalog 检索目标的旧逻辑不再作为主体。

### 3.2 ET 10000 新数据适配

已经基于新的数据生成代码生成并接入 ET 10000 数据，并跑通 SIS/PM noisy 的训练和评估。

当前数据生成相关代码在服务器的 createdata / create data 目录中保留，项目内主要记录训练和评估脚本。

### 3.3 多模型实验

已尝试多种 waveform-only 模型和预处理方式，包括：

- InceptionTime
- InceptionAttn
- GatedTCN
- AttnResNet
- DilatedResNet
- ConvNeXt1D
- SEResNet
- CBAMResNet
- PatchTST
- ROCKET-like 方法
- TimesNetLite
- multiband / bandpass / Hilbert 等预处理组合

当前 noisy 波形模型中，综合效果较好的基础模型为：

- InceptionTime
- InceptionAttn_lr5e4
- GatedTCN

因此后续 reranker 和 ensemble 主要基于这三个模型。

## 4. 当前最佳 waveform-only 结果

在不使用辅助参数，只依赖 noisy 波形的情况下，当前最佳结果约为：

| family | 方法 | R@1 | 说明 |
|---|---|---:|---|
| SIS | waveform-only best | 0.4657 | score ensemble + cross encoder z |
| PM | waveform-only best | 0.3683 | score ensemble + waveform reranker |

这个结果说明：只依赖 noisy 波形时，模型已经能学习到一部分透镜像之间的相似性，但噪声会显著破坏波形细节，导致 R@1 仍然偏低。

## 5. 训练速度相关工作

已做过不同数据规模下的训练速度研究，主要目的是评估样本量、epoch 数、模型结构和预处理方式对训练时间与效果的影响。

已有文档：

- `docs/data_scale_speed_study_cn.md`
- `docs/training_speed_optimization_results_cn.md`

当前结论：

1. 训练速度受数据规模、窗口长度、模型结构和预处理方式共同影响。
2. InceptionTime 是较稳定的基线。
3. 更复杂模型不一定带来稳定提升，需要结合 R@1 和训练成本比较。
4. 后续如果专门研究训练加速，可以围绕数据规模缩放、hard negative 采样、缓存 embedding、混合精度和轻量模型继续展开。

## 6. noisy 性能优化工作

围绕 noisy 数据，已经尝试过以下方向：

1. 更换模型结构。
2. bandpass / multiband / Hilbert 等预处理。
3. ensemble 多模型得分融合。
4. waveform reranker。
5. cross-encoder 辅助重排。
6. 加入少量真实场景可获得的辅助参数。

已有详细记录：

- `docs/noisy_r1_optimization_summary_cn.md`
- `experiments_noisy_r1_optimization_log.md`
- `docs/noisy_model_comparison_cn.md`
- `docs/noisy_model_best_summary_table.xlsx`

## 7. 辅助参数实验

### 7.1 辅助参数选择原则

真实场景中不能使用仿真真值或透镜模型真值，因此当前默认不使用：

- lens truth
- source id
- pair id
- `mu`
- `t_d`
- `z_l`

经过讨论后，辅助参数尽量少，只保留更容易从真实观测流程中获得的量。当前推荐使用两个：

- `delta_time`：两个候选事件的触发/地心时间差。
- `sky_sep`：两个候选事件天空定位中心的角距离。

质量、距离、自旋等参数虽然理论上可以估计，但目前不作为默认最小方案，因为它们对参数估计误差、透镜放大和后验不确定性更敏感。

### 7.2 realistic / rough 的含义

为了避免直接使用仿真真值导致结果过于理想化，辅助参数实验设置了不同扰动模式：

| mode | 含义 |
|---|---|
| exact | 直接使用仿真参数，偏理想，只用于估计上限 |
| mild | 加入较小扰动 |
| realistic | 加入中等扰动，模拟较现实的参数估计误差 |
| rough | 加入较大扰动，模拟参数估计很粗糙的情况 |

当前更应重点参考 realistic 结果。

## 8. 两辅助参数全量实验结果

最新全量实验固定只使用：

`delta_time + sky_sep`

流程为：

1. `InceptionTime + InceptionAttn_lr5e4 + GatedTCN` 做 noisy 波形 top-50 召回。
2. `HistGradientBoostingClassifier` 使用两个辅助参数对 top-50 候选重排。
3. 在完整 test split 上评价 catalog-level R@K，每个 family 有 3000 个有效 query。

结果如下：

| family | mode | R@1 | R@5 | R@10 | R@50 | valid |
|---|---|---:|---:|---:|---:|---:|
| SIS | exact | 0.8577 | 0.8600 | 0.8600 | 0.8600 | 3000 |
| SIS | mild | 0.8473 | 0.8600 | 0.8600 | 0.8600 | 3000 |
| SIS | realistic | 0.7997 | 0.8560 | 0.8560 | 0.8573 | 3000 |
| SIS | rough | 0.6320 | 0.8320 | 0.8577 | 0.8600 | 3000 |
| PM | exact | 0.8103 | 0.8103 | 0.8103 | 0.8103 | 3000 |
| PM | mild | 0.8100 | 0.8103 | 0.8103 | 0.8103 | 3000 |
| PM | realistic | 0.8087 | 0.8103 | 0.8103 | 0.8103 | 3000 |
| PM | rough | 0.8077 | 0.8103 | 0.8103 | 0.8103 | 3000 |

对应文件：

- 脚本：`scripts/experiments/24_time_sky_aux_full.py`
- 汇总表：`runs/et10000_time_sky_aux_full/time_sky_aux_full_summary.csv`
- 文档：`docs/time_sky_aux_full_results_cn.md`
- 日志：`logs/et10000_time_sky_aux_full_20260529_145926/time_sky_aux_full.log`

## 9. 和 waveform-only 的对比

| family | 方法 | 辅助参数数量 | R@1 | 提升 |
|---|---|---:|---:|---:|
| SIS | waveform-only best | 0 | 0.4657 | - |
| SIS | time_sky aux realistic | 2 | 0.7997 | +0.3340 |
| PM | waveform-only best | 0 | 0.3683 | - |
| PM | time_sky aux realistic | 2 | 0.8087 | +0.4404 |

结论：只使用两个辅助参数后，realistic 场景下 SIS 和 PM 的 R@1 都达到约 0.8，显著高于纯波形方法。

## 10. 当前最推荐方案

当前推荐作为主线方案的是：

```text
noisy waveform ensemble top-50 retrieval
+ time_sky auxiliary reranker
```

具体为：

```text
InceptionTime + InceptionAttn_lr5e4 + GatedTCN
+ HistGradientBoostingClassifier(delta_time, sky_sep)
```

理由：

1. 只使用两个辅助参数，变量少，解释性强。
2. 不依赖仿真真值或透镜模型真值。
3. realistic 下 SIS R@1=0.7997，PM R@1=0.8087。
4. 相比加质量、距离等更多参数，更符合“尽量少用辅助参数”的要求。

## 11. 当前结果的注意点

1. `exact` 结果偏乐观，不应作为论文主结论。
2. `realistic` 是当前更合适的主要结果，但它仍然是简化的参数扰动，不是真实参数后验。
3. `rough` 下 SIS R@1 降到 0.6320，说明天空定位误差很大时，两个辅助参数还不够。
4. 当前 reranker 是在 waveform ensemble top-50 候选上重排，因此最终上限受第一阶段召回能力限制。
5. PM 的 R@50 约为 0.8103，说明第一阶段召回上限本身约在这个水平附近，后续提升 PM 需要先提高 waveform/top-k 召回。

## 12. 后续建议

### 12.1 提升 SIS rough 场景

SIS 在 rough 扰动下降明显，后续可尝试：

- 使用天空定位 posterior overlap，而不是单点 `sky_sep`。
- 引入候选簇级别评分，而不是只做 pair-level reranking。
- 改进 noisy 波形编码器，提高 top-50 召回质量。

### 12.2 提升第一阶段召回上限

当前 R@50 已经限制了最终性能，尤其是 PM。可继续研究：

- hard negative mining。
- 更稳定的 waveform encoder。
- 多尺度/多频带 embedding。
- 更强的 ensemble weighting。

### 12.3 更真实的辅助参数建模

后续论文中更严谨的版本应考虑：

- 从点估计转向 posterior overlap。
- 使用真实参数估计误差分布。
- 分析不同 SNR、不同噪声水平下的稳定性。

### 12.4 论文可写的研究内容

当前项目已经具备以下研究线索：

1. match-style catalog-level 强透镜引力波候选检索框架。
2. noisy 波形下多模型检索性能比较。
3. 训练速度与数据规模关系分析。
4. 少量真实可获得辅助参数对 catalog-level 检索的提升。
5. 参数扰动下的鲁棒性分析。

## 13. 主要文件索引

| 类型 | 路径 |
|---|---|
| 两辅助参数全量脚本 | `scripts/experiments/24_time_sky_aux_full.py` |
| 两辅助参数全量结果 | `runs/et10000_time_sky_aux_full/time_sky_aux_full_summary.csv` |
| 两辅助参数结果文档 | `docs/time_sky_aux_full_results_cn.md` |
| 最小辅助参数消融文档 | `docs/minimal_auxiliary_reranker_results_cn.md` |
| 全辅助参数文档 | `docs/observable_auxiliary_reranker_results_cn.md` |
| noisy 优化总结 | `docs/noisy_r1_optimization_summary_cn.md` |
| 模型对比文档 | `docs/noisy_model_comparison_cn.md` |
| 模型对比 Excel | `docs/noisy_model_best_summary_table.xlsx` |
| 训练速度文档 | `docs/training_speed_optimization_results_cn.md` |
| 数据规模速度文档 | `docs/data_scale_speed_study_cn.md` |
| 优化日志 | `experiments_noisy_r1_optimization_log.md` |

## 14. 当前一句话总结

当前 gw-catalog 已经从早期 pair-level 判断推进到 match-style catalog-level 检索；在 ET 10000 noisy 数据上，纯波形模型 R@1 仍有限，但通过只加入 `delta_time + sky_sep` 两个真实场景较可获得的辅助参数，realistic 场景下 SIS 和 PM 的 R@1 都提升到约 0.8，形成了当前最有价值的主线结果。
