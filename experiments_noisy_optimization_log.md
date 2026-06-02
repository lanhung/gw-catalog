# Noisy Optimization Log


## 2026-05-27T16:59:08 pure_aux noisy optimization

目标：在 ET 10000 新数据上优化 noisy 检索，优先把 R@1 / Catalog F1 推到 0.7 以上。

修改内容：
- `matchgw/config.py` 增加 `use_pure_aux`。
- `matchgw/data.py` 在 noisy 训练时可额外加载 clean `h_strain`，构造 noisy-clean、clean-clean 辅助正样本；测试仍然只使用 noisy `data_strain`，不读取 clean waveform。
- `scripts/08_match_first_train.py` 增加 `--use-pure-aux` 参数。

先跑配置：
- SIS noisy: InceptionTime, win16k, Hilbert, 50ep, pure_aux。
- PM noisy: InceptionTime, win16k, no Hilbert, 50ep, pure_aux。


### pure_aux interim result

| run | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | conclusion |
|---|---:|---:|---:|---:|---:|---|
| SIS_noisy_inception_win16k_hilbert_pureaux_ep50 | 0.0573 | 0.1657 | 0.0356 | 0.1893 | 0.0544 | failed, auxiliary clean positives dominated training |

处理：停止 PM pure_aux，转向 noisy-only hard-negative / rerank 优化。


### parameter-assisted catalog retrieval result

Run dir: `runs/et10000_parameter_assisted_20260527_174103`

说明：该结果使用 `source_samples/lensed_source_samples` 中的源本征参数作为参数辅助/上限实验，排除 `geocent_time` 和 `luminosity_distance`；评估仍在 noisy ET 10000 的 test split 上进行。它不是 waveform-only 结果。

| family | R@1 | R@10 | Pair F1 | Catalog F1 | Catalog Precision | Catalog Recall |
|---|---:|---:|---:|---:|---:|---:|
| SIS | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| PM | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

结论：参数辅助 catalog-level 检索可以达到 0.7 以上；waveform-only noisy 当前最好仍是 SIS R@1=0.3510、PM R@1=0.2663，需要继续研究更真实的参数估计噪声/融合策略。



## 2026-05-28T09:23:54 noisy-from-pure embedding distillation

目标：提升 ET 10000 noisy waveform-only 检索。

修改内容：
- 新增 `scripts/13_distill_noisy_from_pure.py`。
- 使用已训练 pure InceptionTime 模型作为 frozen teacher。
- student 只输入 noisy waveform，训练目标是接近同一事件 pure waveform 的 teacher embedding。
- 评估阶段仍只使用 noisy waveform，不使用参数表，也不输入 clean waveform。

运行配置：SIS/PM noisy, InceptionTime, target_len=8192, stride=2, 20ep。

### distill noisy-from-pure ep20 results

| run | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | total_s |
|---|---:|---:|---:|---:|---:|---:|
| PM_noisy_distill_from_pure_ep20 | 0.2000 | 0.4267 | 0.1309 | 0.4647 | 0.2229 | 403.9 |
| SIS_noisy_distill_from_pure_ep20 | 0.2623 | 0.5120 | 0.1693 | 0.5507 | 0.3119 | 414.0 |


## 2026-05-28T09:38:37 hybrid noisy contrastive + pure-teacher distillation

目标：修正纯蒸馏低于 baseline 的问题。

修改内容：
- 新增 `scripts/14_hybrid_noisy_contrastive_distill.py`。
- loss = noisy NT-Xent contrastive + 0.2 * pure-teacher embedding distillation。
- 训练和评估输入仍为 noisy waveform；teacher 只在训练期提供弱约束。

运行配置：SIS/PM noisy, InceptionTime, target_len=8192, stride=2, 20ep, distill_weight=0.2。

### hybrid noisy contrastive + pure-teacher w0.2 ep20 results

| run | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | total_s |
|---|---:|---:|---:|---:|---:|---:|
| PM_noisy_hybrid_distill_w02_ep20 | 0.2773 | 0.5190 | 0.1818 | 0.5560 | 0.3072 | 436.0 |
| SIS_noisy_hybrid_distill_w02_ep20 | 0.3430 | 0.6107 | 0.2307 | 0.6440 | 0.3700 | 439.6 |


