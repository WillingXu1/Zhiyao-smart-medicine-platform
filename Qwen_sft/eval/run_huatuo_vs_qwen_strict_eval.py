#!/usr/bin/env python3
import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluate_metrics_extended import layered_internal_metrics, summarize


def load_dataset(path: Path) -> List[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_prompt(tokenizer, messages: List[dict]) -> str:
    msgs = []
    for m in messages:
        role = m.get("role")
        if role in {"system", "user"}:
            msgs.append({"role": role, "content": m.get("content", "")})

    # Prefer model native chat template when available.
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        except Exception:
            pass

    system_text = ""
    user_text = ""
    for m in msgs:
        if m["role"] == "system":
            system_text = m["content"]
        elif m["role"] == "user":
            user_text = m["content"]
    return f"系统：{system_text}\n用户：{user_text}\n助手："


def generate_once(model, tokenizer, prompt: str, max_new_tokens: int) -> str:
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=0.0,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )
    gen_ids = out[0][inputs["input_ids"].shape[1] :]
    return tokenizer.decode(gen_ids, skip_special_tokens=True).strip()


def infer_dataset(model, tokenizer, dataset: List[dict], tag: str, max_new_tokens: int) -> List[dict]:
    rows: List[dict] = []
    for i, item in enumerate(dataset, start=1):
        messages = item.get("messages", [])
        prompt = build_prompt(tokenizer, messages)
        pred = generate_once(model, tokenizer, prompt, max_new_tokens=max_new_tokens)

        label = ""
        for m in messages:
            if m.get("role") == "assistant":
                label = m.get("content", "")
                break

        rows.append(
            {
                "response": pred,
                "labels": label,
                "messages": messages,
                "tag": tag,
            }
        )
        if i % 5 == 0 or i == len(dataset):
            print(f"[{tag}] {i}/{len(dataset)}")

    return rows


def write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def rep_ratio(text: str) -> float:
    toks = re.findall(r"\S+", text or "")
    if len(toks) < 3:
        return 0.0
    bi = [" ".join(toks[i : i + 2]) for i in range(len(toks) - 1)]
    return 1 - len(set(bi)) / len(bi)


META_PATTERNS = [r"根据您提供的信息", r"建议：", r"请务必", r"仅供参考", r"###", r"总结"]
META_RE = [re.compile(p) for p in META_PATTERNS]


def hallucination_proxy_rate(rows: List[dict]) -> Dict[str, float]:
    n = len(rows)
    low_overlap = 0
    overgen = 0
    high_repeat = 0
    meta = 0
    hallucinated = 0

    for r in rows:
        label = str(r.get("labels", ""))
        pred = str(r.get("response", ""))

        ov = SequenceMatcher(None, pred, label).ratio()
        lr = len(pred) / (len(label) + 1e-6)
        rr = rep_ratio(pred)
        mt = any(rx.search(pred) for rx in META_RE)

        c1 = ov < 0.10
        c2 = lr > 3.0
        c3 = rr > 0.05
        c4 = mt and ov < 0.20

        hall = (c1 or c2 or c3 or c4)

        low_overlap += int(c1)
        overgen += int(c2)
        high_repeat += int(c3)
        meta += int(c4)
        hallucinated += int(hall)

    if n == 0:
        return {
            "n": 0,
            "low_overlap_rate": 0.0,
            "overgen_rate": 0.0,
            "high_repeat_rate": 0.0,
            "meta_hall_rate": 0.0,
            "hallucination_proxy_rate": 0.0,
        }

    return {
        "n": n,
        "low_overlap_rate": low_overlap / n,
        "overgen_rate": overgen / n,
        "high_repeat_rate": high_repeat / n,
        "meta_hall_rate": meta / n,
        "hallucination_proxy_rate": hallucinated / n,
    }


def pooled_mean(v_int: float, n_int: int, v_ext: float, n_ext: int) -> float:
    denom = max(1, n_int + n_ext)
    return (v_int * n_int + v_ext * n_ext) / denom


