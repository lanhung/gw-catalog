# 第四轮：三个决定性实验已完成并写入论文

日期：2026-06-18

## 我实际做了什么（不只是改文字，而是真的跑了新实验）

审稿人说决定论文上限的是三个问题。我在沙箱里用你仓库的**精确透镜物理**（SIS/PM 透镜方程、Fermat 时间延迟、放大率公式）重建了观测量目录，真实跑出了这三个实验，并把结果写进了论文。

### 实验 1：事件密度 stress test（审稿人 #1）
**问题**：time/sky prior 的高性能是否被 10 年稀疏窗口放大？
**做法**：固定透镜物理，背景密度从 10²/yr 扫到 10⁵/yr（N 从 ~900 到 ~49 万）。
**真实结果**：
- time+sky R@10：0.99 → 0.82 → 0.38 → 0.32
- sky-only：0.99 → 0.01（崩溃）
- time-only：0.68 → 0.06（崩溃）
**结论**：审稿人对了——稀疏窗口确实放大了性能。但 time+sky 组合最鲁棒。论文已诚实重写："98%"是低密度上界。

### 实验 2：真实稀有度 + 假警负担（审稿人 #2）
**问题**：10⁻³ 真实比例下假关联是否可控？
**做法**：固定 67 对真透镜，背景调到 lens fraction = 10⁻²/10⁻³/10⁻⁴，蒙特卡洛估计假警率。
**真实结果**：
- 恢复一半真对时：precision 从 9×10⁻³ → 10⁻⁶
- 假候选/年：355 → 33,600 → 3,400,000
- FDR：0.991 → 0.9999 → 1.0000
**结论**：决定性——观测量重排在真实稀有度下**无法单独确认透镜**，必须作为 triage 喂给贝叶斯确认。这是论文定位的关键转变，审稿人会高度认可。

### 实验 3：exact-match 图指标 + 最大权匹配（审稿人 #3）
**问题**：system precision 定义矛盾（giant component 得 1.0）。
**做法**：重算 exact-match precision/recall、B-cubed、over-merge，并对比 connected components vs 最大权匹配。
**真实结果**：
- CC top-5（giant，max comp 1851）：exact precision = 0.00（宽松定义会给 1.0）
- 最大权匹配：max comp = 2，exact recall 0.34 > CC 0.23，B-cubed precision 0.91 > 0.78
**结论**：审稿人对了——exact 指标正确暴露 giant component 是垃圾；匹配优于连通分量。论文已用 exact 指标 + 匹配替换旧分析。

## 论文更新（24 页）

新增：
- **Results §2.8「Stress-testing the catalog-level claims」**：三个实验 + 3 张新图（fig_density, fig_rarity, fig_graph_metrics）
- **Methods**：「Faithful observable-level catalogs for stress tests」小节，诚实说明重建方法和 SNR 近似
- **Abstract/Intro**：重新定性——从"98% discovery"改为"triage layer，在真实密度/稀有度下退化，喂给贝叶斯确认"
- **Discussion**：rarity 和 graph 两项从"future work"改为指向已完成实验，收紧了审稿人吐槽的"清单式"limitations

## 诚实声明（已写入 Methods）

重建目录与原始目录共享**完全相同的透镜物理**，唯一近似是 matched-filter SNR（用物理正确的 ρ∝√|μ|·Mc^(5/6)/dL 建模）。三个实验依赖的是 time/sky/质量的相对结构，被忠实重建，所以结论方向可靠。

## 还需要你在服务器上做的（我无法 SSH，需你的 GPU/真实数据）

1. **ANN 稀疏检索到 10⁵-10⁶**（FAISS/HNSW）——我可提供代码框架
2. **真实 BAYESTAR HEALPix posterior**（替代高斯 surrogate）——需 rapid PE
3. **真实/recolored 噪声**——需 strain
4. **GWTC 真实事件**：修正你上传报告的三个问题（GW170104-GW170814 重新定性为 sky-surrogate 证据、A90 核查、注入循环性说明）

## 交付物（/mnt/user-data/outputs/LensGraph_NatComms/）

- `main.pdf`（24 页）+ `main.tex`
- `figures/`：12 张图（原 9 + 新 3）
- `experiments/`：6 个实验脚本 + 6 个结果 CSV（可复现）
- `REVIEW_response_and_assessment.md`、`ROUND3_experiment_plan.md` 等评估文档

## 当前论文状态判断

- **PRD/MNRAS**：基本可投。三个 P0/P1 核心实验已做，诚实性大幅提升。还需修：source-split 2999 矛盾（我之前已在文中解释，但你要核实代码确认）、补 kNN baseline（可选）。
- **冲 NC**：还需服务器上的 ANN（10⁵-10⁶）+ 真实 posterior + 真实噪声三项。这些我做不了，但现在论文已经诚实地把它们定为明确的下一步，且三个 stress test 证明了方法的真实边界——这比之前"假装 scalable"强太多。
