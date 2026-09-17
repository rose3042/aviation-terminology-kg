# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
rels = json.load(open(r'D:\360MoveData\Users\叶丽娜\Desktop\bert\relations.json', encoding='utf-8'))
none_list = [r for r in rels if r['relation'] == 'none']
print(f"none 共 {len(none_list)} 条，示例:")
for r in none_list[:20]:
    print(f"  [{r['subject']}] → [{r['object']}]  conf={r['confidence']}")