## 2026-05-28T10:04:29 waveform-only spectral preprocessing sweep

约束：不使用任何辅助参数，只使用 noisy waveform。

修改内容：
- `matchgw/config.py` 增加 `preprocess/bandpass_low/bandpass_high/whiten_kernel`。
- `matchgw/data.py` 增加 `spectral_preprocess()`，支持 `bandpass`、`whiten`、`whiten_bandpass`。
- `scripts/08_match_first_train.py` 增加对应 CLI 参数。

筛选配置：SIS/PM noisy, InceptionTime, n=2500+2500, 10ep, target_len=8192, stride=2。

### waveform-only spectral preprocessing n2500 ep10 results

| run | family | preprocess | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | total_s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| PM_noisy_bandpass_n2500_ep10 | PM | bandpass | 0.1947 | 0.4493 | 0.1521 | 0.4907 | 0.2481 | 46.5 |
| PM_noisy_whiten_bandpass_n2500_ep10 | PM | whiten_bandpass | 0.1667 | 0.3947 | 0.1187 | 0.4347 | 0.1865 | 45.7 |
| PM_noisy_whiten_n2500_ep10 | PM | whiten | 0.1253 | 0.3813 | 0.0854 | 0.4187 | 0.1099 | 46.6 |
| SIS_noisy_bandpass_n2500_ep10 | SIS | bandpass | 0.3547 | 0.6440 | 0.2431 | 0.6907 | 0.3596 | 45.2 |
| SIS_noisy_whiten_bandpass_n2500_ep10 | SIS | whiten_bandpass | 0.2947 | 0.5800 | 0.2104 | 0.6133 | 0.3348 | 46.1 |
| SIS_noisy_whiten_n2500_ep10 | SIS | whiten | 0.2000 | 0.5347 | 0.1357 | 0.5787 | 0.1619 | 46.0 |


## 2026-05-28T10:10:13 waveform-only bandpass full run

筛选结论：n2500/10ep 中 `bandpass` 最好，`whiten` 和 `whiten_bandpass` 退化。

全量配置：SIS/PM noisy, InceptionTime, n=10000+10000, 50ep, target_len=8192, stride=2, preprocess=bandpass, bins=[40,580]。

### waveform-only bandpass n10000 ep50 results

| run | family | preprocess | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | total_s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| PM_noisy_bandpass_n10000_ep50 | PM | bandpass | 0.3040 | 0.5407 | 0.1972 | 0.5753 | 0.3216 | 698.5 |
| SIS_noisy_bandpass_n10000_ep50 | SIS | bandpass | 0.4070 | 0.6577 | 0.2820 | 0.6873 | 0.4425 | 679.6 |


## 2026-05-28T10:55:19 waveform-only model sweep

约束：不使用任何辅助参数，只使用 noisy waveform。

修改内容：
- 新增 `dilatedresnet` backbone：多尺度扩张卷积残差网络，扩大长窗口感受野。
- 对比 `dilatedresnet + bandpass` 和 `InceptionTime + bandpass + Hilbert`。

筛选配置：SIS/PM noisy, n=2500+2500, 10ep。

### waveform-only model sweep n2500 ep10 results

| run | family | backbone | Hilbert | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | total_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| PM_noisy_dilatedresnet_bandpass_n2500_ep10 | PM | dilatedresnet | False | 0.1133 | 0.3493 | 0.0896 | 0.3760 | 0.1343 | 48.0 |
| PM_noisy_inception_bandpass_hilbert_n2500_ep10 | PM | inceptiontime | True | 0.1867 | 0.4320 | 0.1289 | 0.4720 | 0.2219 | 49.8 |
| SIS_noisy_dilatedresnet_bandpass_n2500_ep10 | SIS | dilatedresnet | False | 0.1920 | 0.5040 | 0.1387 | 0.5467 | 0.1584 | 46.8 |
| SIS_noisy_inception_bandpass_hilbert_n2500_ep10 | SIS | inceptiontime | True | 0.3787 | 0.6213 | 0.2309 | 0.6613 | 0.4191 | 48.5 |


## 2026-05-28T10:59:48 waveform-only bandpass + Hilbert full SIS run

