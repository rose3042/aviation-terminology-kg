import json
import networkx as nx
import matplotlib.pyplot as plt

# 读取你的标注数据
with open('annotations_500.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 取前 60 个术语作为示例（可以改成全部，但节点太多会看不清）
terms = []
for item in data[:60]:
    term = item['data']['text'].split('.')[0].strip()
    terms.append(term)

# 创建图
G = nx.Graph()
G.add_nodes_from(terms)

# 为相邻的术语建立一条边（也可以根据你的业务逻辑修改）
for i in range(len(terms)-1):
    G.add_edge(terms[i], terms[i+1])

# 画图
plt.figure(figsize=(16, 12))
pos = nx.spring_layout(G, seed=42)  # 布局算法
nx.draw(G, pos, with_labels=True, node_size=2000, node_color='lightblue', 
        font_size=8, font_weight='bold', edge_color='gray')

# 保存高清图片
plt.savefig('term_knowledge_graph.png', dpi=300, bbox_inches='tight')
plt.show()
print("知识图谱图片已生成：term_knowledge_graph.png")