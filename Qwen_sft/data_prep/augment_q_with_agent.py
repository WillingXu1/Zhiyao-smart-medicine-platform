#!/usr/bin/env python3
import argparse
import copy
import json
import os
import random
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple


SYMPTOM_SYNONYMS = {
    "反酸": ["酸水上涌", "胃酸反流"],
    "胃灼热": ["烧心", "胸骨后烧灼感"],
    "胸骨后烧灼感": ["胸后区烧心感", "胸骨后灼热感"],
    "上腹部隐痛": ["上腹隐痛", "上腹部不适疼痛"],
    "腹胀": ["腹部胀满", "腹部发胀"],
    "嗳气": ["打嗝", "反复嗳气"],
    "恶心": ["反胃", "恶心欲吐"],
    "呕吐": ["吐出胃内容物", "频繁呕吐"],
    "吞咽疼痛": ["吞咽时疼痛", "咽下疼痛"],
    "吞咽困难": ["咽下困难", "进食下咽不畅"],
}


def load_dataset(path: Path) -> List[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_dataset(path: Path, data: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def split_user_query(q: str) -> Tuple[str, str]:
    m = re.match(r"^\s*索引词[：:](.*?)；病史摘要[：:](.*)\s*$", q, flags=re.S)
    if not m:
        return "", ""
    return m.group(1).strip(), m.group(2).strip()


def rule_rewrite_history(history: str, rng: random.Random) -> str:
    text = history
    changed = False
    for src, candidates in SYMPTOM_SYNONYMS.items():
        if src in text and rng.random() < 0.8:
            text = text.replace(src, rng.choice(candidates), 1)
            changed = True
    if "，" in text and rng.random() < 0.5:
        text = text.replace("，", "；", 1)
        changed = True
    if not changed:
        text = "患者主诉：" + text
    return text


def call_openai_compatible(base_url: str, model: str, api_key: str, history: str, timeout: int) -> str:
    prompt = (
        "请改写下面病史摘要，只允许做同义词替换和语序微调，保持医学事实完全一致。"
        "不要新增或删除事实，不要编造检查结果，不要改年龄性别。"
        "仅输出改写后的病史摘要正文，不要输出解释。\n\n"
        f"病史摘要：{history}"
    )
    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 512,
        "messages": [
            {"role": "system", "content": "你是医疗文本改写助手，严格保真改写。"},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
    return payload["choices"][0]["message"]["content"].strip()


def normalize_for_compare(s: str) -> str:
    return re.sub(r"\s+", "", s)


def build_augmented(
    records: List[dict],
    mode: str,
    n_aug_per_sample: int,
    max_samples: int,
    seed: int,
    llm_base_url: str,
    llm_model: str,
    llm_api_key: str,
    timeout: int,
) -> Tuple[List[dict], Dict[str, int]]:
    rng = random.Random(seed)
    out = list(records)
    stats = {
        "source_count": len(records),
        "selected_source_count": 0,
        "augmented_count": 0,
        "skipped_format": 0,
        "skipped_duplicate": 0,
        "failed_llm_calls": 0,
        "assistant_unchanged_checks": 0,
    }

    seen_q = set()
    for r in records:
        msgs = r.get("messages", [])
        if len(msgs) < 3:
            stats["skipped_format"] += 1
            continue
        seen_q.add(normalize_for_compare(str(msgs[1].get("content", ""))))

    candidates = [r for r in records if len(r.get("messages", [])) >= 3]
    if max_samples > 0 and len(candidates) > max_samples:
        rng.shuffle(candidates)
        candidates = candidates[:max_samples]
    stats["selected_source_count"] = len(candidates)

    for rec in candidates:
        msgs = rec.get("messages", [])
        user_q = str(msgs[1].get("content", ""))
        ans = str(msgs[2].get("content", ""))
        index_part, history_part = split_user_query(user_q)
        if not index_part or not history_part:
            stats["skipped_format"] += 1
            continue

        for _ in range(n_aug_per_sample):
            if mode == "rule":
                new_history = rule_rewrite_history(history_part, rng)
            else:
                try:
                    new_history = call_openai_compatible(
                        llm_base_url, llm_model, llm_api_key, history_part, timeout
                    )
                except Exception:
                    stats["failed_llm_calls"] += 1
                    continue

            new_q = f"索引词：{index_part}；病史摘要：{new_history.strip()}"
            key = normalize_for_compare(new_q)
            if key in seen_q:
                stats["skipped_duplicate"] += 1
                continue

            new_rec = copy.deepcopy(rec)
            new_rec["messages"][1]["content"] = new_q
            if new_rec["messages"][2]["content"] != ans:
                raise RuntimeError("Assistant content changed unexpectedly.")

            stats["assistant_unchanged_checks"] += 1
            out.append(new_rec)
            seen_q.add(key)
            stats["augmented_count"] += 1

    return out, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Augment Q only while keeping A unchanged.")
    parser.add_argument("--input", required=True, help="Input conversation json")
    parser.add_argument("--output", required=True, help="Output augmented json")
    parser.add_argument("--mode", choices=["rule", "llm"], default="rule")
    parser.add_argument("--n-aug-per-sample", type=int, default=1)
    parser.add_argument("--max-samples", type=int, default=0, help="0 means use all samples")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--llm-base-url", default="http://127.0.0.1:8002")
    parser.add_argument("--llm-model", default="qwen2.5-1.5b-medical-sft")
    parser.add_argument("--llm-api-key", default="")
    parser.add_argument("--llm-api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--report", default="", help="Optional stats json path")
    args = parser.parse_args()

    records = load_dataset(Path(args.input))
    api_key = args.llm_api_key or os.getenv(args.llm_api_key_env, "")
    augmented, stats = build_augmented(
        records=records,
        mode=args.mode,
        n_aug_per_sample=args.n_aug_per_sample,
        max_samples=args.max_samples,
        seed=args.seed,
        llm_base_url=args.llm_base_url,
        llm_model=args.llm_model,
        llm_api_key=api_key,
        timeout=args.timeout,
    )

    dump_dataset(Path(args.output), augmented)
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
