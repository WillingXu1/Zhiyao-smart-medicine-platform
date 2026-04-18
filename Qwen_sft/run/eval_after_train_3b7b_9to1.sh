#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p output/eval_digestive_3b7b_9to1

INTERNAL=/mnt/public/zxs/course/SFT_qwen/datasets/json/dataset_internal_20_run9_1.json
EXTERNAL=/mnt/public/zxs/course/SFT_qwen/datasets/json/dataset_external_v2_latest_run9_1.json

find_latest_ckpt() {
  local run_dir="$1"
  ls -d "${run_dir}"/v*/checkpoint-* 2>/dev/null | sort -V | tail -n 1 || true
}

wait_ckpt() {
  local run_dir="$1"
  local name="$2"
  local ckpt=""
  while true; do
    ckpt=$(find_latest_ckpt "$run_dir")
    if [[ -n "${ckpt}" ]]; then
      echo "${ckpt}"
      return
    fi
    echo "[$(date '+%F %T')] waiting ${name} checkpoint in ${run_dir}"
    sleep 60
  done
}

RUN3B=/mnt/public/zxs/course/SFT_qwen/output/qwen2.5-3b-instruct_lora_digestive_3716_9to1_half3090
RUN7B=/mnt/public/zxs/course/SFT_qwen/output/qwen2.5-7b-instruct_lora_digestive_3716_9to1
RUN7B_SAFE=/mnt/public/zxs/course/SFT_qwen/output/qwen2.5-7b-instruct_lora_digestive_3716_9to1_safe
RUN7B_DUAL=/mnt/public/zxs/course/SFT_qwen/output/qwen2.5-7b-instruct_lora_digestive_3716_9to1_dual

# Wait until training processes fully exit, then evaluate the best/latest checkpoints.
while pgrep -f "qwen2.5-3b-instruct_lora_digestive_3716_9to1_half3090|qwen2.5-7b-instruct_lora_digestive_3716_9to1|qwen2.5-7b-instruct_lora_digestive_3716_9to1_safe|qwen2.5-7b-instruct_lora_digestive_3716_9to1_dual" >/dev/null 2>&1; do
  echo "[$(date '+%F %T')] training still running, wait before eval..."
  sleep 60
done

CKPT3B=$(wait_ckpt "$RUN3B" "3B")

CKPT7B=$(find_latest_ckpt "$RUN7B")
if [[ -z "${CKPT7B}" ]]; then
  CKPT7B=$(find_latest_ckpt "$RUN7B_SAFE")
fi
if [[ -z "${CKPT7B}" ]]; then
  CKPT7B=$(find_latest_ckpt "$RUN7B_DUAL")
fi
if [[ -z "${CKPT7B}" ]]; then
  CKPT7B=$(wait_ckpt "$RUN7B" "7B")
fi

echo "3B ckpt: ${CKPT3B}"
echo "7B ckpt: ${CKPT7B}"

CUDA_VISIBLE_DEVICES=0 conda run -n qwen_sft python eval/evaluate_base_vs_adapter.py \
  --base-model /mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-3B-Instruct \
  --adapter "${CKPT3B}" \
  --adapter-tag qwen2.5-3b-digestive-9to1 \
  --internal "${INTERNAL}" \
  --external "${EXTERNAL}" \
  --out-dir output/eval_digestive_3b7b_9to1/qwen2.5-3b \
  --max-new-tokens 128

conda run -n qwen_sft python eval/evaluate_metrics_extended.py \
  --internal-base output/eval_digestive_3b7b_9to1/qwen2.5-3b/internal20_base.jsonl \
  --internal-new output/eval_digestive_3b7b_9to1/qwen2.5-3b/internal20_qwen2.5-3b-digestive-9to1.jsonl \
  --external-base output/eval_digestive_3b7b_9to1/qwen2.5-3b/external23_base.jsonl \
  --external-new output/eval_digestive_3b7b_9to1/qwen2.5-3b/external23_qwen2.5-3b-digestive-9to1.jsonl \
  --out-json output/eval_digestive_3b7b_9to1/qwen2.5-3b/extended_metrics.json \
  --out-md output/eval_digestive_3b7b_9to1/qwen2.5-3b/extended_metrics.md \
  --internal-base-tag internal20_base \
  --internal-new-tag internal20_qwen2.5-3b-digestive-9to1 \
  --external-base-tag external23_base \
  --external-new-tag external23_qwen2.5-3b-digestive-9to1

CUDA_VISIBLE_DEVICES=1 conda run -n qwen_sft python eval/evaluate_base_vs_adapter.py \
  --base-model /mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-7B-Instruct \
  --adapter "${CKPT7B}" \
  --adapter-tag qwen2.5-7b-digestive-9to1 \
  --internal "${INTERNAL}" \
  --external "${EXTERNAL}" \
  --out-dir output/eval_digestive_3b7b_9to1/qwen2.5-7b \
  --max-new-tokens 128

conda run -n qwen_sft python eval/evaluate_metrics_extended.py \
  --internal-base output/eval_digestive_3b7b_9to1/qwen2.5-7b/internal20_base.jsonl \
  --internal-new output/eval_digestive_3b7b_9to1/qwen2.5-7b/internal20_qwen2.5-7b-digestive-9to1.jsonl \
  --external-base output/eval_digestive_3b7b_9to1/qwen2.5-7b/external23_base.jsonl \
  --external-new output/eval_digestive_3b7b_9to1/qwen2.5-7b/external23_qwen2.5-7b-digestive-9to1.jsonl \
  --out-json output/eval_digestive_3b7b_9to1/qwen2.5-7b/extended_metrics.json \
  --out-md output/eval_digestive_3b7b_9to1/qwen2.5-7b/extended_metrics.md \
  --internal-base-tag internal20_base \
  --internal-new-tag internal20_qwen2.5-7b-digestive-9to1 \
  --external-base-tag external23_base \
  --external-new-tag external23_qwen2.5-7b-digestive-9to1

echo "[$(date '+%F %T')] eval complete: output/eval_digestive_3b7b_9to1"
