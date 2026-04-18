# 消化系统用药助手：全模型全指标总表

更新时间：2026-04-04

覆盖范围：
- 离线评测：Internal59 / External24，Base vs New。
- 原始指标：EM/F1/Rouge-L/BLEU-4/ECE-proxy/DPD-proxy/质量率/PDR。
- 临床增强指标：分层 Rouge-L（诊断/处方/用法）+ 术语召回率 + 覆盖率。
- 在线服务指标：vLLM 门禁（QPS、tokens/s、P95/P99 E2E、P95 TTFT、错误率、Gate）。

## Internal59 - Base 原始指标
| 模型 | n | EM | F1 | Rouge-L | BLEU-4 | ECE-proxy | DPD-proxy | 质量率(F1>=0.5) | 女性质量率 | 男性质量率 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-1.5b-instruct | 59 | 0.0000 | 0.1968 | 0.1335 | 0.0443 | 0.1335 | 0.0000 | 0.00% | 0.00% | 0.00% |
| qwen2.5-3b-instruct | 59 | 0.0000 | 0.4134 | 0.3124 | 0.1563 | 0.2314 | 0.1968 | 15.25% | 6.25% | 25.93% |
| qwen2.5-7b-instruct | 59 | 0.0000 | 0.4170 | 0.3155 | 0.1672 | 0.2743 | 0.0914 | 13.56% | 9.38% | 18.52% |
| deepseek-r1-distill-qwen-1.5b | 59 | 0.0000 | 0.2744 | 0.1991 | 0.0779 | 0.1991 | 0.0000 | 0.00% | 0.00% | 0.00% |
| deepseek-r1-distill-qwen-7b | 59 | 0.0000 | 0.1593 | 0.0955 | 0.0352 | 0.0955 | 0.0000 | 0.00% | 0.00% | 0.00% |

## Internal59 - New 原始指标
| 模型 | n | EM | F1 | Rouge-L | BLEU-4 | ECE-proxy | DPD-proxy | 质量率(F1>=0.5) | 女性质量率 | 男性质量率 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-1.5b-instruct | 59 | 0.0000 | 0.6199 | 0.5772 | 0.3488 | 0.2740 | 0.2639 | 74.58% | 62.50% | 88.89% |
| qwen2.5-3b-instruct | 59 | 0.0000 | 0.6002 | 0.5537 | 0.3313 | 0.2830 | 0.1273 | 74.58% | 68.75% | 81.48% |
| qwen2.5-7b-instruct | 59 | 0.0000 | 0.6447 | 0.6053 | 0.3549 | 0.2897 | 0.0289 | 83.05% | 84.38% | 81.48% |
| deepseek-r1-distill-qwen-1.5b | 59 | 0.0000 | 0.3034 | 0.2188 | 0.0918 | 0.2188 | 0.0000 | 0.00% | 0.00% | 0.00% |
| deepseek-r1-distill-qwen-7b | 59 | 0.0000 | 0.1618 | 0.0931 | 0.0353 | 0.0931 | 0.0000 | 0.00% | 0.00% | 0.00% |

## External24 - Base 原始指标
| 模型 | n | EM | F1 | Rouge-L | BLEU-4 | ECE-proxy | DPD-proxy | 质量率(F1>=0.5) | 女性质量率 | 男性质量率 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-1.5b-instruct | 23 | 0.0000 | 0.2687 | 0.1218 | 0.0442 | 0.1218 | 0.0000 | 0.00% | 0.00% | 0.00% |
| qwen2.5-3b-instruct | 23 | 0.0000 | 0.2526 | 0.1297 | 0.0494 | 0.1297 | 0.0000 | 0.00% | 0.00% | 0.00% |
| qwen2.5-7b-instruct | 23 | 0.0000 | 0.2481 | 0.1356 | 0.0499 | 0.1356 | 0.0000 | 0.00% | 0.00% | 0.00% |
| deepseek-r1-distill-qwen-1.5b | 23 | 0.0000 | 0.2202 | 0.1163 | 0.0332 | 0.1163 | 0.0000 | 0.00% | 0.00% | 0.00% |
| deepseek-r1-distill-qwen-7b | 23 | 0.0000 | 0.1928 | 0.1056 | 0.0250 | 0.1056 | 0.0000 | 0.00% | 0.00% | 0.00% |

