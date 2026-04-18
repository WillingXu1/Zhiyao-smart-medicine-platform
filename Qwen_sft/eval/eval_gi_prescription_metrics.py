#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

UNIT_SET = {"mg", "g", "ml", "ug", "μg", "片", "粒", "袋", "支"}
CN_NUM = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}

DRUG_ALIASES = {
    "奥美拉唑镁肠溶片": "奥美拉唑",
    "奥美拉唑肠溶片": "奥美拉唑",
    "注射用奥美拉唑钠": "奥美拉唑",
    "伴托拉唑钠肠溶片": "伴托拉唑",
    "雷尼替丁胶囊": "雷尼替丁",
    "盐酸雷尼替丁胶囊": "雷尼替丁",
    "法莫替丁胶囊": "法莫替丁",
    "阿莫西林胶囊": "阿莫西林",
    "克拉霉素": "克拉霉素",
}

RX_DRUG_DOSE = re.compile(
    r"([A-Za-z\u4e00-\u9fff\-·]+?(?:片|胶囊|颗粒|注射液|注射用|凝胶|口服液|丸|散|混悬液|乳剂|滴丸|针|制剂))\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s*(mg|g|ml|ug|μg|片|粒|袋|支)",
    re.IGNORECASE,
)

RX_DRUG_ONLY = re.compile(
    r"([A-Za-z\u4e00-\u9fff\-·]{2,30}?(?:片|胶囊|颗粒|注射液|注射用|凝胶|口服液|丸|散|混悬液|乳剂|滴丸|针|制剂))"
)

RX_FREQ = [
    re.compile(r"每日\s*([0-9]+)\s*次"),
    re.compile(r"每天\s*([0-9]+)\s*次"),
    re.compile(r"一日\s*([0-9一二两三四五六七八九十]+)\s*次"),
    re.compile(r"(qd|bid|tid|qid)", re.IGNORECASE),
]

RX_COURSE = [
    re.compile(r"(?:疗程|持续|连续)\s*([0-9]+(?:\.[0-9]+)?)\s*天"),
    re.compile(r"(?:疗程|持续|连续)\s*([0-9]+(?:\.[0-9]+)?)\s*周"),
]

RX_ALLERGY = [
    re.compile(r"对([^，。；;,.]{1,20}?)(?:过敏|不耐受)"),
    re.compile(r"([^，。；;,.]{1,20}?)过敏史"),
]


def normalize_text(s: str) -> str:
    s = (s or "").replace("\r", "").strip()
    s = s.replace("×", "x")
    s = re.sub(r"\s+", " ", s)
    return s


def read_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except Exception:
            continue
    return rows


def canonical_drug(name: str) -> str:
    n = normalize_text(name).lower()
    n = re.sub(r"[()（）,，。:：;； ]", "", n)
    for k, v in DRUG_ALIASES.items():
        if k in name:
            return v
    for suffix in ["肠溶片", "片", "胶囊", "颗粒", "口服液", "凝胶", "注射液", "注射用", "丸", "散", "制剂"]:
        n = n.replace(suffix, "")
    return n


def cn_to_int(s: str) -> Optional[int]:
    if not s:
        return None
    if s.isdigit():
        return int(s)
    if s in CN_NUM:
        return CN_NUM[s]
    if len(s) == 2 and s[0] == "十" and s[1] in CN_NUM:
        return 10 + CN_NUM[s[1]]
    return None


def parse_freq(context: str) -> Optional[str]:
    t = normalize_text(context).lower()
    for rx in RX_FREQ:
        m = rx.search(t)
        if not m:
            continue
        g = m.group(1).lower()
        if g in {"qd", "bid", "tid", "qid"}:
            return g
        n = cn_to_int(g)
        if n is not None:
            return f"{n}/day"
    return None


def parse_course_days(text: str) -> Optional[float]:
    t = normalize_text(text).lower()
    for i, rx in enumerate(RX_COURSE):
        m = rx.search(t)
        if not m:
            continue
        v = float(m.group(1))
        if i == 1:
            return v * 7.0
        return v
    return None


