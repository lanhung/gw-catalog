# Liao realistic rerank 当前实验结果整合

生成时间：2026-06-15

## 1. 一句话结论

当前最值得作为主结果的是 **Stage3：waveform + Liao time-delay LR + observed sky step**。

它没有使用 true sky 作为主输入，只使用由 true sky 模拟出来的 `ra_obs/dec_obs/sky_area90`，同时把时间先验替换为 Liao/GW-LMC 分布驱动的 likelihood ratio。该方案在 ET 和 LIGO noisy 上都是整体最强或最稳定的可解释方法。

## 2. 全部阶段 Top overall 结果

| stage | detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Stage3 time + sky | ET | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | overall | 0.896 | 0.9708 | 0.9825 | 0.9972 | 0.9997 | 0.9997 | 1 |
| Stage5 reranker model | ET | weighted_sum_val_selected_extensible | overall | 0.8928 | 0.964 | 0.9805 | 0.9977 | 1 | 1 | 1 |
| Stage2 observed sky | ET | a90_100_step_val_selected | overall | 0.79 | 0.9132 | 0.9457 | 0.9837 | 0.9918 | 0.9943 | 1 |
| Stage5 reranker model | ET | mlp_tabular | overall | 0.7083 | 0.8935 | 0.9343 | 0.9778 | 0.9817 | 0.9835 | 1 |
| Stage4 SNR/amplitude | ET | plus_raw_snr_ratio | overall | 0.782 | 0.8877 | 0.921 | 0.985 | 0.997 | 0.999 | 1 |
| Stage3 time + sky | LIGO | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | overall | 0.658 | 0.8567 | 0.9073 | 0.9903 | 0.9985 | 0.9993 | 1 |
| Stage5 reranker model | LIGO | weighted_sum_val_selected_extensible | overall | 0.6035 | 0.7842 | 0.8393 | 0.9682 | 0.9982 | 0.9998 | 1 |
| Stage5 reranker model | LIGO | lightgbm | overall | 0.6455 | 0.746 | 0.7958 | 0.9403 | 0.9693 | 0.977 | 1 |
| Stage5 reranker model | LIGO | hgb | overall | 0.534 | 0.7152 | 0.7728 | 0.9315 | 0.9623 | 0.9705 | 1 |
| Stage2 observed sky | LIGO | observed_sky_step_only | overall | 0.771 | 0.771 | 0.7713 | 0.986 | 1 | 1 | 1 |

## 3. 推荐主线结果

推荐主线：

```text
waveform
+ Liao time-delay likelihood ratio
+ observed sky step weight
+ validation-selected weighted fusion
```

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | overall | 0.896 | 0.9708 | 0.9825 | 0.9972 | 0.9997 | 0.9997 | 1 |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | overall | 0.658 | 0.8567 | 0.9073 | 0.9903 | 0.9985 | 0.9993 | 1 |

解释：

- Stage3 每次只在 Stage1/Stage2 已验证的时间与空间 prior 之上做融合，没有加入 SNR/amplitude，也没有切换监督 reranker。
- ET noisy 达到 R@10=0.9825，LIGO noisy 达到 R@10=0.9073，两个 detector 的 median rank 都为 1。
- 相比 Stage5 learned reranker，它更稳定、更容易解释，也更适合作为论文主表方法。

## 4. 分阶段 overall 结果

### Stage1 时间先验

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | waveform_plus_liao_time_lr_val_selected | overall | 0.6112 | 0.7527 | 0.8015 | 0.9243 | 0.9817 | 0.9915 | 1 |
| ET | waveform_plus_liao_time_step_val_selected | overall | 0.329 | 0.5352 | 0.614 | 0.7998 | 0.892 | 0.9202 | 4 |
| ET | liao_time_lr_only | overall | 0.1332 | 0.4085 | 0.5282 | 0.686 | 0.845 | 0.9162 | 9 |
| ET | liao_time_step_only | overall | 0.499 | 0.499 | 0.499 | 0.5002 | 0.5015 | 0.5175 | 34 |
| LIGO | liao_time_lr_only | overall | 0.1445 | 0.4127 | 0.5273 | 0.686 | 0.8397 | 0.9168 | 9 |
| LIGO | liao_time_step_only | overall | 0.5253 | 0.5253 | 0.5253 | 0.5267 | 0.528 | 0.5485 | 1 |
| LIGO | waveform_plus_liao_time_lr_val_selected | overall | 0.1658 | 0.4112 | 0.5197 | 0.7093 | 0.8487 | 0.918 | 9 |
| LIGO | waveform_plus_liao_time_step_val_selected | overall | 0.0108 | 0.031 | 0.043 | 0.15 | 0.2985 | 0.3923 | 1615 |

