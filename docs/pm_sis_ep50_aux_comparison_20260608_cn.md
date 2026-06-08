# PM 与 SIS 全量检索对比结果（50 epoch）

生成时间：2026-06-08

## 实验设置

本次整理包含两组全量实验：

1. PM 数据：`PM 10^4-10^10 M_sun`，生成阶段约束 `t_d >= 24s` 且 `abs(mu_0), abs(mu_1) >= 1`。
2. SIS 数据：已有 10000 match-style SIS 数据。

两组实验均使用相同评估流程：

- waveform 模型：`InceptionTime + bandpass`
- 训练轮数：50 epoch
- 检索任务：catalog-level full ranking
- 每组数据：ET pure、ET noisy、LIGO pure、LIGO noisy
- 对比方法：
  - `waveform only`：只用波形 embedding 相似度
  - `delta_time`：加入 `trigger_time_obs` 计算出的 `delta_time`
  - `delta_time + true sky_sep`：加入真实 `ra/dec` 计算的 sky separation，作为 oracle 上限
  - `delta_time + true sky_overlap`：加入真实位置构造的 sky overlap，作为 oracle 上限
  - `delta_time + predicted sky_overlap`：由 waveform 预测 sky map/方向后计算 sky overlap

> 注：`true sky_sep` 和 `true sky_overlap` 使用真实天空位置，是上限对照，不代表真实观测场景可直接获得。真实可用路线应重点看 `delta_time` 与 `predicted sky_overlap`。

## PM 结果

结果目录：`runs/pm_mass_1e4_1e10_td_min24s_ep50_aux_compare_20260608/summary.csv`

| 数据 | 方法 | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ET pure | waveform only | 0.9570 | 0.9803 | 0.9863 | 0.9937 | 0.9950 | 0.9980 | 1 |
| ET pure | delta_time | 0.9957 | 0.9970 | 0.9970 | 0.9970 | 0.9970 | 0.9970 | 1 |
| ET pure | delta_time + true sky_sep | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| ET pure | delta_time + true sky_overlap | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| ET pure | delta_time + predicted sky_overlap | 0.9933 | 0.9987 | 0.9990 | 0.9990 | 0.9993 | 0.9993 | 1 |
| ET noisy | waveform only | 0.2983 | 0.4657 | 0.5393 | 0.7027 | 0.7650 | 0.8737 | 8 |
| ET noisy | delta_time | 0.8573 | 0.9510 | 0.9870 | 1.0000 | 1.0000 | 1.0000 | 1 |
| ET noisy | delta_time + true sky_sep | 0.9993 | 0.9997 | 0.9997 | 1.0000 | 1.0000 | 1.0000 | 1 |
| ET noisy | delta_time + true sky_overlap | 0.9987 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| ET noisy | delta_time + predicted sky_overlap | 0.8463 | 0.9447 | 0.9873 | 1.0000 | 1.0000 | 1.0000 | 1 |
| LIGO pure | waveform only | 0.9577 | 0.9870 | 0.9900 | 0.9950 | 0.9973 | 0.9990 | 1 |
| LIGO pure | delta_time | 0.9973 | 0.9990 | 0.9993 | 0.9993 | 0.9993 | 0.9993 | 1 |
| LIGO pure | delta_time + true sky_sep | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| LIGO pure | delta_time + true sky_overlap | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| LIGO pure | delta_time + predicted sky_overlap | 0.9960 | 0.9993 | 0.9993 | 0.9993 | 0.9993 | 0.9993 | 1 |
| LIGO noisy | waveform only | 0.0060 | 0.0197 | 0.0290 | 0.0707 | 0.0977 | 0.2287 | 1678 |
| LIGO noisy | delta_time | 0.2520 | 0.7143 | 0.9273 | 1.0000 | 1.0000 | 1.0000 | 3 |
| LIGO noisy | delta_time + true sky_sep | 0.9930 | 0.9993 | 0.9993 | 0.9993 | 0.9993 | 0.9993 | 1 |
| LIGO noisy | delta_time + true sky_overlap | 0.9900 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| LIGO noisy | delta_time + predicted sky_overlap | 0.3293 | 0.7830 | 0.9373 | 1.0000 | 1.0000 | 1.0000 | 2 |

## SIS 结果

结果目录：`runs/sis_ep50_aux_compare_20260608/summary.csv`

