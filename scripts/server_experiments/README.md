# 服务器端实验代码包（需要你的 GPU / 真实数据 / 真实 strain）

这些是我**无法在沙箱里跑**的实验（需要你 autodl 服务器上的训练好的 encoder、
embeddings、真实 strain、真实 GWTC skymap）。我已经把能在沙箱跑的三个实验
（密度、稀有度、图指标）跑完并写进论文了；这里是剩下的、决定能否冲 NC 的三项。

## 放置位置

把整个 `server_experiments/` 目录复制到你的仓库：

```bash
scp -r server_experiments root@<your-server>:/root/autodl-tmp/gw-catalog/scripts/
```

## 三个实验、对应审稿意见、对应论文章节

| 脚本 | 回应审稿 | 写进论文哪里 | 需要什么 |
|---|---|---|---|
| `p2a_ann_sparse_retrieval.py` | #1 "还是 O(N²)" | 替换 §2.8 密度实验旁，证明 O(NK) 可扩展 | 训练好的 embeddings (.npy) + meta.csv |
| `p2b_real_skymap_overlap.py` | #3 "sky 是高斯 surrogate" | §2.8 + Methods sky 部分 | 每事件 HEALPix .fits (BAYESTAR/bilby) |
| `p2c_noise_and_null.py` | #7 "噪声不真实 + 无真实 null test" | 新增 robustness 小节 | 真实 O3/O4 噪声 + encoder；或仅 GWTC observables |

---

## P2-A：ANN 稀疏检索（最重要，直接打掉"伪可扩展"批评）

证明：用 FAISS/HNSW 在 embedding 上做 ANN，只重排 O(NK) 条候选边，
而不是 dense O(N²)。报告 runtime/memory/recall vs N，一路到 10⁶ 事件。

```bash
cd /root/autodl-tmp/gw-catalog
pip install faiss-gpu psutil   # 有 CUDA 用 faiss-gpu，否则 faiss-cpu

python scripts/server_experiments/p2a_ann_sparse_retrieval.py \
    --embeddings runs/<your_run>/catalog_embeddings.npy \
    --meta       runs/<your_run>/catalog_meta.csv \
    --sizes 10000 100000 1000000 \
    --topk 200 \
    --synthesize \
    --out runs/p2a_ann
```

- `catalog_embeddings.npy`：你 dense pipeline 里用的同一组 z_i（编码器输出）。
- `catalog_meta.csv`：列 = event_id, source_id, kind, geocent_time, ra, dec,
  sky_area_90_deg2, network_snr（source_id 为同一透镜系统的两个像共享）。
- 若还没有 10⁶ 事件的真 embedding，加 `--synthesize`（tile+扰动真实
  embedding 到目标规模，脚本会标注 synthetic）——这足以测 ANN 的**扩展性**。
- 输出 `ann_scaling.csv` + `ann_scaling.pdf`：**这张图直接进论文**，证明
  ANN 把 query 时间从 O(N²) 降到近线性，同时 partner recall 基本不掉。

**预期结果**：dense 在 N=10⁶ 不可行（内存/时间爆炸），ANN 在秒级完成且
recall@10 vs dense > 0.95。这就把审稿人 #1 从"致命"变成"已解决"。

---

## P2-B：真实 HEALPix sky overlap（验证高斯 surrogate 是否夸大）

证明：在同一批事件上，用真实 HEALPix posterior overlap 对比高斯 surrogate，
看 surrogate 是否高估了 sky 通道的性能。

```bash
python scripts/server_experiments/p2b_real_skymap_overlap.py \
    --meta runs/<run>/catalog_meta.csv \
    --skymap_dir runs/<run>/skymaps \
    --skymap_col skymap_path \
    --max_events 1000 \
    --out runs/p2b_skymap
```

- 需要每个事件的 HEALPix `.fits`（BAYESTAR 或 bilby 输出）。
- 只需 500–1000 事件子集（审稿人原话），不必全量跑 PE。
- 输出 `skymap_recall.csv`：Gaussian vs HEALPix 的 R@k 对比。

