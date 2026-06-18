# ET3 true sky oracle 对照实验方案

## 1. 目的

ET3 主实验使用 observed sky posterior：

```text
true ra/dec
  -> 按 ET_TRIANGLE 网络 SNR 生成 sky_area90_deg2
  -> 从真实位置附近采样 ra_obs/dec_obs
  -> 使用 observed posterior overlap 做 rerank
```

本补充实验使用真实 `ra/dec` 直接做 catalog-level rerank，作为 ET3 的 oracle upper-bound 对照。它用于回答：

1. 如果 ET3 天空位置完全准确，catalog 检索理论上限是多少。
2. observed sky 误差相对于 true sky oracle 损失了多少。
3. waveform、time、true sky 三类信息组合时，是否仍然存在标定冲突。

这组实验不可作为真实可部署性能，只能单独作为上限/消融结果。

## 2. 新增代码

新增脚本：

```text
scripts/experiments/95_et3_true_sky_combinations.py
```

并接入 ET3 runner：

```bash
/root/miniconda3/bin/python scripts/experiments/90_et3_full_experiment_runner.py --phase true_sky
```

输出目录：

```text
runs/et3_liao_realistic_p1_p2_rerank_20260616/stage8_true_sky_oracle_combinations/
```

核心输出：

```text
stage8_true_sky_oracle_combinations_summary.csv
stage8_true_sky_oracle_combinations_partial.csv
```

## 3. true sky 构造方式

true sky oracle 直接使用 catalog 中的真实天空位置：

```text
ra_obs  = ra_true
dec_obs = dec_true
```

为复用现有 step / Gaussian overlap 代码，固定定位面积为：

```text
TRUE_SKY_A90_DEG2 = 1.0
```

输出字段：

```text
scenario        = TRUE_SKY_ORACLE
sky_model       = oracle_true_ra_dec_fixed_a90
sky_sampling    = none_true_center
sky_area90_deg2 = 1.0
```

## 4. 实验组合

Stage8 跑以下组合：

| variant | 输入信息 |
| --- | --- |
| `waveform_only` | 只用 waveform embedding 相似度 |
| `raw_time_only` | 只用当前 catalog trigger time 差 |
| `liao_time_lr_only` | 只用 Liao/GW-LMC time-delay likelihood ratio |
| `true_sky_sep_only` | 只用真实天空角距离 |
| `true_sky_step_only` | 只用 true sky 阶梯函数 |
| `true_sky_log_overlap_only` | 只用 true sky 二维 Gaussian overlap |
| `waveform_plus_true_sky_*` | waveform + true sky |
| `raw_time_plus_true_sky_*` | raw time + true sky |
| `liao_time_lr_plus_true_sky_*` | Liao time prior + true sky |
| `waveform_plus_raw_time_plus_true_sky_step` | waveform + raw time + true sky step |
| `waveform_plus_liao_time_lr_plus_true_sky_step` | waveform + Liao time prior + true sky step |
| `waveform_plus_liao_time_lr_plus_true_sky_log_overlap` | waveform + Liao time prior + true sky Gaussian overlap |

多特征组合的权重在 validation full catalog 上选择：

```text
GRID = [0.25, 0.5, 1.0, 2.0, 4.0]
```

其中 waveform 权重固定为 1.0，其余辅助项在 grid 中选择。

## 5. 和 ET3 observed sky 主实验的区别

| 项目 | observed sky 主实验 | true sky oracle 实验 |
| --- | --- | --- |
| 天空中心 | `ra_obs/dec_obs` | `ra_true/dec_true` |
| 是否有定位误差 | 有，来自 ET_TRIANGLE A90 和采样扰动 | 无 |
| A90 | ET3 网络 SNR 近似，默认 ref=100 deg2 | 固定 1 deg2 |
| 是否可部署 | 更接近可部署 | 不可部署，只是上限 |
| 结果用途 | 主结果 | 诊断 observed sky 误差上限 |

## 6. 运行结果

服务器端已完成运行，使用环境：

| Python | torch | CUDA | GPU |
| --- | --- | --- | --- |
| `/root/miniconda3/bin/python` | 2.8.0+cu128 | 可用 | RTX 5090 |

使用模型：

```text
runs/et3_fresh50_full_catalog_20260616/fresh_mixed_encoders/et3_noisy_mixed_sis_pm_ep50/model.pt
```

运行命令：

```bash
/root/miniconda3/bin/python scripts/experiments/90_et3_full_experiment_runner.py --phase true_sky
```

### 6.1 结果位置

服务器输出：

```text
/root/autodl-tmp/gw-catalog/runs/et3_liao_realistic_p1_p2_rerank_20260616/stage8_true_sky_oracle_combinations/
```

同步到 Git 的轻量结果目录：

```text
docs/results/et3_20260616/et3_liao_realistic_p1_p2_rerank_20260616/stage8_true_sky_oracle_combinations/
```

### 6.2 Overall 结果

| variant | R@1 | R@5 | R@10 | R@50 | top 1% | median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `true_sky_sep_only` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `true_sky_step_only` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `true_sky_log_overlap_only` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `waveform_plus_raw_time_plus_true_sky_step` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `waveform_plus_liao_time_lr_plus_true_sky_step` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `waveform_plus_true_sky_step` | 0.9998 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `raw_time_plus_true_sky_step` | 0.9978 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `liao_time_lr_plus_true_sky_step` | 0.9978 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `waveform_plus_true_sky_sep` | 0.9587 | 0.9878 | 0.9923 | 0.9983 | 0.9993 | 1 |
| `waveform_plus_liao_time_lr_plus_true_sky_log_overlap` | 0.9457 | 0.9862 | 0.9928 | 0.9982 | 0.9987 | 1 |
| `waveform_plus_true_sky_log_overlap` | 0.8600 | 0.9388 | 0.9628 | 0.9873 | 0.9908 | 1 |
| `waveform_only` | 0.6245 | 0.7978 | 0.8542 | 0.9360 | 0.9585 | 1 |
| `raw_time_only` | 0.1352 | 0.4050 | 0.5298 | 0.6327 | 0.6778 | 9 |
| `liao_time_lr_only` | 0.1297 | 0.4040 | 0.5308 | 0.6373 | 0.6830 | 9 |

### 6.3 SIS / PM 分族结果

| subset | best true-sky-only variant | R@1 | R@5 | R@10 | median rank |
| --- | --- | ---: | ---: | ---: | ---: |
| SIS | `true_sky_sep_only` / `true_sky_step_only` / `true_sky_log_overlap_only` | 1.0000 | 1.0000 | 1.0000 | 1 |
| PM | `true_sky_sep_only` / `true_sky_step_only` / `true_sky_log_overlap_only` | 1.0000 | 1.0000 | 1.0000 | 1 |

### 6.4 结论

1. ET3 中 true sky oracle 与 LIGO 一样极强：只用真实天空位置即可达到 overall R@1=1.0。
2. ET3 waveform-only 已经较强，overall R@1=0.6245，明显高于 LIGO H1+L1 的 waveform-only 结果。
3. true sky step 与 waveform/time 组合后基本保持满分，说明 ET3 波形信息和 true-sky step 的标定冲突小于 LIGO。
4. `true_sky_log_overlap` 与 waveform 组合低于 true-sky-only，说明 Gaussian log-overlap 的连续数值尺度仍可能和 waveform score 不完全匹配。
5. 论文/报告中应将 ET3 true sky 与 LIGO true sky 都作为 oracle upper-bound 表；主结果仍应使用 observed sky posterior。
