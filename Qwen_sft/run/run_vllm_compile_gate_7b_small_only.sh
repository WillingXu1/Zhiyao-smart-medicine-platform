#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p output/online_bench/logs output/online_bench/reports

GPU_ID="${GPU_ID:-1}"
PORT="${PORT:-8012}"

BASE_MODEL="/mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-7B-Instruct"
ADAPTER="/mnt/public/zxs/course/SFT_qwen/output/qwen2.5-7b-instruct_lora_run9_2/v0-20260329-164122/checkpoint-87"
MODEL_ALIAS="medical7b"

LOG_FILE="output/online_bench/logs/vllm_7b_compile.log"
OUT_JSON="output/online_bench/reports/gate_report_compile_7b_vllm_small.json"
OUT_MD="output/online_bench/reports/gate_report_compile_7b_vllm_small.md"
MEM_CSV="output/online_bench/reports/gate_report_compile_7b_vllm_small_mem.csv"

pkill -f "vllm serve .*Qwen2.5-7B-Instruct|VLLM::EngineCore" || true
sleep 2

CUDA_VISIBLE_DEVICES="${GPU_ID}" /home/zxs/anaconda3/envs/qwen_sft/bin/vllm serve "${BASE_MODEL}" \
  --port "${PORT}" \
  --dtype float16 \
  --gpu-memory-utilization 0.72 \
  --max-model-len 2048 \
  --max-num-seqs 2 \
  --max-num-batched-tokens 512 \
  --enable-lora \
  --lora-modules "${MODEL_ALIAS}=${ADAPTER}" \
  > "${LOG_FILE}" 2>&1 &

for i in $(seq 1 360); do
  if curl -sS --max-time 2 "http://127.0.0.1:${PORT}/v1/models" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! curl -sS --max-time 3 "http://127.0.0.1:${PORT}/v1/models" >/dev/null 2>&1; then
  echo "[ERROR] compile server failed to start"
  tail -n 200 "${LOG_FILE}" || true
  exit 1
fi

nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits > "${MEM_CSV}" || true

/home/zxs/anaconda3/envs/qwen_sft/bin/python benchmarks/run_gate_benchmark_bucketed.py \
  --base-url "http://127.0.0.1:${PORT}" \
  --model "${MODEL_ALIAS}" \
  --internal-dataset "datasets/json/dataset_internal_20_run9_1.json" \
  --external-dataset "datasets/json/dataset_external_v2_latest_run9_1.json" \
  --requests-per-domain 100 \
  --concurrency 2 \
  --max-tokens 384 \
  --timeout-sec 300 \
  --health-timeout-sec 120 \
  --p95-threshold-short-sec 30 \
  --p99-threshold-short-sec 45 \
  --p95-threshold-medium-sec 30 \
  --p99-threshold-medium-sec 45 \
  --p95-threshold-long-sec 45 \
  --p99-threshold-long-sec 60 \
  --error-threshold 0.005 \
  --out-json "${OUT_JSON}" \
  --out-md "${OUT_MD}"

pkill -f "vllm serve .*Qwen2.5-7B-Instruct|VLLM::EngineCore" || true
echo "DONE: ${OUT_MD}"
