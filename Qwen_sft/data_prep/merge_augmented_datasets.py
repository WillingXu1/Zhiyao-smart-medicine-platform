#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


def normalize_q(q: str) -> str:
    return re.sub(r"\s+", "", q or "")


def load(path: Path) -> List[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge conversation datasets by unique normalized user query.")
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", default="")
    args = parser.parse_args()

    merged: List[dict] = []
    seen = set()
    stats: Dict[str, int] = {"input_records": 0, "merged_records": 0, "duplicates_skipped": 0}

    for p in args.inputs:
        rows = load(Path(p))
        stats["input_records"] += len(rows)
        for r in rows:
            msgs = r.get("messages", [])
            if len(msgs) < 3:
                continue
            q = normalize_q(str(msgs[1].get("content", "")))
            if not q:
                continue
            if q in seen:
                stats["duplicates_skipped"] += 1
                continue
            seen.add(q)
            merged.append(r)

    stats["merged_records"] = len(merged)
    save(Path(args.output), merged)

    if args.report:
        save(Path(args.report), stats)

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