def extract_items(text: str) -> List[dict]:
    t = normalize_text(text)
    items: List[dict] = []
    for m in RX_DRUG_DOSE.finditer(t):
        drug_raw = m.group(1)
        dose = float(m.group(2))
        unit = m.group(3).lower()
        if unit not in UNIT_SET:
            continue
        start = max(0, m.start() - 30)
        end = min(len(t), m.end() + 80)
        ctx = t[start:end]
        items.append(
            {
                "drug": canonical_drug(drug_raw),
                "drug_raw": drug_raw,
                "dose": dose,
                "unit": unit,
                "freq": parse_freq(ctx),
            }
        )

    # Fallback: capture drug names without explicit dose/unit.
    for m in RX_DRUG_ONLY.finditer(t):
        drug_raw = m.group(1)
        cdrug = canonical_drug(drug_raw)
        if not cdrug:
            continue
        if any(it.get("drug") == cdrug for it in items):
            continue
        start = max(0, m.start() - 30)
        end = min(len(t), m.end() + 80)
        ctx = t[start:end]
        items.append(
            {
                "drug": cdrug,
                "drug_raw": drug_raw,
                "dose": None,
                "unit": None,
                "freq": parse_freq(ctx),
            }
        )

    course = parse_course_days(t)
    for it in items:
        it["course_days"] = course

    # Deduplicate by canonical drug; keep first appearance.
    dedup: Dict[str, dict] = {}
    for it in items:
        if it["drug"] and it["drug"] not in dedup:
            dedup[it["drug"]] = it
    return list(dedup.values())


def get_user_text(row: dict) -> str:
    msgs = row.get("messages") or []
    for m in reversed(msgs):
        if m.get("role") == "user":
            return normalize_text(str(m.get("content", "")))
    return ""


def extract_contra_terms(user_text: str) -> List[str]:
    t = normalize_text(user_text)
    terms: List[str] = []
    for rx in RX_ALLERGY:
        for m in rx.finditer(t):
            x = normalize_text(m.group(1))
            x = re.sub(r"[^A-Za-z\u4e00-\u9fff]", "", x)
            if len(x) >= 2:
                terms.append(x)
    uniq: List[str] = []
    for x in terms:
        if x not in uniq:
            uniq.append(x)
    return uniq


def rel_close(a: float, b: float, tol: float = 0.1) -> bool:
    d = abs(a - b)
    return d / max(abs(b), 1e-6) <= tol


def compute_metrics(rows: List[dict], dose_tol: float = 0.1, course_tol: float = 0.2) -> Dict[str, float]:
    pred_total = 0
    ref_total = 0
    pred_hit = 0
    ref_hit = 0

    aligned_total = 0
    duc_hit = 0
    fcf_sum = 0.0

    ccr_den = 0
    ccr_num = 0

    for r in rows:
        pred_items = extract_items(str(r.get("response", "")))
        ref_items = extract_items(str(r.get("labels", "")))

        pred_total += len(pred_items)
        ref_total += len(ref_items)

        ref_map = {x["drug"]: x for x in ref_items if x.get("drug")}
        pred_map = {x["drug"]: x for x in pred_items if x.get("drug")}

        for d in pred_map:
            if d in ref_map:
                pred_hit += 1
        for d in ref_map:
            if d in pred_map:
                ref_hit += 1

        for d, p in pred_map.items():
            g = ref_map.get(d)
            if not g:
                continue
            aligned_total += 1

            p_dose = p.get("dose")
            g_dose = g.get("dose")
            if (
                p.get("unit")
                and g.get("unit")
                and p_dose is not None
                and g_dose is not None
                and p.get("unit") == g.get("unit")
                and rel_close(float(p_dose), float(g_dose), dose_tol)
            ):
                duc_hit += 1

            freq_ok = 1.0 if (p.get("freq") and g.get("freq") and p.get("freq") == g.get("freq")) else 0.0
            p_course = p.get("course_days")
            g_course = g.get("course_days")
            course_ok = 1.0 if (p_course is not None and g_course is not None and rel_close(float(p_course), float(g_course), course_tol)) else 0.0
            fcf_sum += 0.5 * freq_ok + 0.5 * course_ok

        user_text = get_user_text(r)
        contra_terms = extract_contra_terms(user_text)
        if contra_terms:
            ccr_den += 1
            pred_text = normalize_text(str(r.get("response", "")))
            conflict = any(t in pred_text for t in contra_terms)
            ccr_num += 1 if conflict else 0

    dep = (pred_hit / pred_total) if pred_total else 0.0
    der = (ref_hit / ref_total) if ref_total else 0.0
    duc = (duc_hit / aligned_total) if aligned_total else 0.0
    fcf = (fcf_sum / aligned_total) if aligned_total else 0.0
    ccr = (ccr_num / ccr_den) if ccr_den else 0.0

    score = 0.35 * dep + 0.20 * der + 0.20 * duc + 0.15 * fcf + 0.10 * (1.0 - ccr)

    return {
        "n": len(rows),
        "pred_drug_total": pred_total,
        "ref_drug_total": ref_total,
        "aligned_drug_total": aligned_total,
        "contra_case_total": ccr_den,
        "DEP": dep,
        "DER": der,
        "DUC": duc,
        "FCF": fcf,
        "CCR": ccr,
        "GI_prescription_score": score,
    }