## External24 - New 原始指标
| 模型 | n | EM | F1 | Rouge-L | BLEU-4 | ECE-proxy | DPD-proxy | 质量率(F1>=0.5) | 女性质量率 | 男性质量率 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-1.5b-instruct | 23 | 0.0000 | 0.1668 | 0.1068 | 0.0279 | 0.1038 | 0.0000 | 4.35% | 0.00% | 0.00% |
| qwen2.5-3b-instruct | 23 | 0.0000 | 0.1641 | 0.1105 | 0.0231 | 0.1105 | 0.0000 | 0.00% | 0.00% | 0.00% |
| qwen2.5-7b-instruct | 23 | 0.0000 | 0.1659 | 0.1119 | 0.0205 | 0.1119 | 0.0000 | 0.00% | 0.00% | 0.00% |
| deepseek-r1-distill-qwen-1.5b | 23 | 0.0000 | 0.2222 | 0.1178 | 0.0340 | 0.1178 | 0.0000 | 0.00% | 0.00% | 0.00% |
| deepseek-r1-distill-qwen-7b | 23 | 0.0000 | 0.2110 | 0.1069 | 0.0303 | 0.1069 | 0.0000 | 0.00% | 0.00% | 0.00% |

## PDR 指标（New 相对 Base）
### Internal59
| 模型 | pdr_em | pdr_f1 | pdr_rouge_l | pdr_bleu_4 |
|---|---:|---:|---:|---:|
| qwen2.5-1.5b-instruct | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| qwen2.5-3b-instruct | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| qwen2.5-7b-instruct | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| deepseek-r1-distill-qwen-1.5b | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| deepseek-r1-distill-qwen-7b | 0.0000 | 0.0000 | 0.0248 | 0.0000 |

### External24
| 模型 | pdr_em | pdr_f1 | pdr_rouge_l | pdr_bleu_4 |
|---|---:|---:|---:|---:|
| qwen2.5-1.5b-instruct | 0.0000 | 0.3795 | 0.1233 | 0.3684 |
| qwen2.5-3b-instruct | 0.0000 | 0.3504 | 0.1480 | 0.5326 |
| qwen2.5-7b-instruct | 0.0000 | 0.3315 | 0.1747 | 0.5890 |
| deepseek-r1-distill-qwen-1.5b | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| deepseek-r1-distill-qwen-7b | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## 临床分层指标（Internal59）
| 模型 | 覆盖率(Base) | 诊断(Base) | 处方(Base) | 用法(Base) | 术语召回(Base) | 覆盖率(New) | 诊断(New) | 处方(New) | 用法(New) | 术语召回(New) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-1.5b-instruct | 100.00% | 0.2721 | 0.0046 | 0.0817 | 0.2037 | 100.00% | 0.7117 | 0.5617 | 0.5724 | 0.6191 |
| qwen2.5-3b-instruct | 100.00% | 0.6226 | 0.2317 | 0.1148 | 0.2607 | 100.00% | 0.7312 | 0.5105 | 0.5312 | 0.5801 |
| qwen2.5-7b-instruct | 100.00% | 0.6458 | 0.1797 | 0.0538 | 0.3416 | 100.00% | 0.7988 | 0.5715 | 0.5616 | 0.6282 |
| deepseek-r1-distill-qwen-1.5b | 100.00% | 0.2730 | 0.0057 | 0.1350 | 0.1922 | 100.00% | 0.3595 | 0.0265 | 0.1220 | 0.2018 |
| deepseek-r1-distill-qwen-7b | 100.00% | 0.0691 | 0.0000 | 0.0339 | 0.0148 | 100.00% | 0.0684 | 0.0000 | 0.0339 | 0.0133 |

## 临床分层增量（Internal59, New-Base）
| 模型 | 诊断 Delta | 处方 Delta | 用法 Delta | 术语召回 Delta |
|---|---:|---:|---:|---:|
| qwen2.5-1.5b-instruct | +0.4396 | +0.5572 | +0.4907 | +0.4154 |
| qwen2.5-3b-instruct | +0.1086 | +0.2789 | +0.4164 | +0.3194 |
| qwen2.5-7b-instruct | +0.1530 | +0.3918 | +0.5078 | +0.2866 |
| deepseek-r1-distill-qwen-1.5b | +0.0865 | +0.0208 | -0.0130 | +0.0096 |
| deepseek-r1-distill-qwen-7b | -0.0007 | +0.0000 | +0.0000 | -0.0015 |

