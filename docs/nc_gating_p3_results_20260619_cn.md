# NC gating P3 实验结果报告

日期：2026-06-19
项目：`/root/autodl-tmp/gw-catalog`

本轮针对 `docs/server_experiments_p2_final_assessment_20260618_cn.md` 的 §12.1 前三项完成代码实现和服务器运行：

1. 端到端 triage + confirmation 闭环。
2. 领域强 baseline：posterior-summary kNN。
3. GWTC-5 strict-BBH 真实目录扩展。

## 1. 新增脚本

| checklist 项 | 脚本 | 输出目录 |
| --- | --- | --- |
| 端到端闭环 | `scripts/server_experiments/p3a_end_to_end_confirmation.py` | `runs/p3a_end_to_end_confirmation_20260619/` |
| 领域 baseline | `scripts/server_experiments/p3b_domain_baselines.py` | `runs/p3b_domain_baselines_20260619/` |
| GWTC-5 扩展 | `scripts/server_experiments/p3c_gwtc5_strict_bbh_catalog.py` | `runs/p3c_gwtc5_strict_bbh_20260619/` |

## 2. P3-A：端到端 triage + fast confirmation 闭环

### 2.1 实验设计

使用 ET3 observable simulator 生成带真值标签的 realistic-rarity catalog。流程为：

```text
waveform-like synthetic embedding -> HNSW topK candidate generation -> physical time/sky/SNR shortlist -> posterior-summary fast-confirmation surrogate
```

confirmation 阶段是 cheap posterior-summary surrogate，不是完整 lensing Bayes factor；这里的目标是量化 triage 是否能把 O(N^2) follow-up 压到可计算规模，同时保留多少真双像。

### 2.2 结果

| metric | value |
| --- | ---: |
| catalog events | 52602 |
| true lensed pairs | 52 |
| realized lens-pair fraction | 0.000988556 |
| all-pairs count | 1383458901 |
| HNSW candidate pairs | 4013397 |
| HNSW true-pair recall | 1 |
| physical shortlist size | 5000 |
| physical shortlist recall | 0.538462 |
| confirmation follow-up budget | 200 |
| final recall @ budget | 0.173077 |
| final precision @ budget | 0.045 |
| final FDR @ budget | 0.955 |
| candidate reduction vs all-pairs | 344.71 |
| follow-up reduction vs all-pairs | 6.91729e+06 |
| total wall time (s) | 15.7836 |

Follow-up budget 曲线：

|   followup_budget |   true_pairs |   recall |   precision |    fdr |
|------------------:|-------------:|---------:|------------:|-------:|
|           50.0000 |       4.0000 |   0.0769 |      0.0800 | 0.9200 |
|          100.0000 |       7.0000 |   0.1346 |      0.0700 | 0.9300 |
|          200.0000 |       9.0000 |   0.1731 |      0.0450 | 0.9550 |
|          500.0000 |      14.0000 |   0.2692 |      0.0280 | 0.9720 |
|         1000.0000 |      18.0000 |   0.3462 |      0.0180 | 0.9820 |
|         2000.0000 |      24.0000 |   0.4615 |      0.0120 | 0.9880 |
|         5000.0000 |      28.0000 |   0.5385 |      0.0056 | 0.9944 |

### 2.3 解释

HNSW 本身不是瓶颈：在实际检测后 `f_lens≈9.9e-4` 的 52,602-event catalog 上，HNSW top100 覆盖了全部 52 个真双像系统。瓶颈出现在 physical shortlist 和 fast-confirmation 阶段：5000 条 physical shortlist 只保留 28/52 个真系统；如果只允许 200 次 confirmation follow-up，最终 recall=0.173、precision=0.045、FDR=0.955。

这说明 triage 已经把 1.38e9 个全 pair 压到 200 次 follow-up，计算上可行；但当前 fast-confirmation surrogate 的 false-association burden 仍高，不能作为 NC-ready discovery claim。投稿前仍需要更强的 posterior-overlap、fast lensing Bayes factor 或 phase/Morse consistency confirmation。

## 3. P3-B：领域强 baseline - posterior-summary kNN

在同一类 realistic-rarity ET3 labelled catalog 上比较 waveform-like HNSW、posterior-summary kNN、physical time/sky/SNR 和 posterior-summary+physical fusion。

