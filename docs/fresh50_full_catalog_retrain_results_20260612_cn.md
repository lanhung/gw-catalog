# Fresh 50ep Full-Catalog Ranking 重新训练结果总结

生成时间：2026-06-12
实验目录：`runs/fresh50_full_catalog_ranking_20260611/`
结果表：`runs/fresh50_full_catalog_ranking_20260611/fresh50_full_catalog_summary.csv`
实验脚本：`scripts/experiments/84_fresh50_full_catalog_ranking.py`

## 1. 实验目的

本次实验的目的是重新训练 full-catalog ranking 所用的波形编码模型，而不是复用之前缓存的旧 50ep 模型。

之前的 full-catalog ranking 结果主要基于已训练好的缓存模型。为了确认模型重新训练后是否能带来稳定提升，本次对以下四组数据分别重新训练 50 epoch：

| Detector | Data mode | 模型目录 |
|---|---|---|
| ET | pure | `fresh_mixed_encoders/et_pure_mixed_sis_pm_ep50/` |
| ET | noisy | `fresh_mixed_encoders/et_noisy_mixed_sis_pm_ep50/` |
| LIGO | pure | `fresh_mixed_encoders/ligo_pure_mixed_sis_pm_ep50/` |
| LIGO | noisy | `fresh_mixed_encoders/ligo_noisy_mixed_sis_pm_ep50/` |

每组都生成了新的 `model.pt` 和 `history.csv`，说明这次结果来自重新训练后的模型。

## 2. 实验设置

本实验采用 mixed SIS + PM + unlensed full-catalog ranking 设置。

每个 detector / mode 的测试 catalog 规模为：

| 项目 | 数量 |
|---|---:|
| SIS lensed images | 3000 |
| PM lensed images | 3000 |
| SIS unlensed | 1500 |
| PM unlensed | 1500 |
| Catalog total | 9000 |
| Query total | 6000 |

评价方式是在完整 catalog 中为每个 query 排序，统计真实对应像是否进入前 K 名。

## 3. Fresh 50ep 主要结果

以下表格列出 overall 结果。

| 数据 | 方法 | R@1 | R@5 | R@10 | Top 1% | Top 5% | Top 10% |
|---|---|---:|---:|---:|---:|---:|---:|
| ET pure | waveform only | 0.9725 | 0.9903 | 0.9920 | 0.9968 | 0.9993 | 0.9995 |
| ET pure | waveform + time | 0.9240 | 0.9757 | 0.9898 | 0.9975 | 0.9993 | 0.9995 |
| ET pure | waveform + time + predicted sky | 0.9288 | 0.9818 | 0.9923 | 0.9972 | 0.9993 | 0.9995 |
| ET pure | waveform + time + true sky | 0.9987 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| ET noisy | waveform only | 0.3082 | 0.4842 | 0.5648 | 0.7643 | 0.8887 | 0.9347 |
| ET noisy | waveform + time | 0.3588 | 0.5932 | 0.6747 | 0.8497 | 0.9245 | 0.9532 |
| ET noisy | waveform + time + predicted sky | 0.3850 | 0.6017 | 0.6848 | 0.8547 | 0.9245 | 0.9533 |
| ET noisy | waveform + time + true sky | 0.8868 | 0.9723 | 0.9958 | 1.0000 | 1.0000 | 1.0000 |
| LIGO pure | waveform only | 0.9573 | 0.9855 | 0.9910 | 0.9973 | 0.9992 | 0.9997 |
| LIGO pure | waveform + time | 0.9623 | 0.9788 | 0.9870 | 0.9985 | 0.9993 | 1.0000 |
| LIGO pure | waveform + time + predicted sky | 0.9248 | 0.9735 | 0.9865 | 0.9985 | 0.9997 | 1.0000 |
| LIGO pure | waveform + time + true sky | 0.9978 | 0.9995 | 0.9995 | 0.9997 | 0.9997 | 0.9997 |
| LIGO noisy | waveform only | 0.0052 | 0.0193 | 0.0263 | 0.0887 | 0.2158 | 0.3065 |
| LIGO noisy | waveform + time | 0.0532 | 0.1158 | 0.1622 | 0.4315 | 0.5833 | 0.6820 |
| LIGO noisy | waveform + time + predicted sky | 0.0455 | 0.0948 | 0.1388 | 0.4098 | 0.6062 | 0.6872 |
| LIGO noisy | waveform + time + true sky | 0.6065 | 0.8087 | 0.9380 | 1.0000 | 1.0000 | 1.0000 |

## 4. 与旧 full-catalog 结果的差距

旧结果文件：`runs/time_matched_full_catalog_ranking_20260611/full_catalog_summary.csv`
新结果文件：`runs/fresh50_full_catalog_ranking_20260611/fresh50_full_catalog_summary.csv`