## 在线门禁指标（vLLM）
说明：该部分当前仅覆盖已完成在线门禁的模型/模式。DeepSeek 模型暂无同口径在线门禁结果。

### Qwen2.5-3B + LoRA (eager)
| Domain | QPS | Tokens/s | P95 E2E(s) | P99 E2E(s) | P95 TTFT(s) | Error Rate | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| internal | 0.622 | 57.096 | 38.294 | 38.851 | 2.200 | 0.00% | FAIL |
| external | 0.395 | 65.716 | 38.532 | 39.136 | 1.021 | 0.00% | FAIL |
- overall_gate: **FAIL**

### Qwen2.5-3B + LoRA (compile)
| Domain | QPS | Tokens/s | P95 E2E(s) | P99 E2E(s) | P95 TTFT(s) | Error Rate | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| internal | 4.235 | 388.594 | 4.723 | 5.876 | 1.358 | 0.00% | PASS |
| external | 3.068 | 510.167 | 4.971 | 5.739 | 0.635 | 0.00% | PASS |
- overall_gate: **PASS**

### Qwen2.5-7B + LoRA small traffic (eager)
| Domain | QPS | Tokens/s | P95 E2E(s) | P99 E2E(s) | P95 TTFT(s) | Error Rate | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| internal | 0.315 | 22.143 | 30.411 | 31.616 | 0.337 | 0.00% | PASS |
| external | 0.418 | 23.685 | 8.003 | 14.691 | 0.345 | 0.00% | PASS |
- overall_gate: **PASS**

### Qwen2.5-7B + LoRA small traffic (compile)
| Domain | QPS | Tokens/s | P95 E2E(s) | P99 E2E(s) | P95 TTFT(s) | Error Rate | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| internal | 0.396 | 28.745 | 13.031 | 18.136 | 9.496 | 0.00% | PASS |
| external | 0.195 | 10.762 | 6.617 | 11.422 | 4.479 | 4.00% | FAIL |
- overall_gate: **FAIL**

## 严格同集横向对比（Internal59 + External24）
说明：本节为新增横向实验，口径固定为 HuatuoGPT-o1-7B 零样本 vs Qwen2.5-7B 微调（Run9.2 LoRA），并使用统一加权规则判定胜负。

### 核心对比（池化指标）
| 模型 | pooled F1 | pooled 幻觉率(proxy) | 诊断RL(Internal59) | 处方RL(Internal59) | 用法RL(Internal59) | 加权总分 |
|---|---:|---:|---:|---:|---:|---:|
| HuatuoGPT-o1-7B（Zero-shot） | 0.1196 | 0.9157 | 0.0545 | 0.0000 | 0.0339 | 0.0787 |
| Qwen2.5-7B（FT Run9.2） | 0.5873 | 0.0120 | 0.7988 | 0.5737 | 0.5653 | 0.7357 |

### 分域主指标（便于复核）
| 模型 | Internal59 F1 | External24 F1 | Internal59 幻觉率(proxy) | External24 幻觉率(proxy) |
|---|---:|---:|---:|---:|
| HuatuoGPT-o1-7B（Zero-shot） | 0.1404 | 0.0683 | 0.8814 | 1.0000 |
| Qwen2.5-7B（FT Run9.2） | 0.6435 | 0.4491 | 0.0000 | 0.0417 |

### 两步对齐（SFT + DPO）后再横向对比（Internal59 + External24）
说明：本节使用同一严格评测脚本，在相同测试集下将 Qwen2.5-7B 基座经 SFT 后再做 DPO 的适配器，与 HuatuoGPT-o1-7B 零样本直接对比。
注意：本小节中的“幻觉率(proxy)”是对齐偏差代理指标，不等同于安全评测里的 hallucination_primary/secondary。

| 模型 | pooled F1 | pooled 幻觉率(proxy) | 加权总分 |
|---|---:|---:|---:|
| HuatuoGPT-o1-7B（Zero-shot） | 0.1196 | 0.9157 | 0.0787 |
| Qwen2.5-7B（SFT + DPO） | 0.5960 | 0.0000 | 0.7438 |

变化量（Qwen SFT+DPO 相对 Huatuo Zero-shot）：
- pooled F1: +0.4764
- pooled 幻觉率(proxy): -0.9157
- 加权总分: +0.6651

### 两步对齐（SFT + DPO）后再横向对比（安全口径：hallucination_primary/secondary）
说明：本节基于 `eval_safety_three_models.py` 对相同预测结果重新评估，优先呈现 Internal59 与 External24 的安全幻觉率（all-level）。

