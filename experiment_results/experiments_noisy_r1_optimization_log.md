# Noisy R@1 optimization log

Goal: improve noisy waveform-only retrieval toward R@1=0.7 without auxiliary physical parameters.

Planned directions:
1. Score ensemble of existing encoders.
2. Hard-negative fine-tuning.
3. Pair-level reranker for Top-K candidates.
4. Multi-band waveform channels.


## 2026-05-28 Score ensemble of existing full models

Modification: added `scripts/experiments/15_score_ensemble_existing.py`. It loads existing full-run models and searches validation-set weights for score-level fusion. No retraining and no auxiliary physical parameters.

Models fused:
- InceptionTime + bandpass
- inceptionattn + bandpass + lr=5e-4
- gatedtcn + bandpass

Results on test set:

| Family | Weights | R@1 | R@10 | Pair F1 | Note |
|---|---|---:|---:|---:|---|
| SIS | InceptionTime 0.50, inceptionattn 0.35, gatedtcn 0.15 | 0.4597 | 0.7017 | 0.3968 | Best R@1 so far, +0.0497 over best single SIS model |
| PM | InceptionTime 0.35, inceptionattn 0.30, gatedtcn 0.35 | 0.3593 | 0.6030 | 0.3064 | Best R@1 so far, +0.0553 over best single PM model |

Conclusion: model scores are complementary. Ensemble improves noisy R@1 substantially, but remains below the 0.7 target.

Run root: /root/autodl-tmp/gw-catalog/runs/et10000_score_ensemble_existing

## 2026-05-28 Hard-negative fine-tuning attempt

Modification: enabled existing hard-negative fine-tuning in `scripts/08_match_first_train.py` via `--enable-hard-neg --hard-neg-epochs 4 --hard-neg-min-score 0.65` on `InceptionTime + bandpass`.

SIS full result:

| Family | Model | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | Result |
|---|---|---:|---:|---:|---:|---:|---|
| SIS | InceptionTime + bandpass + hard-negative | 0.1157 | 0.2473 | 0.0944 | 0.2740 | 0.1653 | Failed badly |

Conclusion: current hard-negative objective/configuration collapses retrieval quality. PM run was stopped after SIS failure to save compute. This route should not be used without redesigning the loss/sampling.

Run root: /root/autodl-tmp/gw-catalog/runs/et10000_inceptiontime_hardneg_full_ep50_20260528_170003

## 2026-05-28 Pair-level reranker on ensemble candidates

Modification: added `scripts/experiments/16_pair_reranker_existing.py`. It trains a second-stage HistGradientBoosting classifier on validation Top-50 candidate pairs using per-model scores/ranks/margins from InceptionTime, inceptionattn, gatedtcn, and ensemble score. No auxiliary physical parameters.

Results:

| Family | Val AUC | R@1 | R@5 | R@10 | R@50 | Median true rank | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| SIS | 0.9803 | 0.4610 | 0.6287 | 0.6993 | 0.8157 | 2 | Essentially tied with ensemble |
| PM | 0.9657 | 0.3560 | 0.5390 | 0.6057 | 0.7513 | 4 | Slightly below ensemble |

Conclusion: the candidate-level classifier has high AUC but does not materially improve R@1 beyond weighted score ensemble. The main bottleneck remains waveform representation / candidate recall, not only reranking.

Run root: /root/autodl-tmp/gw-catalog/runs/et10000_pair_reranker_existing

## 2026-05-28 多频带波形输入实验

### 修改内容
- 在 `matchgw/data.py` 中新增 `multiband` 预处理：同一条波形被拆成 4 个频带通道 `(40,160)`, `(160,320)`, `(320,580)`, `(40,580)`，每个通道独立 z-score 和峰值方向归一。
- 在 `matchgw/pipeline.py` 中让 `preprocess=multiband` 自动使用 `in_channels=4`。
- 在 `scripts/08_match_first_train.py` 中开放 `--preprocess multiband` 参数。
- 验证：`python3 -m pytest tests/test_matchgw.py -q` 通过，4 通道模型前向通过。

### 目的
不使用辅助参数，只从波形中保留多频段信息，尝试提升 noisy R@1；先做 n=2500/15ep 小规模筛选。

### 首次运行失败与修复
- 失败现象：训练阶段已经使用 4 通道 multiband，但验证/测试阶段 `EvaluationSet` 仍输出 1 通道，评估时报 `expected input ... to have 4 channels, but got 1 channels`。
- 修复内容：`EvaluationSet.__getitem__` 增加 `preprocess=multiband` 分支，验证/测试也执行相同 4 频带分解、峰值符号归一和逐通道 z-score。
- 验证：`python3 -m pytest tests/test_matchgw.py -q` 通过，`EvaluationSet` 样本形状为 `(4, 4096)`。

### multiband 小规模筛选结果 n=2500/15ep

