# -*- coding: utf-8 -*-
"""
T5：关系质量人工审定抽样表生成
从 merged_relations.json（2475 条）按 12 类关系类型分层随机抽 100 条，
导出 csv（UTF-8 BOM，WPS/Excel 双击直接打开不乱码），附 LLM 依据原文 evidence，
留两列人工填写：判定（对/错/不确定）与备注。
用法：python _sample_relations_for_review.py
"""
import json, random, csv, sys, os
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__)); os.chdir(BASE)
random.seed(20260830)          # 固定种子，可复现

N = 100
d = json.load(open('merged_relations.json', encoding='utf-8'))
by_rel = {}
for r in d:
    by_rel.setdefault(r['relation'], []).append(r)
total = len(d)
print(f'总关系数 {total}，类型 {len(by_rel)} 种')

# 分层：每类至少 2 条，其余按占比分配
order = sorted(by_rel.items(), key=lambda kv: -len(kv[1]))
counts = {rel: max(2, int(N * len(lst) / total)) for rel, lst in order}
remain = N - sum(counts.values())
for rel, _ in order:
    if remain <= 0:
        break
    add = min(remain, len(by_rel[rel]) - counts[rel])
    counts[rel] += add
    remain -= add

samples = []
for rel, n in counts.items():
    picked = random.sample(by_rel[rel], n)
    samples.extend(picked)
    print(f'  {rel:<14} 抽 {n} 条（共 {len(by_rel[rel])}）')
random.shuffle(samples)
assert len(samples) == N

with open('关系人工审定抽样_100条.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['序号', 'subject', 'relation', 'object', 'confidence',
                'LLM依据原文(evidence)', '判定(对/错/不确定)', '备注'])
    for i, r in enumerate(samples, 1):
        ev = (r.get('evidence') or '').replace('\n', ' ').replace('\r', ' ').strip()
        w.writerow([i, r['subject'], r['relation'], r['object'], r.get('confidence', ''),
                    ev, '', ''])
print(f'\n已生成 关系人工审定抽样_100条.csv（{N} 条，WPS 打开即可填写判定列）')
