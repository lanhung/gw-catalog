# ET3 SIS/PM modality 组合实验

本实验基于 ET3 noisy full-catalog 缓存结果，不重新训练 encoder；系统比较 waveform、time、observed sky 及其组合。

## Overall 排名

| variant | R@1 | R@5 | R@10 | Top1% | median rank | weights |
|---|---:|---:|---:|---:|---:|---|
| waveform_plus_raw_time_plus_observed_sky_step | 0.9792 | 0.998 | 0.9992 | 0.9997 | 1 | waveform=1, raw_time=1, observed_sky_step=0.25 |
| waveform_plus_liao_time_lr_plus_observed_sky_step | 0.9757 | 0.9983 | 0.999 | 0.9995 | 1 | waveform=1, liao_time_lr=1, observed_sky_step=0.25 |
| waveform_plus_raw_time_plus_observed_sky_log_overlap | 0.9587 | 0.9873 | 0.9932 | 0.9983 | 1 | waveform=1, raw_time=0.5, observed_sky_log_overlap=4 |
| waveform_plus_observed_sky_step | 0.8968 | 0.9838 | 0.9932 | 0.9982 | 1 | waveform=1, observed_sky_step=0.25 |
| waveform_plus_liao_time_lr_plus_observed_sky_log_overlap | 0.9445 | 0.9863 | 0.992 | 0.9983 | 1 | waveform=1, liao_time_lr=1, observed_sky_log_overlap=4 |
| liao_time_lr_plus_observed_sky_step | 0.7148 | 0.9465 | 0.9808 | 0.9967 | 1 | liao_time_lr=1, observed_sky_step=0.25 |
| raw_time_plus_observed_sky_step | 0.7683 | 0.9463 | 0.971 | 0.9957 | 1 | raw_time=1, observed_sky_step=0.25 |
| waveform_plus_raw_time | 0.858 | 0.9438 | 0.9648 | 0.9923 | 1 | waveform=1, raw_time=0.5 |
| waveform_plus_observed_sky_log_overlap | 0.8587 | 0.9365 | 0.961 | 0.9897 | 1 | waveform=1, observed_sky_log_overlap=4 |
| waveform_plus_liao_time_lr | 0.83 | 0.931 | 0.9597 | 0.9918 | 1 | waveform=1, liao_time_lr=1 |
| observed_sky_step_only | 0.5422 | 0.8278 | 0.945 | 1 | 1 | observed_sky_step=1 |
| observed_sky_log_overlap_only | 0.2417 | 0.6933 | 0.8883 | 0.9998 | 3 | observed_sky_log_overlap=1 |
| waveform_only | 0.6245 | 0.7978 | 0.8542 | 0.9585 | 1 | waveform=1 |
| liao_time_lr_plus_observed_sky_log_overlap | 0.6323 | 0.7823 | 0.833 | 0.979 | 1 | liao_time_lr=0.25, observed_sky_log_overlap=4 |
| raw_time_plus_observed_sky_log_overlap | 0.6025 | 0.7308 | 0.7917 | 0.9868 | 1 | raw_time=0.25, observed_sky_log_overlap=4 |
| liao_time_lr_only | 0.1297 | 0.404 | 0.5308 | 0.683 | 9 | liao_time_lr=1 |
| raw_time_only | 0.1352 | 0.405 | 0.5298 | 0.6778 | 9 | raw_time=1 |

## SIS / PM 分解

