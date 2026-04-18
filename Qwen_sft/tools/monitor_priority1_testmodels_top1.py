#!/usr/bin/env python3
import json
import time
from datetime import datetime
from pathlib import Path

ROOT = Path('/mnt/public/zxs/course/SFT_qwen')
SUMMARY = ROOT / 'output/ablation_3090_priority1_testmodels/ablation_summary.json'
OUT_MD = ROOT / 'output/ablation_3090_priority1_testmodels/top1_recommendation.md'
LOG = ROOT / 'output/ablation_3090/logs/monitor_priority1_testmodels_top1.log'
LOG.parent.mkdir(parents=True, exist_ok=True)

with LOG.open('a', encoding='utf-8') as f:
    f.write(f"[{datetime.now():%F %T}] monitor started\n")

while True:
    if SUMMARY.exists():
        try:
            obj = json.loads(SUMMARY.read_text(encoding='utf-8'))
            results = obj.get('results', [])
            ranking = obj.get('ranking', [])
            ok_models = [r for r in results if isinstance(r.get('status'), str) and r.get('status').startswith('ok')]
            if len(ok_models) >= 4 and len(ranking) >= 1:
                top = ranking[0]
                lines = [
                    f"# Top1 Online Recommendation ({datetime.now():%F %T})",
                    "",
                    f"- Top1 model: {top.get('model')}",
                    f"- Family: {top.get('family')}",
                    f"- Params (B): {top.get('size_b')}",
                    f"- Weighted score: {top.get('weighted_score')}",
                    f"- Internal F1: {top.get('internal_f1')}",
                    f"- External F1: {top.get('external_f1')}",
                    "",
                    "## Ranking Snapshot",
                ]
                for i, r in enumerate(ranking, 1):
                    lines.append(
                        f"{i}. {r.get('model')} | score={r.get('weighted_score')} | iF1={r.get('internal_f1')} | eF1={r.get('external_f1')} | status={r.get('status')}"
                    )
                OUT_MD.write_text("\n".join(lines) + "\n", encoding='utf-8')
                with LOG.open('a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now():%F %T}] finished: wrote {OUT_MD}\n")
                break
            else:
                with LOG.open('a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now():%F %T}] waiting: ok_models={len(ok_models)} ranking={len(ranking)}\n")
        except Exception as e:
            with LOG.open('a', encoding='utf-8') as f:
                f.write(f"[{datetime.now():%F %T}] parse_error: {e}\n")
    else:
        with LOG.open('a', encoding='utf-8') as f:
            f.write(f"[{datetime.now():%F %T}] waiting: summary missing\n")
    time.sleep(120)
