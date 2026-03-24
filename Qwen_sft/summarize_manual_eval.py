#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from statistics import mean

CSV_PATH = Path('/mnt/public/zxs/course/SFT_qwen/datasets/json/manual_eval_external18_base_vs_run6.csv')
SUMMARY_JSON = Path('/mnt/public/zxs/course/SFT_qwen/datasets/json/manual_eval_external18_summary.json')
REPORT_MD = Path('/mnt/public/zxs/course/SFT_qwen/datasets/json/manual_eval_external18_report.md')
AUTO_SUMMARY = Path('/mnt/public/zxs/course/SFT_qwen/datasets/json/training_replan_eval_summary.json')

SCORE_COLS = {
    'base': {
        'history': 'score_base_history_strict_0_2',
        'hallucination': 'score_base_hallucination_0_2',
        'structure': 'score_base_medication_structure_0_2',
    },
    'ft': {
        'history': 'score_ft_history_strict_0_2',
        'hallucination': 'score_ft_hallucination_0_2',
        'structure': 'score_ft_medication_structure_0_2',
    },
}


def to_num(v):
    v = (v or '').strip()
    if v == '':
        return None
    try:
        x = float(v)
    except Exception:
        return None
    if x < 0 or x > 2:
        return None
    return x


def main():
    rows = list(csv.DictReader(CSV_PATH.open(encoding='utf-8')))
    n = len(rows)

    model_metrics = {
        'base': {'history': [], 'hallucination': [], 'structure': [], 'total': []},
        'ft': {'history': [], 'hallucination': [], 'structure': [], 'total': []},
    }
    per_case = []

    for r in rows:
        rec = {'id': r.get('id', ''), 'valid': True}
        for m in ['base', 'ft']:
            h = to_num(r.get(SCORE_COLS[m]['history']))
            g = to_num(r.get(SCORE_COLS[m]['hallucination']))
            s = to_num(r.get(SCORE_COLS[m]['structure']))
            if h is None or g is None or s is None:
                rec['valid'] = False
            rec[f'{m}_history'] = h
            rec[f'{m}_hallucination'] = g
            rec[f'{m}_structure'] = s
            rec[f'{m}_total'] = (h + g + s) if (h is not None and g is not None and s is not None) else None
        per_case.append(rec)

    valid_cases = [x for x in per_case if x['valid']]

    for x in valid_cases:
        for m in ['base', 'ft']:
            model_metrics[m]['history'].append(x[f'{m}_history'])
            model_metrics[m]['hallucination'].append(x[f'{m}_hallucination'])
            model_metrics[m]['structure'].append(x[f'{m}_structure'])
            model_metrics[m]['total'].append(x[f'{m}_total'])

    winners = {'base': 0, 'ft': 0, 'tie': 0}
    for x in valid_cases:
        if x['base_total'] > x['ft_total']:
            winners['base'] += 1
        elif x['base_total'] < x['ft_total']:
            winners['ft'] += 1
        else:
            winners['tie'] += 1

    def avg(vals):
        return round(mean(vals), 4) if vals else None

    summary = {
        'csv_path': str(CSV_PATH),
        'total_cases': n,
        'valid_scored_cases': len(valid_cases),
        'scoring_complete': len(valid_cases) == n and n > 0,
        'ranking': [],
        'metrics': {
            'base': {
                'history_avg': avg(model_metrics['base']['history']),
                'hallucination_avg': avg(model_metrics['base']['hallucination']),
                'structure_avg': avg(model_metrics['base']['structure']),
                'total_avg': avg(model_metrics['base']['total']),
            },
            'ft': {
                'history_avg': avg(model_metrics['ft']['history']),
                'hallucination_avg': avg(model_metrics['ft']['hallucination']),
                'structure_avg': avg(model_metrics['ft']['structure']),
                'total_avg': avg(model_metrics['ft']['total']),
            },
        },
        'winner_counts': winners,
    }

    scored = []
    for m in ['base', 'ft']:
        t = summary['metrics'][m]['total_avg']
        scored.append((m, -1 if t is None else t))
    scored.sort(key=lambda x: x[1], reverse=True)
    summary['ranking'] = [{'rank': i + 1, 'model': m, 'total_avg': (None if v < 0 else v)} for i, (m, v) in enumerate(scored)]

    if AUTO_SUMMARY.exists():
        summary['auto_eval_reference'] = json.loads(AUTO_SUMMARY.read_text(encoding='utf-8'))

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    lines = []
    lines.append('# 外部18例人工评测汇总报告')
    lines.append('')
    lines.append(f'- 样本总数: {n}')
    lines.append(f'- 已完成人工打分样本: {len(valid_cases)}')

    if len(valid_cases) == 0:
        lines.append('- 当前状态: 尚未填写人工评分，暂无法生成正式排行榜。')
        if 'auto_eval_reference' in summary:
            ext = summary['auto_eval_reference'].get('external_test_metrics', {})
            lines.append('')
            lines.append('## 自动指标参考（非人工评分）')
            for name, metric in ext.items():
                lines.append(f"- {name}: rouge-1={metric.get('rouge-1')}, rouge-2={metric.get('rouge-2')}, rouge-l={metric.get('rouge-l')}, bleu-4={metric.get('bleu-4')}")
        lines.append('')
        lines.append('## 下一步')
        lines.append('- 在 CSV 中填写 6 个评分列（每项 0-2）。')
        lines.append('- 重新运行: python /mnt/public/zxs/course/SFT_qwen/summarize_manual_eval.py')
    else:
        lines.append('')
        lines.append('## 排行榜（人工评分）')
        for r in summary['ranking']:
            lines.append(f"- 第{r['rank']}名: {r['model']} (总分均值={r['total_avg']})")
        lines.append('')
        lines.append('## 分项均值')
        for m in ['base', 'ft']:
            met = summary['metrics'][m]
            lines.append(
                f"- {m}: 病史一致性={met['history_avg']}，幻觉控制={met['hallucination_avg']}，用药结构化={met['structure_avg']}，总分均值={met['total_avg']}"
            )
        lines.append('')
        lines.append('## 逐例胜负统计')
        lines.append(f"- base胜: {winners['base']}")
        lines.append(f"- ft胜: {winners['ft']}")
        lines.append(f"- 平局: {winners['tie']}")

    REPORT_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(SUMMARY_JSON)
    print(REPORT_MD)


if __name__ == '__main__':
    main()
