# P2 服务器实验最终复核与论文使用报告

日期：2026-06-18
项目：`/root/autodl-tmp/gw-catalog`
结论口径：本报告替代同日早期 P2-A 的 ANN 召回解释；P2-B/P2-C 的原始数值保持有效。

## 1. 执行结论

本轮完成了 P2-A 的代码审计、exact baseline 修复、ET-3 noisy 重跑、HNSW 参数扫描、LIGO 对照和百万规模 stress test，并复核了 P2-B/P2-C 的论文表述。

最重要的结论如下：

1. P2-A 早期 `recall@10 vs dense=0.12--0.20` 不是 HNSW 检索失败。根因是 dense baseline 用 `argpartition` 取得 top-200 集合后没有在集合内排序，导致“前 10 个”并不是真正的 dense top-10。
2. 修复后，在原生 ET-3 noisy 9000-event catalog 上，exact dense 与 HNSW 的 partner R@10 都是 **0.8565**；HNSW 对 exact dense 的 recall@10 是 **0.99895**。因此可以写“检索质量保持”，但只能针对原生 ET-3 catalog。
3. 在同一修复基准上，LIGO noisy 的 dense 与 HNSW partner R@10 都是 **0.024**，而 HNSW 对 dense recall@10 是 **0.9988**。这证明 LIGO 的低 partner recall 来自 embedding，本身不是 ANN 索引问题。
4. 1,000,000-event synthetic stress test 的全量建索引耗时 **26.84 s**；2000-query benchmark 耗时 **0.90 s**。按测得吞吐量线性外推，全量 1,000,000 queries 约 **452.20 s**，建索引加全量查询约 **479.04 s（约 8.0 min）**。不能把 27.75 s 写成“百万事件全量检索总耗时”。
5. P2-B 仍是本组实验最强的科学结果：posterior-sample HEALPix overlap 将 GW170104--GW170814 的两个方向分别从 Gaussian surrogate rank 57/43 提升到 rank 4/2。

## 2. P2-A 修复内容

修改文件：

- `scripts/server_experiments/p2a_ann_sparse_retrieval.py`
- `scripts/server_experiments/prepare_p2a_et3_meta.py`

具体修复：

- dense top-k 在 `argpartition` 后按相似度降序排序；这是早期异常 ANN fidelity 的根因修复。
- dense 与 ANN 都显式排除 query self-match，避免自身占用一个 top-k 位置。
- `efConstruction` 与 `efSearch` 分离，默认分别设为 256 和 512；`M=32`。
- 输入 embedding 在索引前强制 L2 normalize，inner product 因而等价于 cosine similarity。
- 输出 embedding norm audit、FAISS 版本、线程数、metric、self-match 策略和所有运行参数到 `run_config.json`。
- 默认输入改为已经验证的 ET-3 noisy test embedding，并新增严格重建相同 event ordering 的 metadata 脚本。
- CSV 新增实际 query 数、每千 query 时间、全目录 query 外推时间及全流程外推时间。
- 原 `peak_mem_mb` 实际只是运行前后 RSS 差，并不是真正 peak memory；现更名为 `rss_delta_mb`。
- 图分为 runtime projection、ANN fidelity、native/synthetic partner recall 三部分，避免把 synthetic partner collapse 误写成 ANN fidelity collapse。

## 3. 输入与一致性审计

ET-3 embedding：

`runs/et3_fresh50_full_catalog_20260616/fresh_mixed_encoders/et3_noisy_mixed_sis_pm_ep50/test_embeddings.npy`

形状：9000 x 128。

metadata：

`runs/p2a_ann_et3_noisy_meta_20260618/catalog_meta.csv`

由训练/评估脚本的同一 seed、split 和 `MixedEvaluationSet` ordering 重建：

- 9000 events
- 3000 lensed systems
- 3000 unlensed events
- 每个 lensed `source_id` 恰好出现两次
- metadata 行数、evaluation dataset 行数、raw observable 行数、timing observable 行数和 embedding 行数全部一致

embedding norm audit：

| 指标 | 数值 |
| --- | ---: |
| norm min（输入） | 0.99999988 |
| norm mean（输入） | 1.00000000 |
| norm max（输入） | 1.00000012 |
| zero-norm rows | 0 |
| normalize 后最大绝对 norm 误差 | 1.19e-7 |

因此不存在 metric mismatch 或未归一化问题。

## 4. 原生 ET-3 noisy：检索质量已保持