筛选结论：`dilatedresnet` 显著弱于 InceptionTime；`InceptionTime + bandpass + Hilbert` 在 SIS n2500/10ep 上优于普通 bandpass，但 PM 上较弱。

全量配置：SIS noisy, InceptionTime, n=10000+10000, 50ep, preprocess=bandpass, Hilbert two-channel。

### waveform-only bandpass + Hilbert SIS n10000 ep50 result

| run | Hilbert | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | total_s |
|---|---:|---:|---:|---:|---:|---:|---:|
| SIS_noisy_inception_bandpass_hilbert_n10000_ep50 | True | 0.3960 | 0.6567 | 0.2624 | 0.6860 | 0.4353 | 687.7 |


## 2026-05-28T13:15:40 waveform-only more model sweep

约束：不使用任何辅助参数，只使用 noisy waveform。

新增模型：
- `inceptionattn`: InceptionTime backbone + attention/avg/max pooling readout。
- `convnext1d`: ConvNeXt-style depthwise large-kernel 1D encoder。

筛选配置：SIS/PM noisy, bandpass, n=2500+2500, 10ep。

### waveform-only more model sweep n2500 ep10 results

| run | family | backbone | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | total_s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| PM_noisy_convnext1d_bandpass_n2500_ep10 | PM | convnext1d | 0.0080 | 0.0413 | 0.0067 | 0.0480 | 0.0106 | 43.9 |
| PM_noisy_inceptionattn_bandpass_n2500_ep10 | PM | inceptionattn | 0.2760 | 0.5440 | 0.1856 | 0.5787 | 0.2911 | 46.9 |
| SIS_noisy_convnext1d_bandpass_n2500_ep10 | SIS | convnext1d | 0.0107 | 0.0507 | 0.0107 | 0.0560 | 0.0048 | 48.5 |
| SIS_noisy_inceptionattn_bandpass_n2500_ep10 | SIS | inceptionattn | 0.4240 | 0.7227 | 0.2657 | 0.7627 | 0.4223 | 46.2 |

## 2026-05-28 More waveform-only backbone trials: inception attention and ConvNeXt1D

Goal: try more models without auxiliary physical parameters, continuing to use ET10000 noisy waveform-only data and bandpass preprocessing.

Small screening run, n=2500, 10 epochs:

| Model | Type | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | Conclusion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| inceptionattn + bandpass | SIS noisy | 0.4240 | 0.7227 | 0.2657 | 0.7627 | 0.4223 | Promising; scale to full run |
| convnext1d + bandpass | SIS noisy | 0.0107 | 0.0507 | 0.0107 | 0.0560 | 0.0048 | Failed |
| inceptionattn + bandpass | PM noisy | 0.2760 | 0.5440 | 0.1856 | 0.5787 | 0.2911 | Promising enough for full run |
| convnext1d + bandpass | PM noisy | 0.0080 | 0.0413 | 0.0067 | 0.0480 | 0.0106 | Failed |

Full run, n=10000, 50 epochs:

| Model | Type | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | Total s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| inceptionattn + bandpass | SIS noisy | 0.3943 | 0.6517 | 0.2814 | 0.6800 | 0.4482 | 692.5 |
| inceptionattn + bandpass | PM noisy | 0.2910 | 0.5243 | 0.1948 | 0.5533 | 0.3344 | 690.5 |

Comparison with previous best waveform-only InceptionTime + bandpass 50ep:

| Type | Previous R@1 | New R@1 | Previous Catalog F1 | New Catalog F1 | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| SIS noisy | 0.4070 | 0.3943 | 0.4425 | 0.4482 | Top-1 retrieval decreased slightly; catalog-level F1 improved slightly |
| PM noisy | 0.3040 | 0.2910 | 0.3216 | 0.3344 | Top-1 retrieval decreased slightly; catalog-level F1 improved clearly |

Current conclusion: keep InceptionTime + bandpass as the best pair-level retrieval backbone, and keep inceptionattn + bandpass as the better catalog-level candidate. ConvNeXt1D is not useful under the current training setup.

Run root: /root/autodl-tmp/gw-catalog/runs/et10000_inceptionattn_bandpass_full_ep50_20260528_132036
Log dir: /root/autodl-tmp/gw-catalog/logs/et10000_inceptionattn_bandpass_full_ep50_20260528_132036

