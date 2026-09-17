# -*- coding: utf-8 -*-
"""
第一步（全词典版）：用整本 Dale 词典(14670条术语)做匹配池，扫描2739条定义，挖出几千条候选关系。
关键改进：
  1. 匹配池 = 全词典术语 + 括号别名（比只用clean术语覆盖广得多）
  2. 通用词停用表：过滤 system/control/used 等非航空术语的噪音对象
  3. 只保留"定义里明确提到"的配对，确保有依据
输出：cooccurrence_pairs_full.json（含 subject_def）
"""
import json, os, sys, re
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
DESKTOP = r'D:\360MoveData\Users\叶丽娜\Desktop'
os.chdir(BASE)

# ------------------------------------------------------------------
# 1. 解析全词典
# ------------------------------------------------------------------
def parse_dictionary(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^([A-Za-z][A-Za-z0-9\- ]*?(?:\([^)]+\))?)\.\s+(.+)$', line)
        if m:
            term, definition = m.group(1).strip(), m.group(2).strip()
            if 2 <= len(term) <= 60 and len(definition) >= 8:
                entries.append((term, definition))
    seen = set()
    uniq = []
    for t, d in entries:
        tl = t.lower()
        if tl in seen:
            continue
        seen.add(tl)
        uniq.append((t, d))
    return uniq

dict_entries = None
for fn in ['dictionary_clean.txt', 'dictionary_full.txt']:
    p = os.path.join(DESKTOP, fn)
    if os.path.exists(p):
        dict_entries = parse_dictionary(p)
        print(f"词典 {fn}: {len(dict_entries)} 条")
        break
if dict_entries is None:
    raise FileNotFoundError("找不到词典文件")

# 词典术语 -> 定义
dict_def = {t.lower(): d for t, d in dict_entries}

# ------------------------------------------------------------------
# 2. 通用词停用表（这些词不能作为"被关联对象"，否则全是噪音）
# ------------------------------------------------------------------
GENERIC_STOP = {
    'system', 'used', 'type', 'unit', 'control', 'approach', 'speed',
    'weather', 'altitude', 'traffic', 'display', 'instrument', 'information',
    'aviation', 'aircraft', 'airport', 'flight', 'navigation', 'frequency',
    'operation', 'condition', 'device', 'equipment', 'material', 'component',
    'part', 'process', 'method', 'procedure', 'technique', 'device',
    'a', 'an', 'the', 'in', 'on', 'of', 'for', 'and', 'or', 'to', 'by',
    'with', 'at', 'from', 'up', 'down', 'out', 'over', 'under', 'all',
    'any', 'each', 'more', 'most', 'new', 'old', 'high', 'low', 'long',
    'short', 'big', 'small', 'large', 'water', 'air', 'visual', 'cold',
    'hot', 'dry', 'wet', 'red', 'white', 'black', 'blue', 'green',
    'right', 'left', 'used to', 'per hour', 'meter', 'second', 'minute',
    'hour', 'degree', 'number', 'value', 'point', 'line', 'area', 'center',
}

def is_generic(name):
    n = name.lower().strip().strip('.')
    if n in GENERIC_STOP:
        return True
    # 单/双通用词
    if len(n) <= 4 and n in GENERIC_STOP:
        return True
    return False

# ------------------------------------------------------------------
# 3. 构建匹配池
# ------------------------------------------------------------------
# 词典术语名（含括号全称）
match_terms = [t for t, _ in dict_entries]
alias_map = {}
for t in match_terms:
    m = re.search(r'\(([^)]+)\)', t)
    if m and 3 < len(m.group(1)) < 60:
        alias_map[m.group(1).lower()] = t

# 只保留"够格"的术语参与匹配（长度>=3、非裸短缩写、非通用词）
def is_qualified(name):
    if is_generic(name):
        return False
    if len(name.strip()) < 3:
        return False
    if re.match(r'^[A-Z]{1,3}$', name) and '(' not in name:
        return False
    return True

match_pool = set()
for t in match_terms:
    if is_qualified(t):
        match_pool.add(t)
    # 别名（括号全称）参与匹配
    m = re.search(r'\(([^)]+)\)', t)
    if m and len(m.group(1)) >= 5:
        match_pool.add(m.group(1))

match_pool = sorted(match_pool, key=len, reverse=True)
print(f"匹配池(过滤通用词后): {len(match_pool)}")

# 反向：对象术语 -> 定义（用于结果）
def canon_name(name):
    return alias_map.get(name.lower(), name)

# ------------------------------------------------------------------
# 4. 扫描定义
# ------------------------------------------------------------------
data = json.load(open('auto_labels_clean.json', 'r', encoding='utf-8'))
terms = {item['term']: item['definition'] for item in data}

def make_pattern(name):
    return re.compile(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', re.IGNORECASE)

# 预编译（只对长度>=4的，减少开销）
patterns = {}
for name in match_pool:
    if len(name) >= 4:
        patterns[name] = make_pattern(name)

pairs = set()
occurrences = Counter()
for subj, definition in terms.items():
    dl = definition.lower()
    for name, pat in patterns.items():
        if name.lower() == subj.lower():
            continue
        if pat.search(dl):
            canon = canon_name(name)
            if canon.lower() == subj.lower():
                continue
            # 对象不能是通用词
            if is_generic(canon):
                continue
            pair = tuple(sorted([subj, canon]))
            if pair not in pairs:
                pairs.add(pair)
                occurrences[canon] += 1

print(f"候选关系对: {len(pairs)}")
print(f"涉及术语数: {len(set(n for p in pairs for n in p))}")

# 保存
out = []
for s, o in sorted(pairs):
    # 对象定义（优先用clean，其次词典）
    obj_def = terms.get(o, '') or dict_def.get(o.lower(), '')
    out.append({"subject": s, "object": o, "subject_def": terms[s]})

with open('cooccurrence_pairs_full.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(f"已保存 cooccurrence_pairs_full.json ({len(out)} 对)")

# 高频被提（验证没有通用词刷屏）
print("\n被提最多的术语 Top20:")
for t, c in occurrences.most_common(20):
    print(f"  {c:5d}  {t}")
