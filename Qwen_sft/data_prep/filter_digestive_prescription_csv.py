#!/usr/bin/env python3
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import List


DEFAULT_SYSTEM_PROMPT = "你是一位严格遵循中国消化内科临床指南的医生。"


DIRECT_DEPT_PATTERNS = [
    re.compile(p)
    for p in [
        r"消化",
        r"肝病",
        r"肝胆",
        r"胃肠",
        r"脾胃",
        r"肛肠",
    ]
]

CANDIDATE_DEPT_PATTERNS = [
    re.compile(p)
    for p in [
        r"^内科$",
        r"^普通内科$",
    ]
]

PEDIATRIC_CANDIDATE_DEPT_PATTERNS = [
    re.compile(p)
    for p in [
        r"儿科",
        r"小儿",
        r"儿童",
        r"儿内",
    ]
]

DIGESTIVE_TERMS = {
    "胃炎", "胃溃疡", "十二指肠", "反流", "食管炎", "消化不良", "腹痛", "腹胀", "腹泻", "便秘",
    "黑便", "便血", "恶心", "呕吐", "幽门螺杆菌", "hp", "肝炎", "乙肝", "丙肝", "脂肪肝",
    "肝硬化", "转氨酶", "胆囊炎", "胆结石", "胰腺炎", "黄疸", "胃镜", "肠镜", "结肠", "直肠",
    "消化道", "上消化道", "下消化道",
}

DIGESTIVE_ONCOLOGY_TERMS = {
    "胃癌", "肝癌", "结肠癌", "直肠癌", "结直肠癌", "胰腺癌", "食管癌", "食道癌",
    "胆管癌", "胆囊癌", "胃肠道间质瘤", "消化道肿瘤", "肝转移", "腹膜转移",
}

DIGESTIVE_ONCOLOGY_DEPT_PATTERNS = [
    re.compile(p)
    for p in [
        r"胃", r"肝", r"胆", r"胰", r"食管", r"食道", r"结肠", r"直肠", r"结直肠", r"小肠", r"贲门", r"十二指肠",
    ]
]

RX_INTENT_TERMS = {
    "处方", "开药", "用药", "服药", "吃什么药", "吃啥药", "药方", "治疗方案", "联合用药", "停药",
}

RX_ACTION_TERMS = {
    "口服", "服用", "注射", "静滴", "静脉滴注", "肌注", "饭前", "饭后", "睡前", "餐前", "餐后", "冲服",
    "遵医嘱", "给药", "滴注", "含服", "外用", "涂抹",
}

RX_FREQ_TERMS = {
    "每日", "每天", "一日", "每晚", "每周", "bid", "tid", "qid", "qd", "次/日", "次/天",
}

NON_RX_CONTEXT_TERMS = {
    "性生活", "同房", "做爱", "饮水", "喝水", "运动", "锻炼", "复查", "体检", "化验", "检查", "散步",
}

PPI_TERMS = {
    "奥美拉唑", "埃索美拉唑", "艾司奥美拉唑", "泮托拉唑", "雷贝拉唑", "兰索拉唑", "右兰索拉唑",
}

H2_TERMS = {
    "法莫替丁", "雷尼替丁", "西咪替丁", "尼扎替丁",
}

MUCOSA_ANTACID_TERMS = {
    "硫糖铝", "枸橼酸铋钾", "胶体果胶铋", "铝碳酸镁", "瑞巴派特", "替普瑞酮", "吉法酯", "碳酸氢钠",
}

PROKINETIC_SPASMOLYTIC_TERMS = {
    "莫沙必利", "多潘立酮", "吗丁啉", "伊托必利", "曲美布汀", "匹维溴铵", "消旋山莨菪碱", "654-2",
}

ANTIEMETIC_TERMS = {
    "昂丹司琼", "托烷司琼", "甲氧氯普胺", "多拉司琼", "帕洛诺司琼", "异丙嗪",
}

ANTIDIARRHEAL_TERMS = {
    "蒙脱石散", "洛哌丁胺", "消旋卡多曲", "口服补液盐", "口服补液盐散",
}

PROBIOTIC_TERMS = {
    "双歧杆菌", "枯草杆菌二联活菌", "地衣芽孢杆菌", "酪酸梭菌", "乳酸菌素", "布拉氏酵母菌",
}

LAXATIVE_TERMS = {
    "乳果糖", "聚乙二醇", "比沙可啶", "聚卡波非钙", "开塞露",
}

IBD_TERMS = {
    "美沙拉嗪", "柳氮磺吡啶", "布地奈德", "泼尼松", "英夫利西单抗", "阿达木单抗", "维得利珠单抗", "乌司奴单抗", "托法替布",
}

