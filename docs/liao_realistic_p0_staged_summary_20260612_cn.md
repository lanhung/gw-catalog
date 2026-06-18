# Liao realistic rerank P0 分阶段实验总览

生成时间：2026-06-12

## 1. 实验范围

本轮按照 `gw_catalog_liao_realistic_rerank_plan.md` 的 P0 优先级执行，只覆盖以下内容：

- Stage0：当前 baseline，waveform + raw trigger_time_obs。
- Stage1：只新增 Liao/GW-LMC time-delay likelihood-ratio prior。
- Stage2：只新增 observed sky posterior。
- Stage3：融合 Liao time LR + observed sky posterior。

本轮没有加入 SNR ratio、amplitude prior、LightGBM、cross-encoder 或 catalog connected-component discovery。

## 2. 代码与输出位置

| 项目 | 路径 |
| --- | ---: |
| 实验脚本 | `scripts/experiments/87_liao_realistic_staged_rerank.py` |
| 总结果目录 | `runs/liao_realistic_staged_rerank_20260612` |
| Stage0 文档 | `docs/stage0_baseline_report_20260612_cn.md` |
| Stage1 文档 | `docs/stage1_liao_time_lr_report_20260612_cn.md` |
| Stage2 文档 | `docs/stage2_observed_sky_report_20260612_cn.md` |
| Stage3 文档 | `docs/stage3_liao_time_plus_observed_sky_report_20260612_cn.md` |

## 3. 每阶段最佳结果对比

| Stage | Detector | Variant | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Stage0 baseline | ET | waveform_plus_raw_time_val_selected | 0.6262 | 0.7768 | 0.8245 | 0.9265 | 0.9765 | 0.9865 | 1 |
| Stage0 baseline | LIGO | waveform_plus_raw_time_val_selected | 0.1843 | 0.4255 | 0.5335 | 0.6967 | 0.8502 | 0.9177 | 8 |
| Stage1 Liao time LR | ET | waveform_plus_liao_time_lr_val_selected | 0.6112 | 0.7527 | 0.8015 | 0.9243 | 0.9817 | 0.9915 | 1 |
| Stage1 Liao time LR | LIGO | waveform_plus_liao_time_lr_val_selected | 0.1658 | 0.4112 | 0.5197 | 0.7093 | 0.8487 | 0.918 | 9 |
| Stage2 observed sky | ET | waveform_plus_observed_sky_step_val_selected | 0.7738 | 0.888 | 0.9152 | 0.9615 | 0.9817 | 0.988 | 1 |
| Stage2 observed sky | ET | waveform_plus_observed_sky_log_overlap_val_selected | 0.6225 | 0.7543 | 0.793 | 0.8977 | 0.9563 | 0.9815 | 1 |
| Stage2 observed sky | LIGO | waveform_plus_observed_sky_step_val_selected | 0.171 | 0.2958 | 0.3895 | 0.853 | 0.9812 | 0.9898 | 17 |
| Stage2 observed sky | LIGO | waveform_plus_observed_sky_log_overlap_val_selected | 0.0735 | 0.1375 | 0.1752 | 0.3503 | 0.607 | 0.7558 | 259 |
| Stage3 time+observed sky | ET | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.896 | 0.9708 | 0.9825 | 0.9972 | 0.9997 | 0.9997 | 1 |
| Stage3 time+observed sky | ET | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.7795 | 0.8827 | 0.9177 | 0.9865 | 0.9975 | 0.9995 | 1 |
| Stage3 time+observed sky | LIGO | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | 0.658 | 0.8567 | 0.9073 | 0.9903 | 0.9985 | 0.9993 | 1 |
| Stage3 time+observed sky | LIGO | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | 0.3792 | 0.6062 | 0.6742 | 0.839 | 0.9478 | 0.9833 | 3 |

## 4. Baseline 与单因素结论

### Stage0 baseline

Stage0 表明直接 weighted fusion 比此前 HGB reranker 更稳定。ET noisy 的 waveform+raw time R@10=0.8245，LIGO noisy 的 waveform+raw time R@10=0.5335。

### Stage1 Liao time LR

Liao time LR 单独作为时间先验没有超过 raw time baseline。ET noisy waveform+Liao time LR R@10=0.8015，低于 Stage0 raw time 的 0.8245；LIGO noisy waveform+Liao time LR R@10=0.5197，低于 Stage0 raw time 的 0.5335。

这说明当前模拟数据的时间结构与 GW-LMC/Liao 分布并不完全一致。Liao time LR 更适合作为 realistic prior 实验，而不是当前 toy 数据上的性能增强项。

### Stage2 observed sky

Observed sky posterior 是非常强的辅助信息，尤其 step weight。ET noisy waveform+observed sky step R@10=0.9152；LIGO noisy observed sky step only R@10=0.7713。

但需要明确：这里的 observed sky 是由 true ra/dec 加观测误差模拟得到，不是机器学习 predicted sky-map。它适合作为 realistic observed-sky 条件下的实验，不应和 predicted sky-map 结果混为一谈。

### Stage3 time + observed sky

Stage3 把 Liao time LR 与 observed sky posterior 融合后显著提升。ET noisy step 版本 R@10=0.9825，LIGO noisy step 版本 R@10=0.9073。

这说明：如果真实观测中能够获得可靠 sky posterior，catalog-level rerank 的上限非常高；时间先验与 sky posterior 在综合排序中有互补作用。

## 5. 重要注意事项

1. Stage2/Stage3 的 observed sky 是模拟观测 sky posterior，不是当前 ML predicted sky-map。
2. Stage1 的 Liao prior 使用 GW-LMC time-delay distribution；LIGO 使用 2.5PLUS 作为近似参考，不等同于真实 LIGO HL。
3. 当前 P0 仍未加入 SNR ratio 和 magnification/amplitude prior。
4. LIGO noisy 的 SIS/PM 子集仍需单独查看，不能只看 overall。
5. 后续如果写论文，true sky oracle、observed sky simulation、predicted sky-map 三者必须分开命名。

## 6. 后续建议

1. 继续 P1：加入 SNR ratio raw prior，但仍然单独成 Stage4，不和别的因素混跑。
2. 对 Stage2 observed sky 做 A90 sweep：ET 100/300/1000 deg2，LIGO 50/100/200 deg2。
3. 对 LIGO noisy SIS 单独优化和报告。
4. 在 P0 稳定后，再比较 logistic/HGB/LightGBM，不要提前替代 weighted-sum baseline。
