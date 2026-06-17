# GWTC-3/GWTC-5 真实事件双数据源实验结果报告

日期：2026-06-17  
仓库：`lanhung/gw-catalog`  
主结果文件：`scripts/gwtc/RESULTS_gwtc.md`

## 1. 实验目标

本轮实验按照本地任务文档 `GWTC_codex_prompts_v2_dual_source.md` 执行，目标是在真实 GWTC 事件上验证当前 catalog-level 物理重排层是否可用。重点不是波形 encoder，而是只依赖真实事件可获得的观测摘要：

- 触发时间 `gps_trigger_time`
- 观测天空位置 `ra_median/dec_median`
- 90% 天空定位面积 `sky_area_90_deg2`
- 网络信噪比 `network_snr`
- 质量、距离等辅助观测量

实验覆盖两条数据路径：

- GWTC-3/GWTC-2.1：优先使用完整 PE H5 + skymap stats，作为成熟主线。
- GWTC-5：使用 candidate release 中的 search summary + Bayestar skymap，作为更大 catalog 的可扩展性展示。

最终完成了任务文档中的 Prompt 0 到 Prompt 4。Prompt 5 是可选 baseline 对标，本轮未跑。

## 2. 新增代码与结果文件

新增脚本位于 `scripts/gwtc/`：

| 脚本 | 作用 |
| --- | --- |
| `00_probe_sources.py` | 探测 GWOSC、GWTC-3 PE、GWTC-2.1 PE、GWTC-5 candidate/PE 数据源可用性 |
| `01a_extract_gwtc3_observables.py` | 下载并抽取 GWTC-3-era PE 支持事件的观测量 |
| `01b_extract_gwtc5_observables.py` | 下载并抽取 GWTC-5 strict BBH 候选观测量和 Bayestar 天空定位 |
| `02_build_real_pair_features.py` | 复用 `matchgw/aux_priors` 构建真实事件 pairwise 物理特征 |
| `03_candidate_and_null_analysis.py` | 候选复现、null catalog 阈值曲线和图 |
| `04_injection_recovery.py` | 真实背景下的注入-回收实验 |

主要结果文件：

| 文件 | 内容 |
| --- | --- |
| `scripts/gwtc/source_status.json` | 数据源探测结果 |
| `data/gwtc3_observables.csv` | GWTC-3-era PE 支持事件观测量 |
| `data/gwtc5_observables.csv` | GWTC-5 strict BBH 候选观测量 |
| `data/gwtc3_pair_features.csv` | GWTC-3 pairwise time/sky/SNR 特征 |
| `data/gwtc5_pair_features.csv` | GWTC-5 pairwise time/sky/SNR 特征 |
| `data/gwtc_injection_recovery_records.csv` | 注入恢复 per-seed 原始结果 |
| `data/gwtc_injection_recovery_summary.csv` | 注入恢复 mean/std 汇总 |
| `scripts/gwtc/RESULTS_gwtc.md` | 自动生成的核心结果摘要 |

图文件位于 `figures_gwtc/`：

- `fig_gwtc_candidate_ranks.{png,pdf}`
- `fig_gwtc_null_threshold.{png,pdf}`
- `fig_gwtc_score_hist.{png,pdf}`
- `fig_gwtc_injection_recovery.{png,pdf}`

## 3. 数据源探测结果

### 3.1 GWOSC Event API

GWOSC Event API 可访问：

- 总行数：671
- GWTC-5.0 行数：161
- GWTC-5 或 O4 相关行数：169
- 可直接获得：事件名、GPS、network SNR、质量、距离、FAR、p_astro
- 不直接提供：RA/Dec 天空位置

因此 GWOSC 可作为事件清单和基础参数来源，但 sky 需要从 PE posterior 或 skymap 文件补充。

### 3.2 GWTC-3 / GWTC-2.1 PE

GWTC-3 Zenodo 8177023 可访问：

- `mixed_cosmo.h5`：36 个
- `mixed_nocosmo.h5`：36 个
- `PESkyLocalizations.tar.gz`：存在

GWTC-2.1 Zenodo 6513631 可访问：

- H5 文件：108 个
- skymap stats/skymap 相关文件：55 个
- 覆盖 O1/O2/O3a 事件，包括 GW170104、GW170814

