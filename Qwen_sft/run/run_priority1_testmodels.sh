#!/usr/bin/env bash
set -euo pipefail

ROOT="/mnt/public/zxs/course/SFT_qwen"
LOG_DIR="$ROOT/output/ablation_3090/logs"
mkdir -p "$LOG_DIR" "$ROOT/TestModels"

cd "$ROOT/TestModels"

# Download models to the required local directory.
conda run -n qwen_sft modelscope download --model deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B --local_dir ./DeepSeek-R1-Distill-Qwen-1.5B
conda run -n qwen_sft modelscope download --model deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --local_dir ./DeepSeek-R1-Distill-Qwen-7B
conda run -n qwen_sft modelscope download --model THUDM/glm-4-1.5b-chat --local_dir ./GLM-4-1.5B-Chat

cd "$ROOT"

# Run ablation: reuse run9_2 for Qwen and train/eval the other three models.
conda run -n qwen_sft python run/run_ablation_3090_lora.py \
  --models-file configs/ablation_models_priority1_testmodels.json \
  --reuse-results-json configs/ablation_reuse_priority1.json \
  --dataset datasets/json/dataset_train_run9_2_mix_70_30_no_len_filter.json \
  --val-dataset datasets/json/dataset_internal_20_run9_1.json \
  --internal datasets/json/dataset_internal_20_run9_1.json \
  --external datasets/json/dataset_external_v2_latest_run9_1.json \
  --base-compare-model /mnt/public/zxs/course/SFT_qwen/Qwen2.5-1.5B-Instruct \
  --output-root output/ablation_3090_priority1_testmodels

echo "DONE_PRIORITY1_TESTMODELS"
