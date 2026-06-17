# ET3 三通道全量实验报告

生成时间：2026-06-16

## 1. 实验目的

本轮实验使用重新生成的 ET 三臂数据，验证当前代码是否真正适配多探测器/多通道输入，并在全量 SIS + PM + unlensed catalog 上系统比较 waveform、时间、空间和 rerank 组合效果。

本轮重点回答：

- ET3 数据是否以三通道形式进入模型，而不是旧 ET 单通道方案。
- 多通道 encoder 在 pure/noisy 两种数据上能否完成 full-catalog 检索。
- 真实可用的 observed sky、Liao time、PDF hard-mask、SNR/amplitude 以及可拓展 rerank 模块分别带来多少收益。
- 哪个组合作为当前 ET3 主结果最合适。

本报告把“生成数据”“训练 encoder”“rerank 辅助参数组合”和“结果解读”放在同一个文档中，便于后续复现实验或对比旧 ET/LIGO 结果。需要特别区分两类结果：

- **真实可用结果**：只使用 waveform、trigger time、observed sky 误差模型、SNR/amplitude 等可观测量。
- **上界对照结果**：使用 true sky overlap 等真实标签信息，仅用于判断空间信息理论上限，不能作为部署或论文主结果。

本轮推荐主结果以真实可用结果为准。

## 2. 数据与路径

### 2.1 原始 ET3 数据

原始生成目录：

```text
/root/autodl-tmp/createdata/et3_10000_20260616_1006
```

三类数据均已生成完成：

| 数据集 | 目录 | 规模 | 关键 shape |
|---|---|---:|---|
| SIS | `SIS_GW_events_ET3` | 约 132G | `(10000, 3, 98304)` |
| PM | `PM_GW_events_ET3` | 约 132G | `(10000, 3, 98304)` |
| unlensed | `unlensed_GW_events_ET3` | 约 66G | `(10000, 3, 98304)` |

每个 lensed family 都包含两张透镜像：

```text
SIS_data_strain_1.npy        (10000, 3, 98304)
SIS_data_strain_2.npy        (10000, 3, 98304)
PM_data_strain_1.npy         (10000, 3, 98304)
PM_data_strain_2.npy         (10000, 3, 98304)
unlensed_data_strain.npy     (10000, 3, 98304)
```

SNR 同时保存单臂和 network 版本：

```text
*_optimal_SNR_single*.npy    (10000, 3)
*_optimal_SNR_network*.npy   (10000,)
```

### 2.2 match-style 数据根

训练/匹配使用的整理目录：

```text
/root/autodl-tmp/createdata/et3_10000_20260616_1006_match_root
```

目录结构：

```text
SIS_data_0222/
PM_data_0222/
Unlensed_data_0222/
```

该目录使用符号链接指向原始大文件，避免重复占用空间。

### 2.3 数据语义

ET3 数据中第二维为 detector/channel 维度，三个通道对应 ET 三臂：

```text
channel 0 -> ET1
channel 1 -> ET2
channel 2 -> ET3
```

每个事件的 waveform 数据形状为：

```text
[detector_channel, time_sample] = [3, 98304]
```

进入模型前会经过尾部窗口裁剪、下采样、bandpass 和标准化，最终输入形状为：

```text
[detector_channel, model_time_sample] = [3, 4096]
```

因此本轮实验不是把 ET 三臂合成为一个通道，也不是只取其中一臂，而是让 encoder 同时接收 ET1/ET2/ET3 三个通道。

## 3. 多探测器代码适配

本轮实验已经按多通道输入适配，关键验证结果：

```text
raw       (3, 98304)
prepared  (3, 4096)
channels  3
```

主要修改点：

- `data_generation/detector_network.py`：支持模块化 detector network，可配置不同 detector 数量。
- `matchgw/data.py`：支持 `[time]` 与 `[channels, time]` 两种输入，预处理后保持多通道结构。
- `matchgw/pipeline.py`：模型构建时自动推断 `in_channels`。
- `scripts/experiments/80_mixed_sis_pm_catalog_modality_compare.py`：mixed SIS/PM encoder 训练加载时支持 ET3 三通道 checkpoint。
- `matchgw/aux_priors/observed_sky.py`：新增 ET3 sky 场景。
- `scripts/experiments/90_et3_full_experiment_runner.py`：新增 ET3 全量实验 runner。

