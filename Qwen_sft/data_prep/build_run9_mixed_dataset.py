#!/usr/bin/env python3
import argparse
import json
import random
import re
from pathlib import Path
from typing import Dict, List, Tuple


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def key_of_record(rec: dict) -> str:
    msgs = rec.get("messages", [])
    if len(msgs) < 3:
        return ""
    sys = re.sub(r"\s+", "", str(msgs[0].get("content", "")))
    q = re.sub(r"\s+", "", str(msgs[1].get("content", "")))
    a = re.sub(r"\s+", "", str(msgs[2].get("content", "")))
    return f"{sys}|{q}|{a}"


def diff_aug_records(base: List[dict], mixed: List[dict]) -> List[dict]:
    base_keys = {key_of_record(r) for r in base}
    out = []
    for r in mixed:
        k = key_of_record(r)
        if k and k not in base_keys:
            out.append(r)
    return out


def pick(records: List[dict], n: int, rng: random.Random) -> List[dict]:
    if n <= 0 or not records:
        return []
    if len(records) <= n:
        return list(records)
    return rng.sample(records, n)


def allocate(target_total: int, ratios: Tuple[float, float, float],
             caps: Tuple[int, int, int]) -> Tuple[int, int, int]:
    r_rule, r_ds, r_run8 = ratios
    rule_t = int(round(target_total * r_rule))
    ds_t = int(round(target_total * r_ds))
    run8_t = target_total - rule_t - ds_t

    rule_c, ds_c, run8_c = caps
    got_rule = min(rule_t, rule_c)
    got_ds = min(ds_t, ds_c)
    got_run8 = min(run8_t, run8_c)

    missing = target_total - (got_rule + got_ds + got_run8)
    if missing <= 0:
        return got_rule, got_ds, got_run8

    # Backfill in priority order: deepseek -> run8 -> rule (to keep diversity intent first).
    room_ds = ds_c - got_ds
    add = min(missing, max(0, room_ds))
    got_ds += add
    missing -= add

    room_run8 = run8_c - got_run8
    add = min(missing, max(0, room_run8))
    got_run8 += add
    missing -= add

    room_rule = rule_c - got_rule
    add = min(missing, max(0, room_rule))
    got_rule += add
    missing -= add

    return got_rule, got_ds, got_run8


def main() -> None:
    parser = argparse.ArgumentParser(description="Build run9 mixed dataset with 50/40/10 augmentation ratio")
    parser.add_argument("--base", required=True)
    parser.add_argument("--rule", required=True)
    parser.add_argument("--deepseek", required=True)
    parser.add_argument("--run8", required=True)
    parser.add_argument("--aug-total", type=int, default=0, help="0 means use base size")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    base = load_json(Path(args.base))
    rule_all = load_json(Path(args.rule))
    ds_all = load_json(Path(args.deepseek))
    run8_all = load_json(Path(args.run8))

    rule_aug = diff_aug_records(base, rule_all)
    ds_aug = diff_aug_records(base, ds_all)
    run8_aug = diff_aug_records(base, run8_all)

    aug_total = args.aug_total if args.aug_total > 0 else len(base)
    n_rule, n_ds, n_run8 = allocate(
        target_total=aug_total,
        ratios=(0.5, 0.4, 0.1),
        caps=(len(rule_aug), len(ds_aug), len(run8_aug)),
    )

    chosen_rule = pick(rule_aug, n_rule, rng)
    chosen_ds = pick(ds_aug, n_ds, rng)
    chosen_run8 = pick(run8_aug, n_run8, rng)

    final_data = list(base) + chosen_rule + chosen_ds + chosen_run8

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(final_data, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "base_count": len(base),
        "target_aug_total": aug_total,
        "available": {
            "rule_aug": len(rule_aug),
            "deepseek_aug": len(ds_aug),
            "run8_aug": len(run8_aug),
        },
        "selected": {
            "rule_aug": len(chosen_rule),
            "deepseek_aug": len(chosen_ds),
            "run8_aug": len(chosen_run8),
        },
        "selected_ratio": {
            "rule_aug": round(len(chosen_rule) / max(1, (len(chosen_rule)+len(chosen_ds)+len(chosen_run8))), 4),
            "deepseek_aug": round(len(chosen_ds) / max(1, (len(chosen_rule)+len(chosen_ds)+len(chosen_run8))), 4),
            "run8_aug": round(len(chosen_run8) / max(1, (len(chosen_rule)+len(chosen_ds)+len(chosen_run8))), 4),
        },
        "final_train_count": len(final_data),
    }

    rep_path = Path(args.report)
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    rep_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
