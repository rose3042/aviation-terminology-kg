# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
rels = json.load(open(r'D:\360MoveData\Users\叶丽娜\Desktop\bert\relations.json', encoding='utf-8'))
good = [r for r in rels if r['relation'] != 'none']
print(f"有用关系 {len(good)} 条，按类型:")
from collections import Counter
c = Counter(r['relation'] for r in good)
for k, v in c.most_common():
    print(f"  {k}: {v}")
print("\n--- 各类示例 ---")
for rel in ['defined_by','part_of','is_a','synonym_of','used_for','measures']:
    ex = [r for r in good if r['relation']==rel]
    if ex:
        print(f"\n[{rel}]")
        for r in ex[:5]:
            print(f"  {r['subject']} → {r['object']}  conf={r['confidence']}")
