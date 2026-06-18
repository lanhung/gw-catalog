# LIGO H1+L1 true sky oracle 对照实验方案

## 1. 目的

当前 LIGO H1+L1 主实验使用的是 observed sky：

```text
true ra/dec
  -> 按 LIGO_HL 网络 SNR 生成 sky_area90_deg2
  -> 在真实位置附近采样 ra_obs/dec_obs
  -> 用 observed posterior overlap 做 rerank
```

这更接近真实观测流程。用户提出 LIGO 结果中也需要补充使用真实 sky 数据的结果，因此新增一组单独的 oracle 对照实验，用来回答：

1. 如果天空位置完全准确，LIGO catalog-level 检索的理论上限是多少。
2. 当前 observed sky 的误差是否是性能瓶颈。
3. 时间、波形和 true sky 三类信息组合时，哪些组合最有效。

这组结果不能作为真实部署性能，只能作为上限/消融实验。

## 2. 新增代码

新增脚本：

```text
scripts/experiments/94_ligo_h1l1_true_sky_combinations.py
```

并接入 LIGO runner：

```bash
python scripts/experiments/92_ligo_h1l1_full_experiment_runner.py --phase true_sky
```

输出目录：

```text
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage8_true_sky_oracle_combinations/
```

核心输出：

```text
stage8_true_sky_oracle_combinations_summary.csv
stage8_true_sky_oracle_combinations_partial.csv
```

## 3. true sky 构造方式

true sky 表由原始 catalog 中的真实天空位置直接构造：

```text
ra_obs  = ra_true
dec_obs = dec_true
```

为了复用现有二维 Gaussian / step overlap 代码，脚本设置固定定位面积：

```text
TRUE_SKY_A90_DEG2 = 1.0
```

对应字段：

```text
scenario       = TRUE_SKY_ORACLE
sky_model      = oracle_true_ra_dec_fixed_a90
sky_sampling   = none_true_center
sky_area90_deg2 = 1.0
```

因此 true sky 实验不再模拟观测误差，不使用 H1L1 timing localization，也不使用 antenna pattern 或 HEALPix skymap。

## 4. 计算的 sky 特征

脚本计算三类 true sky 分数矩阵：

| 特征 | 含义 |
| --- | --- |
| `true_sky_sep` | 真实 RA/DEC 的角距离，分数为 `-sep`，越近越高 |
| `true_sky_step` | 基于归一化距离的阶梯函数 |
| `true_sky_log_overlap` | 固定 A90 下的二维 Gaussian log-overlap |

其中 `true_sky_step` 与 observed sky 主实验使用同一套阈值：

```text
d_sky <= 1.18          strong match
1.18 < d_sky <= 2.15   moderate match
2.15 < d_sky <= 3.03   weak match
d_sky > 3.03           mismatch
```

## 5. 实验组合

Stage8 会跑以下组合：

| variant | 输入信息 |
| --- | --- |
| `waveform_only` | 只用波形 embedding 相似度 |
| `raw_time_only` | 只用当前 catalog trigger time 差 |
| `liao_time_lr_only` | 只用 Liao/GW-LMC time-delay likelihood ratio |
| `true_sky_sep_only` | 只用真实天空角距离 |
| `true_sky_step_only` | 只用 true sky 阶梯函数 |
| `true_sky_log_overlap_only` | 只用 true sky 二维 Gaussian overlap |
| `waveform_plus_true_sky_*` | 波形 + true sky |
| `raw_time_plus_true_sky_*` | raw time + true sky |
| `liao_time_lr_plus_true_sky_*` | Liao time prior + true sky |
| `waveform_plus_raw_time_plus_true_sky_step` | 波形 + raw time + true sky step |
| `waveform_plus_liao_time_lr_plus_true_sky_step` | 波形 + Liao time prior + true sky step |
| `waveform_plus_liao_time_lr_plus_true_sky_log_overlap` | 波形 + Liao time prior + true sky Gaussian overlap |

多特征组合的权重仍然在 validation full catalog 上选择：

```text
GRID = [0.25, 0.5, 1.0, 2.0, 4.0]
```