本轮选择优先使用 `mixed_cosmo.h5`。原因是体积更可控，且 sky/mass/distance 的 posterior summary 可以满足当前物理重排层需要。

### 3.3 GWTC-5

GWTC-5 candidate release Zenodo 20276130 可访问：

- SearchSummaryTable 可下载
- Archived_SearchResults skymap 压缩包可下载

GWTC-5 完整 PE 记录在探测中能找到候选记录，但完整 PE 体积大且不是本轮主线。本轮采用 observable-only 路径：SearchSummaryTable + Bayestar skymap。

## 4. 样本选择与实际规模

任务文档中给出的理想规模是 GWTC-3 约 86 个 BBH、GWTC-5 约 390 个事件。但实际下载和严格筛选后，本轮得到：

| catalog | 事件数 | pair 数 | SNR 范围 | A90 median | A90 p90 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GWTC-3 PE-supported | 63 | 1953 | 9.10 - 26.80 | 1020.52 deg² | 14814.78 deg² |
| GWTC-5 strict BBH | 105 | 5460 | 7.84 - 76.61 | 1148.15 deg² | 6367.89 deg² |

规模低于文档理想值的原因：

1. GWTC-3 路径只保留了可成功匹配 PE H5 的事件；有些 marginal 或无完整 PE 的事件没有进入本轮。
2. GWTC-3 还排除了 BNS/NSBH，例如 GW170817、GW190425、GW190814、GW200105、GW200115。
3. GWTC-5 使用 strict BBH cut：`p_BBH > 0.5` 且 `FAR < 1/year`。SearchSummaryTable 中严格通过的候选为 105 个，而不是完整 candidate 表的全部触发。
4. GWTC-5 Event API 不直接给 RA/Dec，本轮以 candidate skymap 计算天空定位，因此要求对应 skymap 可解析。

## 5. sky/time 物理特征实现

本轮没有重写物理打分器，而是复用已有模块：

- `matchgw.aux_priors.a90_to_sigma_rad`
- `matchgw.aux_priors.observed_sky_pair_features`
- `scripts.experiments.88_liao_realistic_p1_p2_rerank.fit_time_lr_from_liao`
- `scripts.experiments.88_liao_realistic_p1_p2_rerank.time_lr_score_matrix`
- `scripts.experiments.88_liao_realistic_p1_p2_rerank.raw_snr_ratio_score_matrix`

pairwise 特征包括：

| 特征 | 含义 |
| --- | --- |
| `delta_t_days` | 两事件 GPS 时间差，单位天 |
| `time_score` | Liao/GW-LMC population-calibrated time-delay LR |
| `sky_norm_sep` | 角距离除以合并 sky sigma |
| `sky_step_weight` | 阶梯函数 sky 权重 |
| `sky_log_overlap` | 二维高斯近似的 sky log overlap |
| `snr_ratio` | SNR 相似性辅助分数 |
| `combined_time_sky_z` | time 和 sky log overlap 的行级 z-score 组合 |

sky 误差处理：

1. 先用 90% 天空定位面积 A90 转成等效二维高斯 sigma。
2. 对两个事件合并误差：`sigma_ij = sqrt(sigma_i^2 + sigma_j^2)`。
3. 归一化天空距离：`d_sky = angular_sep / sigma_ij`。
4. 阶梯函数：
   - `d_sky <= 1.18`：1.0
   - `d_sky <= 2.15`：0.5
   - `d_sky <= 3.03`：0.1
   - 其他：-0.5
5. 二维高斯 log overlap：
   - `-log(2*pi*var) - theta^2/(2*var)`

## 6. 候选复现：GW170104-GW170814

任务文档预期的物理叙事是：GW170104-GW170814 在 sky/parameter 上应较一致，但由于约 7 个月时间差，time prior 应该明显下调。

本轮真实 observable-only 结果如下：

| score | value | rank | total pairs |
| --- | ---: | ---: | ---: |
| sky_step_weight | -0.5000 | 717 | 1953 |
| sky_log_overlap | -79.0780 | 1703 | 1953 |
| sky_norm_sep | 12.7280 | 1702 | 1953 |
| time_score | -1.3033 | 1361 | 1953 |
| combined_time_sky_z | -1.0378 | 1537 | 1953 |

结论：标记为 **EXPLAIN**，不是 PASS。

