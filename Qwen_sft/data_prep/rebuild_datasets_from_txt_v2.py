#!/usr/bin/env python3
import argparse
import json
import os
import random
import re
from dataclasses import dataclass
from typing import List, Optional


SYSTEM_PROMPT_FALLBACK = "你是一位严格遵循中国消化内科临床指南的医生..."


@dataclass
class MedPair:
    prescription: str
    usage: str


def compact_text(s: str) -> str:
    s = s.replace("\u3000", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip(" \n；;，,。")


def normalize_common(text: str) -> str:
    out = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            out.append("")
            continue
        if re.match(r"^===\s*Page\s*\d+\s*===$", s):
            continue
        if s in {"中国医考网", "www.chinayikao.com"}:
            continue
        out.append(s)
    return "\n".join(out)


def normalize_bracket_headings(text: str, keys: List[str]) -> str:
    fixed = text
    for key in keys:
        fixed = re.sub(
            rf"^\s*[【\[]\s*{re.escape(key)}\s*[】\]]\s*$",
            f"{key}：",
            fixed,
            flags=re.M,
        )
        fixed = re.sub(
            rf"^\s*{re.escape(key)}\s*$",
            f"{key}：",
            fixed,
            flags=re.M,
        )
    return fixed


def extract_field(case_text: str, key: str, next_keys: List[str]) -> str:
    keys_group = "|".join(re.escape(k) for k in next_keys)
    pattern = rf"(?m)^\s*{re.escape(key)}\s*[：:]\s*(.*?)(?=^\s*(?:{keys_group})\s*[：:]|\Z)"
    m = re.search(pattern, case_text, flags=re.S)
    return compact_text(m.group(1)) if m else ""


def looks_like_new_prescription_line(line: str) -> bool:
    if not re.match(r"^\s*\d+[\.、．]\s*", line):
        return False
    usage_tokens = ["每次", "每日", "口服", "餐前", "餐后", "睡前", "次/日", "次/天", "静滴", "静注"]
    if any(tok in line for tok in usage_tokens):
        return False
    drug_tokens = ["mg", "g", "ml", "片", "粒", "支", "袋", "胶囊", "注射", "口服液", "丸", "滴丸", "冲剂", "颗粒"]
    return any(tok in line for tok in drug_tokens)


def strip_list_prefix(s: str) -> str:
    return re.sub(r"^\s*\d+[\.、．]\s*", "", s).strip()


def looks_like_prescription_text(text: str) -> bool:
    drug_tokens = ["mg", "g", "ml", "片", "粒", "支", "袋", "胶囊", "注射", "口服液", "丸", "滴丸", "冲剂", "颗粒"]
    return any(tok in text for tok in drug_tokens)


def split_numbered_entries(content: str) -> List[str]:
    lines = [x.strip() for x in content.splitlines() if x.strip()]
    entries: List[str] = []
    cur: List[str] = []
    saw_numbered = False

    for line in lines:
        m = re.match(r"^\s*\d+[\.、．]\s*(.*)$", line)
        if m:
            saw_numbered = True
            if cur:
                entries.append(compact_text("\n".join(cur)))
            cur = [m.group(1).strip()]
        else:
            if cur:
                cur.append(line)
            else:
                cur = [line]

    if cur:
        entries.append(compact_text("\n".join(cur)))

    if saw_numbered:
        return [e for e in entries if e]

    merged = compact_text(content)
    return [merged] if merged else []


def split_usage_entries(content: str) -> List[str]:
    raw_entries = split_numbered_entries(content)
    out: List[str] = []
    for e in raw_entries:
        lines = [x.strip() for x in e.splitlines() if x.strip()]
        if not lines:
            continue
        if len(lines) > 1 and looks_like_prescription_text(lines[0]):
            tail = compact_text("\n".join(lines[1:]))
            out.append(tail if tail else compact_text(e))
        else:
            out.append(compact_text(e))
    return [x for x in out if x]


def split_heading_blocks(section: str) -> List[tuple[str, str]]:
    blocks: List[tuple[str, str]] = []
    matches = list(re.finditer(r"(?m)^\s*(处方|用法)\s*[：:]\s*", section))
    if not matches:
        return blocks

    for i, m in enumerate(matches):
        key = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
        blocks.append((key, section[start:end]))
    return blocks


def parse_med_pairs(med_section: str) -> List[MedPair]:
    blocks = split_heading_blocks(med_section)
    pairs: List[MedPair] = []
    pending_rx: List[str] = []

    for key, content in blocks:
        if key == "处方":
            pending_rx = split_numbered_entries(content)
            continue

        usages = split_usage_entries(content)

        if pending_rx:
            for i, rx in enumerate(pending_rx):
                if len(usages) == len(pending_rx):
                    use = usages[i]
                elif len(usages) == 1:
                    use = usages[0]
                elif i < len(usages):
                    use = usages[i]
                else:
                    use = ""
                pairs.append(MedPair(prescription=compact_text(rx), usage=compact_text(use)))
            pending_rx = []
            continue

        # Fallback: usage appears without visible prescription heading.
        for use in usages:
            pairs.append(MedPair(prescription="", usage=compact_text(use)))

    for rx in pending_rx:
        pairs.append(MedPair(prescription=compact_text(rx), usage=""))

    # Merge rare malformed sequences where a usage block starts with an implicit prescription line.
    merged: List[MedPair] = []
    for p in pairs:
        if merged and (not p.prescription) and looks_like_new_prescription_line(p.usage):
            merged.append(MedPair(prescription=strip_list_prefix(p.usage), usage=""))
        else:
            merged.append(p)

    return merged


def extract_data_txt_qa(text: str) -> List[dict]:
    keys = ["索引词", "病史摘要", "诊断", "处方", "用法", "分析与结果", "分析", "结果"]
    cleaned = normalize_common(text)
    cleaned = normalize_bracket_headings(cleaned, keys)

    start_iter = list(re.finditer(r"(?m)^\s*索引词\s*[：:]", cleaned))
    qa_pairs: List[dict] = []

    for i, m in enumerate(start_iter):
        start = m.start()
        end = start_iter[i + 1].start() if i + 1 < len(start_iter) else len(cleaned)
        case = cleaned[start:end]

        idx_words = extract_field(case, "索引词", ["病史摘要", "诊断", "处方", "用法", "分析与结果", "分析", "结果", "索引词"])
        history = extract_field(case, "病史摘要", ["诊断", "处方", "用法", "分析与结果", "分析", "结果", "索引词"])
        diagnosis = extract_field(case, "诊断", ["处方", "用法", "分析与结果", "分析", "结果", "索引词"])

        if not idx_words or not history:
            continue

        med_start = re.search(r"(?m)^\s*处方\s*[：:]", case)
        if med_start:
            med_tail = case[med_start.start():]
            stop_m = re.search(r"(?m)^\s*(分析与结果|分析|结果)\s*[：:]", med_tail)
            if stop_m:
                med_tail = med_tail[:stop_m.start()]
            med_pairs = parse_med_pairs(med_tail)
        else:
            med_pairs = []

        q = f"索引词：{idx_words}；病史摘要：{history}"

        a_lines = []
        a_lines.append(f"诊断：{diagnosis if diagnosis else '未提取到'}")
        if med_pairs:
            a_lines.append("处方与用法：")
            for n, pair in enumerate(med_pairs, start=1):
                rx = pair.prescription if pair.prescription else "未提取到"
                use = pair.usage if pair.usage else "未提取到"
                a_lines.append(f"{n}. 处方：{rx} 用法：{use}")
        else:
            a_lines.append("处方与用法：未提取到")

        qa_pairs.append({"Q": q, "A": "\n".join(a_lines)})

    return qa_pairs


def find_next_stop_for_treatment(text: str, start_pos: int) -> int:
    chapter_m = re.search(r"(?m)^\s*第\s*[一二三四五六七八九十百0-9]+\s*章", text[start_pos:])
    sec_m = re.search(r"(?m)^\s*[一二三四五六七八九十]+[、.]", text[start_pos:])

    candidates = []
    if chapter_m:
        candidates.append(start_pos + chapter_m.start())
    if sec_m:
        candidates.append(start_pos + sec_m.start())

    return min(candidates) if candidates else len(text)


def extract_data2_txt_qa(text: str) -> List[dict]:
    keys = ["临床表现", "诊断", "治疗"]
    cleaned = normalize_common(text)
    cleaned = normalize_bracket_headings(cleaned, keys)

    heading_iter = list(re.finditer(r"(?m)^\s*(临床表现|诊断|治疗)\s*[：:]", cleaned))
    qa_pairs: List[dict] = []

    last_t_end = 0
    for i, hm in enumerate(heading_iter):
        key = hm.group(1)
        if key != "治疗":
            continue

        t_start = hm.end()
        t_stop = find_next_stop_for_treatment(cleaned, t_start)
        treatment = compact_text(cleaned[t_start:t_stop])
        if not treatment:
            continue

        prev_region = cleaned[last_t_end:hm.start()]

        clin = ""
        diag = ""

        clin_iter = list(re.finditer(r"(?m)^\s*临床表现\s*[：:]", prev_region))
        if clin_iter:
            c0 = clin_iter[-1]
            c_start = c0.end()
            c_stop_m = re.search(r"(?m)^\s*(诊断|治疗|临床表现)\s*[：:]", prev_region[c_start:])
            c_stop = c_start + c_stop_m.start() if c_stop_m else len(prev_region)
            clin = compact_text(prev_region[c_start:c_stop])

        diag_iter = list(re.finditer(r"(?m)^\s*诊断\s*[：:]", prev_region))
        if diag_iter:
            d0 = diag_iter[-1]
            d_start = d0.end()
            d_stop_m = re.search(r"(?m)^\s*(治疗|临床表现|诊断)\s*[：:]", prev_region[d_start:])
            d_stop = d_start + d_stop_m.start() if d_stop_m else len(prev_region)
            diag = compact_text(prev_region[d_start:d_stop])

        if not clin and not diag:
            last_t_end = t_stop
            continue

        q_parts = []
        if clin:
            q_parts.append(f"临床表现：{clin}")
        if diag:
            q_parts.append(f"诊断：{diag}")

        q = "；".join(q_parts)
        a = f"治疗：{treatment}"
        qa_pairs.append({"Q": q, "A": a})

        last_t_end = t_stop

    return qa_pairs


def qa_to_conversations(qa_pairs: List[dict], system_prompt: str) -> List[dict]:
    data = []
    for item in qa_pairs:
        q = item.get("Q", "").strip()
        a = item.get("A", "").strip()
        if not q or not a:
            continue
        data.append(
            {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": q},
                    {"role": "assistant", "content": a},
                ]
            }
        )
    return data