HP_ERADICATION_TERMS = {
    "阿莫西林", "克拉霉素", "甲硝唑", "替硝唑", "左氧氟沙星", "呋喃唑酮", "四环素", "铋剂",
}

HBV_LIVER_SUPPORT_TERMS = {
    "恩替卡韦", "替诺福韦", "阿德福韦", "拉米夫定", "替比夫定", "丙酚替诺福韦", "富马酸替诺福韦二吡呋酯",
    "熊去氧胆酸", "还原型谷胱甘肽", "门冬氨酸鸟氨酸", "利福昔明",
}

ANALGESIC_TERMS = {
    "吗啡", "羟考酮", "芬太尼", "对乙酰氨基酚", "曲马多",
}

DIGESTIVE_DRUG_GROUPS = {
    "ppi": PPI_TERMS,
    "h2": H2_TERMS,
    "mucosa_antacid": MUCOSA_ANTACID_TERMS,
    "prokinetic_spasmolytic": PROKINETIC_SPASMOLYTIC_TERMS,
    "antiemetic": ANTIEMETIC_TERMS,
    "antidiarrheal": ANTIDIARRHEAL_TERMS,
    "probiotic": PROBIOTIC_TERMS,
    "laxative": LAXATIVE_TERMS,
    "ibd": IBD_TERMS,
    "hp_eradication": HP_ERADICATION_TERMS,
    "hbv_liver_support": HBV_LIVER_SUPPORT_TERMS,
    "analgesic": ANALGESIC_TERMS,
}

PRECISION_DRUG_GROUP_NAMES = {
    "ppi", "h2", "mucosa_antacid", "prokinetic_spasmolytic", "antiemetic", "antidiarrheal", "probiotic",
    "laxative", "ibd", "hp_eradication", "hbv_liver_support",
}

PRECISION_DRUG_TERMS = set().union(*[DIGESTIVE_DRUG_GROUPS[g] for g in PRECISION_DRUG_GROUP_NAMES])
RECALL_DRUG_TERMS = {
    "dexlansoprazole", "TAF", "TDF", "ORS", "索拉非尼", "仑伐替尼", "卡培他滨", "奥沙利铂", "替吉奥", "多柔比星",
}
ALL_DIGESTIVE_DRUG_TERMS = PRECISION_DRUG_TERMS | RECALL_DRUG_TERMS

# Keep this alias for backward compatibility with existing filtering logic/imports.
COMMON_DRUG_TERMS = ALL_DIGESTIVE_DRUG_TERMS

RX_DRUG_RE = re.compile(
    r"([A-Za-z\u4e00-\u9fff0-9\-·]{2,30}?(?:片|胶囊|颗粒|注射液|注射用|口服液|滴丸|丸|散|混悬液|乳膏|栓|制剂|糖浆))"
)

RX_DOSE_RE = re.compile(
    r"([0-9]+(?:\.[0-9]+)?)\s*(mg|g|ml|ug|μg|iu|毫克|克|毫升|微克|单位|片|粒|袋|支|丸|滴)",
    re.IGNORECASE,
)

RX_FREQ_RE = re.compile(
    r"(每日\s*[0-9一二两三四五六七八九十]+\s*次|每天\s*[0-9一二两三四五六七八九十]+\s*次|一日\s*[0-9一二两三四五六七八九十]+\s*次|每\s*[0-9一二两三四五六七八九十]+\s*小时\s*1?次|每周\s*[0-9一二两三四五六七八九十]+\s*次|每晚\s*1?次|qd|bid|tid|qid|q\d+h|次/日|次/天)",
    re.IGNORECASE,
)

NON_RX_FREQ_RE = re.compile(
    r"(性生活|同房|做爱|饮水|喝水|运动|锻炼|散步|复查|体检|化验|检查).{0,10}(每日|每天|每周|每月|一日|次/日|次/天|次)",
    re.IGNORECASE,
)


def normalize_text(s: str) -> str:
    t = (s or "").replace("\r", "").strip()
    t = re.sub(r"\s+", " ", t)
    return t


def resolve_encoding(path: Path, encoding_arg: str) -> str:
    if encoding_arg.lower() != "auto":
        return encoding_arg

    candidates = ["utf-8-sig", "utf-8", "gb18030", "gbk"]
    for enc in candidates:
        try:
            with path.open("r", encoding=enc, errors="strict", newline="") as f:
                header = f.readline()
            if "department" in header and "ask" in header and "answer" in header:
                return enc
        except Exception:
            continue
    return "gb18030"


