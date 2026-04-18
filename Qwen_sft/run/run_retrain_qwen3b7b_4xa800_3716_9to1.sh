#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=/mnt/public/zxs/course/SFT_qwen
SPLIT_REPORT=${1:-/mnt/public/zxs/course/SFT_qwen/data/datasets/json/splits/digestive_total_3716_split_9to1_report.json}
RUN_ID=${RUN_ID:-$(date +%Y%m%d-%H%M%S)}

# 3B stability-focused defaults for future reruns; can be overridden via env vars.
THREEB_GRAD_ACC=${THREEB_GRAD_ACC:-8}
THREEB_LR=${THREEB_LR:-1.5e-05}
THREEB_WARMUP=${THREEB_WARMUP:-0.12}
THREEB_EVAL_SAVE_STEPS=${THREEB_EVAL_SAVE_STEPS:-10}
THREEB_EARLY_STOP_INTERVAL=${THREEB_EARLY_STOP_INTERVAL:-8}

# Keep this run fully isolated from previous experiments.
RUN_ROOT="${ROOT_DIR}/results/output/retrain_4xa800_3716_9to1/${RUN_ID}"
LOG_DIR="${RUN_ROOT}/logs"
mkdir -p "${LOG_DIR}"

if [[ ! -f "${SPLIT_REPORT}" ]]; then
  echo "[ERROR] split report not found: ${SPLIT_REPORT}"
  exit 1
fi

TRAIN_JSON=$(python3 - <<'PY' "${SPLIT_REPORT}"
import json, sys
p = sys.argv[1]
with open(p, 'r', encoding='utf-8') as f:
    j = json.load(f)
print(j.get('output', {}).get('train', ''))
PY
)

VAL_JSON=$(python3 - <<'PY' "${SPLIT_REPORT}"
import json, sys
p = sys.argv[1]
with open(p, 'r', encoding='utf-8') as f:
    j = json.load(f)
print(j.get('output', {}).get('val', ''))
PY
)

if [[ -z "${TRAIN_JSON}" || -z "${VAL_JSON}" ]]; then
  echo "[ERROR] failed to parse train/val paths from split report: ${SPLIT_REPORT}"
  exit 1
fi

if [[ ! -f "${TRAIN_JSON}" || ! -f "${VAL_JSON}" ]]; then
  echo "[ERROR] dataset file missing"
  echo "  train=${TRAIN_JSON}"
  echo "  val=${VAL_JSON}"
  exit 1
fi

cd "${ROOT_DIR}"

cat > "${RUN_ROOT}/run_meta.txt" <<EOF
run_id=${RUN_ID}
split_report=${SPLIT_REPORT}
train_json=${TRAIN_JSON}
val_json=${VAL_JSON}
gpus=0,1,2,3
env=qwen_sft
threeb_grad_acc=${THREEB_GRAD_ACC}
threeb_lr=${THREEB_LR}
threeb_warmup=${THREEB_WARMUP}
threeb_eval_save_steps=${THREEB_EVAL_SAVE_STEPS}
threeb_early_stop_interval=${THREEB_EARLY_STOP_INTERVAL}
EOF

echo "[$(date '+%F %T')] START 3B retrain on 4xA800"
MASTER_PORT=29610 CUDA_VISIBLE_DEVICES=0,1,2,3 NPROC_PER_NODE=4 conda run -n qwen_sft swift sft \
  --model /mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-3B-Instruct \
  --dataset "${TRAIN_JSON}" \
  --val_dataset "${VAL_JSON}" \
  --split_dataset_ratio 0 \
  --output_dir "${RUN_ROOT}/qwen2.5-3b-instruct_lora" \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps "${THREEB_GRAD_ACC}" \
  --num_train_epochs 3 \
  --learning_rate "${THREEB_LR}" \
  --lr_scheduler_type cosine \
  --warmup_ratio "${THREEB_WARMUP}" \
  --weight_decay 0.1 \
  --max_length 768 \
  --fp16 true --bf16 false --gradient_checkpointing true \
  --eval_steps "${THREEB_EVAL_SAVE_STEPS}" --save_steps "${THREEB_EVAL_SAVE_STEPS}" --save_total_limit 4 \
  --early_stop_interval "${THREEB_EARLY_STOP_INTERVAL}" \
  --load_best_model_at_end true --metric_for_best_model loss --greater_is_better false \
  --logging_steps 5 --seed 42 \
  --tuner_backend peft --tuner_type lora \
  --lora_rank 16 --lora_alpha 32 --lora_dropout 0.05 --target_modules all-linear \
  2>&1 | tee "${LOG_DIR}/train_qwen3b.log"

echo "[$(date '+%F %T')] START 7B retrain on 4xA800"
MASTER_PORT=29620 CUDA_VISIBLE_DEVICES=0,1,2,3 NPROC_PER_NODE=4 conda run -n qwen_sft swift sft \
  --model /mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-7B-Instruct \
  --dataset "${TRAIN_JSON}" \
  --val_dataset "${VAL_JSON}" \
  --split_dataset_ratio 0 \
  --output_dir "${RUN_ROOT}/qwen2.5-7b-instruct_lora" \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 4 \
  --num_train_epochs 3 \
  --learning_rate 2e-05 \
  --lr_scheduler_type cosine \
  --warmup_ratio 0.1 \
  --weight_decay 0.1 \
  --max_length 1024 \
  --fp16 true --bf16 false --gradient_checkpointing true \
  --eval_steps 20 --save_steps 20 --save_total_limit 3 \
  --load_best_model_at_end true --metric_for_best_model loss --greater_is_better false \
  --logging_steps 5 --seed 42 \
  --tuner_backend peft --tuner_type lora \
  --lora_rank 16 --lora_alpha 32 --lora_dropout 0.05 --target_modules all-linear \
  2>&1 | tee "${LOG_DIR}/train_qwen7b.log"

echo "[$(date '+%F %T')] DONE retrain, outputs under: ${RUN_ROOT}"