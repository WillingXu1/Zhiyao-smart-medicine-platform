#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=/mnt/public/zxs/course/SFT_qwen
SPLIT_REPORT=${1:-/mnt/public/zxs/course/SFT_qwen/data/datasets/json/splits/digestive_total_3716_split_9to1_report.json}
OLD_RUN_DIR=${2:-/mnt/public/zxs/course/SFT_qwen/results/output/retrain_4xa800_3716_9to1/retrain_4xa800_20260407-061649/qwen2.5-3b-instruct_lora/v0-20260407-061712}
RUN_ID=${RUN_ID:-compare3b_optimized_$(date +%Y%m%d-%H%M%S)}

# Optimized 3B defaults (override by env if needed).
THREEB_GRAD_ACC=${THREEB_GRAD_ACC:-8}
THREEB_LR=${THREEB_LR:-1.5e-05}
THREEB_WARMUP=${THREEB_WARMUP:-0.12}
THREEB_EVAL_SAVE_STEPS=${THREEB_EVAL_SAVE_STEPS:-10}
THREEB_EARLY_STOP_INTERVAL=${THREEB_EARLY_STOP_INTERVAL:-8}

RUN_ROOT="${ROOT_DIR}/results/output/retrain_4xa800_3716_9to1_3b_compare/${RUN_ID}"
LOG_DIR="${RUN_ROOT}/logs"
REPORT_DIR="${RUN_ROOT}/reports"
mkdir -p "${LOG_DIR}" "${REPORT_DIR}"

if [[ ! -f "${SPLIT_REPORT}" ]]; then
  echo "[ERROR] split report not found: ${SPLIT_REPORT}"
  exit 1
fi

if [[ ! -f "${OLD_RUN_DIR}/logging.jsonl" ]]; then
  echo "[ERROR] old run logging not found: ${OLD_RUN_DIR}/logging.jsonl"
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
  echo "[ERROR] failed to parse train/val from split report: ${SPLIT_REPORT}"
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
old_run_dir=${OLD_RUN_DIR}
gpus=0,1,2,3
env=qwen_sft
threeb_grad_acc=${THREEB_GRAD_ACC}
threeb_lr=${THREEB_LR}
threeb_warmup=${THREEB_WARMUP}
threeb_eval_save_steps=${THREEB_EVAL_SAVE_STEPS}
threeb_early_stop_interval=${THREEB_EARLY_STOP_INTERVAL}
EOF

echo "[$(date '+%F %T')] START 3B optimized compare run"
MASTER_PORT=29630 CUDA_VISIBLE_DEVICES=0,1,2,3 NPROC_PER_NODE=4 conda run -n qwen_sft swift sft \
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

NEW_RUN_DIR=$(ls -dt "${RUN_ROOT}/qwen2.5-3b-instruct_lora"/v0-* 2>/dev/null | head -n 1 || true)
if [[ -z "${NEW_RUN_DIR}" || ! -f "${NEW_RUN_DIR}/logging.jsonl" ]]; then
  echo "[ERROR] new run logging not found under ${RUN_ROOT}/qwen2.5-3b-instruct_lora"
  exit 1
fi

python3 - <<'PY' "${OLD_RUN_DIR}" "${NEW_RUN_DIR}" "${REPORT_DIR}"
import csv
import json
import os
import re
import sys

old_run, new_run, report_dir = sys.argv[1:4]
old_log = os.path.join(old_run, 'logging.jsonl')
new_log = os.path.join(new_run, 'logging.jsonl')

def parse_step(row):
    if isinstance(row.get('global_step'), int):
        return row['global_step']
    gsm = row.get('global_step/max_steps')
    if isinstance(gsm, str):
        m = re.match(r'\s*(\d+)\s*/\s*\d+\s*$', gsm)
        if m:
            return int(m.group(1))
    return None

def load_eval_points(path):
    points = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if 'eval_loss' in row:
                points.append({'step': parse_step(row), 'eval_loss': float(row['eval_loss'])})
    return points

def best_info(run_dir):
    latest_ts = None
    latest = None
    root = run_dir
    for name in os.listdir(root):
        if not name.startswith('checkpoint-'):
            continue
        p = os.path.join(root, name, 'trainer_state.json')
        if not os.path.isfile(p):
            continue
        mt = os.path.getmtime(p)
        if latest_ts is None or mt > latest_ts:
            latest_ts = mt
            latest = p
    if latest is None:
        return {'trainer_state': None, 'best_model_checkpoint': None, 'best_metric': None}
    with open(latest, 'r', encoding='utf-8') as f:
        j = json.load(f)
    return {
        'trainer_state': latest,
        'best_model_checkpoint': j.get('best_model_checkpoint'),
        'best_metric': j.get('best_metric'),
    }

old_eval = load_eval_points(old_log)
new_eval = load_eval_points(new_log)

