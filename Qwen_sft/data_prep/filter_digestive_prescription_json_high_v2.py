#!/usr/bin/env python3
import argparse
import json
import sys
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path
from typing import Any, Dict, Generator, List


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from filter_digestive_prescription_csv import (  # noqa: E402
    ALL_DIGESTIVE_DRUG_TERMS,
    COMMON_DRUG_TERMS,
    DIGESTIVE_ONCOLOGY_TERMS,
    DIGESTIVE_TERMS,
    NON_RX_FREQ_RE,
    PRECISION_DRUG_TERMS,
    RECALL_DRUG_TERMS,
    RX_ACTION_TERMS,
    RX_DOSE_RE,
    RX_DRUG_RE,
    RX_FREQ_RE,
    RX_FREQ_TERMS,
    RX_INTENT_TERMS,
    build_messages,
    classify_tier,
    classify_tier_v2,
    contains_any,
    normalize_text,
    tier_rank,
)


def iter_jsonl(path: Path, encoding: str) -> Generator[Dict[str, Any], None, None]:
    with path.open("r", encoding=encoding, errors="ignore") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                yield obj


def iter_json_array(path: Path, encoding: str) -> Generator[Dict[str, Any], None, None]:
    decoder = json.JSONDecoder()
    with path.open("r", encoding=encoding, errors="ignore") as f:
        while True:
            ch = f.read(1)
            if not ch:
                return
            if ch.isspace():
                continue
            if ch == "[":
                break
            raise ValueError("Input JSON must be a top-level array")

        buf = ""
        reached_end = False
        while True:
            while True:
                s = buf.lstrip()
                if s.startswith(","):
                    buf = s[1:]
                    continue
                if s:
                    buf = s
                    break
                if reached_end:
                    return
                chunk = f.read(1 << 20)
                if not chunk:
                    reached_end = True
                else:
                    buf += chunk

            if buf.startswith("]"):
                return

            try:
                obj, idx = decoder.raw_decode(buf)
            except json.JSONDecodeError:
                if reached_end:
                    raise
                chunk = f.read(1 << 20)
                if not chunk:
                    reached_end = True
                else:
                    buf += chunk
                continue

            if isinstance(obj, dict):
                yield obj
            buf = buf[idx:]


def iter_records(path: Path, encoding: str) -> Generator[Dict[str, Any], None, None]:
    if path.suffix.lower() == ".jsonl":
        yield from iter_jsonl(path, encoding)
        return

    with path.open("r", encoding=encoding, errors="ignore") as f:
        head = f.read(4096)
    first = ""
    for ch in head:
        if not ch.isspace():
            first = ch
            break

    if first == "[":
        yield from iter_json_array(path, encoding)
    else:
        yield from iter_jsonl(path, encoding)


def map_row_to_qa(row: Dict[str, Any]) -> Dict[str, str]:
    title = normalize_text(str(row.get("instruction", "") or ""))
    ask = normalize_text(str(row.get("input", "") or ""))
    answer = normalize_text(str(row.get("output", "") or ""))
    history = row.get("history", "")
    description = normalize_text("" if history is None else str(history))

    # Many instruction-tuning datasets keep `input` empty and place the user query in `instruction`.
    if not ask and title:
        ask = title

    if ask and answer:
        return {
            "title": title,
            "ask": ask,
            "answer": answer,
            "description": description,
        }

    conv = row.get("conversation")
    if isinstance(conv, list) and conv:
        first_user = ""
        last_user = ""
        last_assistant = ""
        prev_user = ""
        for msg in conv:
            if not isinstance(msg, dict):
                continue
            role = str(msg.get("role", "")).lower()
            content = normalize_text(str(msg.get("content", "") or ""))
            if not content:
                continue
            if role == "user":
                prev_user = content
                if not first_user:
                    first_user = content
                last_user = content
            elif role == "assistant":
                if prev_user:
                    last_user = prev_user
                last_assistant = content

        if last_user and last_assistant:
            mapped_title = normalize_text(first_user[:80])
            mapped_desc = normalize_text(str(row.get("source", "") or ""))
            return {
                "title": mapped_title,
                "ask": last_user,
                "answer": last_assistant,
                "description": mapped_desc,
            }

    return {
        "title": "",
        "ask": "",
        "answer": "",
        "description": "",
    }


def infer_digestive_reason(title: str, ask: str, answer: str, description: str) -> str:
    # Use question-side text first to reduce answer-side contamination.
    probe_text = normalize_text("\n".join([title, ask]))

    if contains_any(probe_text, DIGESTIVE_TERMS):
        return "text_digestive"
    if ("癌" in probe_text or "肿瘤" in probe_text) and contains_any(probe_text, DIGESTIVE_ONCOLOGY_TERMS):
        return "text_oncology_digestive"

    # Conservative fallback: allow answer-side digestive signals only when question has weak GI cues.
    weak_probe = {"腹", "胃", "肠", "肝", "胆", "胰", "恶心", "呕吐", "便", "食欲"}
    full_text = normalize_text("\n".join([title, ask, answer, description]))
    if contains_any(full_text, DIGESTIVE_TERMS) and contains_any(probe_text, weak_probe):
        return "text_digestive_fallback"
    return ""