### Stage2 observed sky

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | a90_100_step_val_selected | overall | 0.79 | 0.9132 | 0.9457 | 0.9837 | 0.9918 | 0.9943 | 1 |
| ET | a90_300_step_val_selected | overall | 0.78 | 0.8895 | 0.916 | 0.9647 | 0.982 | 0.9872 | 1 |
| ET | waveform_plus_observed_sky_step_val_selected | overall | 0.7738 | 0.888 | 0.9152 | 0.9615 | 0.9817 | 0.988 | 1 |
| ET | a90_1000_step_val_selected | overall | 0.6902 | 0.835 | 0.8718 | 0.9653 | 0.9888 | 0.9945 | 1 |
| ET | a90_100_gaussian_log_overlap_val_selected | overall | 0.6312 | 0.7585 | 0.8005 | 0.904 | 0.961 | 0.9863 | 1 |
| ET | a90_300_gaussian_log_overlap_val_selected | overall | 0.6253 | 0.7535 | 0.7935 | 0.898 | 0.9563 | 0.9812 | 1 |
| ET | waveform_plus_observed_sky_log_overlap_val_selected | overall | 0.6225 | 0.7543 | 0.793 | 0.8977 | 0.9563 | 0.9815 | 1 |
| ET | a90_1000_gaussian_log_overlap_val_selected | overall | 0.6125 | 0.744 | 0.786 | 0.8927 | 0.9548 | 0.9785 | 1 |
| ET | observed_sky_step_only | overall | 0.7497 | 0.752 | 0.778 | 0.9943 | 0.9998 | 1 | 1 |
| ET | observed_sky_log_overlap_only | overall | 0.2357 | 0.5878 | 0.7532 | 0.9862 | 0.9993 | 1 | 4 |
| LIGO | observed_sky_step_only | overall | 0.771 | 0.771 | 0.7713 | 0.986 | 1 | 1 | 1 |
| LIGO | observed_sky_log_overlap_only | overall | 0.1958 | 0.3827 | 0.4925 | 0.9387 | 1 | 1 | 11 |
| LIGO | a90_50_step_val_selected | overall | 0.1908 | 0.322 | 0.4358 | 0.9123 | 0.9877 | 0.9925 | 13 |
| LIGO | waveform_plus_observed_sky_step_val_selected | overall | 0.171 | 0.2958 | 0.3895 | 0.853 | 0.9812 | 0.9898 | 17 |
| LIGO | a90_100_step_val_selected | overall | 0.1707 | 0.2977 | 0.386 | 0.8577 | 0.9768 | 0.9847 | 18 |
| LIGO | a90_200_step_val_selected | overall | 0.1425 | 0.2603 | 0.3448 | 0.8078 | 0.9745 | 0.9862 | 23 |
| LIGO | a90_200_gaussian_log_overlap_val_selected | overall | 0.0722 | 0.1382 | 0.1753 | 0.3593 | 0.6307 | 0.7882 | 235.5 |
| LIGO | waveform_plus_observed_sky_log_overlap_val_selected | overall | 0.0735 | 0.1375 | 0.1752 | 0.3503 | 0.607 | 0.7558 | 259 |
| LIGO | a90_100_gaussian_log_overlap_val_selected | overall | 0.0728 | 0.1375 | 0.1748 | 0.3507 | 0.6072 | 0.7592 | 259 |
| LIGO | a90_50_gaussian_log_overlap_val_selected | overall | 0.0713 | 0.1365 | 0.1735 | 0.3372 | 0.5772 | 0.7237 | 293 |

### Stage3 time + sky

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | overall | 0.896 | 0.9708 | 0.9825 | 0.9972 | 0.9997 | 0.9997 | 1 |
| ET | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | overall | 0.7795 | 0.8827 | 0.9177 | 0.9865 | 0.9975 | 0.9995 | 1 |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | overall | 0.658 | 0.8567 | 0.9073 | 0.9903 | 0.9985 | 0.9993 | 1 |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | overall | 0.3792 | 0.6062 | 0.6742 | 0.839 | 0.9478 | 0.9833 | 3 |

