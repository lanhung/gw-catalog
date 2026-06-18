# 服务器端 P2 实验执行结果报告

> **复核更新（2026-06-18）：** 本文第 4 节早期 P2-A 中的
> `recall@10 vs dense=0.12--0.20` 已确认来自 dense top-200 集合未排序的
> baseline 实现错误，不是 HNSW 召回失败。修复后 ET-3 noisy 原生目录的
> HNSW recall@10 vs exact dense 为 0.99895，且 partner R@10 与 dense 同为
> 0.8565。请以 `docs/server_experiments_p2_final_assessment_20260618_cn.md`
> 作为 P2-A 的最终口径；本文 P2-B/P2-C 数值仍有效。

日期：2026-06-18
服务器项目目录：`/root/autodl-tmp/gw-catalog`
脚本目录：`scripts/server_experiments/`

## 1. 执行范围

按照 `scripts/server_experiments/README.md` 的优先级，本轮在服务器上执行了以下步骤：

1. P2-C Part 2：GWTC 真实事件 null test。
2. P2-A：ANN/HNSW 稀疏检索扩展性实验。
3. P2-B：真实 posterior HEALPix sky overlap 对比 Gaussian surrogate。

P2-C Part 1 真实/recolored 噪声实验没有执行。原因是该脚本仍是 scaffold，需要接入真实 strain I/O、训练好的 encoder forward 和真实噪声段；当前脚本会显式抛出 `NotImplementedError`。

## 2. 脚本与输入

服务器上脚本放置位置已按 README 修正为：

`/root/autodl-tmp/gw-catalog/scripts/server_experiments/`

本轮使用和生成的主要输入：

| 项目 | 路径 | 说明 |
| --- | --- | --- |
| GWTC-3 observables | `data/gwtc3_observables.csv` | 63 个 PE 支持真实事件 |
| P2-A embeddings | `runs/fresh50_full_catalog_ranking_20260611/fresh_mixed_encoders/ligo_noisy_mixed_sis_pm_ep50/test_embeddings.npy` | 9000 x 128 LIGO noisy mixed SIS+PM test embeddings |
| P2-A generated meta | `runs/p2a_ann_ligo_noisy_meta_20260618/catalog_meta.csv` | 9000 个事件，3000 个 lensed systems |
| P2-B posterior maps | `runs/p2b_gwtc3_posterior_healpix_20260618/skymaps/` | 由 PE H5 的 RA/Dec posterior samples 生成，nside=256 |

注意：P2-B 的 posterior maps 是中间文件，体积较大，只保留在服务器，没有同步回 GitHub。

## 3. P2-C：GWTC 真实 null test

### 3.1 修改

README 特别要求把原脚本中的临时 `time_score = -log1p(dt_days)` 替换为仓库真实 Liao LR。已完成修改：

- 使用 `scripts.experiments.88_liao_realistic_p1_p2_rerank.fit_time_lr_from_liao`
- 使用 `scripts.experiments.88_liao_realistic_p1_p2_rerank.time_lr_score_matrix`
- sky 特征复用 `matchgw.aux_priors.observed_sky_pair_features`

### 3.2 命令

```bash
python scripts/server_experiments/p2c_noise_and_null.py null \
  --observables data/gwtc3_observables.csv \
  --out runs/p2c_null_liao_lr_20260618
```

### 3.3 输出

| 文件 | 说明 |
| --- | --- |
| `runs/p2c_null_liao_lr_20260618/gwtc_null_pairs.csv` | 1953 个真实事件 pair 的 time/sky/combined 分数 |
| `runs/p2c_null_liao_lr_20260618/gwtc_null_top20.csv` | top-20 triage candidates |

### 3.4 结果

GWTC-3 null test：

- 事件数：63
- pair 数：1953
- Liao prior：`GW-LMC 2.5PLUS BBH Any_Detected_SNR1`
- Liao delay count：4498
- Liao delay median：32.38 days
- Liao delay p90：269.50 days

combined score 分位数：

| quantile | score |
| ---: | ---: |
| 0.5 | 0.320 |
| 0.9 | 1.603 |
| 0.99 | 2.407 |
| 0.999 | 2.952 |

top-5 triage candidates：

| event_i | event_j | delta_t_days | ang_sep_deg | combined |
| --- | --- | ---: | ---: | ---: |
| GW151012 | GW170104 | 450.01 | 113.08 | 3.188 |
| GW190925_232845 | GW190929_012149 | 3.08 | 61.17 | 3.129 |
| GW191215_223052 | GW191216_213338 | 0.96 | 99.83 | 2.943 |
| GW190519_153544 | GW190521_074359 | 1.67 | 51.28 | 2.926 |
| GW190725_174728 | GW190728_064510 | 2.54 | 43.84 | 2.900 |

