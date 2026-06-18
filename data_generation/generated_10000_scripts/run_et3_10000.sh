#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/root/autodl-tmp/gw-catalog}"
RUN_TAG="${RUN_TAG:-et3_10000_$(date -u +%Y%m%d_%H%M%S)}"
GW_OUTPUT_ROOT="${GW_OUTPUT_ROOT:-/root/autodl-tmp/createdata/${RUN_TAG}}"
MATCH_ROOT="${MATCH_ROOT:-/root/autodl-tmp/createdata/${RUN_TAG}_match_root}"
PYTHON_BIN="${PYTHON_BIN:-/root/miniconda3/bin/python}"

export GW_OUTPUT_ROOT
export GW_N_SAMPLES="${GW_N_SAMPLES:-10000}"
export GW_N_LENS="${GW_N_LENS:-10000}"
export GW_DETECTOR_NETWORK="${GW_DETECTOR_NETWORK:-ET}"
export GW_DETECTOR_CHANNELS="${GW_DETECTOR_CHANNELS:-3}"
export PYTHONUNBUFFERED=1

mkdir -p "${GW_OUTPUT_ROOT}" "${PROJECT_ROOT}/logs"
cd "${PROJECT_ROOT}"

echo "RUN_TAG=${RUN_TAG}"
echo "GW_OUTPUT_ROOT=${GW_OUTPUT_ROOT}"
echo "MATCH_ROOT=${MATCH_ROOT}"
echo "GW_N_SAMPLES=${GW_N_SAMPLES}"
echo "GW_N_LENS=${GW_N_LENS}"
echo "GW_DETECTOR_NETWORK=${GW_DETECTOR_NETWORK}"
echo "GW_DETECTOR_CHANNELS=${GW_DETECTOR_CHANNELS}"
date -u

"${PYTHON_BIN}" data_generation/generated_10000_scripts/SIS_GW_events_ET3.py
"${PYTHON_BIN}" data_generation/generated_10000_scripts/PM_GW_events_ET3.py
"${PYTHON_BIN}" data_generation/generated_10000_scripts/unlensed_GW_events_ET3.py

"${PYTHON_BIN}" scripts/prepare_et3_match_root.py \
  --generated-root "${GW_OUTPUT_ROOT}" \
  --out-root "${MATCH_ROOT}"

date -u
echo "ET3 10000 generation complete"
