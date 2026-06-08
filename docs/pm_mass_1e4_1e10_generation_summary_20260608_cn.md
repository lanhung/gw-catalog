# PM 透镜质量扩展数据生成记录（2026-06-08）

## 目的

将 PM 透镜质量采样范围从原来的 `10^8-10^10 M_sun` 扩展到 `10^4-10^10 M_sun`，并生成一组新的 ET/LIGO 透镜与未透镜数据。旧数据不覆盖。

## 生成代码

新脚本目录：

- `data_generation/pm_mass_1e4_1e10_scripts/PM_GW_events_ET_pm_mass_1e4_1e10.py`
- `data_generation/pm_mass_1e4_1e10_scripts/PM_GW_events_LIGO_pm_mass_1e4_1e10.py`
- `data_generation/pm_mass_1e4_1e10_scripts/unlensed_GW_events_ET_pm_mass_1e4_1e10.py`
- `data_generation/pm_mass_1e4_1e10_scripts/unlensed_GW_events_LIGO_pm_mass_1e4_1e10.py`
- `data_generation/pm_mass_1e4_1e10_scripts/run_pm_mass_1e4_1e10_all.sh`

PM 透镜质量采样代码：

```python
m_l = np.random.uniform(1e4, 1e10) * ms
```

## 输出位置

新数据输出目录：

`data_generation/pm_mass_1e4_1e10_outputs/`

该目录包含较大的 `.npy` 波形数据，未上传到 GitHub。

## 生成完成情况

日志：

`logs/pm_mass_1e4_1e10_generation.log`

四个任务均已完成：

| run | 说明 | 样本数 |
|---|---|---:|
| `PM_GW_events_ET_pm_mass_1e4_1e10` | ET PM 透镜数据 | 10000 个透镜系统，两幅透镜像 |
| `PM_GW_events_LIGO_pm_mass_1e4_1e10` | LIGO PM 透镜数据 | 10000 个透镜系统，两幅透镜像 |
| `unlensed_GW_events_ET_pm_mass_1e4_1e10` | ET 未透镜数据 | 10000 条 |
| `unlensed_GW_events_LIGO_pm_mass_1e4_1e10` | LIGO 未透镜数据 | 10000 条 |

## 实际 PM 透镜质量范围

本次随机生成的 `lens_params.csv` 中，PM 透镜质量字段为 `m_l`，单位为 `M_sun`。

| 数据 | min `M_sun` | max `M_sun` | median `M_sun` |
|---|---:|---:|---:|
| ET PM | `4.8786e5` | `9.9986e9` | `5.0263e9` |
| LIGO PM | `4.8786e5` | `9.9986e9` | `5.0263e9` |

说明：代码采样范围是 `10^4-10^10 M_sun`，但有限 10000 个随机样本中实际最小值为约 `4.88e5 M_sun`，没有抽到特别接近 `10^4 M_sun` 的样本。

## GitHub 上传说明

已上传到 GitHub 的内容包括：

- 生成脚本
- 运行脚本
- 本说明文档

未上传内容：

- `.npy` 波形数据
- 生成输出目录中的大文件

原因：这些文件体积很大，不适合直接放入 GitHub 普通仓库。
