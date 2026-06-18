#!/usr/bin/env bash
set -euo pipefail

cd /root/autodl-tmp/gw-catalog
source /root/miniconda3/etc/profile.d/conda.sh
conda activate base

RUN_ROOT="runs/liao_realistic_p1_p2_rerank_20260612"
mkdir -p "${RUN_ROOT}"

echo "[runner56] start $(date -Is)"

rm -rf "${RUN_ROOT}/stage5_reranker_model_compare" "${RUN_ROOT}/stage6_catalog_graph_discovery"

echo "[runner56] run stage5 $(date -Is)"
PYTHONPATH=. python scripts/experiments/88_liao_realistic_p1_p2_rerank.py --stage stage5_reranker_model_compare \
  > "${RUN_ROOT}/stage5_reranker_model_compare.log" 2>&1

echo "[runner56] run stage6 $(date -Is)"
PYTHONPATH=. python scripts/experiments/88_liao_realistic_p1_p2_rerank.py --stage stage6_catalog_graph_discovery \
  > "${RUN_ROOT}/stage6_catalog_graph_discovery.log" 2>&1

echo "[runner56] done $(date -Is)"
