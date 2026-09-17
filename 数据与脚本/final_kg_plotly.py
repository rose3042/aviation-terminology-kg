import json
import re
import plotly.graph_objects as go
import networkx as nx

# 1. 读取数据
with open('annotations_500.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

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

# 2. 关系抽取（改为共现关联 + 少量规则）
def extract_relations(term, definition, all_terms):
    relations = []
    # 2.1 同义词模式（如果存在）
    syn_pats = [r'also called ([A-Za-z0-9\s\(\)\-]+?)[\.\,]', r'or ([A-Za-z0-9\s\(\)\-]+?)[\.\,]']
    for pat in syn_pats:
        m = re.search(pat, definition, re.IGNORECASE)
        if m:
            target = m.group(1).strip()
            if target in all_terms:
                relations.append((term, target, 'SYNONYM_OF'))
    # 2.2 上下位模式
    hypo_pats = [r'is a type of ([A-Za-z0-9\s\(\)\-]+?)[\.\,]', r'is a ([A-Za-z0-9\s\(\)\-]+?)[\.\,]']
    for pat in hypo_pats:
        m = re.search(pat, definition, re.IGNORECASE)
        if m:
            target = m.group(1).strip()
            if target in all_terms:
                relations.append((term, target, 'IS_A'))
    # 2.3 共现关联：如果定义中包含其他术语名称（且不是自己），添加 RELATED 边
    for other in all_terms:
        if other != term and other.lower() in definition.lower():
            # 避免重复添加同一条边（无向）
            if (other, term, 'RELATED') not in relations and (term, other, 'RELATED') not in relations:
                relations.append((term, other, 'RELATED'))
    return relations

# 构建图
G = nx.Graph()
G.add_nodes_from(terms)

edge_type_color = {'SYNONYM_OF': 'green', 'IS_A': 'blue', 'RELATED': 'lightgray', 'PART_OF': 'orange'}
edge_list = []
for term, definition in term_def.items():
    rels = extract_relations(term, definition, terms)
    for src, tgt, rtype in rels:
        if not G.has_edge(src, tgt):   # 避免重复
            G.add_edge(src, tgt, label=rtype, color=edge_type_color.get(rtype, 'gray'))
            edge_list.append((src, tgt, rtype))

print(f"共添加 {len(edge_list)} 条关系边")

# 布局
pos = nx.spring_layout(G, seed=42, k=2, iterations=50)

# 按颜色分组边迹
traces = []
colors_done = set()
for color in edge_type_color.values():
    x_vals, y_vals = [], []
    has_edge = False
    for src, tgt, rtype in edge_list:
        if edge_type_color.get(rtype, 'gray') == color:
            x0, y0 = pos[src]
            x1, y1 = pos[tgt]
            x_vals.extend([x0, x1, None])
            y_vals.extend([y0, y1, None])
            has_edge = True
    if has_edge:
        traces.append(go.Scatter(
            x=x_vals, y=y_vals,
            mode='lines',
            line=dict(width=1.5, color=color),
            hoverinfo='none',
            name=f'{color} edges'
        ))

# 节点迹
node_x = [pos[node][0] for node in terms]
node_y = [pos[node][1] for node in terms]
node_text = terms
node_hover = [term_def[node][:120] + '...' if len(term_def[node]) > 120 else term_def[node] for node in terms]

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers+text',
    text=node_text,
    textposition='top center',
    hovertext=node_hover,
    hoverinfo='text',
    marker=dict(size=18, color='lightblue', line=dict(width=1, color='darkblue')),
    textfont=dict(family='Times New Roman', size=12, color='black')
)

# 绘图
fig = go.Figure(data=traces + [node_trace],
                layout=go.Layout(
                    title=dict(text='航空术语知识图谱 (500个术语)', font=dict(size=18, family='Times New Roman')),
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=50),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    font=dict(family='Times New Roman')
                ))

fig.write_html("aviation_kg_500.html")
print("✅ 交互式图谱已生成：aviation_kg_500.html")