# GW-Augmented Full Run Status - 2026-05-22

Generated data root:

`/root/autodl-tmp/qkzhang_gwaug_20260522_162031`

Dataset summary:

- Source root: `/root/autodl-tmp/qkzhang`
- SIS: 10000 lensed pairs, waveform length 98304
- PM: 10000 lensed pairs, waveform length 98304
- Unlensed: 10000 examples, waveform length 98304
- Added GW-style augmentation: magnification perturbation, compressed time-delay sample shifts, Morse/Hilbert phase handling, colored nonstationary noise, low-frequency drift, occasional glitches, per-event metadata.

Full InceptionTime 50-epoch runs requested:

- SIS noisy
- SIS pure
- PM noisy
- PM pure

Status:

The first full run attempt trained SIS noisy to epoch 50 but was stopped during the slow full validation grid search. The evaluation code was then optimized with top-k partial sorting and a smaller full-run tuning grid. A later restart attempt hit a CUDA runtime failure before producing final summaries. `nvidia-smi -q` reported `gpu_recovery_action=Reboot`, while PyTorch reported `torch.cuda.is_available() == False`. The machine should be rebooted before re-running the four full jobs.

Relevant logs:

- `logs/gwaug_data_gen_20260522_162031.log`
- `logs/gwaug_full_SIS_noisy_ep50_163436.log`
- `logs/gwaug_full_fast_SIS_noisy_ep50_170202.log`
- `logs/gwaug_full_fastgrid_SIS_noisy_ep50_172245.log`

Recommended rerun command after reboot:

```bash
cd /root/autodl-tmp/gw-catalog
DATA=/root/autodl-tmp/qkzhang_gwaug_20260522_162031
RUNROOT=runs/gwaug_full_fastgrid_$(date +%Y%m%d_%H%M%S)
mkdir -p logs "$RUNROOT"
screen -dmS gwaug_full_fastgrid bash -lc "set -e; cd /root/autodl-tmp/gw-catalog; DATA='$DATA'; RUNROOT='$RUNROOT'; mkdir -p logs \"\$RUNROOT\"; for model in SIS PM; do for mode in noisy pure; do OUT=\"\$RUNROOT/\${model}_\${mode}_inception_ep50_full\"; LOG=\"logs/gwaug_full_fastgrid_\${model}_\${mode}_ep50_\${RUNROOT##*_}.log\"; echo \"===== START \$(date) model=\$model mode=\$mode out=\$OUT =====\" | tee -a \"\$LOG\"; PYTHONUNBUFFERED=1 python scripts/08_match_first_train.py --data-root \"\$DATA\" --backbone inceptiontime --model-type \"\$model\" --data-mode \"\$mode\" --epochs 50 --lensed-limit 10000 --unlensed-limit 10000 --batch-size 128 --out-dir \"\$OUT\" 2>&1 | tee -a \"\$LOG\"; echo \"===== END \$(date) model=\$model mode=\$mode =====\" | tee -a \"\$LOG\"; done; done"
```
