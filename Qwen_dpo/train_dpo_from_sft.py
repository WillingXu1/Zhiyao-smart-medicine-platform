#!/usr/bin/env python3
import argparse
import inspect
import json
import os
from pathlib import Path

import torch
from datasets import load_dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOConfig, DPOTrainer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train DPO from an SFT adapter checkpoint.")
    p.add_argument("--base-model", required=True, help="Base model path, e.g. Qwen2.5-3B-Instruct")
    p.add_argument("--sft-adapter", required=True, help="SFT adapter checkpoint path")
    p.add_argument("--train-jsonl", required=True, help="DPO train jsonl with prompt/chosen/rejected")
    p.add_argument("--eval-jsonl", required=True, help="DPO eval jsonl with prompt/chosen/rejected")
    p.add_argument("--output-dir", required=True, help="Output directory for DPO run")

    p.add_argument("--num-train-epochs", type=float, default=2.0)
    p.add_argument("--per-device-train-batch-size", type=int, default=1)
    p.add_argument("--per-device-eval-batch-size", type=int, default=1)
    p.add_argument("--gradient-accumulation-steps", type=int, default=8)
    p.add_argument("--learning-rate", type=float, default=5e-6)
    p.add_argument("--weight-decay", type=float, default=0.0)
    p.add_argument("--warmup-ratio", type=float, default=0.03)
    p.add_argument("--beta", type=float, default=0.1)
    p.add_argument("--max-prompt-length", type=int, default=768)
    p.add_argument("--max-length", type=int, default=1024)
    p.add_argument("--logging-steps", type=int, default=5)
    p.add_argument("--eval-steps", type=int, default=50)
    p.add_argument("--save-steps", type=int, default=50)
    p.add_argument("--save-total-limit", type=int, default=3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--gradient-checkpointing", action="store_true")
    p.add_argument("--no-gradient-checkpointing", action="store_true")
    return p.parse_args()


def pick_precision() -> dict:
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return {"bf16": True, "fp16": False}
    if torch.cuda.is_available():
        return {"bf16": False, "fp16": True}
    return {"bf16": False, "fp16": False}


def main() -> None:
    args = parse_args()

    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", "-1"))
    is_distributed = world_size > 1

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ds_train = load_dataset("json", data_files=args.train_jsonl, split="train")
    ds_eval = load_dataset("json", data_files=args.eval_jsonl, split="train")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float16
    # For torchrun/DDP, avoid device_map='auto' so each rank owns its local GPU.
    # Keep auto mapping for the single-process fallback path.
    model_kwargs = {
        "torch_dtype": dtype if torch.cuda.is_available() else torch.float32,
        "trust_remote_code": True,
    }
    if is_distributed:
        model_kwargs["device_map"] = None
    else:
        model_kwargs["device_map"] = "auto"

    base_model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)
    model = PeftModel.from_pretrained(base_model, args.sft_adapter, is_trainable=True)

    use_gc = True
    if args.no_gradient_checkpointing:
        use_gc = False
    elif args.gradient_checkpointing:
        use_gc = True

    if use_gc:
        # Needed to avoid cache/checkpointing incompatibility and reduce VRAM.
        model.config.use_cache = False

    precision = pick_precision()
    cfg_kwargs = dict(
        output_dir=str(out_dir),
        num_train_epochs=args.num_train_epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        logging_steps=args.logging_steps,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_strategy="steps",
        save_steps=args.save_steps,
        save_total_limit=args.save_total_limit,
        beta=args.beta,
        max_length=args.max_length,
        remove_unused_columns=False,
        gradient_checkpointing=use_gc,
        ddp_find_unused_parameters=False,
        seed=args.seed,
        report_to=["none"],
    )

    # TRL versions differ in whether DPOConfig exposes max_prompt_length.
    dpo_config_params = set(inspect.signature(DPOConfig.__init__).parameters.keys())
    if "max_prompt_length" in dpo_config_params:
        cfg_kwargs["max_prompt_length"] = args.max_prompt_length

    cfg = DPOConfig(
        **cfg_kwargs,
        **precision,
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,
        args=cfg,
        train_dataset=ds_train,
        eval_dataset=ds_eval,
        processing_class=tokenizer,
    )

    train_result = trainer.train()

    final_dir = out_dir / "dpo_final"
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))

    summary = {
        "base_model": args.base_model,
        "sft_adapter": args.sft_adapter,
        "train_jsonl": args.train_jsonl,
        "eval_jsonl": args.eval_jsonl,
        "output_dir": str(out_dir),
        "final_model_dir": str(final_dir),
        "train_metrics": dict(train_result.metrics),
        "dpo_config": {
            "num_train_epochs": args.num_train_epochs,
            "per_device_train_batch_size": args.per_device_train_batch_size,
            "gradient_accumulation_steps": args.gradient_accumulation_steps,
            "learning_rate": args.learning_rate,
            "beta": args.beta,
            "max_prompt_length": args.max_prompt_length,
            "max_length": args.max_length,
        },
        "runtime": {
            "world_size": world_size,
            "local_rank": local_rank,
            "distributed": is_distributed,
            "gradient_checkpointing": use_gc,
        },
    }
    (out_dir / "dpo_train_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
