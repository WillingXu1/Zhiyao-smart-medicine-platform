#!/usr/bin/env bash
set -euo pipefail

cd /mnt/public/zxs/course/SFT_qwen
mkdir -p output/online_bench/logs output/online_bench/reports

BASE_MODEL="/mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-3B-Instruct"
ADAPTER="/mnt/public/zxs/course/SFT_qwen/output/ablation_qwen3b_replace/runs/qwen2.5-3b-instruct/v0-20260329-144508/checkpoint-87"
MODEL_ALIAS="medical"

INTERNAL_DATASET="datasets/json/dataset_internal_20_run9_1.json"
EXTERNAL_DATASET="datasets/json/dataset_external_v2_latest_run9_1.json"

REQUESTS_PER_DOMAIN="${REQUESTS_PER_DOMAIN:-120}"
CONCURRENCY="${CONCURRENCY:-8}"
MAX_TOKENS="${MAX_TOKENS:-384}"

# Eager and compile can have different memory behavior on 3090.
# Keep eager aggressive, compile conservative by default.
EAGER_GPU_MEM_UTIL="${EAGER_GPU_MEM_UTIL:-0.90}"
EAGER_MAX_NUM_SEQS="${EAGER_MAX_NUM_SEQS:-64}"
EAGER_MAX_BATCHED_TOKENS="${EAGER_MAX_BATCHED_TOKENS:-8192}"

COMPILE_GPU_MEM_UTIL="${COMPILE_GPU_MEM_UTIL:-0.82}"
COMPILE_MAX_NUM_SEQS="${COMPILE_MAX_NUM_SEQS:-24}"
COMPILE_MAX_BATCHED_TOKENS="${COMPILE_MAX_BATCHED_TOKENS:-4096}"

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

run_one_mode() {
  local mode="$1"
  local port="$2"
  local eager_flag="$3"
  local gpu_mem_util="$4"
  local max_num_seqs="$5"
  local max_batched_tokens="$6"
  local log_file="output/online_bench/logs/vllm_3b_${mode}.log"
  local out_json="output/online_bench/reports/gate_report_${mode}_3b_vllm.json"
  local out_md="output/online_bench/reports/gate_report_${mode}_3b_vllm.md"

  cleanup_port "${port}"
  pkill -f "vllm serve .*Qwen2.5-3B-Instruct" || true
  sleep 2

  CUDA_VISIBLE_DEVICES=0 /home/zxs/anaconda3/envs/qwen_sft/bin/vllm serve "${BASE_MODEL}" \
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

  for i in $(seq 1 240); do
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
  pkill -f "vllm serve .*Qwen2.5-3B-Instruct" || true
  sleep 2
}

# 1) eager baseline
run_one_mode "eager" 8001 "--enforce-eager" \
  "${EAGER_GPU_MEM_UTIL}" "${EAGER_MAX_NUM_SEQS}" "${EAGER_MAX_BATCHED_TOKENS}"

# 2) compile path (no --enforce-eager)
run_one_mode "compile" 8002 "" \
  "${COMPILE_GPU_MEM_UTIL}" "${COMPILE_MAX_NUM_SEQS}" "${COMPILE_MAX_BATCHED_TOKENS}"

# 3) merge compare report
/home/zxs/anaconda3/envs/qwen_sft/bin/python - <<'PY'
import json
from pathlib import Path

pe = Path('output/online_bench/reports/gate_report_eager_3b_vllm.json')
pc = Path('output/online_bench/reports/gate_report_compile_3b_vllm.json')
out_md = Path('output/online_bench/reports/gate_report_eager_vs_compile_3b_vllm.md')
out_json = Path('output/online_bench/reports/gate_report_eager_vs_compile_3b_vllm.json')

e = json.loads(pe.read_text(encoding='utf-8'))
c = json.loads(pc.read_text(encoding='utf-8'))

merged = {
  'eager': e,
  'compile': c,
}
out_json.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')