def infer_department(digestive_reason: str) -> str:
    if digestive_reason == "text_oncology_digestive":
        return "消化肿瘤(推断)"
    if digestive_reason in {"text_digestive", "text_digestive_fallback"}:
        return "内科(推断)"
    return "未知"


def process_record(
    record_id: int,
    row: Dict[str, Any],
    rule_version: str,
    min_tier: str,
    require_precision_drug: bool = False,
) -> Dict[str, Any]:
    mapped = map_row_to_qa(row)
    title = mapped["title"]
    ask = mapped["ask"]
    answer = mapped["answer"]
    description = mapped["description"]

    rec_result: Dict[str, Any] = {
        "total_rows": 1,
        "skipped_empty_qa": 0,
        "digestive_related": 0,
        "selected": 0,
        "tier": None,
        "digestive_reason": None,
        "department": None,
        "has_precision_hit": 0,
        "has_recall_hit": 0,
        "record": None,
    }

    if not ask or not answer:
        rec_result["skipped_empty_qa"] = 1
        return rec_result

    digest_reason = infer_digestive_reason(title, ask, answer, description)
    if not digest_reason:
        return rec_result

    rec_result["digestive_related"] = 1
    rec_result["digestive_reason"] = digest_reason
    department = infer_department(digest_reason)
    rec_result["department"] = department

    full_text = normalize_text("\n".join([title, ask, answer, description]))
    has_rx_intent = contains_any(full_text, RX_INTENT_TERMS)
    has_rx_action = contains_any(full_text, RX_ACTION_TERMS)
    drug_regex_matches = RX_DRUG_RE.findall(full_text)
    precision_hits = [t for t in PRECISION_DRUG_TERMS if t in full_text]
    recall_hits = [t for t in RECALL_DRUG_TERMS if t in full_text]
    drug_dict_hits = [t for t in COMMON_DRUG_TERMS if t in full_text]
    rec_result["has_precision_hit"] = 1 if precision_hits else 0
    rec_result["has_recall_hit"] = 1 if recall_hits else 0
    if require_precision_drug and not precision_hits:
        return rec_result
    drug_match_count = len(drug_regex_matches) + len(drug_dict_hits)
    has_drug = drug_match_count > 0
    has_dose = bool(RX_DOSE_RE.search(full_text))
    has_freq = bool(RX_FREQ_RE.search(full_text) or contains_any(full_text.lower(), RX_FREQ_TERMS))
    has_non_rx_context = bool(NON_RX_FREQ_RE.search(full_text))

    if rule_version == "v2":
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

    rec_result["tier"] = tier
    if tier_rank(tier) < tier_rank(min_tier):
        return rec_result

    rec_result["selected"] = 1
    rec_result["record"] = {
        "id": record_id,
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
    return rec_result


def process_batch(
    batch: List[tuple],
    rule_version: str,
    min_tier: str,
    require_precision_drug: bool = False,
) -> Dict[str, Any]:
    stats = {
        "total_rows": 0,
        "skipped_empty_qa": 0,
        "digestive_related": 0,
        "selected": 0,
        "rows_with_precision_hit": 0,
        "rows_with_recall_hit": 0,
    }
    tier_counter: Counter = Counter()
    digest_reason_counter: Counter = Counter()
    selected_dept_counter: Counter = Counter()
    selected_records: List[dict] = []

    for record_id, row in batch:
        rr = process_record(
            record_id,
            row,
            rule_version,
            min_tier,
            require_precision_drug=require_precision_drug,
        )
        stats["total_rows"] += rr["total_rows"]
        stats["skipped_empty_qa"] += rr["skipped_empty_qa"]
        stats["digestive_related"] += rr["digestive_related"]
        stats["selected"] += rr["selected"]
        stats["rows_with_precision_hit"] += rr["has_precision_hit"]
        stats["rows_with_recall_hit"] += rr["has_recall_hit"]
        if rr["tier"] is not None:
            tier_counter[rr["tier"]] += 1
        if rr["digestive_reason"] is not None:
            digest_reason_counter[rr["digestive_reason"]] += 1
        if rr["selected"]:
            dept = rr["department"] or "未知"
            selected_dept_counter[dept] += 1
            selected_records.append(rr["record"])

    return {
        "stats": stats,
        "tier_counter": dict(tier_counter),
        "digest_reason_counter": dict(digest_reason_counter),
        "selected_dept_counter": dict(selected_dept_counter),
        "selected_records": selected_records,
    }


def merge_partials(
    partial: Dict[str, Any],
    stats: Dict[str, int],
    tier_counter: Counter,
    digest_reason_counter: Counter,
    selected_dept_counter: Counter,
    selected: List[dict],
) -> None:
    pstats = partial["stats"]
    stats["total_rows"] += pstats.get("total_rows", 0)
    stats["skipped_empty_qa"] += pstats.get("skipped_empty_qa", 0)
    stats["digestive_related"] += pstats.get("digestive_related", 0)
    stats["selected"] += pstats.get("selected", 0)
    stats["rows_with_precision_hit"] += pstats.get("rows_with_precision_hit", 0)
    stats["rows_with_recall_hit"] += pstats.get("rows_with_recall_hit", 0)
    tier_counter.update(partial.get("tier_counter", {}))
    digest_reason_counter.update(partial.get("digest_reason_counter", {}))
    selected_dept_counter.update(partial.get("selected_dept_counter", {}))
    selected.extend(partial.get("selected_records", []))


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter digestive-related prescription QA from JSON/JSONL dataset")
    parser.add_argument("--input-json", required=True, help="Path to source JSON/JSONL")
    parser.add_argument("--out-json", required=True, help="Path to selected JSON output")
    parser.add_argument("--out-report", required=True, help="Path to summary report JSON")
    parser.add_argument("--encoding", default="utf-8", help="Input encoding")
    parser.add_argument("--min-tier", choices=["low", "medium", "high"], default="high")
    parser.add_argument("--rule-version", choices=["v1", "v2"], default="v2")
    parser.add_argument("--require-precision-drug", action="store_true", help="Require at least one precision-dictionary drug hit")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes. 1 means single-process")
    parser.add_argument("--batch-size", type=int, default=2000, help="Number of records per processing batch")
    parser.add_argument("--max-outstanding", type=int, default=4, help="Max in-flight batches when workers>1")
    args = parser.parse_args()

    input_path = Path(args.input_json)
    out_path = Path(args.out_json)
    report_path = Path(args.out_report)

    selected: List[dict] = []
    stats = {
        "total_rows": 0,
        "skipped_empty_qa": 0,
        "digestive_related": 0,
        "selected": 0,
        "rows_with_precision_hit": 0,
        "rows_with_recall_hit": 0,
    }
    tier_counter: Counter = Counter()
    digest_reason_counter: Counter = Counter()
    selected_dept_counter: Counter = Counter()

    if args.workers <= 1:
        batch: List[tuple] = []
        for i, row in enumerate(iter_records(input_path, args.encoding), start=1):
            batch.append((i, row))
            if len(batch) >= args.batch_size:
                partial = process_batch(
                    batch,
                    args.rule_version,
                    args.min_tier,
                    require_precision_drug=args.require_precision_drug,
                )
                merge_partials(partial, stats, tier_counter, digest_reason_counter, selected_dept_counter, selected)
                batch = []
        if batch:
            partial = process_batch(
                batch,
                args.rule_version,
                args.min_tier,
                require_precision_drug=args.require_precision_drug,
            )
            merge_partials(partial, stats, tier_counter, digest_reason_counter, selected_dept_counter, selected)
    else:
        batch: List[tuple] = []
        futures = set()
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            for i, row in enumerate(iter_records(input_path, args.encoding), start=1):
                batch.append((i, row))
                if len(batch) >= args.batch_size:
                    futures.add(
                        ex.submit(
                            process_batch,
                            batch,
                            args.rule_version,
                            args.min_tier,
                            args.require_precision_drug,
                        )
                    )
                    batch = []
                if len(futures) >= args.max_outstanding:
                    done, futures = wait(futures, return_when=FIRST_COMPLETED)
                    for fut in done:
                        partial = fut.result()
                        merge_partials(partial, stats, tier_counter, digest_reason_counter, selected_dept_counter, selected)

            if batch:
                futures.add(
                    ex.submit(
                        process_batch,
                        batch,
                        args.rule_version,
                        args.min_tier,
                        args.require_precision_drug,
                    )
                )

            if futures:
                done, _ = wait(futures)
                for fut in done:
                    partial = fut.result()
                    merge_partials(partial, stats, tier_counter, digest_reason_counter, selected_dept_counter, selected)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "input_json": str(input_path),
        "output_json": str(out_path),
        "rows": stats,
        "threshold": {
            "min_tier": args.min_tier,
            "rule_version": args.rule_version,
            "require_precision_drug": args.require_precision_drug,
        },
        "dictionary_sizes": {
            "precision_size": len(PRECISION_DRUG_TERMS),
            "recall_size": len(RECALL_DRUG_TERMS),
            "all_dict_size": len(ALL_DIGESTIVE_DRUG_TERMS),
        },
        "dictionary_hit_rows": {
            "rows_with_precision_hit": stats["rows_with_precision_hit"],
            "rows_with_recall_hit": stats["rows_with_recall_hit"],
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
        "rule_version": args.rule_version,
        "top_selected_departments": selected_dept_counter.most_common(10),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
