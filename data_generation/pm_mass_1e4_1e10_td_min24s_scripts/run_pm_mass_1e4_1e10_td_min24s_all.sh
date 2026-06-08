#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
OUT_ROOT="$REPO_ROOT/data_generation/pm_mass_1e4_1e10_td_min24s_outputs"
mkdir -p "$OUT_ROOT"
export GW_OUTPUT_ROOT="$OUT_ROOT"

run_one() {
  local script="$1"
  local name="$2"
  local log="$OUT_ROOT/${name}.log"
  echo "[RUN] $name"
  GW_RUN_NAME="$name" python "$SCRIPT_DIR/$script" > "$log" 2>&1
  echo "[DONE] $name log=$log"
}

run_one PM_GW_events_ET_pm_mass_1e4_1e10_td_min24s.py PM_GW_events_ET_pm_mass_1e4_1e10_td_min24s
run_one PM_GW_events_LIGO_pm_mass_1e4_1e10_td_min24s.py PM_GW_events_LIGO_pm_mass_1e4_1e10_td_min24s
run_one unlensed_GW_events_ET_pm_mass_1e4_1e10_td_min24s.py unlensed_GW_events_ET_pm_mass_1e4_1e10_td_min24s
run_one unlensed_GW_events_LIGO_pm_mass_1e4_1e10_td_min24s.py unlensed_GW_events_LIGO_pm_mass_1e4_1e10_td_min24s
