#!/usr/bin/env bash
set -euo pipefail

cd /root/autodl-tmp/gw-catalog
source /root/miniconda3/etc/profile.d/conda.sh
conda activate base

RUN_ROOT="runs/liao_realistic_p1_p2_rerank_20260612"
mkdir -p "${RUN_ROOT}"

echo "[runner] start $(date -Is)"

while pgrep -f "88_liao_realistic_p1_p2_rerank.py --stage stage4_snr_amplitude_prior" >/dev/null 2>&1; do
  echo "[runner] waiting for existing stage4 $(date -Is)"
  sleep 60
done

if [ ! -f "${RUN_ROOT}/stage4_snr_amplitude_prior/stage4_snr_amplitude_prior_summary.csv" ]; then
  echo "[runner] run stage4 $(date -Is)"
  PYTHONPATH=. python scripts/experiments/88_liao_realistic_p1_p2_rerank.py --stage stage4_snr_amplitude_prior \
    > "${RUN_ROOT}/stage4_snr_amplitude_prior.log" 2>&1
fi

echo "[runner] run stage5 $(date -Is)"
PYTHONPATH=. python scripts/experiments/88_liao_realistic_p1_p2_rerank.py --stage stage5_reranker_model_compare \
  > "${RUN_ROOT}/stage5_reranker_model_compare.log" 2>&1

echo "[runner] run stage6 $(date -Is)"
PYTHONPATH=. python scripts/experiments/88_liao_realistic_p1_p2_rerank.py --stage stage6_catalog_graph_discovery \
  > "${RUN_ROOT}/stage6_catalog_graph_discovery.log" 2>&1

echo "[runner] done $(date -Is)"