def pooled(v_i: float, n_i: int, v_e: float, n_e: int) -> float:
    d = n_i + n_e
    return (v_i * n_i + v_e * n_e) / d if d else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description="GI prescription capability metrics (DEP/DER/DUC/FCF/CCR)")
    ap.add_argument("--internal-dir", required=True)
    ap.add_argument("--external-dir", required=True)
    ap.add_argument("--internal-prefix", default="internal59")
    ap.add_argument("--external-prefix", default="external24")
    ap.add_argument("--models", default="huatuo_o1_7b_zeroshot,qwen25_7b_ft_run9_2")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--output-prefix", default="gi_prescription_eval")
    ap.add_argument("--dose-tol", type=float, default=0.1)
    ap.add_argument("--course-tol", type=float, default=0.2)
    args = ap.parse_args()

    models = [x.strip() for x in args.models.split(",") if x.strip()]
    if not models:
        raise ValueError("--models must not be empty")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report: Dict[str, Dict[str, dict]] = {"internal": {}, "external": {}, "pooled": {}}

    for model in models:
        p_i = Path(args.internal_dir) / f"{args.internal_prefix}_{model}.jsonl"
        p_e = Path(args.external_dir) / f"{args.external_prefix}_{model}.jsonl"
        rows_i = read_jsonl(p_i)
        rows_e = read_jsonl(p_e)

        m_i = compute_metrics(rows_i, dose_tol=args.dose_tol, course_tol=args.course_tol)
        m_e = compute_metrics(rows_e, dose_tol=args.dose_tol, course_tol=args.course_tol)

        report["internal"][model] = m_i
        report["external"][model] = m_e

        n_i, n_e = m_i["n"], m_e["n"]
        report["pooled"][model] = {
            "n": n_i + n_e,
            "DEP": pooled(m_i["DEP"], n_i, m_e["DEP"], n_e),
            "DER": pooled(m_i["DER"], n_i, m_e["DER"], n_e),
            "DUC": pooled(m_i["DUC"], n_i, m_e["DUC"], n_e),
            "FCF": pooled(m_i["FCF"], n_i, m_e["FCF"], n_e),
            "CCR": pooled(m_i["CCR"], n_i, m_e["CCR"], n_e),
            "GI_prescription_score": pooled(m_i["GI_prescription_score"], n_i, m_e["GI_prescription_score"], n_e),
        }

    out_json = out_dir / f"{args.output_prefix}.json"
    out_md = out_dir / f"{args.output_prefix}.md"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md: List[str] = [
        "# GI处方能力自动评估（DEP/DER/DUC/FCF/CCR）",
        "",
        f"- dose_tol={args.dose_tol}",
        f"- course_tol={args.course_tol}",
        "",
        "## Pooled (Internal + External)",
        "",
        "| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for model in models:
        x = report["pooled"][model]
        md.append(
            f"| {model} | {x['n']} | {x['DEP']:.4f} | {x['DER']:.4f} | {x['DUC']:.4f} | {x['FCF']:.4f} | {x['CCR']:.4f} | {x['GI_prescription_score']:.4f} |"
        )

    for split in ["internal", "external"]:
        md.extend([
            "",
            f"## {split.title()}",
            "",
            "| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for model in models:
            x = report[split][model]
            md.append(
                f"| {model} | {x['n']} | {x['DEP']:.4f} | {x['DER']:.4f} | {x['DUC']:.4f} | {x['FCF']:.4f} | {x['CCR']:.4f} | {x['GI_prescription_score']:.4f} |"
            )

    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"saved: {out_json}")
    print(f"saved: {out_md}")


if __name__ == "__main__":
    main()