def is_valid_department(department: str) -> bool:
    # Guard against malformed rows where a whole CSV fragment leaks into department.
    if not department:
        return False
    if "," in department or "\n" in department or "\r" in department:
        return False
    if len(department) > 30:
        return False
    return True


def tier_rank(name: str) -> int:
    mapping = {"low": 1, "medium": 2, "high": 3}
    return mapping.get(name, 2)


def contains_any(text: str, terms: set) -> bool:
    lt = text.lower()
    for t in terms:
        if t in text or t in lt:
            return True
    return False


def match_patterns(text: str, patterns: List[re.Pattern]) -> bool:
    return any(p.search(text) for p in patterns)


def classify_tier(has_rx_intent: bool, has_drug: bool, has_dose: bool, has_freq: bool) -> str:
    if has_drug and has_dose and has_freq:
        return "high"
    if has_drug and (has_dose or has_freq):
        return "medium"
    if has_rx_intent and has_drug:
        return "low"
    return "none"


def classify_tier_v2(
    has_rx_intent: bool,
    has_rx_action: bool,
    has_drug: bool,
    has_dose: bool,
    has_freq: bool,
    has_non_rx_context: bool,
    drug_match_count: int,
) -> str:
    if has_drug and has_dose and has_freq and (has_rx_intent or has_rx_action) and not has_non_rx_context:
        return "high"
    if has_drug and has_dose and has_freq and drug_match_count >= 2 and not has_non_rx_context:
        return "high"
    if has_drug and ((has_dose and has_rx_action) or (has_freq and has_rx_action) or (has_dose and has_freq)) and not has_non_rx_context:
        return "medium"
    if has_drug and (has_rx_intent or has_rx_action):
        return "low"
    return "none"


def is_digestive_oncology_department(department: str) -> bool:
    # Accept explicit digestive oncology departments, and treat generic oncology departments as undecided.
    if department in {"肿瘤科", "肿瘤", "肿瘤疾病"}:
        return False
    return any(p.search(department) for p in DIGESTIVE_ONCOLOGY_DEPT_PATTERNS)


