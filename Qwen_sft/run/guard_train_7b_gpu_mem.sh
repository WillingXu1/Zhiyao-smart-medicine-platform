#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p logs

MEM_LIMIT_MIB=${MEM_LIMIT_MIB:-23800}
CHECK_INTERVAL=${CHECK_INTERVAL:-20}
LOG_FILE=logs/guard_7b_gpu_mem.log

echo "[$(date '+%F %T')] guard started: MEM_LIMIT_MIB=${MEM_LIMIT_MIB}, CHECK_INTERVAL=${CHECK_INTERVAL}" >> "$LOG_FILE"

while true; do
  ts=$(date '+%F %T')
  mem=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | sed -n '2p' | tr -d ' ')
  util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | sed -n '2p' | tr -d ' ')
  echo "[$ts] gpu1_mem_mib=${mem} gpu1_util=${util}" >> "$LOG_FILE"

  # If 7B process disappeared or memory reaches critical zone, restart with safer config.
  if ! pgrep -f "qwen2.5-7b-instruct_lora_digestive_3716_9to1" >/dev/null 2>&1 || [[ "${mem}" -ge "${MEM_LIMIT_MIB}" ]]; then
    echo "[$ts] trigger fallback restart for 7B (process missing or memory >= ${MEM_LIMIT_MIB})" >> "$LOG_FILE"

    pkill -f "qwen2.5-7B-Instruct" >/dev/null 2>&1 || true
    pkill -f "run_qwen7b_train_gpu1_9to1" >/dev/null 2>&1 || true
    sleep 2

    nohup bash run/run_qwen7b_train_gpu1_9to1_safe.sh > logs/train_qwen7b_9to1_safe.log 2>&1 &
    new_pid=$!
    echo "[$(date '+%F %T')] restarted 7B safe mode pid=${new_pid}" >> "$LOG_FILE"
    break
  fi

  sleep "$CHECK_INTERVAL"
done
