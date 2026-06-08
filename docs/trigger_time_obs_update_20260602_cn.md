# trigger_time_obs 替代 geocent_time 计算 delta_time 的代码更新记录

生成日期：2026-06-02

## 1. 修改原因

根据本地文档《观测触发时间估计值_概念说明与代码修改指南.docx》，真实观测中不能直接把模拟真值 `geocent_time` 或 `lens.csv` 中的 `t_d` 当作模型输入。模型或 catalog-level reranker 应使用观测可获得的触发时间估计值：

```text
trigger_time_obs = geocent_time_true + timing_jitter
```

候选 pair 的时间差改为：

```text
delta_time_obs = abs(trigger_time_obs_i - trigger_time_obs_j)
log1p_delta_time_obs = log(1 + delta_time_obs)
```

其中 timing jitter 使用文档建议的 SNR 相关误差模型：

```text
sigma_t = max(0.01, 1.0 / max(SNR, 1.0))
```

## 2. 新增代码

新增文件：

```text
matchgw/trigger_time.py
```

主要函数：

```text
timing_sigma_from_snr
ensure_lensed_trigger_time_features
ensure_unlensed_trigger_time_features
catalog_trigger_time_frame
log1p_delta_time_obs
```

作用：

1. 为 SIS/PM 透镜双像生成 `SIS_trigger_time_features.csv` 或 `PM_trigger_time_features.csv`。
2. 为 unlensed 单事件生成 `unlensed_trigger_time_features.csv`。
3. 返回与当前 catalog 顺序一致的事件级 `trigger_time_obs` 表。
4. pair-level 特征统一通过 `trigger_time_obs` 计算 `log1p_delta_time_obs`。

## 3. 已修改实验脚本

### 3.1 Gaussian predicted sky map overlap

```text
scripts/experiments/39_waveform_predicted_skymap_rerank.py
```

修改前：

```text
log1p(abs(geocent_time_i - geocent_time_j))
```

修改后：

```text
log1p(abs(trigger_time_obs_i - trigger_time_obs_j))
```

输出结果中的特征名也改为：

```text
log1p_delta_time_obs
```

### 3.2 Toy HEALPix SkyMapNet overlap

```text
scripts/experiments/41_toy_skymapnet_overlap_rerank.py
```

修改为通过 `base.log1p_delta_time_obs(...)` 计算时间差，不再读取 `geocent_time` 作为 reranker 输入。

### 3.3 Sky predictor sweep

```text
scripts/experiments/40_skymap_predictor_sweep.py
```

该脚本复用 `39` 的 `load_split` 和 `feature_matrix`，因此会自动使用新的 `trigger_time_obs` 时间特征，不需要单独修改。

## 4. 已生成的新数据文件

ET 数据：

```text
/root/autodl-tmp/gw_et_10000_matchstyle_20260527_091859/SIS_data_0222/SIS_trigger_time_features.csv
/root/autodl-tmp/gw_et_10000_matchstyle_20260527_091859/PM_data_0222/PM_trigger_time_features.csv
/root/autodl-tmp/gw_et_10000_matchstyle_20260527_091859/Unlensed_data_0222/unlensed_trigger_time_features.csv
```

LIGO 数据：

```text
/root/autodl-tmp/gw_ligo_10000_matchstyle_20260527_091859/SIS_data_0222/SIS_trigger_time_features.csv
/root/autodl-tmp/gw_ligo_10000_matchstyle_20260527_091859/PM_data_0222/PM_trigger_time_features.csv
/root/autodl-tmp/gw_ligo_10000_matchstyle_20260527_091859/Unlensed_data_0222/unlensed_trigger_time_features.csv
```

每个透镜文件包含：

```text
pair_id
geocent_time_true_1 / geocent_time_true_2
delta_time_true
lens_t_d
trigger_time_obs_1 / trigger_time_obs_2
trigger_time_sigma_1 / trigger_time_sigma_2
delta_time_obs
sigma_delta_time
log10_delta_time_obs
snr_1 / snr_2
```

unlensed 文件包含：

```text
event_id
geocent_time_true
trigger_time_obs
trigger_time_sigma
snr
```

## 5. 检查结果

以 ET noisy SIS 为例，已生成 10000 行 trigger-time 特征。检查结果显示：

```text
mean_abs(delta_time_obs - delta_time_true) = 0.033 s
```

这说明 `delta_time_obs` 接近真值但不完全等于真值，符合 SNR timing jitter 设定。

## 6. 验证命令

已通过：

```text
PYTHONPATH=. python3 -m py_compile matchgw/trigger_time.py scripts/experiments/39_waveform_predicted_skymap_rerank.py scripts/experiments/41_toy_skymapnet_overlap_rerank.py
PYTHONPATH=. OMP_NUM_THREADS=4 python3 -m pytest tests/test_matchgw.py -q
```

测试结果：

```text
5 passed in 1.67s
```

## 7. 当前结论

从现在开始，当前 sky_map_overlap 相关实验中的 `delta_time` 已改为 realistic 的 `trigger_time_obs` 差值，不再直接使用真实 `geocent_time` 或 `lens.csv` 的 `t_d` 作为模型输入。`geocent_time_true` 和 `delta_time_true` 仅保存在 trigger feature CSV 中，用于检查和评估。
