#!/usr/bin/env python3
import argparse
import json
import random
import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Tuple


def normalize_text(s: str) -> str:
    s = (s or "").replace("\r", "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def split_sections(text: str) -> Dict[str, str]:
    t = normalize_text(text)
    out = {"diagnosis": "", "prescription": "", "usage": ""}
    if not t:
        return out

    pats = {
        "diagnosis": r"(诊断[：:])",
        "prescription": r"(处方[：:])",
        "usage": r"(用法[：:])",
    }
    locs: List[Tuple[str, int]] = []
    for k, p in pats.items():
        m = re.search(p, t)
        if m:
            locs.append((k, m.start()))

    if not locs:
        # Fallback: treat first sentence as diagnosis-like text.
        first = re.split(r"[。；;\n]", t)[0].strip()
        out["diagnosis"] = first or t[:48]
        return out

    locs.sort(key=lambda x: x[1])
    for i, (k, st) in enumerate(locs):
        ed = locs[i + 1][1] if i + 1 < len(locs) else len(t)
        chunk = normalize_text(t[st:ed])
        chunk = re.sub(r"^(诊断|处方|用法)[：:]\s*", "", chunk)
        out[k] = chunk
    return out


DRUG_RX = re.compile(
    r"([A-Za-z\u4e00-\u9fff\-·]{2,24}(?:片|胶囊|颗粒|注射液|注射用|口服液|丸|散|制剂)?)\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s*(mg|g|ml|ug|μg)",
    re.IGNORECASE,
)
FREQ_RX = [
    re.compile(r"每日\s*([0-9]+)\s*次"),
    re.compile(r"每天\s*([0-9]+)\s*次"),
    re.compile(r"一日\s*([0-9一二两三四五六七八九十]+)\s*次"),
    re.compile(r"(qd|bid|tid|qid)", re.IGNORECASE),
]


def parse_freq(text: str) -> str:
    t = normalize_text(text).lower()
    for rx in FREQ_RX:
        m = rx.search(t)
        if not m:
            continue
        return normalize_text(m.group(0))
    return "每日1次"


def build_structured_chosen(answer: str) -> str:
    ans = normalize_text(answer)
    sec = split_sections(ans)

    diagnosis = sec["diagnosis"]
    if not diagnosis:
        diagnosis = re.split(r"[。；;\n]", ans)[0].strip() or "需结合病史进一步评估"

    meds = []
    for m in DRUG_RX.finditer(ans):
        meds.append(f"{m.group(1)}{m.group(2)}{m.group(3)}")
    meds = meds[:3]

    if sec["prescription"]:
        prescription = sec["prescription"]
    elif meds:
        prescription = "；".join(meds)
    else:
        prescription = "根据病情给予抑酸及胃黏膜保护方案"

    if sec["usage"]:
        usage = sec["usage"]
    else:
        usage = parse_freq(ans)

    return f"诊断：{normalize_text(diagnosis)}\n处方：{normalize_text(prescription)}\n用法：{normalize_text(usage)}"


def build_rejected(answer: str, chosen: str) -> str:
    raw = normalize_text(answer)
    c = normalize_text(chosen)

    # Prefer raw long-form style as rejected when it differs from strict structured chosen.
    if raw and raw != c and len(raw) >= 20:
        return raw

    # Fallback: intentionally remove structure and key medication clarity.
    flat = c.replace("诊断：", "").replace("处方：", "").replace("用法：", "")
    flat = re.sub(r"\s+", " ", flat)
    return f"建议结合临床情况综合处理，先观察并调整生活方式。{flat[:120]}"


def parse_messages_item(item: dict, source: str) -> dict:
    msgs = item.get("messages", []) if isinstance(item, dict) else []
    system = ""
    user = ""
    assistant = ""
    for m in msgs:
        role = m.get("role", "")
        if role == "system" and not system:
            system = normalize_text(str(m.get("content", "")))
        elif role == "user" and not user:
            user = normalize_text(str(m.get("content", "")))
        elif role == "assistant" and not assistant:
            assistant = normalize_text(str(m.get("content", "")))

    if not user or not assistant:
        return {}

    prompt = f"系统：{system}\n用户：{user}" if system else f"用户：{user}"
    chosen = build_structured_chosen(assistant)
    rejected = build_rejected(assistant, chosen)
    if not rejected or rejected == chosen:
        return {}

    return {
        "prompt": prompt,
        "chosen": chosen,
        "rejected": rejected,
        "meta": {
            "source": source,
            "raw_answer_len": len(assistant),
            "chosen_len": len(chosen),
            "rejected_len": len(rejected),
        },
    }


def parse_task(task: Tuple[dict, str]) -> dict:
    return parse_messages_item(task[0], task[1])


def load_json_list(path: Path) -> List[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected list json: {path}")
    return data


def write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def split_rows(
    rows: List[dict],
    seed: int,
    val_ratio: float,
    test_ratio_main: float,
    holdout_external_all: bool,
) -> Tuple[List[dict], List[dict], List[dict]]:
    rng = random.Random(seed)

    ext = [r for r in rows if r.get("meta", {}).get("source") == "external_24"]
    main = [r for r in rows if r.get("meta", {}).get("source") != "external_24"]

    rng.shuffle(main)
    rng.shuffle(ext)

    test = []
    if holdout_external_all:
        test.extend(ext)
        ext = []
    else:
        n_ext_test = max(1, int(round(len(ext) * 0.5))) if len(ext) > 1 else len(ext)
        test.extend(ext[:n_ext_test])
        ext = ext[n_ext_test:]

    n_main_test = max(1, int(round(len(main) * test_ratio_main))) if len(main) > 1 and test_ratio_main > 0 else 0
    test.extend(main[:n_main_test])
    remain = main[n_main_test:] + ext
    rng.shuffle(remain)

    n_val = max(1, int(round(len(remain) * val_ratio))) if len(remain) > 1 and val_ratio > 0 else 0
    val = remain[:n_val]
    train = remain[n_val:]
    return train, val, test


def main() -> None:
    ap = argparse.ArgumentParser(description="Build structured DPO dataset from run9_2 + external24 with holdout split")
    ap.add_argument("--main-json", required=True)
    ap.add_argument("--external-json", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--prefix", default="qwen7b_struct_align_dpo")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val-ratio", type=float, default=0.1)
    ap.add_argument("--test-ratio-main", type=float, default=0.12)
    ap.add_argument("--holdout-external-all", action="store_true", dest="holdout_external_all")
    ap.add_argument("--no-holdout-external-all", action="store_false", dest="holdout_external_all")
    ap.set_defaults(holdout_external_all=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    main_items = load_json_list(Path(args.main_json))
    ext_items = load_json_list(Path(args.external_json))

    tasks: List[Tuple[dict, str]] = []
    tasks.extend((x, "train455") for x in main_items)
    tasks.extend((x, "external_24") for x in ext_items)

    rows: List[dict] = []
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as ex:
        for rec in ex.map(parse_task, tasks, chunksize=32):
            if rec:
                rows.append(rec)

    # Deduplicate by prompt to reduce leakage.
    uniq = {}
    for r in rows:
        k = normalize_text(r["prompt"])
        if k and k not in uniq:
            uniq[k] = r
    rows = list(uniq.values())

    train, val, test = split_rows(
        rows,
        seed=args.seed,
        val_ratio=args.val_ratio,
        test_ratio_main=args.test_ratio_main,
        holdout_external_all=args.holdout_external_all,
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    train_p = out_dir / f"{args.prefix}_train.jsonl"
    val_p = out_dir / f"{args.prefix}_val.jsonl"
    test_p = out_dir / f"{args.prefix}_test.jsonl"
    all_p = out_dir / f"{args.prefix}_all.jsonl"
    meta_p = out_dir / f"{args.prefix}_meta.json"

    write_jsonl(train_p, train)
    write_jsonl(val_p, val)
    write_jsonl(test_p, test)
    write_jsonl(all_p, rows)

    def source_count(xs: List[dict]) -> Dict[str, int]:
        return dict(Counter(r.get("meta", {}).get("source", "unknown") for r in xs))

    meta = {
        "input": {
            "main_json": args.main_json,
            "external_json": args.external_json,
            "main_count": len(main_items),
            "external_count": len(ext_items),
        },
        "output": {
            "all": str(all_p),
            "train": str(train_p),
            "val": str(val_p),
            "test": str(test_p),
        },
        "counts": {
            "all": len(rows),
            "train": len(train),
            "val": len(val),
            "test": len(test),
        },
        "source_distribution": {
            "all": source_count(rows),
            "train": source_count(train),
            "val": source_count(val),
            "test": source_count(test),
        },
        "config": {
            "seed": args.seed,
            "val_ratio": args.val_ratio,
            "test_ratio_main": args.test_ratio_main,
            "holdout_external_all": args.holdout_external_all,
            "workers": args.workers,
        },
    }
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
