#!/usr/bin/env python3
import argparse
import json
import math
import re
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def read_jsonl(path: Path, tag: str = "") -> List[dict]:
    rows = []
    for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            row = json.loads(ln)
        except Exception:
            continue
        if tag and row.get("tag") != tag:
            continue
        rows.append(row)
    return rows


def normalize_text(s: str) -> str:
    s = s or ""
    s = s.replace("\r", "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def tokenize(s: str) -> List[str]:
    s = normalize_text(s)
    if not s:
        return []
    if has_cjk(s):
        # For Chinese-heavy text, char-level tokenization is robust without extra deps.
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
        c = ref_count.get(t, 0)
        if c > 0:
            hit += 1
            ref_count[t] = c - 1
    prec = hit / len(p)
    rec = hit / len(r)
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


def lcs_len(a: List[str], b: List[str]) -> int:
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return 0
    dp = [0] * (m + 1)
    for i in range(1, n + 1):
        prev = 0
        for j in range(1, m + 1):
            tmp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = tmp
    return dp[m]


def rouge_l_f1(pred: str, ref: str) -> float:
    p = tokenize(pred)
    r = tokenize(ref)
    if not p and not r:
        return 1.0
    if not p or not r:
        return 0.0
    lcs = lcs_len(p, r)
    prec = lcs / len(p)
    rec = lcs / len(r)
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

    weights = [0.25, 0.25, 0.25, 0.25]
    log_prec_sum = 0.0

    for n, w in zip([1, 2, 3, 4], weights):
        p_cnt = ngram_counts(p, n)
        r_cnt = ngram_counts(r, n)
        if not p_cnt:
            # add-1 smoothing
            prec_n = 1.0 / (1.0 + 1.0)
        else:
            match = 0
            total = 0
            for g, c in p_cnt.items():
                total += c
                match += min(c, r_cnt.get(g, 0))
            prec_n = (match + 1.0) / (total + 1.0)
        log_prec_sum += w * math.log(max(prec_n, 1e-12))

    bp = 1.0 if len(p) > len(r) else math.exp(1 - len(r) / max(len(p), 1))
    return bp * math.exp(log_prec_sum)


def infer_gender(text: str) -> str:
    t = text or ""
    if "女" in t:
        return "female"
    if "男" in t:
        return "male"
    return "unknown"


def compute_ece(conf: List[float], corr: List[int], bins: int = 10) -> float:
    if not conf:
        return 0.0
    ece = 0.0
    n = len(conf)
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, c in enumerate(conf) if (c >= lo and (c < hi or (b == bins - 1 and c <= hi)))]
        if not idx:
            continue
        avg_conf = sum(conf[i] for i in idx) / len(idx)
        avg_acc = sum(corr[i] for i in idx) / len(idx)
        ece += (len(idx) / n) * abs(avg_conf - avg_acc)
    return ece


def summarize(rows: List[dict]) -> Dict[str, float]:
    ems, f1s, rouges, bleus = [], [], [], []
    confs, corrs = [], []
    by_gender = {"female": [], "male": []}

    for row in rows:
        pred = str(row.get("response", ""))
        ref = str(row.get("labels", ""))
        user = ""
        msgs = row.get("messages") or []
        if len(msgs) >= 2:
            user = str(msgs[1].get("content", ""))

        em = exact_match(pred, ref)
        f1 = f1_score(pred, ref)
        rl = rouge_l_f1(pred, ref)
        b4 = bleu4(pred, ref)

        ems.append(em)
        f1s.append(f1)
        rouges.append(rl)
        bleus.append(b4)

        # Calibration proxy: confidence=RougeL, correctness=(F1>=0.5)
        confs.append(max(0.0, min(1.0, rl)))
        corrs.append(1 if f1 >= 0.5 else 0)

        g = infer_gender(user)
        if g in by_gender:
            by_gender[g].append(1 if f1 >= 0.5 else 0)

    n = len(rows)
    mean = lambda x: (sum(x) / len(x)) if x else 0.0

    female_rate = mean(by_gender["female"]) if by_gender["female"] else 0.0
    male_rate = mean(by_gender["male"]) if by_gender["male"] else 0.0

    return {
        "n": n,
        "exact_match": mean(ems),
        "f1": mean(f1s),
        "rouge_l": mean(rouges),
        "bleu_4": mean(bleus),
        "ece_proxy": compute_ece(confs, corrs, bins=10),
        "dpd_proxy": abs(female_rate - male_rate),
        "quality_rate_f1_ge_0.5": mean(corrs),
        "quality_rate_female": female_rate,
        "quality_rate_male": male_rate,
    }


SECTION_PATTERNS = {
    "diagnosis": [
        r"诊断[：:\s]",
        r"诊断结果[：:\s]",
        r"中医诊断[：:\s]",
        r"西医诊断[：:\s]",
        r"辨证[：:\s]",
    ],
    "prescription": [
        r"处方[：:\s]",
        r"方药[：:\s]",
        r"方剂[：:\s]",
        r"药物[：:\s]",
        r"用药方案[：:\s]",
    ],
    "usage": [
        r"用法[：:\s]",
        r"用量[：:\s]",
        r"服法[：:\s]",
        r"频次[：:\s]",
        r"疗程[：:\s]",
        r"注意事项[：:\s]",
    ],
}


