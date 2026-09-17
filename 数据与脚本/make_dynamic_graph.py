# -*- coding: utf-8 -*-
"""
生成动态交互式航空术语知识图谱（HTML，Plotly）
基于真实的 DeepSeek 分类结果（12类关系），生成可缩放/拖拽/筛选/点击查详情的图谱。

用法：python make_dynamic_graph.py
输出：aviation_kg_dynamic.html
"""
import json, os, sys
from collections import Counter, defaultdict
import plotly.graph_objects as go

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# ------------------------------------------------------------------
# 1. 读取关系数据（核心子图优先，回退到基础关系）
# ------------------------------------------------------------------
def load_relations():
    # 优先读合并后的关系文件，回退到单文件
    for fn in ['merged_relations.json', 'relations_core_v2.json', 'relations.json']:
        if os.path.exists(fn):
            with open(fn, 'r', encoding='utf-8') as f:
                rels = json.load(f)
            # 过滤 none
            rels = [r for r in rels if r.get('relation') != 'none']
            print(f"读取 {fn}: {len(rels)} 条有效关系")
            return rels
    raise FileNotFoundError("没有找到关系文件，请先运行 step2")

relations = load_relations()

# 术语定义
with open('auto_labels_clean.json', 'r', encoding='utf-8') as f:
    clean = json.load(f)
term_def = {item['term']: item['definition'] for item in clean}

# ------------------------------------------------------------------
# 2. 构建图结构
# ------------------------------------------------------------------
nodes = set()
for r in relations:
    nodes.add(r['subject'])
    nodes.add(r['object'])
nodes = sorted(nodes)
print(f"节点数: {len(nodes)}，边数: {len(relations)}")

# 节点连接度
degree = Counter()
for r in relations:
    degree[r['subject']] += 1
    degree[r['object']] += 1

# 关系类型配色（12类）
REL_COLORS = {
    'synonym_of': '#2ecc71',  'is_a': '#3498db',       'part_of': '#e67e22',
    'has_property': '#9b59b6','located_in': '#f1c40f', 'controls': '#e74c3c',
    'operates_with': '#1abc9c','causes': '#e91e63',    'consists_of': '#f39c12',
    'used_for': '#16a085',    'measures': '#34495e',   'defined_by': '#8e44ad',
}

# 边数据按类型分组（用于图例和筛选）
edges_by_type = defaultdict(list)
for r in relations:
    rel = r['relation']
    edges_by_type[rel].append((r['subject'], r['object']))

# ------------------------------------------------------------------
# 3. 布局：简单的力导向（spring）布局
# ------------------------------------------------------------------
try:
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(nodes)
    for r in relations:
        G.add_edge(r['subject'], r['object'])
    # 用 spring 布局
    pos = nx.spring_layout(G, seed=42, k=0.8, iterations=80)
except Exception:
    # 兜底：环形布局
    import math
    pos = {n: (math.cos(i*2*math.pi/len(nodes)), math.sin(i*2*math.pi/len(nodes)))
           for i, n in enumerate(nodes)}

# ------------------------------------------------------------------
# 4. 绘制边（按类型着色）
# ------------------------------------------------------------------
edge_traces = []
for rel, pairs in edges_by_type.items():
    color = REL_COLORS.get(rel, '#888')
    xs, ys = [], []
    for s, o in pairs:
        if s in pos and o in pos:
            x0, y0 = pos[s]
            x1, y1 = pos[o]
            xs.extend([x0, x1, None])
            ys.extend([y0, y1, None])
    edge_traces.append(go.Scatter(
        x=xs, y=ys, mode='lines',
        line=dict(width=1.2, color=color),
        hoverinfo='none',
        name=f'{rel} ({len(pairs)})',
        legendgroup=rel,
    ))

# ------------------------------------------------------------------
# 5. 节点（大小按连接度，hover 显示定义）
# ------------------------------------------------------------------
node_x = [pos[n][0] for n in nodes]
node_y = [pos[n][1] for n in nodes]
node_size = [8 + 4 * min(degree.get(n, 0), 8) for n in nodes]
# 节点颜色：按度数（hub 更亮）
node_color = [min(degree.get(n, 0) / max(degree.values()), 1) for n in nodes]

node_text = [n for n in nodes]
node_hover = []
for n in nodes:
    d = term_def.get(n, '')
    d_short = d[:150] + ('...' if len(d) > 150 else '')
    node_hover.append(f"<b>{n}</b><br>度数: {degree.get(n,0)}<br>{d_short}")

node_trace = go.Scatter(
    x=node_x, y=node_y, mode='markers+text',
    text=node_text, textposition='top center',
    hovertext=node_hover, hoverinfo='text',
    marker=dict(size=node_size, color=node_color, colorscale='Viridis',
                showscale=True, colorbar=dict(title='连接度'),
                line=dict(width=1, color='#333')),
    textfont=dict(size=11, color='#333'),
)

# ------------------------------------------------------------------
# 6. 组合 + 导出
# ------------------------------------------------------------------
fig = go.Figure(data=edge_traces + [node_trace])

fig.update_layout(
    title=dict(text='航空术语知识图谱（动态交互版）', font=dict(size=18)),
    showlegend=True,
    hovermode='closest',
    margin=dict(b=20, l=5, r=5, t=60),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    height=800,
    legend=dict(font=dict(size=10)),
)

out = os.path.join(BASE, 'aviation_kg_dynamic.html')
fig.write_html(out, include_plotlyjs='cdn', full_html=True)
print(f"✅ 动态图谱已生成: {out}")
print(f"   节点 {len(nodes)}，边 {len(relations)}，关系类型 {len(edges_by_type)} 种")
