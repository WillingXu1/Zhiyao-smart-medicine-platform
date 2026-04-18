#!/usr/bin/env python3
import argparse
import concurrent.futures
import csv
import json
import os
import shlex
import subprocess
import time
from pathlib import Path


def run_cmd(cmd: str, log_path: Path, dry_run: bool = False) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print("[DRY_RUN]", cmd)
        return 0
    with log_path.open("a", encoding="utf-8") as f:
        f.write("\n==== CMD ====\n")
        f.write(cmd + "\n")
        f.flush()
        proc = subprocess.run(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
    return proc.returncode


def latest_version_dir(output_dir: Path) -> Path:
    candidates = sorted(output_dir.glob("v0-*"))
    if not candidates:
        raise RuntimeError(f"No version dir found under {output_dir}")
    return candidates[-1]


def best_checkpoint(version_dir: Path) -> Path:
    log_file = version_dir / "logging.jsonl"
    if log_file.exists():
        for ln in log_file.read_text(encoding="utf-8", errors="ignore").splitlines()[::-1]:
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            if "best_model_checkpoint" in obj:
                return Path(obj["best_model_checkpoint"])
    ckpts = sorted(version_dir.glob("checkpoint-*"), key=lambda p: p.name)
    if not ckpts:
        raise RuntimeError(f"No checkpoints under {version_dir}")
    return ckpts[-1]


def load_metrics(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def result_from_metrics(name: str, family: str, size_b, status: str, best_ckpt: str, metric_obj: dict):
    ib = metric_obj["internal"]["new"]
    eb = metric_obj["external"]["new"]
    score = 0.7 * ib.get("f1", 0.0) + 0.3 * eb.get("f1", 0.0)
    return {
        "model": name,
        "family": family,
        "size_b": size_b,
        "status": status,
        "best_ckpt": best_ckpt,
        "internal_f1": ib.get("f1", 0.0),
        "internal_rouge_l": ib.get("rouge_l", 0.0),
        "external_f1": eb.get("f1", 0.0),
        "external_rouge_l": eb.get("rouge_l", 0.0),
        "weighted_score": score,
    }


def to_float_size(size_b) -> float:
    try:
        return float(size_b)
    except Exception:
        return 999.0


def with_gpu_prefix(cmd: str, gpu_id: str | None) -> str:
    if gpu_id is None or str(gpu_id).strip() == "":
        return cmd
    return f"CUDA_VISIBLE_DEVICES={shlex.quote(str(gpu_id))} {cmd}"


def local_model_has_weights(model_path: Path) -> bool:
    if not model_path.exists() or not model_path.is_dir():
        return False
    candidates = [
        "model.safetensors",
        "model.safetensors.index.json",
        "pytorch_model.bin",
        "pytorch_model.bin.index.json",
    ]
    for c in candidates:
        if (model_path / c).exists():
            return True
    return False


def wait_local_model_ready(model_id: str, wait_seconds: int, poll_seconds: int, log_path: Path | None = None) -> bool:
    p = Path(model_id)
    if not p.is_absolute():
        return True
    if wait_seconds <= 0:
        return local_model_has_weights(p)
    deadline = time.time() + wait_seconds
    while time.time() <= deadline:
        if local_model_has_weights(p):
            return True
        if log_path is not None:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(f"[WAIT_MODEL] waiting for local model files: {model_id}\n")
        time.sleep(max(1, poll_seconds))
    return local_model_has_weights(p)


def run_one_model(m: dict, args, reuse_map: dict, runs_dir: Path, eval_dir: Path, logs_dir: Path, gpu_id: str | None = None):
    name = m["name"]
    model_id = m["model_id"]

    if name in reuse_map:
        rm = reuse_map[name]
        metric_json = Path(rm["metrics_json"])
        metric_obj = load_metrics(metric_json)
        if not metric_obj:
            return {
                "model": name,
                "family": rm.get("family", m.get("family", "")),
                "size_b": rm.get("size_b", m.get("size_b", "")),
                "status": "reused_metric_missing",
                "best_ckpt": rm.get("best_ckpt", ""),
                "metrics_json": str(metric_json),
            }
        return result_from_metrics(
            name=name,
            family=rm.get("family", m.get("family", "")),
            size_b=rm.get("size_b", m.get("size_b", "")),
            status=rm.get("status", "ok_reused"),
            best_ckpt=rm.get("best_ckpt", ""),
            metric_obj=metric_obj,
        )

    run_out = runs_dir / name
    run_out.mkdir(parents=True, exist_ok=True)
    train_log = logs_dir / f"{name}_train.log"

    if not wait_local_model_ready(model_id, args.wait_model_ready_seconds, args.wait_model_poll_seconds, train_log):
        return {
            "model": name,
            "status": "model_not_ready",
            "model_id": model_id,
        }

    train_cmd = (
        f"conda run -n {shlex.quote(args.conda_env)} swift sft "
        f"--model {shlex.quote(model_id)} "
        f"--dataset {shlex.quote(args.dataset)} "
        f"--val_dataset {shlex.quote(args.val_dataset)} "
        f"--split_dataset_ratio 0 "
        f"--output_dir {shlex.quote(str(run_out))} "
        f"--per_device_train_batch_size {args.batch_size} "
        f"--gradient_accumulation_steps {args.grad_acc} "
        f"--num_train_epochs {args.epochs} "
        f"--learning_rate {args.learning_rate} "
        f"--lr_scheduler_type cosine "
        f"--warmup_ratio 0.1 "
        f"--weight_decay 0.1 "
        f"--max_length {args.max_length} "
        f"--fp16 true --bf16 false --gradient_checkpointing true "
        f"--eval_steps 10 --save_steps 10 --save_total_limit 3 "
        f"--load_best_model_at_end true --metric_for_best_model loss --greater_is_better false "
        f"--logging_steps 5 --seed {args.seed} "
        f"--tuner_backend peft --tuner_type lora "
        f"--lora_rank 16 --lora_alpha 32 --lora_dropout 0.05 --target_modules all-linear"
    )
    code = run_cmd(with_gpu_prefix(train_cmd, gpu_id), train_log, args.dry_run)
    if code != 0:
        return {"model": name, "status": "train_failed", "return_code": code}

    if args.dry_run:
        return {"model": name, "status": "dry_run"}

    try:
        version_dir = latest_version_dir(run_out)
        best_ckpt = best_checkpoint(version_dir)
    except Exception as e:
        return {"model": name, "status": "checkpoint_not_found", "error": str(e)}

    model_eval_dir = eval_dir / name
    model_eval_dir.mkdir(parents=True, exist_ok=True)
    infer_log = logs_dir / f"{name}_infer.log"
    infer_cmd = (
        f"conda run -n {shlex.quote(args.conda_env)} python eval/evaluate_base_vs_adapter.py "
        f"--base-model {shlex.quote(args.base_compare_model)} "
        f"--adapter {shlex.quote(str(best_ckpt))} "
        f"--adapter-tag {shlex.quote(name)} "
        f"--internal {shlex.quote(args.internal)} "
        f"--external {shlex.quote(args.external)} "
        f"--out-dir {shlex.quote(str(model_eval_dir))} "
        f"--max-new-tokens {args.max_new_tokens}"
    )
    code = run_cmd(with_gpu_prefix(infer_cmd, gpu_id), infer_log, args.dry_run)
    if code != 0:
        return {"model": name, "status": "infer_failed", "return_code": code, "best_ckpt": str(best_ckpt)}

    metric_log = logs_dir / f"{name}_metric.log"
    metric_json = model_eval_dir / f"extended_metrics_base_vs_{name}.json"
    metric_md = model_eval_dir / f"extended_metrics_base_vs_{name}.md"
    metric_cmd = (
        f"conda run -n {shlex.quote(args.conda_env)} python eval/evaluate_metrics_extended.py "
        f"--internal-base {shlex.quote(str(model_eval_dir / 'internal20_base.jsonl'))} "
        f"--internal-new {shlex.quote(str(model_eval_dir / f'internal20_{name}.jsonl'))} "
        f"--external-base {shlex.quote(str(model_eval_dir / 'external23_base.jsonl'))} "
        f"--external-new {shlex.quote(str(model_eval_dir / f'external23_{name}.jsonl'))} "
        f"--out-json {shlex.quote(str(metric_json))} "
        f"--out-md {shlex.quote(str(metric_md))} "
        f"--internal-base-tag internal20_base "
        f"--internal-new-tag internal20_{shlex.quote(name)} "
        f"--external-base-tag external23_base "
        f"--external-new-tag external23_{shlex.quote(name)}"
    )
    code = run_cmd(with_gpu_prefix(metric_cmd, gpu_id), metric_log, args.dry_run)
    if code != 0:
        return {"model": name, "status": "metric_failed", "return_code": code, "best_ckpt": str(best_ckpt)}

    metric_obj = load_metrics(metric_json)
    if not metric_obj:
        return {"model": name, "status": "metric_missing", "best_ckpt": str(best_ckpt)}

    return result_from_metrics(
        name=name,
        family=m.get("family", ""),
        size_b=m.get("size_b", ""),
        status="ok",
        best_ckpt=str(best_ckpt),
        metric_obj=metric_obj,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LoRA ablation on 3090 and summarize results")
    parser.add_argument("--models-file", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--val-dataset", required=True)
    parser.add_argument("--internal", required=True)
    parser.add_argument("--external", required=True)
    parser.add_argument("--base-compare-model", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--conda-env", default="qwen_sft")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-acc", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--reuse-results-json", default="")
    parser.add_argument("--parallel-1p5b-first", action="store_true")
    parser.add_argument("--first-phase-max-size-b", type=float, default=1.5)
    parser.add_argument("--parallel-gpus", default="0,1")
    parser.add_argument("--wait-model-ready-seconds", type=int, default=0)
    parser.add_argument("--wait-model-poll-seconds", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    runs_dir = root / "runs"
    eval_dir = root / "eval"
    logs_dir = root / "logs"
    summary_json = root / "ablation_summary.json"
    summary_csv = root / "ablation_summary.csv"

    models = json.loads(Path(args.models_file).read_text(encoding="utf-8")).get("models", [])
    reuse_map = {}
    if args.reuse_results_json:
        reuse_map = json.loads(Path(args.reuse_results_json).read_text(encoding="utf-8"))
    results = []

    reusable = [m for m in models if m.get("name") in reuse_map]
    trainable = [m for m in models if m.get("name") not in reuse_map]

    for m in reusable:
        results.append(run_one_model(m, args, reuse_map, runs_dir, eval_dir, logs_dir, gpu_id=None))

    if args.parallel_1p5b_first:
        gpu_list = [g.strip() for g in args.parallel_gpus.split(",") if g.strip()]
        if not gpu_list:
            gpu_list = ["0", "1"]
        first_phase = [m for m in trainable if to_float_size(m.get("size_b")) <= args.first_phase_max_size_b]
        second_phase = [m for m in trainable if to_float_size(m.get("size_b")) > args.first_phase_max_size_b]

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(first_phase), len(gpu_list)) or 1) as ex:
            futs = []
            for i, m in enumerate(first_phase):
                futs.append(
                    ex.submit(
                        run_one_model,
                        m,
                        args,
                        reuse_map,
                        runs_dir,
                        eval_dir,
                        logs_dir,
                        gpu_list[i % len(gpu_list)],
                    )
                )
            for f in futs:
                results.append(f.result())

        for m in second_phase:
            # Run larger models sequentially after 1.5B phase to avoid VRAM contention.
            results.append(run_one_model(m, args, reuse_map, runs_dir, eval_dir, logs_dir, gpu_list[0]))
    else:
        for m in trainable:
            results.append(run_one_model(m, args, reuse_map, runs_dir, eval_dir, logs_dir, gpu_id=None))

    ok_rows = [
        r
        for r in results
        if isinstance(r.get("status"), str) and r.get("status").startswith("ok")
    ]
    ok_rows.sort(key=lambda x: x.get("weighted_score", 0.0), reverse=True)

    out = {
        "config": {
            "dataset": args.dataset,
            "val_dataset": args.val_dataset,
            "internal": args.internal,
            "external": args.external,
            "base_compare_model": args.base_compare_model,
            "seed": args.seed,
            "learning_rate": args.learning_rate,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "grad_acc": args.grad_acc,
            "max_length": args.max_length,
        },
        "results": results,
        "ranking": ok_rows,
    }
    summary_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "model",
            "family",
            "size_b",
            "status",
            "internal_f1",
            "internal_rouge_l",
            "external_f1",
            "external_rouge_l",
            "weighted_score",
            "best_ckpt",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fields})

    print(summary_json)
    print(summary_csv)
    if ok_rows:
        print("TOP_MODEL", ok_rows[0]["model"], ok_rows[0]["weighted_score"])


if __name__ == "__main__":
    main()