def load_system_prompt(default_prompt: str, existing_dataset: Optional[str]) -> str:
    if not existing_dataset or not os.path.exists(existing_dataset):
        return default_prompt
    try:
        with open(existing_dataset, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data and "messages" in data[0] and data[0]["messages"]:
            return data[0]["messages"][0].get("content", default_prompt)
    except Exception:
        return default_prompt
    return default_prompt


def save_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild QA + datasets from data.txt and data2.txt")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=int, default=20)
    args = parser.parse_args()

    root = args.project_root
    txt_dir = os.path.join(root, "datasets", "txt")
    qa_dir = os.path.join(root, "datasets", "QA")
    json_dir = os.path.join(root, "datasets", "json")

    data_txt = os.path.join(txt_dir, "data.txt")
    data2_txt = os.path.join(txt_dir, "data2.txt")

    with open(data_txt, "r", encoding="utf-8") as f:
        t1 = f.read()
    with open(data2_txt, "r", encoding="utf-8") as f:
        t2 = f.read()

    qa_data = extract_data_txt_qa(t1)
    qa_data2 = extract_data2_txt_qa(t2)

    save_json(os.path.join(qa_dir, "data_qa_v2.json.txt"), {"qa_pairs": qa_data})
    save_json(os.path.join(qa_dir, "data2_qa_v2.json.txt"), {"qa_pairs": qa_data2})

    system_prompt = load_system_prompt(
        SYSTEM_PROMPT_FALLBACK,
        os.path.join(json_dir, "dataset.json"),
    )

    conv_data = qa_to_conversations(qa_data, system_prompt)
    conv_data2 = qa_to_conversations(qa_data2, system_prompt)

    save_json(os.path.join(json_dir, "dataset_data_v2.json"), conv_data)
    save_json(os.path.join(json_dir, "dataset_data2_v2.json"), conv_data2)

    rng = random.Random(args.seed)
    indices = list(range(len(conv_data)))
    test_size = min(args.test_size, len(indices))
    test_indices = set(rng.sample(indices, test_size))

    data_test_20 = [x for i, x in enumerate(conv_data) if i in test_indices]
    data_train_rest = [x for i, x in enumerate(conv_data) if i not in test_indices]

    eval_mix = list(data_test_20) + list(conv_data2)

    save_json(os.path.join(json_dir, "dataset_data20_test_v2.json"), data_test_20)
    save_json(os.path.join(json_dir, "dataset_internal_test_data20_v2.json"), data_test_20)
    save_json(os.path.join(json_dir, "dataset_data_train_wo20_v2.json"), data_train_rest)
    save_json(os.path.join(json_dir, "dataset_external_test_data2_v2.json"), conv_data2)
    save_json(os.path.join(json_dir, "dataset_eval_data20_plus_data2_v2.json"), eval_mix)

    meta = {
        "seed": args.seed,
        "test_size": test_size,
        "data_count": len(conv_data),
        "data2_count": len(conv_data2),
        "train_count": len(data_train_rest),
        "internal_test20_count": len(data_test_20),
        "external_test_data2_count": len(conv_data2),
        "eval_mix_count": len(eval_mix),
        "test_indices": sorted(test_indices),
        "files": {
            "qa_data": os.path.join(qa_dir, "data_qa_v2.json.txt"),
            "qa_data2": os.path.join(qa_dir, "data2_qa_v2.json.txt"),
            "dataset_data": os.path.join(json_dir, "dataset_data_v2.json"),
            "dataset_data2": os.path.join(json_dir, "dataset_data2_v2.json"),
            "train": os.path.join(json_dir, "dataset_data_train_wo20_v2.json"),
            "internal_test20": os.path.join(json_dir, "dataset_internal_test_data20_v2.json"),
            "external_test_data2": os.path.join(json_dir, "dataset_external_test_data2_v2.json"),
            "compat_test20": os.path.join(json_dir, "dataset_data20_test_v2.json"),
            "compat_eval_mix": os.path.join(json_dir, "dataset_eval_data20_plus_data2_v2.json"),
        },
    }
    save_json(os.path.join(json_dir, "dataset_rebuild_v2_meta.json"), meta)

    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
