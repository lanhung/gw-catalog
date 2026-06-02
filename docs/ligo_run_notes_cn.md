# LIGO 数据运行记录与下一步方案

生成时间：2026-06-01

## 1. 数据位置

LIGO 10000 原始生成数据已经存在：

```text
/root/autodl-tmp/createdata/generated_10000_20260527_091859/SIS_GW_events_LIGO_10000
/root/autodl-tmp/createdata/generated_10000_20260527_091859/PM_GW_events_LIGO_10000
/root/autodl-tmp/createdata/generated_10000_20260527_091859/unlensed_GW_events_LIGO_10000
```

为了复用当前 match-style 训练代码，创建了一个软链接数据根目录：

```text
/root/autodl-tmp/gw_ligo_10000_matchstyle_20260527_091859
```

目录映射：

```text
SIS_data_0222      -> SIS_GW_events_LIGO_10000
PM_data_0222       -> PM_GW_events_LIGO_10000
Unlensed_data_0222 -> unlensed_GW_events_LIGO_10000
```

## 2. 和 ET 数据的关键差异

ET 数据形状：

```text
(N, 98304)
```

LIGO 数据形状：

```text
(N, 2, 98304)
```

也就是说 LIGO 是双探测器通道。为此已经修改代码，使模型自动识别输入通道数：

- ET：1 channel
- LIGO：2 channels
- LIGO multiband：2 detectors * 4 bands = 8 channels

修改文件：

```text
matchgw/data.py
matchgw/pipeline.py
```

修改内容：

1. `to_channels` 支持 detector x time 输入。
2. `spectral_preprocess` 对多探测器逐通道做 bandpass/whiten。
3. `multiband_preprocess` 对多探测器展开为 detector * band 通道。
4. `build_model` 自动根据 `.npy` 形状设置 `in_channels`。

验证：

```text
python3 -m pytest tests/test_matchgw.py -q
5 passed
```

## 3. Smoke 测试

先跑了 SIS noisy 小样本 smoke：

```bash
env OMP_NUM_THREADS=4 PYTHONPATH=. python3 scripts/08_match_first_train.py \
  --data-root /root/autodl-tmp/gw_ligo_10000_matchstyle_20260527_091859 \
  --model-type SIS \
  --data-mode noisy \
  --out-dir runs/ligo_smoke_sis_noisy_20260601 \
  --backbone inceptiontime \
  --lensed-limit 100 \
  --unlensed-limit 100 \
  --epochs 1 \
  --batch-size 32 \
  --eval-batch-size 128 \
  --target-len 8192 \
  --stride 2 \
  --preprocess bandpass \
  --bandpass-low 40 \
  --bandpass-high 580 \
  --num-workers 0
```

结果：训练、评估、summary 保存均正常。

## 4. 首版 full baseline

启动了 LIGO noisy full baseline：

- SIS noisy
- PM noisy
- n=10000
- 50 epoch
- InceptionTime
- bandpass 40-580
- batch size 128
- AMP bf16

运行目录：

```text
runs/ligo_inceptiontime_bandpass_full_ep50_20260601_095620
```

日志：

```text
logs/ligo_inceptiontime_bandpass_full_ep50_20260601_095620/ligo_inceptiontime_bandpass_full_ep50.log
```

## 5. 首版结果

| family | mode | model | R@1 | R@5 | R@10 | MRR | median rank | mean epoch s | total s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| SIS | noisy | InceptionTime + bandpass | 0.0103 | 0.0243 | 0.0400 | 0.0220 | 1180 | 6.23 | 785.86 |
| PM | noisy | InceptionTime + bandpass | 0.0067 | 0.0170 | 0.0283 | 0.0152 | 1445 | 6.24 | 832.25 |

## 6. 结论

1. LIGO 数据现在已经可以被当前项目训练代码读取和运行。
2. 双通道输入兼容已经完成，不需要复制大文件，只使用软链接目录。
3. 直接套 ET 上的 `InceptionTime + bandpass 40-580` 效果很差，说明 LIGO 数据分布与 ET 明显不同。
4. 首版结果只能作为“跑通基线”，不能作为最终 LIGO 结果。

