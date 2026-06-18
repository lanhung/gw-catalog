# ET 三臂数据生成与训练说明

本文档说明如何生成新的 ET three-arm 数据，并让现有 match-first 训练流程读取三通道 waveform。

## 当前状态

旧 ET 数据是 single-channel approximation：

- `InterferometerList(['ET'])[0]`
- strain shape: `(n_events, N)`
- SNR shape: `(n_events,)`

新 ET3 脚本改为：

- `InterferometerList(['ET'])[:3]`
- strain shape: `(n_events, 3, N)`
- single-channel SNR shape: `(n_events, 3)`
- network SNR shape: `(n_events,)`

旧数据不要覆盖，作为 `ET_single_channel` baseline 保留。

## 生成脚本

三臂脚本位于：

- `data_generation/generated_10000_scripts/SIS_GW_events_ET3.py`
- `data_generation/generated_10000_scripts/PM_GW_events_ET3.py`
- `data_generation/generated_10000_scripts/unlensed_GW_events_ET3.py`

可用环境变量控制样本量：

```bash
export GW_OUTPUT_ROOT=/root/autodl-tmp/createdata/et3_smoke
export GW_N_SAMPLES=100
export GW_N_LENS=100
export GW_DETECTOR_NETWORK=ET
export GW_DETECTOR_CHANNELS=3

python data_generation/generated_10000_scripts/SIS_GW_events_ET3.py
python data_generation/generated_10000_scripts/PM_GW_events_ET3.py
python data_generation/generated_10000_scripts/unlensed_GW_events_ET3.py
```

正式 10000 版本：

```bash
export GW_OUTPUT_ROOT=/root/autodl-tmp/createdata/et3_10000
export GW_N_SAMPLES=10000
export GW_N_LENS=10000
export GW_DETECTOR_NETWORK=ET
export GW_DETECTOR_CHANNELS=3

python data_generation/generated_10000_scripts/SIS_GW_events_ET3.py
python data_generation/generated_10000_scripts/PM_GW_events_ET3.py
python data_generation/generated_10000_scripts/unlensed_GW_events_ET3.py
```

## 探测器网络模块化

探测器投影逻辑已经从具体 ET3 脚本中抽到：

- `data_generation/detector_network.py`

核心接口：

- `DetectorNetworkSpec.from_string("ET", max_channels=3)`
- `build_interferometers(bilby, spec)`
- `simulate_detector_network(...)`

因此生成脚本不再写死单个 ET 或 ET3。通过环境变量即可切换：

```bash
# ET 三臂
export GW_DETECTOR_NETWORK=ET
export GW_DETECTOR_CHANNELS=3

# 单通道 ET baseline
export GW_DETECTOR_NETWORK=ET
export GW_DETECTOR_CHANNELS=1

# LIGO H1/L1 两探测器
export GW_DETECTOR_NETWORK=H1,L1
export GW_DETECTOR_CHANNELS=2
```

输出 shape 会随探测器数量变化：

- `n_ifos=1`: `(n_events, 1, N)`
- `n_ifos=2`: `(n_events, 2, N)`
- `n_ifos=3`: `(n_events, 3, N)`

训练侧会自动从样本 shape 推断 `in_channels`，不需要手动改模型第一层。

## 整理为训练数据根目录

训练代码默认读取：

- `SIS_data_0222`
- `PM_data_0222`
- `Unlensed_data_0222`

生成完成后运行：

```bash
python scripts/prepare_et3_match_root.py \
  --generated-root /root/autodl-tmp/createdata/et3_10000 \
  --out-root /root/autodl-tmp/createdata/et3_match_root
```

默认创建 symlink；如果需要物理复制，加 `--copy`。

## 训练命令

```bash
python scripts/08_match_first_train.py \
  --data-root /root/autodl-tmp/createdata/et3_match_root \
  --model-type SIS \
  --data-mode noisy \
  --backbone inceptionattn \
  --preprocess bandpass \
  --lensed-limit 10000 \
  --unlensed-limit 10000 \
  --epochs 50 \
  --batch-size 128 \
  --out-dir runs/et3_sis_noisy_inceptionattn_bandpass
```

PM 只需把 `--model-type SIS` 改为 `--model-type PM`。

训练侧已经支持：

- 旧一维输入 `(N,)` -> `1` channel
- ET3 输入 `(3, N)` -> `3` channels
- `--use-hilbert` 时 `(3, N)` -> `6` channels
- `--preprocess multiband` 时 `(3, N)` -> `12` channels

## 验证项

生成后至少检查：

```bash
python - <<'PY'
import numpy as np
from pathlib import Path
root = Path('/root/autodl-tmp/createdata/et3_10000/SIS_GW_events_ET3')
for name in [
    'SIS_data_strain_1.npy',
    'SIS_h_strain_1.npy',
    'SIS_optimal_SNR_single_1.npy',
    'SIS_optimal_SNR_network_1.npy',
]:
    x = np.load(root / name, mmap_mode='r')
    print(name, x.shape, x.dtype)
PY
```

期望：

- `SIS_data_strain_1.npy`: `(10000, 3, 98304)`
- `SIS_h_strain_1.npy`: `(10000, 3, 98304)`
- `SIS_optimal_SNR_single_1.npy`: `(10000, 3)`
- `SIS_optimal_SNR_network_1.npy`: `(10000,)`