其中 waveform 权重固定为 1.0，其余辅助项在 grid 中选择。

## 6. 和 observed sky 主实验的区别

| 项目 | observed sky 主实验 | true sky oracle 实验 |
| --- | --- | --- |
| 天空中心 | `ra_obs/dec_obs` | `ra_true/dec_true` |
| 是否有定位误差 | 有，来自 A90 和采样扰动 | 无 |
| A90 | LIGO_HL 网络 SNR 近似，默认 ref=100 deg2，并有 sweep | 固定 1 deg2 |
| 是否可部署 | 更接近可部署 | 不可部署，只是上限 |
| 结果用途 | 主结果 | 诊断 observed sky 误差上限 |

## 7. 运行结果

服务器端已使用 `/root/miniconda3/bin/python` 完成运行。环境检查：

| Python | pandas | sklearn | torch | CUDA |
| --- | --- | --- | --- | --- |
| `/root/miniconda3/bin/python` | 3.0.3 | 1.8.0 | 2.8.0+cu128 | 可用，RTX 5090 |

使用模型：

```text
runs/ligo_h1l1_fresh50_full_catalog_20260617/fresh_mixed_encoders/ligo_noisy_mixed_sis_pm_ep50/model.pt
```

运行命令为：

```bash
/root/miniconda3/bin/python scripts/experiments/92_ligo_h1l1_full_experiment_runner.py --phase true_sky
```

服务器输出：

```text
runs/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage8_true_sky_oracle_combinations/
  stage8_true_sky_oracle_combinations_summary.csv
  stage8_true_sky_oracle_combinations_partial.csv
```

已同步到本地轻量结果目录：

```text
docs/results/ligo_h1l1_20260617/ligo_h1l1_liao_realistic_p1_p2_rerank_20260617/stage8_true_sky_oracle_combinations/
```

### 7.1 Overall 结果

| variant | R@1 | R@5 | R@10 | R@50 | top 1% | median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `true_sky_sep_only` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `true_sky_step_only` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `true_sky_log_overlap_only` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `raw_time_plus_true_sky_step` | 0.9978 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `waveform_plus_liao_time_lr_plus_true_sky_step` | 0.9975 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `liao_time_lr_plus_true_sky_step` | 0.9973 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `waveform_plus_raw_time_plus_true_sky_step` | 0.9973 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `waveform_plus_true_sky_step` | 0.9713 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| `liao_time_lr_only` | 0.1445 | 0.4127 | 0.5273 | 0.6398 | 0.6860 | 9 |
| `raw_time_only` | 0.1365 | 0.4117 | 0.5308 | 0.6332 | 0.6778 | 9 |
| `waveform_only` | 0.0040 | 0.0145 | 0.0235 | 0.0653 | 0.0900 | 2431 |

### 7.2 SIS / PM 分族结果

| subset | best true-sky-only variant | R@1 | R@5 | R@10 | median rank |
| --- | --- | ---: | ---: | ---: | ---: |
| SIS | `true_sky_sep_only` / `true_sky_step_only` / `true_sky_log_overlap_only` | 1.0000 | 1.0000 | 1.0000 | 1 |
| PM | `true_sky_sep_only` / `true_sky_step_only` / `true_sky_log_overlap_only` | 1.0000 | 1.0000 | 1.0000 | 1 |

### 7.3 结论

1. LIGO H1+L1 中，真实天空位置是极强 oracle 信息：只用 true sky 就能达到 overall R@1=1.0。
2. 这说明 true sky 结果只能作为理论上限，不能和 observed sky 主结果混作真实可部署性能。
3. true sky step 与 true sky sep/log-overlap 都达到满分，说明在无观测误差时，当前 catalog 中透镜配对的真实天空位置足够区分正负样本。
4. 加入 waveform 后部分组合反而低于 true-sky-only，例如 `waveform_plus_true_sky_step` 为 R@1=0.9713，说明 waveform score 与 oracle sky score 标定不一致时会引入少量排序干扰。
5. 对论文或报告建议：主表使用 observed sky；true sky 单独放在 oracle upper-bound / ablation 表中，用来说明天空定位误差对 LIGO 结果的影响上限。
