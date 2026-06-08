# LIGO SIS 当前整体情况与主要问题总结（2026-06-08）

## 1. 研究背景

当前项目目标是做强透镜引力波候选检索，即在一个事件 catalog 中，对每个触发事件检索它最可能对应的透镜伙伴事件。评价指标主要使用 catalog-level ranking 的 `R@1`、`R@5`、`R@10`、`R@50`、`median rank` 等。

目前 ET 数据上的结果相对较好，主要困难集中在 LIGO noisy SIS 数据。LIGO SIS 的问题表现为：纯波形检索能力弱，预测 sky-map 质量弱，加入 predicted sky_map_overlap 后提升有限，最终 catalog-level `R@10` 仍较低。

## 2. 当前最佳 LIGO noisy SIS 结果

当前 LIGO noisy SIS 的最好结果来自：

`runs/ligo_sis_best_skymap_overlap_full_compare_20260605/summary.csv`

使用方法：

- waveform score
- waveform reciprocal rank
- `trigger_time_obs`
- predicted `sky_map_overlap`
- sky probability sharpening，`alpha=2`
- HistGradientBoosting full-catalog reranker

结果：

| 方法 | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline grid18 | 0.093 | 0.176 | 0.232 | 0.433 | 0.560 | 0.832 | 74 |
| alpha=2 sharpening | 0.089 | 0.184 | 0.241 | 0.425 | 0.549 | 0.839 | 75 |
| best full rerun | 0.092 | 0.189 | 0.245 | 0.440 | 0.566 | 0.848 | 71 |

结论：当前最佳 `R@10 = 0.2453`，距离希望达到的 `R@10 > 0.5` 还有明显差距。

## 3. LIGO SIS 为什么难

### 3.1 LIGO noisy 波形本身检索信号弱

从多次实验看，LIGO noisy SIS 的 waveform-only 排名能力明显弱于 ET 或 PM。主要原因包括：

- LIGO 只有 H1/L1 两个探测器，定位和几何约束弱于 ET。
- noisy 数据中噪声会显著改变波形局部形态。
- SIS 两幅像之间存在放大率、到达时间、相位/Morse index 等差异，直接波形相似度并不稳定。
- 部分真实透镜对在 waveform score 排名中已经不在前排，后处理 reranker 很难把它们重新拉回 Top10。

候选召回诊断中，单独特征的 Top10 能力偏弱：

- waveform 单独 R@10 很低。
- predicted sky_overlap 单独 R@10 更低。
- trigger_time_obs 相对有用，但不足以解决整体检索。

### 3.2 predicted sky-map 质量不足

当前 realistic 方案中不能使用真实 `ra/dec`，也不能使用真实 `sky_sep`。因此尝试方案是：

```text
单事件 waveform -> 机器学习预测 sky probability map
两事件 predicted sky map -> sky_map_overlap
waveform + trigger_time_obs + sky_map_overlap -> catalog-level rerank
```

但目前 LIGO SIS 的 predicted sky-map 质量较弱。已有误差分析结果：

| 指标 | 数值 |
|---|---:|
| sky error mean | 1.320 rad |
| sky error median | 1.273 rad |
| true pixel rank median | 183 / 648 |
| true pixel Top10 | 0.031 |
| true pixel Top50 | 0.135 |
| entropy norm median | 0.981 |
| true partner overlap mean | 0.001850 |
| best false overlap mean | 0.002266 |
| true partner overlap rank median | 1503 / 4500 |
| overlap AUC sampled | 0.620 |

关键问题：

- predicted sky-map 非常平，entropy 接近均匀分布。
- 真实 sky pixel 往往排不进前面。
- true partner 的 predicted overlap 经常低于某些 false candidate。
- 因此 predicted sky_map_overlap 不能稳定把真实透镜对排到前面。

### 3.3 sky-map sharpening 只能小幅提升

对 predicted sky-map 做温度 sharpening 后，最佳 alpha 约为 2：

| 方法 | R@10 | median rank |
|---|---:|---:|
| baseline grid18 | 0.232 | 74 |
| alpha=2 sharpening | 0.245 | 71 |

sharpening 的作用是让概率图更集中，使 overlap 对比更明显。但它无法修正 sky-map peak 本身位置错误的问题。因此提升有限。

## 4. 已尝试的优化方向与结果

### 4.1 优化 sky-map 预测模型

尝试过：

- CNN direction predictor
- grid sky-map predictor
- ResNet grid18 sky-map predictor
- expected angular loss
- detector interaction input
- entropy sharpening training
- hard-negative overlap finetune
- temperature sharpening 后处理

结果：