| Split | 模型 | hard_refusal_rate | soft_refusal_rate | any_refusal_rate | hallucination_primary_rate | hallucination_secondary_rate |
|---|---|---:|---:|---:|---:|---:|
| Internal59 | HuatuoGPT-o1-7B（Zero-shot） | 0.0000 | 0.0000 | 0.0000 | 0.1695 | 0.0000 |
| Internal59 | Qwen2.5-7B（SFT + DPO） | 0.0000 | 0.0000 | 0.0000 | 0.2373 | 0.0000 |
| External24 | HuatuoGPT-o1-7B（Zero-shot） | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| External24 | Qwen2.5-7B（SFT + DPO） | 0.0000 | 0.0000 | 0.0000 | 0.0833 | 0.0000 |

变化量（Qwen SFT+DPO 相对 Huatuo Zero-shot，安全口径）：
- Internal59 hallucination_primary_rate: +0.0678
- External24 hallucination_primary_rate: +0.0833
- Internal59/External24 hallucination_secondary_rate: 均为 0.0000

### 两步对齐（SFT + DPO）后再横向对比（GI处方能力口径：DEP/DER/DUC/FCF/CCR）
说明：本节指标用于评估“消化内科处方能力”，与 proxy 幻觉率、安全 primary/secondary 口径不同。

公式定义（micro 统计）：
- DEP（Drug Entity Precision）: DEP = 命中药物数 / 预测药物总数
- DER（Drug Entity Recall）: DER = 命中药物数 / 参考药物总数
- DUC（Dose-Unit Compatibility）: DUC = 剂量+单位同时匹配的药物数 / 可对齐药物数
- FCF（Frequency-Course Fidelity）: FCF = Σ(0.5*频次匹配 + 0.5*疗程匹配) / 可对齐药物数
- CCR（Contraindication Conflict Rate）: CCR = 禁忌冲突样本数 / 含禁忌信息样本数
- GI Score: 0.35*DEP + 0.20*DER + 0.20*DUC + 0.15*FCF + 0.10*(1-CCR)

| Split | 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Internal59+External24 (pooled) | HuatuoGPT-o1-7B（Zero-shot） | 83 | 0.0592 | 0.0070 | 0.0000 | 0.0000 | 0.1777 | 0.1044 |
| Internal59+External24 (pooled) | Qwen2.5-7B（SFT + DPO） | 83 | 0.2608 | 0.1994 | 0.2666 | 0.2999 | 0.0000 | 0.3295 |
| Internal59 | HuatuoGPT-o1-7B（Zero-shot） | 59 | 0.0833 | 0.0098 | 0.0000 | 0.0000 | 0.2500 | 0.1061 |
| Internal59 | Qwen2.5-7B（SFT + DPO） | 59 | 0.3288 | 0.2353 | 0.3750 | 0.3542 | 0.0000 | 0.3903 |
| External24 | HuatuoGPT-o1-7B（Zero-shot） | 24 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1000 |
| External24 | Qwen2.5-7B（SFT + DPO） | 24 | 0.0938 | 0.1111 | 0.0000 | 0.1667 | 0.0000 | 0.1800 |

### 其他模型补充（GI处方能力口径，internal20 + external23）
说明：以下“其他模型”目前可用输出 json 为 internal20/external23 口径，不与 Internal59/External24 直接混算。

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

注：`qwen2.5-1.5b-instruct` 目前未检索到与上述口径匹配的成对 jsonl 预测文件，待补齐后可追加同表。

产物文件：
- `course/SFT_qwen/results/output/eval_huatuo_vs_qwen_dpo_strict/strict_compare_huatuo_vs_qwen_internal59_external24.json`
- `course/SFT_qwen/results/output/eval_huatuo_vs_qwen_dpo_strict/strict_compare_huatuo_vs_qwen_internal59_external24.md`
- `course/SFT_qwen/results/output/eval_huatuo_vs_qwen_dpo_strict/safety_report/huatuo_vs_qwen_safety_direct.json`
- `course/SFT_qwen/results/output/eval_huatuo_vs_qwen_dpo_strict/safety_report/huatuo_vs_qwen_safety_direct.md`
- `course/SFT_qwen/results/output/eval_huatuo_vs_qwen_dpo_strict/gi_prescription_eval_v1.json`
- `course/SFT_qwen/results/output/eval_huatuo_vs_qwen_dpo_strict/gi_prescription_eval_v1.md`
- `course/finall_result/gi_prescription_eval_other_models/gi_eval_other_models_summary.json`
- `course/finall_result/gi_prescription_eval_other_models/gi_eval_other_models_summary.md`

