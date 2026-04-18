# 消化系统用药助手：项目全流程复盘（主流程+细节）

更新时间：2026-03-29

## 主流程 1：任务定义与数据方案
### 目标
- 建立一个面向消化系统场景的问答/建议助手。
- 在可控成本下提升临床相关回答质量，并兼顾在线可部署性。
### 细节
- 训练数据采用内部医疗指令数据主集，并预留 internal20/external23 做评测。
- 数据增强采用 rule + LLM 双通道，构建 run9 训练池。
- LLM 增强时同时使用本地模型与外部接口，形成多样化改写样本。

## 主流程 2：数据增强与训练集构建
### 执行动作
- 运行 rule 模式增强，扩大稳态样本。
- 运行 llm 模式增强，生成高多样性表达。
- 组合不同来源比例形成 run9 mix 训练集。
### 细节
- 对 273 样本池进行分批增强，分别产出 rule/deepseek/run8 风格数据。
- 通过报告文件记录样本数量、失败样本与分布信息。

## 主流程 3：LoRA 微调训练（1.5B/3B/7B）
### 训练配置
- 框架：swift sft + peft LoRA。
- 典型参数：rank=16, alpha=32, dropout=0.05, fp16, grad_accum=16。
- 训练策略：按 eval_steps/save_steps 保存并选择最佳 checkpoint。
### 细节
- 1.5B 多组 run9 实验用于验证数据配比。
- 3B 与 7B 作为质量上探与上线备选模型。

## 主流程 4：离线评测（原始指标）
### 指标体系
- EM, F1, Rouge-L, BLEU-4。
- ECE-proxy（基于 Rouge-L 代理置信度）。
- DPD-proxy（基于性别词代理分组差异）。
- PDR（相对 Base 的退化率指标）。
### 细节
- 每个模型都执行 internal20/external23 配对评测（base/new 对照）。
- 评测原始输出 jsonl 全量保留，便于审计与复算。

## 主流程 5：临床风险导向评测升级（三层机制）
### 机制设计
- 分层 Rouge-L：诊断、处方、用法三层独立计算。
- 术语召回率：评估关键医学术语覆盖。
- 人工审核队列：按风险排序输出 TopK 样本。
### 代码与产物
- 扩展 evaluate_metrics_extended.py，新增 clinical_layered_internal 与 manual review 导出。
- 产出每模型 clinical json/md 与 manual_review_top40.csv。

## 主流程 6：在线服务压测与门禁（vLLM）
### 已完成
- Qwen2.5-3B：eager vs compile 对照门禁已完成，compile PASS，eager FAIL。
- Qwen2.5-7B small traffic：eager/compile 均有报告，compile external long 桶 FAIL。
### 关键现象
- compile 模式可显著提升吞吐，但更依赖显存与上下文长度配置。
- 7B compile external 失败原因包含 context length 越界与读超时。

## 主流程 7：统一汇总与交付
### 交付内容
- 全模型离线 + 临床分层 + 在线门禁统一总表。
- 主流程复盘文档（本文件）。
- STAR 面试版本项目叙述。

## 已验证结果清单
- 原始推理输出（jsonl）已保留。
- 四模型临床三层机制已批量跑通（1.5B/7B/DeepSeek1.5B/DeepSeek7B）。
- 全模型总表已落地。

## 下一步 
设计多 LoRA Adapter 路由机制：按科室训练独立Adapter，并基于意图分类（规则/分类模型）将请求动态路由至对应 Adapter，实现按科室横向扩展
## 当前瓶颈
1. 修复 7B compile external long 桶失败：输入截断、max_model_len、超时策略。
2. DeepSeek 7B 缺高质量增益，建议回到数据分布与训练策略层面复查。
3. 在上线前将人工审核 TopK 与自动指标形成闭环反馈。

