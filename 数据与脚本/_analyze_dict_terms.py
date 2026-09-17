# -*- coding: utf-8 -*-
# 分析：从整本Dale词典中筛出"可补进图谱的干净术语"，与现有2739个对比
import json, os, sys, re
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

DESKTOP = r'D:\360MoveData\Users\叶丽娜\Desktop'

# 1. 解析全词典
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

# 2. 现有 clean 术语
data = json.load(open(r'D:\360MoveData\Users\叶丽娜\Desktop\bert\auto_labels_clean.json', encoding='utf-8'))
have = set()
for item in data:
    t = item['term'].lower()
    have.add(t)
    # 括号别名也计入已有
    m = re.search(r'\(([^)]+)\)', item['term'])
    if m and len(m.group(1)) > 3:
        have.add(m.group(1).lower())
print(f"现有术语(含别名): {len(have)}")

# 3. 过滤噪音的术语过滤器
STOP = {'a','an','the','in','on','of','for','and','or','to','by','with','at','from',
        'up','down','out','over','under','all','any','each','more','most','new','old',
        'high','low','long','short','big','small','large','water','air','visual',
        'cold','hot','dry','wet','red','white','black','blue','green','right','left',
        'used','type','unit','control','system','approach','speed','weather','altitude',
        'traffic','display','instrument','information','aviation','key','next','main'}
def is_good_term(t):
    tl = t.lower()
    if len(tl) < 3: return False
    if tl in STOP: return False
    if re.match(r'^[A-Z]{1,3}$', t) and '(' not in t: return False
    if re.match(r'^[A-Z0-9/.-]+$', t) and len(t) <= 3 and '(' not in t: return False
    # 含动词特征的短语不算术语
    if re.search(r'\b(is|are|has|have|was|were|used to|composed of|known as)\b', t, re.I):
        return False
    return True

# 4. 找出"词典里有但现有图谱没有"的干净术语
new_terms = []
for t, d in dict_entries:
    tl = t.lower()
    # 归一化对比
    core = re.sub(r'\s*\([^)]*\)', '', t).strip().lower()
    if tl in have or core in have:
        continue
    if not is_good_term(t):
        continue
    new_terms.append((t, d))

print(f"\n可补进图谱的新术语: {len(new_terms)}")
# 去重（按核心词）
seen_core = set()
uniq_new = []
for t, d in new_terms:
    core = re.sub(r'\s*\([^)]*\)', '', t).strip().lower()
    if core in seen_core:
        continue
    seen_core.add(core)
    uniq_new.append((t, d))
print(f"去重后新术语: {len(uniq_new)}")
print(f"图谱总节点预计: {len(have) + len(uniq_new)}")

# 样例
print("\n新术语样例（前30）:")
for t, d in uniq_new[:30]:
    print(f"  {t}")
