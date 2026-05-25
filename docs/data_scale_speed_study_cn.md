# 不同数据规模下的训练加速研究方案

## 研究目标

在当前 match-first / InceptionTime 检索框架上，系统研究训练数据规模对训练耗时、检索效果和候选筛选效率的影响。核心问题不是单纯追求最高准确率，而是回答：在多少训练样本规模下，模型已经接近全量性能；继续扩大数据带来的收益是否值得额外训练成本。

## 实验变量

- 数据规模：用同一个 `scale` 同时限制 lensed pair 数量和 unlensed 数量，例如 `500/1000/2500/5000/10000`。
- 物理模型：`SIS` 与 `PM` 分开统计。
- 数据模式：`noisy` 与 `pure` 分开统计。
- 模型主体：默认使用当前最好表现的 `inceptiontime`。
- 训练轮数：默认 `20 epoch`，如要和最终结果对齐可改为 `50 epoch`。

## 记录指标

训练加速部分：

- `train_s`：纯训练耗时。
- `mean_epoch_s`：平均每轮耗时。
- `mean_pairs_per_s`：训练 pair 吞吐量。
- `total_s`：训练、验证调参、测试评估和保存的总耗时。
- `events_per_total_s`：单位总耗时处理的 catalog 事件数。

效果部分：

- `test_r@1 / test_r@5 / test_r@10`：检索召回。
- `test_f1`：最大权匹配后的成对识别 F1。
- `candidate_pair_recall`：Top-K 候选集合覆盖真实强透镜 pair 的比例。
- `candidate_edges`：候选边数量，反映后续人工/物理复核成本。

## 代码入口

主脚本：

```bash
python scripts/11_data_scale_speed_study.py \
  --data-root /root/autodl-tmp/qkzhang_gwaug_20260522_162031 \
  --out-root runs/data_scale_speed_study_$(date +%Y%m%d_%H%M%S) \
  --scales 500 1000 2500 5000 10000 \
  --model-types SIS PM \
  --data-modes noisy pure \
  --backbone inceptiontime \
  --epochs 20
```

如果要对齐当前 ep50 最好结果：

```bash
python scripts/11_data_scale_speed_study.py \
  --data-root /root/autodl-tmp/qkzhang_gwaug_20260522_162031 \
  --out-root runs/data_scale_speed_ep50_$(date +%Y%m%d_%H%M%S) \
  --scales 500 1000 2500 5000 10000 \
  --model-types SIS PM \
  --data-modes noisy pure \
  --backbone inceptiontime \
  --epochs 50
```

脚本会输出：

- `summary.csv`：完整实验表。
- `summary_compact.csv`：论文作图常用指标。
- `commands.txt`：所有实际执行命令，便于复现。
- 每个子实验目录下的 `summary.json / timing.csv / sizes.csv / history.csv / model.pt`。

## 论文分析角度

1. 数据规模-准确率曲线：观察 `test_r@10`、`test_f1`、`candidate_pair_recall` 随 scale 增长是否进入平台期。
2. 数据规模-训练时间曲线：观察 `train_s` 和 `mean_epoch_s` 是否近似线性增长，并比较 SIS/PM、noisy/pure 的差异。
3. 加速收益：如果小规模训练已经达到接近全量的 `candidate_pair_recall`，可以把它作为快速预训练或参数筛选阶段。
4. 性价比指标：用 `test_f1 / train_s`、`candidate_pair_recall / total_s` 或达到固定召回所需时间衡量不同规模的效率。
5. 二阶段策略：先用小规模数据快速确定 backbone、窗口长度、增强强度，再用较大规模做最终 ep50 训练。

## 当前实现改动

- `matchgw/pipeline.py` 增加了训练、验证、测试各阶段计时，并保存 `timing.csv` 和 `sizes.csv`。
- 每轮训练日志增加 `epoch_s`、`batches`、`batch_pairs`、`pairs_per_s`。
- 新增 `scripts/11_data_scale_speed_study.py`，用于自动跑不同 scale 并汇总速度和精度。