| 数据 | 方法 | 旧 R@10 | 新 R@10 | 差值 |
|---|---|---:|---:|---:|
| ET pure | waveform only | 0.9940 | 0.9920 | -0.0020 |
| ET pure | waveform + time | 0.9855 | 0.9898 | +0.0043 |
| ET pure | waveform + time + predicted sky | 0.9922 | 0.9923 | +0.0002 |
| ET pure | waveform + time + true sky | 0.9992 | 1.0000 | +0.0008 |
| ET noisy | waveform only | 0.5457 | 0.5648 | +0.0192 |
| ET noisy | waveform + time | 0.6277 | 0.6747 | +0.0470 |
| ET noisy | waveform + time + predicted sky | 0.6272 | 0.6848 | +0.0577 |
| ET noisy | waveform + time + true sky | 0.9922 | 0.9958 | +0.0037 |
| LIGO pure | waveform only | 0.9903 | 0.9910 | +0.0007 |
| LIGO pure | waveform + time | 0.9870 | 0.9870 | +0.0000 |
| LIGO pure | waveform + time + predicted sky | 0.9885 | 0.9865 | -0.0020 |
| LIGO pure | waveform + time + true sky | 1.0000 | 0.9995 | -0.0005 |
| LIGO noisy | waveform only | 0.0257 | 0.0263 | +0.0007 |
| LIGO noisy | waveform + time | 0.1572 | 0.1622 | +0.0050 |
| LIGO noisy | waveform + time + predicted sky | 0.1493 | 0.1388 | -0.0105 |
| LIGO noisy | waveform + time + true sky | 0.9322 | 0.9380 | +0.0058 |

## 5. 结果分析

### 5.1 ET noisy 有稳定提升

重新训练 50ep 后，ET noisy 的表现明显好于旧缓存模型。其中 `waveform + time + predicted sky` 的 R@10 从 0.6272 提升到 0.6848，提升 0.0577。

这说明 fresh 50ep 训练对 ET noisy 的波形表征有帮助，并且和 time、predicted sky overlap 组合后提升更明显。

### 5.2 LIGO noisy 仍然是主要瓶颈

LIGO noisy 的只靠波形结果几乎没有提升：

| 方法 | 旧 R@10 | 新 R@10 | 提升 |
|---|---:|---:|---:|
| waveform only | 0.0257 | 0.0263 | +0.0007 |
| waveform + time | 0.1572 | 0.1622 | +0.0050 |
| waveform + time + predicted sky | 0.1493 | 0.1388 | -0.0105 |

这说明单纯重新训练 50ep 不能解决 LIGO noisy 的核心问题。

当前 LIGO noisy 的瓶颈主要有两个：

1. LIGO noisy 下波形受噪声影响严重，波形编码相似度难以区分真实透镜像和非透镜候选。
2. predicted sky overlap 在 LIGO noisy 下质量不足，加入后没有稳定提升，甚至略低于只使用 waveform + time。

### 5.3 真实 sky overlap 的上限很高

LIGO noisy 如果使用真实 sky overlap，结果会大幅提升：

| 方法 | R@1 | R@5 | R@10 | Top 1% |
|---|---:|---:|---:|---:|
| waveform + time | 0.0532 | 0.1158 | 0.1622 | 0.4315 |
| waveform + time + predicted sky | 0.0455 | 0.0948 | 0.1388 | 0.4098 |
| waveform + time + true sky | 0.6065 | 0.8087 | 0.9380 | 1.0000 |

这说明 full-catalog ranking 框架本身是有效的。如果能够获得质量足够好的 sky overlap，LIGO noisy 的 catalog-level 检索可以显著提升。

目前的问题不是 catalog-level ranking 方案无效，而是机器学习预测 sky-map / sky-overlap 的质量还不足以替代真实 sky overlap。

## 6. 当前结论

1. 本次实验已经完成 fresh 50ep 重新训练，四组 ET/LIGO pure/noisy 都生成了新的模型和结果。
2. ET noisy 相比旧结果有稳定提升，特别是 `waveform + time + predicted sky` 的 R@10 从 0.6272 提升到 0.6848。
3. LIGO pure 和 ET pure 已经接近饱和，重新训练带来的差异很小。
4. LIGO noisy 仍然是最困难场景，单纯重新训练模型无法明显提升只靠波形的检索性能。
5. predicted sky overlap 当前在 LIGO noisy 中没有起到有效辅助作用，说明 sky-map 预测质量仍是关键限制。
6. true sky overlap 可以把 LIGO noisy 的 R@10 提升到 0.9380，说明真实空间定位信息对这个任务非常关键。

## 7. 后续优化方向

后续如果继续优化 LIGO noisy，建议重点放在以下方向：

1. 提升 LIGO noisy 波形编码器的抗噪能力，例如加入更强的数据增强、对比学习、hard negative mining、denoising pretraining。
2. 单独优化 sky-map 预测模型，重点评估 predicted sky overlap 与 true sky overlap 的误差分布，而不仅看最终 ranking 结果。
3. 尝试让 sky-map 预测模型直接面向 pair-level overlap 目标训练，而不是只做单事件 sky map 回归。
4. 对 LIGO noisy 的 SIS 和 PM 分开诊断，因为当前 LIGO noisy 中 SIS 的 time-only 和 waveform-only 都明显弱于 PM。
5. 在论文中将 `true sky overlap` 作为物理上限或 oracle setting，将 `predicted sky overlap` 作为当前可实现机器学习方案。
