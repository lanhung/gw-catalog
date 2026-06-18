#!/usr/bin/env bash
set -euo pipefail

REPO=/root/autodl-tmp/gw-catalog
PID_FILE="${REPO}/logs/ligo_h1l1_full_experiment_20260617.pid"
WATCH_LOG="${REPO}/logs/ligo_h1l1_stage7_watch_20260617.log"
STAGE7_LOG="${REPO}/logs/ligo_h1l1_stage7_modality_combinations_20260617.log"

main_pid=$(cat "${PID_FILE}")
echo "WATCH_MAIN_PID=${main_pid}"

while kill -0 "${main_pid}" 2>/dev/null; do
  sleep 60
done

echo "FULL_RUN_EXITED_AT=$(date -Is)"
cd "${REPO}"
/root/miniconda3/bin/python scripts/experiments/93_ligo_h1l1_modality_combinations.py > "${STAGE7_LOG}" 2>&1
echo "STAGE7_EXITED_AT=$(date -Is)"
echo "WATCH_LOG=${WATCH_LOG}"
