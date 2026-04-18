#!/usr/bin/env python3
import argparse
import json
import random
import re
from pathlib import Path
from typing import List, Tuple


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def key_of_record(rec: dict) -> str:
    msgs = rec.get("messages", [])
    if len(msgs) < 3:
        return ""
    sys = norm(str(msgs[0].get("content", "")))
    q = norm(str(msgs[1].get("content", "")))
    a = norm(str(msgs[2].get("content", "")))
    return f"{sys}|{q}|{a}"


def q_len(rec: dict) -> int:
    msgs = rec.get("messages", [])
    if len(msgs) < 2:
        return 0
    return len(str(msgs[1].get("content", "")).strip())


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


def filter_by_q_len(records: List[dict], max_len: int) -> Tuple[List[dict], int]:
    kept = []
    dropped = 0
    for r in records:
        if q_len(r) <= max_len:
            kept.append(r)
        else:
            dropped += 1
    return kept, dropped


def allocate(target_total: int, rule_ratio: float, ds_ratio: float, caps: Tuple[int, int]) -> Tuple[int, int]:
    rule_t = int(round(target_total * rule_ratio))
    ds_t = target_total - rule_t
    rule_c, ds_c = caps

    got_rule = min(rule_t, rule_c)
    got_ds = min(ds_t, ds_c)

    missing = target_total - (got_rule + got_ds)
    if missing > 0:
        room_rule = rule_c - got_rule
        add = min(missing, max(0, room_rule))
        got_rule += add
        missing -= add

    if missing > 0:
        room_ds = ds_c - got_ds
        add = min(missing, max(0, room_ds))
        got_ds += add

    return got_rule, got_ds


def main() -> None:
    parser = argparse.ArgumentParser(description="Build run9.1 mixed dataset with rule/deepseek ratio + q length filter")
    parser.add_argument("--base", required=True)
    parser.add_argument("--rule", required=True)
    parser.add_argument("--deepseek", required=True)
    parser.add_argument("--aug-total", type=int, default=0, help="0 means use base size")
    parser.add_argument("--rule-ratio", type=float, default=0.7)
    parser.add_argument("--deepseek-ratio", type=float, default=0.3)
    parser.add_argument("--q-len-ratio", type=float, default=1.2)
    parser.add_argument("--disable-q-len-filter", action="store_true", help="Disable question length filtering")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    if args.rule_ratio <= 0 or args.deepseek_ratio <= 0 or abs((args.rule_ratio + args.deepseek_ratio) - 1.0) > 1e-6:
        raise ValueError("rule_ratio + deepseek_ratio must be 1.0 and both > 0")

    rng = random.Random(args.seed)

    base = load_json(Path(args.base))
    rule_all = load_json(Path(args.rule))
    ds_all = load_json(Path(args.deepseek))

    base_q_lens = sorted([q_len(r) for r in base if q_len(r) > 0])
    median_q = base_q_lens[len(base_q_lens) // 2] if base_q_lens else 0
    max_q = int(round(median_q * args.q_len_ratio)) if median_q else 999999

    rule_aug_raw = diff_aug_records(base, rule_all)
    ds_aug_raw = diff_aug_records(base, ds_all)

    if args.disable_q_len_filter:
        rule_aug, dropped_rule = list(rule_aug_raw), 0
        ds_aug, dropped_ds = list(ds_aug_raw), 0
    else:
        rule_aug, dropped_rule = filter_by_q_len(rule_aug_raw, max_q)
        ds_aug, dropped_ds = filter_by_q_len(ds_aug_raw, max_q)

    aug_total = args.aug_total if args.aug_total > 0 else len(base)
    n_rule, n_ds = allocate(
        target_total=aug_total,
        rule_ratio=args.rule_ratio,
        ds_ratio=args.deepseek_ratio,
        caps=(len(rule_aug), len(ds_aug)),
    )

    chosen_rule = pick(rule_aug, n_rule, rng)
    chosen_ds = pick(ds_aug, n_ds, rng)

    final_data = list(base) + chosen_rule + chosen_ds

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(final_data, ensure_ascii=False, indent=2), encoding="utf-8")

    selected_aug = len(chosen_rule) + len(chosen_ds)
    report = {
        "base_count": len(base),
        "target_aug_total": aug_total,
        "q_len_filter": {
            "enabled": not args.disable_q_len_filter,
            "median_base_q_len": median_q,
            "max_q_len": max_q,
            "q_len_ratio": args.q_len_ratio,
        },
        "available_before_filter": {
            "rule_aug": len(rule_aug_raw),
            "deepseek_aug": len(ds_aug_raw),
        },
        "dropped_by_q_len": {
            "rule_aug": dropped_rule,
            "deepseek_aug": dropped_ds,
        },
        "available_after_filter": {
            "rule_aug": len(rule_aug),
            "deepseek_aug": len(ds_aug),
        },
        "selected": {
            "rule_aug": len(chosen_rule),
            "deepseek_aug": len(chosen_ds),
        },
        "selected_ratio": {
            "rule_aug": round(len(chosen_rule) / max(1, selected_aug), 4),
            "deepseek_aug": round(len(chosen_ds) / max(1, selected_aug), 4),
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
