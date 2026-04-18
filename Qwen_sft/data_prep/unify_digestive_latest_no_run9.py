#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List


STD_KEYS = [
    "id",
    "source_dataset",
    "department",
    "title",
    "ask",
    "answer",
    "description",
    "digestive_reason",
    "signals",
    "messages",
]

RUN9_FILE_RE = re.compile(r"(^|[_\-])run9([_\-]|$)", re.IGNORECASE)


def normalize_text(text: Any) -> str:
    s = "" if text is None else str(text)
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def qa_hash(item: Dict[str, Any]) -> str:
    key = "||".join(
        [
            normalize_text(item.get("title", "")),
            normalize_text(item.get("ask", "")),
            normalize_text(item.get("answer", "")),
        ]
    )
    return hashlib.md5(key.encode("utf-8", errors="ignore")).hexdigest()


def standardize_record(rec: Dict[str, Any], source_name: str, out_id: int) -> Dict[str, Any]:
    std = {
        "id": out_id,
        "source_dataset": source_name,
        "department": rec.get("department", ""),
        "title": rec.get("title", ""),
        "ask": rec.get("ask", ""),
        "answer": rec.get("answer", ""),
        "description": rec.get("description", ""),
        "digestive_reason": rec.get("digestive_reason", ""),
        "signals": rec.get("signals", {}),
        "messages": rec.get("messages", []),
    }
    # Keep exact key order as requested.
    return {k: std[k] for k in STD_KEYS}


def load_json_list(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Unify latest digestive datasets and exclude run9 sources")
    parser.add_argument("--inputs", nargs="+", required=True, help="Input JSON files")
    parser.add_argument("--out-json", required=True, help="Unified output JSON path")
    parser.add_argument("--out-report", required=True, help="Summary report JSON path")
    parser.add_argument(
        "--scan-dir",
        default="/mnt/public/zxs/course/SFT_qwen/data/datasets/json",
        help="Directory to scan for *run9*.json files",
    )
    parser.add_argument(
        "--dedup",
        action="store_true",
        help="Enable exact QA dedup by normalized title+ask+answer hash (default: disabled)",
    )
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.inputs]
    out_json = Path(args.out_json)
    out_report = Path(args.out_report)

    source_raw_counts: Dict[str, int] = {}
    per_source_after_dedup: Dict[str, int] = {}

    seen = set()
    unified: List[Dict[str, Any]] = []
    combined_raw_count = 0
    removed_duplicates = 0

    for p in input_paths:
        p_str_lower = str(p).lower()
        if "run9" in p_str_lower:
            continue
        if not p.exists():
            continue

        rows = load_json_list(p)
        source_name = p.name
        source_raw_counts[source_name] = len(rows)
        per_source_after_dedup[source_name] = 0
        combined_raw_count += len(rows)

        for rec in rows:
            if args.dedup:
                candidate = {
                    "title": rec.get("title", ""),
                    "ask": rec.get("ask", ""),
                    "answer": rec.get("answer", ""),
                }
                h = qa_hash(candidate)
                if h in seen:
                    removed_duplicates += 1
                    continue
                seen.add(h)
            std = standardize_record(rec, source_name=source_name, out_id=len(unified) + 1)
            unified.append(std)
            per_source_after_dedup[source_name] += 1

    excluded_run9_files = sorted(
        [
            f.name
            for f in Path(args.scan_dir).glob("*.json")
            if f.is_file() and RUN9_FILE_RE.search(f.stem) and "no_run9" not in f.stem.lower()
        ]
    )

    report = {
        "dedup_enabled": args.dedup,
        "source_raw_counts": source_raw_counts,
        "combined_raw_count": combined_raw_count,
        "dedup_count": len(unified),
        "removed_duplicates": removed_duplicates,
        "per_source_after_dedup": per_source_after_dedup,
        "excluded_run9_files": excluded_run9_files,
        "schema_keys": STD_KEYS,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(unified, ensure_ascii=False, indent=2), encoding="utf-8")
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
