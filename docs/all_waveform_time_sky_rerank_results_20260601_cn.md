# 原 waveform 模型 + `delta_time + sky_sep` catalog-level reranking 全量结果

日期：2026-06-01

## 方法说明

主模型仍使用原 waveform Siamese encoder / InceptionTime，先计算 waveform embedding similarity。辅助信息只使用两个真实可获得参数：

- `delta_time`: `log1p(|t_i - t_j|)`
- `sky_sep`: 两个事件 RA/DEC 天空位置角距离

最终 catalog-level reranking 使用的特征为：

- `log1p_delta_time`
- `sky_sep`
- `waveform_score`
- `waveform_reciprocal_rank`

没有使用质量、spin、距离等扩展参数。

## 运行入口

脚本：`scripts/experiments/37_all_waveform_time_sky_rerank.py`

结果：

- `runs/all_waveform_time_sky_rerank_20260601/summary.csv`
- `runs/all_waveform_time_sky_rerank_20260601/summary.json`

说明：ET pure 使用已有 `et10000_full_20260527_111510` 中的 ep20 InceptionTime checkpoint；ET noisy、LIGO pure、LIGO noisy 使用已有对应 full/bandpass checkpoint。

## 总表

| detector | data | family | waveform R@1 | waveform R@5 | waveform R@10 | rerank R@1 | rerank R@5 | rerank R@10 | rerank R@50 | rerank median rank |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ET | pure | SIS | 0.9417 | 0.9807 | 0.9873 | 0.9877 | 0.9970 | 0.9983 | 0.9993 | 1 |
| ET | pure | PM | 0.9357 | 0.9740 | 0.9800 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| ET | noisy | SIS | 0.4070 | 0.5913 | 0.6577 | 0.8500 | 0.9443 | 0.9720 | 0.9973 | 1 |
| ET | noisy | PM | 0.3040 | 0.4630 | 0.5407 | 0.9900 | 0.9997 | 1.0000 | 1.0000 | 1 |
| LIGO | pure | SIS | 0.9543 | 0.9833 | 0.9887 | 0.9947 | 0.9960 | 0.9963 | 0.9977 | 1 |
| LIGO | pure | PM | 0.9547 | 0.9843 | 0.9883 | 0.9997 | 1.0000 | 1.0000 | 1.0000 | 1 |
| LIGO | noisy | SIS | 0.0103 | 0.0243 | 0.0400 | 0.4850 | 0.7413 | 0.8617 | 0.9947 | 2 |
| LIGO | noisy | PM | 0.0067 | 0.0170 | 0.0283 | 0.9647 | 1.0000 | 1.0000 | 1.0000 | 1 |

## 结论

1. 该方案在 ET pure/noisy 和 LIGO pure/noisy 上都能提升原 waveform 模型结果。
2. noisy 数据提升最明显：ET noisy SIS 从 R@1=0.4070 到 0.8500，ET noisy PM 从 0.3040 到 0.9900；LIGO noisy SIS 从 0.0103 到 0.4850，LIGO noisy PM 从 0.0067 到 0.9647。
3. LIGO noisy SIS 的 R@1 仍低于其他组，但 R@5=0.7413、R@10=0.8617、R@50=0.9947，说明真实配对已经被稳定排到前列。
4. 后续如果只允许两个辅助参数，主结果建议使用该方案：`waveform model + delta_time + sky_sep catalog-level reranking`。