lines = []
lines.append('# Eager vs Compile 门禁对照（vLLM 3B + LoRA）')
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
lines.append(f"- overall_gate_eager: **{e['overall_gate']}**")
lines.append(f"- overall_gate_compile: **{c['overall_gate']}**")

out_md.write_text('\n'.join(lines), encoding='utf-8')
print('saved:', out_json)
print('saved:', out_md)
PY

echo "DONE: output/online_bench/reports/gate_report_eager_vs_compile_3b_vllm.md"


'''

#!/usr/bin/env bash
# 指定脚本使用 bash 解释器执行

set -euo pipefail
# -e: 任意命令失败立即退出
# -u: 使用未定义变量时报错
# -o pipefail: 管道中任一命令失败即整体失败

cd /mnt/public/zxs/course/SFT_qwen
# 切换到项目根目录，确保后续相对路径正确

mkdir -p output/online_bench/logs output/online_bench/reports
# 创建日志和报告输出目录（已存在也不报错）

BASE_MODEL="/mnt/public/zxs/course/SFT_qwen/TestModels/Qwen2.5-3B-Instruct"
# Base 模型路径（3B Instruct）

ADAPTER="/mnt/public/zxs/course/SFT_qwen/output/ablation_qwen3b_replace/runs/qwen2.5-3b-instruct/v0-20260329-144508/checkpoint-87"
# LoRA Adapter 路径（微调权重）

MODEL_ALIAS="medical"
# 给 LoRA 模块起一个别名，供请求时 model 字段使用

INTERNAL_DATASET="datasets/json/dataset_internal_20_run9_1.json"
# 内部评测数据集路径

EXTERNAL_DATASET="datasets/json/dataset_external_v2_latest_run9_1.json"
# 外部评测数据集路径

REQUESTS_PER_DOMAIN="${REQUESTS_PER_DOMAIN:-120}"
# 每个域（internal/external）请求总数，默认 120，可被环境变量覆盖

CONCURRENCY="${CONCURRENCY:-8}"
# 并发线程数，默认 8，可被环境变量覆盖

MAX_TOKENS="${MAX_TOKENS:-384}"
# 每次生成最大 token 数，默认 384

# Eager and compile can have different memory behavior on 3090.
# Keep eager aggressive, compile conservative by default.
# 注释：说明 3090 上 eager/compile 的显存行为不同
# 设计策略：eager 配置更激进，compile 更保守

EAGER_GPU_MEM_UTIL="${EAGER_GPU_MEM_UTIL:-0.90}"
# eager 模式 GPU 显存利用率上限，默认 0.90

EAGER_MAX_NUM_SEQS="${EAGER_MAX_NUM_SEQS:-64}"
# eager 模式最大并行序列数，默认 64

EAGER_MAX_BATCHED_TOKENS="${EAGER_MAX_BATCHED_TOKENS:-8192}"
# eager 模式单批最大 token 数，默认 8192

COMPILE_GPU_MEM_UTIL="${COMPILE_GPU_MEM_UTIL:-0.82}"
# compile 模式 GPU 显存利用率上限，默认 0.82（更保守）

COMPILE_MAX_NUM_SEQS="${COMPILE_MAX_NUM_SEQS:-24}"
# compile 模式最大并行序列数，默认 24

COMPILE_MAX_BATCHED_TOKENS="${COMPILE_MAX_BATCHED_TOKENS:-4096}"
# compile 模式单批最大 token 数，默认 4096

P95_SHORT="${P95_SHORT:-30}"
# short 桶 P95 阈值（秒）

P99_SHORT="${P99_SHORT:-45}"
# short 桶 P99 阈值（秒）

P95_MEDIUM="${P95_MEDIUM:-30}"
# medium 桶 P95 阈值（秒）

P99_MEDIUM="${P99_MEDIUM:-45}"
# medium 桶 P99 阈值（秒）

P95_LONG="${P95_LONG:-45}"
# long 桶 P95 阈值（秒）

P99_LONG="${P99_LONG:-60}"
# long 桶 P99 阈值（秒）

ERR_TH="${ERR_TH:-0.005}"
# 错误率阈值，默认 0.5%

cleanup_port() {
  # 定义函数：清理指定端口上正在监听的进程
  local port="$1"
  # 读取函数第一个参数，作为端口号

  local pid
  # 声明局部变量 pid

  pid=$(lsof -t -iTCP:${port} -sTCP:LISTEN -n -P || true)
  # 查找该端口 LISTEN 状态的进程 PID
  # 没找到时返回空（通过 || true 避免 set -e 中断）

  if [ -n "${pid}" ]; then
    # 若 pid 非空，说明端口被占用
    kill -9 ${pid} || true
    # 强制结束占用端口进程
  fi
}

run_one_mode() {
  # 定义函数：运行一次指定模式（eager 或 compile）的完整压测流程

  local mode="$1"
  # 模式名：eager 或 compile

  local port="$2"
  # 服务端口，如 8001/8002

  local eager_flag="$3"
  # 传给 vLLM 的模式开关（eager 时为 --enforce-eager，compile 时为空）

  local gpu_mem_util="$4"
  # 当前模式的显存利用率参数

  local max_num_seqs="$5"
  # 当前模式的最大并行序列数参数

  local max_batched_tokens="$6"
  # 当前模式的最大 batched tokens 参数

  local log_file="output/online_bench/logs/vllm_3b_${mode}.log"
  # 当前模式 vLLM 服务日志输出路径

  local out_json="output/online_bench/reports/gate_report_${mode}_3b_vllm.json"
  # 当前模式压测 JSON 报告输出路径

  local out_md="output/online_bench/reports/gate_report_${mode}_3b_vllm.md"
  # 当前模式压测 Markdown 报告输出路径

  cleanup_port "${port}"
  # 启动前先清理端口，避免端口冲突

  pkill -f "vllm serve .*Qwen2.5-3B-Instruct" || true
  # 兜底清理旧的 3B vLLM 进程

  sleep 2
  # 等待进程完全退出，避免残留占用

  CUDA_VISIBLE_DEVICES=0 /home/zxs/anaconda3/envs/qwen_sft/bin/vllm serve "${BASE_MODEL}" \
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
  # 在后台启动 vLLM OpenAI 兼容服务
  # 关键点：
  # 1) 固定用 GPU 0
  # 2) 加载 base + LoRA
  # 3) eager/compile 差异通过 eager_flag 和资源参数体现
  # 4) stdout/stderr 全写入日志文件

  for i in $(seq 1 240); do
    # 最多轮询 240 次（每次 2 秒，约 8 分钟）等待服务就绪

    if curl -sS --max-time 2 "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; then
      # 访问 /v1/models 成功即认为服务可用
      break
      # 跳出等待循环
    fi

    sleep 2
    # 未就绪就继续等待 2 秒
  done

  if ! curl -sS --max-time 3 "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; then
    # 轮询后再次确认；若仍不可用，判定启动失败

    echo "[ERROR] ${mode} server failed to start. tail log:"
    # 打印错误提示

    tail -n 120 "${log_file}" || true
    # 打印最后 120 行日志，便于排查

    return 1
    # 函数返回失败
  fi

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
  # 调用分桶门禁压测脚本：
  # 1) 对 internal/external 分域压测
  # 2) 对 short/medium/long 分桶统计
  # 3) 输出 JSON/MD 报告
  # 4) 按 P95/P99/错误率阈值做 PASS/FAIL 门禁

  cleanup_port "${port}"
  # 压测完成后清理端口

  pkill -f "vllm serve .*Qwen2.5-3B-Instruct" || true
  # 再次兜底清理 vLLM 进程

  sleep 2
  # 等待资源释放稳定
}

# 1) eager baseline
# 注释：先跑 eager 作为基线

run_one_mode "eager" 8001 "--enforce-eager" \
  "${EAGER_GPU_MEM_UTIL}" "${EAGER_MAX_NUM_SEQS}" "${EAGER_MAX_BATCHED_TOKENS}"
# 调用 eager 模式：
# 端口 8001，带 --enforce-eager，使用 eager 资源参数

# 2) compile path (no --enforce-eager)
# 注释：再跑 compile 路径，不传 --enforce-eager

run_one_mode "compile" 8002 "" \
  "${COMPILE_GPU_MEM_UTIL}" "${COMPILE_MAX_NUM_SEQS}" "${COMPILE_MAX_BATCHED_TOKENS}"
# 调用 compile 模式：
# 端口 8002，不传 eager flag，使用 compile 资源参数

# 3) merge compare report
# 注释：最后把 eager 与 compile 两份报告合并并生成对照表

/home/zxs/anaconda3/envs/qwen_sft/bin/python - <<'PY'
# 启动一个内联 Python 脚本（heredoc）

import json
# 导入 json 库

from pathlib import Path
# 导入 Path 处理文件路径

pe = Path('output/online_bench/reports/gate_report_eager_3b_vllm.json')
# eager JSON 报告路径

pc = Path('output/online_bench/reports/gate_report_compile_3b_vllm.json')
# compile JSON 报告路径

out_md = Path('output/online_bench/reports/gate_report_eager_vs_compile_3b_vllm.md')
# 对照 Markdown 输出路径

out_json = Path('output/online_bench/reports/gate_report_eager_vs_compile_3b_vllm.json')
# 对照 JSON 输出路径

e = json.loads(pe.read_text(encoding='utf-8'))
# 读取 eager 报告到对象 e

c = json.loads(pc.read_text(encoding='utf-8'))
# 读取 compile 报告到对象 c

merged = {
  'eager': e,
  'compile': c,
}
# 构造合并后的总对象

out_json.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
# 写入合并 JSON（保留中文，缩进美化）

lines = []
# 初始化 Markdown 行列表

lines.append('# Eager vs Compile 门禁对照（vLLM 3B + LoRA）')
# Markdown 标题

lines.append('')
# 空行分隔

lines.append('| Mode | Domain | QPS | Tokens/s | P95 E2E(s) | P99 E2E(s) | P95 TTFT(s) | Error Rate | Gate |')
# 表头：模式、域、吞吐、时延、错误率、门禁结果

lines.append('|---|---|---:|---:|---:|---:|---:|---:|---|')
# Markdown 表格对齐行

for mode, obj in [('eager', e), ('compile', c)]:
    # 外层循环：先 eager 再 compile
    for domain in ['internal', 'external']:
        # 内层循环：internal/external 两个域
        s = obj['domains'][domain]['summary']
        # 取该模式该域的 summary 指标
        lines.append(
            f"| {mode} | {domain} | {s['qps']:.3f} | {s['completion_tokens']['tokens_per_sec']:.3f} | {s['latency_e2e']['p95_sec']:.3f} | {s['latency_e2e']['p99_sec']:.3f} | {(s['latency_ttft']['p95_sec'] or 0):.3f} | {s['error_rate']:.2%} | {obj['domains'][domain]['gate']} |"
        )
        # 把该行写入表格：
        # QPS、tokens/s、P95/P99 E2E、P95 TTFT、错误率、门禁结论

lines.append('')
# 空行分隔

lines.append(f"- overall_gate_eager: **{e['overall_gate']}**")
# 追加 eager 总体门禁结论

lines.append(f"- overall_gate_compile: **{c['overall_gate']}**")
# 追加 compile 总体门禁结论

out_md.write_text('\n'.join(lines), encoding='utf-8')
# 写入最终 Markdown 对照报告

print('saved:', out_json)
# 打印 JSON 报告保存路径

print('saved:', out_md)
# 打印 Markdown 报告保存路径
PY
# 结束内联 Python 脚本

echo "DONE: output/online_bench/reports/gate_report_eager_vs_compile_3b_vllm.md"
# 打印完成提示，告诉你最终重点查看哪份报告

'''
