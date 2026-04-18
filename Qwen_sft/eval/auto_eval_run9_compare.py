#!/usr/bin/env python3
import json
import re
import time
from pathlib import Path
from difflib import SequenceMatcher as S

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


BASE_MODEL = "/mnt/public/zxs/course/SFT_qwen/Qwen2.5-1.5B-Instruct"
RUN8_DIR = Path("/mnt/public/zxs/course/SFT_qwen/qwen2.5-1.5b_medical_lora_run8_aug_val20_r1/v0-20260328-142135")
RUN9_DIR = Path("/mnt/public/zxs/course/SFT_qwen/qwen2.5-1.5b_medical_lora_run9_mix_50_40_10_r1/v0-20260328-180200")
INTERNAL = Path("/mnt/public/zxs/course/SFT_qwen/datasets/json/dataset_internal_test_data20_v2.json")
EXTERNAL = Path("/mnt/public/zxs/course/SFT_qwen/datasets/json/dataset_external_test_data2_v2.json")
RUN7_INTERNAL = Path("/mnt/public/zxs/course/SFT_qwen/output/eval_run7/internal20_run7.jsonl")
RUN7_EXTERNAL = Path("/mnt/public/zxs/course/SFT_qwen/output/eval_run7/external23_run7.jsonl")
OUT_DIR = Path("/mnt/public/zxs/course/SFT_qwen/output/eval_run9_compare")


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


def wait_train_finish(logging_path: Path, timeout_sec: int = 8 * 3600):
    start = time.time()
    while True:
        if logging_path.exists():
            txt = logging_path.read_text(encoding="utf-8", errors="ignore")
            if '"train_runtime"' in txt:
                return True
        if time.time() - start > timeout_sec:
            return False
        time.sleep(20)


def get_best_ckpt(run_dir: Path) -> Path:
    log_path = run_dir / "logging.jsonl"
    best = None
    if log_path.exists():
        for ln in log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[::-1]:
            if not ln.strip():
                continue
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            if "best_model_checkpoint" in obj:
                best = obj["best_model_checkpoint"]
                break
    if best:
        return Path(best)

    cks = sorted(run_dir.glob("checkpoint-*"), key=lambda p: p.name)
    if not cks:
        raise RuntimeError(f"No checkpoint found in {run_dir}")
    return cks[-1]


def build_prompt(tokenizer, messages):
    msgs = []
    for m in messages:
        if m.get("role") in {"system", "user"}:
            msgs.append({"role": m.get("role"), "content": m.get("content", "")})
    return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def load_model(adapter: Path):
    tok = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
    )
    model = PeftModel.from_pretrained(base, str(adapter))
    model.eval()
    return model, tok


def infer_dataset(model, tok, dataset, out_path: Path, tag: str, max_new_tokens: int = 512):
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
                    eos_token_id=tok.eos_token_id,
                    pad_token_id=tok.eos_token_id,
                )
            gen_ids = out[0][inputs["input_ids"].shape[1]:]
            pred = tok.decode(gen_ids, skip_special_tokens=True).strip()
            label = ""
            for m in messages:
                if m.get("role") == "assistant":
                    label = m.get("content", "")
                    break
            rec = {"response": pred, "labels": label, "messages": messages, "tag": tag}
            fw.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if i % 5 == 0 or i == len(dataset):
                print(f"[{tag}] {i}/{len(dataset)}")


def repeat_ratio(text: str) -> float:
    toks = re.findall(r"\S+", text)
    if len(toks) < 3:
        return 0.0
    bi = [" ".join(toks[i:i+2]) for i in range(len(toks)-1)]
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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ok = wait_train_finish(RUN9_DIR / "logging.jsonl")
    if not ok:
        (OUT_DIR / "run9_compare_status.txt").write_text("timeout_waiting_run9", encoding="utf-8")
        return

    run8_ckpt = get_best_ckpt(RUN8_DIR)
    run9_ckpt = get_best_ckpt(RUN9_DIR)

    internal = read_json(INTERNAL)
    external = read_json(EXTERNAL)

    print("Evaluating run8 adapter:", run8_ckpt)
    model8, tok8 = load_model(run8_ckpt)
    infer_dataset(model8, tok8, internal, OUT_DIR / "internal20_run8.jsonl", "internal20_run8")
    infer_dataset(model8, tok8, external, OUT_DIR / "external23_run8.jsonl", "external23_run8")
    del model8
    torch.cuda.empty_cache()

    print("Evaluating run9 adapter:", run9_ckpt)
    model9, tok9 = load_model(run9_ckpt)
    infer_dataset(model9, tok9, internal, OUT_DIR / "internal20_run9.jsonl", "internal20_run9")
    infer_dataset(model9, tok9, external, OUT_DIR / "external23_run9.jsonl", "external23_run9")
    del model9
    torch.cuda.empty_cache()

    run7_int = summarize(read_jsonl(RUN7_INTERNAL))
    run7_ext = summarize(read_jsonl(RUN7_EXTERNAL))
    run8_int = summarize(read_jsonl(OUT_DIR / "internal20_run8.jsonl"))
    run8_ext = summarize(read_jsonl(OUT_DIR / "external23_run8.jsonl"))
    run9_int = summarize(read_jsonl(OUT_DIR / "internal20_run9.jsonl"))
    run9_ext = summarize(read_jsonl(OUT_DIR / "external23_run9.jsonl"))

    report = {
        "checkpoints": {"run8": str(run8_ckpt), "run9": str(run9_ckpt)},
        "internal20": {"run7": run7_int, "run8": run8_int, "run9": run9_int},
        "external23": {"run7": run7_ext, "run8": run8_ext, "run9": run9_ext},
    }
    (OUT_DIR / "run7_run8_run9_compare.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = ["# run7 vs run8 vs run9 自动评测对比", "", "## 内部集 internal20", "", "| 模型 | overlap_mean | len_ratio_mean | repeat_mean | EM |", "|---|---:|---:|---:|---:|"]
    for name, obj in [("run7", run7_int), ("run8", run8_int), ("run9", run9_int)]:
        md.append(f"| {name} | {obj.get('overlap_mean',0):.4f} | {obj.get('len_ratio_mean',0):.4f} | {obj.get('repeat_mean',0):.4f} | {obj.get('exact_match_rate',0):.4f} |")
    md += ["", "## 外部集 external23", "", "| 模型 | overlap_mean | len_ratio_mean | repeat_mean | EM |", "|---|---:|---:|---:|---:|"]
    for name, obj in [("run7", run7_ext), ("run8", run8_ext), ("run9", run9_ext)]:
        md.append(f"| {name} | {obj.get('overlap_mean',0):.4f} | {obj.get('len_ratio_mean',0):.4f} | {obj.get('repeat_mean',0):.4f} | {obj.get('exact_match_rate',0):.4f} |")
    (OUT_DIR / "run7_run8_run9_compare.md").write_text("\n".join(md), encoding="utf-8")

    (OUT_DIR / "run9_compare_status.txt").write_text("done", encoding="utf-8")


if __name__ == "__main__":
    main()
