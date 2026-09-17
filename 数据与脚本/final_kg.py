import json
import re
from pyvis.network import Network

# ---------- 1. 读取数据 ----------
with open('annotations_500.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 构建术语字典：term -> definition
term_def = {}
for item in data:
    text = item['data']['text']
    if '.' not in text:
        continue
    term = text.split('.')[0].strip()
    definition = text.split('.', 1)[1].strip()
    term_def[term] = definition

terms = list(term_def.keys())
print(f"共加载 {len(terms)} 个术语")

# ---------- 2. 关系抽取函数（基于正则模式）----------
def extract_relations(term, definition):
    """返回关系列表，每个关系为 (source, target, rel_type)"""
    relations = []
    # 同义词模式
    syn_patterns = [
        r'also called ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'or ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'i\.e\. ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'known as ([A-Za-z0-9\s\(\)\-]+?)[\.\,]'
    ]
    for pat in syn_patterns:
        m = re.search(pat, definition, re.IGNORECASE)
        if m:
            target = m.group(1).strip()
            relations.append((term, target, 'SYNONYM_OF'))
    
    # 上下位模式
    hypo_patterns = [
        r'is a type of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'is a form of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'is a ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'a type of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]'
    ]
    for pat in hypo_patterns:
        m = re.search(pat, definition, re.IGNORECASE)
        if m:
            target = m.group(1).strip()
            relations.append((term, target, 'IS_A'))
    
    # 部分-整体模式
    part_patterns = [
        r'part of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'consists of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'a component of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]'
    ]
    for pat in part_patterns:
        m = re.search(pat, definition, re.IGNORECASE)
        if m:
            target = m.group(1).strip()
            relations.append((term, target, 'PART_OF'))
    
    return relations

# ---------- 3. 构建图 ----------
net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black")
# 设置全局字体为 Times New Roman
net.set_edge_smooth('dynamic')
net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100)

# 添加节点（所有术语）
for term in terms:
    # 将定义作为悬停提示（截取前150字符）
    hover = term_def[term][:150] + '...' if len(term_def[term]) > 150 else term_def[term]
    net.add_node(term, label=term, title=hover, size=20, font='16px "Times New Roman"')

# 添加边（不同类型用不同颜色）
edge_colors = {
    'SYNONYM_OF': 'green',
    'IS_A': 'blue',
    'PART_OF': 'orange'
}
rel_count = 0
for term, definition in term_def.items():
    relations = extract_relations(term, definition)
    for src, tgt, rel_type in relations:
        # 如果目标词也存在于术语集中，则添加边；否则跳过（避免外部节点）
        if tgt in term_def:
            color = edge_colors.get(rel_type, 'gray')
            net.add_edge(src, tgt, title=rel_type, color=color, width=2)
            rel_count += 1

print(f"共添加 {rel_count} 条关系边")

# ---------- 4. 生成 HTML ----------
net.show("aviation_final_kg.html")
print("✅ 知识图谱已生成：aviation_final_kg.html")
