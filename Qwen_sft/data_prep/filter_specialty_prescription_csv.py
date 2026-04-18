#!/usr/bin/env python3
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Pattern, Set


DEFAULT_RX_INTENT_TERMS = {
    "处方", "开药", "用药", "服药", "吃什么药", "吃啥药", "药方", "治疗方案", "联合用药", "停药",
}

DEFAULT_RX_ACTION_TERMS = {
    "口服", "服用", "注射", "静滴", "静脉滴注", "肌注", "饭前", "饭后", "睡前", "餐前", "餐后", "冲服",
    "遵医嘱", "给药", "滴注", "含服", "外用", "涂抹",
}

DEFAULT_RX_FREQ_TERMS = {
    "每日", "每天", "一日", "每晚", "每周", "bid", "tid", "qid", "qd", "次/日", "次/天",
}

DEFAULT_NON_RX_CONTEXT_TERMS = {
    "性生活", "同房", "做爱", "饮水", "喝水", "运动", "锻炼", "复查", "体检", "化验", "检查", "散步",
}

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


def contains_any(text: str, terms: Set[str]) -> bool:
    lt = text.lower()
    for t in terms:
        if t in text or t in lt:
            return True
    return False


def match_patterns(text: str, patterns: List[Pattern]) -> bool:
    return any(p.search(text) for p in patterns)


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


def compile_patterns(items: List[str]) -> List[Pattern]:
    return [re.compile(p) for p in items]


def load_config(path: Path) -> Dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))

    drug_groups: Dict[str, Set[str]] = {
        k: set(v) for k, v in (cfg.get("drug_groups") or {}).items()
    }
    precision_names = set(cfg.get("precision_group_names") or [])
    precision_terms = set().union(*[drug_groups[g] for g in precision_names if g in drug_groups]) if precision_names else set()
    recall_terms = set(cfg.get("recall_terms") or [])

    cfg_runtime = {
        "specialty_name": cfg.get("specialty_name", "专科"),
        "default_system_prompt": cfg.get("default_system_prompt", "你是一位严格遵循中国临床指南的医生。"),
        "direct_dept_patterns": compile_patterns(cfg.get("direct_dept_patterns") or []),
        "candidate_dept_patterns": compile_patterns(cfg.get("candidate_dept_patterns") or []),
        "aux_candidate_dept_patterns": compile_patterns(cfg.get("aux_candidate_dept_patterns") or []),
        "specialty_terms": set(cfg.get("specialty_terms") or []),
        "specialty_oncology_terms": set(cfg.get("specialty_oncology_terms") or []),
        "specialty_oncology_dept_patterns": compile_patterns(cfg.get("specialty_oncology_dept_patterns") or []),
        "rx_intent_terms": set(cfg.get("rx_intent_terms") or list(DEFAULT_RX_INTENT_TERMS)),
        "rx_action_terms": set(cfg.get("rx_action_terms") or list(DEFAULT_RX_ACTION_TERMS)),
        "rx_freq_terms": set(cfg.get("rx_freq_terms") or list(DEFAULT_RX_FREQ_TERMS)),
        "non_rx_context_terms": set(cfg.get("non_rx_context_terms") or list(DEFAULT_NON_RX_CONTEXT_TERMS)),
        "drug_groups": drug_groups,
        "precision_terms": precision_terms,
        "recall_terms": recall_terms,
        "all_drug_terms": precision_terms | recall_terms,
    }
    return cfg_runtime


