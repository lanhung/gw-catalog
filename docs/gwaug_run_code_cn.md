# GW-Augmented 全量实验代码位置说明

本轮结果使用的新数据和训练代码都在 `/root/autodl-tmp/gw-catalog` 仓库中。

## 1. 数据生成代码

- `scripts/10_generate_gw_augmented_match_data.py`

作用：在 match 项目生成的 SIS/PM/unlensed 数据基础上，派生一个新的 GW-augmented match-style 数据集。它不会覆盖原始 `/root/autodl-tmp/qkzhang`，而是写入新的 `--out-root`。

本轮使用的数据目录：

```bash
/root/autodl-tmp/qkzhang_gwaug_20260522_162031
```

主要增强内容：

- magnification perturbation；
- compressed time-delay sample shift；
- Morse phase / Hilbert transform；
- colored nonstationary noise；
- low-frequency drift；
- occasional sine-Gaussian glitch；
- per-event metadata。

## 2. 训练入口

- `scripts/08_match_first_train.py`

作用：启动一次 match-first Siamese / InceptionTime 训练和评估。

本轮全量运行等价命令：

```bash
python scripts/08_match_first_train.py \
  --data-root /root/autodl-tmp/qkzhang_gwaug_20260522_162031 \
  --backbone inceptiontime \
  --model-type SIS \
  --data-mode noisy \
  --epochs 50 \
  --lensed-limit 10000 \
  --unlensed-limit 10000 \
  --batch-size 128 \
  --out-dir runs/gwaug_full_fastgrid_20260525_101529/SIS_noisy_inception_ep50_full
```

四组实验分别替换：

- `--model-type SIS --data-mode noisy`
- `--model-type SIS --data-mode pure`
- `--model-type PM --data-mode noisy`
- `--model-type PM --data-mode pure`

## 3. 核心模块

- `matchgw/config.py`：统一实验配置和数据路径。
- `matchgw/data.py`：读取 match-style npy 数据，构造训练 pair 和评估 catalog。
- `matchgw/models.py`：CNN baseline、InceptionTime encoder、NT-Xent loss。
- `matchgw/pipeline.py`：完整训练、验证、校准、测试和结果保存流程。
- `matchgw/matching.py`：相似度矩阵、Top-K 候选边、最大权匹配、Recall@K/F1 指标。
- `matchgw/rerank.py`：候选边特征、概率校准、Tier1/Tier2/Tier3 和 follow-up reduction 指标。

## 4. 本轮结果位置

```bash
runs/gwaug_full_fastgrid_20260525_101529/summary_compact.csv
```

结果摘要：

| 模型 | 数据 | R@5 | R@10 | F1 | candidate recall |
|---|---:|---:|---:|---:|---:|
| SIS | noisy | 0.9830 | 0.9877 | 0.8315 | 0.9887 |
| SIS | pure | 0.9857 | 0.9883 | 0.8511 | 0.9907 |
| PM | noisy | 0.9813 | 0.9883 | 0.8033 | 0.9900 |
| PM | pure | 0.9850 | 0.9913 | 0.8233 | 0.9940 |