### Stage4 SNR/amplitude

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | plus_raw_snr_ratio | overall | 0.782 | 0.8877 | 0.921 | 0.985 | 0.997 | 0.999 | 1 |
| ET | waveform_plus_time_lr_plus_sky_log_overlap | overall | 0.78 | 0.8833 | 0.9187 | 0.9862 | 0.9973 | 0.9995 | 1 |
| ET | plus_amp_time_2d_lr | overall | 0.78 | 0.8833 | 0.9187 | 0.9862 | 0.9973 | 0.9995 | 1 |
| LIGO | plus_amp_time_2d_lr | overall | 0.3777 | 0.607 | 0.6772 | 0.8312 | 0.9438 | 0.9818 | 3 |
| LIGO | waveform_plus_time_lr_plus_sky_log_overlap | overall | 0.3782 | 0.6048 | 0.6718 | 0.8382 | 0.9487 | 0.9837 | 3 |
| LIGO | plus_raw_snr_ratio | overall | 0.3853 | 0.6075 | 0.6667 | 0.8287 | 0.9353 | 0.9735 | 3 |

### Stage5 reranker model

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | weighted_sum_val_selected_extensible | overall | 0.8928 | 0.964 | 0.9805 | 0.9977 | 1 | 1 | 1 |
| ET | mlp_tabular | overall | 0.7083 | 0.8935 | 0.9343 | 0.9778 | 0.9817 | 0.9835 | 1 |
| ET | weighted_sum_stage4_lambdas | overall | 0.7795 | 0.8823 | 0.9192 | 0.987 | 0.9972 | 0.9995 | 1 |
| ET | hgb | overall | 0.5712 | 0.8127 | 0.8842 | 0.9503 | 0.9668 | 0.9733 | 1 |
| ET | lightgbm | overall | 0.5568 | 0.7723 | 0.864 | 0.957 | 0.9638 | 0.9703 | 1 |
| ET | logistic_regression | overall | 0.0065 | 0.015 | 0.0192 | 0.0585 | 0.1067 | 0.1505 | 3036 |
| LIGO | weighted_sum_val_selected_extensible | overall | 0.6035 | 0.7842 | 0.8393 | 0.9682 | 0.9982 | 0.9998 | 1 |
| LIGO | lightgbm | overall | 0.6455 | 0.746 | 0.7958 | 0.9403 | 0.9693 | 0.977 | 1 |
| LIGO | hgb | overall | 0.534 | 0.7152 | 0.7728 | 0.9315 | 0.9623 | 0.9705 | 1 |
| LIGO | weighted_sum_stage4_lambdas | overall | 0.3767 | 0.6062 | 0.6763 | 0.8327 | 0.9433 | 0.9827 | 3 |
| LIGO | mlp_tabular | overall | 0.4323 | 0.5702 | 0.6287 | 0.7778 | 0.8547 | 0.8883 | 3 |
| LIGO | logistic_regression | overall | 0.183 | 0.183 | 0.183 | 0.184 | 0.2732 | 0.3852 | 1518 |

## 5. SIS / PM 分解结果

### Stage1 时间先验

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | liao_time_lr_only | PM | 0.2527 | 0.7613 | 0.9477 | 1 | 1 | 1 | 3 |
| ET | waveform_plus_liao_time_lr_val_selected | PM | 0.7877 | 0.8803 | 0.908 | 0.9807 | 0.998 | 1 | 1 |
| ET | waveform_plus_liao_time_step_val_selected | PM | 0.177 | 0.408 | 0.5093 | 0.7507 | 0.8537 | 0.8837 | 10 |
| ET | liao_time_step_only | PM | 0.1767 | 0.1767 | 0.1767 | 0.1767 | 0.1767 | 0.1997 | 1396 |
| ET | liao_time_step_only | SIS | 0.8213 | 0.8213 | 0.8213 | 0.8237 | 0.8263 | 0.8353 | 1 |
| ET | waveform_plus_liao_time_step_val_selected | SIS | 0.481 | 0.6623 | 0.7187 | 0.849 | 0.9303 | 0.9567 | 2 |
| ET | waveform_plus_liao_time_lr_val_selected | SIS | 0.4347 | 0.625 | 0.695 | 0.868 | 0.9653 | 0.983 | 2 |
| ET | liao_time_lr_only | SIS | 0.0137 | 0.0557 | 0.1087 | 0.372 | 0.69 | 0.8323 | 172 |
| LIGO | liao_time_lr_only | PM | 0.2777 | 0.7677 | 0.944 | 1 | 1 | 1 | 3 |
| LIGO | waveform_plus_liao_time_lr_val_selected | PM | 0.3057 | 0.731 | 0.8893 | 1 | 1 | 1 | 3 |
| LIGO | liao_time_step_only | PM | 0.2293 | 0.2293 | 0.2293 | 0.2293 | 0.2293 | 0.2607 | 1293 |
| LIGO | waveform_plus_liao_time_step_val_selected | PM | 0.001 | 0.0053 | 0.0077 | 0.0693 | 0.207 | 0.3023 | 2361.5 |
| LIGO | liao_time_step_only | SIS | 0.8213 | 0.8213 | 0.8213 | 0.824 | 0.8267 | 0.8363 | 1 |
| LIGO | waveform_plus_liao_time_lr_val_selected | SIS | 0.026 | 0.0913 | 0.15 | 0.4187 | 0.6973 | 0.836 | 144.5 |
| LIGO | liao_time_lr_only | SIS | 0.0113 | 0.0577 | 0.1107 | 0.372 | 0.6793 | 0.8337 | 176 |
| LIGO | waveform_plus_liao_time_step_val_selected | SIS | 0.0207 | 0.0567 | 0.0783 | 0.2307 | 0.39 | 0.4823 | 984 |

