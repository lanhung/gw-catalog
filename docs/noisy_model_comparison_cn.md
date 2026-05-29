# ET10000 noisy 各模型结果对比

说明：本表汇总当前仓库中 ET10000 noisy 实验的 `summary.json`。主要比较 pair-level 检索指标和 catalog-level 指标；`Aux=True` 的行不是纯 waveform-only。

## 全部模型对比

| Family | Run | Backbone | Preprocess | Hilbert | Aux | N | Ep | R@1 | R@10 | Pair F1 | Cand Recall | Catalog F1 | Time(s) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PM | `PM_noisy_attnresnet_win16k_noaug_ep50` | attnresnet | none | False | False | 10000 | 50 | 0.1040 | 0.3050 | 0.0773 | 0.3373 | 0.0931 | 911.0064 |
| PM | `PM_noisy_gatedtcn_bandpass_n10000_ep50` | gatedtcn | bandpass | False | False | 10000 | 50 | 0.2650 | 0.5207 | 0.1844 | 0.5547 | 0.2950 | 685.5577 |
| PM | `PM_noisy_inceptionattn_bandpass_n10000_ep50` | inceptionattn | bandpass | False | False | 10000 | 50 | 0.2910 | 0.5243 | 0.1948 | 0.5533 | 0.3344 | 690.5136 |
| PM | `PM_noisy_bandpass_n10000_ep50` | inceptiontime | bandpass | False | False | 10000 | 50 | 0.3040 | 0.5407 | 0.1972 | 0.5753 | 0.3216 | 698.5294 |
| PM | `PM_noisy_win16k_hilbert_ep50` | inceptiontime | none | True | False | 10000 | 50 | 0.2483 | 0.4913 | 0.1644 | 0.5253 | 0.2699 | 1007.5953 |
| PM | `PM_noisy_win16k_noaug_ep50` | inceptiontime | none | False | False | 10000 | 50 | 0.2663 | 0.5047 | 0.1842 | 0.5353 | 0.3103 | 1008.9929 |
| PM | `PM_noisy_win32k_stride4_ep50` | inceptiontime | none | False | False | 10000 | 50 | 0.1377 | 0.3133 | 0.0915 | 0.3433 | 0.1637 | 1031.5571 |
| PM | `PM_noisy_distill_from_pure_ep20` | inceptiontime | none | False | False | 10000 | 20 | 0.2000 | 0.4267 | 0.1309 | 0.4647 | 0.2229 | 403.9107 |
| PM | `PM_noisy_ep20_inceptiontime` | inceptiontime | none | False | False | 10000 | 20 | 0.2673 | 0.5103 | 0.1731 | 0.5400 | 0.2596 | 561.4373 |
| PM | `PM_noisy_hybrid_distill_w02_ep20` | inceptiontime | none | False | False | 10000 | 20 | 0.2773 | 0.5190 | 0.1818 | 0.5560 | 0.3072 | 435.9692 |
| PM | `PM_noisy_cbamresnet_bandpass_n2500_ep10` | cbamresnet | bandpass | False | False | 2500 | 10 | 0.0720 | 0.2787 | 0.0491 | 0.3067 | 0.0424 | 47.4705 |
| PM | `PM_noisy_convnext1d_bandpass_n2500_ep10` | convnext1d | bandpass | False | False | 2500 | 10 | 0.0080 | 0.0413 | 0.0067 | 0.0480 | 0.0106 | 43.8891 |
| PM | `PM_noisy_dilatedresnet_bandpass_n2500_ep10` | dilatedresnet | bandpass | False | False | 2500 | 10 | 0.1133 | 0.3493 | 0.0896 | 0.3760 | 0.1343 | 48.0444 |
| PM | `PM_noisy_gatedtcn_bandpass_n2500_ep10` | gatedtcn | bandpass | False | False | 2500 | 10 | 0.2747 | 0.5227 | 0.2085 | 0.5600 | 0.2773 | 43.2113 |
| PM | `PM_noisy_inceptionattn_bandpass_n2500_ep10` | inceptionattn | bandpass | False | False | 2500 | 10 | 0.2760 | 0.5440 | 0.1856 | 0.5787 | 0.2911 | 46.9228 |
| PM | `PM_noisy_bandpass_n2500_ep10` | inceptiontime | bandpass | False | False | 2500 | 10 | 0.1947 | 0.4493 | 0.1521 | 0.4907 | 0.2481 | 46.5445 |
| PM | `PM_noisy_inception_bandpass_hilbert_n2500_ep10` | inceptiontime | bandpass | True | False | 2500 | 10 | 0.1867 | 0.4320 | 0.1289 | 0.4720 | 0.2219 | 49.8445 |
| PM | `PM_noisy_whiten_bandpass_n2500_ep10` | inceptiontime | whiten_bandpass | False | False | 2500 | 10 | 0.1667 | 0.3947 | 0.1187 | 0.4347 | 0.1865 | 45.6900 |
| PM | `PM_noisy_whiten_n2500_ep10` | inceptiontime | whiten | False | False | 2500 | 10 | 0.1253 | 0.3813 | 0.0854 | 0.4187 | 0.1099 | 46.5771 |
| PM | `PM_noisy_patchtst_bandpass_n2500_ep10` | patchtst | bandpass | False | False | 2500 | 10 | 0.0773 | 0.2680 | 0.0514 | 0.2987 | 0.0663 | 40.2438 |
| PM | `PM_noisy_rocket_bandpass_n2500_ep10` | rocket | bandpass | False | False | 2500 | 10 | 0.0800 | 0.2827 | 0.0459 | 0.3253 | 0.0625 | 34.3953 |
| PM | `PM_noisy_seresnet_bandpass_n2500_ep10` | seresnet | bandpass | False | False | 2500 | 10 | 0.0613 | 0.2053 | 0.0414 | 0.2293 | 0.0530 | 47.7674 |
| PM | `PM_noisy_timesnetlite_bandpass_n2500_ep10` | timesnetlite | bandpass | False | False | 2500 | 10 | 0.2307 | 0.5040 | 0.1788 | 0.5467 | 0.2717 | 35.1734 |
| SIS | `SIS_noisy_attnresnet_win16k_noaug_ep50` | attnresnet | none | False | False | 10000 | 50 | 0.1807 | 0.4287 | 0.1276 | 0.4700 | 0.1995 | 909.3949 |
| SIS | `SIS_noisy_gatedtcn_bandpass_n10000_ep50` | gatedtcn | bandpass | False | False | 10000 | 50 | 0.3277 | 0.6020 | 0.2945 | 0.6360 | 0.3719 | 668.0278 |
| SIS | `SIS_noisy_inceptionattn_bandpass_n10000_ep50` | inceptionattn | bandpass | False | False | 10000 | 50 | 0.3943 | 0.6517 | 0.2814 | 0.6800 | 0.4482 | 692.5081 |
| SIS | `SIS_noisy_bandpass_n10000_ep50` | inceptiontime | bandpass | False | False | 10000 | 50 | 0.4070 | 0.6577 | 0.2820 | 0.6873 | 0.4425 | 679.5947 |
| SIS | `SIS_noisy_inception_bandpass_hilbert_n10000_ep50` | inceptiontime | bandpass | True | False | 10000 | 50 | 0.3960 | 0.6567 | 0.2624 | 0.6860 | 0.4353 | 687.7422 |
| SIS | `SIS_noisy_inception_win16k_hilbert_pureaux_ep50` | inceptiontime | none | True | True | 10000 | 50 | 0.0573 | 0.1657 | 0.0356 | 0.1893 | 0.0544 | 2306.7381 |
| SIS | `SIS_noisy_win16k_hilbert_ep50` | inceptiontime | none | True | False | 10000 | 50 | 0.3510 | 0.6030 | 0.2305 | 0.6380 | 0.3955 | 1013.8648 |
| SIS | `SIS_noisy_win16k_noaug_ep50` | inceptiontime | none | False | False | 10000 | 50 | 0.3230 | 0.5950 | 0.2205 | 0.6327 | 0.3606 | 1009.2944 |
| SIS | `SIS_noisy_win32k_stride4_ep50` | inceptiontime | none | False | False | 10000 | 50 | 0.2233 | 0.4397 | 0.1578 | 0.4733 | 0.2683 | 1012.0989 |
| SIS | `SIS_noisy_distill_from_pure_ep20` | inceptiontime | none | False | False | 10000 | 20 | 0.2623 | 0.5120 | 0.1693 | 0.5507 | 0.3119 | 414.0247 |
| SIS | `SIS_noisy_ep20_inceptiontime` | inceptiontime | none | False | False | 10000 | 20 | 0.3177 | 0.5973 | 0.2082 | 0.6340 | 0.3319 | 553.9883 |
| SIS | `SIS_noisy_hybrid_distill_w02_ep20` | inceptiontime | none | False | False | 10000 | 20 | 0.3430 | 0.6107 | 0.2307 | 0.6440 | 0.3700 | 439.5943 |
| SIS | `SIS_noisy_cbamresnet_bandpass_n2500_ep10` | cbamresnet | bandpass | False | False | 2500 | 10 | 0.1560 | 0.4587 | 0.1153 | 0.4907 | 0.1285 | 51.9043 |
| SIS | `SIS_noisy_convnext1d_bandpass_n2500_ep10` | convnext1d | bandpass | False | False | 2500 | 10 | 0.0107 | 0.0507 | 0.0107 | 0.0560 | 0.0048 | 48.5329 |
| SIS | `SIS_noisy_dilatedresnet_bandpass_n2500_ep10` | dilatedresnet | bandpass | False | False | 2500 | 10 | 0.1920 | 0.5040 | 0.1387 | 0.5467 | 0.1584 | 46.7548 |
| SIS | `SIS_noisy_gatedtcn_bandpass_n2500_ep10` | gatedtcn | bandpass | False | False | 2500 | 10 | 0.4173 | 0.7107 | 0.3533 | 0.7387 | 0.4621 | 43.6566 |
| SIS | `SIS_noisy_inceptionattn_bandpass_n2500_ep10` | inceptionattn | bandpass | False | False | 2500 | 10 | 0.4240 | 0.7227 | 0.2657 | 0.7627 | 0.4223 | 46.1804 |
| SIS | `SIS_noisy_bandpass_n2500_ep10` | inceptiontime | bandpass | False | False | 2500 | 10 | 0.3547 | 0.6440 | 0.2431 | 0.6907 | 0.3596 | 45.2487 |
| SIS | `SIS_noisy_inception_bandpass_hilbert_n2500_ep10` | inceptiontime | bandpass | True | False | 2500 | 10 | 0.3787 | 0.6213 | 0.2309 | 0.6613 | 0.4191 | 48.5096 |
| SIS | `SIS_noisy_whiten_bandpass_n2500_ep10` | inceptiontime | whiten_bandpass | False | False | 2500 | 10 | 0.2947 | 0.5800 | 0.2104 | 0.6133 | 0.3348 | 46.0580 |
| SIS | `SIS_noisy_whiten_n2500_ep10` | inceptiontime | whiten | False | False | 2500 | 10 | 0.2000 | 0.5347 | 0.1357 | 0.5787 | 0.1619 | 46.0030 |
| SIS | `SIS_noisy_patchtst_bandpass_n2500_ep10` | patchtst | bandpass | False | False | 2500 | 10 | 0.1387 | 0.4173 | 0.0918 | 0.4667 | 0.1236 | 41.9584 |
| SIS | `SIS_noisy_rocket_bandpass_n2500_ep10` | rocket | bandpass | False | False | 2500 | 10 | 0.1533 | 0.4213 | 0.0889 | 0.4773 | 0.1789 | 34.3341 |
| SIS | `SIS_noisy_seresnet_bandpass_n2500_ep10` | seresnet | bandpass | False | False | 2500 | 10 | 0.1133 | 0.3720 | 0.0814 | 0.4107 | 0.1096 | 47.5934 |
| SIS | `SIS_noisy_timesnetlite_bandpass_n2500_ep10` | timesnetlite | bandpass | False | False | 2500 | 10 | 0.3813 | 0.6827 | 0.3174 | 0.7173 | 0.4135 | 34.6727 |

## 当前结论

- Pair-level/top-k 检索优先：`InceptionTime + bandpass` 仍是当前最佳，SIS R@1=0.4070，PM R@1=0.3040。
- Catalog-level 系统检出优先：`inceptionattn + bandpass` 当前更好，SIS Catalog F1=0.4482，PM Catalog F1=0.3344。
- 新增模型中 `gatedtcn` 小规模表现最好，但 n=10000、50ep 后没有超过 InceptionTime 系列；`timesnetlite` 可作为速度较快的次级 ablation；`seresnet`、`cbamresnet`、`patchtst`、`rocket` 当前效果偏弱。
