#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p output/online_bench/logs output/online_bench/reports

BASE_MODEL="/mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-3B-Instruct"
ADAPTER="/mnt/public/zxs/course/SFT_qwen/output/ablation_qwen3b_replace/runs/qwen2.5-3b-instruct/v0-20260329-144508/checkpoint-87"
MODEL_NAME="qwen2.5-3b-medical-gate"
PORT=8113

INTERNAL_DATASET="datasets/json/dataset_internal_20_run9_1.json"
EXTERNAL_DATASET="datasets/json/dataset_external_v2_latest_run9_1.json"

cleanup() {
  PID=$(lsof -t -iTCP:${PORT} -sTCP:LISTEN -n -P || true)
  if [ -n "${PID}" ]; then
    kill -9 ${PID} || true
  fi
  pkill -f "serve_lora_openai.py --model-name ${MODEL_NAME}" || true
}
trap cleanup EXIT

cleanup

CUDA_VISIBLE_DEVICES=0 conda run -n qwen_sft python deployment/serve_lora_openai.py \
  --base-model "${BASE_MODEL}" \
  --adapter "${ADAPTER}" \
  --model-name "${MODEL_NAME}" \
  --port ${PORT} \
  --max-new-tokens-default 64 \
  --max-concurrent-generations 1 \
  > output/online_bench/logs/server_gate_3b.log 2>&1 &

# Domain-split + length-bucketed gate benchmark.
conda run -n qwen_sft python benchmarks/run_gate_benchmark_bucketed.py \
  --base-url http://127.0.0.1:${PORT} \
  --model "${MODEL_NAME}" \
  --internal-dataset "${INTERNAL_DATASET}" \
  --external-dataset "${EXTERNAL_DATASET}" \
  --requests-per-domain 120 \
  --concurrency 4 \
  --max-tokens 64 \
  --timeout-sec 180 \
  --health-timeout-sec 600 \
  --p95-threshold-sec 30 \
  --p99-threshold-sec 45 \
  --error-threshold 0.005 \
  --out-json output/online_bench/reports/gate_report_internal_external_3b.json \
  --out-md output/online_bench/reports/gate_report_internal_external_3b.md

echo "DONE: output/online_bench/reports/gate_report_internal_external_3b.md"
