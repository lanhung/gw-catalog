#!/usr/bin/env bash
set -euo pipefail
export MPLBACKEND=Agg
export GW_OUTPUT_ROOT="/root/autodl-tmp/createdata/generated_10000_20260527_091859"
cd "/root/autodl-tmp/createdata/generated_10000_20260527_091859_scripts"
for script in SIS_GW_events_ET.py SIS_GW_events_LIGO.py PM_GW_events_ET.py PM_GW_events_LIGO.py unlensed_GW_events_ET.py unlensed_GW_events_LIGO.py; do
  name="${script%.py}"
  export GW_RUN_NAME="${name}_10000"
  echo "==== START $script at $(date -Is) -> $GW_OUTPUT_ROOT/$GW_RUN_NAME"
  python3 "$script"
  echo "==== DONE $script at $(date -Is)"
done