rows = []
max_len = max(len(old_eval), len(new_eval))
for i in range(max_len):
    o = old_eval[i] if i < len(old_eval) else {'step': None, 'eval_loss': None}
    n = new_eval[i] if i < len(new_eval) else {'step': None, 'eval_loss': None}
    delta = None
    if o['eval_loss'] is not None and n['eval_loss'] is not None:
        delta = n['eval_loss'] - o['eval_loss']
    rows.append({
        'eval_idx': i + 1,
        'old_step': o['step'],
        'old_eval_loss': o['eval_loss'],
        'new_step': n['step'],
        'new_eval_loss': n['eval_loss'],
        'delta_new_minus_old': delta,
    })

def min_point(points):
    if not points:
        return {'step': None, 'eval_loss': None}
    x = min(points, key=lambda t: t['eval_loss'])
    return {'step': x['step'], 'eval_loss': x['eval_loss']}

def last_point(points):
    if not points:
        return {'step': None, 'eval_loss': None}
    x = points[-1]
    return {'step': x['step'], 'eval_loss': x['eval_loss']}

summary = {
    'old_run_dir': old_run,
    'new_run_dir': new_run,
    'old_eval_points': len(old_eval),
    'new_eval_points': len(new_eval),
    'old_best_eval': min_point(old_eval),
    'new_best_eval': min_point(new_eval),
    'old_last_eval': last_point(old_eval),
    'new_last_eval': last_point(new_eval),
    'improvement_best_eval_loss': (min_point(old_eval)['eval_loss'] - min_point(new_eval)['eval_loss']) if old_eval and new_eval else None,
    'improvement_last_eval_loss': (last_point(old_eval)['eval_loss'] - last_point(new_eval)['eval_loss']) if old_eval and new_eval else None,
    'new_best_checkpoint': best_info(new_run),
}

os.makedirs(report_dir, exist_ok=True)
json_path = os.path.join(report_dir, 'val_loss_compare_old_vs_new.json')
csv_path = os.path.join(report_dir, 'val_loss_compare_old_vs_new.csv')
md_path = os.path.join(report_dir, 'val_loss_compare_old_vs_new.md')

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump({'summary': summary, 'rows': rows}, f, ensure_ascii=False, indent=2)

with open(csv_path, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['eval_idx', 'old_step', 'old_eval_loss', 'new_step', 'new_eval_loss', 'delta_new_minus_old'])
    w.writeheader()
    for r in rows:
        w.writerow(r)

def fmt(v):
    if v is None:
        return ''
    if isinstance(v, float):
        return f'{v:.6f}'
    return str(v)

lines = []
lines.append('# Val Loss Compare (Old vs New 3B)')
lines.append('')
lines.append('## Summary')
lines.append('')
lines.append(f"- old_run_dir: {summary['old_run_dir']}")
lines.append(f"- new_run_dir: {summary['new_run_dir']}")
lines.append(f"- old_best_eval_loss: {fmt(summary['old_best_eval']['eval_loss'])} (step {fmt(summary['old_best_eval']['step'])})")
lines.append(f"- new_best_eval_loss: {fmt(summary['new_best_eval']['eval_loss'])} (step {fmt(summary['new_best_eval']['step'])})")
lines.append(f"- best_eval_improvement(old-new): {fmt(summary['improvement_best_eval_loss'])}")
lines.append(f"- old_last_eval_loss: {fmt(summary['old_last_eval']['eval_loss'])} (step {fmt(summary['old_last_eval']['step'])})")
lines.append(f"- new_last_eval_loss: {fmt(summary['new_last_eval']['eval_loss'])} (step {fmt(summary['new_last_eval']['step'])})")
lines.append(f"- last_eval_improvement(old-new): {fmt(summary['improvement_last_eval_loss'])}")
lines.append(f"- new_best_checkpoint: {summary['new_best_checkpoint'].get('best_model_checkpoint')}")
lines.append('')
lines.append('## Eval-by-Eval Table')
lines.append('')
lines.append('| Eval # | Old Step | Old Eval Loss | New Step | New Eval Loss | Delta (new-old) |')
lines.append('|---:|---:|---:|---:|---:|---:|')
for r in rows:
    lines.append(
        f"| {fmt(r['eval_idx'])} | {fmt(r['old_step'])} | {fmt(r['old_eval_loss'])} | {fmt(r['new_step'])} | {fmt(r['new_eval_loss'])} | {fmt(r['delta_new_minus_old'])} |"
    )

with open(md_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

print('saved:', json_path)
print('saved:', csv_path)
print('saved:', md_path)
print('new_best_checkpoint:', summary['new_best_checkpoint'].get('best_model_checkpoint'))
print('new_best_metric:', summary['new_best_checkpoint'].get('best_metric'))
PY

echo "[$(date '+%F %T')] DONE 3B compare run"
echo "[REPORT] ${REPORT_DIR}/val_loss_compare_old_vs_new.md"