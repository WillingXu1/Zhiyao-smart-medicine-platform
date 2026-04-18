#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_dataset(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(tokenizer, messages):
    msgs = []
    for m in messages:
        role = m.get("role")
        if role in {"system", "user"}:
            msgs.append({"role": role, "content": m.get("content", "")})
    return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def generate_once(model, tokenizer, prompt: str, max_new_tokens: int):
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


def run_eval(model, tokenizer, dataset, out_path: str, max_new_tokens: int, tag: str):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fw:
        for i, item in enumerate(dataset, start=1):
            messages = item.get("messages", [])
            prompt = build_prompt(tokenizer, messages)
            pred = generate_once(model, tokenizer, prompt, max_new_tokens=max_new_tokens)

            label = ""
            for m in messages:
                if m.get("role") == "assistant":
                    label = m.get("content", "")
                    break

            fw.write(
                json.dumps(
                    {
                        "response": pred,
                        "labels": label,
                        "messages": messages,
                        "tag": tag,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

            if i % 5 == 0 or i == len(dataset):
                print(f"[{tag}] {i}/{len(dataset)}")


def load_base_model(model_path: str):
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return model, tokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--adapter-tag", required=True, help="e.g. run8")
    parser.add_argument("--internal", required=True)
    parser.add_argument("--external", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    args = parser.parse_args()

    internal = load_dataset(args.internal)
    external = load_dataset(args.external)

    print("Loading base model...")
    base_model, tokenizer = load_base_model(args.base_model)
    run_eval(
        base_model,
        tokenizer,
        internal,
        os.path.join(args.out_dir, "internal20_base.jsonl"),
        args.max_new_tokens,
        "internal20_base",
    )
    run_eval(
        base_model,
        tokenizer,
        external,
        os.path.join(args.out_dir, "external23_base.jsonl"),
        args.max_new_tokens,
        "external23_base",
    )

    del base_model
    torch.cuda.empty_cache()

    print("Loading adapter model...")
    sft_base, tokenizer2 = load_base_model(args.base_model)
    sft_model = PeftModel.from_pretrained(sft_base, args.adapter)
    sft_model.eval()

    run_eval(
        sft_model,
        tokenizer2,
        internal,
        os.path.join(args.out_dir, f"internal20_{args.adapter_tag}.jsonl"),
        args.max_new_tokens,
        f"internal20_{args.adapter_tag}",
    )
    run_eval(
        sft_model,
        tokenizer2,
        external,
        os.path.join(args.out_dir, f"external23_{args.adapter_tag}.jsonl"),
        args.max_new_tokens,
        f"external23_{args.adapter_tag}",
    )

    print("done")


if __name__ == "__main__":
    main()
