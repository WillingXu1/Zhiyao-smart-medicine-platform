#!/usr/bin/env python3
import argparse
import json
import math
import random
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return math.nan
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def load_prompts(dataset_path: str, limit: int) -> list[list[dict[str, str]]]:
    data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    prompts = []
    for item in data:
        msgs = []
        for m in item.get("messages", []):
            if m.get("role") in {"system", "user"}:
                msgs.append({"role": m["role"], "content": m.get("content", "")})
        if msgs:
            prompts.append(msgs)
    if not prompts:
        raise RuntimeError("No prompts found in dataset")
    return prompts[:limit]


def wait_health(base_url: str, timeout_sec: int) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            r = requests.get(f"{base_url}/health", timeout=3)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(f"Service not ready: {base_url}")


def run_one_scenario(
    base_url: str,
    model: str,
    prompts: list[list[dict[str, str]]],
    concurrency: int,
    total_requests: int,
    max_tokens: int,
    timeout_sec: int,
) -> dict[str, Any]:
    url = f"{base_url}/v1/chat/completions"

    counter = {"idx": 0}
    counter_lock = threading.Lock()

    latencies = []
    status_codes = []
    errors = []
    completion_lens = []

    def worker() -> list[tuple[float, int, str | None, int]]:
        local_rows = []
        while True:
            with counter_lock:
                if counter["idx"] >= total_requests:
                    break
                i = counter["idx"]
                counter["idx"] += 1

            messages = prompts[i % len(prompts)]
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.0,
            }
            t0 = time.time()
            err = None
            code = -1
            out_len = 0
            try:
                r = requests.post(url, json=payload, timeout=timeout_sec)
                code = r.status_code
                if code == 200:
                    content = (
                        r.json()
                        .get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    out_len = len(content)
                else:
                    err = r.text[:200]
            except Exception as exc:
                err = str(exc)

            latency = time.time() - t0
            local_rows.append((latency, code, err, out_len))
        return local_rows

    t_start = time.time()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(worker) for _ in range(concurrency)]
        for fut in as_completed(futures):
            rows = fut.result()
            for latency, code, err, out_len in rows:
                latencies.append(latency)
                status_codes.append(code)
                if err is not None:
                    errors.append(err)
                completion_lens.append(out_len)
    elapsed = time.time() - t_start

    ok = sum(1 for c in status_codes if c == 200)
    fail = len(status_codes) - ok
    err_rate = (fail / len(status_codes)) if status_codes else 1.0

    sorted_lat = sorted(latencies)
    p50 = percentile(sorted_lat, 50)
    p95 = percentile(sorted_lat, 95)
    p99 = percentile(sorted_lat, 99)

    result = {
        "concurrency": concurrency,
        "total_requests": len(status_codes),
        "success": ok,
        "failed": fail,
        "error_rate": err_rate,
        "elapsed_sec": elapsed,
        "qps": (ok / elapsed) if elapsed > 0 else 0.0,
        "latency": {
            "mean_sec": statistics.mean(latencies) if latencies else math.nan,
            "p50_sec": p50,
            "p95_sec": p95,
            "p99_sec": p99,
            "max_sec": max(latencies) if latencies else math.nan,
        },
        "avg_completion_chars": (
            statistics.mean(completion_lens) if completion_lens else 0.0
        ),
        "non_200_samples": errors[:5],
    }
    return result


def make_markdown(report: dict[str, Any]) -> str:
    lines = []
    lines.append(f"# Load Test Report: {report['model']}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"- base_url: {report['base_url']} | max_tokens: {report['max_tokens']} | prompts: {report['prompt_count']}"
    )
    lines.append("")
    lines.append("## Scenarios")
    lines.append("")
    lines.append("| Concurrency | Requests | QPS | P95(s) | P99(s) | Error Rate |")
    lines.append("|---:|---:|---:|---:|---:|---:|")
    for r in report["results"]:
        lines.append(
            "| {concurrency} | {total_requests} | {qps:.3f} | {p95:.3f} | {p99:.3f} | {err:.2%} |".format(
                concurrency=r["concurrency"],
                total_requests=r["total_requests"],
                qps=r["qps"],
                p95=r["latency"]["p95_sec"],
                p99=r["latency"]["p99_sec"],
                err=r["error_rate"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--prompt-limit", type=int, default=20)
    parser.add_argument("--concurrency", required=True, help="comma-separated, e.g. 1,2,4,8")
    parser.add_argument("--requests-per-concurrency", type=int, default=40)
    parser.add_argument("--max-tokens", type=int, default=384)
    parser.add_argument("--timeout-sec", type=int, default=120)
    parser.add_argument("--health-timeout-sec", type=int, default=300)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    prompts = load_prompts(args.dataset, args.prompt_limit)
    wait_health(args.base_url, args.health_timeout_sec)

    conc_levels = [int(x.strip()) for x in args.concurrency.split(",") if x.strip()]
    results = []
    for c in conc_levels:
        print(f"Running scenario concurrency={c}")
        r = run_one_scenario(
            base_url=args.base_url,
            model=args.model,
            prompts=prompts,
            concurrency=c,
            total_requests=args.requests_per_concurrency,
            max_tokens=args.max_tokens,
            timeout_sec=args.timeout_sec,
        )
        results.append(r)

    report = {
        "model": args.model,
        "base_url": args.base_url,
        "dataset": args.dataset,
        "prompt_count": len(prompts),
        "max_tokens": args.max_tokens,
        "results": results,
        "generated_at": int(time.time()),
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    Path(args.out_md).write_text(make_markdown(report), encoding="utf-8")

    print(f"saved: {args.out_json}")
    print(f"saved: {args.out_md}")


if __name__ == "__main__":
    main()
