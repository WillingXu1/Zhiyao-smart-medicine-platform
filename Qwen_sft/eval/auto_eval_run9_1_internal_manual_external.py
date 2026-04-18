#!/usr/bin/env python3
import argparse
import csv
import json
import re
from pathlib import Path
from difflib import SequenceMatcher as S

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
    for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if ln.strip():
            rows.append(json.loads(ln))
    return rows


def build_prompt(tokenizer, messages):
    msgs = []
    for m in messages:
        if m.get("role") in {"system", "user"}:
            msgs.append({"role": m.get("role"), "content": m.get("content", "")})
    return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def load_model(base_model: str, adapter: str):
    tok = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
    )
    model = PeftModel.from_pretrained(base, adapter)
    model.eval()
    return model, tok


def infer_dataset(model, tok, dataset, out_path: Path, tag: str, max_new_tokens: int = 384):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fw:
        for i, item in enumerate(dataset, 1):
            messages = item.get("messages", [])
            prompt = build_prompt(tok, messages)
            inputs = tok(prompt, return_tensors="pt")
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    temperature=0.0,
                    top_p=1.0,
                    eos_token_id=tok.eos_token_id,
                    pad_token_id=tok.eos_token_id,
                )
            gen_ids = out[0][inputs["input_ids"].shape[1] :]
            pred = tok.decode(gen_ids, skip_special_tokens=True).strip()
            label = ""
            user_q = ""
            for m in messages:
                if m.get("role") == "assistant" and not label:
                    label = m.get("content", "")
                if m.get("role") == "user" and not user_q:
                    user_q = m.get("content", "")
            rec = {"id": i, "question": user_q, "response": pred, "labels": label, "messages": messages, "tag": tag}
            fw.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if i % 5 == 0 or i == len(dataset):
                print(f"[{tag}] {i}/{len(dataset)}")


def repeat_ratio(text: str) -> float:
    toks = re.findall(r"\S+", text)
    if len(toks) < 3:
        return 0.0
    bi = [" ".join(toks[i : i + 2]) for i in range(len(toks) - 1)]
    return 1 - len(set(bi)) / len(bi)


def summarize(rows):
    if not rows:
        return {}
    overlaps, lens, reps = [], [], []
    em = 0
    for r in rows:
        pred = str(r.get("response", ""))
        lab = str(r.get("labels", ""))
        overlaps.append(S(None, pred, lab).ratio())
        lens.append(len(pred) / (len(lab) + 1e-6))
        reps.append(repeat_ratio(pred))
        if pred.strip() == lab.strip():
            em += 1
    n = len(rows)
    return {
        "n": n,
        "overlap_mean": sum(overlaps) / n,
        "len_ratio_mean": sum(lens) / n,
        "repeat_mean": sum(reps) / n,
        "exact_match_rate": em / n,
    }


def get_best_ckpt(run_dir: Path) -> Path:
    log_path = run_dir / "logging.jsonl"
    if log_path.exists():
        for ln in log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[::-1]:
            if not ln.strip():
                continue
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            if "best_model_checkpoint" in obj:
                return Path(obj["best_model_checkpoint"])
    cks = sorted(run_dir.glob("checkpoint-*"), key=lambda p: p.name)
    if not cks:
        raise RuntimeError(f"No checkpoint found in {run_dir}")
    return cks[-1]


