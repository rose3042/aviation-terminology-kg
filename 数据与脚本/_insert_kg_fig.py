# -*- coding: utf-8 -*-
"""把知识图谱可视化图（_fig/fig13_kg_overall.png）作为 Figure 8 / 图8 插入三个稿件 §4.6。
位置：Figure 7（图谱规模）图题之后、Table 8 之前。"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

EN_ANCHOR = "*Figure 7. Scale of the knowledge graph before (base version, 352 nodes / 388 edges) and after (full-dictionary pool, 2,184 nodes / 2,475 edges).*"
ZH_ANCHOR = "*图7. 知识图谱的规模：扩展前（基础版，352节点/388边）与扩展后（全词典池，2,184节点/2,475边）。*"

EN_BLOCK = """

The resulting graph is visualized in Figure 8.

![Aviation terminology knowledge graph](_fig/fig13_kg_overall.png)

*Figure 8. Visualization of the full aviation terminology knowledge graph (2,184 nodes, 2,475 edges). Node color encodes degree tier: dark red = core hubs (degree ≥ 6), blue = important terms (degree 3–5), light gray = peripheral terms (degree < 3); the five highest-degree hubs (e.g., RADAR) are labeled.*
"""

ZH_BLOCK = """

图谱本体见图8。

![航空术语知识图谱](_fig/fig13_kg_overall.png)

*图8. 完整航空术语知识图谱的可视化（2,184个节点，2,475条边）。节点颜色表示度数层级：深红＝核心枢纽（度数≥6），蓝色＝重要术语（度数3–5），浅灰＝一般术语（度数<3）；度数最高的五个枢纽（如RADAR）已标注。*
"""

def insert(path, anchor, block, tag, marker):
    t = open(path, encoding='utf-8').read()
    n = t.count(anchor)
    assert n == 1, f'[{tag}] 锚点命中 {n} 次（应恰为1）: {anchor[:60]!r}'
    assert marker not in t, f'[{tag}] 已存在 {marker!r}，跳过不重复插入'
    t = t.replace(anchor, anchor + block)
    open(path, 'w', encoding='utf-8').write(t)
    print(f'✓ [{tag}] 已插入 {marker}')

insert('论文_英文稿_ESP.md',   EN_ANCHOR, EN_BLOCK, '英文ESP',  'Figure 8.')
insert('论文_英文稿_Lingua.md', EN_ANCHOR, EN_BLOCK, '英文Lingua','Figure 8.')
insert('论文_中文稿_ESP.md',   ZH_ANCHOR, ZH_BLOCK, '中文',     '图8.')
print('全部完成')
