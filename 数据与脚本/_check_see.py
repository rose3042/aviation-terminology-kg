# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
s = json.load(open(r'D:\360MoveData\Users\叶丽娜\Desktop\bert\see_also_pairs.json', encoding='utf-8'))
resolved = [x for x in s if x.get('resolved')]
unresolved = [x for x in s if not x.get('resolved')]
print('See总数:', len(s), '| 已解析(可导入):', len(resolved), '| 未解析:', len(unresolved))
print('--- 已解析示例 ---')
for x in resolved[:10]:
    print(f"  {x['subject']} --see_also--> {x['object']}")
print('--- 未解析示例 ---')
for x in unresolved[:10]:
    print(f"  {x['subject']} --see_also--> {x['object']}")