HNSW 配置：`M=32, efConstruction=256, efSearch=512, topK=200`。召回评估使用固定随机种子的 2000 个 lensed queries。

| method | partner R@1 | partner R@10 | partner R@50 | observed build + 2000 queries | candidate edges |
| --- | ---: | ---: | ---: | ---: | ---: |
| exact dense | 0.6270 | 0.8565 | 0.9360 | 0.92 s | 40,495,500 |
| HNSW | 0.6270 | 0.8565 | 0.9360 | 0.93 s | 1,800,000 |

HNSW 对 exact dense：

| fidelity metric | value |
| --- | ---: |
| recall@1 vs dense | 0.99600 |
| recall@10 vs dense | 0.99895 |
| recall@50 vs dense | 0.99982 |
| recall@100 vs dense | 0.99987 |

partner recall 与已有 ET-3 waveform-only full-catalog 结果 R@10=0.8542 一致；小差异来自本脚本固定抽取 2000 个 lensed queries，而原报告统计全部有效 queries。

结论：在原生 ET-3 noisy catalog 上，HNSW 近似误差对科学 partner retrieval 指标没有可见影响。这里可以使用“scalability + retrieval-quality-preserved”的表述。

## 5. efSearch 扫描

固定 `M=32, efConstruction=256`：

| efSearch | ANN recall@10 vs dense | partner R@10 | 2000-query time |
| ---: | ---: | ---: | ---: |
| 64 | 0.99895 | 0.8565 | 0.300 s |
| 128 | 0.99895 | 0.8565 | 0.289 s |
| 256 | 0.99895 | 0.8565 | 0.300 s |
| 512 | 0.99895 | 0.8565 | 0.496 s |

这组数据上 `efSearch=64` 已经足够；512 是保守默认值。早期 0.12 并非提高 efSearch 才修复，而是修复 dense top-k 排序后消失。论文中不应把问题归因为“mistuned HNSW”。

## 6. LIGO noisy 对照：embedding 弱，ANN 正常

修复基准后的 9000-event LIGO noisy 结果：

| method | partner R@1 | partner R@10 | partner R@50 |
| --- | ---: | ---: | ---: |
| exact dense | 0.0065 | 0.0240 | 0.0585 |
| HNSW | 0.0065 | 0.0240 | 0.0585 |

HNSW recall@10 vs dense = 0.9988。

因此可以严格拆分两种误差：

- ANN approximation error：约 0.1%，不是主问题。
- LIGO waveform representation error：partner R@10 只有 2.4%，是科学性能瓶颈。

## 7. 规模 stress test

10000、100000、1000000 均由原生 9000 embeddings tile + Gaussian perturbation 生成，明确标记为 synthetic。该构造只用于测工程 scaling 和 ANN fidelity，不能用于声称科学 partner recall 随 catalog size 的真实退化规律。

| N | method | build | sampled query | sampled query count | projected full-query total | candidate edges | ANN recall@10 vs dense |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 9,000 real | dense | 0 | 0.92 s | 2,000 | 4.15 s | 40,495,500 | NA |
| 9,000 real | HNSW | 0.44 s | 0.49 s | 2,000 | 2.65 s | 1,800,000 | 0.99895 |
| 10,000 synth | dense | 0 | 1.01 s | 2,000 | 5.07 s | 49,995,000 | NA |
| 10,000 synth | HNSW | 0.38 s | 0.49 s | 2,000 | 2.84 s | 2,000,000 | 1.00000 |
| 100,000 synth | dense | 0 | 7.88 s | 2,000 | 393.78 s | 4,999,950,000 | NA |
| 100,000 synth | HNSW | 2.29 s | 0.50 s | 2,000 | 27.35 s | 20,000,000 | 1.00000 |
| 1,000,000 synth | HNSW | 26.84 s | 0.90 s | 2,000 | 479.04 s | 200,000,000 | NA |

时间解释：

- `sampled query` 是实际测量值。
- `projected full-query total = build + sampled_query_time * N / 2000`，是线性吞吐量外推，不是全量 query 的直接实测。
- 1M 上 dense 没有运行，因此没有 ANN-vs-dense fidelity 数字。

边数解释：

- dense 列为无向全 pair 数 `N(N-1)/2`。
- ANN 列为有向候选数 `N*K`，K=200。
- 1M 时从约 5.0e11 个无向全 pair 降到 2.0e8 个有向候选，数量级减少约 2500 倍。

## 8. synthetic partner recall 为什么下降