成立的部分：

- `time_score` 排名 1361/1953，说明 222.01 天时间差被 time prior 下调，这是符合预期的。

没有复现的部分：

- sky-only 没有高排名。当前用 PE posterior/skymap summary 的 `ra_median/dec_median + A90` 做 observable-only 二维高斯近似，得到两者 sky center 分离约 111.22 deg，`sky_norm_sep=12.73`，因此 sky overlap 很低。

这说明当前 observable-only sky center/A90 代理不足以复现文献中“参数一致”的说法。要验证 GW170104-GW170814 的文献叙事，需要后续加入更完整的 posterior parameter-overlap 或 phazap/detector-basis baseline，也就是任务文档中的 Prompt 5。

## 7. Null catalog 分析

将真实 GWTC catalog 暂时视作没有确认透镜事件的 null catalog，计算所有 unordered pairs 的 combined time+sky 分数，并与 Campailla 185/3655 的 shortlist fraction 对齐。

| catalog | pairs | Campailla fraction equivalent count | equivalent threshold | top-185 fraction |
| --- | ---: | ---: | ---: | ---: |
| GWTC-3 PE-supported | 1953 | 99 | 1.8944 | 0.0947 |
| GWTC-5 strict BBH | 5460 | 276 | 1.8637 | 0.0339 |

解释：

- 在 GWTC-3 当前 1953 对中，若采用 Campailla 185/3655 的保留比例，等价 shortlist 约 99 对。
- 在 GWTC-5 当前 5460 对中，等价 shortlist 约 276 对。
- 这说明 cheap observable-level time+sky triage 能把全 pair 空间压缩到较小候选集，适合放在 posterior-overlap 或 joint-PE 确认之前。

## 8. Top pair 检查

### 8.1 GWTC-3 combined time+sky 前 5

| event_i | event_j | delta_t_days | time_score | sky_norm_sep | combined |
| --- | --- | ---: | ---: | ---: | ---: |
| GW151012 | GW170104 | 450.01 | 2.9345 | 8.2667 | 3.1881 |
| GW190925_232845 | GW190929_012149 | 3.08 | 2.3828 | 3.4424 | 3.1289 |
| GW191215_223052 | GW191216_213338 | 0.96 | 2.1477 | 2.7192 | 2.9429 |
| GW190519_153544 | GW190521_074359 | 1.67 | 2.3315 | 6.0634 | 2.9260 |
| GW190725_174728 | GW190728_064510 | 2.54 | 2.0915 | 3.2987 | 2.8999 |

### 8.2 GWTC-3 sky-only 最一致前 5

| event_i | event_j | sky_norm_sep | sky_log_overlap | ang_sep_deg |
| --- | --- | ---: | ---: | ---: |
| GW190602_175927 | GW191204_171526 | 0.1255 | -0.4384 | 3.56 |
| GW190707_093326 | GW200128_022011 | 0.1407 | -1.4562 | 6.63 |
| GW191109_010717 | GW191222_033537 | 0.1651 | -1.5723 | 8.23 |
| GW170809 | GW191105_143521 | 0.1719 | -1.1311 | 6.87 |
| GW200128_022011 | GW200302_015811 | 0.1731 | -2.3501 | 12.72 |

### 8.3 GWTC-5 combined time+sky 前 5

| event_i | event_j | delta_t_days | time_score | sky_norm_sep | combined |
| --- | --- | ---: | ---: | ---: | ---: |
| GW240514_121713 | GW240515_005301 | 0.52 | 3.2423 | 9.6704 | 5.0436 |
| GW241130_034908 | GW241130_110422 | 0.30 | 3.0574 | 12.3675 | 4.4603 |
| GW240621_195059 | GW240621_214041 | 0.08 | 2.6037 | 6.6921 | 4.4327 |
| GW240621_214041 | GW240622_004008 | 0.12 | 2.4955 | 8.4463 | 4.1359 |
| GW241102_124058 | GW241102_144729 | 0.09 | 2.6037 | 11.6062 | 3.9457 |

### 8.4 GWTC-5 sky-only 最一致前 5

