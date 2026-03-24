#!/usr/bin/env python3
import argparse
import json
import os
import re


def normalize_text(text: str) -> str:
    # Remove OCR watermarks and page markers that are unrelated to case content.
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            lines.append("")
            continue
        if re.match(r"^===\s*Page\s*\d+\s*===", s):
            continue
        if s in {"中国医考网", "www.chinayikao.com"}:
            continue
        lines.append(s)
    return "\n".join(lines)


def compact(s: str) -> str:
    s = re.sub(r"\s+", "", s)
    return s.strip("，,;；。 ")


def extract_field(block: str, key: str, all_keys: list[str]) -> str:
    key_group = "|".join(re.escape(k) for k in all_keys)
    pattern = rf"{re.escape(key)}[：:]\s*(.*?)(?=(?:\n(?:{key_group})[：:])|$)"
    m = re.search(pattern, block, flags=re.S)
    if not m:
        return ""
    return compact(m.group(1))


def normalize_headings(text: str, all_keys: list[str]) -> str:
    normalized = text
    for key in all_keys:
        # Normalize headings like "【临床表现】" to "临床表现："
        normalized = re.sub(rf"^[【\[]\s*{re.escape(key)}\s*[】\]]\s*$", f"{key}：", normalized, flags=re.M)
        # Normalize standalone headings like "临床表现。" or "临床表现"
        normalized = re.sub(rf"^{re.escape(key)}[。\s]*$", f"{key}：", normalized, flags=re.M)
    return normalized


def extract_qa_pairs(text: str, q_keys: list[str], a_keys: list[str]) -> list[dict]:
    cleaned = normalize_text(text)
    start_key = q_keys[0]
    all_keys = q_keys + a_keys
    cleaned = normalize_headings(cleaned, all_keys)
    blocks = re.split(rf"(?={re.escape(start_key)}[：:])", cleaned)

    qa_pairs = []
    for block in blocks:
        if not block.strip().startswith(start_key):
            continue

        q_values = [extract_field(block, k, all_keys) for k in q_keys]
        a_values = [extract_field(block, k, all_keys) for k in a_keys]

        # Require all Q fields to avoid malformed samples.
        if any(not v for v in q_values):
            continue

        q = "；".join(f"{k}：{v}" for k, v in zip(q_keys, q_values))
        a = "；".join(f"{k}：{(v if v else '未提取到')}" for k, v in zip(a_keys, a_values))

        qa_pairs.append({"Q": q, "A": a})

    return qa_pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract QA JSON from OCR TXT")
    parser.add_argument("--input", required=True, help="Input OCR txt path")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--output-name", default="data_qa.json.txt", help="Output txt filename")
    parser.add_argument("--q-keys", nargs="+", required=True, help="Ordered keys used to build Q")
    parser.add_argument("--a-keys", nargs="+", required=True, help="Ordered keys used to build A")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    qa_pairs = extract_qa_pairs(text, args.q_keys, args.a_keys)
    output = {"qa_pairs": qa_pairs}

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, args.output_name)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)

    print(out_path)
    print(f"qa_count={len(qa_pairs)}")


if __name__ == "__main__":
    main()