### Stage2 observed sky

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | a90_100_step_val_selected | PM | 0.751 | 0.8913 | 0.9273 | 0.9797 | 0.9893 | 0.9917 | 1 |
| ET | a90_300_step_val_selected | PM | 0.7443 | 0.859 | 0.8923 | 0.9507 | 0.9757 | 0.984 | 1 |
| ET | waveform_plus_observed_sky_step_val_selected | PM | 0.7377 | 0.855 | 0.886 | 0.9457 | 0.974 | 0.984 | 1 |
| ET | a90_1000_step_val_selected | PM | 0.6527 | 0.7973 | 0.8407 | 0.9533 | 0.9847 | 0.9923 | 1 |
| ET | observed_sky_step_only | PM | 0.7533 | 0.7553 | 0.7803 | 0.991 | 0.9997 | 1 | 1 |
| ET | a90_100_gaussian_log_overlap_val_selected | PM | 0.5793 | 0.7163 | 0.7647 | 0.8737 | 0.9473 | 0.9807 | 1 |
| ET | a90_300_gaussian_log_overlap_val_selected | PM | 0.5717 | 0.7123 | 0.7583 | 0.8677 | 0.94 | 0.9757 | 1 |
| ET | waveform_plus_observed_sky_log_overlap_val_selected | PM | 0.5673 | 0.7127 | 0.7577 | 0.8673 | 0.9397 | 0.976 | 1 |
| ET | a90_1000_gaussian_log_overlap_val_selected | PM | 0.56 | 0.702 | 0.7513 | 0.8627 | 0.9373 | 0.9723 | 1 |
| ET | observed_sky_log_overlap_only | PM | 0.2253 | 0.5657 | 0.7247 | 0.9787 | 0.999 | 1 | 4 |
| ET | a90_100_step_val_selected | SIS | 0.829 | 0.935 | 0.964 | 0.9877 | 0.9943 | 0.997 | 1 |
| ET | waveform_plus_observed_sky_step_val_selected | SIS | 0.81 | 0.921 | 0.9443 | 0.9773 | 0.9893 | 0.992 | 1 |
| ET | a90_300_step_val_selected | SIS | 0.8157 | 0.92 | 0.9397 | 0.9787 | 0.9883 | 0.9903 | 1 |
| ET | a90_1000_step_val_selected | SIS | 0.7277 | 0.8727 | 0.903 | 0.9773 | 0.993 | 0.9967 | 1 |
| ET | a90_100_gaussian_log_overlap_val_selected | SIS | 0.683 | 0.8007 | 0.8363 | 0.9343 | 0.9747 | 0.992 | 1 |
| ET | a90_300_gaussian_log_overlap_val_selected | SIS | 0.679 | 0.7947 | 0.8287 | 0.9283 | 0.9727 | 0.9867 | 1 |
| ET | waveform_plus_observed_sky_log_overlap_val_selected | SIS | 0.6777 | 0.796 | 0.8283 | 0.928 | 0.973 | 0.987 | 1 |
| ET | a90_1000_gaussian_log_overlap_val_selected | SIS | 0.665 | 0.786 | 0.8207 | 0.9227 | 0.9723 | 0.9847 | 1 |
| ET | observed_sky_log_overlap_only | SIS | 0.246 | 0.61 | 0.7817 | 0.9937 | 0.9997 | 1 | 4 |
| ET | observed_sky_step_only | SIS | 0.746 | 0.7487 | 0.7757 | 0.9977 | 1 | 1 | 1 |
| LIGO | observed_sky_step_only | PM | 0.7653 | 0.7653 | 0.7653 | 0.984 | 1 | 1 | 1 |
| LIGO | observed_sky_log_overlap_only | PM | 0.154 | 0.3177 | 0.42 | 0.9207 | 1 | 1 | 15 |
| LIGO | a90_50_step_val_selected | PM | 0.1543 | 0.273 | 0.3863 | 0.897 | 0.9847 | 0.9913 | 16 |
| LIGO | a90_100_step_val_selected | PM | 0.1403 | 0.247 | 0.3323 | 0.838 | 0.9727 | 0.983 | 22 |
| LIGO | waveform_plus_observed_sky_step_val_selected | PM | 0.138 | 0.2403 | 0.3317 | 0.8293 | 0.9757 | 0.9863 | 22 |
| LIGO | a90_200_step_val_selected | PM | 0.111 | 0.2093 | 0.292 | 0.7887 | 0.9733 | 0.9867 | 28 |
| LIGO | a90_100_gaussian_log_overlap_val_selected | PM | 0.0563 | 0.1107 | 0.1423 | 0.2987 | 0.5713 | 0.74 | 329 |
| LIGO | a90_50_gaussian_log_overlap_val_selected | PM | 0.054 | 0.1097 | 0.1413 | 0.2863 | 0.542 | 0.6997 | 367.5 |
| LIGO | waveform_plus_observed_sky_log_overlap_val_selected | PM | 0.055 | 0.11 | 0.141 | 0.299 | 0.572 | 0.7333 | 331.5 |
| LIGO | a90_200_gaussian_log_overlap_val_selected | PM | 0.0547 | 0.1117 | 0.1403 | 0.3083 | 0.5947 | 0.7693 | 298.5 |
| LIGO | observed_sky_step_only | SIS | 0.7767 | 0.7767 | 0.7773 | 0.988 | 1 | 1 | 1 |
| LIGO | observed_sky_log_overlap_only | SIS | 0.2377 | 0.4477 | 0.565 | 0.9567 | 1 | 1 | 8 |
| LIGO | a90_50_step_val_selected | SIS | 0.2273 | 0.371 | 0.4853 | 0.9277 | 0.9907 | 0.9937 | 11 |
| LIGO | waveform_plus_observed_sky_step_val_selected | SIS | 0.204 | 0.3513 | 0.4473 | 0.8767 | 0.9867 | 0.9933 | 14 |
| LIGO | a90_100_step_val_selected | SIS | 0.201 | 0.3483 | 0.4397 | 0.8773 | 0.981 | 0.9863 | 14 |
| LIGO | a90_200_step_val_selected | SIS | 0.174 | 0.3113 | 0.3977 | 0.827 | 0.9757 | 0.9857 | 19 |
| LIGO | a90_200_gaussian_log_overlap_val_selected | SIS | 0.0897 | 0.1647 | 0.2103 | 0.4103 | 0.6667 | 0.807 | 174.5 |
| LIGO | waveform_plus_observed_sky_log_overlap_val_selected | SIS | 0.092 | 0.165 | 0.2093 | 0.4017 | 0.642 | 0.7783 | 194.5 |
| LIGO | a90_100_gaussian_log_overlap_val_selected | SIS | 0.0893 | 0.1643 | 0.2073 | 0.4027 | 0.643 | 0.7783 | 193.5 |
| LIGO | a90_50_gaussian_log_overlap_val_selected | SIS | 0.0887 | 0.1633 | 0.2057 | 0.388 | 0.6123 | 0.7477 | 221.5 |