sky 场景映射：

| detector key | sky scenario | 含义 |
|---|---|---|
| `ET` | `ET_SINGLE` | 旧 ET 单探测器近似 |
| `ET3` | `ET_TRIANGLE` | ET1/ET2/ET3 三臂 network-SNR A90 近似 |
| `LIGO` | `LIGO_HL` | H1+L1 双站 A90 近似 |

注意：`ET_TRIANGLE` 不是 HEALPix 真实 skymap，也不是 H1L1 那种长基线双站定位；当前采用 network SNR + A90 的近似 observed sky 模型。

### 3.1 多通道数据流

ET3 waveform 在代码中的处理流程：

```text
原始 npy: (N, 3, 98304)
单个样本: (3, 98304)
pad_or_trim + stride: (3, 4096)
bandpass: (3, 4096)
zscore per channel: (3, 4096)
Conv1d/InceptionTime input: in_channels=3
```

关键点是 `in_channels` 由数据自动推断，不再写死为 1。checkpoint 加载时也使用相同的 `in_channels=3`，否则旧单通道模型结构无法加载 ET3 三通道权重。

### 3.2 observed sky 误差模型

当前 ET3 observed sky 使用 `ET_TRIANGLE` 场景：

```text
a90_ref_deg2 = 100
rho_ref = 12
clip_min_deg2 = 20
clip_max_deg2 = 1000
snr_for_sky = network
sampling = tangent_2d_gaussian
```

A90 面积随 network SNR 动态变化：

```text
A90 = a90_ref_deg2 * (rho_ref / network_snr)^2 * lognormal_noise
A90 = clip(A90, 20, 1000)
```

其中 `lognormal_noise` 用于模拟实际定位误差的散布，不让 A90 完全由 SNR 决定。得到 A90 后，换算为二维高斯的等效 sigma，然后在天球切平面上采样 observed center：

```text
dx ~ Normal(0, sigma)
dy ~ Normal(0, sigma)
observed_direction = normalize(true_direction + dx * e1 + dy * e2)
```

当前 ET3 noisy test audit 的误差统计：

| 项目 | median | mean | p90 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|
| A90 deg2 | 20.00 | 24.81 | 27.26 | 47.33 | 124.53 | 930.41 |
| sigma deg | 1.18 | 1.26 | 1.37 | 1.81 | 2.93 | 8.02 |
| actual center offset deg | 1.45 | 1.59 | 2.71 | 3.19 | 4.70 | 11.27 |

因此当前默认 ET3 sky 误差可以概括为：多数事件被限制在最小 A90=20 平方度附近，实际 observed center 相对 true sky 的偏移中位数约 1.45 度，90% 事件在 2.7 度以内。

### 3.3 rerank 辅助参数模块

rerank 使用的辅助分数都先转换为 full-catalog score matrix，再统一按行标准化：

```text
waveform_score
raw_time_score
liao_time_lr_score
observed_sky_step_score
observed_sky_log_overlap_score
raw_snr_ratio_score
amp_time_2d_lr_score
```

组合时采用可拓展的 weighted sum 或小模型 reranker：

```text
score = waveform + lambda_time * time + lambda_sky * sky + ...
```

lambda 在 validation full catalog 上选择，再应用到 test full catalog。这样避免直接在 test 上调参。

## 4. 实验入口与输出

启动命令：

```bash
cd /root/autodl-tmp/gw-catalog
/root/miniconda3/bin/python scripts/experiments/90_et3_full_experiment_runner.py --phase all
```

日志：

```text
/root/autodl-tmp/gw-catalog/logs/et3_full_experiment_20260616.log
```

结果目录：

```text
/root/autodl-tmp/gw-catalog/runs/et3_fresh50_full_catalog_20260616
/root/autodl-tmp/gw-catalog/runs/et3_liao_realistic_p1_p2_rerank_20260616
```

本轮 `--phase all` 已全部完成，包括：

1. ET3 pure fresh50 full-catalog
2. ET3 noisy fresh50 full-catalog
3. ET3 noisy stage0-stage3
4. PDF hard-mask baseline
5. stage4-stage6 rerank/model compare/graph discovery
6. stage7 modality combinations：SIS/PM 分解的 waveform/time/sky 单项与组合实验