GW170104-GW170814 检查：

- 时间差：222.0 days
- 角距离：111.2 deg
- sky rank：1703 / 1953
- time rank：1361 / 1953

解释：长时间差被 Liao time prior 下调，符合预期；median sky + A90 Gaussian surrogate 没有给出 sky 高排名，后续用 P2-B 的 posterior HEALPix overlap 检查。

## 4. P2-A：ANN 稀疏检索扩展性

### 4.1 依赖与环境

服务器原环境没有 `faiss`。安装了：

```bash
python -m pip install --timeout 60 -i https://pypi.org/simple faiss-cpu==1.8.0.post1
```

注意：该版本 `faiss-cpu` 将 numpy 从 2.3.2 降到了 1.26.4，并与 `ligo-skymap>=2.0` 的声明依赖存在冲突。不过本轮 P2-B 中 `healpy`、`ligo.skymap`、`astropy` 仍可导入并完成运行。后续如果继续跑 ligo-skymap 重任务，建议单独建环境隔离 FAISS 和 ligo-skymap。

### 4.2 输入

使用 LIGO noisy mixed SIS+PM test embeddings：

- embeddings：9000 x 128
- meta：9000 events
- lensed systems：3000
- 通过 `--synthesize` 扩展到 1e4、1e5、1e6。

### 4.3 命令

```bash
python scripts/server_experiments/p2a_ann_sparse_retrieval.py \
  --embeddings runs/fresh50_full_catalog_ranking_20260611/fresh_mixed_encoders/ligo_noisy_mixed_sis_pm_ep50/test_embeddings.npy \
  --meta runs/p2a_ann_ligo_noisy_meta_20260618/catalog_meta.csv \
  --sizes 10000 100000 1000000 \
  --topk 200 \
  --synthesize \
  --out runs/p2a_ann_ligo_noisy_20260618
```

### 4.4 输出

| 文件 | 说明 |
| --- | --- |
| `runs/p2a_ann_ligo_noisy_20260618/ann_scaling.csv` | dense vs ANN runtime/memory/recall |
| `runs/p2a_ann_ligo_noisy_20260618/ann_scaling.png` | runtime/recall 图 |
| `runs/p2a_ann_ligo_noisy_20260618/ann_scaling.pdf` | 同上 PDF |

### 4.5 结果

| N | method | total_s | candidate_edges | partner R@10 | recall@10 vs dense |
| ---: | --- | ---: | ---: | ---: | ---: |
| 10000 | dense_exhaustive | 1.12 | 49,995,000 | 0.0065 | NA |
| 10000 | ann_hnsw | 0.43 | 2,000,000 | 0.0185 | 0.1199 |
| 100000 | dense_exhaustive | 7.35 | 4,999,950,000 | 0.0030 | NA |
| 100000 | ann_hnsw | 2.05 | 20,000,000 | 0.0000 | 0.1960 |
| 1000000 | ann_hnsw | 20.82 | 200,000,000 | 0.0000 | NA |

结论分两部分：

1. 扩展性成立：ANN/HNSW 能在 1e6 synthetic events 上完成构建和查询，总时间约 20.8 秒，候选边从 dense 的 O(N²) 降为 N x topK = 2e8。
2. 当前这组 waveform embeddings 的 partner recall 很低，不能用来声称“ANN 不掉召回”。这更像是扩展性工程验证，而不是科学检索性能验证。后续需要换用更强的 embedding 或用 physical/time/sky prefilter 参与 ANN candidate generation。

## 5. P2-B：真实 posterior HEALPix overlap

### 5.1 背景

之前 GWTC 报告中，GW170104-GW170814 的 Gaussian sky surrogate 排名很低。README 指出这不应直接写成 bug，而应解释为 median-sky + A90 Gaussian 近似抓不住真实 posterior 形状。

服务器上没有 GW170104/GW170814 的现成 FITS skymap，只有 PE H5 和 skymap stats。因此本轮从 PE H5 中的 `C01:Mixed/posterior_samples` 抽取 RA/Dec 样本，生成 nside=256 的 HEALPix probability maps。

### 5.2 输入生成

生成目录：

`runs/p2b_gwtc3_posterior_healpix_20260618/skymaps/`

生成内容：

- 63 个 GWTC-3 PE-supported events 的 posterior HEALPix maps
- meta 文件：`runs/p2b_gwtc3_posterior_healpix_20260618/gwtc3_posterior_skymap_meta.csv`
- 将 GW170104 和 GW170814 标记为同一个历史候选 pair

