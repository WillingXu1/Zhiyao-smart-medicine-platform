# 消化内科处方数据筛选全流程汇总（从初始到最终版）

## 1. 目标与约束

- 目标：构建可用于消化内科 SFT 的高质量问答数据，重点保留“药名 + 剂量 + 频次”处方表达。
- 约束：
  - 不混入原本用于评测的 run9 系列数据（尤其 external/internal 测试集）。
  - 大文件处理必须采用流式思路，避免一次性全量加载。

---

## 2. 第一阶段：CSV 主集筛选（内科5000-33000）

### 2.1 初版规则（v1）

脚本：
- `/mnt/public/zxs/course/SFT_qwen/data_prep/filter_digestive_prescription_csv.py`

核心策略：
- 科室粗筛：消化/肝病/肝胆/胃肠/脾胃/肛肠。
- `内科` 候选语义筛：结合消化词典。
- 处方信号：药名、剂量、频次。

发现的问题：
- 编码和方言解析不稳定（GBK/GB18030 数据）。
- 高阶样本存在误触发（非用药频次也被识别为频次）。

### 2.2 规则升级（high_v2）

关键优化：
- 编码自动探测（`utf-8/gbk/gb18030`）。
- 高频误判修正：
  - 剂量单位修正（去除把“次”当剂量单位的误判）。
  - 增加非用药频次上下文过滤（如性生活/饮水/运动频次）。
- 增加用药动作词（口服/注射/饭前饭后等）。
- 增加常见药名词典，提升召回。

最终主集结果（high_v2r2）：
- 报告：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_digestive_prescription_candidates_from_csv_high_v2r2_report.json`
- `selected = 629`

---

## 3. 第二阶段：肿瘤科定向补充

输入：
- `/mnt/public/zxs/course/SFT_qwen/data/datasets/csv/肿瘤科5-10000.csv`

策略：
- 仅纳入消化系统相关肿瘤科室/病种。
- 沿用 high_v2 规则。
- 收紧泛肿瘤标签污染。

结果（high_v2r2）：
- 报告：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_digestive_prescription_candidates_from_oncology_high_v2r2_report.json`
- `selected = 47`

---

## 4. 第三阶段：JSON/JSONL 大数据源适配

### 4.1 train_0001_of_0001.json 适配

脚本：
- `/mnt/public/zxs/course/SFT_qwen/data_prep/filter_digestive_prescription_json_high_v2.py`

能力：
- 流式解析 JSON 顶层数组。
- 复用 high_v2 规则。
- 支持多进程批处理（workers/batch-size/max-outstanding）。

结果：
- 报告：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_digestive_prescription_candidates_from_train0001_high_v2_report.json`
- `selected = 1086`

### 4.2 DISC-Med-SFT_released.jsonl 适配

扩展能力：
- 自动识别 JSON/JSONL。
- 适配 `conversation` 多轮结构，提取 user-assistant 问答对。

结果：
- 报告：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_digestive_prescription_candidates_from_disc_med_high_v2_report.json`
- `selected = 242`

---

## 5. 第四阶段：统一格式与 run9 隔离

统一脚本：
- `/mnt/public/zxs/course/SFT_qwen/data_prep/unify_digestive_latest_no_run9.py`

统一 schema：
- `id`
- `source_dataset`
- `department`
- `title`
- `ask`
- `answer`
- `description`
- `digestive_reason`
- `signals`
- `messages`

run9 隔离规则：
- 明确排除 run9 系列文件，仅保留为外部测试用途。
- 典型文件：
  - `/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_external_24_latest_run9_1.json`
  - `/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_internal_59_run9_1.json`
  - `/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_data_v2_latest_run9_1.json`

### 去重决策变更（最终）

- 早期：有过归一化去重版本。
- 最终：默认不去重，仅在显式 `--dedup` 时去重。
- 原因：避免把“相似但仍有价值”的临床问答误删。

当前最终统一集（不去重）：
- 数据：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_digestive_prescription_candidates_unified_latest_no_run9_high_v2.json`
- 报告：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_digestive_prescription_candidates_unified_latest_no_run9_high_v2_report.json`
- 统计：
  - `combined_raw_count = 2004`
  - `dedup_enabled = false`
  - `dedup_count = 2004`
  - `removed_duplicates = 0`

来源构成（最终统一集）：
- csv_high_v2r2: 629
- oncology_high_v2r2: 47
- train0001_high_v2: 1086
- disc_med_high_v2: 242

---

## 6. 第五阶段：训练前增强（enhanced_v1）