## 7. 下一步建议

### 7.1 优先诊断数据和频带

LIGO 首版 R@1 很低，优先检查：

- 两个 detector 通道是否需要先合成为 network strain。
- 当前 `bandpass 40-580` 是否适合 LIGO。
- LIGO noisy 数据的 SNR 分布是否低于 ET。
- LIGO `data_strain` 和 `h_strain` 差异是否过大。

### 7.2 尝试 LIGO 专用预处理

建议下一组先扫：

```text
none
bandpass 20-512
bandpass 30-512
bandpass 40-512
whiten
whiten_bandpass
network-combined strain
```

### 7.3 先跑 pure 对照

如果 LIGO pure 也很低，说明主要是双通道/波形处理问题。
如果 pure 高、noisy 低，说明主要是噪声建模和预处理问题。

推荐下一步命令示例：

```bash
env OMP_NUM_THREADS=4 PYTHONPATH=. python3 scripts/08_match_first_train.py \
  --data-root /root/autodl-tmp/gw_ligo_10000_matchstyle_20260527_091859 \
  --model-type SIS \
  --data-mode pure \
  --out-dir runs/ligo_sis_pure_inceptiontime_bandpass_n10000_ep50 \
  --backbone inceptiontime \
  --lensed-limit 10000 \
  --unlensed-limit 10000 \
  --epochs 50 \
  --batch-size 128 \
  --eval-batch-size 512 \
  --target-len 8192 \
  --stride 2 \
  --preprocess bandpass \
  --bandpass-low 40 \
  --bandpass-high 580 \
  --amp \
  --pin-memory \
  --num-workers 4
```

## 8. 当前建议

下一步不要直接大规模扫模型，应该先做 LIGO 数据诊断和预处理扫。当前最值得先跑的是：

1. SIS pure / PM pure full baseline。
2. noisy 小样本预处理 sweep。
3. 比较双通道输入和 network-combined 单通道输入。

## 9. LIGO pure 全量对照结果

在 noisy 首版结果很低后，补跑了 LIGO pure 全量对照：

- SIS pure
- PM pure
- n=10000
- 50 epoch
- InceptionTime
- bandpass 40-580

运行目录：

```text
runs/ligo_pure_inceptiontime_bandpass_full_ep50_20260601_103901
```

日志：

```text
logs/ligo_pure_inceptiontime_bandpass_full_ep50_20260601_103901/ligo_pure_inceptiontime_bandpass_full_ep50.log
```

结果：

| family | mode | model | R@1 | R@5 | R@10 | MRR | median rank | mean epoch s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| SIS | pure | InceptionTime + bandpass | 0.9543 | 0.9833 | 0.9887 | 0.9675 | 1.0 | 6.24 |
| PM | pure | InceptionTime + bandpass | 0.9547 | 0.9843 | 0.9883 | 0.9679 | 1.0 | 6.26 |

## 10. pure/noisy 对比结论

| family | pure R@1 | noisy R@1 | 差距 |
|---|---:|---:|---:|
| SIS | 0.9543 | 0.0103 | -0.9440 |
| PM | 0.9547 | 0.0067 | -0.9480 |

结论非常明确：LIGO 双通道数据和训练流程本身是可用的，因为 pure 可以达到约 0.955 R@1；问题主要出在 noisy 数据处理上。下一步应重点优化 LIGO noisy 的噪声抑制、whitening、频带选择、SNR筛选或 noisy-to-pure 辅助训练，而不是优先换模型。

## 11. LIGO noisy 加 delta_time + sky_sep 辅助参数

在 LIGO noisy InceptionTime + bandpass top-50 候选上加入 `delta_time + sky_sep` reranker。结果：SIS realistic R@1 从 0.0107 提升到 0.1043，PM realistic R@1 从 0.0067 提升到 0.0777。

但 waveform top-50 召回上限很低：SIS R@50=0.1077，PM R@50=0.0780。因此当前瓶颈是第一阶段 noisy waveform 召回，而不是辅助参数 reranker。完整文档见 `docs/ligo_noisy_time_sky_aux_results_cn.md`。