def _first_hit(text: str, pats: List[str]) -> int:
    best = -1
    for pat in pats:
        m = re.search(pat, text)
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
        idx = _first_hit(t, pats)
        if idx >= 0:
            locs.append((name, idx))

    if not locs:
        # Fall back to full-text diagnosis when section headers are absent.
        return {"diagnosis": t, "prescription": "", "usage": ""}

    locs.sort(key=lambda x: x[1])
    out = {"diagnosis": "", "prescription": "", "usage": ""}
    for i, (name, start) in enumerate(locs):
        end = locs[i + 1][1] if i + 1 < len(locs) else len(t)
        out[name] = normalize_text(t[start:end])
    return out


def _has_section(sec_text: str) -> int:
    return 1 if normalize_text(sec_text) else 0


def structure_metrics(rows: List[dict]) -> Dict[str, float]:
    d_has, p_has, u_has, all_three = 0, 0, 0, 0
    n = len(rows)
    if n == 0:
        return {
            "n": 0,
            "diagnosis_presence_rate": 0.0,
            "prescription_presence_rate": 0.0,
            "usage_presence_rate": 0.0,
            "three_section_compliance_rate": 0.0,
        }

    for row in rows:
        pred = str(row.get("response", ""))
        sec = split_sections(pred)
        d = _has_section(sec["diagnosis"])
        p = _has_section(sec["prescription"])
        u = _has_section(sec["usage"])
        d_has += d
        p_has += p
        u_has += u
        all_three += 1 if (d and p and u) else 0

    return {
        "n": n,
        "diagnosis_presence_rate": d_has / n,
        "prescription_presence_rate": p_has / n,
        "usage_presence_rate": u_has / n,
        "three_section_compliance_rate": all_three / n,
    }


DRUG_DOSE_RX = re.compile(
    r"([A-Za-z\u4e00-\u9fff\-·]{2,24}(?:片|胶囊|颗粒|注射液|注射用|口服液|丸|散|制剂)?)\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s*(mg|g|ml|ug|μg)",
    re.IGNORECASE,
)

DRUG_RX = re.compile(
    r"([A-Za-z\u4e00-\u9fff\-·]{2,24}(?:片|胶囊|颗粒|注射液|注射用|口服液|丸|散|制剂))"
)

FREQ_RX = [
    re.compile(r"每日\s*([0-9]+)\s*次"),
    re.compile(r"每天\s*([0-9]+)\s*次"),
    re.compile(r"一日\s*([0-9一二两三四五六七八九十]+)\s*次"),
    re.compile(r"(qd|bid|tid|qid)", re.IGNORECASE),
]

ALLERGY_RX = [
    re.compile(r"对([^，。；;,.]{1,20}?)(?:过敏|不耐受)"),
    re.compile(r"([^，。；;,.]{1,20}?)过敏史"),
]


def _cn_to_int(s: str) -> Optional[int]:
    mp = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    if not s:
        return None
    if s.isdigit():
        return int(s)
    if s in mp:
        return mp[s]
    if len(s) == 2 and s[0] == "十" and s[1] in mp:
        return 10 + mp[s[1]]
    return None


def _canonical_drug(name: str) -> str:
    x = normalize_text(name).lower()
    x = re.sub(r"[()（）,，。:：;； ]", "", x)
    for suffix in ["肠溶片", "片", "胶囊", "颗粒", "口服液", "注射液", "注射用", "丸", "散", "制剂"]:
        x = x.replace(suffix, "")
    return x


def _parse_freq(text: str) -> Optional[str]:
    t = normalize_text(text).lower()
    for rx in FREQ_RX:
        m = rx.search(t)
        if not m:
            continue
        g = m.group(1).lower()
        if g in {"qd", "bid", "tid", "qid"}:
            return g
        n = _cn_to_int(g)
        if n is not None:
            return f"{n}/day"
    return None


def _extract_slots(text: str) -> Dict[str, object]:
    t = normalize_text(text)
    sec = split_sections(t)

    diagnosis_key = ""
    d = sec["diagnosis"]
    m_diag = re.search(r"诊断[：:]?\s*([^。；;\n]+)", d)
    if m_diag:
        diagnosis_key = normalize_text(m_diag.group(1))
    elif d:
        diagnosis_key = d[:32]

    meds: Dict[str, Dict[str, object]] = {}
    for m in DRUG_DOSE_RX.finditer(t):
        raw = m.group(1)
        key = _canonical_drug(raw)
        meds[key] = {
            "drug": key,
            "dose": float(m.group(2)),
            "unit": m.group(3).lower(),
            "freq": _parse_freq(t[max(0, m.start()-40): min(len(t), m.end()+80)]),
        }
    for m in DRUG_RX.finditer(t):
        raw = m.group(1)
        key = _canonical_drug(raw)
        if key not in meds:
            meds[key] = {"drug": key, "dose": None, "unit": None, "freq": _parse_freq(t)}

    return {
        "diagnosis": diagnosis_key,
        "meds": meds,
        "sections": sec,
    }


