import json
from pyvis.network import Network

# 读取三元组
with open('extracted_relations_500.json', 'r', encoding='utf-8') as f:
    triples = json.load(f)

# 创建网络
net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")

# 添加节点和边
for trip in triples:
    subj = trip['subject']
    obj = trip['object']
    rel = trip['relation']
    net.add_node(subj, label=subj, title=subj)
    net.add_node(obj, label=obj, title=obj)
    net.add_edge(subj, obj, title=rel, label=rel)

# 设置物理布局（可选，节点会稍微移动）
net.set_options("""
var options = {
  "physics": {"enabled": true},
  "edges": {"smooth": {"type": "continuous"}}
}
""")

net.show("kg_from_relations.html")
print("已生成 kg_from_relations.html，请用浏览器打开。")