**解读**：若 Gaussian R@k ≫ HEALPix R@k → surrogate 偏乐观，论文里 sky 驱动的
数字是上界（诚实标注即可）；若接近 → surrogate 被验证，是个强结果。两种结论
都对论文有利，因为它把"未验证的近似"变成"已对照的近似"。

---

## P2-C：真实噪声鲁棒性 + 真实 GWTC null test

### Part 2（无需 GPU，立刻能跑）：GWTC null test

用你已经提取的 GWTC observables 跑物理重排，证明 pipeline 不会在真实数据上
制造高置信假关联，并检查 GW170104-GW170814 行为符合预期。

```bash
python scripts/server_experiments/p2c_noise_and_null.py null \
    --observables data/gwtc3_observables.csv \
    --out runs/p2c_null
```

输出 score 分布 + top-20 候选 + 历史候选对的 rank 分析。

> **重要**：把脚本里 `time_score = -np.log1p(dt_days)` 换成你仓库里真正的
> Liao LR（`from scripts.experiments.<...> import fit_time_lr_from_liao`），
> 保持和论文同口径。

### Part 1（需 GPU + 真实 strain）：recolored 真实噪声

这是个 scaffold，逻辑完整，但三处 strain I/O + encoder forward 需要你接到
自己的模块（脚本里标了 TODO 1-3）。步骤：
1. 载入干净 signal bank（你已有的投影 strain）+ meta
2. 每事件抽一段真实 O3/O4 噪声，估 PSD，recolor 到目标 PSD，叠加
3. 跑训练好的 encoder → embedding → 同一套 retrieval+rerank，记录
   Gaussian 噪声 vs recolored 真实噪声的 R@1/R@10

**预期**：encoder 在真实噪声下 R@k 会掉一些；掉多少就是真实噪声鲁棒性结果。
即使掉得多也没关系——它诚实回答了 #7，且和论文"物理先验在波形失效时仍 work"
的主线一致。

---

## 修正你上传的 GWTC 报告里的三个问题

你之前 `gwtc_dual_source_real_event_analysis_report` 有三处要改（我之前指出的）：

1. **GW170104-GW170814 sky "失败" 重新定性**：不是 bug，是 median-sky+A90 高斯
   近似抓不住香蕉形 posterior overlap。用 P2-B 的真实 HEALPix overlap 重算这对，
   大概率能复现文献的"sky 一致"。

2. **A90 中位 ~1020 deg² 可疑**：用 `p2c ... null` 跑前先抽查几个事件的 A90 是否
   和 GWOSC 官网一致。若真这么大，说明很多是单/双探测器事件，sky 通道本就弱。

3. **注入-回收循环性**：注入用的 sky+time 模型 = 打分器模型，所以 R@k 高有
   "自我实现"成分。论文/报告里要写成"机制 sanity check"，不能写成"能发现真透镜"。

---

## 沙箱里已经跑完的三个实验（供参考/复现）

在 `../experiments/` 目录，可在服务器上同样运行（纯 CPU）：

```bash
cd experiments
python exp1_density_stress.py   # 密度 stress test
python exp2_rarity.py           # 稀有度 + 假警负担
python exp3_graph.py            # exact-match 图指标 + 最大权匹配
python make_new_figures.py      # 生成三张图
```

这三个用的是**忠实重建的观测量目录**（你仓库的精确透镜物理），结果已写进论文
§2.8。如果你想用真实 embedding 替换观测量重排，把 `rerank_engine.py` 的打分器
换成你 `matchgw/aux_priors` 的即可。

---

## 优先级建议

1. **先跑 P2-C 的 null test**（无需 GPU，立刻能跑，补上真实数据演示）
2. **再跑 P2-A 的 ANN**（最重要，直接打掉 #1，且 `--synthesize` 不需要真 10⁶ 数据）
3. **P2-B 真实 skymap**（需要 .fits，但只要 1000 事件子集）
4. **P2-C Part 1 真实噪声**（最重，需接你的 strain pipeline，可最后做）

做完 1+2，论文对 NC 的两个最硬批评（伪可扩展、无真实数据）就有实质回应了。
```