## 2026-05-28 Extra waveform-only backbone sweep

Goal: try additional waveform-only models on ET10000 noisy bandpass data. Added `seresnet`, `cbamresnet`, `gatedtcn`, `patchtst`, `rocket`, and `timesnetlite`.

Small screening run, n=2500, 10 epochs:

| Run | Family | Backbone | N | Ep | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | Total s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `PM_noisy_cbamresnet_bandpass_n2500_ep10` | PM | cbamresnet | 2500 | 10 | 0.0720 | 0.2787 | 0.0491 | 0.3067 | 0.0424 | 47.5 |
| `PM_noisy_gatedtcn_bandpass_n2500_ep10` | PM | gatedtcn | 2500 | 10 | 0.2747 | 0.5227 | 0.2085 | 0.5600 | 0.2773 | 43.2 |
| `PM_noisy_patchtst_bandpass_n2500_ep10` | PM | patchtst | 2500 | 10 | 0.0773 | 0.2680 | 0.0514 | 0.2987 | 0.0663 | 40.2 |
| `PM_noisy_rocket_bandpass_n2500_ep10` | PM | rocket | 2500 | 10 | 0.0800 | 0.2827 | 0.0459 | 0.3253 | 0.0625 | 34.4 |
| `PM_noisy_seresnet_bandpass_n2500_ep10` | PM | seresnet | 2500 | 10 | 0.0613 | 0.2053 | 0.0414 | 0.2293 | 0.0530 | 47.8 |
| `PM_noisy_timesnetlite_bandpass_n2500_ep10` | PM | timesnetlite | 2500 | 10 | 0.2307 | 0.5040 | 0.1788 | 0.5467 | 0.2717 | 35.2 |
| `SIS_noisy_cbamresnet_bandpass_n2500_ep10` | SIS | cbamresnet | 2500 | 10 | 0.1560 | 0.4587 | 0.1153 | 0.4907 | 0.1285 | 51.9 |
| `SIS_noisy_gatedtcn_bandpass_n2500_ep10` | SIS | gatedtcn | 2500 | 10 | 0.4173 | 0.7107 | 0.3533 | 0.7387 | 0.4621 | 43.7 |
| `SIS_noisy_patchtst_bandpass_n2500_ep10` | SIS | patchtst | 2500 | 10 | 0.1387 | 0.4173 | 0.0918 | 0.4667 | 0.1236 | 42.0 |
| `SIS_noisy_rocket_bandpass_n2500_ep10` | SIS | rocket | 2500 | 10 | 0.1533 | 0.4213 | 0.0889 | 0.4773 | 0.1789 | 34.3 |
| `SIS_noisy_seresnet_bandpass_n2500_ep10` | SIS | seresnet | 2500 | 10 | 0.1133 | 0.3720 | 0.0814 | 0.4107 | 0.1096 | 47.6 |
| `SIS_noisy_timesnetlite_bandpass_n2500_ep10` | SIS | timesnetlite | 2500 | 10 | 0.3813 | 0.6827 | 0.3174 | 0.7173 | 0.4135 | 34.7 |

Full follow-up run for the best screening model, n=10000, 50 epochs:

| Run | Family | Backbone | N | Ep | R@1 | R@10 | Pair F1 | Candidate Recall | Catalog F1 | Total s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `PM_noisy_gatedtcn_bandpass_n10000_ep50` | PM | gatedtcn | 10000 | 50 | 0.2650 | 0.5207 | 0.1844 | 0.5547 | 0.2950 | 685.6 |
| `SIS_noisy_gatedtcn_bandpass_n10000_ep50` | SIS | gatedtcn | 10000 | 50 | 0.3277 | 0.6020 | 0.2945 | 0.6360 | 0.3719 | 668.0 |

Conclusion: `gatedtcn` was strongest in the small sweep, especially on SIS Pair F1, but did not beat `InceptionTime + bandpass` or `inceptionattn + bandpass` after scaling to n=10000, 50 epochs. Keep it as a useful ablation rather than the main model.
Run root: /root/autodl-tmp/gw-catalog/runs/et10000_extra_models_sweep_20260528_135717
Full run root: /root/autodl-tmp/gw-catalog/runs/et10000_gatedtcn_bandpass_full_ep50_20260528_140806