在 100k/1M synthetic catalog 中，每个原始 embedding 被 tile 多次并加入很小的扰动。这会人为产生大量同模板近重复 impostors。随着 tile 次数增加，这些近重复项会挤占 top-k，原始物理 partner 的 rank 因而下降：

- 10k synthetic partner R@10 = 0.836
- 100k synthetic partner R@10 = 0.018
- 1M synthetic partner R@10 = 0.000

这不是 HNSW approximation failure：100k 上 ANN recall@10 vs dense=1.0，且 dense 与 ANN partner R@10 都是 0.018。它是 synthetic stress generator 改变候选难度分布的结果。论文应只使用 synthetic 部分支持工程 scaling，不能用它支持真实百万目录的科学 recall。

## 9. P2-B 最终解释

结果保持不变：

| query direction | Gaussian median+A90 rank | posterior-sample HEALPix rank |
| --- | ---: | ---: |
| GW170104 -> GW170814 | 57 | 4 |
| GW170814 -> GW170104 | 43 | 2 |

必须使用准确 provenance：这些 map 是从 PE H5 中的 RA/Dec posterior samples 通过 KDE/HEALPix reconstruction 得到，`nside=256`；它们不是 BAYESTAR localization products。

推荐术语：

> posterior-sample HEALPix overlap

不推荐术语：

> BAYESTAR skymap overlap

科学含义：GW170104--GW170814 的低 surrogate sky rank 是 median-sky+A90 Gaussian 表达能力不足，而不是 sky consistency 本身不存在。这是适合正文 figure 的结果。

## 10. P2-C 最终解释

GWTC-3 null test 使用 63 个 PE-supported events、1953 pairs 和真实 Liao time LR。GW170104--GW170814：

- time rank = 1361/1953
- observable-only Gaussian sky rank = 1703/1953

长时间差被 time prior 下调，符合 LVK null interpretation。低 Gaussian sky rank 应交叉引用 P2-B：真实 posterior overlap 能恢复该候选的 sky consistency，因此两项结果不矛盾。

top candidates 主要是较短时间差、相对邻近天空位置的 pairs，适合作为 triage；null test 没有证明任何 pair 是强透镜关联，也不应据此设置 discovery claim。

## 11. 论文可直接使用的英文表述

### Methods: ANN retrieval

> We replaced exhaustive all-pairs retrieval with a sparse HNSW candidate-generation stage operating on L2-normalized waveform embeddings. Inner product therefore equals cosine similarity. We used M=32, efConstruction=256, efSearch=512, excluded self-matches, and retained K=200 directed candidates per event. Approximation fidelity was measured against an exact, sorted dense top-k baseline on catalogs for which exhaustive evaluation was feasible.

### Results: native ET-3 fidelity

> On the native 9,000-event noisy ET-3 catalog, exact retrieval and HNSW achieved identical partner recall (R@1=0.6270, R@10=0.8565, and R@50=0.9360). HNSW recovered 99.895% of the exact dense top-10 neighbors, showing that sparse candidate generation preserved retrieval quality in this catalog while reducing the candidate set from 40,495,500 exhaustive pairs to 1,800,000 directed edges.

### Results: scaling caveat

> In a synthetic scaling stress test, HNSW built an index for 10^6 perturbed embeddings in 26.84 s and processed a 2,000-query benchmark in 0.90 s. Linear extrapolation of the measured throughput gives approximately 452 s for querying all 10^6 events (479 s including index construction). The synthetic catalogs contain tiled near-duplicates and were used only to characterize computational scaling, not scientific partner recall.

### Results: posterior sky overlap

> For the historical GW170104--GW170814 candidate, the median-position plus A90 Gaussian surrogate ranked the counterpart at 57 and 43 in the two query directions. A HEALPix overlap reconstructed from PE posterior right-ascension and declination samples improved these ranks to 4 and 2. This comparison identifies surrogate expressiveness, rather than an absence of posterior sky consistency, as the limiting factor.

## 12. 可发表性判断

可以写入论文的结论：

- P2-B：正文结果和新 figure，明确写 posterior-sample HEALPix。
- P2-A native ET-3：HNSW fidelity >0.998、partner recall preserved。
- P2-A synthetic scaling：百万规模 index build 与候选边缩减，附全量 query 为外推的限制。
- P2-C：作为 real-catalog null/triage demonstration，并交叉引用 P2-B。

不能写入论文的过度结论：