| 数据 | 方法 | R@1 | R@5 | R@10 | R@50 | R@100 | R@500 | median rank |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ET pure | waveform only | 0.9583 | 0.9787 | 0.9830 | 0.9937 | 0.9963 | 0.9980 | 1 |
| ET pure | delta_time | 0.8483 | 0.9857 | 0.9937 | 0.9953 | 0.9963 | 0.9997 | 1 |
| ET pure | delta_time + true sky_sep | 0.9983 | 0.9993 | 0.9993 | 0.9993 | 0.9993 | 0.9993 | 1 |
| ET pure | delta_time + true sky_overlap | 0.9987 | 0.9993 | 0.9993 | 0.9993 | 0.9993 | 0.9993 | 1 |
| ET pure | delta_time + predicted sky_overlap | 0.9080 | 0.9843 | 0.9937 | 0.9957 | 0.9973 | 0.9997 | 1 |
| ET noisy | waveform only | 0.4053 | 0.5790 | 0.6533 | 0.7897 | 0.8353 | 0.9147 | 3 |
| ET noisy | delta_time | 0.5267 | 0.7253 | 0.7883 | 0.8723 | 0.9067 | 0.9727 | 1 |
| ET noisy | delta_time + true sky_sep | 0.9563 | 0.9953 | 0.9993 | 0.9993 | 0.9993 | 0.9993 | 1 |
| ET noisy | delta_time + true sky_overlap | 0.9553 | 0.9977 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 |
| ET noisy | delta_time + predicted sky_overlap | 0.5193 | 0.7153 | 0.7733 | 0.8737 | 0.9073 | 0.9723 | 1 |
| LIGO pure | waveform only | 0.9477 | 0.9847 | 0.9883 | 0.9963 | 0.9990 | 0.9997 | 1 |
| LIGO pure | delta_time | 0.9053 | 0.9853 | 0.9940 | 0.9980 | 0.9990 | 0.9990 | 1 |
| LIGO pure | delta_time + true sky_sep | 0.9973 | 0.9980 | 0.9980 | 0.9980 | 0.9980 | 0.9980 | 1 |
| LIGO pure | delta_time + true sky_overlap | 0.9970 | 0.9980 | 0.9987 | 0.9990 | 0.9990 | 0.9990 | 1 |
| LIGO pure | delta_time + predicted sky_overlap | 0.8803 | 0.9883 | 0.9940 | 0.9970 | 0.9980 | 0.9993 | 1 |
| LIGO noisy | waveform only | 0.0107 | 0.0257 | 0.0387 | 0.1010 | 0.1507 | 0.3440 | 1171.5 |
| LIGO noisy | delta_time | 0.0873 | 0.1840 | 0.2477 | 0.4307 | 0.5483 | 0.8433 | 74 |
| LIGO noisy | delta_time + true sky_sep | 0.7990 | 0.9773 | 0.9983 | 0.9993 | 0.9993 | 0.9993 | 1 |
| LIGO noisy | delta_time + true sky_overlap | 0.7873 | 0.9810 | 0.9990 | 0.9993 | 0.9993 | 0.9993 | 1 |
| LIGO noisy | delta_time + predicted sky_overlap | 0.0807 | 0.1740 | 0.2293 | 0.4273 | 0.5230 | 0.8160 | 86 |

## 关键对比

### 1. PM 的 `delta_time` 特征非常强

在 PM 的 LIGO noisy 上，纯波形几乎不可用：

- waveform only：R@10 = 0.0290，median rank = 1678
- delta_time：R@10 = 0.9273，median rank = 3
- delta_time + predicted sky_overlap：R@10 = 0.9373，median rank = 2

说明 PM 扩展质量范围下，透镜时延分布对检索极其有效。加入预测 sky_overlap 只有小幅增益。

### 2. SIS 的 LIGO noisy 仍然是主要困难点

SIS 的 LIGO noisy 结果：

- waveform only：R@10 = 0.0387，median rank = 1171.5
- delta_time：R@10 = 0.2477，median rank = 74
- delta_time + predicted sky_overlap：R@10 = 0.2293，median rank = 86
- delta_time + true sky_overlap：R@10 = 0.9990，median rank = 1

说明 SIS 中真实天空定位信息理论上非常有用，但当前 waveform 预测 sky_overlap 的质量不足，不能替代真实 sky 信息。

### 3. ET noisy 比 LIGO noisy 稳定

ET noisy 上，纯 waveform 已经有一定检索能力：

- PM ET noisy waveform R@10 = 0.5393
- SIS ET noisy waveform R@10 = 0.6533

LIGO noisy 上，纯 waveform 显著下降：

- PM LIGO noisy waveform R@10 = 0.0290
- SIS LIGO noisy waveform R@10 = 0.0387

这说明当前困难主要来自 LIGO noisy 条件下波形形态被噪声破坏后，embedding 无法稳定保持同源关系。

### 4. 真实 sky 信息是强上限，但预测 sky 还不稳定

真实 sky_sep / true sky_overlap 在 PM 与 SIS 的 noisy 条件下都能接近满分，尤其是 LIGO noisy：

- PM LIGO noisy true sky_overlap R@10 = 1.0000
- SIS LIGO noisy true sky_overlap R@10 = 0.9990

但 predicted sky_overlap 表现分化：

- PM LIGO noisy predicted sky_overlap R@10 = 0.9373，略高于 delta_time 的 0.9273
- SIS LIGO noisy predicted sky_overlap R@10 = 0.2293，低于 delta_time 的 0.2477

因此，当前预测 sky-map/sky-overlap 方法对 PM 有轻微帮助，但对 SIS 仍不可靠。

## 论文中可采用的实验结构

建议主表分成两类：

1. 可观测/可部署方法：`waveform only`、`delta_time`、`delta_time + predicted sky_overlap`
2. Oracle 上限方法：`delta_time + true sky_sep`、`delta_time + true sky_overlap`

论文叙述时应避免把 true sky 结果当作真实可部署性能，而应作为“如果定位信息足够准确，catalog 检索可达到的上限”。

## 当前结论

- PM 数据在加入 `delta_time` 后，尤其是 LIGO noisy，已经能达到很高检索性能。
- SIS 数据的 LIGO noisy 仍是核心难点，`delta_time` 有提升但不足，当前 predicted sky_overlap 也没有解决问题。
- 后续优化重点应放在 SIS/LIGO noisy 的可观测 sky-map 预测质量，或者寻找比 sky prediction 更稳健的可观测辅助特征。
