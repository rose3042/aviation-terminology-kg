import json
import re
from pyvis.network import Network

# 读取标注数据
with open('annotations_500.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 存储所有术语节点
terms = {}
for item in data:
    text = item['data']['text']
    term = text.split('.')[0].strip()
    definition = text.split('.', 1)[1].strip()
    terms[term] = definition

# 关系抽取函数（简单规则）
def extract_relations(term, definition):
    relations = []
    # 1. 同义词：定义中出现 "also called", "or", "i.e." 后面跟一个术语
    synonym_patterns = [
        r'also called ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'or ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'i\.e\. ([A-Za-z0-9\s\(\)\-]+?)[\.\,]'
    ]
    for pat in synonym_patterns:
        match = re.search(pat, definition, re.IGNORECASE)
        if match:
            synonym = match.group(1).strip()
            relations.append((term, synonym, 'SYNONYM_OF'))
    
    # 2. 上下位关系：定义中出现 "is a type of", "is a form of", "is a"
    hyponym_patterns = [
        r'is a type of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'is a form of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'is a ([A-Za-z0-9\s\(\)\-]+?)[\.\,]'
    ]
    for pat in hyponym_patterns:
        match = re.search(pat, definition, re.IGNORECASE)
        if match:
            hypernym = match.group(1).strip()
            relations.append((term, hypernym, 'IS_A'))
    
    # 3. 部分-整体关系：定义中出现 "part of", "consists of"
    part_patterns = [
        r'part of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]',
        r'consists of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]'
    ]
    for pat in part_patterns:
        match = re.search(pat, definition, re.IGNORECASE)
        if match:
            whole = match.group(1).strip()
            relations.append((term, whole, 'PART_OF'))
    
    return relations

# 构建图
net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
net.set_options("""
var options = {
  "nodes": {
    "font": {"size": 14}
  },
  "edges": {
    "smooth": {"type": "continuous"}
  },
  "physics": {"enabled": true}
}
""")

# 添加节点
for term in terms:
    net.add_node(term, label=term, title=terms[term][:100], size=20)

# 添加边（关系）
relation_colors = {
    'SYNONYM_OF': 'green',
    'IS_A': 'blue',
    'PART_OF': 'orange'
}
for term, definition in terms.items():
    relations = extract_relations(term, definition)
    for src, tgt, rel_type in relations:
        if src in terms and tgt in terms:
            net.add_edge(src, tgt, title=rel_type, color=relation_colors.get(rel_type, 'gray'), width=2)
        else:
            # 目标词可能不在当前节点集中，可以添加为临时节点（灰色）
            net.add_node(tgt, label=tgt, title="外部概念", size=15, color='lightgray')
            net.add_edge(src, tgt, title=rel_type, color=relation_colors.get(rel_type, 'gray'), width=2, dashes=True)

# 保存为 HTML
net.show("aviation_knowledge_graph.html")
print("交互式知识图谱已生成：aviation_knowledge_graph.html")