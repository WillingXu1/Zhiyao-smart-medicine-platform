#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p output/online_bench/logs output/online_bench/reports

BASE_MODEL="/mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-7B-Instruct"
ADAPTER="/mnt/public/zxs/course/SFT_qwen/output/qwen2.5-7b-instruct_lora_run9_2/v0-20260329-164122/checkpoint-87"
MODEL_ALIAS="medical7b"
GPU_ID="${GPU_ID:-1}"

INTERNAL_DATASET="datasets/json/dataset_internal_20_run9_1.json"
EXTERNAL_DATASET="datasets/json/dataset_external_v2_latest_run9_1.json"

# Small-traffic defaults for 7B to keep test affordable and stable.
REQUESTS_PER_DOMAIN="${REQUESTS_PER_DOMAIN:-100}"
CONCURRENCY="${CONCURRENCY:-2}"
MAX_TOKENS="${MAX_TOKENS:-384}"

EAGER_GPU_MEM_UTIL="${EAGER_GPU_MEM_UTIL:-0.88}"
EAGER_MAX_NUM_SEQS="${EAGER_MAX_NUM_SEQS:-16}"
EAGER_MAX_BATCHED_TOKENS="${EAGER_MAX_BATCHED_TOKENS:-4096}"

COMPILE_GPU_MEM_UTIL="${COMPILE_GPU_MEM_UTIL:-0.82}"
COMPILE_MAX_NUM_SEQS="${COMPILE_MAX_NUM_SEQS:-8}"
COMPILE_MAX_BATCHED_TOKENS="${COMPILE_MAX_BATCHED_TOKENS:-2048}"

P95_SHORT="${P95_SHORT:-30}"
P99_SHORT="${P99_SHORT:-45}"
P95_MEDIUM="${P95_MEDIUM:-30}"
P99_MEDIUM="${P99_MEDIUM:-45}"
P95_LONG="${P95_LONG:-45}"
P99_LONG="${P99_LONG:-60}"
ERR_TH="${ERR_TH:-0.005}"

cleanup_port() {
  local port="$1"
  local pid
  pid=$(lsof -t -iTCP:${port} -sTCP:LISTEN -n -P || true)
  if [ -n "${pid}" ]; then
    kill -9 ${pid} || true
  fi
}

snapshot_mem() {
  local out_file="$1"
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits > "${out_file}" || true
}

run_one_mode() {
  local mode="$1"
  local port="$2"
  local eager_flag="$3"
  local gpu_mem_util="$4"
  local max_num_seqs="$5"
  local max_batched_tokens="$6"
  local log_file="output/online_bench/logs/vllm_7b_${mode}.log"
  local mem_file="output/online_bench/reports/gate_report_${mode}_7b_vllm_small_mem.csv"
  local out_json="output/online_bench/reports/gate_report_${mode}_7b_vllm_small.json"
  local out_md="output/online_bench/reports/gate_report_${mode}_7b_vllm_small.md"

  cleanup_port "${port}"
  pkill -f "vllm serve .*Qwen2.5-7B-Instruct" || true
  sleep 2

  CUDA_VISIBLE_DEVICES="${GPU_ID}" /home/zxs/anaconda3/envs/qwen_sft/bin/vllm serve "${BASE_MODEL}" \
    --port "${port}" \
    --dtype float16 \
    --gpu-memory-utilization "${gpu_mem_util}" \
    --max-model-len 4096 \
    --max-num-seqs "${max_num_seqs}" \
    --max-num-batched-tokens "${max_batched_tokens}" \
    --enable-lora \
    --lora-modules "${MODEL_ALIAS}=${ADAPTER}" \
    ${eager_flag} \
    > "${log_file}" 2>&1 &

  for i in $(seq 1 360); do
    if curl -sS --max-time 2 "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  if ! curl -sS --max-time 3 "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; then
    echo "[ERROR] ${mode} server failed to start. tail log:"
    tail -n 120 "${log_file}" || true
    return 1
  fi

  snapshot_mem "${mem_file}"

  /home/zxs/anaconda3/envs/qwen_sft/bin/python benchmarks/run_gate_benchmark_bucketed.py \
    --base-url "http://127.0.0.1:${port}" \
    --model "${MODEL_ALIAS}" \
    --internal-dataset "${INTERNAL_DATASET}" \
    --external-dataset "${EXTERNAL_DATASET}" \
    --requests-per-domain "${REQUESTS_PER_DOMAIN}" \
    --concurrency "${CONCURRENCY}" \
    --max-tokens "${MAX_TOKENS}" \
    --timeout-sec 300 \
    --health-timeout-sec 120 \
    --p95-threshold-short-sec "${P95_SHORT}" \
    --p99-threshold-short-sec "${P99_SHORT}" \
    --p95-threshold-medium-sec "${P95_MEDIUM}" \
    --p99-threshold-medium-sec "${P99_MEDIUM}" \
    --p95-threshold-long-sec "${P95_LONG}" \
    --p99-threshold-long-sec "${P99_LONG}" \
    --error-threshold "${ERR_TH}" \
    --out-json "${out_json}" \
    --out-md "${out_md}"

  cleanup_port "${port}"
  pkill -f "vllm serve .*Qwen2.5-7B-Instruct" || true
  sleep 2
}

