#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p output/online_bench/logs output/online_bench/reports

DATASET="datasets/json/dataset_internal_20_run9_1.json"
MAX_TOKENS="${MAX_TOKENS:-384}"

cleanup() {
  pkill -f "serve_lora_openai.py --model-name qwen2.5-3b-medical" || true
  pkill -f "serve_lora_openai.py --model-name qwen2.5-7b-medical" || true
}
trap cleanup EXIT

cleanup

# 1) 3B main load test
CUDA_VISIBLE_DEVICES=0 conda run -n qwen_sft python deployment/serve_lora_openai.py \
  --base-model /mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-3B-Instruct \
  --adapter /mnt/public/zxs/course/SFT_qwen/output/ablation_qwen3b_replace/runs/qwen2.5-3b-instruct/v0-20260329-144508/checkpoint-87 \
  --model-name qwen2.5-3b-medical \
  --port 8103 \
  --max-new-tokens-default "$MAX_TOKENS" \
  --max-concurrent-generations 1 \
  --enable-cuda-graph true \
  > output/online_bench/logs/server_3b.log 2>&1 &
PID3B=$!
echo "$PID3B" > output/online_bench/logs/server_3b.pid

conda run -n qwen_sft python benchmarks/run_load_benchmark.py \
  --base-url http://127.0.0.1:8103 \
  --model qwen2.5-3b-medical \
  --dataset "$DATASET" \
  --prompt-limit 20 \
  --concurrency 1,2,4,8 \
  --requests-per-concurrency 40 \
  --max-tokens "$MAX_TOKENS" \
  --timeout-sec 180 \
  --health-timeout-sec 600 \
  --out-json output/online_bench/reports/bench_3b.json \
  --out-md output/online_bench/reports/bench_3b.md

kill "$PID3B" || true
sleep 3

# 2) 7B low-traffic comparison
CUDA_VISIBLE_DEVICES=0 conda run -n qwen_sft python deployment/serve_lora_openai.py \
  --base-model /mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-7B-Instruct \
  --adapter /mnt/public/zxs/course/SFT_qwen/output/qwen2.5-7b-instruct_lora_run9_2/v0-20260329-164122/checkpoint-87 \
  --model-name qwen2.5-7b-medical \
  --port 8107 \
  --max-new-tokens-default "$MAX_TOKENS" \
  --max-concurrent-generations 1 \
  --enable-cuda-graph true \
  > output/online_bench/logs/server_7b.log 2>&1 &
PID7B=$!
echo "$PID7B" > output/online_bench/logs/server_7b.pid

conda run -n qwen_sft python benchmarks/run_load_benchmark.py \
  --base-url http://127.0.0.1:8107 \
  --model qwen2.5-7b-medical \
  --dataset "$DATASET" \
  --prompt-limit 20 \
  --concurrency 1,2,4 \
  --requests-per-concurrency 24 \
  --max-tokens "$MAX_TOKENS" \
  --timeout-sec 180 \
  --health-timeout-sec 900 \
  --out-json output/online_bench/reports/bench_7b_small.json \
  --out-md output/online_bench/reports/bench_7b_small.md

kill "$PID7B" || true
sleep 2

# 3) Merge summary table
conda run -n qwen_sft python - <<'PY'
import json
from pathlib import Path

p3 = Path('output/online_bench/reports/bench_3b.json')
p7 = Path('output/online_bench/reports/bench_7b_small.json')
j3 = json.loads(p3.read_text(encoding='utf-8'))
j7 = json.loads(p7.read_text(encoding='utf-8'))

rows = []
for r in j3['results']:
    rows.append({
        'model': '3B',
        'concurrency': r['concurrency'],
        'qps': r['qps'],
        'p95': r['latency']['p95_sec'],
        'p99': r['latency']['p99_sec'],
        'error_rate': r['error_rate'],
    })
for r in j7['results']:
    rows.append({
        'model': '7B',
        'concurrency': r['concurrency'],
        'qps': r['qps'],
        'p95': r['latency']['p95_sec'],
        'p99': r['latency']['p99_sec'],
        'error_rate': r['error_rate'],
    })

out_json = Path('output/online_bench/reports/bench_compare_summary.json')
out_md = Path('output/online_bench/reports/bench_compare_summary.md')
out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')

lines = []
lines.append('# Online Stress Compare (3B vs 7B)')
lines.append('')
lines.append('| Model | Concurrency | QPS | P95(s) | P99(s) | Error Rate |')
lines.append('|---|---:|---:|---:|---:|---:|')
for x in rows:
    lines.append(f"| {x['model']} | {x['concurrency']} | {x['qps']:.3f} | {x['p95']:.3f} | {x['p99']:.3f} | {x['error_rate']:.2%} |")

# Same-concurrency value analysis where available
c3 = {x['concurrency']: x for x in rows if x['model'] == '3B'}
c7 = {x['concurrency']: x for x in rows if x['model'] == '7B'}
commons = sorted(set(c3) & set(c7))
if commons:
    lines.append('')
    lines.append('## 7B value over 3B (same concurrency)')
    lines.append('')
    lines.append('| Concurrency | QPS Ratio(7B/3B) | P95 Delta(s,7B-3B) | P99 Delta(s,7B-3B) |')
    lines.append('|---:|---:|---:|---:|')
    for c in commons:
        qps_ratio = (c7[c]['qps'] / c3[c]['qps']) if c3[c]['qps'] > 0 else 0.0
        p95_delta = c7[c]['p95'] - c3[c]['p95']
        p99_delta = c7[c]['p99'] - c3[c]['p99']
        lines.append(f"| {c} | {qps_ratio:.3f} | {p95_delta:.3f} | {p99_delta:.3f} |")

out_md.write_text('\n'.join(lines), encoding='utf-8')
print('saved:', out_json)
print('saved:', out_md)
PY

echo "DONE: output/online_bench/reports/bench_compare_summary.md"
