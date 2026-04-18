#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p output/qwen2.5-7b-instruct_lora_digestive_3716_9to1_safe
mkdir -p logs

# Safer fallback config for single 3090 when memory is tight.
CUDA_VISIBLE_DEVICES=1 conda run -n qwen_sft swift sft \
  --model /mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-7B-Instruct \
  --dataset /mnt/public/zxs/course/SFT_qwen/data/datasets/json/splits/digestive_total_3716_train_3344_9to1.json \
  --val_dataset /mnt/public/zxs/course/SFT_qwen/data/datasets/json/splits/digestive_total_3716_val_372_9to1.json \
  --split_dataset_ratio 0 \
  --output_dir /mnt/public/zxs/course/SFT_qwen/output/qwen2.5-7b-instruct_lora_digestive_3716_9to1_safe \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 32 \
  --num_train_epochs 3 \
  --learning_rate 2e-05 \
  --lr_scheduler_type cosine \
  --warmup_ratio 0.1 \
  --weight_decay 0.1 \
  --max_length 768 \
  --fp16 true --bf16 false --gradient_checkpointing true \
  --eval_steps 20 --save_steps 20 --save_total_limit 3 \
  --load_best_model_at_end true --metric_for_best_model loss --greater_is_better false \
  --logging_steps 5 --seed 42 \
  --tuner_backend peft --tuner_type lora \
  --lora_rank 16 --lora_alpha 32 --lora_dropout 0.05 --target_modules all-linear
