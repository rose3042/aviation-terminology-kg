# -*- coding: utf-8 -*-
# 清理核心术语：去掉明显噪音，重生成 core_pairs.json
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

core = json.load(open(r'D:\360MoveData\Users\叶丽娜\Desktop\bert\core_terms.json', encoding='utf-8'))
terms = {item['term']: item['definition'] for item in json.load(open(r'D:\360MoveData\Users\叶丽娜\Desktop\bert\auto_labels_clean.json', encoding='utf-8'))}

# 手工噪音黑名单（这些不是好的枢纽术语）
NOISE = {
    'Technology', 'America', 'United States', 'Mercator projection (navigation)',
    'North Pacific (air traffic control)', 'Irish linen (aircraft fabric)',
    'Heaviside layer (atmosphere)', 'Cuno filter (fluid filter)', 'Dacron',
}
# 手工枢纽补充（公认的航空核心）
HUB_ADD = [
    'aircraft', 'engine', 'airport', 'flight', 'pilot', 'fuel', 'wing',
    'navigation', 'communication', 'radar', 'weather', 'safety', 'maintenance',
    'control', 'pressure', 'temperature', 'speed', 'altitude', 'airspace',
    'avionics', 'hydraulic', 'propeller', 'turbine', 'aircraft',
]

clean = [t for t in core if t not in NOISE]
# 加入 HUB_ADD 中存在于 terms 的
for hub in HUB_ADD:
    for term in terms:
        if term.lower() == hub:
            if term not in clean:
                clean.append(term)
            break
    else:
        for term in terms:
            if hub in term.lower() and len(term) < 35:
                if term not in clean:
                    clean.append(term)
                break

# 去重保序
seen = set()
clean2 = []
for t in clean:
    if t.lower() not in seen:
        seen.add(t.lower())
        clean2.append(t)
clean = clean2

print(f"清理后核心术语: {len(clean)}")
from itertools import combinations
pairs = []
for a, b in combinations(clean, 2):
    pairs.append({"subject": a, "object": b, "subject_def": terms.get(a, "")})
print(f"两两配对: {len(pairs)} 对")

json.dump(clean, open(r'D:\360MoveData\Users\叶丽娜\Desktop\bert\core_terms.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
json.dump(pairs, open(r'D:\360MoveData\Users\叶丽娜\Desktop\bert\core_pairs.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print("已更新 core_terms.json / core_pairs.json")
