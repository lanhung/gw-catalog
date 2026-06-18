# 文档索引

`docs/` 同时保存当前方案说明和历史实验记录。带日期的报告是实验快照，
其中“当前”“最新”等措辞只代表报告生成当日，不应覆盖较新报告的结论。

## 当前入口

1. `gw_lensing_identification_overall_scheme_detailed_20260617_cn.md`
   - 当前 ET3/LIGO catalog-level 两阶段结构、数据设计和主要结果。
2. `server_experiments_p2_final_assessment_20260618_cn.md`
   - ANN、posterior-sample HEALPix overlap、null test 的最终复核口径。
   - 本文明确替代同日较早的 `server_experiments_p2_results_20260618_cn.md`
     中有关 P2-A ANN 的解释。
   - 写论文时以该文件的谨慎措辞为准：百万规模只代表 ANN 工程 scaling，
     GWTC 只代表 null/case-study，不代表真实透镜确认。
3. `et3_full_experiment_report_20260616_cn.md`
   - ET3 三臂 full-catalog 实验细节。
4. `ligo_h1l1_full_experiment_report_20260617_cn.md`
   - LIGO H1/L1 full-catalog 实验细节。
5. `gwtc_dual_source_real_event_analysis_report_20260617_cn.md`
   - GWTC 双数据源真实事件分析。

## 方法与阶段报告

- `liao_realistic_rerank_overall_scheme_20260615_cn.md`：realistic prior
  和分阶段 rerank 设计。
- `stage0_baseline_report_20260612_cn.md` 至
  `stage6_catalog_graph_discovery_report_20260612_cn.md`：逐阶段消融记录。
- `stage2b_pdf_rule_time_sky_baseline_*`：PDF-rule time/sky 基线。
- `et3_observed_sky_simulation_scheme_20260617_cn.md`：observed-sky 模拟约束。
- `et3_true_sky_oracle_experiment_plan_20260617_cn.md` 和
  `ligo_h1l1_true_sky_oracle_experiment_plan_20260617_cn.md`：仅用于 oracle
  上限实验，不能作为主实验可观测输入方案。

## 历史记录使用规则

- 2026-05 至 2026-06 初的 `current_*`、`*_plan*`、优化总结保留用于追溯，
  不作为当前结果入口。
- `server_experiments_p2_results_20260618_cn.md` 是修复前记录；涉及 ANN
  fidelity、百万规模耗时或 dense top-k 时，以 final assessment 为准。
- `stage6_catalog_graph_discovery_report_20260612_cn.md` 使用旧的宽松
  connected-component `system_precision`，只能作为历史记录。投稿表格应改用
  `scripts/server_experiments/exp3_graph.py` 产生的 exact-match、B-cubed、
  over-merge、fragmentation 和 singleton precision/recall。
- true sky 只能用于生成模拟观测量或 oracle 上限，主 rerank 不应直接使用。
- synthetic 百万目录只支持工程 scaling 结论，不支持真实科学 recall 结论。
- “Realistic class imbalance”仅可用于真实稀有度实验；10% lensed 设置应写成
  high-prevalence/intermediate imbalance stress test。

## 文件卫生

Jupyter 的 `.ipynb_checkpoints/`、Python 的 `__pycache__/`、`*.pyc` 和
`*.bak_*` 都是本地临时产物，不属于文档或源码。它们已由 `.gitignore`
排除，不应作为研究记录引用。