### Stage3 time + sky

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | PM | 0.949 | 0.9863 | 0.9933 | 0.9993 | 1 | 1 | 1 |
| ET | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | PM | 0.8937 | 0.9577 | 0.978 | 0.999 | 1 | 1 | 1 |
| ET | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | SIS | 0.843 | 0.9553 | 0.9717 | 0.995 | 0.9993 | 0.9993 | 1 |
| ET | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | SIS | 0.6653 | 0.8077 | 0.8573 | 0.974 | 0.995 | 0.999 | 1 |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | PM | 0.8833 | 0.987 | 0.995 | 1 | 1 | 1 | 1 |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | PM | 0.6273 | 0.916 | 0.966 | 1 | 1 | 1 | 1 |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_step_val_selected | SIS | 0.4327 | 0.7263 | 0.8197 | 0.9807 | 0.997 | 0.9987 | 2 |
| LIGO | waveform_plus_liao_time_lr_plus_observed_sky_log_overlap_val_selected | SIS | 0.131 | 0.2963 | 0.3823 | 0.678 | 0.8957 | 0.9667 | 26 |

### Stage4 SNR/amplitude

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | waveform_plus_time_lr_plus_sky_log_overlap | PM | 0.8953 | 0.9587 | 0.9773 | 0.9993 | 1 | 1 | 1 |
| ET | plus_amp_time_2d_lr | PM | 0.8953 | 0.9587 | 0.9773 | 0.9993 | 1 | 1 | 1 |
| ET | plus_raw_snr_ratio | PM | 0.888 | 0.954 | 0.9753 | 0.998 | 1 | 1 | 1 |
| ET | plus_raw_snr_ratio | SIS | 0.676 | 0.8213 | 0.8667 | 0.972 | 0.994 | 0.998 | 1 |
| ET | waveform_plus_time_lr_plus_sky_log_overlap | SIS | 0.6647 | 0.808 | 0.86 | 0.973 | 0.9947 | 0.999 | 1 |
| ET | plus_amp_time_2d_lr | SIS | 0.6647 | 0.808 | 0.86 | 0.973 | 0.9947 | 0.999 | 1 |
| LIGO | plus_amp_time_2d_lr | PM | 0.638 | 0.9347 | 0.9817 | 1 | 1 | 1 | 1 |
| LIGO | plus_raw_snr_ratio | PM | 0.653 | 0.9437 | 0.98 | 1 | 1 | 1 | 1 |
| LIGO | waveform_plus_time_lr_plus_sky_log_overlap | PM | 0.626 | 0.9143 | 0.964 | 1 | 1 | 1 | 1 |
| LIGO | waveform_plus_time_lr_plus_sky_log_overlap | SIS | 0.1303 | 0.2953 | 0.3797 | 0.6763 | 0.8973 | 0.9673 | 26 |
| LIGO | plus_amp_time_2d_lr | SIS | 0.1173 | 0.2793 | 0.3727 | 0.6623 | 0.8877 | 0.9637 | 28 |
| LIGO | plus_raw_snr_ratio | SIS | 0.1177 | 0.2713 | 0.3533 | 0.6573 | 0.8707 | 0.947 | 30.5 |