| event_i | event_j | sky_norm_sep | sky_log_overlap | ang_sep_deg |
| --- | --- | ---: | ---: | ---: |
| GW240612_081540 | GW240908_082628 | 0.0503 | 0.5463 | 0.87 |
| GW241101_220523 | GW241114_235258 | 0.0975 | -0.9902 | 3.65 |
| GW240902_143306 | GW241225_042553 | 0.1043 | 0.4348 | 1.91 |
| GW240420_175625 | GW240615_113620 | 0.1401 | -1.1747 | 5.73 |
| GW240512_024139 | GW240916_184352 | 0.1425 | 1.5950 | 1.46 |

这些 top pairs 不是确认透镜事件，只是根据当前 cheap physical prior 选出的候选。后续若要科学解释，需要进一步跑 posterior overlap / parameter consistency / waveform consistency。

## 9. 注入-回收实验

注入恢复是本轮最能说明 pipeline 合理性的部分。实验方式：

1. 以真实 GWTC observables 作为背景 catalog。
2. 从真实事件中抽取源事件作为 image-1。
3. image-2 使用相同 latent sky，并在 A90 对应的二维高斯误差内独立散射。
4. 时间延迟和 SNR ratio 从 Liao/GW-LMC detected-pair prior 抽样。
5. K 取 `{10,20,50}`。
6. 每个 K 跑 10 个随机种子。
7. 评价 R@1/R@5/R@10/R@50 和 median rank，汇总 mean±std。

### 9.1 GWTC-3 注入恢复

| K | score | R@1 | R@5 | R@10 | median rank |
| ---: | --- | ---: | ---: | ---: | ---: |
| 10 | combined_time_sky | 0.470±0.116 | 0.775±0.118 | 0.835±0.116 | 1.65±0.71 |
| 10 | sky_log_overlap | 0.100±0.088 | 0.640±0.179 | 0.755±0.162 | 4.20±3.12 |
| 10 | sky_step | 0.550±0.149 | 0.690±0.176 | 0.855±0.126 | 2.80±2.20 |
| 20 | combined_time_sky | 0.468±0.118 | 0.802±0.090 | 0.890±0.064 | 1.80±0.82 |
| 20 | sky_log_overlap | 0.113±0.050 | 0.600±0.134 | 0.725±0.115 | 4.75±2.96 |
| 20 | sky_step | 0.530±0.111 | 0.625±0.135 | 0.850±0.104 | 2.90±2.46 |
| 50 | combined_time_sky | 0.302±0.033 | 0.640±0.064 | 0.769±0.047 | 3.40±0.70 |
| 50 | sky_log_overlap | 0.113±0.026 | 0.507±0.069 | 0.655±0.071 | 5.70±1.40 |
| 50 | sky_step | 0.556±0.079 | 0.592±0.072 | 0.747±0.059 | 2.00±1.63 |

GWTC-3 结果说明：在真实事件背景中，只要注入对符合“同源 sky + 合理 time delay”的假设，当前 rerank 能把同源对排到很靠前的位置。K=20 时 combined_time_sky 的 R@10 达到 0.890±0.064。

### 9.2 GWTC-5 注入恢复

| K | score | R@1 | R@5 | R@10 | median rank |
| ---: | --- | ---: | ---: | ---: | ---: |
| 10 | combined_time_sky | 0.155±0.114 | 0.370±0.144 | 0.500±0.175 | 14.80±8.76 |
| 10 | sky_log_overlap | 0.085±0.063 | 0.615±0.147 | 0.785±0.082 | 4.25±1.27 |
| 10 | sky_step | 0.515±0.156 | 0.700±0.122 | 0.910±0.077 | 2.90±1.61 |
| 20 | combined_time_sky | 0.133±0.064 | 0.323±0.096 | 0.512±0.129 | 12.25±5.07 |
| 20 | sky_log_overlap | 0.140±0.064 | 0.628±0.074 | 0.787±0.073 | 3.55±1.04 |
| 20 | sky_step | 0.512±0.138 | 0.695±0.113 | 0.903±0.075 | 2.55±1.77 |
| 50 | combined_time_sky | 0.123±0.041 | 0.281±0.040 | 0.410±0.044 | 15.85±3.04 |
| 50 | sky_log_overlap | 0.123±0.032 | 0.529±0.060 | 0.716±0.058 | 5.05±0.96 |
| 50 | sky_step | 0.511±0.075 | 0.615±0.071 | 0.803±0.064 | 2.55±1.80 |

