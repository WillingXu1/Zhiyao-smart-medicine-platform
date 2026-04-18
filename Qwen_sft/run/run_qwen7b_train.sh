#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p output/qwen2.5-7b-instruct_lora_run9_2

CUDA_VISIBLE_DEVICES=0 conda run -n qwen_sft swift sft \
  --model /mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-7B-Instruct \
  --dataset datasets/json/dataset_train_run9_2_mix_70_30_no_len_filter.json \
  --val_dataset datasets/json/dataset_internal_20_run9_1.json \
  --split_dataset_ratio 0 \
  --output_dir output/qwen2.5-7b-instruct_lora_run9_2 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 16 \
  --num_train_epochs 3 \
  --learning_rate 2e-05 \
  --lr_scheduler_type cosine \
  --warmup_ratio 0.1 \
  --weight_decay 0.1 \
  --max_length 1024 \
  --fp16 true --bf16 false --gradient_checkpointing true \
  --eval_steps 10 --save_steps 10 --save_total_limit 3 \
  --load_best_model_at_end true --metric_for_best_model loss --greater_is_better false \
  --logging_steps 5 --seed 42 \
  --tuner_backend peft --tuner_type lora \
  --lora_rank 16 --lora_alpha 32 --lora_dropout 0.05 --target_modules all-linear
