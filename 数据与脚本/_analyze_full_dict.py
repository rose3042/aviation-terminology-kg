# -*- coding: utf-8 -*-
# 分析：用整本Dale词典(14670条)作为匹配池，扫描2739条定义，看能到多少候选对
import json, os, sys, re
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

DESKTOP = r'D:\360MoveData\Users\叶丽娜\Desktop'

# 1. 解析全词典术语名
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

# 词典术语名
dict_terms = [t for t, _ in dict_entries]
print(f"词典术语名: {len(dict_terms)}")

# 2. 加载 clean 术语定义
data = json.load(open(r'D:\360MoveData\Users\叶丽娜\Desktop\bert\auto_labels_clean.json', encoding='utf-8'))
terms = {item['term']: item['definition'] for item in data}
print(f"clean术语定义: {len(terms)}")

# 3. 过滤词典术语名中的明显噪音（普通英文词、太短）
STOP = {'a','an','the','in','on','of','for','and','or','to','by','with','at','from',
        'up','down','out','over','under','all','any','each','more','most','new','old',
        'high','low','long','short','big','small','large','water','air','visual',
        'cold','hot','dry','wet','red','white','black','blue','green','right','left'}
def is_good_term(t):
    tl = t.lower()
    if len(t) < 3: return False
    if tl in STOP: return False
    if re.match(r'^[A-Z]{1,3}$', t): return False  # 裸短缩写
    return True

match_terms = [t for t in dict_terms if is_good_term(t)]
print(f"过滤后可用匹配术语: {len(match_terms)}")

# 括号别名也加入
alias_map = {}
for t in match_terms:
    m = re.search(r'\(([^)]+)\)', t)
    if m and 3 < len(m.group(1)) < 60:
        alias_map[m.group(1).lower()] = t

match_pool = set(match_terms) | set(alias_map.keys())
match_pool = sorted(match_pool, key=len, reverse=True)
print(f"匹配池(含别名): {len(match_pool)}")

# 4. 扫描定义
def make_pattern(name):
    return re.compile(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', re.IGNORECASE)
patterns = {n: make_pattern(n) for n in match_pool}

pairs = set()
occurrences = Counter()
for subj, definition in terms.items():
    for name in match_pool:
        if name.lower() == subj.lower():
            continue
        if patterns[name].search(definition):
            canon = alias_map.get(name.lower(), name)
            if canon.lower() == subj.lower():
                continue
            pair = tuple(sorted([subj, canon]))
            if pair not in pairs:
                pairs.add(pair)
                occurrences[canon] += 1

print(f"\n=== 全词典匹配池扫描结果 ===")
print(f"候选关系对: {len(pairs)}")
print(f"涉及术语数: {len(set(n for p in pairs for n in p))}")
print(f"被提最多 Top20:")
for t, c in occurrences.most_common(20):
    print(f"  {c:5d}  {t}")