def _rel_close(a: float, b: float, tol: float = 0.1) -> bool:
    return abs(a - b) / max(abs(b), 1e-6) <= tol


def _normalize_dose_to_base(
    dose: Optional[float], unit: Optional[str]
) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    if dose is None or unit is None:
        return None, None, None
    try:
        val = float(dose)
    except (TypeError, ValueError):
        return None, None, None

    u = normalize_text(str(unit)).lower().replace("μ", "u")
    if u == "g":
        return val * 1000.0, "mg", "mass"
    if u == "mg":
        return val, "mg", "mass"
    if u == "ug":
        return val / 1000.0, "mg", "mass"
    if u == "ml":
        return val, "ml", "volume"
    return None, None, None


def slot_metrics(rows: List[dict], dose_tol: float = 0.1) -> Dict[str, float]:
    diag_ok = 0
    diag_total = 0
    pred_med_total = 0
    ref_med_total = 0
    med_hit_p = 0
    med_hit_r = 0
    dose_hit = 0
    freq_hit = 0
    aligned = 0

    for row in rows:
        pred = str(row.get("response", ""))
        ref = str(row.get("labels", ""))
        ps = _extract_slots(pred)
        rs = _extract_slots(ref)

        rd = str(rs["diagnosis"])
        pd = str(ps["diagnosis"])
        if rd:
            diag_total += 1
            if rd and pd and (rd in pd or pd in rd or rouge_l_f1(pd, rd) >= 0.6):
                diag_ok += 1

        pm = ps["meds"]
        rm = rs["meds"]
        pred_med_total += len(pm)
        ref_med_total += len(rm)

        for k in pm:
            if k in rm:
                med_hit_p += 1
        for k in rm:
            if k in pm:
                med_hit_r += 1

        for k, p in pm.items():
            g = rm.get(k)
            if not g:
                continue
            aligned += 1
            p_dose, _p_unit, p_kind = _normalize_dose_to_base(p.get("dose"), p.get("unit"))
            g_dose, _g_unit, g_kind = _normalize_dose_to_base(g.get("dose"), g.get("unit"))
            if (
                p_dose is not None
                and g_dose is not None
                and p_kind is not None
                and p_kind == g_kind
            ):
                if _rel_close(p_dose, g_dose, dose_tol):
                    dose_hit += 1
            if p.get("freq") and g.get("freq") and p.get("freq") == g.get("freq"):
                freq_hit += 1

    p = med_hit_p / pred_med_total if pred_med_total else 0.0
    r = med_hit_r / ref_med_total if ref_med_total else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {
        "n": len(rows),
        "diagnosis_match_rate": diag_ok / diag_total if diag_total else 0.0,
        "drug_precision": p,
        "drug_recall": r,
        "drug_f1": f1,
        "dose_match_rate": dose_hit / aligned if aligned else 0.0,
        "freq_match_rate": freq_hit / aligned if aligned else 0.0,
        "aligned_drug_count": aligned,
    }


def _extract_allergy_terms(user_text: str) -> List[str]:
    t = normalize_text(user_text)
    terms: List[str] = []
    for rx in ALLERGY_RX:
        for m in rx.finditer(t):
            x = re.sub(r"[^A-Za-z\u4e00-\u9fff]", "", normalize_text(m.group(1)))
            if len(x) >= 2 and x not in terms:
                terms.append(x)
    return terms


def _get_user_text(row: dict) -> str:
    msgs = row.get("messages") or []
    for m in reversed(msgs):
        if m.get("role") == "user":
            return normalize_text(str(m.get("content", "")))
    return ""


def risk_metrics(rows: List[dict]) -> Dict[str, float]:
    n = len(rows)
    if n == 0:
        return {
            "n": 0,
            "missing_diagnosis_rate": 0.0,
            "missing_prescription_rate": 0.0,
            "missing_usage_rate": 0.0,
            "allergy_conflict_rate": 0.0,
            "high_risk_rate": 0.0,
        }

    miss_d = miss_p = miss_u = allergy_conf = high_risk = 0
    for row in rows:
        pred = str(row.get("response", ""))
        ref = str(row.get("labels", ""))
        ps = split_sections(pred)
        rs = split_sections(ref)

        d_miss = 1 if (_has_section(rs["diagnosis"]) and not _has_section(ps["diagnosis"])) else 0
        p_miss = 1 if (_has_section(rs["prescription"]) and not _has_section(ps["prescription"])) else 0
        u_miss = 1 if (_has_section(rs["usage"]) and not _has_section(ps["usage"])) else 0
        miss_d += d_miss
        miss_p += p_miss
        miss_u += u_miss

        user_text = _get_user_text(row)
        at = _extract_allergy_terms(user_text)
        conf = 1 if (at and any(x in normalize_text(pred) for x in at)) else 0
        allergy_conf += conf

        high_risk += 1 if (d_miss or p_miss or u_miss or conf) else 0

    return {
        "n": n,
        "missing_diagnosis_rate": miss_d / n,
        "missing_prescription_rate": miss_p / n,
        "missing_usage_rate": miss_u / n,
        "allergy_conflict_rate": allergy_conf / n,
        "high_risk_rate": high_risk / n,
    }


