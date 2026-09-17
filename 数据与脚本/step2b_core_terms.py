# -*- coding: utf-8 -*-
"""
第二步B：核心术语子图（申博代表作的核心）
选出 N 个"枢纽术语"（被定义提到最多、连接度最高），两两配对送 DeepSeek 分类，
从语义上把图谱密度拉高（目标：>1.0）。

两轮策略（避免一次性 5000 对太贵）：
  轮1: 选 TOP 80 个枢纽术语，两两配对 (80*79/2 = 3160 对)，成本 ~¥15-25
  轮2（可选）: 轮1 里涌现的"高频相连"术语再加深
本脚本：先输出核心术语清单和两两配对文件，供 step2 用。
"""
import json, os, sys, re
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

with open('auto_labels_clean.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
terms = {item['term']: item['definition'] for item in data}

# ------------------------------------------------------------------
# 1. 统计"被提到最多"的术语（连接中心）
# ------------------------------------------------------------------
# 先构建可匹配名字（含多词括号全称）
def is_qualified_name(name):
    n = name.strip()
    if not n:
        return False
    if len(n) > 40 and ' ' in n:
        return False
    if re.search(r'\b(is|are|has|have|was|were|used to|composed of)\b', n, re.I):
        return False
    if re.match(r'^[A-Z]{1,3}$', n) and '(' not in n:
        return False
    if len(n) < 3 and '(' not in n:
        return False
    return True

qualified = [t for t in terms if is_qualified_name(t)]

# 别名（多词全称）
alias_map = {}
for term in qualified:
    m = re.search(r'\(([^)]+)\)', term)
    if m:
        alias = m.group(1).strip()
        if 3 < len(alias) < 60 and (' ' in alias or '-' in alias or len(alias) >= 6):
            alias_map[alias.lower()] = term

match_names = list(qualified) + list(alias_map.keys())
match_names.sort(key=len, reverse=True)
uniq = []
seen = set()
for n in match_names:
    if n.lower() in seen:
        continue
    seen.add(n.lower())
    uniq.append(n)

def make_pattern(name):
    return re.compile(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', re.IGNORECASE)
patterns = {n: make_pattern(n) for n in uniq}

# 统计被提到次数
occurrences = Counter()
for subj in qualified:
    definition = terms[subj]
    for name in uniq:
        if name.lower() == subj.lower():
            continue
        if patterns[name].search(definition):
            canon = alias_map.get(name.lower(), name)
            if canon != subj:
                occurrences[canon] += 1

print("被提到次数最多的核心术语（连接中心）Top 80:")
for i, (t, c) in enumerate(occurrences.most_common(80), 1):
    print(f"  {i:3d}. {t}  ({c}次)")

# 手工补充：航空领域公认的枢纽术语（即使定义里被提次数不多）
HUB_EXTRA = [
    "aircraft", "engine", "airport", "flight", "pilot", "fuel", "wing",
    "propeller", "navigation", "communication", "radar", "weather",
    "safety", "maintenance", "control", "pressure", "temperature",
    "speed", "altitude", "airspace", "avionics", "hydraulic",
]

# 输出核心术语清单
core = [t for t, _ in occurrences.most_common(80)]
# 加入手工补充的（如果存在于 terms）
for hub in HUB_EXTRA:
    # 尝试精确或包含匹配
    for term in terms:
        if term.lower() == hub:
            if term not in core:
                core.append(term)
            break
    else:
        # 模糊匹配：terms 里包含该词的关键术语
        for term in qualified:
            if hub in term.lower() and len(term) < 35:
                if term not in core:
                    core.append(term)
                break

print(f"\n最终核心术语数: {len(core)}")
with open('core_terms.json', 'w', encoding='utf-8') as f:
    json.dump(core, f, indent=1, ensure_ascii=False)

# ------------------------------------------------------------------
# 2. 两两配对（组合），生成候选对文件
# ------------------------------------------------------------------
from itertools import combinations
core_pairs = []
for a, b in combinations(core, 2):
    core_pairs.append({
        "subject": a, "object": b,
        "subject_def": terms.get(a, "")
    })
print(f"核心术语两两配对: {len(core_pairs)} 对")
with open('core_pairs.json', 'w', encoding='utf-8') as f:
    json.dump(core_pairs, f, indent=1, ensure_ascii=False)
print("已保存 core_terms.json 和 core_pairs.json")
