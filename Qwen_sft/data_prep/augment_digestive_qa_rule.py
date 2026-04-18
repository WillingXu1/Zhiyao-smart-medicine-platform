#!/usr/bin/env python3
import argparse
import copy
import json
import random
import re
from pathlib import Path
from typing import Dict, List


SYSTEM_PROMPT = "你是一位严格遵循中国消化内科临床指南的医生。"

ASK_SYNONYMS = {
    "怎么": ["如何", "怎样"],
    "怎么办": ["如何处理", "该怎么处理"],
    "吃什么药": ["用什么药", "该用哪些药"],
    "用药": ["药物治疗", "药物方案"],
    "需要": ["是否需要", "要不要"],
    "可以": ["能否", "可不可以"],
    "腹痛": ["肚子痛", "腹部疼痛"],
    "腹胀": ["肚子胀", "腹部胀满"],
    "腹泻": ["拉肚子", "大便次数增多"],
    "便秘": ["排便困难", "大便干结"],
    "反酸": ["胃酸反流", "酸水上涌"],
    "恶心": ["反胃", "恶心想吐"],
    "呕吐": ["吐", "吐出胃内容物"],
    "幽门螺杆菌": ["HP", "幽门杆菌"],
}

PREFIXES = [
    "请问",
    "想咨询一下",
    "麻烦问下",
    "医生您好，",
    "请教一下，",
]


def load_json(path: Path) -> List[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Input json must be a list")
    return data


def dump_json(path: Path, data: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_for_dedup(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip().lower())


def ensure_messages(title: str, ask: str, answer: str, messages) -> List[dict]:
    if isinstance(messages, list) and len(messages) >= 2 and all(isinstance(m, dict) for m in messages):
        return messages
    user_text = f"标题：{title}\n问题：{ask}" if title else ask
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": answer},
    ]


def rewrite_ask(ask: str, rng: random.Random) -> str:
    text = ask.strip()
    changed = False

    for src, cands in ASK_SYNONYMS.items():
        if src in text and rng.random() < 0.7:
            text = text.replace(src, rng.choice(cands), 1)
            changed = True

    if text and not any(text.startswith(p) for p in PREFIXES) and rng.random() < 0.4:
        text = rng.choice(PREFIXES) + text
        changed = True

    if "，" in text and rng.random() < 0.3:
        text = text.replace("，", "；", 1)
        changed = True

    if not changed:
        text = "请问" + text

    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Rule-based augmentation for digestive QA dataset")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--n-aug-per-sample", type=int, default=1)
    parser.add_argument("--max-samples", type=int, default=0, help="0 means all")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    records = load_json(Path(args.input))

    stats: Dict[str, int] = {
        "input_records": len(records),
        "selected_source_records": 0,
        "augmented_records": 0,
        "skipped_empty_qa": 0,
        "skipped_duplicate": 0,
    }

    base = []
    seen_q = set()
    for i, item in enumerate(records, start=1):
        if not isinstance(item, dict):
            continue
        ask = str(item.get("ask") or item.get("input") or item.get("instruction") or "").strip()
        answer = str(item.get("answer") or item.get("output") or item.get("response") or "").strip()
        title = str(item.get("title") or "").strip()
        if not ask or not answer:
            stats["skipped_empty_qa"] += 1
            continue

        rec = {
            "id": item.get("id", i),
            "title": title or ask[:80],
            "ask": ask,
            "answer": answer,
            "description": str(item.get("description") or ""),
            "source": str(item.get("source") or "digestive_total"),
            "messages": ensure_messages(title, ask, answer, item.get("messages")),
        }
        base.append(rec)
        seen_q.add(normalize_for_dedup(ask))

    candidates = list(base)
    if args.max_samples > 0 and len(candidates) > args.max_samples:
        rng.shuffle(candidates)
        candidates = candidates[: args.max_samples]
    stats["selected_source_records"] = len(candidates)

    out = list(base)
    for rec in candidates:
        for _ in range(args.n_aug_per_sample):
            new_ask = rewrite_ask(rec["ask"], rng)
            key = normalize_for_dedup(new_ask)
            if key in seen_q:
                stats["skipped_duplicate"] += 1
                continue

            new_rec = copy.deepcopy(rec)
            new_rec["id"] = f"aug_{len(out) + 1}"
            new_rec["ask"] = new_ask
            new_rec["source"] = str(rec.get("source", "digestive_total")) + "_rule_aug"

            if isinstance(new_rec.get("messages"), list) and len(new_rec["messages"]) >= 3:
                user_text = str(new_rec["messages"][1].get("content") or "")
                if "问题：" in user_text:
                    new_rec["messages"][1]["content"] = re.sub(r"问题：.*$", f"问题：{new_ask}", user_text, flags=re.S)
                else:
                    new_rec["messages"][1]["content"] = new_ask
                new_rec["messages"][2]["content"] = rec["answer"]
            else:
                new_rec["messages"] = ensure_messages(new_rec["title"], new_ask, rec["answer"], None)

            out.append(new_rec)
            seen_q.add(key)
            stats["augmented_records"] += 1

    stats["output_records"] = len(out)

    dump_json(Path(args.output), out)
    dump_json(Path(args.report), {
        "input": args.input,
        "output": args.output,
        "config": {
            "n_aug_per_sample": args.n_aug_per_sample,
            "max_samples": args.max_samples,
            "seed": args.seed,
        },
        "counts": stats,
    })

    print(json.dumps({"output": args.output, "report": args.report, "counts": stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