def build_messages(title: str, ask: str, answer: str) -> List[dict]:
    q = normalize_text(f"标题：{title}\n问题：{ask}")
    a = normalize_text(answer)
    return [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": q},
        {"role": "assistant", "content": a},
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter digestive-related prescription QA from a CSV dataset")
    parser.add_argument("--input-csv", required=True, help="Path to source CSV")
    parser.add_argument("--out-json", required=True, help="Path to selected JSON output")
    parser.add_argument("--out-report", required=True, help="Path to summary report JSON")
    parser.add_argument("--encoding", default="auto", help="CSV encoding, e.g. utf-8/gbk/gb18030/auto")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter, default ','")
    parser.add_argument("--min-tier", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--rule-version", choices=["v1", "v2"], default="v2")
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    out_path = Path(args.out_json)
    report_path = Path(args.out_report)

    resolved_encoding = resolve_encoding(input_path, args.encoding)

    selected: List[dict] = []
    stats = {
        "total_rows": 0,
        "skipped_empty_qa": 0,
        "skipped_bad_department": 0,
        "digestive_related": 0,
        "selected": 0,
    }
    tier_counter: Counter = Counter()
    digest_reason_counter: Counter = Counter()
    selected_dept_counter: Counter = Counter()
    rows_with_precision_hit = 0
    rows_with_recall_hit = 0

    with input_path.open("r", encoding=resolved_encoding, errors="ignore", newline="") as f:
        reader = csv.DictReader(f, delimiter=args.delimiter)
        if not reader.fieldnames:
            raise ValueError("CSV header is empty or unreadable")
        required_fields = {"department", "title", "ask", "answer"}
        missing_fields = required_fields - set(reader.fieldnames)
        if missing_fields:
            raise ValueError(f"CSV missing required fields: {sorted(missing_fields)}; got {reader.fieldnames}")
        for i, row in enumerate(reader, start=1):
            stats["total_rows"] += 1

            department = normalize_text(row.get("department", ""))
            if not is_valid_department(department):
                stats["skipped_bad_department"] += 1
                continue
            title = normalize_text(row.get("title", ""))
            ask = normalize_text(row.get("ask", ""))
            answer = normalize_text(row.get("answer", ""))
            description = normalize_text(row.get("description", ""))

            if not ask or not answer:
                stats["skipped_empty_qa"] += 1
                continue

            full_text = normalize_text("\n".join([title, ask, answer, description]))
            oncology_probe_text = normalize_text("\n".join([department, title, ask]))

            digestive_related = False
            digest_reason = ""
            if match_patterns(department, DIRECT_DEPT_PATTERNS):
                digestive_related = True
                digest_reason = "dept_direct"
            elif ("肿瘤" in department or "癌" in department) and (
                is_digestive_oncology_department(department)
                or (department in {"肿瘤科", "肿瘤"} and contains_any(oncology_probe_text, DIGESTIVE_ONCOLOGY_TERMS))
            ):
                digestive_related = True
                digest_reason = "dept_oncology_digestive"
            elif match_patterns(department, CANDIDATE_DEPT_PATTERNS) and contains_any(full_text, DIGESTIVE_TERMS):
                digestive_related = True
                digest_reason = "dept_internal_semantic"
            elif match_patterns(department, PEDIATRIC_CANDIDATE_DEPT_PATTERNS) and contains_any(full_text, DIGESTIVE_TERMS):
                digestive_related = True
                digest_reason = "dept_pediatric_semantic"

            if not digestive_related:
                continue

            stats["digestive_related"] += 1
            digest_reason_counter[digest_reason] += 1

            has_rx_intent = contains_any(full_text, RX_INTENT_TERMS)
            has_rx_action = contains_any(full_text, RX_ACTION_TERMS)
            drug_regex_matches = RX_DRUG_RE.findall(full_text)
            precision_hits = [t for t in PRECISION_DRUG_TERMS if t in full_text]
            recall_hits = [t for t in RECALL_DRUG_TERMS if t in full_text]
            drug_dict_hits = [t for t in COMMON_DRUG_TERMS if t in full_text]
            drug_match_count = len(drug_regex_matches) + len(drug_dict_hits)
            has_drug = drug_match_count > 0
            has_dose = bool(RX_DOSE_RE.search(full_text))
            has_freq = bool(RX_FREQ_RE.search(full_text) or contains_any(full_text.lower(), RX_FREQ_TERMS))
            has_non_rx_context = bool(NON_RX_FREQ_RE.search(full_text))

            if precision_hits:
                rows_with_precision_hit += 1
            if recall_hits:
                rows_with_recall_hit += 1

            if args.rule_version == "v2":
                tier = classify_tier_v2(
                    has_rx_intent=has_rx_intent,
                    has_rx_action=has_rx_action,
                    has_drug=has_drug,
                    has_dose=has_dose,
                    has_freq=has_freq,
                    has_non_rx_context=has_non_rx_context,
                    drug_match_count=drug_match_count,
                )
            else:
                tier = classify_tier(has_rx_intent, has_drug, has_dose, has_freq)
            tier_counter[tier] += 1

            if tier_rank(tier) < tier_rank(args.min_tier):
                continue

            rec = {
                "id": i,
                "department": department,
                "title": title,
                "ask": ask,
                "answer": answer,
                "description": description,
                "digestive_reason": digest_reason,
                "signals": {
                    "has_rx_intent": has_rx_intent,
                    "has_rx_action": has_rx_action,
                    "has_drug": has_drug,
                    "has_dose": has_dose,
                    "has_freq": has_freq,
                    "has_non_rx_context": has_non_rx_context,
                    "precision_drug_hit_count": len(precision_hits),
                    "precision_drug_hits": sorted(precision_hits),
                    "recall_drug_hit_count": len(recall_hits),
                    "recall_drug_hits": sorted(recall_hits),
                    "drug_dict_hit_count": len(drug_dict_hits),
                    "drug_dict_hits": sorted(drug_dict_hits),
                    "drug_match_count": drug_match_count,
                    "tier": tier,
                },
                "messages": build_messages(title, ask, answer),
            }
            selected.append(rec)
            selected_dept_counter[department] += 1

    stats["selected"] = len(selected)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "input_csv": str(input_path),
        "output_json": str(out_path),
        "resolved_encoding": resolved_encoding,
        "rows": stats,
        "threshold": {"min_tier": args.min_tier, "rule_version": args.rule_version},
        "dictionary_sizes": {
            "precision_size": len(PRECISION_DRUG_TERMS),
            "recall_size": len(RECALL_DRUG_TERMS),
            "all_dict_size": len(ALL_DIGESTIVE_DRUG_TERMS),
        },
        "dictionary_hit_rows": {
            "rows_with_precision_hit": rows_with_precision_hit,
            "rows_with_recall_hit": rows_with_recall_hit,
        },
        "digestive_reason_counts": dict(digest_reason_counter),
        "tier_counts_before_threshold": dict(tier_counter),
        "top_selected_departments": selected_dept_counter.most_common(20),
        "sample_preview": selected[:5],
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "rows": stats,
        "min_tier": args.min_tier,
        "top_selected_departments": selected_dept_counter.most_common(10),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
