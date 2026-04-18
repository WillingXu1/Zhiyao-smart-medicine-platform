#!/usr/bin/env python3
import argparse
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def load_rows(path: Path) -> List[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list")
    rows = [r for r in data if isinstance(r, dict)]
    return rows


def split_stratified(rows: List[dict], train_ratio: float, seed: int) -> Tuple[List[dict], List[dict], Dict[str, Dict[str, int]]]:
    rng = random.Random(seed)
    buckets: Dict[str, List[dict]] = defaultdict(list)
    for r in rows:
        buckets[str(r.get("source", "unknown"))].append(r)

    train: List[dict] = []
    val: List[dict] = []
    per_source: Dict[str, Dict[str, int]] = {}

    for source, items in buckets.items():
        items = list(items)
        rng.shuffle(items)

        n = len(items)
        n_train = int(round(n * train_ratio))
        # Keep both sides non-empty for buckets with >=2 samples.
        if n >= 2:
            n_train = max(1, min(n - 1, n_train))
        else:
            n_train = n

        train_items = items[:n_train]
        val_items = items[n_train:]

        train.extend(train_items)
        val.extend(val_items)
        per_source[source] = {
            "total": n,
            "train": len(train_items),
            "val": len(val_items),
        }

    # Global shuffle to avoid source blocks.
    rng.shuffle(train)
    rng.shuffle(val)

    # Reindex IDs for train/val files.
    for i, r in enumerate(train, start=1):
        r["id"] = i
    for i, r in enumerate(val, start=1):
        r["id"] = i

    return train, val, per_source


def main() -> None:
    parser = argparse.ArgumentParser(description="Create stratified train/val splits for digestive QA dataset")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ratios", default="0.9,0.8", help="Comma separated train ratios, e.g. 0.9,0.8")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(input_path)
    total = len(rows)

    ratios = []
    for x in args.ratios.split(","):
        x = x.strip()
        if not x:
            continue
        r = float(x)
        if not (0.0 < r < 1.0):
            raise ValueError(f"Invalid ratio: {x}")
        ratios.append(r)

    all_reports = {
        "input": str(input_path),
        "total": total,
        "seed": args.seed,
        "splits": [],
    }

    for ratio in ratios:
        train, val, per_source = split_stratified(rows, ratio, args.seed)
        train_n = len(train)
        val_n = len(val)

        ratio_name = f"{int(round(ratio * 10))}to{int(round((1 - ratio) * 10))}"
        train_path = out_dir / f"digestive_total_{total}_train_{train_n}_{ratio_name}.json"
        val_path = out_dir / f"digestive_total_{total}_val_{val_n}_{ratio_name}.json"
        report_path = out_dir / f"digestive_total_{total}_split_{ratio_name}_report.json"

        train_path.write_text(json.dumps(train, ensure_ascii=False, indent=2), encoding="utf-8")
        val_path.write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding="utf-8")

        report = {
            "input": str(input_path),
            "seed": args.seed,
            "train_ratio": ratio,
            "val_ratio": 1 - ratio,
            "counts": {
                "total": total,
                "train": train_n,
                "val": val_n,
            },
            "per_source": per_source,
            "output": {
                "train": str(train_path),
                "val": str(val_path),
            },
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        all_reports["splits"].append(
            {
                "ratio_name": ratio_name,
                "train_ratio": ratio,
                "counts": report["counts"],
                "train": str(train_path),
                "val": str(val_path),
                "report": str(report_path),
            }
        )

    summary_path = out_dir / f"digestive_total_{total}_split_summary.json"
    summary_path.write_text(json.dumps(all_reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(all_reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