### Stage5 reranker model

| detector | variant | subset | R@1 | R@5 | R@10 | Top1% | Top5% | Top10% | Median rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ET | weighted_sum_val_selected_extensible | PM | 0.9577 | 0.9913 | 0.997 | 1 | 1 | 1 | 1 |
| ET | mlp_tabular | PM | 0.8897 | 0.9793 | 0.9907 | 0.9993 | 0.9993 | 0.9993 | 1 |
| ET | weighted_sum_stage4_lambdas | PM | 0.8947 | 0.9573 | 0.9783 | 0.9997 | 1 | 1 | 1 |
| ET | hgb | PM | 0.8137 | 0.9287 | 0.9503 | 0.9833 | 0.9923 | 0.9943 | 1 |
| ET | lightgbm | PM | 0.8367 | 0.9197 | 0.9417 | 0.9867 | 0.9897 | 0.9917 | 1 |
| ET | logistic_regression | PM | 0.0117 | 0.0263 | 0.0333 | 0.096 | 0.162 | 0.219 | 2140 |
| ET | weighted_sum_val_selected_extensible | SIS | 0.828 | 0.9367 | 0.964 | 0.9953 | 1 | 1 | 1 |
| ET | mlp_tabular | SIS | 0.527 | 0.8077 | 0.878 | 0.9563 | 0.964 | 0.9677 | 1 |
| ET | weighted_sum_stage4_lambdas | SIS | 0.6643 | 0.8073 | 0.86 | 0.9743 | 0.9943 | 0.999 | 1 |
| ET | hgb | SIS | 0.3287 | 0.6967 | 0.818 | 0.9173 | 0.9413 | 0.9523 | 3 |
| ET | lightgbm | SIS | 0.277 | 0.625 | 0.7863 | 0.9273 | 0.938 | 0.949 | 4 |
| ET | logistic_regression | SIS | 0.0013 | 0.0037 | 0.005 | 0.021 | 0.0513 | 0.082 | 4156.5 |
| LIGO | weighted_sum_val_selected_extensible | PM | 0.8283 | 0.9747 | 0.9937 | 1 | 1 | 1 | 1 |
| LIGO | weighted_sum_stage4_lambdas | PM | 0.6353 | 0.934 | 0.9803 | 1 | 1 | 1 | 1 |
| LIGO | hgb | PM | 0.7563 | 0.931 | 0.9447 | 0.9643 | 0.979 | 0.9837 | 1 |
| LIGO | lightgbm | PM | 0.8117 | 0.9027 | 0.932 | 0.973 | 0.9837 | 0.987 | 1 |
| LIGO | mlp_tabular | PM | 0.5333 | 0.6597 | 0.7123 | 0.8463 | 0.9073 | 0.9307 | 1 |
| LIGO | logistic_regression | PM | 0.2487 | 0.2487 | 0.2487 | 0.25 | 0.365 | 0.4957 | 921.5 |
| LIGO | weighted_sum_val_selected_extensible | SIS | 0.3787 | 0.5937 | 0.685 | 0.9363 | 0.9963 | 0.9997 | 3 |
| LIGO | lightgbm | SIS | 0.4793 | 0.5893 | 0.6597 | 0.9077 | 0.955 | 0.967 | 2 |
| LIGO | hgb | SIS | 0.3117 | 0.4993 | 0.601 | 0.8987 | 0.9457 | 0.9573 | 6 |
| LIGO | mlp_tabular | SIS | 0.3313 | 0.4807 | 0.545 | 0.7093 | 0.802 | 0.846 | 7 |
| LIGO | weighted_sum_stage4_lambdas | SIS | 0.118 | 0.2783 | 0.3723 | 0.6653 | 0.8867 | 0.9653 | 27 |
| LIGO | logistic_regression | SIS | 0.1173 | 0.1173 | 0.1173 | 0.118 | 0.1813 | 0.2747 | 2521 |