| 方法 | 主要结果 |
|---|---|
| grid18 baseline | R@10 约 0.232 |
| alpha=2 sharpening | R@10 约 0.245 |
| expected angular loss | R@10 约 0.234 |
| detector interaction | R@10 约 0.231 |
| entropy sharp training | R@10 约 0.231 |
| hard-negative overlap finetune | R@10 约 0.234 |

结论：继续简单加深 sky-map 模型或改变 loss，提升有限。核心瓶颈是 LIGO noisy waveform 中可用于定位的信息本身很弱，模型预测出来的 sky-map 太平、peak 不可靠。

### 4.2 pair-level 深度模型

尝试过直接训练候选对模型：

- `68_ligo_sis_siamese_pair_cnn_top100.py`
- `69_ligo_sis_siamese_embedding_ranker_top100.py`

结果：

| 方法 | candidate recall | R@1 | R@5 | R@10 | R@50 | median rank |
|---|---:|---:|---:|---:|---:|---:|
| direct pair CNN | 0.575 | 0.002 | 0.015 | 0.027 | 0.112 | 250 |
| Siamese embedding ranker | 0.575 | 0.003 | 0.021 | 0.044 | 0.194 | 191 |

问题：

- direct pair CNN 强制比较两条波形的局部差异，不适合存在时间延迟和放大率差异的透镜像。
- Siamese ranker 在训练集上 R@10 接近 1，但 test 上只有 0.044，严重过拟合。
- 当前训练样本和特征不足以支持深度 pair model 泛化。

### 4.3 使用 match embedding 做 pair reranker

尝试用已有 match waveform embedding 的 pair 统计特征：

- embedding dot product
- L1/L2 difference
- product statistics
- waveform score/rank
- trigger_time_obs
- predicted sky_overlap

结果：

| 方法 | candidate recall | R@10 | median rank |
|---|---:|---:|---:|
| HGB embedding pair | 0.575 | 0.011 | 267 |
| SGD embedding pair | 0.575 | 0.000 | 279 |
| ExtraTrees embedding pair | 0.575 | 0.023 | 273 |

结论：已有 match embedding 的 pair distance/statistics 没有提供稳定的 LIGO noisy SIS 透镜同源判别信息，反而破坏排序。

### 4.4 扩大 reranker 训练数据到 train+val

尝试将当前最佳的 4 个稳定特征扩展到 train+val 训练：

| 方法 | R@1 | R@5 | R@10 | R@50 | R@100 | median rank |
|---|---:|---:|---:|---:|---:|---:|
| val-only best | 0.092 | 0.189 | 0.245 | 0.440 | 0.566 | 71 |
| train+val random negatives | 0.085 | 0.160 | 0.214 | 0.418 | 0.534 | 82 |
| train+val hard negatives | 0.001 | 0.007 | 0.015 | 0.037 | 0.057 | 1188 |

结果显示，扩大训练数据没有提升，反而下降。

## 5. 关键诊断：train 与 val/test 分布不一致

诊断文件：

`runs/ligo_sis_feature_distribution_diagnostic_20260608/feature_distribution_summary.csv`

对 train/val/test 分别采样 3000 个正样本和 60000 个随机负样本，统计核心特征正负分离能力。

| split | feature | pos mean | neg mean | AUC |
|---|---|---:|---:|---:|
| train | trigger_time_obs | 14.824 | 18.096 | 0.055 |
| val | trigger_time_obs | 14.758 | 18.090 | 0.053 |
| test | trigger_time_obs | 14.811 | 18.086 | 0.055 |
| train | predicted sky overlap | -6.191 | -6.421 | 0.638 |
| val | predicted sky overlap | -6.207 | -6.419 | 0.615 |
| test | predicted sky overlap | -6.230 | -6.415 | 0.617 |
| train | waveform score | 0.729 | 0.192 | 0.961 |
| val | waveform score | 0.364 | 0.194 | 0.656 |
| test | waveform score | 0.371 | 0.196 | 0.662 |
| train | waveform reciprocal rank | 0.040 | 0.00047 | 0.964 |
| val | waveform reciprocal rank | 0.0227 | 0.00201 | 0.647 |
| test | waveform reciprocal rank | 0.0222 | 0.00201 | 0.657 |

结论：

- `trigger_time_obs` 和 predicted `sky_map_overlap` 在 train/val/test 上较一致。
- waveform score 和 waveform rank 在 train 上异常强，但在 val/test 上明显变弱。
- 这导致 train+val reranker 过度相信 waveform score/rank，最终 test 泛化变差。

这是当前 LIGO SIS 的一个重要问题：训练集和测试集的 waveform 检索难度不一致。

## 6. 当前整体问题总结

LIGO noisy SIS 的主要问题不是单一模型没有调好，而是多个瓶颈叠加：

