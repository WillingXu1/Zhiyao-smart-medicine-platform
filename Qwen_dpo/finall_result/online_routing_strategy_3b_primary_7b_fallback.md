# 3B主干-7B兜底：上线路由策略（一页版）

## 1. 策略目标
- 在当前实验结果下，优先保证稳定性与吞吐：默认走 3B（compile）。
- 对高风险、高复杂度、低置信度请求进行质量兜底：升级到 7B（当前建议 eager）。
- 控制线上风险：避免 7B compile 在 external long 场景的上下文越界和超时问题。

## 2. 当前依据（来自已验证数据）
- 3B compile：双域门禁 PASS，QPS/tokens/s 显著高于 3B eager，可作为主承载。
- 7B：离线质量（尤其分层诊断/处方/用法与术语召回）总体更强，适合兜底高价值请求。
- 7B compile small traffic：external long 桶出现 FAIL（context overflow + timeout），短期不建议做默认承载。

## 3. 路由总原则
1. 默认请求 -> 3B compile。
2. 命中高风险/高复杂度/低置信度条件 -> 升级 7B eager。
3. 7B失败或超时 -> 回退 3B，并返回安全提示 + 人工审核标记。
4. 所有高风险问答进入审核队列，形成离线再训练闭环。

## 4. 可执行阈值（建议初始值）
### 4.1 输入侧阈值
- input_tokens_warn: 1200
- input_tokens_hard_limit_for_7b_compile: 1600
- intent_high_risk:
  - 剂量调整
  - 处方变更
  - 联合用药冲突
  - 孕妇/儿童/老年/肝肾功能异常

### 4.2 输出质量阈值（基于3B首答自检）
- conf_min_for_stay_3b: 0.72
- term_recall_min_for_stay_3b: 0.55
- layered_rouge_diag_min: 0.60
- layered_rouge_rx_min: 0.45
- layered_rouge_usage_min: 0.45
- missing_required_sections_max: 0

说明：
- conf 可由规则融合得到，例如：0.5 * answer_consistency + 0.3 * retrieval_support + 0.2 * policy_compliance。
- 若线上没有 reference，layered_rouge 可替换为结构完整性打分（字段存在率 + 术语覆盖率）。

### 4.3 服务SLA阈值
- p95_latency_budget_sec: 8
- timeout_3b_sec: 18
- timeout_7b_sec: 28
- retry_on_7b_fail: 1

## 5. 路由判定逻辑（可直接实现）
```text
if intent in high_risk:
    route = 7b_eager
elif complexity_score >= 0.65:
    route = 7b_eager
elif input_tokens >= 1200:
    route = 7b_eager
else:
    route = 3b_compile

# 3B首答后再判定是否升级
if route == 3b_compile:
    if conf < 0.72 or term_recall < 0.55 or missing_sections > 0:
        route = 7b_eager

# 失败回退
if route == 7b_eager and (timeout or non_2xx):
    fallback_to = 3b_compile
    add_flag = ["requires_manual_review"]
```

## 6. 阈值配置模板（YAML）
```yaml
routing:
  primary_model: qwen2.5-3b-medical
  primary_mode: compile
  fallback_model: qwen2.5-7b-medical
  fallback_mode: eager

thresholds:
  input_tokens_warn: 1200
  input_tokens_hard_limit_for_7b_compile: 1600
  complexity_score_upgrade: 0.65
  conf_min_for_stay_3b: 0.72
  term_recall_min_for_stay_3b: 0.55
  layered_diag_min: 0.60
  layered_rx_min: 0.45
  layered_usage_min: 0.45
  missing_required_sections_max: 0

sla:
  p95_latency_budget_sec: 8
  timeout_3b_sec: 18
  timeout_7b_sec: 28
  retry_on_7b_fail: 1

high_risk_intents:
  - dose_adjustment
  - prescription_change
  - drug_interaction
  - special_population

required_sections:
  - diagnosis
  - prescription
  - usage

fallback:
  on_7b_timeout_to_3b: true
  on_7b_non_2xx_to_3b: true
  add_manual_review_flag: true
```

## 7. 灰度上线计划
1. Phase A（1周）：100%走3B，记录触发升级条件但不实际升级，校准阈值。
2. Phase B（1周）：10%流量启用7B兜底，观察高风险命中率、P95、错误率、人工审核通过率。
3. Phase C：逐步提升到20%-30%兜底比例，仅在高风险和低置信条件触发。

## 8. 监控与回滚
- 关键监控：upgrade_rate、7b_timeout_rate、manual_review_rate、adverse_case_rate。
- 回滚条件（任一满足即回滚到纯3B）：
  - 7b_timeout_rate > 3%
  - overall_error_rate > 1%
  - p95_latency 超预算持续30分钟

## 9. 短期优化项（建议并行推进）
- 修复7B compile external long失败：提升 max_model_len、输入截断策略、max_new_tokens 动态下调。
- 在网关层增加 token 预算器：确保 input_tokens + max_new_tokens <= context_limit。
- 将人工审核结论回灌训练集，按周更新兜底阈值。