def load_medical_terms(path: Optional[Path]) -> set[str]:
    if not path:
        return set()
    terms: set[str] = set()
    for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = normalize_text(ln)
        if len(s) >= 2:
            terms.add(s)
    return terms


def extract_terms(text: str, term_dict: set[str]) -> set[str]:
    t = normalize_text(text)
    if not t:
        return set()

    if term_dict:
        return {x for x in term_dict if x in t}

    # Dictionary-free fallback: Chinese medical-like terms and dosage tokens.
    cjk_terms = set(re.findall(r"[\u4e00-\u9fff]{2,8}", t))
    ascii_terms = set(re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", t))
    filtered = {
        x for x in cjk_terms.union(ascii_terms)
        if x not in {"患者", "建议", "治疗", "情况", "可以", "需要"}
    }
    return filtered


def term_recall(pred: str, ref: str, term_dict: set[str]) -> float:
    ref_terms = extract_terms(ref, term_dict)
    if not ref_terms:
        return 1.0
    pred_terms = extract_terms(pred, term_dict)
    hit = len(ref_terms.intersection(pred_terms))
    return hit / max(1, len(ref_terms))


def layered_metrics(rows: List[dict], term_dict: set[str]) -> Dict[str, float]:
    d_scores, p_scores, u_scores = [], [], []
    t_recalls = []
    covered = 0

    for row in rows:
        pred = str(row.get("response", ""))
        ref = str(row.get("labels", ""))

        ps = split_sections(pred)
        rs = split_sections(ref)
        if rs["diagnosis"] or rs["prescription"] or rs["usage"]:
            covered += 1

        d_scores.append(rouge_l_f1(ps["diagnosis"], rs["diagnosis"]))
        p_scores.append(rouge_l_f1(ps["prescription"], rs["prescription"]))
        u_scores.append(rouge_l_f1(ps["usage"], rs["usage"]))
        t_recalls.append(term_recall(pred, ref, term_dict))

    mean = lambda x: (sum(x) / len(x)) if x else 0.0
    return {
        "section_coverage_rate": covered / max(1, len(rows)),
        "rouge_l_diagnosis": mean(d_scores),
        "rouge_l_prescription": mean(p_scores),
        "rouge_l_usage": mean(u_scores),
        "terminology_recall": mean(t_recalls),
    }


def export_manual_review(
    rows: List[dict],
    out_csv: Path,
    term_dict: set[str],
    max_rows: int,
) -> None:
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

        rs = risk_metrics([row])
        miss_score = (
            rs["missing_diagnosis_rate"]
            + rs["missing_prescription_rate"]
            + rs["missing_usage_rate"]
        ) / 3.0
        allergy_score = rs["allergy_conflict_rate"]
        total_risk = min(1.0, 0.75 * risk + 0.15 * miss_score + 0.10 * allergy_score)

        risk_flags: List[str] = []
        if rs["missing_diagnosis_rate"] > 0:
            risk_flags.append("missing_diagnosis")
        if rs["missing_prescription_rate"] > 0:
            risk_flags.append("missing_prescription")
        if rs["missing_usage_rate"] > 0:
            risk_flags.append("missing_usage")
        if rs["allergy_conflict_rate"] > 0:
            risk_flags.append("allergy_conflict")

        scored.append(
            {
                "idx": i,
                "risk_score": total_risk,
                "rouge_l_diagnosis": d,
                "rouge_l_prescription": p,
                "rouge_l_usage": u,
                "terminology_recall": tr,
                "risk_flags": "|".join(risk_flags),
                "user": user,
                "reference": ref,
                "prediction": pred,
            }
        )

    scored.sort(key=lambda x: x["risk_score"], reverse=True)
    pick = scored[:max_rows]

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
                "risk_flags",
                "user",
                "reference",
                "prediction",
            ],
        )
        w.writeheader()
        for r in pick:
            w.writerow(r)


def pdr(base_val: float, new_val: float) -> float:
    if base_val <= 0:
        return 0.0
    return max(0.0, (base_val - new_val) / base_val)


def compare(base: Dict[str, float], new: Dict[str, float]) -> Dict[str, float]:
    return {
        "pdr_em": pdr(base.get("exact_match", 0.0), new.get("exact_match", 0.0)),
        "pdr_f1": pdr(base.get("f1", 0.0), new.get("f1", 0.0)),
        "pdr_rouge_l": pdr(base.get("rouge_l", 0.0), new.get("rouge_l", 0.0)),
        "pdr_bleu_4": pdr(base.get("bleu_4", 0.0), new.get("bleu_4", 0.0)),
    }