### 4.1 实验恢复与缓存

本轮全量实验会生成并复用以下缓存：

- encoder checkpoint：`model.pt`
- train/val/test embeddings：`*_embeddings.npy`
- val/test similarity matrix：`*_scores.npy`
- observed sky audit CSV
- 每个 stage 的 partial CSV 和 summary CSV

如果中途失败，通常不需要重新训练已完成的 encoder。重新运行同一脚本时会优先加载 checkpoint 和 embedding/scores 缓存。

## 5. Catalog 设置

full-catalog 测试集规模：

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

训练配置：

| 项目 | 值 |
|---|---|
| backbone | `inceptiontime` |
| preprocess | `bandpass` |
| epochs | 50 |
| 输入通道 | 3 |
| 输入长度 | 4096 |
| 数据模式 | pure + noisy |

训练耗时：

| 模式 | train_s | mean_epoch_s | 最终 loss |
|---|---:|---:|---:|
| ET3 pure | 1312.48 | 26.25 | 0.0122 |
| ET3 noisy | 1940.88 | 38.82 | 0.0367 |

### 5.1 指标解释

本报告主要使用 retrieval/ranking 指标：

| 指标 | 含义 |
|---|---|
| R@1 | 正确透镜配对排在第 1 名的比例 |
| R@5 | 正确配对进入前 5 名的比例 |
| R@10 | 正确配对进入前 10 名的比例 |
| Top1% | 正确配对进入 catalog 前 1% 候选的比例 |
| Median rank | 正确配对的中位排名 |

full-catalog 设置下，每个 query 都要在 9000 个 catalog event 中找对应的透镜伴随像，因此 R@1/R@10 比普通小候选集评估更严格。

## 6. Fresh50 Full-Catalog 结果

### 6.1 ET3 noisy 主要结果

| variant | R@1 | R@5 | R@10 | Top1% | Median rank |
|---|---:|---:|---:|---:|---:|
| waveform only | 0.6245 | 0.7978 | 0.8542 | 0.9585 | 1 |
| time only | 0.1352 | 0.4050 | 0.5298 | 0.6778 | 9 |
| predicted sky overlap only | 0.0062 | 0.0238 | 0.0440 | 0.2395 | 352 |
| waveform + time | 0.6338 | 0.8493 | 0.8982 | 0.9855 | 1 |
| waveform + predicted sky overlap | 0.5320 | 0.7708 | 0.8162 | 0.9538 | 1 |
| waveform + time + predicted sky overlap | 0.6313 | 0.8463 | 0.8988 | 0.9808 | 1 |
| true sky overlap only | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| waveform + time + true sky overlap | 0.9832 | 0.9980 | 0.9992 | 1.0000 | 1 |

`true sky` 结果只作为上界/泄漏对照，不能作为真实可用方案。

noisy 模式下，waveform-only 已经能达到 R@10=0.8542，说明 ET3 三通道 waveform encoder 能从噪声数据中学到稳定的同源特征。但 R@1 只有 0.6245，说明仅靠波形仍存在大量近邻混淆，尤其在 full-catalog 9000 规模下需要时间/空间信息辅助。

### 6.2 ET3 pure 参考

| variant | R@1 | R@5 | R@10 | Top1% | Median rank |
|---|---:|---:|---:|---:|---:|
| waveform only | 0.9843 | 0.9953 | 0.9973 | 0.9995 | 1 |
| waveform + time | 0.9277 | 0.9755 | 0.9947 | 0.9995 | 1 |
| waveform + time + predicted sky overlap | 0.9567 | 0.9887 | 0.9938 | 0.9992 | 1 |
| true sky overlap only | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |

pure 数据上 waveform 本身已经非常强，noisy 数据才是更有参考价值的真实设置。

pure 模式代表无噪声或理想 waveform 条件，waveform-only 已经达到 R@10=0.9973。这个结果证明模型结构和多通道输入本身没有问题，但它不能代表真实观测性能。后续阶段主要关注 noisy。

## 7. Realistic Rerank 分阶段结果

以下结果均为 ET3 noisy。

### 7.1 Stage0 baseline

Stage0 只比较最基础的信息源：

