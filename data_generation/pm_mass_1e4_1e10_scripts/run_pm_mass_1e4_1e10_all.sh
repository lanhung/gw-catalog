#!/usr/bin/env bash
set -euo pipefail
cd /root/autodl-tmp/gw-catalog
export GW_OUTPUT_ROOT=/root/autodl-tmp/gw-catalog/data_generation/pm_mass_1e4_1e10_outputs
mkdir -p "$GW_OUTPUT_ROOT" logs
run_one() {
  local run_name="$1"
  local script="$2"
  echo "===== START ${run_name} $(date -Is) ====="
  GW_RUN_NAME="$run_name" python -u "$script"
  echo "===== DONE ${run_name} $(date -Is) ====="
}
run_one PM_GW_events_ET_pm_mass_1e4_1e10 data_generation/pm_mass_1e4_1e10_scripts/PM_GW_events_ET_pm_mass_1e4_1e10.py
run_one PM_GW_events_LIGO_pm_mass_1e4_1e10 data_generation/pm_mass_1e4_1e10_scripts/PM_GW_events_LIGO_pm_mass_1e4_1e10.py
run_one unlensed_GW_events_ET_pm_mass_1e4_1e10 data_generation/pm_mass_1e4_1e10_scripts/unlensed_GW_events_ET_pm_mass_1e4_1e10.py
run_one unlensed_GW_events_LIGO_pm_mass_1e4_1e10 data_generation/pm_mass_1e4_1e10_scripts/unlensed_GW_events_LIGO_pm_mass_1e4_1e10.py
