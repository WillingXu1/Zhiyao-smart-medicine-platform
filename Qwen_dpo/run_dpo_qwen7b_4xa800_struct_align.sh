#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/mnt/public/zxs/course/DPO_qwen"
DATA_DIR="${ROOT_DIR}/datasets/struct_align_run1"
TRAIN_JSONL="${DATA_DIR}/qwen7b_struct_align_train.jsonl"
EVAL_JSONL="${DATA_DIR}/qwen7b_struct_align_val.jsonl"

# Default: latest known SFT-7B adapter from run9_2. Can be overridden by env.
SFT_ADAPTER="${SFT_ADAPTER:-/mnt/public/zxs/course/SFT_qwen/results/output/qwen2.5-7b-instruct_lora_run9_2/v0-20260329-164122/checkpoint-87}"
BASE_MODEL="${BASE_MODEL:-/mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-7B-Instruct}"

RUN_ID="dpo_struct_align_7b_$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${ROOT_DIR}/output/${RUN_ID}"
LOG_PATH="${OUT_DIR}/train.log"

mkdir -p "${OUT_DIR}"

echo "[INFO] ROOT_DIR=${ROOT_DIR}"
echo "[INFO] SFT_ADAPTER=${SFT_ADAPTER}"
echo "[INFO] TRAIN_JSONL=${TRAIN_JSONL}"
echo "[INFO] EVAL_JSONL=${EVAL_JSONL}"
echo "[INFO] OUT_DIR=${OUT_DIR}"

if [[ ! -f "${TRAIN_JSONL}" ]]; then
  echo "[ERROR] missing train jsonl: ${TRAIN_JSONL}" >&2
  exit 1
fi
if [[ ! -f "${EVAL_JSONL}" ]]; then
  echo "[ERROR] missing eval jsonl: ${EVAL_JSONL}" >&2
  exit 1
fi
if [[ ! -d "${SFT_ADAPTER}" ]]; then
  echo "[ERROR] missing sft adapter dir: ${SFT_ADAPTER}" >&2
  exit 1
fi

cd "${ROOT_DIR}"

# Conservative first run to validate stability on 4xA800.
nohup /home/zxs/anaconda3/bin/conda run -n qwen_sft \
  torchrun --nproc_per_node=4 train_dpo_from_sft.py \
  --base-model "${BASE_MODEL}" \
  --sft-adapter "${SFT_ADAPTER}" \
  --train-jsonl "${TRAIN_JSONL}" \
  --eval-jsonl "${EVAL_JSONL}" \
  --output-dir "${OUT_DIR}" \
  --num-train-epochs 1.0 \
  --per-device-train-batch-size 1 \
  --per-device-eval-batch-size 1 \
  --gradient-accumulation-steps 8 \
  --learning-rate 5e-6 \
  --beta 0.1 \
  --max-prompt-length 768 \
  --max-length 1024 \
  --logging-steps 5 \
  --eval-steps 25 \
  --save-steps 25 \
  --save-total-limit 3 \
  --gradient-checkpointing \
  > "${LOG_PATH}" 2>&1 &

echo "[OK] DPO started in background."
echo "[OK] LOG_PATH=${LOG_PATH}"
echo "[OK] OUT_DIR=${OUT_DIR}"
