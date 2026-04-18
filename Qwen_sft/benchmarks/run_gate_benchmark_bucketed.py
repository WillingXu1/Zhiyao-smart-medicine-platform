#!/usr/bin/env python3
import argparse
import json
import math
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests


def percentile(sorted_values: list[float], p: float) -> float | None:
    if not sorted_values:
        return None
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)


def stat_dict(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {
            "mean_sec": None,
            "p50_sec": None,
            "p95_sec": None,
            "p99_sec": None,
            "max_sec": None,
        }
    s = sorted(values)
    return {
        "mean_sec": statistics.mean(values),
        "p50_sec": percentile(s, 50),
        "p95_sec": percentile(s, 95),
        "p99_sec": percentile(s, 99),
        "max_sec": max(values),
    }


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


def extract_prompts(dataset_path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    prompts = []
    for item in data:
        msgs = []
        length_chars = 0
        for m in item.get("messages", []):
            role = m.get("role")
            if role in {"system", "user"}:
                content = m.get("content", "")
                msgs.append({"role": role, "content": content})
                length_chars += len(content)
        if msgs:
            prompts.append({"messages": msgs, "length_chars": length_chars})
    if not prompts:
        raise RuntimeError(f"No prompts found in {dataset_path}")
    return prompts


def bucketize(prompts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    lens = sorted(x["length_chars"] for x in prompts)
    i1 = max(0, int(len(lens) * 0.33) - 1)
    i2 = max(0, int(len(lens) * 0.66) - 1)
    t1 = lens[i1]
    t2 = lens[i2]

    out = {"short": [], "medium": [], "long": []}
    for p in prompts:
        n = p["length_chars"]
        if n <= t1:
            out["short"].append(p)
        elif n <= t2:
            out["medium"].append(p)
        else:
            out["long"].append(p)

    for b in ["short", "medium", "long"]:
        if not out[b]:
            out[b] = prompts[:]
    return out


def run_requests(
    *,
    base_url: str,
    model: str,
    prompts: list[dict[str, Any]],
    total_requests: int,
    concurrency: int,
    max_tokens: int,
    timeout_sec: int,
) -> dict[str, Any]:
    url = f"{base_url}/v1/chat/completions"

    idx = {"v": 0}
    idx_lock = threading.Lock()

    e2e_latencies: list[float] = []
    ttfts: list[float] = []
    codes: list[int] = []
    errors: list[str] = []
    completion_tokens_all: list[int] = []

    def worker() -> list[tuple[float, float | None, int, str | None, int]]:
        rows = []
        while True:
            with idx_lock:
                if idx["v"] >= total_requests:
                    break
                i = idx["v"]
                idx["v"] += 1

            sample = prompts[i % len(prompts)]
            payload = {
                "model": model,
                "messages": sample["messages"],
                "max_tokens": max_tokens,
                "temperature": 0.0,
                "stream": True,
                "stream_options": {"include_usage": True},
            }

            started = time.time()
            first_token_ts = None
            code = -1
            err = None
            completion_tokens = 0

            try:
                r = requests.post(url, json=payload, timeout=timeout_sec, stream=True)
                code = r.status_code
                if code == 200:
                    for raw in r.iter_lines(decode_unicode=True):
                        if not raw:
                            continue
                        if not raw.startswith("data:"):
                            continue
                        data = raw[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue

                        choices = chunk.get("choices") or []
                        if choices:
                            delta = choices[0].get("delta") or {}
                            content_piece = delta.get("content")
                            if content_piece and first_token_ts is None:
                                first_token_ts = time.time()

                        usage = chunk.get("usage")
                        if usage and isinstance(usage, dict):
                            completion_tokens = int(usage.get("completion_tokens") or 0)
                else:
                    err = (r.text or "")[:300]
            except Exception as exc:
                err = str(exc)

            e2e = time.time() - started
            ttft = (first_token_ts - started) if first_token_ts is not None else None
            rows.append((e2e, ttft, code, err, completion_tokens))
        return rows

    started_all = time.time()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(worker) for _ in range(concurrency)]
        for f in as_completed(futures):
            for e2e, ttft, code, err, completion_tokens in f.result():
                e2e_latencies.append(e2e)
                if ttft is not None:
                    ttfts.append(ttft)
                codes.append(code)
                completion_tokens_all.append(completion_tokens)
                if err:
                    errors.append(err)
    elapsed = time.time() - started_all

    success = sum(1 for c in codes if c == 200)
    failed = len(codes) - success
    err_rate = (failed / len(codes)) if codes else 1.0

    total_completion_tokens = int(sum(completion_tokens_all))
    result = {
        "total_requests": len(codes),
        "success": success,
        "failed": failed,
        "error_rate": err_rate,
        "elapsed_sec": elapsed,
        "qps": (success / elapsed) if elapsed > 0 else 0.0,
        "latency_e2e": stat_dict(e2e_latencies),
        "latency_ttft": stat_dict(ttfts),
        "completion_tokens": {
            "total": total_completion_tokens,
            "avg_per_request": (total_completion_tokens / len(codes)) if codes else 0.0,
            "tokens_per_sec": (total_completion_tokens / elapsed) if elapsed > 0 else 0.0,
        },
        "errors_sample": errors[:5],
        "_e2e": e2e_latencies,
        "_ttft": ttfts,
        "_codes": codes,
        "_completion_tokens": completion_tokens_all,
    }
    return result


def aggregate(parts: list[dict[str, Any]]) -> dict[str, Any]:
    all_e2e: list[float] = []
    all_ttft: list[float] = []
    codes: list[int] = []
    completion_tokens_all: list[int] = []
    elapsed = 0.0
    for p in parts:
        all_e2e.extend(p["_e2e"])
        all_ttft.extend(p["_ttft"])
        codes.extend(p["_codes"])
        completion_tokens_all.extend(p["_completion_tokens"])
        elapsed += p["elapsed_sec"]

    success = sum(1 for c in codes if c == 200)
    failed = len(codes) - success
    err_rate = (failed / len(codes)) if codes else 1.0
    total_completion_tokens = int(sum(completion_tokens_all))

    return {
        "total_requests": len(codes),
        "success": success,
        "failed": failed,
        "error_rate": err_rate,
        "elapsed_sec": elapsed,
        "qps": (success / elapsed) if elapsed > 0 else 0.0,
        "latency_e2e": stat_dict(all_e2e),
        "latency_ttft": stat_dict(all_ttft),
        "completion_tokens": {
            "total": total_completion_tokens,
            "avg_per_request": (total_completion_tokens / len(codes)) if codes else 0.0,
            "tokens_per_sec": (total_completion_tokens / elapsed) if elapsed > 0 else 0.0,
        },
    }


def make_md(report: dict[str, Any]) -> str:
    lines = []
    lines.append("# 上线门禁压测报告（internal/external + 分桶 + TTFT + tokens/s）")
    lines.append("")
    lines.append("## 测试配置")
    lines.append("")
    lines.append(f"- model: {report['model']}")
    lines.append(f"- base_url: {report['base_url']}")
    lines.append(f"- concurrency: {report['concurrency']}")
    lines.append(f"- max_tokens: {report['max_tokens']}")
    lines.append(f"- requests_per_domain: {report['requests_per_domain']}")
    lines.append("")
    lines.append("## 门禁阈值")
    lines.append("")
    for b in ["short", "medium", "long"]:
        t = report["thresholds"][b]
        lines.append(
            f"- {b}: p95_e2e <= {t['p95_sec']:.3f}s, p99_e2e <= {t['p99_sec']:.3f}s, error_rate <= {t['error_rate']:.2%}"
        )

    lines.append("")
    lines.append("## 分域汇总")
    lines.append("")
    lines.append("| Domain | Requests | QPS | Tokens/s | P95 E2E(s) | P99 E2E(s) | P95 TTFT(s) | Error Rate | Gate |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")

    for d in ["internal", "external"]:
        s = report["domains"][d]["summary"]
        g = report["domains"][d]["gate"]
        lines.append(
            "| {d} | {req} | {qps:.3f} | {tps:.3f} | {p95:.3f} | {p99:.3f} | {ttft:.3f} | {err:.2%} | {g} |".format(
                d=d,
                req=s["total_requests"],
                qps=s["qps"],
                tps=s["completion_tokens"]["tokens_per_sec"],
                p95=s["latency_e2e"]["p95_sec"] or 0.0,
                p99=s["latency_e2e"]["p99_sec"] or 0.0,
                ttft=s["latency_ttft"]["p95_sec"] or 0.0,
                err=s["error_rate"],
                g=g,
            )
        )

    lines.append("")
    lines.append("## 分桶结果")
    lines.append("")
    lines.append("| Domain | Bucket | Requests | QPS | Tokens/s | P95 E2E(s) | P99 E2E(s) | P95 TTFT(s) | Error Rate | Gate |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---|")

    for d in ["internal", "external"]:
        for b in ["short", "medium", "long"]:
            r = report["domains"][d]["buckets"][b]
            lines.append(
                "| {d} | {b} | {req} | {qps:.3f} | {tps:.3f} | {p95:.3f} | {p99:.3f} | {ttft:.3f} | {err:.2%} | {g} |".format(
                    d=d,
                    b=b,
                    req=r["total_requests"],
                    qps=r["qps"],
                    tps=r["completion_tokens"]["tokens_per_sec"],
                    p95=r["latency_e2e"]["p95_sec"] or 0.0,
                    p99=r["latency_e2e"]["p99_sec"] or 0.0,
                    ttft=r["latency_ttft"]["p95_sec"] or 0.0,
                    err=r["error_rate"],
                    g=r["gate"],
                )
            )

    lines.append("")
    lines.append("## 总体门禁结论")
    lines.append("")
    lines.append(f"- overall_gate: **{report['overall_gate']}**")
    lines.append("")
    return "\n".join(lines)


def bucket_gate(
    bucket_result: dict[str, Any],
    *,
    p95_th: float,
    p99_th: float,
    err_th: float,
) -> str:
    p95 = bucket_result["latency_e2e"]["p95_sec"]
    p99 = bucket_result["latency_e2e"]["p99_sec"]
    err = bucket_result["error_rate"]
    if p95 is None or p99 is None:
        return "FAIL"
    ok = (p95 <= p95_th) and (p99 <= p99_th) and (err <= err_th)
    return "PASS" if ok else "FAIL"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--internal-dataset", required=True)
    p.add_argument("--external-dataset", required=True)
    p.add_argument("--requests-per-domain", type=int, default=120)
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--max-tokens", type=int, default=384)
    p.add_argument("--timeout-sec", type=int, default=300)
    p.add_argument("--health-timeout-sec", type=int, default=300)

    p.add_argument("--p95-threshold-short-sec", type=float, default=30.0)
    p.add_argument("--p99-threshold-short-sec", type=float, default=45.0)
    p.add_argument("--p95-threshold-medium-sec", type=float, default=30.0)
    p.add_argument("--p99-threshold-medium-sec", type=float, default=45.0)
    p.add_argument("--p95-threshold-long-sec", type=float, default=45.0)
    p.add_argument("--p99-threshold-long-sec", type=float, default=60.0)
    p.add_argument("--error-threshold", type=float, default=0.005)

    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    args = p.parse_args()

    if args.requests_per_domain < 100 or args.requests_per_domain > 300:
        raise ValueError("requests-per-domain must be in [100, 300]")

    wait_health(args.base_url, args.health_timeout_sec)

    domains = {
        "internal": extract_prompts(args.internal_dataset),
        "external": extract_prompts(args.external_dataset),
    }

    thresholds = {
        "short": {
            "p95_sec": args.p95_threshold_short_sec,
            "p99_sec": args.p99_threshold_short_sec,
            "error_rate": args.error_threshold,
        },
        "medium": {
            "p95_sec": args.p95_threshold_medium_sec,
            "p99_sec": args.p99_threshold_medium_sec,
            "error_rate": args.error_threshold,
        },
        "long": {
            "p95_sec": args.p95_threshold_long_sec,
            "p99_sec": args.p99_threshold_long_sec,
            "error_rate": args.error_threshold,
        },
    }

    report = {
        "model": args.model,
        "base_url": args.base_url,
        "concurrency": args.concurrency,
        "max_tokens": args.max_tokens,
        "requests_per_domain": args.requests_per_domain,
        "thresholds": thresholds,
        "domains": {},
        "generated_at": int(time.time()),
    }

    base = args.requests_per_domain // 3
    rem = args.requests_per_domain % 3
    reqs = {"short": base, "medium": base, "long": base}
    for b in ["short", "medium", "long"][:rem]:
        reqs[b] += 1

    overall_pass = True
    for domain_name, prompts in domains.items():
        buckets = bucketize(prompts)
        bucket_results: dict[str, Any] = {}
        parts = []

        for b in ["short", "medium", "long"]:
            print(f"Running {domain_name}/{b} ...")
            r = run_requests(
                base_url=args.base_url,
                model=args.model,
                prompts=buckets[b],
                total_requests=reqs[b],
                concurrency=args.concurrency,
                max_tokens=args.max_tokens,
                timeout_sec=args.timeout_sec,
            )
            g = bucket_gate(
                r,
                p95_th=thresholds[b]["p95_sec"],
                p99_th=thresholds[b]["p99_sec"],
                err_th=thresholds[b]["error_rate"],
            )
            r["gate"] = g
            bucket_results[b] = r
            parts.append(r)

        summary = aggregate(parts)
        domain_pass = all(bucket_results[b]["gate"] == "PASS" for b in ["short", "medium", "long"])
        domain_gate = "PASS" if domain_pass else "FAIL"
        if domain_gate != "PASS":
            overall_pass = False

        report["domains"][domain_name] = {
            "bucket_requests": reqs,
            "bucket_sizes": {k: len(v) for k, v in buckets.items()},
            "buckets": {
                k: {
                    kk: vv
                    for kk, vv in bucket_results[k].items()
                    if not kk.startswith("_")
                }
                for k in ["short", "medium", "long"]
            },
            "summary": summary,
            "gate": domain_gate,
        }

    report["overall_gate"] = "PASS" if overall_pass else "FAIL"

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.out_md).write_text(make_md(report), encoding="utf-8")

    print(f"saved: {args.out_json}")
    print(f"saved: {args.out_md}")


if __name__ == "__main__":
    main()