|   N_events |   n_true_pairs |   target_lens_fraction | method                          |   n_queries |    R@1 |    R@5 |   R@10 |   R@50 |   median_rank |   wall_s |   topk |
|-----------:|---------------:|-----------------------:|:--------------------------------|------------:|-------:|-------:|-------:|-------:|--------------:|---------:|-------:|
|      52459 |             52 |                 0.0010 | waveform_like_HNSW_embedding    |         104 | 0.5288 | 0.7788 | 0.8173 | 0.9327 |        1.0000 |   0.9940 |     50 |
|      52459 |             52 |                 0.0010 | posterior_summary_kNN           |         104 | 0.8942 | 0.9712 | 0.9808 | 0.9904 |        1.0000 |   0.0956 |     50 |
|      52459 |             52 |                 0.0010 | physical_time_sky_snr           |         104 | 0.4038 | 0.5000 | 0.5000 | 0.7692 |       10.5000 |   0.7258 |  52458 |
|      52459 |             52 |                 0.0010 | posterior_summary_plus_physical |         104 | 0.5096 | 0.5192 | 0.5192 | 0.7692 |        1.0000 |   1.7167 |  52458 |

最重要的新结论：posterior-summary kNN 是当前最强领域 baseline，R@10=0.9808，明显高于 waveform-like HNSW 的 0.8173，也高于 physical-only 的 0.5000。这个结果可以直接回应 §12.1 第 2 项：论文不能只和 logistic/HGB/LightGBM 这类 classification fusion 比，还必须纳入 posterior-summary / posterior-overlap 这类领域基线。

当前简单 `posterior_summary_plus_physical` fusion 反而低于 kNN，说明 naive 加权会被 time/sky 的现实稀有度误报拖累；后续应使用 validation-selected 或 ranking-objective fusion，而不是手写等权相加。

## 4. P3-C：GWTC-5 strict-BBH 真实目录扩展

### 4.1 目录规模

| metric | value |
| --- | ---: |
| events | 105 |
| pairs | 5460 |
| time span days | 288.524 |
| median network SNR | 11.0819 |
| median A90 deg2 | 1148.15 |
| p90 A90 deg2 | 6367.89 |
| candidate skymaps | 105 |
| missing chirp mass | 0 |
| missing mass ratio | 5 |

### 4.2 Null shortlist

| metric | value |
| --- | ---: |
| Campailla-fraction equivalent count | 276 |
| equivalent threshold | 1.86366 |
| top-185 fraction | 0.0338828 |
| top-185 threshold | 2.07058 |
| combined score q90 | 1.56989 |
| combined score q99 | 2.79193 |
| combined score q999 | 3.70909 |

完整 top combined、top sky、posterior-summary kNN top pairs 和 GWTC-5 injection recovery 表在 `runs/p3c_gwtc5_strict_bbh_20260619/p3c_gwtc5_report.md`。

### 4.3 解释

GWTC-5 strict-BBH 扩展到 105 个事件、5460 对，比 GWTC-3 PE-supported 的 63 个事件/1953 对更大。105 个事件都有 candidate skymap；A90 中位数为 1148 deg2，p90 为 6368 deg2，说明真实 candidate-skymap localization 仍很宽。Campailla 185/3655 等价保留 276 对，适合作为 cheap triage 后接 posterior/Bayes confirmation 的输入。

注入恢复仍显示 sky_step 在 GWTC-5 背景中最强：K=10 时 R@10=0.91，K=20 时 R@10=0.9025；combined_time_sky 在 GWTC-5 上较弱，说明 time prior 权重与 O4/GWTC-5 candidate 背景还需要重新校准。

严格表述：这是 `candidate-skymap observable-only analysis`，不是完整 PE posterior catalog；不能写成真实透镜确认。

## 5. 复现命令

```bash
cd /root/autodl-tmp/gw-catalog
/root/miniconda3/bin/python scripts/server_experiments/p3a_end_to_end_confirmation.py --n-true-pairs 60 --lens-fraction 1e-3 --n-background 110000 --seed 0 --topk 100 --shortlist-budget 5000 --followup-budget 200 --out runs/p3a_end_to_end_confirmation_20260619
/root/miniconda3/bin/python scripts/server_experiments/p3b_domain_baselines.py --n-true-pairs 60 --lens-fraction 1e-3 --n-background 110000 --seed 1 --topk 50 --out runs/p3b_domain_baselines_20260619
/root/miniconda3/bin/python scripts/server_experiments/p3c_gwtc5_strict_bbh_catalog.py --out runs/p3c_gwtc5_strict_bbh_20260619
```

## 6. 投稿状态判断

本轮完成了 §12.1 前三项的代码和初步服务器结果，但结论是 mixed：

- 可正面写入：sparse retrieval 让 follow-up 数量从 1.38e9 all-pairs 降到 200-5000 量级；posterior-summary kNN baseline 已加入且非常强；GWTC-5 strict-BBH observable-only catalog 已扩展。
- 仍不能过度声称：当前 fast-confirmation surrogate 在 `f_lens≈1e-3` 下 precision 仍低、FDR 高；GWTC-5 缺完整 PE posterior；time+sky 权重在 GWTC-5 背景上需要重新校准。
- 下一步最重要：把 P3-A 的 confirmation surrogate 替换成真正的 posterior-overlap / fast lensing Bayes factor / phase-Morse consistency，并对 threshold 做 validation-selected calibration。