- waveform：encoder embedding 相似度。
- raw time：直接用观测触发时间差构造的时间接近分数。
- waveform + raw time：validation 上选择时间权重后与 waveform 融合。

| variant | R@1 | R@5 | R@10 | Top1% | Median rank | lambda |
|---|---:|---:|---:|---:|---:|---:|
| waveform only | 0.6245 | 0.7978 | 0.8542 | 0.9585 | 1 | - |
| raw time only | 0.1352 | 0.4050 | 0.5298 | 0.6778 | 9 | - |
| waveform + raw time | 0.8580 | 0.9438 | 0.9648 | 0.9923 | 1 | 0.5 |

### 7.2 Stage1 Liao time prior

Stage1 将原始时间差替换为参考真实参数分布的 Liao/GW-LMC time-delay prior。这里测试两类时间先验：

- time step：阶梯函数形式，接近 PDF 后处理中的硬规则思想。
- time LR：用 Liao time-delay 分布训练得到的 logistic-like 连续时间分数。

| variant | R@1 | R@5 | R@10 | Top1% | Median rank |
|---|---:|---:|---:|---:|---:|
| Liao time step only | 0.5060 | 0.5060 | 0.5060 | 0.5072 | 1 |
| Liao time LR only | 0.1297 | 0.4040 | 0.5308 | 0.6830 | 9 |
| waveform + Liao time step | 0.6280 | 0.8273 | 0.8835 | 0.9688 | 1 |
| waveform + Liao time LR | 0.8300 | 0.9310 | 0.9597 | 0.9918 | 1 |

Liao time LR 比阶梯时间函数更适合作为 ET3 noisy 的时间辅助项。

### 7.3 Stage2 observed sky

Stage2 专门测试 observed sky。它不直接使用 true sky 做 rerank feature，而是先生成带误差的 `ra_obs/dec_obs/sky_area90`，再从 observed posterior 构造 pairwise sky score。

测试了两类空间分数：

- step：按归一化角距离给阶梯权重，强调“空间越近，透镜概率越高”。
- Gaussian/log overlap：二维高斯 posterior overlap，强调两个事件 localization posterior 的重叠程度。

| variant | R@1 | R@5 | R@10 | Top1% | Median rank | lambda |
|---|---:|---:|---:|---:|---:|---:|
| observed sky step only | 0.5342 | 0.8247 | 0.9407 | 1.0000 | 1 | - |
| observed sky log overlap only | 0.2370 | 0.6848 | 0.8872 | 0.9998 | 3 | - |
| waveform + observed sky step | 0.8963 | 0.9788 | 0.9908 | 0.9987 | 1 | 0.25 |
| waveform + observed sky log overlap | 0.8592 | 0.9362 | 0.9608 | 0.9898 | 1 | 4.0 |
| A90=50 step | 0.8835 | 0.9838 | 0.9972 | 0.9993 | 1 | 0.25 |
| A90=100 step | 0.9055 | 0.9843 | 0.9943 | 0.9980 | 1 | 0.25 |
| A90=300 step | 0.9117 | 0.9803 | 0.9890 | 0.9963 | 1 | 0.25 |

按 R@10 看，A90=50 step 最好；按 R@1 看，A90=300 step 略高。综合后续 stage3/stage5，step 类空间赋权优于单独 Gaussian log-overlap。

### 7.4 Stage2b PDF hard-mask baseline

Stage2b 对应 `透镜识别流程.pdf` 后续处理里更原始的硬阈值空间赋权思路。它把 sky 判断简化成面积阈值内/外的 hard mask。这个 baseline 有助于比较“简单硬规则”和“posterior-aware observed sky”之间的差异。

| variant | R@1 | R@5 | R@10 | Top1% | Median rank |
|---|---:|---:|---:|---:|---:|
| PDF sky hard mask only | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| waveform + PDF sky hard mask | 0.8968 | 0.9755 | 0.9852 | 0.9977 | 1 |
| waveform + Liao time LR | 0.8300 | 0.9310 | 0.9597 | 0.9918 | 1 |
| waveform + PDF sky hard mask + Liao time LR | 0.9720 | 0.9953 | 0.9970 | 1.0000 | 1 |