def build_messages(system_prompt: str, title: str, ask: str, answer: str) -> List[dict]:
    q = normalize_text(f"标题：{title}\n问题：{ask}")
    a = normalize_text(answer)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": q},
        {"role": "assistant", "content": a},
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generic specialty prescription filter from CSV")
    parser.add_argument("--config-json", required=True)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    parser.add_argument("--encoding", default="auto")
    parser.add_argument("--delimiter", default=",")
    parser.add_argument("--min-tier", choices=["low", "medium", "high"], default="high")
    args = parser.parse_args()

    cfg = load_config(Path(args.config_json))
    input_path = Path(args.input_csv)
    out_path = Path(args.out_json)
    report_path = Path(args.out_report)

    selected: List[dict] = []
    stats = {
        "total_rows": 0,
        "skipped_empty_qa": 0,
        "skipped_bad_department": 0,
        "specialty_related": 0,
        "selected": 0,
        "rows_with_precision_hit": 0,
        "rows_with_recall_hit": 0,
    }
    tier_counter: Counter = Counter()
    reason_counter: Counter = Counter()
    selected_dept_counter: Counter = Counter()

    resolved_encoding = resolve_encoding(input_path, args.encoding)
    with input_path.open("r", encoding=resolved_encoding, errors="ignore", newline="") as f:
        reader = csv.DictReader(f, delimiter=args.delimiter)
        if not reader.fieldnames:
            raise ValueError("CSV header is empty or unreadable")
        required_fields = {"department", "title", "ask", "answer"}
        missing = required_fields - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV missing required fields: {sorted(missing)}")

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
            probe_text = normalize_text("\n".join([department, title, ask]))

            specialty_related = False
            reason = ""
            if match_patterns(department, cfg["direct_dept_patterns"]):
                specialty_related = True
                reason = "dept_direct"
            elif (
                ("肿瘤" in department or "癌" in department)
                and (
                    match_patterns(department, cfg["specialty_oncology_dept_patterns"])
                    or (department in {"肿瘤科", "肿瘤"} and contains_any(probe_text, cfg["specialty_oncology_terms"]))
                )
            ):
                specialty_related = True
                reason = "dept_oncology_specialty"
            elif match_patterns(department, cfg["candidate_dept_patterns"]) and contains_any(full_text, cfg["specialty_terms"]):
                specialty_related = True
                reason = "dept_candidate_semantic"
            elif match_patterns(department, cfg["aux_candidate_dept_patterns"]) and contains_any(full_text, cfg["specialty_terms"]):
                specialty_related = True
                reason = "dept_aux_candidate_semantic"

            if not specialty_related:
                continue

            stats["specialty_related"] += 1
            reason_counter[reason] += 1

            has_rx_intent = contains_any(full_text, cfg["rx_intent_terms"])
            has_rx_action = contains_any(full_text, cfg["rx_action_terms"])
            has_dose = bool(RX_DOSE_RE.search(full_text))
            has_freq = bool(RX_FREQ_RE.search(full_text) or contains_any(full_text.lower(), cfg["rx_freq_terms"]))
            has_non_rx_context = bool(NON_RX_FREQ_RE.search(full_text))

            drug_regex_hits = RX_DRUG_RE.findall(full_text)
            precision_hits = [t for t in cfg["precision_terms"] if t in full_text]
            recall_hits = [t for t in cfg["recall_terms"] if t in full_text]
            all_drug_hits = [t for t in cfg["all_drug_terms"] if t in full_text]
            if precision_hits:
                stats["rows_with_precision_hit"] += 1
            if recall_hits:
                stats["rows_with_recall_hit"] += 1

            drug_match_count = len(drug_regex_hits) + len(all_drug_hits)
            has_drug = drug_match_count > 0

            tier = classify_tier_v2(
                has_rx_intent=has_rx_intent,
                has_rx_action=has_rx_action,
                has_drug=has_drug,
                has_dose=has_dose,
                has_freq=has_freq,
                has_non_rx_context=has_non_rx_context,
                drug_match_count=drug_match_count,
            )
            tier_counter[tier] += 1
            if tier_rank(tier) < tier_rank(args.min_tier):
                continue

            rec = {
                "id": i,
                "source_dataset": input_path.name,
                "department": department,
                "title": title,
                "ask": ask,
                "answer": answer,
                "description": description,
                "specialty_reason": reason,
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
                    "drug_dict_hit_count": len(all_drug_hits),
                    "drug_dict_hits": sorted(all_drug_hits),
                    "drug_match_count": drug_match_count,
                    "tier": tier,
                },
                "messages": build_messages(cfg["default_system_prompt"], title, ask, answer),
            }
            selected.append(rec)
            selected_dept_counter[department] += 1

    stats["selected"] = len(selected)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "specialty_name": cfg["specialty_name"],
        "input_csv": str(input_path),
        "output_json": str(out_path),
        "resolved_encoding": resolved_encoding,
        "rows": stats,
        "threshold": {"min_tier": args.min_tier, "rule_version": "v2"},
        "dictionary_sizes": {
            "group_count": len(cfg["drug_groups"]),
            "precision_size": len(cfg["precision_terms"]),
            "recall_size": len(cfg["recall_terms"]),
            "all_dict_size": len(cfg["all_drug_terms"]),
        },
        "specialty_reason_counts": dict(reason_counter),
        "tier_counts_before_threshold": dict(tier_counter),
        "top_selected_departments": selected_dept_counter.most_common(20),
        "sample_preview": selected[:5],
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "specialty_name": cfg["specialty_name"],
        "rows": stats,
        "top_selected_departments": selected_dept_counter.most_common(10),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
