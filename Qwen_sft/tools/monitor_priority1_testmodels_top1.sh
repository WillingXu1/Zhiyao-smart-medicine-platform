#!/usr/bin/env bash
set -euo pipefail

ROOT="/mnt/public/zxs/course/SFT_qwen"
SUMMARY="$ROOT/results/output/ablation_3090_priority1_testmodels/ablation_summary.json"
OUT_MD="$ROOT/results/output/ablation_3090_priority1_testmodels/top1_recommendation.md"
LOG="$ROOT/results/output/ablation_3090/logs/monitor_priority1_testmodels_top1.log"

mkdir -p "$ROOT/results/output/ablation_3090/logs"

echo "[$(date '+%F %T')] monitor started" >> "$LOG"

while true; do
  if [[ -f "$SUMMARY" ]]; then
    python - <<'PY' "$SUMMARY" "$OUT_MD" "$LOG"
import json, sys, datetime
summary, out_md, log = sys.argv[1], sys.argv[2], sys.argv[3]
obj = json.load(open(summary, 'r', encoding='utf-8'))
results = obj.get('results', [])
ranking = obj.get('ranking', [])
ok_models = [r for r in results if isinstance(r.get('status'), str) and r.get('status').startswith('ok')]
# Expect 4 rows: 1 reused qwen + 3 newly trained models
if len(ok_models) < 4 or len(ranking) < 1:
    with open(log, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.datetime.now():%F %T}] waiting: ok_models={len(ok_models)} ranking={len(ranking)}\n")
    raise SystemExit(2)

top = ranking[0]
lines = []
lines.append(f"# Top1 Online Recommendation ({datetime.datetime.now():%F %T})")
lines.append("")
lines.append(f"- Top1 model: {top.get('model')}")
lines.append(f"- Family: {top.get('family')}")
lines.append(f"- Params (B): {top.get('size_b')}")
lines.append(f"- Weighted score: {top.get('weighted_score')}")
lines.append(f"- Internal F1: {top.get('internal_f1')}")
lines.append(f"- External F1: {top.get('external_f1')}")
lines.append("")
lines.append("## Ranking Snapshot")
for i, r in enumerate(ranking, 1):
    lines.append(f"{i}. {r.get('model')} | score={r.get('weighted_score')} | iF1={r.get('internal_f1')} | eF1={r.get('external_f1')} | status={r.get('status')}")

with open(out_md, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines) + "\n")
with open(log, 'a', encoding='utf-8') as f:
    f.write(f"[{datetime.datetime.now():%F %T}] finished: wrote {out_md}\n")
PY
    if [[ $? -eq 0 ]]; then
      break
    fi
  else
    echo "[$(date '+%F %T')] waiting: summary missing" >> "$LOG"
  fi
  sleep 120
done