PDF hard mask 在当前模拟 observed center 下非常强，但它是硬阈值规则，容易受阈值和模拟误差分布影响；主方案仍建议使用可解释且可调的 observed sky step/overlap 模块做主线。

### 7.5 Stage3 Liao time + observed sky

Stage3 是第一个完整的真实可用物理辅助组合：

```text
waveform + Liao time LR + observed sky
```

它回答的问题是：时间先验和空间先验是否互补。结果显示，step 形式的 observed sky 与 Liao time LR 融合后，R@1 从 waveform-only 的 0.6245 提升到 0.9763。

| variant | R@1 | R@5 | R@10 | Top1% | Median rank |
|---|---:|---:|---:|---:|---:|
| waveform + Liao time LR + observed sky step | 0.9763 | 0.9967 | 0.9980 | 0.9998 | 1 |
| waveform + Liao time LR + observed sky log overlap | 0.9455 | 0.9853 | 0.9923 | 0.9983 | 1 |

Stage3 是当前物理解释和效果较平衡的主线方案。

### 7.6 Stage4 SNR/amplitude prior

Stage4 进一步测试 SNR/amplitude 信息是否能在 waveform+time+sky 之外提供增益。包含：

- raw SNR ratio
- amplitude/time 二维 LR
- time LR + sky log overlap 的组合

本轮 ET3 noisy 下，amp-time 相关项最终权重为 0，说明它没有在 validation 上提供稳定额外收益。

| variant | R@1 | R@5 | R@10 | Top1% | Median rank |
|---|---:|---:|---:|---:|---:|
| waveform + time LR + sky log overlap | 0.9448 | 0.9862 | 0.9923 | 0.9983 | 1 |
| plus raw SNR ratio | 0.9448 | 0.9862 | 0.9923 | 0.9983 | 1 |
| plus amp-time 2D LR | 0.9448 | 0.9862 | 0.9923 | 0.9983 | 1 |

本轮 ET3 下 SNR/amplitude 额外项没有带来可见增益，选出的 `lambda_amp_time_lr=0.0`。

### 7.7 Stage5 reranker model compare

Stage5 将辅助参数模块做成可拓展的 reranker，对比：

- 固定加权求和
- validation 选择的可拓展 weighted sum
- logistic regression
- HistGradientBoosting
- MLP tabular
- LightGBM

其中 weighted sum val-selected extensible 最好，说明当前特征规模下，简单可解释的加权组合比复杂表格模型更稳定。

| variant | R@1 | R@5 | R@10 | Top1% | Median rank |
|---|---:|---:|---:|---:|---:|
| weighted sum val-selected extensible | 0.9840 | 0.9973 | 0.9985 | 1.0000 | 1 |
| weighted sum stage4 lambdas | 0.9457 | 0.9857 | 0.9923 | 0.9983 | 1 |
| MLP tabular | 0.8302 | 0.9517 | 0.9762 | 0.9832 | 1 |
| LightGBM | 0.8548 | 0.9313 | 0.9397 | 0.9498 | 1 |
| HGB | 0.8185 | 0.8995 | 0.9187 | 0.9407 | 1 |
| logistic regression | 0.0012 | 0.0017 | 0.0035 | 0.0117 | 1507.5 |

当前最佳真实可用方案是 `weighted_sum_val_selected_extensible`。

### 7.8 Stage6 graph discovery

Stage6 不再只看单个 query 的 rank，而是把 catalog 中高分候选边作为图结构处理，用于后续发现透镜系统候选簇。该阶段为后续误报分析和多像系统扩展保留结果。

Stage6 已完成并输出：

```text
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage6_catalog_graph_discovery/stage6_catalog_graph_discovery_summary.csv
```

该阶段用于 catalog graph discovery 风格的候选边评估，结果文件已生成，后续可单独展开分析候选边质量、连通分量和误报情况。

### 7.9 Stage7 waveform/time/sky 各种组合

Stage7 基于 ET3 noisy full-catalog 缓存结果，不重新训练 encoder，专门补充 SIS/PM 分解的 modality ablation：只靠 waveform、只靠 time、只靠 sky，以及 waveform/time/sky 的二元和三元组合。

输出：

```text
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage7_modality_combinations/stage7_modality_combinations_summary.csv
```

#### Overall 排名