run_one_mode "eager" 8011 "--enforce-eager" \
  "${EAGER_GPU_MEM_UTIL}" "${EAGER_MAX_NUM_SEQS}" "${EAGER_MAX_BATCHED_TOKENS}"

run_one_mode "compile" 8012 "" \
  "${COMPILE_GPU_MEM_UTIL}" "${COMPILE_MAX_NUM_SEQS}" "${COMPILE_MAX_BATCHED_TOKENS}"

/home/zxs/anaconda3/envs/qwen_sft/bin/python - <<'PY'
import csv
import json
from pathlib import Path

pe = Path('output/online_bench/reports/gate_report_eager_7b_vllm_small.json')
pc = Path('output/online_bench/reports/gate_report_compile_7b_vllm_small.json')
me = Path('output/online_bench/reports/gate_report_eager_7b_vllm_small_mem.csv')
mc = Path('output/online_bench/reports/gate_report_compile_7b_vllm_small_mem.csv')
out_md = Path('output/online_bench/reports/gate_report_eager_vs_compile_7b_vllm_small.md')
out_json = Path('output/online_bench/reports/gate_report_eager_vs_compile_7b_vllm_small.json')

e = json.loads(pe.read_text(encoding='utf-8'))
c = json.loads(pc.read_text(encoding='utf-8'))

def parse_mem(path: Path):
    if not path.exists():
        return None
    rows = list(csv.reader(path.read_text(encoding='utf-8').strip().splitlines()))
    if not rows:
        return None
    first = rows[0]
    if len(first) < 5:
        return None
    return {
        'gpu_index': first[0].strip(),
        'gpu_name': first[1].strip(),
        'memory_used_mib': float(first[2].strip()),
        'memory_total_mib': float(first[3].strip()),
        'utilization_gpu': float(first[4].strip()),
    }

mem_e = parse_mem(me)
mem_c = parse_mem(mc)

merged = {
    'eager': e,
    'compile': c,
    'memory_snapshot_mib': {
        'eager': mem_e,
        'compile': mem_c,
        'delta_compile_minus_eager': (
            (mem_c['memory_used_mib'] - mem_e['memory_used_mib'])
            if mem_e and mem_c else None
        )
    }
}
out_json.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')

lines = []
lines.append('# Eager vs Compile 门禁对照（vLLM 7B + LoRA，小流量）')
lines.append('')
lines.append('| Mode | Domain | QPS | Tokens/s | P95 E2E(s) | P99 E2E(s) | P95 TTFT(s) | Error Rate | Gate |')
lines.append('|---|---|---:|---:|---:|---:|---:|---:|---|')
for mode, obj in [('eager', e), ('compile', c)]:
    for domain in ['internal', 'external']:
        s = obj['domains'][domain]['summary']
        lines.append(
            f"| {mode} | {domain} | {s['qps']:.3f} | {s['completion_tokens']['tokens_per_sec']:.3f} | {s['latency_e2e']['p95_sec']:.3f} | {s['latency_e2e']['p99_sec']:.3f} | {(s['latency_ttft']['p95_sec'] or 0):.3f} | {s['error_rate']:.2%} | {obj['domains'][domain]['gate']} |"
        )

lines.append('')
if mem_e and mem_c:
    lines.append('| Mode | GPU Mem Used (MiB) | GPU Mem Total (MiB) |')
    lines.append('|---|---:|---:|')
    lines.append(f"| eager | {mem_e['memory_used_mib']:.0f} | {mem_e['memory_total_mib']:.0f} |")
    lines.append(f"| compile | {mem_c['memory_used_mib']:.0f} | {mem_c['memory_total_mib']:.0f} |")
    lines.append(f"- delta_mem_compile_minus_eager_mib: {mem_c['memory_used_mib'] - mem_e['memory_used_mib']:.0f}")
else:
    lines.append('- memory snapshot unavailable')

lines.append(f"- overall_gate_eager: **{e['overall_gate']}**")
lines.append(f"- overall_gate_compile: **{c['overall_gate']}**")

out_md.write_text('\n'.join(lines), encoding='utf-8')
print('saved:', out_json)
print('saved:', out_md)
PY

echo "DONE: output/online_bench/reports/gate_report_eager_vs_compile_7b_vllm_small.md"