### 5.3 命令

```bash
python scripts/server_experiments/p2b_real_skymap_overlap.py \
  --meta runs/p2b_gwtc3_posterior_healpix_20260618/gwtc3_posterior_skymap_meta.csv \
  --skymap_dir runs/p2b_gwtc3_posterior_healpix_20260618/skymaps \
  --skymap_col skymap_path \
  --max_events 1000 \
  --out runs/p2b_gwtc3_posterior_healpix_20260618/results
```

### 5.4 输出

| 文件 | 说明 |
| --- | --- |
| `runs/p2b_gwtc3_posterior_healpix_20260618/results/skymap_compare.csv` | Gaussian vs HEALPix partner rank |
| `runs/p2b_gwtc3_posterior_healpix_20260618/results/skymap_recall.csv` | R@k 对比 |
| `runs/p2b_gwtc3_posterior_healpix_20260618/results/skymap_compare.png` | 图 |
| `runs/p2b_gwtc3_posterior_healpix_20260618/results/skymap_compare.pdf` | PDF |

### 5.5 结果

| model | R@1 | R@5 | R@10 | R@50 |
| --- | ---: | ---: | ---: | ---: |
| Gaussian surrogate | 0.0 | 0.0 | 0.0 | 0.5 |
| Real HEALPix | 0.0 | 1.0 | 1.0 | 1.0 |

两个方向的 partner rank：

| query direction | Gaussian rank | HEALPix rank |
| --- | ---: | ---: |
| GW170104 -> GW170814 | 57 | 4 |
| GW170814 -> GW170104 | 43 | 2 |

结论：真实 posterior HEALPix overlap 将 GW170104-GW170814 排到 top-5，而 median-sky + A90 Gaussian surrogate 分别排到 57 和 43。这直接支持 README 的判断：之前的 sky “失败”不是物理 pipeline bug，而是 Gaussian surrogate 对复杂 posterior 形状不够表达。

## 6. A90 核查

抽查结果：

| event | A90 deg² | source |
| --- | ---: | --- |
| GW150914 | 251.76 | skymap_stats |
| GW170104 | 1012.57 | skymap_stats |
| GW170814 | 92.14 | skymap_stats |
| GW190412 | 243.40 | skymap_stats |
| GW190521 | 1020.52 | skymap_stats |
| GW191204_171526 | 10887.38 | posterior_ra_dec_gaussian |

整体分布：

| quantile | A90 deg² |
| ---: | ---: |
| min | 34.50 |
| 25% | 380.07 |
| 50% | 1020.52 |
| 75% | 8338.33 |
| 90% | 14814.78 |
| max | 47143.26 |

A90 > 1000 deg²：34 / 63。

解释：A90 中位数约 1020 deg² 不是单纯公式错误。多数早期/低定位精度事件本身 sky localization 很大；部分没有 stats 的事件使用 posterior RA/Dec Gaussian fallback，会进一步放大长尾。报告里应把 sky 通道写成“真实定位质量受限时较弱”，而不是假设所有事件都有高精度 sky。

## 7. 对原 GWTC 报告的修正建议

1. GW170104-GW170814 sky 失败应重新定性：Gaussian median+A90 surrogate 失败，但真实 posterior HEALPix overlap 支持 sky consistency。
2. A90 大的问题应写成真实 catalog 定位精度和 fallback 方法共同导致的长尾，不应简单视为 bug。
3. 注入-回收必须写成 mechanism sanity check。因为注入模型和打分模型共享 time/sky 假设，不能用它单独声称能发现真实透镜。
4. P2-A 的 ANN 结果应分开写：工程扩展性成立，但当前 embedding recall 不足，需要更强 embedding 或 physical candidate generation。

## 8. 结论

本轮按 README 完成了服务器端最优先的 P2-C null test、P2-A ANN scaling 和 P2-B real posterior overlap。

最强结果是 P2-B：真实 HEALPix posterior overlap 把 GW170104-GW170814 排进 top-5，修正了此前 Gaussian surrogate 下 sky rank 很低的问题。

P2-A 给出了 1e6 规模 ANN 工程可运行证据，但也暴露当前 waveform embeddings 的 partner recall 很弱。这个结果不能包装成“检索性能已解决”，只能作为“候选边数量从 O(N²) 降到 O(NK)”的工程扩展性证据。

P2-C null test 已按真实 Liao LR 口径完成，可作为真实 GWTC 数据上不制造强假关联的补充材料。
