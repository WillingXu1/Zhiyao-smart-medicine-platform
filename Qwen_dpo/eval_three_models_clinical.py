#!/usr/bin/env python3
import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_json(path: Path) -> List[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(s: str) -> str:
    s = (s or "").replace("\r", "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def tokenize(s: str) -> List[str]:
    s = normalize_text(s)
    if not s:
        return []
    if has_cjk(s):
        return [c for c in s if not c.isspace()]
    return s.split(" ")


def exact_match(pred: str, ref: str) -> float:
    return 1.0 if normalize_text(pred) == normalize_text(ref) else 0.0


def f1_score(pred: str, ref: str) -> float:
    p = tokenize(pred)
    r = tokenize(ref)
    if not p and not r:
        return 1.0
    if not p or not r:
        return 0.0

    ref_count: Dict[str, int] = {}
    for t in r:
        ref_count[t] = ref_count.get(t, 0) + 1
    hit = 0
    for t in p:
        if ref_count.get(t, 0) > 0:
            hit += 1
            ref_count[t] -= 1
    prec = hit / len(p)
    rec = hit / len(r)
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


def lcs_len(a: List[str], b: List[str]) -> int:
    if not a or not b:
        return 0
    dp = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        prev = 0
        for j in range(1, len(b) + 1):
            tmp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = tmp
    return dp[-1]


def rouge_l_f1(pred: str, ref: str) -> float:
    p = tokenize(pred)
    r = tokenize(ref)
    if not p and not r:
        return 1.0
    if not p or not r:
        return 0.0
    l = lcs_len(p, r)
    prec = l / len(p)
    rec = l / len(r)
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


def ngram_counts(tokens: List[str], n: int) -> Dict[Tuple[str, ...], int]:
    d: Dict[Tuple[str, ...], int] = {}
    if len(tokens) < n:
        return d
    for i in range(len(tokens) - n + 1):
        g = tuple(tokens[i : i + n])
        d[g] = d.get(g, 0) + 1
    return d


def bleu4(pred: str, ref: str) -> float:
    p = tokenize(pred)
    r = tokenize(ref)
    if not p and not r:
        return 1.0
    if not p or not r:
        return 0.0

    log_prec_sum = 0.0
    for n in [1, 2, 3, 4]:
        p_cnt = ngram_counts(p, n)
        r_cnt = ngram_counts(r, n)
        if not p_cnt:
            prec_n = 0.5
        else:
            match = 0
            total = 0
            for g, c in p_cnt.items():
                total += c
                match += min(c, r_cnt.get(g, 0))
            prec_n = (match + 1.0) / (total + 1.0)
        log_prec_sum += 0.25 * math.log(max(prec_n, 1e-12))
    bp = 1.0 if len(p) > len(r) else math.exp(1 - len(r) / max(1, len(p)))
    return bp * math.exp(log_prec_sum)


SECTION_PATTERNS = {
    "diagnosis": [r"诊断[：:\s]", r"诊断结果[：:\s]", r"中医诊断[：:\s]", r"西医诊断[：:\s]", r"辨证[：:\s]"],
    "prescription": [r"处方[：:\s]", r"方药[：:\s]", r"方剂[：:\s]", r"药物[：:\s]", r"用药方案[：:\s]"],
    "usage": [r"用法[：:\s]", r"用量[：:\s]", r"服法[：:\s]", r"频次[：:\s]", r"疗程[：:\s]", r"注意事项[：:\s]"],
}


def first_hit(text: str, pats: List[str]) -> int:
    best = -1
    for p in pats:
        m = re.search(p, text)
        if not m:
            continue
        i = m.start()
        if best < 0 or i < best:
            best = i
    return best


def split_sections(text: str) -> Dict[str, str]:
    t = normalize_text(text)
    if not t:
        return {"diagnosis": "", "prescription": "", "usage": ""}
    locs: List[Tuple[str, int]] = []
    for name, pats in SECTION_PATTERNS.items():
        i = first_hit(t, pats)
        if i >= 0:
            locs.append((name, i))
    if not locs:
        return {"diagnosis": t, "prescription": "", "usage": ""}

    locs.sort(key=lambda x: x[1])
    out = {"diagnosis": "", "prescription": "", "usage": ""}
    for i, (name, st) in enumerate(locs):
        ed = locs[i + 1][1] if i + 1 < len(locs) else len(t)
        out[name] = normalize_text(t[st:ed])
    return out


def load_medical_terms(path: str) -> set:
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        return set()
    terms = set()
    for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        x = normalize_text(ln)
        if len(x) >= 2:
            terms.add(x)
    return terms


def extract_terms(text: str, term_dict: set) -> set:
    t = normalize_text(text)
    if not t:
        return set()
    if term_dict:
        return {x for x in term_dict if x in t}
    cjk = set(re.findall(r"[\u4e00-\u9fff]{2,8}", t))
    ascii_terms = set(re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", t))
    return {x for x in cjk.union(ascii_terms) if x not in {"患者", "建议", "治疗", "情况", "可以", "需要"}}


def term_recall(pred: str, ref: str, term_dict: set) -> float:
    rt = extract_terms(ref, term_dict)
    if not rt:
        return 1.0
    pt = extract_terms(pred, term_dict)
    return len(rt.intersection(pt)) / max(1, len(rt))


def build_prompt(tokenizer, messages: List[dict]) -> str:
    msgs = []
    for m in messages:
        if m.get("role") in {"system", "user"}:
            msgs.append({"role": m.get("role"), "content": m.get("content", "")})
    return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def load_model_tokenizer(base_model: str, adapter: str):
    tok = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=dtype if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )
    if adapter:
        model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    return model, tok


def run_generation(model, tok, dataset: List[dict], out_jsonl: Path, tag: str, max_new_tokens: int) -> None:
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as fw:
        for i, item in enumerate(dataset, 1):
            messages = item.get("messages", [])
            prompt = build_prompt(tok, messages)
            inputs = tok(prompt, return_tensors="pt")
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            with torch.inference_mode():
                out = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    temperature=0.0,
                    eos_token_id=tok.eos_token_id,
                    pad_token_id=tok.eos_token_id,
                )
            gen_ids = out[0][inputs["input_ids"].shape[1] :]
            pred = tok.decode(gen_ids, skip_special_tokens=True).strip()

            ref = ""
            for m in messages:
                if m.get("role") == "assistant":
                    ref = m.get("content", "")
                    break
            fw.write(
                json.dumps(
                    {"response": pred, "labels": ref, "messages": messages, "tag": tag},
                    ensure_ascii=False,
                )
                + "\n"
            )
            if i % 5 == 0 or i == len(dataset):
                print(f"[{tag}] {i}/{len(dataset)}")


def summarize_rows(rows: List[dict], term_dict: set) -> Dict[str, float]:
    ems, f1s, rls, b4s, trs = [], [], [], [], []
    d_scores, p_scores, u_scores = [], [], []

    for row in rows:
        pred = str(row.get("response", ""))
        ref = str(row.get("labels", ""))

        ems.append(exact_match(pred, ref))
        f1s.append(f1_score(pred, ref))
        rls.append(rouge_l_f1(pred, ref))
        b4s.append(bleu4(pred, ref))
        trs.append(term_recall(pred, ref, term_dict))

        ps = split_sections(pred)
        rs = split_sections(ref)
        d_scores.append(rouge_l_f1(ps["diagnosis"], rs["diagnosis"]))
        p_scores.append(rouge_l_f1(ps["prescription"], rs["prescription"]))
        u_scores.append(rouge_l_f1(ps["usage"], rs["usage"]))

    mean = lambda x: (sum(x) / len(x)) if x else 0.0
    return {
        "n": len(rows),
        "exact_match": mean(ems),
        "f1": mean(f1s),
        "rouge_l": mean(rls),
        "bleu_4": mean(b4s),
        "rouge_l_diagnosis": mean(d_scores),
        "rouge_l_prescription": mean(p_scores),
        "rouge_l_usage": mean(u_scores),
        "terminology_recall": mean(trs),
    }


def read_jsonl(path: Path) -> List[dict]:
    out = []
    for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        out.append(json.loads(ln))
    return out


def export_manual_topk(rows: List[dict], out_csv: Path, topk: int, term_dict: set) -> None:
    scored = []
    for i, row in enumerate(rows):
        pred = str(row.get("response", ""))
        ref = str(row.get("labels", ""))
        ps = split_sections(pred)
        rs = split_sections(ref)
        d = rouge_l_f1(ps["diagnosis"], rs["diagnosis"])
        p = rouge_l_f1(ps["prescription"], rs["prescription"])
        u = rouge_l_f1(ps["usage"], rs["usage"])
        tr = term_recall(pred, ref, term_dict)
        risk = 1.0 - (0.4 * d + 0.25 * p + 0.25 * u + 0.10 * tr)
        user = ""
        msgs = row.get("messages") or []
        if len(msgs) >= 2:
            user = str(msgs[1].get("content", ""))
        scored.append(
            {
                "idx": i,
                "risk_score": risk,
                "rouge_l_diagnosis": d,
                "rouge_l_prescription": p,
                "rouge_l_usage": u,
                "terminology_recall": tr,
                "user": user,
                "reference": ref,
                "prediction": pred,
            }
        )

    scored.sort(key=lambda x: x["risk_score"], reverse=True)
    pick = scored[: max(1, topk)]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "idx",
                "risk_score",
                "rouge_l_diagnosis",
                "rouge_l_prescription",
                "rouge_l_usage",
                "terminology_recall",
                "user",
                "reference",
                "prediction",
            ],
        )
        w.writeheader()
        for r in pick:
            w.writerow(r)


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate base/SFT/DPO with aligned clinical layered metrics.")
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--sft-adapter", required=True)
    ap.add_argument("--dpo-adapter", required=True)
    ap.add_argument("--internal", required=True)
    ap.add_argument("--external", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--medical-terms-file", default="")
    ap.add_argument("--manual-topk", type=int, default=40)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    terms = load_medical_terms(args.medical_terms_file)

    internal = load_json(Path(args.internal))
    external = load_json(Path(args.external))

    specs = [
        ("base", ""),
        ("sft", args.sft_adapter),
        ("dpo", args.dpo_adapter),
    ]

    for name, adapter in specs:
        model, tok = load_model_tokenizer(args.base_model, adapter)
        run_generation(
            model,
            tok,
            internal,
            out_dir / f"internal20_{name}.jsonl",
            f"internal20_{name}",
            args.max_new_tokens,
        )
        run_generation(
            model,
            tok,
            external,
            out_dir / f"external23_{name}.jsonl",
            f"external23_{name}",
            args.max_new_tokens,
        )
        del model
        torch.cuda.empty_cache()

    report = {"internal": {}, "external": {}, "delta_vs_base": {"internal": {}, "external": {}}}
    for split, prefix in [("internal", "internal20"), ("external", "external23")]:
        for name in ["base", "sft", "dpo"]:
            rows = read_jsonl(out_dir / f"{prefix}_{name}.jsonl")
            report[split][name] = summarize_rows(rows, terms)

        b = report[split]["base"]
        for name in ["sft", "dpo"]:
            x = report[split][name]
            report["delta_vs_base"][split][name] = {
                "rouge_l": x["rouge_l"] - b["rouge_l"],
                "f1": x["f1"] - b["f1"],
                "rouge_l_diagnosis": x["rouge_l_diagnosis"] - b["rouge_l_diagnosis"],
                "rouge_l_prescription": x["rouge_l_prescription"] - b["rouge_l_prescription"],
                "rouge_l_usage": x["rouge_l_usage"] - b["rouge_l_usage"],
                "terminology_recall": x["terminology_recall"] - b["terminology_recall"],
            }

    dpo_internal_rows = read_jsonl(out_dir / "internal20_dpo.jsonl")
    export_manual_topk(dpo_internal_rows, out_dir / "manual_review_topk_dpo_internal.csv", args.manual_topk, terms)

    report_path = out_dir / "three_model_eval_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# 三模型对比评测（Base vs SFT vs DPO）",
        "",
        "## Internal20",
        "",
        "| 模型 | EM | F1 | Rouge-L | 诊断RL | 处方RL | 用法RL | 术语召回 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ["base", "sft", "dpo"]:
        m = report["internal"][name]
        md_lines.append(
            f"| {name} | {m['exact_match']:.4f} | {m['f1']:.4f} | {m['rouge_l']:.4f} | {m['rouge_l_diagnosis']:.4f} | {m['rouge_l_prescription']:.4f} | {m['rouge_l_usage']:.4f} | {m['terminology_recall']:.4f} |"
        )

    md_lines += [
        "",
        "## External23",
        "",
        "| 模型 | EM | F1 | Rouge-L | 诊断RL | 处方RL | 用法RL | 术语召回 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ["base", "sft", "dpo"]:
        m = report["external"][name]
        md_lines.append(
            f"| {name} | {m['exact_match']:.4f} | {m['f1']:.4f} | {m['rouge_l']:.4f} | {m['rouge_l_diagnosis']:.4f} | {m['rouge_l_prescription']:.4f} | {m['rouge_l_usage']:.4f} | {m['terminology_recall']:.4f} |"
        )
    md_lines += [
        "",
        "## Delta vs Base (Internal20)",
        f"- SFT: Rouge-L={report['delta_vs_base']['internal']['sft']['rouge_l']:+.4f}, 诊断RL={report['delta_vs_base']['internal']['sft']['rouge_l_diagnosis']:+.4f}, 处方RL={report['delta_vs_base']['internal']['sft']['rouge_l_prescription']:+.4f}, 用法RL={report['delta_vs_base']['internal']['sft']['rouge_l_usage']:+.4f}, 术语召回={report['delta_vs_base']['internal']['sft']['terminology_recall']:+.4f}",
        f"- DPO: Rouge-L={report['delta_vs_base']['internal']['dpo']['rouge_l']:+.4f}, 诊断RL={report['delta_vs_base']['internal']['dpo']['rouge_l_diagnosis']:+.4f}, 处方RL={report['delta_vs_base']['internal']['dpo']['rouge_l_prescription']:+.4f}, 用法RL={report['delta_vs_base']['internal']['dpo']['rouge_l_usage']:+.4f}, 术语召回={report['delta_vs_base']['internal']['dpo']['terminology_recall']:+.4f}",
        "",
        "- 人审清单: manual_review_topk_dpo_internal.csv",
    ]

    (out_dir / "three_model_eval_report.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"saved: {report_path}")
    print(f"saved: {out_dir / 'three_model_eval_report.md'}")
    print(f"saved: {out_dir / 'manual_review_topk_dpo_internal.csv'}")


if __name__ == "__main__":
    main()