| variant | R@1 | R@5 | R@10 | Top1% | Median rank | weights |
|---|---:|---:|---:|---:|---:|---|
| waveform + raw time + observed sky step | 0.9792 | 0.9980 | 0.9992 | 0.9997 | 1 | waveform=1, raw_time=1, sky_step=0.25 |
| waveform + Liao time LR + observed sky step | 0.9757 | 0.9983 | 0.9990 | 0.9995 | 1 | waveform=1, liao_time_lr=1, sky_step=0.25 |
| waveform + raw time + observed sky log overlap | 0.9587 | 0.9873 | 0.9932 | 0.9983 | 1 | waveform=1, raw_time=0.5, sky_log_overlap=4 |
| waveform + observed sky step | 0.8968 | 0.9838 | 0.9932 | 0.9982 | 1 | waveform=1, sky_step=0.25 |
| waveform + Liao time LR + observed sky log overlap | 0.9445 | 0.9863 | 0.9920 | 0.9983 | 1 | waveform=1, liao_time_lr=1, sky_log_overlap=4 |
| Liao time LR + observed sky step | 0.7148 | 0.9465 | 0.9808 | 0.9967 | 1 | liao_time_lr=1, sky_step=0.25 |
| raw time + observed sky step | 0.7683 | 0.9463 | 0.9710 | 0.9957 | 1 | raw_time=1, sky_step=0.25 |
| waveform + raw time | 0.8580 | 0.9438 | 0.9648 | 0.9923 | 1 | waveform=1, raw_time=0.5 |
| waveform + observed sky log overlap | 0.8587 | 0.9365 | 0.9610 | 0.9897 | 1 | waveform=1, sky_log_overlap=4 |
| waveform + Liao time LR | 0.8300 | 0.9310 | 0.9597 | 0.9918 | 1 | waveform=1, liao_time_lr=1 |
| observed sky step only | 0.5422 | 0.8278 | 0.9450 | 1.0000 | 1 | sky_step=1 |
| observed sky log overlap only | 0.2417 | 0.6933 | 0.8883 | 0.9998 | 3 | sky_log_overlap=1 |
| waveform only | 0.6245 | 0.7978 | 0.8542 | 0.9585 | 1 | waveform=1 |
| Liao time LR + observed sky log overlap | 0.6323 | 0.7823 | 0.8330 | 0.9790 | 1 | liao_time_lr=0.25, sky_log_overlap=4 |
| raw time + observed sky log overlap | 0.6025 | 0.7308 | 0.7917 | 0.9868 | 1 | raw_time=0.25, sky_log_overlap=4 |
| Liao time LR only | 0.1297 | 0.4040 | 0.5308 | 0.6830 | 9 | liao_time_lr=1 |
| raw time only | 0.1352 | 0.4050 | 0.5298 | 0.6778 | 9 | raw_time=1 |

#### SIS / PM 分解

| variant | SIS R@1 | SIS R@10 | PM R@1 | PM R@10 | 结论 |
|---|---:|---:|---:|---:|---|
| waveform only | 0.6740 | 0.8907 | 0.5750 | 0.8177 | waveform 对 SIS 略强于 PM |
| raw time only | 0.0097 | 0.1020 | 0.2607 | 0.9577 | raw time 对 PM 很强，对 SIS 很弱 |
| Liao time LR only | 0.0120 | 0.1110 | 0.2473 | 0.9507 | Liao time 与 raw time 类似，主要提升 PM |
| observed sky step only | 0.5387 | 0.9470 | 0.5457 | 0.9430 | sky step 对 SIS/PM 都强 |
| observed sky log overlap only | 0.2390 | 0.8927 | 0.2443 | 0.8840 | log overlap R@10 高，但 R@1 弱 |
| waveform + raw time | 0.7863 | 0.9503 | 0.9297 | 0.9793 | raw time 显著提升 PM |
| waveform + Liao time LR | 0.7200 | 0.9330 | 0.9400 | 0.9863 | Liao time 对 PM 提升更明显 |
| waveform + observed sky step | 0.9150 | 0.9957 | 0.8787 | 0.9907 | sky step 对两类都稳定提升 |
| waveform + observed sky log overlap | 0.8937 | 0.9770 | 0.8237 | 0.9450 | log overlap 低于 step |
| raw time + observed sky step | 0.6033 | 0.9447 | 0.9333 | 0.9973 | time+sky 对 PM 接近完美 |
| raw time + observed sky log overlap | 0.2370 | 0.5833 | 0.9680 | 1.0000 | PM 极强，SIS 明显不足 |
| Liao time LR + observed sky step | 0.5890 | 0.9667 | 0.8407 | 0.9950 | 无 waveform 时 sky step 是关键 |
| Liao time LR + observed sky log overlap | 0.3087 | 0.6660 | 0.9560 | 1.0000 | PM 极强，SIS 不足 |
| waveform + raw time + observed sky step | 0.9643 | 0.9983 | 0.9940 | 1.0000 | Overall 最佳组合 |
| waveform + raw time + observed sky log overlap | 0.9437 | 0.9910 | 0.9737 | 0.9953 | 低于 sky step 组合 |
| waveform + Liao time LR + observed sky step | 0.9650 | 0.9987 | 0.9863 | 0.9993 | SIS 最佳，Overall 接近最佳 |
| waveform + Liao time LR + observed sky log overlap | 0.9087 | 0.9853 | 0.9803 | 0.9987 | 低于 sky step 组合 |