def write_manual_csv(run8_rows, run_new_rows, csv_path: Path, new_tag: str):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id",
            "question",
            "reference",
            "run8_response",
            f"{new_tag}_response",
            "score_run8_history_0_2",
            "score_run8_hallucination_0_2",
            "score_run8_structure_0_2",
            f"score_{new_tag}_history_0_2",
            f"score_{new_tag}_hallucination_0_2",
            f"score_{new_tag}_structure_0_2",
            f"winner(run8/{new_tag}/tie)",
            "notes",
        ])
        n = min(len(run8_rows), len(run_new_rows))
        for i in range(n):
            a = run8_rows[i]
            b = run_new_rows[i]
            writer.writerow([
                i + 1,
                a.get("question", "").replace("\n", " "),
                a.get("labels", "").replace("\n", " "),
                a.get("response", "").replace("\n", " "),
                b.get("response", "").replace("\n", " "),
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ])


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate run8 vs target run (internal auto, external manual package)")
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--run8-dir", required=True)
    parser.add_argument("--target-run-dir", required=True)
    parser.add_argument("--target-tag", default="run9_1")
    parser.add_argument("--internal", required=True)
    parser.add_argument("--external", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target_tag = args.target_tag

    run8_ckpt = get_best_ckpt(Path(args.run8_dir))
    run_new_ckpt = get_best_ckpt(Path(args.target_run_dir))

    internal = read_json(Path(args.internal))
    external = read_json(Path(args.external))

    print("Evaluating run8:", run8_ckpt)
    model8, tok8 = load_model(args.base_model, str(run8_ckpt))
    infer_dataset(model8, tok8, internal, out_dir / "internal_run8.jsonl", "internal_run8")
    infer_dataset(model8, tok8, external, out_dir / "external_run8_manual.jsonl", "external_run8_manual")
    del model8
    torch.cuda.empty_cache()

    print(f"Evaluating {target_tag}:", run_new_ckpt)
    model_new, tok_new = load_model(args.base_model, str(run_new_ckpt))
    infer_dataset(model_new, tok_new, internal, out_dir / f"internal_{target_tag}.jsonl", f"internal_{target_tag}")
    infer_dataset(model_new, tok_new, external, out_dir / f"external_{target_tag}_manual.jsonl", f"external_{target_tag}_manual")
    del model_new
    torch.cuda.empty_cache()

    int8 = summarize(read_jsonl(out_dir / "internal_run8.jsonl"))
    int_new = summarize(read_jsonl(out_dir / f"internal_{target_tag}.jsonl"))

    # Dual goal adaptation:
    # External is manual-only for this run, so external overlap gate is marked pending.
    len_gate = int_new.get("len_ratio_mean", 999) <= int8.get("len_ratio_mean", 0) * 1.1 if int8 and int_new else False
    decision = {
        "external_overlap_gate": "manual_review_required",
        "len_ratio_gate_internal": len_gate,
        "recommendation": "pending_manual_external",
    }

    report = {
        "checkpoints": {"run8": str(run8_ckpt), target_tag: str(run_new_ckpt)},
        "internal_auto": {"run8": int8, target_tag: int_new},
        "gates": decision,
        "notes": [
            f"External dataset is evaluated by manual review only in {target_tag}.",
            "Generation is deterministic (do_sample=False, temperature=0, top_p=1).",
            "max_new_tokens is capped at 384 to suppress over-long outputs.",
        ],
    }
    (out_dir / f"run8_vs_{target_tag}_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append(f"# run8 vs {target_tag} 评测结果")
    md.append("")
    md.append("## 内部集自动指标")
    md.append("")
    md.append("| 模型 | overlap_mean | len_ratio_mean | repeat_mean | EM |")
    md.append("|---|---:|---:|---:|---:|")
    for name, obj in [("run8", int8), (target_tag, int_new)]:
        md.append(
            f"| {name} | {obj.get('overlap_mean',0):.4f} | {obj.get('len_ratio_mean',0):.4f} | {obj.get('repeat_mean',0):.4f} | {obj.get('exact_match_rate',0):.4f} |"
        )
    md.append("")
    md.append("## 判定")
    md.append(f"- 外部集主目标（overlap不下降）：手工评测中，待人工结论。")
    md.append(f"- 内部集长度约束（{target_tag} len_ratio <= run8 * 1.1）：{'通过' if len_gate else '未通过'}")
    md.append("")
    md.append("## 外部集人工评测包")
    md.append("- external_run8_manual.jsonl")
    md.append(f"- external_{target_tag}_manual.jsonl")
    md.append(f"- manual_external_run8_vs_{target_tag}.csv")
    md.append(f"- manual_external_run8_vs_{target_tag}_rubric.md")
    (out_dir / f"run8_vs_{target_tag}_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    run8_ext = read_jsonl(out_dir / "external_run8_manual.jsonl")
    run_new_ext = read_jsonl(out_dir / f"external_{target_tag}_manual.jsonl")
    write_manual_csv(run8_ext, run_new_ext, out_dir / f"manual_external_run8_vs_{target_tag}.csv", target_tag)

    rubric = []
    rubric.append(f"# 外部集人工评测规则（run8 vs {target_tag}）")
    rubric.append("")
    rubric.append(f"每条样本分别给 run8 与 {target_tag} 打分，每项 0-2 分：")
    rubric.append("- history: 是否忠实于病史与问题，不遗漏关键事实")
    rubric.append("- hallucination: 是否存在编造、越权诊断、无依据新增")
    rubric.append("- structure: 诊断/处方/用法表达是否清晰、规范、可执行")
    rubric.append("")
    rubric.append(f"最终 winner 填写 run8 / {target_tag} / tie。")
    (out_dir / f"manual_external_run8_vs_{target_tag}_rubric.md").write_text("\n".join(rubric) + "\n", encoding="utf-8")

    (out_dir / "status.txt").write_text("done", encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