- “旧 recall-vs-dense=0.12 证明 HNSW 参数太低。”错误；根因是 dense top-k 未排序。
- “1M 全目录检索在 27 s 完成。”错误；27 s 是建索引加 2000 queries。
- “synthetic 1M partner recall 表示真实 ET-3 百万目录性能。”不成立。
- “P2-B 使用 BAYESTAR skymaps。”不准确。
- “null test 的 top candidates 是 lensing detections。”不成立。

## 12.1 NC 投稿前 gating checklist

当前结果已经把 ANN scaling、真实事件密度、真实稀有度和 graph 指标问题推进到可写入论文的程度，但若目标是 Nature Communications，仍不应把此版本当成最终稿。优先级如下：

1. **端到端 triage + confirmation 闭环**：在接近真实 density 且 `f_lens=1e-3` 的设置下，报告 HNSW retrieval -> physical shortlist -> posterior-overlap / fast Bayes confirmation 的 final recall、final precision/FDR、Bayesian follow-up 次数和总计算时间。核心问题是证明 triage 让原本不可行的 Bayesian follow-up 变成可计算，而不是只证明 triage 自身会留下大量 false candidates。
2. **至少一个领域强 baseline**：加入 posterior-summary kNN、posterior overlap、phase/Morse consistency 或 fast lensing Bayes factor 中至少一项。与 logistic/HGB/LightGBM 的比较只能说明 tested classification-based fusion models 没有超过 weighted sum，不能替代 GW-lensing 领域基线。
3. **真实目录扩大**：GWTC-3 的 63 个 PE-supported BBH 只能作为 case study/null demonstration。投稿前应尽量加入 GWTC-4/O4a 或 GWTC-5 strict-BBH observable catalog；若完整 PE 不可得，要明确写成 candidate-skymap observable-only analysis。
4. **rarity tail 置信区间**：`1e-3` 和 `1e-4` 下的 false-candidate/year 应报告 sampled unlensed pairs、threshold grid、tail-estimation 方法、Poisson/binomial 区间和多 seed 变化，避免给出过度精确的尾部数字。
5. **graph 表格补齐**：正文或 supplement 中的 graph table 必须包含 exact precision/recall、B-cubed precision/recall、over-merge、fragmentation、singleton precision/recall 和 max component size。旧 `system_precision` 只能作为历史对照，不能作为主指标。
6. **公开发布边界**：在 Data/code availability 中准确区分 GitHub code、Zenodo release、derived CSV、selected embeddings/checkpoints 和因体积未发布的数据。不能写“All simulated catalogs and derived data are openly available”，除非这些产物确实有 DOI 或公开下载路径。

建议投稿中心句调整为：

> A physics-guided sparse retrieval stage reduces catalog-scale gravitational-wave lensing search to a tractable Bayesian follow-up problem, with quantified recall, false-association burden and computational cost under realistic event density and source rarity.

## 13. 输出文件

主输出：

- `runs/p2a_ann_et3_noisy_retuned_20260618/ann_scaling.csv`
- `runs/p2a_ann_et3_noisy_retuned_20260618/ann_scaling.png`
- `runs/p2a_ann_et3_noisy_retuned_20260618/ann_scaling.pdf`
- `runs/p2a_ann_et3_noisy_retuned_20260618/run_config.json`
- `runs/p2a_ann_et3_noisy_retuned_20260618.log`

诊断输出：

- `runs/p2a_ann_et3_ef64_20260618/`
- `runs/p2a_ann_et3_ef128_20260618/`
- `runs/p2a_ann_et3_ef256_20260618/`
- `runs/p2a_ann_et3_ef512_20260618/`
- `runs/p2a_ann_ligo_noisy_corrected_20260618/`

P2-B/P2-C：

- `runs/p2b_gwtc3_posterior_healpix_20260618/results/`
- `runs/p2c_null_liao_lr_20260618/`

## 14. 复现命令

```bash
cd /root/autodl-tmp/gw-catalog
source /root/miniconda3/etc/profile.d/conda.sh
conda activate base

python scripts/server_experiments/prepare_p2a_et3_meta.py

python scripts/server_experiments/p2a_ann_sparse_retrieval.py \
  --sizes 9000 10000 100000 1000000 \
  --topk 200 \
  --synthesize \
  --hnsw-m 32 \
  --ef-construction 256 \
  --ef-search 512 \
  --out runs/p2a_ann_et3_noisy_retuned_20260618
```

下一项科学工作应是 parameter-shift/phazap baseline。它与 P2-B 的 sky posterior result 互补，但本轮仓库中没有可直接复用且已验证的 phazap implementation，因此本报告不虚构该结果。