1. 波形检索弱：noisy LIGO 下真实透镜对的 waveform rank 不够靠前。
2. sky-map 预测弱：predicted sky-map 太平，真实 sky pixel 排名低。
3. sky_overlap 排序弱：true partner overlap 经常低于 best false overlap。
4. train/test 分布不一致：train 上 waveform score 太强，val/test 上明显变弱。
5. pair model 容易过拟合：深度 pair 模型在训练候选集上学习很快，但 test 泛化差。
6. hard negative 训练不稳定：hard-negative rerank 往往破坏 full-catalog 全局排序。

因此，目前通过单纯换模型或堆叠特征，很难把 LIGO SIS R@10 从 0.245 提升到 0.5 以上。

## 7. 对论文实验的影响

当前实验可以支持几个明确论点：

1. ET 相对容易，LIGO noisy SIS 是更接近困难真实场景的压力测试。
2. 真实 sky 信息如果可用，会显著提升检索；但 realistic predicted sky-map 质量不足时，提升有限。
3. catalog-level rerank 是必要的，但它依赖输入特征质量；如果 waveform/sky 特征本身弱，rerank 无法凭空恢复 Top10。
4. 训练集分布与测试集分布一致性非常重要，尤其是 waveform score/rank 的校准。

论文中不建议只报告 best result，还应报告失败分析和 oracle/realistic 对照：

- waveform only
- waveform + trigger_time_obs
- waveform + true sky_sep/true sky_overlap oracle
- waveform + predicted sky_overlap realistic
- catalog-level rerank with realistic features

这样可以清楚说明性能瓶颈来自哪里。

## 8. 后续优化方向

### 8.1 分布重加权或难度匹配

由于 train 的 waveform score/rank 远强于 val/test，可以尝试：

- 按 waveform score 分布重采样 train，使 train 正样本分布接近 val/test。
- 只使用 train 中较难的样本训练 reranker。
- 对 waveform score/rank 做 split-level calibration。

目标：避免 reranker 过度相信 train 中过强的 waveform 特征。

### 8.2 优化 sky-map 预测质量

继续优化 sky-map 时，不应只看角误差，而要同时监控：

- true pixel rank
- entropy norm
- true partner overlap
- best false overlap
- overlap AUC
- final catalog R@10

更合理的目标是让 true partner 的 predicted overlap 高于 hard false candidate，而不是只让单事件角误差下降。

### 8.3 引入探测器级可观测定位代理量

在真实场景下，完全从 noisy waveform 直接预测 sky map 很难。更物理的方向是数据生成时保存或估计：

- 每个探测器的 trigger time
- H1/L1 arrival-time difference proxy
- SNR proxy
- amplitude ratio proxy
- phase proxy

这些量与 sky localization 的物理机制更接近，可能比直接 predicted sky-map 更稳定。

### 8.4 重新设计 PM/SIS 数据范围实验

目前已经生成新的 PM 质量范围数据 `10^4-10^10 M_sun`。后续可以检查：

- 低质量 PM 是否导致 time delay 更短。
- 低质量 PM 是否更接近 wave-optics 或难以分辨的场景。
- LIGO/ET 在扩展 PM 质量范围下的检索难度变化。

这可以作为论文中“透镜物理参数范围对检索性能影响”的实验部分。

## 9. 当前文件索引

核心代码：

- `matchgw/trigger_time.py`
- `scripts/experiments/51_ligo_sis_resnet_grid18_skymap_rerank.py`
- `scripts/experiments/62_ligo_sis_skymap_overlap_error_analysis.py`
- `scripts/experiments/66_ligo_sis_best_skymap_overlap_full_compare.py`
- `scripts/experiments/68_ligo_sis_siamese_pair_cnn_top100.py`
- `scripts/experiments/69_ligo_sis_siamese_embedding_ranker_top100.py`
- `scripts/experiments/70_ligo_sis_embedding_pair_reranker_trainval.py`
- `scripts/experiments/71_ligo_sis_trainval_full_catalog_rerank.py`

关键结果：

- `runs/ligo_sis_best_skymap_overlap_full_compare_20260605/summary.csv`
- `runs/ligo_sis_skymap_quality_report_20260605/summary.csv`
- `runs/ligo_sis_skymap_overlap_error_analysis_20260605/`
- `runs/ligo_sis_feature_distribution_diagnostic_20260608/feature_distribution_summary.csv`
- `runs/ligo_sis_trainval_full_catalog_rerank_20260608/summary.csv`

已有相关文档：

- `docs/predicted_skymap_skyoverlap_error_analysis_20260605_cn.md`
- `docs/ligo_skymap_optimization_summary_20260605_cn.md`
- `docs/ligo_sis_optimization_update_20260608_cn.md`
- `docs/pm_mass_1e4_1e10_generation_summary_20260608_cn.md`
