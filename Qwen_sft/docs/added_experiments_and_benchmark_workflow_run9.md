# Run9 新增内容全流程记录（横向实验 + 压测任务）

## 1. 本次新增内容范围

本次新增包含两大块：

1. 模型横向对比实验（同口径）
- 修正 Qwen2.5-3B 评测 base 后重新评测
- 新增 Qwen2.5-7B 训练与评测
- 与既有 1.5B 与 DeepSeek1.5B 结果统一到同一比较框架

2. 系统压测任务
- 3B 主压测（并发/QPS/P95/P99/错误率）
- 7B 小流量对照压测
- 评估 7B 的额外显存成本是否值得

## 2. 横向实验流程（离线质量）

### 2.1 统一评测口径

- 统一 internal 与 external 数据
- 统一输出格式：base/new 两组 jsonl
- 统一指标汇总：extended_metrics_base_vs_xxx.json

核心评测脚本：
- [evaluate_base_vs_adapter.py](evaluate_base_vs_adapter.py)
- [evaluate_metrics_extended.py](evaluate_metrics_extended.py)

### 2.2 Qwen2.5-3B 修正评测

背景：早期存在 base-adapter 架构不匹配，导致加载失败。后续改为正确 3B base 重新跑通。

执行脚本：
- [run_qwen3b_eval_fixed_base.sh](run_qwen3b_eval_fixed_base.sh)

产物：
- [output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/extended_metrics_base_vs_qwen2.5-3b-instruct.json](output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/extended_metrics_base_vs_qwen2.5-3b-instruct.json)
- [output/ablation_qwen3b_replace/logs/qwen3b_eval_summary.txt](output/ablation_qwen3b_replace/logs/qwen3b_eval_summary.txt)

### 2.3 Qwen2.5-7B 新增训练与评测

训练脚本：
- [run_qwen7b_train.sh](run_qwen7b_train.sh)

训练完成产物（checkpoint-87）：
- [output/qwen2.5-7b-instruct_lora_run9_2/train.log](output/qwen2.5-7b-instruct_lora_run9_2/train.log)

评测脚本（训练后自动触发）：
- [run_qwen7b_eval_after_train.sh](run_qwen7b_eval_after_train.sh)

评测产物：
- [output/eval_qwen2.5-7b-instruct_run9_2/extended_metrics_base_vs_qwen2.5-7b-instruct.json](output/eval_qwen2.5-7b-instruct_run9_2/extended_metrics_base_vs_qwen2.5-7b-instruct.json)
- [output/eval_qwen2.5-7b-instruct_run9_2/eval_summary.txt](output/eval_qwen2.5-7b-instruct_run9_2/eval_summary.txt)

### 2.4 同口径横向质量对比（新增后）

| 模型 | Internal F1 | External F1 | 加权分(0.7*internal + 0.3*external) |
|---|---:|---:|---:|
| Qwen2.5-1.5B-Run9_2 | 0.6199 | 0.1668 | 0.4839 |
| DeepSeek-R1-Distill-Qwen-1.5B | 0.3034 | 0.2222 | 0.2790 |
| Qwen2.5-3B-Instruct | 0.6002 | 0.1641 | 0.4694 |
| Qwen2.5-7B-Instruct | 0.6447 | 0.1659 | 0.5011 |

对应指标文件：
- [output/eval_run9_2_base_compare/extended_metrics_base_vs_run9_2.json](output/eval_run9_2_base_compare/extended_metrics_base_vs_run9_2.json)
- [output/ablation_qwen3b_replace/eval/deepseek-r1-distill-qwen-1.5b/extended_metrics_base_vs_deepseek-r1-distill-qwen-1.5b.json](output/ablation_qwen3b_replace/eval/deepseek-r1-distill-qwen-1.5b/extended_metrics_base_vs_deepseek-r1-distill-qwen-1.5b.json)
- [output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/extended_metrics_base_vs_qwen2.5-3b-instruct.json](output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/extended_metrics_base_vs_qwen2.5-3b-instruct.json)
- [output/eval_qwen2.5-7b-instruct_run9_2/extended_metrics_base_vs_qwen2.5-7b-instruct.json](output/eval_qwen2.5-7b-instruct_run9_2/extended_metrics_base_vs_qwen2.5-7b-instruct.json)

## 3. 压测任务流程（在线系统性能）

### 3.1 目的

- 评估 3B 作为主上线模型的系统承载能力
- 在相同请求场景下补测 7B 小流量，量化性能提升是否抵消显存成本

### 3.2 执行步骤

1. 启动 3B 本地服务（8103）
2. 跑并发场景 1/2/4/8
3. 停 3B，启动 7B 服务（8107）
4. 跑并发场景 1/2/4
5. 汇总成对照报告

脚本与产物：
- 编排： [run_online_stress_compare.sh](run_online_stress_compare.sh)
- 服务： [serve_lora_openai.py](serve_lora_openai.py)
- 压测： [run_load_benchmark.py](run_load_benchmark.py)
- 汇总： [output/online_bench/reports/bench_compare_summary.md](output/online_bench/reports/bench_compare_summary.md)

### 3.3 结果摘要

| 模型 | 并发 | QPS | P95(s) | P99(s) | 错误率 |
|---|---:|---:|---:|---:|---:|
| 3B | 1 | 0.177 | 7.506 | 7.535 | 0.00% |
| 3B | 2 | 0.179 | 14.389 | 14.637 | 0.00% |
| 3B | 4 | 0.177 | 27.189 | 28.053 | 0.00% |
| 3B | 8 | 0.181 | 50.871 | 52.031 | 0.00% |
| 7B | 1 | 0.225 | 5.814 | 6.333 | 0.00% |
| 7B | 2 | 0.212 | 11.577 | 11.864 | 0.00% |
| 7B | 4 | 0.230 | 19.789 | 20.185 | 0.00% |

显存快照：
- 3B 服务约 6530 MiB
- 7B 服务约 15218 MiB
- 增量约 +8688 MiB

## 4. 本次执行中的关键工程经验

1. 端口冲突与僵尸进程
- 现象：8103 被旧服务占用，导致新服务 bind 失败
- 处理：启动前清理进程与端口，必要时按端口 kill

2. 手动中断导致流程不完整
- 现象：历史多次 KeyboardInterrupt 导致脚本半途退出
- 处理：拆分为阶段执行，并通过产物文件校验是否完成

3. 显存释放延迟
- 现象：进程退出后显存短时不回落
- 处理：等待并复核 nvidia-smi，再切换下一个模型服务

## 5. 建议的后续标准化改造

1. 给编排脚本增加端口健康检查与强制清理函数
2. 增加外部数据集压测入口，产出 internal vs external 分域系统性能报告
3. 增加首 token 时延、超时率、5xx 分布等线上化指标
4. 建立可重复执行的 nightly 压测任务（固定数据快照 + 固定并发配置）