## 6. 分阶段分析

### 6.1 Stage1：真实时间分布

Stage1 只测试时间先验，不引入 sky 和 SNR。新增两类时间特征：

- `liao_time_step`：基于 Liao 检测多图像时延分布的 q10-q90 / q05-q95 / q01-q99 阶梯函数。
- `liao_time_lr`：`log p(delta_t | lensed) - log p(delta_t | random)`。

主要观察：

- ET 中 `waveform + Liao time LR` 明显最好，R@10=0.8015，说明 Liao time LR 与 waveform 互补。
- LIGO 中 `liao_time_step_only` 的 R@1 很高，但与 waveform 融合后严重下降，说明简单阶梯 time prior 的排序形态和 waveform score 标定冲突。
- LIGO 的 time LR 更稳，但单独提升有限，必须与 sky prior 融合。

### 6.2 Stage2：observed sky posterior

Stage2 只测试 observed sky，不引入 Liao time 和 SNR。true sky 只用于生成模拟观测中心和 A90，不直接进入 rerank。

主要观察：

- ET 中 A90=100 deg2 的 step 最强，R@10=0.9457；A90 越大，定位越差，R@10 降到 0.8718。
- LIGO 中 `observed_sky_step_only` 很强，R@10=0.7713，但 `waveform + sky_step` 反而降到 R@10=0.3895。
- 这说明 sky prior 本身有效，但与 waveform 直接加权时需要更好的权重选择或与 time prior 一起校准。
- 当前圆形 Gaussian/log-overlap 普遍弱于 step，可能因为 log-overlap 的面积归一化项对 A90 标定较敏感。

### 6.3 Stage3：time + observed sky 融合

Stage3 是当前最关键的结果。只融合 Liao time LR 与 observed sky，不加入 SNR，也不切换模型。

主要观察：

- ET：time LR + sky step 达到 R@10=0.9825。
- LIGO：time LR + sky step 达到 R@10=0.9073。
- 两个 detector 都显著超过 Stage1/Stage2 单独因素，说明时间和空间 prior 是互补的。
- sky step 明显优于 sky log-overlap，是当前主线。

### 6.4 Stage4：SNR ratio / amplitude prior

Stage4 在 time LR + sky log-overlap 基础上新增 SNR/amplitude prior。注意这里使用的是 sky log-overlap，而不是 Stage3 最强的 sky step，因此 Stage4 不是与 Stage3 直接争主线，而是专门回答 SNR 是否有额外收益。

主要观察：

- ET：raw SNR ratio 只有极小提升，amp-time 2D LR 被 validation 选为 0，说明没有稳定额外收益。
- LIGO：amp-time 2D LR 从基础 R@10=0.6718 提升到 0.6772，小幅有效。
- SNR/amplitude prior 可以保留为扩展特征，但不建议作为当前主结果核心。

### 6.5 Stage5：rerank 模型比较

Stage5 固定同一组特征，只比较 reranker 和加权修正。特征包括 waveform、rank、margin、time LR、sky norm sep、sky log-overlap、amp-time LR。

主要观察：