def _sanitize_tag(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9._-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def infer_qwen_tag(adapter_path: str) -> str:
    p = Path(adapter_path)
    name = _sanitize_tag(p.name)
    parent = _sanitize_tag(p.parent.name)

    if name == "dpo_final":
        if parent:
            return f"qwen25_7b_{parent}_dpo"
        return "qwen25_7b_dpo"

    if name.startswith("checkpoint-"):
        if parent:
            return f"qwen25_7b_{parent}_{name}"
        return f"qwen25_7b_{name}"

    if name:
        return f"qwen25_7b_{name}"

    return "qwen25_7b_adapter"


def main() -> None:
    parser = argparse.ArgumentParser(description="Strict same-set comparison: Huatuo zero-shot vs Qwen7B adapter")
    parser.add_argument("--huatuo-model", required=True)
    parser.add_argument("--qwen-base-model", required=True)
    parser.add_argument("--qwen-adapter", required=True)
    parser.add_argument(
        "--qwen-tag",
        default="",
        help="Optional custom tag for qwen outputs/report. If empty, infer from adapter path.",
    )
    parser.add_argument("--internal", required=True)
    parser.add_argument("--external", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=128)

    parser.add_argument("--w-f1", type=float, default=0.35)
    parser.add_argument("--w-diagnosis", type=float, default=0.15)
    parser.add_argument("--w-prescription", type=float, default=0.10)
    parser.add_argument("--w-usage", type=float, default=0.10)
    parser.add_argument("--w-hallucination", type=float, default=0.30)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    qwen_tag = _sanitize_tag(args.qwen_tag) if args.qwen_tag else infer_qwen_tag(args.qwen_adapter)
    qwen_internal_tag = f"internal59_{qwen_tag}"
    qwen_external_tag = f"external24_{qwen_tag}"

    internal = load_dataset(Path(args.internal))
    external = load_dataset(Path(args.external))

    # 1) Huatuo zero-shot inference.
    print("Loading Huatuo model...")
    huatuo_tok = AutoTokenizer.from_pretrained(args.huatuo_model, trust_remote_code=True)
    if huatuo_tok.pad_token is None:
        huatuo_tok.pad_token = huatuo_tok.eos_token
    huatuo_model = AutoModelForCausalLM.from_pretrained(
        args.huatuo_model,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    huatuo_model.eval()

    rows_i_h = infer_dataset(huatuo_model, huatuo_tok, internal, "internal59_huatuo_o1_7b_zeroshot", args.max_new_tokens)
    rows_e_h = infer_dataset(huatuo_model, huatuo_tok, external, "external24_huatuo_o1_7b_zeroshot", args.max_new_tokens)

    write_jsonl(out_dir / "internal59_huatuo_o1_7b_zeroshot.jsonl", rows_i_h)
    write_jsonl(out_dir / "external24_huatuo_o1_7b_zeroshot.jsonl", rows_e_h)

    del huatuo_model
    torch.cuda.empty_cache()

    # 2) Qwen fine-tuned inference.
    print("Loading Qwen base + LoRA...")
    qwen_tok = AutoTokenizer.from_pretrained(args.qwen_base_model, trust_remote_code=True)
    if qwen_tok.pad_token is None:
        qwen_tok.pad_token = qwen_tok.eos_token
    qwen_base = AutoModelForCausalLM.from_pretrained(
        args.qwen_base_model,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    qwen_model = PeftModel.from_pretrained(qwen_base, args.qwen_adapter)
    qwen_model.eval()

    rows_i_q = infer_dataset(qwen_model, qwen_tok, internal, qwen_internal_tag, args.max_new_tokens)
    rows_e_q = infer_dataset(qwen_model, qwen_tok, external, qwen_external_tag, args.max_new_tokens)

    write_jsonl(out_dir / f"{qwen_internal_tag}.jsonl", rows_i_q)
    write_jsonl(out_dir / f"{qwen_external_tag}.jsonl", rows_e_q)

    # 3) Unified metrics.
    m_i_h = summarize(rows_i_h)
    m_e_h = summarize(rows_e_h)
    m_i_q = summarize(rows_i_q)
    m_e_q = summarize(rows_e_q)

    layered_h = layered_internal_metrics(rows_i_h, set())
    layered_q = layered_internal_metrics(rows_i_q, set())

    hall_i_h = hallucination_proxy_rate(rows_i_h)
    hall_e_h = hallucination_proxy_rate(rows_e_h)
    hall_i_q = hallucination_proxy_rate(rows_i_q)
    hall_e_q = hallucination_proxy_rate(rows_e_q)

    n_i = len(rows_i_h)
    n_e = len(rows_e_h)

    f1_h = pooled_mean(m_i_h["f1"], n_i, m_e_h["f1"], n_e)
    f1_q = pooled_mean(m_i_q["f1"], n_i, m_e_q["f1"], n_e)

    hall_h = pooled_mean(hall_i_h["hallucination_proxy_rate"], n_i, hall_e_h["hallucination_proxy_rate"], n_e)
    hall_q = pooled_mean(hall_i_q["hallucination_proxy_rate"], n_i, hall_e_q["hallucination_proxy_rate"], n_e)

    wsum = args.w_f1 + args.w_diagnosis + args.w_prescription + args.w_usage + args.w_hallucination
    if abs(wsum - 1.0) > 1e-8:
        raise ValueError(f"weights must sum to 1.0, got {wsum}")

    score_h = (
        args.w_f1 * f1_h
        + args.w_diagnosis * layered_h["rouge_l_diagnosis"]
        + args.w_prescription * layered_h["rouge_l_prescription"]
        + args.w_usage * layered_h["rouge_l_usage"]
        + args.w_hallucination * (1.0 - hall_h)
    )
    score_q = (
        args.w_f1 * f1_q
        + args.w_diagnosis * layered_q["rouge_l_diagnosis"]
        + args.w_prescription * layered_q["rouge_l_prescription"]
        + args.w_usage * layered_q["rouge_l_usage"]
        + args.w_hallucination * (1.0 - hall_q)
    )

    winner = "huatuo_o1_7b_zeroshot" if score_h > score_q else qwen_tag

    report = {
        "dataset": {
            "internal": args.internal,
            "external": args.external,
            "internal_n": n_i,
            "external_n": n_e,
            "qwen_adapter": args.qwen_adapter,
            "qwen_tag": qwen_tag,
        },
        "models": {
            "huatuo": {
                "internal": m_i_h,
                "external": m_e_h,
                "internal_layered": layered_h,
                "hallucination_internal": hall_i_h,
                "hallucination_external": hall_e_h,
                "pooled_f1": f1_h,
                "pooled_hallucination_proxy_rate": hall_h,
                "weighted_score": score_h,
            },
            "qwen_ft": {
                "internal": m_i_q,
                "external": m_e_q,
                "internal_layered": layered_q,
                "hallucination_internal": hall_i_q,
                "hallucination_external": hall_e_q,
                "pooled_f1": f1_q,
                "pooled_hallucination_proxy_rate": hall_q,
                "weighted_score": score_q,
            },
        },
        "weights": {
            "f1": args.w_f1,
            "rouge_l_diagnosis": args.w_diagnosis,
            "rouge_l_prescription": args.w_prescription,
            "rouge_l_usage": args.w_usage,
            "hallucination_inverse": args.w_hallucination,
        },
        "decision": {
            "winner": winner,
            "score_delta_huatuo_minus_qwen": score_h - score_q,
            "recommendation": (
                "Huatuo wins: proceed to Huatuo SFT then DPO pilot"
                if winner == "huatuo_o1_7b_zeroshot"
                else "Qwen adapter wins: keep Qwen as mainline, Huatuo remains baseline"
            ),
        },
    }

    out_json = out_dir / "strict_compare_huatuo_vs_qwen_internal59_external24.json"
    out_md = out_dir / "strict_compare_huatuo_vs_qwen_internal59_external24.md"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# Strict Same-Set Comparison: HuatuoGPT-o1-7B Zero-shot vs Qwen2.5-7B Adapter")
    md.append("")
    md.append(f"- internal_n: {n_i}")
    md.append(f"- external_n: {n_e}")
    md.append(f"- qwen_tag: {qwen_tag}")
    md.append("")
    md.append("## Weighted Decision")
    md.append(f"- huatuo_score: {score_h:.6f}")
    md.append(f"- qwen_ft_score: {score_q:.6f}")
    md.append(f"- delta(h-q): {score_h - score_q:+.6f}")
    md.append(f"- winner: {winner}")
    md.append("")
    md.append("## Pooled Core Metrics")
    md.append("| Model | pooled F1 | pooled Hallucination(proxy) | diagnosis RL | prescription RL | usage RL |")
    md.append("|---|---:|---:|---:|---:|---:|")
    md.append(
        "| Huatuo-o1-7B-zero | "
        f"{f1_h:.4f} | {hall_h:.4f} | {layered_h['rouge_l_diagnosis']:.4f} | {layered_h['rouge_l_prescription']:.4f} | {layered_h['rouge_l_usage']:.4f} |"
    )
    md.append(
        f"| Qwen2.5-7B-{qwen_tag} | "
        f"{f1_q:.4f} | {hall_q:.4f} | {layered_q['rouge_l_diagnosis']:.4f} | {layered_q['rouge_l_prescription']:.4f} | {layered_q['rouge_l_usage']:.4f} |"
    )

    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"saved: {out_json}")
    print(f"saved: {out_md}")


if __name__ == "__main__":
    main()
