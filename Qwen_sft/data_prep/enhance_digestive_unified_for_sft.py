#!/usr/bin/env python3
import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

DIGESTIVE_TERMS = {
    "胃", "肠", "肝", "胆", "胰", "消化", "腹", "便", "反流", "幽门",
    "结肠", "直肠", "食管", "食道", "乙肝", "脂肪肝", "胆囊", "胰腺",
    "腹泻", "便秘", "胃炎", "肠炎", "肝炎", "胆结石", "胰腺炎", "幽门螺杆菌",
}

NON_DIGESTIVE_TERMS = {
    "皮肤", "眼", "耳鼻喉", "口腔", "妇科", "产科", "骨科", "呼吸", "肺", "心脏",
    "肾", "泌尿", "甲状腺", "神经", "乳腺", "前列腺", "精神", "抑郁",
}


def normalize_text(text: Any) -> str:
    s = "" if text is None else str(text)
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def contains_any(text: str, terms: set) -> bool:
    return any(t in text for t in terms)


def safe_bool(v: Any) -> bool:
    return bool(v) if isinstance(v, bool) else False


def main() -> None:
    parser = argparse.ArgumentParser(description="Enhance unified digestive dataset for SFT")
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-per-source", type=int, default=600)
    parser.add_argument("--min-ask-len", type=int, default=6)
    parser.add_argument("--min-answer-len", type=int, default=20)
    args = parser.parse_args()

    random.seed(args.seed)

    src_path = Path(args.input_json)
    out_path = Path(args.out_json)
    report_path = Path(args.out_report)

    data = json.loads(src_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list")

    stats = Counter()
    by_source: Dict[str, List[dict]] = defaultdict(list)
    reject_samples: List[dict] = []

    for rec in data:
        stats["total"] += 1
        title = normalize_text(rec.get("title", ""))
        ask = normalize_text(rec.get("ask", ""))
        answer = normalize_text(rec.get("answer", ""))
        qa_text = f"{title} {ask}"

        has_digestive = contains_any(qa_text, DIGESTIVE_TERMS)
        has_non_digestive = contains_any(qa_text, NON_DIGESTIVE_TERMS)

        signals = rec.get("signals", {}) if isinstance(rec.get("signals", {}), dict) else {}
        has_drug = safe_bool(signals.get("has_drug"))
        has_dose = safe_bool(signals.get("has_dose"))
        has_freq = safe_bool(signals.get("has_freq"))
        has_high_signal = has_drug and has_dose and has_freq

        quality_ok = len(ask) >= args.min_ask_len and len(answer) >= args.min_answer_len

        # Keep rule:
        # 1) question side should be digestive-related
        # 2) avoid clear non-digestive specialty questions
        # 3) keep high-signal prescription structure and minimal text quality (thresholds are configurable)
        keep = has_digestive and (not has_non_digestive) and has_high_signal and quality_ok

        if keep:
            source = str(rec.get("source_dataset", "unknown"))
            by_source[source].append(rec)
            stats["kept_before_balance"] += 1
        else:
            stats["rejected"] += 1
            if len(reject_samples) < 20:
                reject_samples.append(
                    {
                        "title": rec.get("title", ""),
                        "source_dataset": rec.get("source_dataset", ""),
                        "has_digestive": has_digestive,
                        "has_non_digestive": has_non_digestive,
                        "has_high_signal": has_high_signal,
                        "ask_len": len(ask),
                        "answer_len": len(answer),
                    }
                )

    balanced: List[dict] = []
    per_source_kept = {}
    for source, rows in by_source.items():
        random.shuffle(rows)
        selected = rows[: args.max_per_source]
        per_source_kept[source] = len(selected)
        balanced.extend(selected)

    # Re-index IDs after enhancement.
    for i, rec in enumerate(balanced, start=1):
        rec["id"] = i

    stats["final_count"] = len(balanced)

    report = {
        "input_json": str(src_path),
        "output_json": str(out_path),
        "config": {
            "seed": args.seed,
            "max_per_source": args.max_per_source,
            "min_ask_len": args.min_ask_len,
            "min_answer_len": args.min_answer_len,
        },
        "counts": dict(stats),
        "per_source_kept": per_source_kept,
        "reject_samples": reject_samples,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(balanced, ensure_ascii=False, indent=2), encoding="utf-8")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