| variant | subset | R@1 | R@5 | R@10 | Top1% | median rank |
|---|---|---:|---:|---:|---:|---:|
| liao_time_lr_only | PM | 0.2473 | 0.751 | 0.9507 | 1 | 3 |
| liao_time_lr_only | SIS | 0.012 | 0.057 | 0.111 | 0.366 | 172 |
| liao_time_lr_plus_observed_sky_log_overlap | PM | 0.956 | 1 | 1 | 1 | 1 |
| liao_time_lr_plus_observed_sky_log_overlap | SIS | 0.3087 | 0.5647 | 0.666 | 0.958 | 4 |
| liao_time_lr_plus_observed_sky_step | PM | 0.8407 | 0.9877 | 0.995 | 1 | 1 |
| liao_time_lr_plus_observed_sky_step | SIS | 0.589 | 0.9053 | 0.9667 | 0.9933 | 1 |
| observed_sky_log_overlap_only | PM | 0.2443 | 0.6913 | 0.884 | 1 | 3 |
| observed_sky_log_overlap_only | SIS | 0.239 | 0.6953 | 0.8927 | 0.9997 | 3 |
| observed_sky_step_only | PM | 0.5457 | 0.818 | 0.943 | 1 | 1 |
| observed_sky_step_only | SIS | 0.5387 | 0.8377 | 0.947 | 1 | 1 |
| raw_time_only | PM | 0.2607 | 0.7577 | 0.9577 | 1 | 3 |
| raw_time_only | SIS | 0.0097 | 0.0523 | 0.102 | 0.3557 | 188 |
| raw_time_plus_observed_sky_log_overlap | PM | 0.968 | 1 | 1 | 1 | 1 |
| raw_time_plus_observed_sky_log_overlap | SIS | 0.237 | 0.4617 | 0.5833 | 0.9737 | 7 |
| raw_time_plus_observed_sky_step | PM | 0.9333 | 0.9937 | 0.9973 | 1 | 1 |
| raw_time_plus_observed_sky_step | SIS | 0.6033 | 0.899 | 0.9447 | 0.9913 | 1 |
| waveform_only | PM | 0.575 | 0.751 | 0.8177 | 0.942 | 1 |
| waveform_only | SIS | 0.674 | 0.8447 | 0.8907 | 0.975 | 1 |
| waveform_plus_liao_time_lr | PM | 0.94 | 0.9797 | 0.9863 | 0.9983 | 1 |
| waveform_plus_liao_time_lr | SIS | 0.72 | 0.8823 | 0.933 | 0.9853 | 1 |
| waveform_plus_liao_time_lr_plus_observed_sky_log_overlap | PM | 0.9803 | 0.9963 | 0.9987 | 1 | 1 |
| waveform_plus_liao_time_lr_plus_observed_sky_log_overlap | SIS | 0.9087 | 0.9763 | 0.9853 | 0.9967 | 1 |
| waveform_plus_liao_time_lr_plus_observed_sky_step | PM | 0.9863 | 0.9987 | 0.9993 | 1 | 1 |
| waveform_plus_liao_time_lr_plus_observed_sky_step | SIS | 0.965 | 0.998 | 0.9987 | 0.999 | 1 |
| waveform_plus_observed_sky_log_overlap | PM | 0.8237 | 0.9157 | 0.945 | 0.9847 | 1 |
| waveform_plus_observed_sky_log_overlap | SIS | 0.8937 | 0.9573 | 0.977 | 0.9947 | 1 |
| waveform_plus_observed_sky_step | PM | 0.8787 | 0.979 | 0.9907 | 0.9973 | 1 |
| waveform_plus_observed_sky_step | SIS | 0.915 | 0.9887 | 0.9957 | 0.999 | 1 |
| waveform_plus_raw_time | PM | 0.9297 | 0.9693 | 0.9793 | 0.9953 | 1 |
| waveform_plus_raw_time | SIS | 0.7863 | 0.9183 | 0.9503 | 0.9893 | 1 |
| waveform_plus_raw_time_plus_observed_sky_log_overlap | PM | 0.9737 | 0.991 | 0.9953 | 1 | 1 |
| waveform_plus_raw_time_plus_observed_sky_log_overlap | SIS | 0.9437 | 0.9837 | 0.991 | 0.9967 | 1 |
| waveform_plus_raw_time_plus_observed_sky_step | PM | 0.994 | 0.9997 | 1 | 1 | 1 |
| waveform_plus_raw_time_plus_observed_sky_step | SIS | 0.9643 | 0.9963 | 0.9983 | 0.9993 | 1 |