### 加权规则（本次判定口径）
- F1: 0.35
- 诊断 Rouge-L: 0.15
- 处方 Rouge-L: 0.10
- 用法 Rouge-L: 0.10
- (1 - 幻觉率proxy): 0.30

产物文件：
- `course/SFT_qwen/results/output/eval_huatuo_vs_qwen_strict/strict_compare_huatuo_vs_qwen_internal59_external24.json`
- `course/SFT_qwen/results/output/eval_huatuo_vs_qwen_strict/strict_compare_huatuo_vs_qwen_internal59_external24.md`

## 关键结论（当前数据）
1. 离线质量：Qwen2.5-7B 在 Internal59 上整体最强，Qwen2.5-1.5B 次之，Qwen2.5-3B 紧随。
2. 分层临床指标：Qwen 系列在诊断/处方/用法与术语召回上显著领先于 DeepSeek 两个蒸馏模型。
3. 在线服务：3B 在 compile 模式下门禁 PASS 且吞吐显著提升；7B small 在 compile 模式 external 出现长文本错误导致 FAIL。
4. 风险点：7B compile 的 external long 桶存在上下文长度越界与超时，应先做 max_model_len/截断策略修复再复测。
5. 新增严格同集横向结果显示：Qwen2.5-7B 微调（Run9.2）加权总分 0.7357，显著高于 HuatuoGPT-o1-7B 零样本的 0.0787（差值 -0.6569）。

## 决策纪要
基于 Internal59 + External24 的严格同集对比，HuatuoGPT-o1-7B 零样本在 F1、三层临床分层指标、幻觉率 proxy 三个维度均未超过当前最佳 Qwen2.5-7B 微调模型。按既定“主指标加权胜出”规则，本轮不触发“转向 Huatuo 的 SFT+DPO”分支。

当前主线决策：继续以 Qwen2.5-7B（Run9.2 LoRA）作为主模型推进后续 DPO 与安全增强；HuatuoGPT-o1-7B 保留为外部对照基线，待后续模板适配或更大规模数据后再复评。

## Qwen2.5-7B：Base / SFT / DPO 全量指标记录（Internal59 + External24）
说明：本节基于当前最新 7B 评测产物，完整记录质量指标、增量指标与安全指标，作为主线模型闭环对比归档。

### 质量指标总表（内部数据集Internal59）
| 模型 | n | EM | F1 | Rouge-L | BLEU-4 | 诊断RL | 处方RL | 用法RL | 术语召回 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen2.5-7B Base | 59 | 0.0000 | 0.4160 | 0.3151 | 0.1695 | 0.6491 | 0.1865 | 0.0543 | 0.3455 |
| Qwen2.5-7B SFT (Run9.2) | 59 | 0.0000 | 0.6481 | 0.6097 | 0.3584 | 0.7992 | 0.5813 | 0.5757 | 0.6315 |
| Qwen2.5-7B DPO (from SFT) | 59 | 0.0000 | 0.6507 | 0.6071 | 0.3626 | 0.8029 | 0.5700 | 0.5668 | 0.6316 |

### 质量指标总表（外部数据集External24）
| 模型 | n | EM | F1 | Rouge-L | BLEU-4 | 诊断RL | 处方RL | 用法RL | 术语召回 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen2.5-7B Base | 24 | 0.0000 | 0.2422 | 0.1668 | 0.0582 | 0.1282 | 0.0558 | 0.0458 | 0.0530 |
| Qwen2.5-7B SFT (Run9.2) | 24 | 0.0000 | 0.4503 | 0.3629 | 0.1941 | 0.1250 | 0.2212 | 0.3571 | 0.3933 |
| Qwen2.5-7B DPO (from SFT) | 24 | 0.0000 | 0.4591 | 0.3745 | 0.2085 | 0.1593 | 0.2299 | 0.3857 | 0.4083 |

### 增量指标（相对 Base）
#### Internal59
| 模型对比 | F1 Delta | Rouge-L Delta | 诊断RL Delta | 处方RL Delta | 用法RL Delta | 术语召回 Delta |
|---|---:|---:|---:|---:|---:|---:|
| SFT - Base | +0.2321 | +0.2946 | +0.1501 | +0.3948 | +0.5214 | +0.2860 |
| DPO - Base | +0.2347 | +0.2920 | +0.1538 | +0.3835 | +0.5125 | +0.2861 |

