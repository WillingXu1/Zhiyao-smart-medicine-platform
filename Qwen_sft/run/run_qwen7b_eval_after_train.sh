#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p output/qwen2.5-7b-instruct_lora_run9_2 output/eval_qwen2.5-7b-instruct_run9_2

# Wait for final checkpoint from training run
while true; do
  ckpt=$(ls -d output/qwen2.5-7b-instruct_lora_run9_2/v0-*/checkpoint-87 2>/dev/null | sort -V | tail -n 1 || true)
  if [[ -n "${ckpt}" ]]; then
    break
  fi
  sleep 20
done

start_ts=$(date +%s)
echo "[$(date '+%F %T')] START qwen7b eval using checkpoint: $ckpt"

(
  while true; do
    ts=$(date +%s)
    mem=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | sed -n '1p')
    util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | sed -n '1p')
    echo "$ts,$mem,$util"
    sleep 2
  done
) > output/eval_qwen2.5-7b-instruct_run9_2/gpu0_mem.csv &
mon_pid=$!

CUDA_VISIBLE_DEVICES=0 conda run -n qwen_sft python eval/evaluate_base_vs_adapter.py \
  --base-model /mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-7B-Instruct \
  --adapter "$ckpt" \
  --adapter-tag qwen2.5-7b-instruct \
  --internal datasets/json/dataset_internal_20_run9_1.json \
  --external datasets/json/dataset_external_v2_latest_run9_1.json \
  --out-dir output/eval_qwen2.5-7b-instruct_run9_2 \
  --max-new-tokens 128

conda run -n qwen_sft python eval/evaluate_metrics_extended.py \
  --internal-base output/eval_qwen2.5-7b-instruct_run9_2/internal20_base.jsonl \
  --internal-new output/eval_qwen2.5-7b-instruct_run9_2/internal20_qwen2.5-7b-instruct.jsonl \
  --external-base output/eval_qwen2.5-7b-instruct_run9_2/external23_base.jsonl \
  --external-new output/eval_qwen2.5-7b-instruct_run9_2/external23_qwen2.5-7b-instruct.jsonl \
  --out-json output/eval_qwen2.5-7b-instruct_run9_2/extended_metrics_base_vs_qwen2.5-7b-instruct.json \
  --out-md output/eval_qwen2.5-7b-instruct_run9_2/extended_metrics_base_vs_qwen2.5-7b-instruct.md \
  --internal-base-tag internal20_base \
  --internal-new-tag internal20_qwen2.5-7b-instruct \
  --external-base-tag external23_base \
  --external-new-tag external23_qwen2.5-7b-instruct

end_ts=$(date +%s)
kill "$mon_pid" 2>/dev/null || true
peak_mem=$(awk -F, 'BEGIN{m=0} {if($2+0>m)m=$2+0} END{print m}' output/eval_qwen2.5-7b-instruct_run9_2/gpu0_mem.csv)
dur=$((end_ts-start_ts))
{
  echo "duration_sec=$dur"
  echo "peak_gpu_mem_mib=$peak_mem"
} > output/eval_qwen2.5-7b-instruct_run9_2/eval_summary.txt

echo "[$(date '+%F %T')] DONE qwen7b eval"