增强脚本：
- `/mnt/public/zxs/course/SFT_qwen/data_prep/enhance_digestive_unified_for_sft.py`

增强策略：
- 问题侧消化关键词优先。
- 非消化专科噪声剔除。
- 保留高信号处方样本（药名+剂量+频次）。
- 最短问答长度过滤（可配置，支持放宽或关闭）。
- 来源平衡采样（每源上限，可配置，默认保留）。

增强产物：
- 数据：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_digestive_prescription_candidates_unified_latest_no_run9_high_v2_enhanced_v1.json`
- 报告：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_digestive_prescription_candidates_unified_latest_no_run9_high_v2_enhanced_v1_report.json`

增强产物（放宽长度阈值，enhanced_v2）：
- 数据：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_digestive_prescription_candidates_unified_latest_no_run9_high_v2_enhanced_v2.json`
- 报告：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_digestive_prescription_candidates_unified_latest_no_run9_high_v2_enhanced_v2_report.json`

增强结果：
- `total = 2004`
- `kept_before_balance = 1496`
- `rejected = 508`
- `final_count = 1166`

per-source kept：
- csv_high_v2r2: 497
- oncology_high_v2r2: 37
- train0001_high_v2: 500
- disc_med_high_v2: 132

增强结果（enhanced_v2，`min_ask_len=6`，`min_answer_len=20`，`max_per_source=500`）：
- `total = 2004`
- `kept_before_balance = 1561`
- `rejected = 443`
- `final_count = 1189`

per-source kept（enhanced_v2）：
- csv_high_v2r2: 500
- oncology_high_v2r2: 37
- train0001_high_v2: 500
- disc_med_high_v2: 152

---

## 7. 当前建议（对应最终版数据）

- 可用于直接训练的优先数据：
  - `enhanced_v2`（1189 条，长度阈值更宽松）
  - `enhanced_v1`（1166 条，更严格）
- 保留对照：
  - `unified_latest_no_run9_high_v2`（2004 条，不去重）

建议训练实践：
- 先用 `enhanced_v1` 跑 baseline（更稳）。
- 再用 `2004` 做对照实验，比较过拟合与泛化差异。
- run9 外测集保持隔离，不参与训练。

---

## 8. 关键脚本索引

- 主筛选（CSV）：`/mnt/public/zxs/course/SFT_qwen/data_prep/filter_digestive_prescription_csv.py`
- 大 JSON/JSONL 筛选：`/mnt/public/zxs/course/SFT_qwen/data_prep/filter_digestive_prescription_json_high_v2.py`
- 统一合并（排除 run9）：`/mnt/public/zxs/course/SFT_qwen/data_prep/unify_digestive_latest_no_run9.py`
- 训练前增强：`/mnt/public/zxs/course/SFT_qwen/data_prep/enhance_digestive_unified_for_sft.py`

---

## 9. 多专科参数化复用（新增）

为支持后续妇产科、儿科、心内科等专科扩展，已新增“主引擎 + 专科配置”模式：

- 通用主引擎（CSV）：`/mnt/public/zxs/course/SFT_qwen/data_prep/filter_specialty_prescription_csv.py`
- 专科配置目录：`/mnt/public/zxs/course/SFT_qwen/data_prep/specialty_configs/`

### 9.1 配置化内容

可按专科替换：
- 科室模式（direct/candidate/aux）。
- 专科语义词典（病种/症状）。
- 专科肿瘤语义与科室模式。
- 药名分组（`drug_groups`）与双层词典（`precision_group_names` + `recall_terms`）。

无需改动主引擎：
- 编码自动探测、CSV 解析、high_v2 分层、报告结构、messages 构建。

### 9.2 妇产科首轮验证

- 配置文件：`/mnt/public/zxs/course/SFT_qwen/data_prep/specialty_configs/obgyn.json`
- 输入数据：`/mnt/public/zxs/course/SFT_qwen/data/datasets/csv/妇产科6-28000.csv`
- 输出数据：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_obgyn_prescription_candidates_from_csv_high_v2.json`
- 输出报告：`/mnt/public/zxs/course/SFT_qwen/data/datasets/json/dataset_obgyn_prescription_candidates_from_csv_high_v2_report.json`

首轮结果（`min_tier=high`）：
- `total_rows = 183751`
- `specialty_related = 183750`
- `selected = 1061`
- `rows_with_precision_hit = 11944`
- `rows_with_recall_hit = 2649`

妇产科词典规模：
- `group_count = 10`
- `precision_size = 33`
- `recall_size = 10`
- `all_dict_size = 43`