Stage7 结论：

- 单项里，`observed_sky_step_only` 是最强辅助信号，R@10 达到 0.9450，明显高于 time-only。
- PM 对时间信息极敏感，`raw_time_only` 和 `liao_time_lr_only` 的 PM R@10 分别达到 0.9577 和 0.9507，但 SIS 上几乎失效。
- `observed_sky_step` 比 `observed_sky_log_overlap` 更适合作为当前 ET3 noisy 的主空间特征。
- Overall 最佳 modality 组合是 `waveform + raw time + observed sky step`，R@10=0.9992。
- 如果强调真实物理先验一致性，`waveform + Liao time LR + observed sky step` 也非常接近，R@10=0.9990，且 SIS R@10 略高。

## 8. 当前最佳方案

如果只看真实可用输入，不使用 true sky 泄漏项，当前建议主结果为：

```text
stage5 weighted_sum_val_selected_extensible
```

指标：

| 指标 | 值 |
|---|---:|
| R@1 | 0.9840 |
| R@5 | 0.9973 |
| R@10 | 0.9985 |
| Top1% | 1.0000 |
| Median rank | 1 |

对比 waveform-only：

| 方案 | R@1 | R@10 | Top1% |
|---|---:|---:|---:|
| waveform only | 0.6245 | 0.8542 | 0.9585 |
| stage3 waveform + Liao time + observed sky step | 0.9763 | 0.9980 | 0.9998 |
| stage5 weighted sum val-selected extensible | 0.9840 | 0.9985 | 1.0000 |

结论：ET3 noisy 下，多通道 waveform encoder 已经提供较强基线；加入时间和 observed sky 后提升非常明显，最终可拓展加权 rerank 进一步把 R@1 提升到 0.9840。

### 8.1 主结果选择理由

虽然 Stage7 的 `waveform + raw time + observed sky step` 在 R@10 上达到 0.9992，但报告主结果仍建议采用 Stage5 的 `weighted_sum_val_selected_extensible`，原因是：

1. Stage5 使用更完整的可拓展辅助特征集合，后续加入新参数更方便。
2. 权重选择流程已经封装为统一模块，适合后续复现实验和对比。
3. Stage5 的 R@1=0.9840，是当前真实可用方案里最高的整体 R@1。
4. Stage7 更适合作为 modality ablation，解释 waveform/time/sky 各自贡献。

如果论文或汇报需要展示“物理可解释组合”，建议同时报告：

| 用途 | 推荐方案 | 说明 |
|---|---|---|
| 主结果 | Stage5 weighted_sum_val_selected_extensible | 当前整体最优 |
| 物理可解释 ablation | waveform + Liao time LR + observed sky step | 避免 raw time 过拟合解释，接近最佳 |
| modality 最强组合 | waveform + raw time + observed sky step | Stage7 Overall 最强 |
| 上界对照 | true sky overlap only | 只作理论上界，不可作为主结果 |

### 8.2 SIS 与 PM 差异总结

SIS 和 PM 对辅助信息的依赖不同：

