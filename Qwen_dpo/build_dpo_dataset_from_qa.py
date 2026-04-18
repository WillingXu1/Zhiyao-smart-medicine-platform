#!/usr/bin/env python3
import argparse
import json
import random
import re
from pathlib import Path
from typing import Dict, List, Tuple


def remove_ctrl_chars(text: str) -> str:
    return "".join(ch if (ch in "\n\r\t" or ord(ch) >= 32) else " " for ch in text)


def fix_broken_json_lines(raw: str) -> str:
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
            if quote_count % 2 == 1:
                nl = "\n" if line.endswith("\n") else ""
                core = line[:-1] if nl else line
                line = core + '"' + nl
        fixed.append(line)
    return "".join(fixed)


def load_qa_pairs(path: Path) -> List[Dict[str, str]]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = remove_ctrl_chars(raw)
    try:
        obj = json.loads(raw)
    except Exception:
        obj = json.loads(fix_broken_json_lines(raw))

    pairs = obj.get("qa_pairs", []) if isinstance(obj, dict) else []
    out = []
    for x in pairs:
        q = str(x.get("Q", "")).strip()
        a = str(x.get("A", "")).strip()
        if q and a:
            out.append({"Q": q, "A": a})
    return out


def load_from_conversations(path: Path) -> List[Dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for item in data:
        msgs = item.get("messages", []) if isinstance(item, dict) else []
        q = ""
        a = ""
        for m in msgs:
            role = m.get("role", "")
            if role == "user" and not q:
                q = str(m.get("content", "")).strip()
            if role == "assistant" and not a:
                a = str(m.get("content", "")).strip()
        if q and a:
            out.append({"Q": q, "A": a})
    return out


def risk_signal(text: str) -> bool:
    patterns = [
        r"处方",
        r"用法",
        r"mg",
        r"毫克",
        r"每日",
        r"每晚",
        r"每次",
        r"口服",
        r"片",
        r"粒",
        r"疗程",
    ]
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def build_chat_messages(question: str) -> List[Dict[str, str]]:
    # Intentionally use a weak system instruction so base model output naturally
    # reflects its raw preference and can serve as rejected samples.
    return [
        {"role": "system", "content": "你是一名医疗问答助手，请直接给出建议。"},
        {"role": "user", "content": question},
    ]


def generate_rejected_transformers(
    prompts: List[str],
    model_path: str,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
    do_sample: bool,
    batch_size: int,
) -> List[str]:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch

    try:
        from tqdm import tqdm
    except Exception:
        tqdm = None

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()

    outputs: List[str] = []
    text_prompts = [
        tokenizer.apply_chat_template(build_chat_messages(q), tokenize=False, add_generation_prompt=True)
        for q in prompts
    ]

    starts = range(0, len(text_prompts), max(1, batch_size))
    if tqdm is not None:
        starts = tqdm(starts, total=(len(text_prompts) + max(1, batch_size) - 1) // max(1, batch_size), desc="Generating rejected")

    for st in starts:
        ed = min(st + max(1, batch_size), len(text_prompts))
        batch_texts = text_prompts[st:ed]
        inputs = tokenizer(
            batch_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(model.device)

        with torch.inference_mode():
            gen_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=do_sample,
                temperature=temperature,
                top_p=top_p,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id,
            )

        input_lens = inputs["attention_mask"].sum(dim=1).tolist()
        for row_ids, in_len in zip(gen_ids, input_lens):
            new_ids = row_ids[int(in_len):]
            text = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
            outputs.append(text)
    return outputs


def generate_rejected_openai(
    prompts: List[str],
    model_name: str,
    base_url: str,
    api_key: str,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
) -> List[str]:
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key)
    outputs = []
    for q in prompts:
        resp = client.chat.completions.create(
            model=model_name,
            messages=build_chat_messages(q),
            max_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        text = (resp.choices[0].message.content or "").strip()
        outputs.append(text)
    return outputs


def generate_rejected_mock(prompts: List[str]) -> List[str]:
    out = []
    for q in prompts:
        out.append(
            "可以先口服奥美拉唑20mg，每日2次，连用2周观察效果；"
            "若症状重可联合多潘立酮10mg，每日3次。" + q[:0]
        )
    return out


def split_train_eval(rows: List[dict], eval_ratio: float, seed: int) -> Tuple[List[dict], List[dict]]:
    if not rows:
        return [], []
    rng = random.Random(seed)
    idx = list(range(len(rows)))
    rng.shuffle(idx)
    eval_n = max(1, int(round(len(rows) * eval_ratio))) if len(rows) > 1 and eval_ratio > 0 else 0
    eval_ids = set(idx[:eval_n])
    train = [r for i, r in enumerate(rows) if i not in eval_ids]
    eval_rows = [r for i, r in enumerate(rows) if i in eval_ids]
    return train, eval_rows


def write_jsonl(path: Path, rows: List[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build DPO dataset with base-model rejected responses")
    parser.add_argument("--input-qa", default="datasets/QA/data_qa_v2.json.txt", help="qa_pairs json/txt path")
    parser.add_argument(
        "--input-conversations",
        default="",
        help="Optional existing conversations json path. If set, read Q/A from messages.",
    )
    parser.add_argument("--output-dir", default="datasets/dpo", help="Output directory")
    parser.add_argument("--output-prefix", default="qwen25_3b_from_qa", help="Output file prefix")
    parser.add_argument("--backend", choices=["transformers", "openai", "mock"], default="transformers")

    parser.add_argument("--model-path", default="TestModels/Qwen2.5-3B-Instruct", help="HF model path for transformers backend")
    parser.add_argument("--openai-model", default="Qwen2.5-3B-Instruct", help="Model name for OpenAI-compatible backend")
    parser.add_argument("--openai-base-url", default="http://127.0.0.1:8000/v1", help="OpenAI-compatible endpoint")
    parser.add_argument("--openai-api-key", default="EMPTY", help="OpenAI-compatible api key")

    parser.add_argument("--max-samples", type=int, default=0, help="0 means all")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-new-tokens", type=int, default=320)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for transformers backend")
    parser.add_argument("--do-sample", action="store_true", default=True)
    parser.add_argument("--no-sample", action="store_true", help="Disable sampling")
    parser.add_argument("--eval-ratio", type=float, default=0.1)
    parser.add_argument("--drop-empty-rejected", action="store_true", default=True)
    parser.add_argument("--keep-non-risk-rejected", action="store_true", help="Keep rows where rejected has no dose/prescription-like signal")
    args = parser.parse_args()

    use_sample = False if args.no_sample else bool(args.do_sample)

    if args.input_conversations:
        pairs = load_from_conversations(Path(args.input_conversations))
    else:
        pairs = load_qa_pairs(Path(args.input_qa))

    if args.max_samples and args.max_samples > 0:
        pairs = pairs[: args.max_samples]

    prompts = [x["Q"] for x in pairs]
    chosen = [x["A"] for x in pairs]

    if args.backend == "transformers":
        rejected = generate_rejected_transformers(
            prompts,
            model_path=args.model_path,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            do_sample=use_sample,
            batch_size=args.batch_size,
        )
    elif args.backend == "openai":
        rejected = generate_rejected_openai(
            prompts,
            model_name=args.openai_model,
            base_url=args.openai_base_url,
            api_key=args.openai_api_key,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
        )
    else:
        rejected = generate_rejected_mock(prompts)

    rows: List[dict] = []
    risky_cnt = 0
    for p, c, r in zip(prompts, chosen, rejected):
        p = str(p).strip()
        c = str(c).strip()
        r = str(r).strip()
        if not p or not c:
            continue
        if args.drop_empty_rejected and not r:
            continue
        is_risky = risk_signal(r)
        if is_risky:
            risky_cnt += 1
        if (not args.keep_non_risk_rejected) and (not is_risky):
            continue
        rows.append(
            {
                "prompt": p,
                "chosen": c,
                "rejected": r,
            }
        )

    train_rows, eval_rows = split_train_eval(rows, args.eval_ratio, args.seed)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_path = out_dir / f"{args.output_prefix}_train.jsonl"
    eval_path = out_dir / f"{args.output_prefix}_eval.jsonl"
    all_path = out_dir / f"{args.output_prefix}_all.jsonl"
    meta_path = out_dir / f"{args.output_prefix}_meta.json"

    write_jsonl(train_path, train_rows)
    write_jsonl(eval_path, eval_rows)
    write_jsonl(all_path, rows)

    meta = {
        "backend": args.backend,
        "input_qa": args.input_qa,
        "input_conversations": args.input_conversations,
        "total_input_pairs": len(pairs),
        "total_output_pairs": len(rows),
        "train_size": len(train_rows),
        "eval_size": len(eval_rows),
        "risk_signal_count": risky_cnt,
        "risk_signal_ratio": round(risky_cnt / len(rejected), 4) if rejected else 0.0,
        "args": {
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "batch_size": args.batch_size,
            "do_sample": use_sample,
            "eval_ratio": args.eval_ratio,
            "keep_non_risk_rejected": args.keep_non_risk_rejected,
        },
        "files": {
            "train": str(train_path),
            "eval": str(eval_path),
            "all": str(all_path),
        },
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
