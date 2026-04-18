#!/usr/bin/env python3
import argparse
import json
import random
import re
from pathlib import Path
from typing import Dict, List


SYSTEM_PROMPT_FALLBACK = "你是一位严格遵循中国消化内科临床指南的医生。"


def _remove_ctrl_chars(s: str) -> str:
    # Keep common whitespace controls; replace other control chars.
    return "".join(ch if (ch in "\n\r\t" or ord(ch) >= 32) else " " for ch in s)


def _fix_broken_json_lines(raw: str) -> str:
    fixed = []
    for line in raw.splitlines(True):
        if '"Q": "' in line or '"A": "' in line:
            esc = False
            quote_count = 0
            for ch in line:
                if ch == "\\" and not esc:
                    esc = True
                    continue
                if ch == '"' and not esc:
                    quote_count += 1
                esc = False
            # Key line should usually have even quote count; odd means broken string.
            if quote_count % 2 == 1:
                nl = "\n" if line.endswith("\n") else ""
                core = line[:-1] if nl else line
                line = core + '"' + nl
        fixed.append(line)
    return "".join(fixed)


def load_qa_pairs(path: Path) -> List[Dict[str, str]]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = _remove_ctrl_chars(raw)
    try:
        obj = json.loads(raw)
    except Exception:
        raw2 = _fix_broken_json_lines(raw)
        obj = json.loads(raw2)

    pairs = obj.get("qa_pairs", []) if isinstance(obj, dict) else []
    out = []
    for x in pairs:
        q = str(x.get("Q", "")).strip()
        a = str(x.get("A", "")).strip()
        if q and a:
            out.append({"Q": q, "A": a})
    return out


def load_system_prompt(default_prompt: str, existing_dataset: Path) -> str:
    if not existing_dataset.exists():
        return default_prompt
    try:
        data = json.loads(existing_dataset.read_text(encoding="utf-8"))
        if data and "messages" in data[0] and data[0]["messages"]:
            return data[0]["messages"][0].get("content", default_prompt)
    except Exception:
        return default_prompt
    return default_prompt


def to_conversations(qa_pairs: List[Dict[str, str]], system_prompt: str) -> List[dict]:
    out = []
    for it in qa_pairs:
        out.append(
            {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": it["Q"]},
                    {"role": "assistant", "content": it["A"]},
                ]
            }
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build run9.1 datasets from latest QA txt files")
    parser.add_argument("--main-qa", required=True)
    parser.add_argument("--external-qa", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--json-dir", required=True)
    parser.add_argument("--existing-dataset", default="")
    parser.add_argument("--append-system-instruction", default="")
    args = parser.parse_args()

    main_pairs = load_qa_pairs(Path(args.main_qa))
    ext_pairs = load_qa_pairs(Path(args.external_qa))

    existing = Path(args.existing_dataset) if args.existing_dataset else Path(args.json_dir) / "dataset.json"
    sys_prompt = load_system_prompt(SYSTEM_PROMPT_FALLBACK, existing)
    if args.append_system_instruction.strip():
        sys_prompt = sys_prompt.rstrip() + "\n" + args.append_system_instruction.strip()

    main_conv = to_conversations(main_pairs, sys_prompt)
    ext_conv = to_conversations(ext_pairs, sys_prompt)

    rng = random.Random(args.seed)
    n = len(main_conv)
    val_n = max(1, int(round(n * args.val_ratio))) if n > 0 else 0
    val_n = min(val_n, n)
    idx = list(range(n))
    rng.shuffle(idx)
    val_idx = set(idx[:val_n])

    train = [x for i, x in enumerate(main_conv) if i not in val_idx]
    val = [x for i, x in enumerate(main_conv) if i in val_idx]

    json_dir = Path(args.json_dir)
    json_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "main_conv": json_dir / "dataset_data_v2_latest_run9_1.json",
        "external_conv": json_dir / "dataset_external_v2_latest_run9_1.json",
        "train": json_dir / "dataset_train_80_run9_1.json",
        "internal": json_dir / "dataset_internal_20_run9_1.json",
    }
    files["main_conv"].write_text(json.dumps(main_conv, ensure_ascii=False, indent=2), encoding="utf-8")
    files["external_conv"].write_text(json.dumps(ext_conv, ensure_ascii=False, indent=2), encoding="utf-8")
    files["train"].write_text(json.dumps(train, ensure_ascii=False, indent=2), encoding="utf-8")
    files["internal"].write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = {
        "seed": args.seed,
        "val_ratio": args.val_ratio,
        "counts": {
            "main_pairs": len(main_pairs),
            "external_pairs": len(ext_pairs),
            "train": len(train),
            "internal": len(val),
        },
        "files": {k: str(v) for k, v in files.items()},
    }
    (json_dir / "dataset_run9_1_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
