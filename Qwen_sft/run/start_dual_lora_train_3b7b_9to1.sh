#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p logs

chmod +x run/run_qwen3b_train_half_gpu0_9to1.sh run/run_qwen7b_train_gpu1_9to1.sh

nohup bash run/run_qwen3b_train_half_gpu0_9to1.sh > logs/train_qwen3b_9to1.log 2>&1 &
PID_3B=$!

nohup bash run/run_qwen7b_train_gpu1_9to1.sh > logs/train_qwen7b_9to1.log 2>&1 &
PID_7B=$!

cat > logs/train_dual_3b7b_9to1.pid <<EOF
3B_PID=${PID_3B}
7B_PID=${PID_7B}
EOF

echo "3B training started, PID=${PID_3B}, log=logs/train_qwen3b_9to1.log"
echo "7B training started, PID=${PID_7B}, log=logs/train_qwen7b_9to1.log"
echo "PID file saved: logs/train_dual_3b7b_9to1.pid"