GWTC-5 结果显示：

- sky_step 表现最好，K=10 时 R@10 为 0.910±0.077，K=20 时 R@10 为 0.903±0.075。
- sky_log_overlap 也稳定有效，R@10 约 0.716 到 0.787。
- combined_time_sky 在 GWTC-5 上明显弱于 sky-only，说明当前 time prior 与 GWTC-5 真实背景时间分布、注入时间分布之间的权重没有校准好。后续需要做 catalog-specific weighting 或 validation-selected lambda。

## 10. 当前结论

### 10.1 已经支持的结论

1. 真实 GWTC observables 可以接入当前 catalog-level physical reranker。
2. sky overlap 的阶梯函数和二维高斯 log overlap 在真实背景注入恢复中是有效的。
3. time prior 能正确下调 GW170104-GW170814 这种长时间差 pair。
4. cheap observable-level triage 可以把 GWTC-3/GWTC-5 pair 空间压缩到较小 shortlist，适合作为后续高成本 posterior-overlap 或 joint-PE 的前置层。
5. GWTC-5 即使没有使用完整 PE，也能基于 candidate skymap 跑完整 pipeline。

### 10.2 不能过度声称的结论

1. 不能声称 GW170104-GW170814 的 sky-only 高排名已复现。本轮没有复现，必须写成 EXPLAIN。
2. 不能声称 combined_time_sky 是 GWTC-5 上最优组合。当前 GWTC-5 注入恢复中 sky_step 明显更强。
3. 不能把 top-ranked pairs 解释成真实透镜候选，只能说它们是当前物理先验下的 triage shortlist。
4. 不能把 63/105 的结果说成完整 86/390 全量结果。实际样本由可下载 PE/skymap 和 strict cuts 决定。

## 11. 主要问题与下一步

### 11.1 GW170104-GW170814 sky 不高的问题

当前用 `ra_median/dec_median + A90` 的二维高斯近似会丢失 posterior 形状、多峰结构、质量参数一致性和 detector-basis 信息，因此无法复现文献中的参数一致结论。

建议下一步跑 Prompt 5：

- 尝试 phazap；
- 如果 phazap 不可用，则实现 reduced Gaussian parameter-shift baseline；
- 参数空间至少包括 chirp mass、mass ratio、distance、sky；
- 对比 GW170104-GW170814 在 posterior/parameter consistency 下的位置。

### 11.2 GWTC-5 combined 权重问题

GWTC-5 中 combined_time_sky 弱于 sky-only，说明 time prior 权重需要按 catalog 调整。建议：

- 用注入恢复的 validation seeds 选择 `lambda_time` 和 `lambda_sky`；
- 分别报告 sky_step、sky_log_overlap、time_lr、weighted combined；
- 对 GWTC-3 和 GWTC-5 分开选权重，不共享默认权重。

### 11.3 样本覆盖问题

GWTC-3 当前只跑了 63 个 PE 支持事件。若要接近任务文档中的 86：

- 补齐未匹配 PE 的 marginal/confident 事件；
- 允许使用 GWOSC median + fallback sky 或其他 release；
- 明确区分 full-PE-supported set 和 observable-only-expanded set。

GWTC-5 当前 strict BBH 为 105。如果要展示更大规模：

- 可放宽为 p_astro/FAR 不同阈值的 sensitivity analysis；
- 或将所有 candidate search rows 作为 scalability stress test，但必须标注其不是 strict BBH science sample。

## 12. 最终评价

本轮实验完成了真实 GWTC 数据的端到端接入、真实 pair feature 构建、候选/null 分析和真实背景注入恢复。最有价值的结论是：

- 当前物理 reranker 在“真实背景 + 模拟透镜注入”的条件下能有效回收同源 pair；
- sky overlap 模块尤其稳定，说明用 A90 映射到二维高斯误差并做 step/log-overlap 是可行的；
- 真实候选 GW170104-GW170814 的 time-downweight 被复现，但 sky/parameter 一致性需要更完整 posterior/baseline 方法，不能只靠 median sky + A90。

因此，这一版结果可以作为论文或汇报中的“真实事件可运行性 + 注入恢复合理性”证据，但如果要支撑“复现历史候选参数一致性”的叙事，需要继续补 Prompt 5 baseline。