| family | backbone | noisy R@1 | R@10 | pair F1 | candidate recall | catalog F1 | 结论 |
|---|---|---:|---:|---:|---:|---:|---|
| SIS | inceptionattn | 0.4533 | 0.7120 | 0.3303 | 0.7413 | 0.4924 | 小规模最优，进入全量 50ep |
| SIS | inceptiontime | 0.4213 | 0.6907 | 0.2652 | 0.7387 | 0.4618 | 有提升，但弱于 inceptionattn |
| PM | inceptionattn | 0.2840 | 0.5773 | 0.2120 | 0.6160 | 0.3183 | 不优于当前 full ensemble |
| PM | inceptiontime | 0.2240 | 0.5053 | 0.1494 | 0.5573 | 0.2775 | 不优于当前 full ensemble |

### 下一步
- 全量运行 `SIS noisy inceptionattn + multiband, n=10000, 50ep`。
- 继续尝试 waveform-only 二阶段重排：不加物理辅助参数，只用候选对的波形相似度、频带相关性、排名和 embedding 分数特征。

### multiband 全量结果 n=10000/50ep

| family | backbone | noisy R@1 | R@10 | pair F1 | candidate recall | catalog F1 | total_s | 结论 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| SIS | inceptionattn + multiband | 0.4157 | 0.6533 | 0.2806 | 0.6827 | 0.4677 | 700.2 | 低于现有 full ensemble 0.4597，暂不作为主结果 |

### 观察
- multiband 小规模有效，但全量 50ep 后 R@1 没有继续提升，可能是高频/分频噪声被模型过拟合。
- 当前最优仍是 score ensemble：SIS R@1=0.4597，PM R@1=0.3593。
- 下一步继续验证 waveform-only reranker，看能否利用候选对的频带相关性提升 top-1 排序。

## 2026-05-28 waveform-only 二阶段重排实验

### 修改内容
- 新增 `scripts/experiments/17_waveform_reranker_existing.py`。
- 输入：沿用三个 full 模型的 embedding score/排名，同时对候选事件对提取 waveform-only 特征：4 频带相关性、绝对相关性、MSE、小平移相关性、双向 score 一致性。
- 不使用质量、红移、时间延迟、SNR 等物理辅助参数。
- 目标：把 top-50 候选内的真配对重排到第 1，从而提升 noisy R@1。

### waveform-only 二阶段重排结果

| family | 方法 | noisy R@1 | R@5 | R@10 | R@50 | val_auc | 结论 |
|---|---|---:|---:|---:|---:|---:|---|
| SIS | score ensemble + waveform reranker | 0.4627 | 0.6337 | 0.7030 | 0.8197 | 0.9924 | 略高于 score ensemble 0.4597，但提升很小 |
| PM | score ensemble + waveform reranker | 0.3683 | 0.5403 | 0.6120 | 0.7530 | 0.9842 | 略高于 score ensemble 0.3593，但提升很小 |

### 观察
- R@50 上限较高：SIS 0.8197、PM 0.7530，说明候选集中经常包含真配对。
- R@1 仍低，核心瓶颈是 top candidates 内部排序，不是候选召回本身。
- 仅靠浅层 waveform 相关性和 score/rank 特征，无法接近 0.7；需要更强的重排训练或更强 pair/cross-encoder。

### 下一步
- 试 `train split` 上的大样本 waveform reranker，只先跑 SIS。相比只用 val 训练，训练正例数量更多，可能改善泛化排序。

### train-split 大样本 waveform reranker 结果

| family | 训练 split | train topK | test topK | fit examples | noisy R@1 | R@5 | R@10 | R@50 | 结论 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| SIS | train | 30 | 50 | 713997 | 0.4333 | 0.6037 | 0.6680 | 0.7937 | 低于 val-only reranker 0.4627，负结果 |

### 观察
- 更多训练样本没有提升 test R@1，反而下降，说明浅层 waveform 特征的分布泛化不足。
- 继续尝试更强的 waveform-only pair cross-encoder，直接学习候选波形对的二分类重排分数。

### waveform pair cross-encoder 结果

| family | 方法 | train pairs | positive | negative | noisy R@1 | R@5 | R@10 | R@50 | 结论 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| SIS | waveform pair cross-encoder 单独排序 | 140000 | 14000 | 126000 | 0.0370 | 0.1200 | 0.2033 | 0.6127 | 明显失败，不能直接替代 embedding 排名 |

### 观察
- loss 下降但 test 排名很差，说明简单 pair CNN 对 hard negatives 的泛化不足。
- 直接二分类 pair score 会破坏原 embedding 的候选排序，需要尝试与 ensemble score 混合，而不是单独使用。

### cross-encoder 与 ensemble 混合结果

| family | 方法 | beta | noisy R@1 | R@5 | R@10 | R@50 | 结论 |
|---|---|---:|---:|---:|---:|---:|---|
| SIS | ensemble_z + beta * cross_encoder_z | 0.05 | 0.4657 | 0.6373 | 0.7047 | 0.8190 | 当前最高，但只比 ensemble 0.4597 小幅提升 |

### 阶段结论
- 当前 noisy R@1 最好结果是 SIS 0.4657，未达到 0.7。
- 已尝试并记录：多模型 score ensemble、pair-level reranker、multiband 输入、train-split 大样本 reranker、waveform pair cross-encoder、cross-encoder score blend。
- 不加辅助参数时，主要瓶颈是 noisy 波形下真配对和 hard negative 的 waveform 相似性过强；top50 上限足够高，但 top1 排序仍不稳定。
