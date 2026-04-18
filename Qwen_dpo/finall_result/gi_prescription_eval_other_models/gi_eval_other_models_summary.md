# GI处方能力自动评估（其他模型，internal20+external23）
1. 目标对齐与口径冻结：将“幻觉”定义为临床处方相关错误，不再把合理给药本身视为风险；明确三类核心错误优先级为错药 > 错剂量 > 错用法。
2. 新指标体系设计（Phase A，设计可评估口径）：
2.1 处方实体准确率（Drug Entity Precision, DEP）：预测药物中与参考/规则库一致的占比。分母=预测药物数。
2.2 处方召回率（Drug Entity Recall, DER）：参考药物被覆盖比例。分母=参考药物数。
2.3 剂量单位一致率（Dose-Unit Compatibility, DUC）：药物级别剂量数值+单位一致比例。分母=可对齐药物数。
2.4 频次疗程一致率（Frequency-Course Fidelity, FCF）：频次与疗程字段一致比例。分母=可对齐药物数。
2.5 临床禁忌冲突率（Contraindication Conflict Rate, CCR）：命中过敏/禁忌冲突样本占比。分母=具备病史字段样本数。
3. 新总分方案（Phase B，和现有报表并行）：
3.1 设加权总分 GI-Prescription Score = 0.35*DEP + 0.20*DER + 0.20*DUC + 0.15*FCF + 0.10*(1-CCR)。

| 模型 | split | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-3b-instruct | pooled | 82 | 0.2398 | 0.1481 | 0.1028 | 0.1884 | 0.0000 | 0.2624 |
| qwen2.5-3b-instruct | internal | 59 | 0.3333 | 0.2059 | 0.1429 | 0.2619 | 0.0000 | 0.3257 |
| qwen2.5-3b-instruct | external | 23 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1000 |
| qwen2.5-7b-instruct | pooled | 82 | 0.2805 | 0.1622 | 0.2190 | 0.2503 | 0.0000 | 0.3120 |
| qwen2.5-7b-instruct | internal | 59 | 0.3898 | 0.2255 | 0.3043 | 0.3478 | 0.0000 | 0.3946 |
| qwen2.5-7b-instruct | external | 23 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1000 |
| deepseek-r1-distill-qwen-1.5b | pooled | 82 | 0.0799 | 0.0282 | 0.0000 | 0.0000 | 0.1799 | 0.1156 |
| deepseek-r1-distill-qwen-1.5b | internal | 59 | 0.1111 | 0.0392 | 0.0000 | 0.0000 | 0.2500 | 0.1217 |
| deepseek-r1-distill-qwen-1.5b | external | 23 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1000 |
| deepseek-r1-distill-qwen-7b | pooled | 82 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1799 | 0.0820 |
| deepseek-r1-distill-qwen-7b | internal | 59 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.2500 | 0.0750 |
| deepseek-r1-distill-qwen-7b | external | 23 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1000 |