- ET：`weighted_sum_val_selected_extensible` R@10=0.9805，接近 Stage3 主线。
- LIGO：`weighted_sum_val_selected_extensible` R@10=0.8393，低于 Stage3 sky step 主线，但高于 Stage4 固定权重。
- LIGO LightGBM 的 R@1=0.6455 高于 weighted-sum 的 0.6035，但 R@10=0.7958 低于 weighted-sum 的 0.8393。
- Logistic regression 在当前采样和标定下严重失败，不建议作为主方法。
- HGB/LightGBM/MLP 都没有稳定超过可解释 weighted-sum。

## 7. 按 detector 的结论

### 7.1 ET noisy

ET 的 waveform 与辅助 prior 兼容性较好。时间 LR、sky step、validation weighted-sum 都能稳定提升。当前 ET 最强为 Stage3 time LR + sky step：R@1=0.8960，R@10=0.9825。

ET 的 A90 sensitivity 清晰：A90=100 step > A90=300 step > A90=1000 step，符合定位误差越小、空间先验越强的预期。

### 7.2 LIGO noisy

LIGO 的单项 prior 更容易出现标定冲突：sky-only 很强，但 waveform + sky 简单融合会变差；time-only 也不足。加入 time LR 后，sky step 的作用被稳定释放，Stage3 达到 R@10=0.9073。

LIGO LightGBM 可提高 R@1，但牺牲 R@10；如果目标是 top-1 discovery，可以作为补充实验；如果目标是稳健召回，weighted-sum 更合适。

## 8. 按 lens family 的结论

从 SIS/PM 分解看，PM 通常更容易被 time/sky prior 拉到前排；SIS 在 LIGO noisy 下仍是更难的部分。Stage3 的 LIGO R@10 提升主要说明 time+sky 的互补性足以缓解 SIS/PM 混合 catalog 中的排序问题。

后续如果要继续优化，应优先看 LIGO noisy SIS 的错误样本：判断是 sky posterior overlap 排序不足、waveform score 与 sky/time 标定冲突，还是 hard-negative 分布与 test full-catalog 不一致。

## 9. 当前最终建议

1. 主表方法：Stage3 `waveform + Liao time LR + observed sky step`。
2. 强 baseline：Stage5 `weighted_sum_val_selected_extensible`，体现可扩展模块和自动加权修正。
3. Ablation 表：Stage1 时间、Stage2 空间、Stage4 SNR/amplitude、Stage5 模型比较分开报告。
4. 不建议把 LightGBM/HGB 作为当前主线；它们可作为 learned reranker 对照。
5. 不建议把 raw true sky 结果放入主表；只能作为 oracle upper bound。
6. 后续优先扩展真实 skymap overlap：椭圆 Gaussian 或 HEALPix posterior overlap。
7. 若做 cross-encoder，只能 Top-K 精排，必须同时报告 candidate recall@K。

## 10. 文件索引

### 10.1 代码

| file | 说明 |
| --- | ---: |
| matchgw/aux_priors/feature_builder.py | observed sky、time step、rank/margin pair feature 构造 |
| matchgw/aux_priors/scorer.py | validation weighted-sum 权重搜索 |
| scripts/experiments/88_liao_realistic_p1_p2_rerank.py | Stage1-5 主实验脚本 |
| scripts/experiments/80_mixed_sis_pm_catalog_modality_compare.py | mixed SIS/PM catalog 数据加载与 encoder 复用 |
| scripts/experiments/81_time_matched_hard_negative_mixed_catalog.py | valid query / hard negative 工具 |
| scripts/experiments/84_fresh50_full_catalog_ranking.py | full-catalog ranking metrics |

### 10.2 结果 CSV

| stage | CSV |
| --- | ---: |
| Stage1 | runs/liao_realistic_p1_p2_rerank_20260612/stage1_liao_time_lr/stage1_liao_time_lr_summary.csv |
| Stage2 | runs/liao_realistic_p1_p2_rerank_20260612/stage2_observed_sky/stage2_observed_sky_summary.csv |
| Stage3 | runs/liao_realistic_p1_p2_rerank_20260612/stage3_liao_time_plus_observed_sky/stage3_liao_time_plus_observed_sky_summary.csv |
| Stage4 | runs/liao_realistic_p1_p2_rerank_20260612/stage4_snr_amplitude_prior/stage4_snr_amplitude_prior_summary.csv |
| Stage5 | runs/liao_realistic_p1_p2_rerank_20260612/stage5_reranker_model_compare/stage5_reranker_model_compare_summary.csv |