- SIS：waveform 更强，time-only 几乎无效；需要 waveform + sky step 才能稳定提升。
- PM：time 信息非常强，raw_time_only 和 Liao_time_only 的 PM R@10 都接近或超过 0.95。
- sky step：对 SIS/PM 都有效，是最稳定的单个辅助信息。
- sky log overlap：Top1% 很高，但 R@1 不如 sky step，说明它更适合粗筛，不一定适合精排第一名。

这说明后续可以考虑 family-aware weighting：SIS 更依赖 waveform/sky，PM 可以给 time 更高权重。

## 9. 需要注意的问题

1. `true_sky_overlap_only` 和包含 `true_sky_overlap` 的结果只能作为上界对照，不能作为真实部署方案。
2. `PDF sky hard mask only` 得到 1.0，说明当前模拟空间中心和硬阈值规则在本数据上非常强；需要警惕它对模拟误差分布和阈值的敏感性。
3. `predicted_sky_overlap_only` 在 noisy 下很弱，说明从 waveform embedding 回归 sky 的模型仍不可靠；当前更推荐 observed sky 误差模型，而不是 waveform-predicted sky。
4. Stage4 中 SNR/amplitude 对 ET3 没有额外收益，当前权重选择等价于不使用 amp-time LR。
5. ET3 sky 仍是 A90 approximation，不是真实 skymap；后续如果要更物理，需要接入 Fisher/BAYESTAR/HEALPix 类定位模型。

## 10. 输出文件清单

主要 summary：

```text
runs/et3_fresh50_full_catalog_20260616/fresh50_full_catalog_summary.csv
runs/et3_fresh50_full_catalog_20260616/et3_pure_full_catalog/fresh50_full_catalog_summary.csv
runs/et3_fresh50_full_catalog_20260616/et3_noisy_full_catalog/fresh50_full_catalog_summary.csv

runs/et3_liao_realistic_p1_p2_rerank_20260616/stage0_baseline/stage0_baseline_summary.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage1_liao_time_lr/stage1_liao_time_lr_summary.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage2_observed_sky/stage2_observed_sky_summary.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage2b_pdf_rule_time_sky_baseline/stage2b_pdf_rule_time_sky_baseline_summary.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage3_liao_time_plus_observed_sky/stage3_liao_time_plus_observed_sky_summary.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage4_snr_amplitude_prior/stage4_snr_amplitude_prior_summary.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage5_reranker_model_compare/stage5_reranker_model_compare_summary.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage6_catalog_graph_discovery/stage6_catalog_graph_discovery_summary.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage7_modality_combinations/stage7_modality_combinations_summary.csv
```

集中放置在 `docs/` 下的文档与导出表：

```text
docs/et3_full_experiment_report_20260616_cn.md
docs/et3_stage7_modality_combinations_report_20260616_cn.md
docs/et3_stage7_modality_combinations_summary_20260616.csv
```

encoder 输出：

```text
runs/et3_fresh50_full_catalog_20260616/fresh_mixed_encoders/et3_pure_mixed_sis_pm_ep50/model.pt
runs/et3_fresh50_full_catalog_20260616/fresh_mixed_encoders/et3_noisy_mixed_sis_pm_ep50/model.pt
```

审计文件：

```text
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage2_observed_sky/ET3_noisy_val_observed_sky_audit.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage2_observed_sky/ET3_noisy_test_observed_sky_audit.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage3_liao_time_plus_observed_sky/stage3_prior_sky_diagnostics.csv
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage4_snr_amplitude_prior/amp_time_prior_diagnostics.csv
```

## 11. 下一步建议

1. 固定 `stage5 weighted_sum_val_selected_extensible` 作为当前 ET3 noisy 主结果。
2. 对 `PDF hard mask` 做阈值扫描，确认 1000 deg2 结果是否过于依赖当前模拟误差。
3. 对 observed sky 的 A90 分布做更细扫描，例如 25/50/75/100/150/300 deg2。
4. 将 Stage6 graph discovery 展开成候选边质量报告，重点看 false positive 的时间差、空间距离和 family 分布。
5. 如果后续要进一步提高物理真实性，应把 ET3 的 A90 approximation 替换为真实 localization/skymap 生成流程。