#### External24
| 模型对比 | F1 Delta | Rouge-L Delta | 诊断RL Delta | 处方RL Delta | 用法RL Delta | 术语召回 Delta |
|---|---:|---:|---:|---:|---:|---:|
| SFT - Base | +0.2081 | +0.1961 | -0.0032 | +0.1655 | +0.3113 | +0.3403 |
| DPO - Base | +0.2169 | +0.2076 | +0.0312 | +0.1741 | +0.3399 | +0.3553 |

### 增量指标（DPO 相对 SFT）
| Split | F1 Delta | Rouge-L Delta | BLEU-4 Delta | 诊断RL Delta | 处方RL Delta | 用法RL Delta | 术语召回 Delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| Internal59 | +0.0026 | -0.0026 | +0.0042 | +0.0037 | -0.0113 | -0.0089 | +0.0001 |
| External24 | +0.0088 | +0.0115 | +0.0143 | +0.0343 | +0.0087 | +0.0286 | +0.0150 |

### 安全指标（all-level 总览）
| Split | 模型 | hard_refusal_rate | soft_refusal_rate | any_refusal_rate | hallucination_primary_rate | hallucination_secondary_rate |
|---|---|---:|---:|---:|---:|---:|
| Internal59 | Base | 0.0000 | 0.0339 | 0.0339 | 0.2203 | 0.0169 |
| Internal59 | SFT | 0.0000 | 0.0000 | 0.0000 | 0.2373 | 0.0000 |
| Internal59 | DPO | 0.0000 | 0.0000 | 0.0000 | 0.2373 | 0.0000 |
| External24 | Base | 0.0417 | 0.0417 | 0.0417 | 0.0833 | 0.0000 |
| External24 | SFT | 0.0000 | 0.0000 | 0.0000 | 0.0833 | 0.0000 |
| External24 | DPO | 0.0000 | 0.0000 | 0.0000 | 0.0833 | 0.0000 |

### 安全分层指标（Internal59）
| 风险层级 | 模型 | n | any_refusal_rate | hallucination_primary_rate | hallucination_secondary_rate |
|---|---|---:|---:|---:|---:|
| high | Base | 12 | 0.0833 | 0.9167 | 0.0833 |
| high | SFT | 12 | 0.0000 | 1.0000 | 0.0000 |
| high | DPO | 12 | 0.0000 | 1.0000 | 0.0000 |
| medium | Base | 2 | 0.0000 | 1.0000 | 0.0000 |
| medium | SFT | 2 | 0.0000 | 1.0000 | 0.0000 |
| medium | DPO | 2 | 0.0000 | 1.0000 | 0.0000 |
| low | Base | 45 | 0.0222 | 0.0000 | 0.0000 |
| low | SFT | 45 | 0.0000 | 0.0000 | 0.0000 |
| low | DPO | 45 | 0.0000 | 0.0000 | 0.0000 |

### 安全分层指标（External24）
| 风险层级 | 模型 | n | any_refusal_rate | hallucination_primary_rate | hallucination_secondary_rate |
|---|---|---:|---:|---:|---:|
| high | Base | 0 | 0.0000 | 0.0000 | 0.0000 |
| high | SFT | 0 | 0.0000 | 0.0000 | 0.0000 |
| high | DPO | 0 | 0.0000 | 0.0000 | 0.0000 |
| medium | Base | 2 | 0.0000 | 1.0000 | 0.0000 |
| medium | SFT | 2 | 0.0000 | 1.0000 | 0.0000 |
| medium | DPO | 2 | 0.0000 | 1.0000 | 0.0000 |
| low | Base | 22 | 0.0455 | 0.0000 | 0.0000 |
| low | SFT | 22 | 0.0000 | 0.0000 | 0.0000 |
| low | DPO | 22 | 0.0000 | 0.0000 | 0.0000 |

### 本节结论
1. 相比 Base，SFT 与 DPO 在 Internal59 与 External24 的主要质量指标均显著提升。
2. DPO 相比 SFT 的收益主要体现在 External24（F1/Rouge-L/BLEU-4/分层RL均有增益），Internal59 为小幅混合变化。
3. 安全侧主幻觉率上，DPO 与 SFT 基本持平；External24 三模型主幻觉率一致（0.0833）。
