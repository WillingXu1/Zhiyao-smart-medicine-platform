# SFT_qwen 代码与产物梳理及重构执行方案

更新时间：2026-04-04

## 1. 目标与约束

目标：将杂乱脚本按职责归类，尤其将 run 入口统一收敛到 run 路径；同时明确结果文件来源，避免后续维护时找不到产物对应脚本。

约束：
- 先出梳理文档，再执行文件移动。
- 分两批迁移：先低风险，再高耦合。
- 本次范围包含 datasets 与 output 的目录重排。
- 历史脚本归入 legacy。

## 2. 当前脚本职责梳理

### 2.1 训练/编排入口（run）
- run_qwen7b_train.sh: 启动 Qwen2.5-7B LoRA 训练。
- run_qwen7b_eval_after_train.sh: 等待 checkpoint 后执行 base-vs-adapter 推理及扩展指标评测。
- run_qwen3b_eval_fixed_base.sh: 修正后的 3B base 评测入口。
- run_priority1_testmodels.sh: 下载部分模型并调用批量消融训练/评测。
- run_online_stress_compare.sh: 3B/7B 在线压力对比编排。
- run_gate_benchmark_internal_external.sh: internal/external 门禁压测编排。
- run_vllm_eager_vs_compile_gate.sh: 3B vLLM eager/compile 门禁对照。
- run_vllm_eager_vs_compile_gate_7b_small.sh: 7B 小流量 eager/compile 门禁对照。
- run_vllm_compile_gate_7b_small_only.sh: 7B compile-only 门禁回归。
- run_ablation_3090_lora.py: 批量 LoRA 训练+推理+指标汇总编排器。

### 2.2 评测分析（eval）
- evaluate_base_vs_adapter.py: 生成 base/new 的 internal/external 预测 jsonl。
- evaluate_metrics_extended.py: 计算 EM/F1/Rouge-L/BLEU-4/ECE/DPD + 三层Rouge-L + 术语召回等。
- auto_eval_run9_1_internal_manual_external.py: 生成 run8 vs 新模型自动指标和外部人工评测包。
- auto_eval_run9_compare.py: run7/run8/run9 对比评测。
- hallucination_proxy_analysis.py: 幻觉代理分析脚本。
- summarize_manual_eval.py: 人工评测 CSV 汇总为报告。

### 2.3 数据构建（data_prep）
- extract_qa_from_txt.py: OCR 文本抽取 QA。
- rebuild_datasets_from_txt_v2.py: 从 txt 重建数据集。
- build_run9_1_datasets_from_qa_txt.py: 构建 run9.1 训练/内部/外部数据。
- build_run9_1_mixed_dataset.py: 按比例混合 rule/deepseek 增强集。
- build_run9_mixed_dataset.py: run9 混合集构建。
- build_dpo_dataset_from_qa.py: 由 QA 构建 DPO 数据。
- merge_augmented_datasets.py: 合并增强数据。
- augment_q_with_agent.py: 问题增强数据生成。

### 2.4 部署与压测执行器
- serve_lora_openai.py: OpenAI 兼容推理服务。
- openai_utf8_proxy.py: UTF-8 代理。
- run_load_benchmark.py: 通用压测执行。
- run_gate_benchmark_bucketed.py: 分桶门禁评测。

### 2.5 工具与历史脚本
- monitor_priority1_testmodels_top1.py/.sh: top1 监控推荐。
- evaluate_base_vs_run7.py: 历史阶段脚本（归档）。
- sft_qwen.py: 旧入口/占位（归档）。

## 3. 结果文件与来源映射

