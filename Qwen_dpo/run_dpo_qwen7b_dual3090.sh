#!/usr/bin/env bash
set -euo pipefail

# True dual-GPU DPO launch for Qwen2.5-7B (LoRA on top of SFT adapter)
ROOT="/mnt/public/zxs/course/DPO_qwen"
cd "$ROOT"

BASE_MODEL="/mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-7B-Instruct"
SFT_ADAPTER="/mnt/public/zxs/course/SFT_qwen/results/output/qwen2.5-7b-instruct_lora_run9_2/v0-20260329-164122/checkpoint-87"
TRAIN_JSONL="/mnt/public/zxs/course/DPO_qwen/datasets/dpo/qwen25_3b_dpo_from_aug_full455_train.jsonl"
EVAL_JSONL="/mnt/public/zxs/course/DPO_qwen/datasets/dpo/qwen25_3b_dpo_from_aug_full455_eval.jsonl"
OUT_DIR="/mnt/public/zxs/course/DPO_qwen/output/dpo_runs/qwen25_7b_from_sft_full455_dual3090_v1"

mkdir -p "$OUT_DIR"

# Close to 3B settings, but length trimmed for 7B stability on dual 24GB cards.
CUDA_VISIBLE_DEVICES=0,1 \
/home/zxs/anaconda3/envs/qwen_sft/bin/torchrun \
  --nproc_per_node=2 \
  --master_port=29608 \
  /mnt/public/zxs/course/DPO_qwen/train_dpo_from_sft.py \
  --base-model "$BASE_MODEL" \
  --sft-adapter "$SFT_ADAPTER" \
  --train-jsonl "$TRAIN_JSONL" \
  --eval-jsonl "$EVAL_JSONL" \
  --output-dir "$OUT_DIR" \
  --num-train-epochs 2 \
  --per-device-train-batch-size 1 \
  --per-device-eval-batch-size 1 \
  --gradient-accumulation-steps 8 \
  --learning-rate 5e-6 \
  --weight-decay 0.0 \
  --warmup-ratio 0.03 \
  --beta 0.1 \
  --max-prompt-length 512 \
  --max-length 768 \
  --logging-steps 5 \
  --eval-steps 50 \
  --save-steps 50 \
  --save-total-limit 3 \
  --seed 42 \
  --gradient-checkpointing

echo "DONE: $OUT_DIR"
