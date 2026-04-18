#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p output/ablation_qwen3b_replace/logs output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct

rm -f output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/*.jsonl
rm -f output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/extended_metrics_base_vs_qwen2.5-3b-instruct.json
rm -f output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/extended_metrics_base_vs_qwen2.5-3b-instruct.md
rm -f output/ablation_qwen3b_replace/logs/qwen3b_eval_gpu1_mem.csv
rm -f output/ablation_qwen3b_replace/logs/qwen3b_eval_summary.txt

start_ts=$(date +%s)
echo "[$(date '+%F %T')] START qwen3b eval fixed base"

(
  while true; do
    ts=$(date +%s)
    mem=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | sed -n '2p')
    util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | sed -n '2p')
    echo "$ts,$mem,$util"
    sleep 2
  done
) > output/ablation_qwen3b_replace/logs/qwen3b_eval_gpu1_mem.csv &
mon_pid=$!

CUDA_VISIBLE_DEVICES=1 conda run -n qwen_sft python eval/evaluate_base_vs_adapter.py \
  --base-model /mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-3B-Instruct \
  --adapter /mnt/public/zxs/course/SFT_qwen/output/ablation_qwen3b_replace/runs/qwen2.5-3b-instruct/v0-20260329-144508/checkpoint-87 \
  --adapter-tag qwen2.5-3b-instruct \
  --internal datasets/json/dataset_internal_20_run9_1.json \
  --external datasets/json/dataset_external_v2_latest_run9_1.json \
  --out-dir output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct \
  --max-new-tokens 128

conda run -n qwen_sft python eval/evaluate_metrics_extended.py \
  --internal-base output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/internal20_base.jsonl \
  --internal-new output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/internal20_qwen2.5-3b-instruct.jsonl \
  --external-base output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/external23_base.jsonl \
  --external-new output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/external23_qwen2.5-3b-instruct.jsonl \
  --out-json output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/extended_metrics_base_vs_qwen2.5-3b-instruct.json \
  --out-md output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/extended_metrics_base_vs_qwen2.5-3b-instruct.md \
  --internal-base-tag internal20_base \
  --internal-new-tag internal20_qwen2.5-3b-instruct \
  --external-base-tag external23_base \
  --external-new-tag external23_qwen2.5-3b-instruct

end_ts=$(date +%s)
kill "$mon_pid" 2>/dev/null || true
peak_mem=$(awk -F, 'BEGIN{m=0} {if($2+0>m)m=$2+0} END{print m}' output/ablation_qwen3b_replace/logs/qwen3b_eval_gpu1_mem.csv)
dur=$((end_ts-start_ts))
{
  echo "duration_sec=$dur"
  echo "peak_gpu_mem_mib=$peak_mem"
} > output/ablation_qwen3b_replace/logs/qwen3b_eval_summary.txt

echo "[$(date '+%F %T')] DONE qwen3b eval fixed base"
