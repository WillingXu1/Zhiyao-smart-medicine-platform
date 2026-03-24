import json
import re
from pathlib import Path
from difflib import SequenceMatcher as S


def load(path, tag):
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("tag", "") == tag:
                rows.append(r)
    return rows


def rep_ratio(text):
    toks = re.findall(r"\S+", text)
    if len(toks) < 3:
        return 0.0
    bi = [" ".join(toks[i:i + 2]) for i in range(len(toks) - 1)]
    return 1 - len(set(bi)) / len(bi)


META_PATTERNS = [r"根据您提供的信息", r"建议：", r"请务必", r"仅供参考", r"###", r"总结"]
META_RE = [re.compile(p) for p in META_PATTERNS]


def analyze(rows):
    n = len(rows)
    low_overlap = 0
    overgen = 0
    high_repeat = 0
    meta = 0
    hallucinated = 0
    details = []

    for i, r in enumerate(rows):
        label = str(r.get("labels", ""))
        pred = str(r.get("response", ""))
        ov = S(None, pred, label).ratio()
        lr = len(pred) / (len(label) + 1e-6)
        rr = rep_ratio(pred)
        mt = any(rx.search(pred) for rx in META_RE)

        c1 = ov < 0.10
        c2 = lr > 3.0
        c3 = rr > 0.05
        c4 = mt and ov < 0.20

        flags = sum([c1, c2, c3, c4])
        hall = flags >= 1

        low_overlap += c1
        overgen += c2
        high_repeat += c3
        meta += c4
        hallucinated += hall

        details.append((i, ov, lr, rr, flags, pred[:120].replace("\n", " "), label[:120].replace("\n", " ")))

    return {
        "n": n,
        "low_overlap_rate": low_overlap / n if n else 0,
        "overgen_rate": overgen / n if n else 0,
        "high_repeat_rate": high_repeat / n if n else 0,
        "meta_hall_rate": meta / n if n else 0,
        "hallucination_proxy_rate": hallucinated / n if n else 0,
        "details": details,
    }


def main():
    sets = [
        ("internal20_base", "output/eval_run7/internal20_base.jsonl", "internal20_base"),
        ("internal20_run7", "output/eval_run7/internal20_run7.jsonl", "internal20_run7"),
        ("external23_base", "output/eval_run7/external23_base.jsonl", "external23_base"),
        ("external23_run7", "output/eval_run7/external23_run7.jsonl", "external23_run7"),
    ]

    res = {}
    for name, path, tag in sets:
        rows = load(path, tag)
        res[name] = analyze(rows)

    for k, v in res.items():
        print(
            k,
            "n=", v["n"],
            "hall=", round(v["hallucination_proxy_rate"], 4),
            "low_ov=", round(v["low_overlap_rate"], 4),
            "overgen=", round(v["overgen_rate"], 4),
            "repeat=", round(v["high_repeat_rate"], 4),
            "meta=", round(v["meta_hall_rate"], 4),
        )

    out = Path("output/eval_run7/hallucination_proxy_report.json")
    out.write_text(
        json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "details"} for k, v in res.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("saved", out)

    for key in ["external23_base", "external23_run7"]:
        arr = sorted(res[key]["details"], key=lambda x: (x[4], -x[1]), reverse=True)[:3]
        print("TOP", key)
        for a in arr:
            print("idx", a[0], "ov", round(a[1], 3), "lr", round(a[2], 2), "rr", round(a[3], 3), "flags", a[4])
            print("pred", a[5])
            print("lab ", a[6])


if __name__ == "__main__":
    main()
