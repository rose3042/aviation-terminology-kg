# -*- coding: utf-8 -*-
"""
合并全部关系（基础12类 + 核心子图12类 + See交叉参照），去重，输出统一关系文件。
用法：python merge_relations.py
输出：merged_relations.json, merged_stats.json
"""
import json, os, sys, re
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

def load(fn, default=None):
    if os.path.exists(fn):
        with open(fn, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

base = load('relations_base_v2.json', [])
core = load('relations_core_v2.json', [])
see = load('see_also_pairs.json', [])
full = load('relations_full.json', [])   # 整本Dale词典匹配池挖出的关系（几千条）

print(f"基础12类: {len(base)} | 核心12类: {len(core)} | See: {len(see)} | 全词典: {len(full)}")

# 归一化术语名（去括号全称差异、去标点、小写）
def norm(t):
    import re
    t = re.sub(r'\s*\([^)]*\)', ' ', t or '').strip().lower()
    t = re.sub(r'[^a-z0-9 ]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

# 合并去重（同一 subject-relation-object 只留一条，用置信度最高的）
merged = {}

# 自连接过滤（ARTS -> ARTS (automated radar terminal systems) 这类归一化后自指的）
# 通用对象词过滤（systems/equipment 等刷屏噪音）
GENERIC_OBJ = {'systems', 'equipment', 'component', 'components', 'devices',
               'unit', 'units', 'operation', 'operations', 'process', 'processes',
               'method', 'methods', 'procedure', 'procedures', 'technique',
               'techniques', 'material', 'materials', 'condition', 'conditions'}

def add(subj, rel, obj, conf, source, evidence=''):
    if rel == 'none':
        return
    ns, no = norm(subj), norm(obj)
    if ns == no:          # 自循环噪音
        return
    if no in GENERIC_OBJ:  # 通用词对象噪音
        return
    if re.match(r'^(a|an|the)\s+[a-z]', no):  # 带冠词短语（a computer）噪音
        return
    key = (ns, rel, no)
    entry = {
        'subject': subj, 'relation': rel, 'object': obj,
        'confidence': conf, 'source': source, 'evidence': evidence,
    }
    if key not in merged or merged[key]['confidence'] < conf:
        merged[key] = entry

# 基础
for r in base:
    add(r.get('subject'), r.get('relation'), r.get('object'),
        r.get('confidence', 0), 'base', r.get('evidence', ''))
# 核心
for r in core:
    add(r.get('subject'), r.get('relation'), r.get('object'),
        r.get('confidence', 0), 'core', r.get('evidence', ''))
# See 交叉参照（关系类型定为 synonym_of 近似 / see_also）
for r in see:
    if r.get('resolved'):
        add(r.get('subject'), 'synonym_of', r.get('object'), 0.9, 'see', '')
# 全词典匹配池（来源 full）
for r in full:
    add(r.get('subject'), r.get('relation'), r.get('object'),
        r.get('confidence', 0), 'full', r.get('evidence', ''))

result = list(merged.values())
print(f"合并后有效关系: {len(result)}")

# 统计
dist = Counter(r['relation'] for r in result)
src = Counter(r['source'] for r in result)
print("关系分布:", dict(dist))
print("来源分布:", dict(src))

with open('merged_relations.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=1, ensure_ascii=False)
with open('merged_stats.json', 'w', encoding='utf-8') as f:
    json.dump({'total': len(result), 'dist': dict(dist), 'source': dict(src)},
              f, indent=1, ensure_ascii=False)

# 节点数
nodes = set()
for r in result:
    nodes.add(r['subject']); nodes.add(r['object'])
print(f"涉及节点数: {len(nodes)}, 密度(边/节点): {len(result)/len(nodes):.2f}")