### 3.1 训练产物
- results/output/qwen2.5-7b-instruct_lora_run9_2/*
  - 来源：run_qwen7b_train.sh

- results/output/ablation_3090_priority1_testmodels/runs/*
  - 来源：run_priority1_testmodels.sh -> run_ablation_3090_lora.py

### 3.2 离线评测产物
- results/output/eval_qwen2.5-7b-instruct_run9_2/internal20_*.jsonl, external23_*.jsonl
  - 来源：run_qwen7b_eval_after_train.sh -> evaluate_base_vs_adapter.py

- results/output/eval_qwen2.5-7b-instruct_run9_2/extended_metrics_base_vs_qwen2.5-7b-instruct.{json,md}
  - 来源：run_qwen7b_eval_after_train.sh -> evaluate_metrics_extended.py

- results/output/ablation_qwen3b_replace/eval/qwen2.5-3b-instruct/extended_metrics_base_vs_qwen2.5-3b-instruct.{json,md}
  - 来源：run_qwen3b_eval_fixed_base.sh -> evaluate_metrics_extended.py

- results/output/ablation_3090_priority1_testmodels/eval/*/extended_metrics_base_vs_*.{json,md}
  - 来源：run_ablation_3090_lora.py

### 3.3 人工评测与阶段对比
- results/output/eval_run9_1/*manual*.jsonl, manual_external_*.csv, *rubric.md, run8_vs_*.{json,md}
  - 来源：auto_eval_run9_1_internal_manual_external.py

- results/output/eval_run9_compare/run7_run8_run9_compare.{json,md}
  - 来源：auto_eval_run9_compare.py

### 3.4 在线压测/门禁
- results/output/online_bench/reports/bench_*.{json,md}, bench_compare_summary.{json,md}
  - 来源：run_online_stress_compare.sh -> run_load_benchmark.py

- results/output/online_bench/reports/gate_report_*.{json,md}
  - 来源：run_gate_benchmark_internal_external.sh 或 run_vllm_* -> run_gate_benchmark_bucketed.py

## 4. 目标目录结构

```
course/SFT_qwen/
  run/
  train/
  eval/
  data_prep/
  deployment/
  benchmarks/
  tools/
  configs/
  legacy/
  data/
    datasets/
  results/
    output/
  docs/
```

## 5. 迁移清单（两批）

### 5.1 第一批（低风险）
- run_*.sh -> run/
- run_ablation_3090_lora.py -> run/
- ablation_*.json -> configs/
- monitor_priority1_testmodels_top1.py/.sh -> tools/
- evaluate_base_vs_run7.py, sft_qwen.py -> legacy/

### 5.2 第二批（高耦合）
- evaluate_*.py, auto_eval_*.py, summarize_manual_eval.py, hallucination_proxy_analysis.py -> eval/
- build_*.py, extract_qa_from_txt.py, rebuild_datasets_from_txt_v2.py, merge_augmented_datasets.py, augment_q_with_agent.py -> data_prep/
- serve_lora_openai.py, openai_utf8_proxy.py -> deployment/
- run_load_benchmark.py, run_gate_benchmark_bucketed.py -> benchmarks/
- datasets -> data/datasets
- output -> results/output

## 6. 风险与修复

- 风险1：脚本硬编码旧路径 datasets/output。
  - 修复：统一使用 data/datasets 与 results/output，或保留兼容软链接。
- 风险2：run 脚本调用 python 文件路径失效。
  - 修复：批量改为新的子目录路径（eval/, benchmarks/, deployment/, run/）。
- 风险3：历史文档中的相对链接失效。
  - 修复：后续补一次文档链接扫描。

## 7. 验证清单

1. 目录层面：脚本均归位，不再散落根目录。
2. 路径层面：run 脚本可找到其调用的 python 脚本。
3. 数据层面：data/datasets 与 results/output 可被脚本正确访问。
4. 产物层面：至少打通 1 条离线评测链和 1 条在线门禁链。

## 8. 执行状态

- [x] 梳理文档完成（本文件）
- [x] 第一批迁移
- [x] 第二批迁移
- [x] 路径修复与验证

补充说明：
- 已创建兼容软链接：datasets -> data/datasets，output -> results/output。
- 目的：在新结构生效后，旧脚本中的历史路径仍可运行，降低迁移中断风险。