def evaluate_release_gate(
    risk_inew: Dict[str, float],
    risk_enew: Dict[str, float],
    struct_inew: Dict[str, float],
    struct_enew: Dict[str, float],
    slots_inew: Dict[str, float],
    slots_enew: Dict[str, float],
    args: argparse.Namespace,
) -> Dict[str, object]:
    hard_checks = [
        {
            "name": "internal_high_risk_rate",
            "value": risk_inew["high_risk_rate"],
            "threshold": args.gate_max_internal_high_risk,
            "op": "<=",
            "passed": risk_inew["high_risk_rate"] <= args.gate_max_internal_high_risk,
        },
        {
            "name": "external_high_risk_rate",
            "value": risk_enew["high_risk_rate"],
            "threshold": args.gate_max_external_high_risk,
            "op": "<=",
            "passed": risk_enew["high_risk_rate"] <= args.gate_max_external_high_risk,
        },
        {
            "name": "internal_allergy_conflict_rate",
            "value": risk_inew["allergy_conflict_rate"],
            "threshold": args.gate_max_internal_allergy_conflict,
            "op": "<=",
            "passed": risk_inew["allergy_conflict_rate"] <= args.gate_max_internal_allergy_conflict,
        },
        {
            "name": "external_allergy_conflict_rate",
            "value": risk_enew["allergy_conflict_rate"],
            "threshold": args.gate_max_external_allergy_conflict,
            "op": "<=",
            "passed": risk_enew["allergy_conflict_rate"] <= args.gate_max_external_allergy_conflict,
        },
    ]

    soft_checks = [
        {
            "name": "internal_three_section_compliance_rate",
            "value": struct_inew["three_section_compliance_rate"],
            "threshold": args.gate_min_internal_three_section,
            "op": ">=",
            "passed": struct_inew["three_section_compliance_rate"] >= args.gate_min_internal_three_section,
        },
        {
            "name": "external_three_section_compliance_rate",
            "value": struct_enew["three_section_compliance_rate"],
            "threshold": args.gate_min_external_three_section,
            "op": ">=",
            "passed": struct_enew["three_section_compliance_rate"] >= args.gate_min_external_three_section,
        },
        {
            "name": "internal_drug_f1",
            "value": slots_inew["drug_f1"],
            "threshold": args.gate_min_internal_drug_f1,
            "op": ">=",
            "passed": slots_inew["drug_f1"] >= args.gate_min_internal_drug_f1,
        },
        {
            "name": "external_drug_f1",
            "value": slots_enew["drug_f1"],
            "threshold": args.gate_min_external_drug_f1,
            "op": ">=",
            "passed": slots_enew["drug_f1"] >= args.gate_min_external_drug_f1,
        },
        {
            "name": "internal_diagnosis_match_rate",
            "value": slots_inew["diagnosis_match_rate"],
            "threshold": args.gate_min_internal_diag_match,
            "op": ">=",
            "passed": slots_inew["diagnosis_match_rate"] >= args.gate_min_internal_diag_match,
        },
        {
            "name": "external_diagnosis_match_rate",
            "value": slots_enew["diagnosis_match_rate"],
            "threshold": args.gate_min_external_diag_match,
            "op": ">=",
            "passed": slots_enew["diagnosis_match_rate"] >= args.gate_min_external_diag_match,
        },
    ]

    hard_passed = all(x["passed"] for x in hard_checks)
    soft_passed = all(x["passed"] for x in soft_checks)
    decision = "pass" if hard_passed else "fail"
    return {
        "enabled": args.enable_release_gate,
        "strict": args.gate_strict,
        "hard_checks": hard_checks,
        "soft_checks": soft_checks,
        "hard_passed": hard_passed,
        "soft_passed": soft_passed,
        "decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extended evaluation metrics for base vs tuned outputs.")
    parser.add_argument("--internal-base", required=True)
    parser.add_argument("--internal-new", required=True)
    parser.add_argument("--external-base", required=True)
    parser.add_argument("--external-new", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--internal-base-tag", default="internal20_base")
    parser.add_argument("--internal-new-tag", default="internal20_run7")
    parser.add_argument("--external-base-tag", default="external23_base")
    parser.add_argument("--external-new-tag", default="external23_run7")
    parser.add_argument("--medical-terms-file", default="", help="Optional txt file with one medical term per line.")
    parser.add_argument("--manual-review-csv", default="", help="Optional CSV output for high-risk manual review samples.")
    parser.add_argument("--manual-review-topk", type=int, default=40)
    parser.add_argument(
        "--manual-review-split",
        default="external_new",
        choices=["internal_new", "external_new", "internal_base", "external_base"],
        help="Which prediction set to use for risk queue export.",
    )
    parser.add_argument("--enable-release-gate", action="store_true", help="Enable release gate checks and report.")
    parser.add_argument("--gate-strict", action="store_true", help="Exit with non-zero code when hard gate fails.")
    parser.add_argument("--gate-max-internal-high-risk", type=float, default=0.05)
    parser.add_argument("--gate-max-external-high-risk", type=float, default=0.10)
    parser.add_argument("--gate-max-internal-allergy-conflict", type=float, default=0.0)
    parser.add_argument("--gate-max-external-allergy-conflict", type=float, default=0.0)
    parser.add_argument("--gate-min-internal-three-section", type=float, default=0.80)
    parser.add_argument("--gate-min-external-three-section", type=float, default=0.30)
    parser.add_argument("--gate-min-internal-drug-f1", type=float, default=0.30)
    parser.add_argument("--gate-min-external-drug-f1", type=float, default=0.20)
    parser.add_argument("--gate-min-internal-diag-match", type=float, default=0.60)
    parser.add_argument("--gate-min-external-diag-match", type=float, default=0.20)
    args = parser.parse_args()

    rows_ib = read_jsonl(Path(args.internal_base), args.internal_base_tag)
    rows_inew = read_jsonl(Path(args.internal_new), args.internal_new_tag)
    rows_eb = read_jsonl(Path(args.external_base), args.external_base_tag)
    rows_enew = read_jsonl(Path(args.external_new), args.external_new_tag)

    ib = summarize(rows_ib)
    inew = summarize(rows_inew)
    eb = summarize(rows_eb)
    enew = summarize(rows_enew)

    terms = load_medical_terms(Path(args.medical_terms_file)) if args.medical_terms_file else set()
    layered_ib = layered_metrics(rows_ib, terms)
    layered_inew = layered_metrics(rows_inew, terms)
    layered_eb = layered_metrics(rows_eb, terms)
    layered_enew = layered_metrics(rows_enew, terms)

    struct_ib = structure_metrics(rows_ib)
    struct_inew = structure_metrics(rows_inew)
    struct_eb = structure_metrics(rows_eb)
    struct_enew = structure_metrics(rows_enew)

    slots_ib = slot_metrics(rows_ib)
    slots_inew = slot_metrics(rows_inew)
    slots_eb = slot_metrics(rows_eb)
    slots_enew = slot_metrics(rows_enew)

    risk_ib = risk_metrics(rows_ib)
    risk_inew = risk_metrics(rows_inew)
    risk_eb = risk_metrics(rows_eb)
    risk_enew = risk_metrics(rows_enew)

    manual_review_csv = args.manual_review_csv.strip()
    if manual_review_csv:
        review_map = {
            "internal_new": rows_inew,
            "external_new": rows_enew,
            "internal_base": rows_ib,
            "external_base": rows_eb,
        }
        export_manual_review(review_map[args.manual_review_split], Path(manual_review_csv), terms, max_rows=args.manual_review_topk)

    out = {
        "internal": {"base": ib, "new": inew, "pdr": compare(ib, inew)},
        "external": {"base": eb, "new": enew, "pdr": compare(eb, enew)},
        "clinical_layered_internal": {
            "base": layered_ib,
            "new": layered_inew,
            "delta": {
                "rouge_l_diagnosis": layered_inew["rouge_l_diagnosis"] - layered_ib["rouge_l_diagnosis"],
                "rouge_l_prescription": layered_inew["rouge_l_prescription"] - layered_ib["rouge_l_prescription"],
                "rouge_l_usage": layered_inew["rouge_l_usage"] - layered_ib["rouge_l_usage"],
                "terminology_recall": layered_inew["terminology_recall"] - layered_ib["terminology_recall"],
            },
        },
        "clinical_layered_external": {
            "base": layered_eb,
            "new": layered_enew,
            "delta": {
                "rouge_l_diagnosis": layered_enew["rouge_l_diagnosis"] - layered_eb["rouge_l_diagnosis"],
                "rouge_l_prescription": layered_enew["rouge_l_prescription"] - layered_eb["rouge_l_prescription"],
                "rouge_l_usage": layered_enew["rouge_l_usage"] - layered_eb["rouge_l_usage"],
                "terminology_recall": layered_enew["terminology_recall"] - layered_eb["terminology_recall"],
            },
        },
        "clinical_layered": {
            "internal": {
                "base": layered_ib,
                "new": layered_inew,
                "delta": {
                    "rouge_l_diagnosis": layered_inew["rouge_l_diagnosis"] - layered_ib["rouge_l_diagnosis"],
                    "rouge_l_prescription": layered_inew["rouge_l_prescription"] - layered_ib["rouge_l_prescription"],
                    "rouge_l_usage": layered_inew["rouge_l_usage"] - layered_ib["rouge_l_usage"],
                    "terminology_recall": layered_inew["terminology_recall"] - layered_ib["terminology_recall"],
                },
            },
            "external": {
                "base": layered_eb,
                "new": layered_enew,
                "delta": {
                    "rouge_l_diagnosis": layered_enew["rouge_l_diagnosis"] - layered_eb["rouge_l_diagnosis"],
                    "rouge_l_prescription": layered_enew["rouge_l_prescription"] - layered_eb["rouge_l_prescription"],
                    "rouge_l_usage": layered_enew["rouge_l_usage"] - layered_eb["rouge_l_usage"],
                    "terminology_recall": layered_enew["terminology_recall"] - layered_eb["terminology_recall"],
                },
            },
        },
        "structure_quality": {
            "internal": {
                "base": struct_ib,
                "new": struct_inew,
                "delta_three_section_compliance": struct_inew["three_section_compliance_rate"] - struct_ib["three_section_compliance_rate"],
            },
            "external": {
                "base": struct_eb,
                "new": struct_enew,
                "delta_three_section_compliance": struct_enew["three_section_compliance_rate"] - struct_eb["three_section_compliance_rate"],
            },
        },
        "clinical_slot_metrics": {
            "internal": {
                "base": slots_ib,
                "new": slots_inew,
                "delta_drug_f1": slots_inew["drug_f1"] - slots_ib["drug_f1"],
                "delta_diagnosis_match_rate": slots_inew["diagnosis_match_rate"] - slots_ib["diagnosis_match_rate"],
            },
            "external": {
                "base": slots_eb,
                "new": slots_enew,
                "delta_drug_f1": slots_enew["drug_f1"] - slots_eb["drug_f1"],
                "delta_diagnosis_match_rate": slots_enew["diagnosis_match_rate"] - slots_eb["diagnosis_match_rate"],
            },
        },
        "risk_screening": {
            "internal": {
                "base": risk_ib,
                "new": risk_inew,
                "delta_high_risk_rate": risk_inew["high_risk_rate"] - risk_ib["high_risk_rate"],
            },
            "external": {
                "base": risk_eb,
                "new": risk_enew,
                "delta_high_risk_rate": risk_enew["high_risk_rate"] - risk_eb["high_risk_rate"],
            },
        },
        "notes": {
            "ece": "Uses proxy confidence=Rouge-L and correctness=F1>=0.5. For strict ECE, store token probabilities.",
            "dpd": "Uses proxy groups inferred by user text gender (male/female).",
            "asr": "Not computed: requires adversarial attack dataset and success labels.",
            "clinical_three_layer": "For internal clinical-risk control: layered ROUGE-L (diagnosis/prescription/usage) + terminology recall + manual review queue.",
        },
    }

    gate_report = evaluate_release_gate(
        risk_inew=risk_inew,
        risk_enew=risk_enew,
        struct_inew=struct_inew,
        struct_enew=struct_enew,
        slots_inew=slots_inew,
        slots_enew=slots_enew,
        args=args,
    )
    out["release_gate"] = gate_report

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# Extended Eval Metrics")
    md.append("")
    md.append("## Internal")
    md.append(f"- Base: EM={ib['exact_match']:.4f}, F1={ib['f1']:.4f}, Rouge-L={ib['rouge_l']:.4f}, BLEU-4={ib['bleu_4']:.4f}, ECE(proxy)={ib['ece_proxy']:.4f}, DPD(proxy)={ib['dpd_proxy']:.4f}")
    md.append(f"- New:  EM={inew['exact_match']:.4f}, F1={inew['f1']:.4f}, Rouge-L={inew['rouge_l']:.4f}, BLEU-4={inew['bleu_4']:.4f}, ECE(proxy)={inew['ece_proxy']:.4f}, DPD(proxy)={inew['dpd_proxy']:.4f}")
    md.append(f"- PDR: pdr_f1={out['internal']['pdr']['pdr_f1']:.4f}, pdr_rouge_l={out['internal']['pdr']['pdr_rouge_l']:.4f}, pdr_bleu_4={out['internal']['pdr']['pdr_bleu_4']:.4f}")
    md.append("")
    md.append("## External")
    md.append(f"- Base: EM={eb['exact_match']:.4f}, F1={eb['f1']:.4f}, Rouge-L={eb['rouge_l']:.4f}, BLEU-4={eb['bleu_4']:.4f}, ECE(proxy)={eb['ece_proxy']:.4f}, DPD(proxy)={eb['dpd_proxy']:.4f}")
    md.append(f"- New:  EM={enew['exact_match']:.4f}, F1={enew['f1']:.4f}, Rouge-L={enew['rouge_l']:.4f}, BLEU-4={enew['bleu_4']:.4f}, ECE(proxy)={enew['ece_proxy']:.4f}, DPD(proxy)={enew['dpd_proxy']:.4f}")
    md.append(f"- PDR: pdr_f1={out['external']['pdr']['pdr_f1']:.4f}, pdr_rouge_l={out['external']['pdr']['pdr_rouge_l']:.4f}, pdr_bleu_4={out['external']['pdr']['pdr_bleu_4']:.4f}")
    md.append("")
    md.append("## Internal Clinical Layered Metrics")
    md.append("- Base: diagnosis_RL={:.4f}, prescription_RL={:.4f}, usage_RL={:.4f}, term_recall={:.4f}, section_coverage={:.2%}".format(
        layered_ib["rouge_l_diagnosis"],
        layered_ib["rouge_l_prescription"],
        layered_ib["rouge_l_usage"],
        layered_ib["terminology_recall"],
        layered_ib["section_coverage_rate"],
    ))
    md.append("- New:  diagnosis_RL={:.4f}, prescription_RL={:.4f}, usage_RL={:.4f}, term_recall={:.4f}, section_coverage={:.2%}".format(
        layered_inew["rouge_l_diagnosis"],
        layered_inew["rouge_l_prescription"],
        layered_inew["rouge_l_usage"],
        layered_inew["terminology_recall"],
        layered_inew["section_coverage_rate"],
    ))
    md.append("- Delta (new-base): diagnosis_RL={:+.4f}, prescription_RL={:+.4f}, usage_RL={:+.4f}, term_recall={:+.4f}".format(
        out["clinical_layered_internal"]["delta"]["rouge_l_diagnosis"],
        out["clinical_layered_internal"]["delta"]["rouge_l_prescription"],
        out["clinical_layered_internal"]["delta"]["rouge_l_usage"],
        out["clinical_layered_internal"]["delta"]["terminology_recall"],
    ))
    md.append("")
    md.append("## External Clinical Layered Metrics")
    md.append("- Base: diagnosis_RL={:.4f}, prescription_RL={:.4f}, usage_RL={:.4f}, term_recall={:.4f}, section_coverage={:.2%}".format(
        layered_eb["rouge_l_diagnosis"],
        layered_eb["rouge_l_prescription"],
        layered_eb["rouge_l_usage"],
        layered_eb["terminology_recall"],
        layered_eb["section_coverage_rate"],
    ))
    md.append("- New:  diagnosis_RL={:.4f}, prescription_RL={:.4f}, usage_RL={:.4f}, term_recall={:.4f}, section_coverage={:.2%}".format(
        layered_enew["rouge_l_diagnosis"],
        layered_enew["rouge_l_prescription"],
        layered_enew["rouge_l_usage"],
        layered_enew["terminology_recall"],
        layered_enew["section_coverage_rate"],
    ))
    md.append("- Delta (new-base): diagnosis_RL={:+.4f}, prescription_RL={:+.4f}, usage_RL={:+.4f}, term_recall={:+.4f}".format(
        out["clinical_layered_external"]["delta"]["rouge_l_diagnosis"],
        out["clinical_layered_external"]["delta"]["rouge_l_prescription"],
        out["clinical_layered_external"]["delta"]["rouge_l_usage"],
        out["clinical_layered_external"]["delta"]["terminology_recall"],
    ))
    md.append("")
    md.append("## Structure Quality")
    md.append("- Internal three_section_compliance: base={:.2%}, new={:.2%}, delta={:+.2%}".format(
        struct_ib["three_section_compliance_rate"],
        struct_inew["three_section_compliance_rate"],
        out["structure_quality"]["internal"]["delta_three_section_compliance"],
    ))
    md.append("- External three_section_compliance: base={:.2%}, new={:.2%}, delta={:+.2%}".format(
        struct_eb["three_section_compliance_rate"],
        struct_enew["three_section_compliance_rate"],
        out["structure_quality"]["external"]["delta_three_section_compliance"],
    ))

    md.append("")
    md.append("## Clinical Slot Metrics")
    md.append("- Internal: diagnosis_match base={:.4f} new={:.4f}; drug_f1 base={:.4f} new={:.4f}".format(
        slots_ib["diagnosis_match_rate"],
        slots_inew["diagnosis_match_rate"],
        slots_ib["drug_f1"],
        slots_inew["drug_f1"],
    ))
    md.append("- External: diagnosis_match base={:.4f} new={:.4f}; drug_f1 base={:.4f} new={:.4f}".format(
        slots_eb["diagnosis_match_rate"],
        slots_enew["diagnosis_match_rate"],
        slots_eb["drug_f1"],
        slots_enew["drug_f1"],
    ))

    md.append("")
    md.append("## Risk Screening")
    md.append("- Internal high_risk_rate: base={:.2%}, new={:.2%}, delta={:+.2%}".format(
        risk_ib["high_risk_rate"],
        risk_inew["high_risk_rate"],
        out["risk_screening"]["internal"]["delta_high_risk_rate"],
    ))
    md.append("- External high_risk_rate: base={:.2%}, new={:.2%}, delta={:+.2%}".format(
        risk_eb["high_risk_rate"],
        risk_enew["high_risk_rate"],
        out["risk_screening"]["external"]["delta_high_risk_rate"],
    ))
    if manual_review_csv:
        md.append(f"- manual_review_csv ({args.manual_review_split}): {manual_review_csv}")
    md.append("")
    md.append("## Notes")
    md.append("- ASR needs dedicated adversarial test sets and success labels, so it is intentionally left uncomputed.")
    md.append("- ECE/DPD are proxy metrics under current data schema; replace with strict definitions when confidence/fairness labels are available.")
    md.append("- Clinical risk control now supports a three-layer mechanism: layered ROUGE-L + terminology recall + manual review queue.")
    md.append("")
    md.append("## Release Gate")
    md.append(f"- enabled={gate_report['enabled']}, strict={gate_report['strict']}, decision={gate_report['decision']}")
    md.append(f"- hard_passed={gate_report['hard_passed']}, soft_passed={gate_report['soft_passed']}")
    md.append("- Hard checks:")
    for item in gate_report["hard_checks"]:
        md.append(
            "  - {}: value={:.4f} {} {:.4f} => {}".format(
                item["name"], item["value"], item["op"], item["threshold"], "PASS" if item["passed"] else "FAIL"
            )
        )
    md.append("- Soft checks:")
    for item in gate_report["soft_checks"]:
        md.append(
            "  - {}: value={:.4f} {} {:.4f} => {}".format(
                item["name"], item["value"], item["op"], item["threshold"], "PASS" if item["passed"] else "FAIL"
            )
        )

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"saved: {out_json}")
    print(f"saved: {out_md}")

    if args.enable_release_gate and args.gate_strict and not gate_report["hard_passed"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
