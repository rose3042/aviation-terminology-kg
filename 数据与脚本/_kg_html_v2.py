# -*- coding: utf-8 -*-
"""知识图谱 3D 交互 HTML v2：完整2184节点/2475关系，白底（与正文图6/图12风格统一）。
功能：360°旋转/缩放、按12类关系类型筛选、六视角相机预设、hub发光标签、hover关系详情。
输出：航空术语知识图谱_3D交互.html（可离线双击打开）
"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------- 数据与布局（与 _figs_kg_v2.py 完全一致，seed=42） ----------
d = json.load(open('merged_relations.json', encoding='utf-8'))
G = nx.Graph()
for r in d:
    G.add_edge(r['subject'], r['object'])
deg = dict(G.degree())
pos = nx.spring_layout(G, dim=3, k=0.28, iterations=35, seed=42)

nodes = list(G.nodes())
X = np.array([pos[n][0] for n in nodes])
Y = np.array([pos[n][1] for n in nodes])
Z = np.array([pos[n][2] for n in nodes])
D = np.array([deg[n] for n in nodes])
node_deg = {n: deg[n] for n in nodes}

BG = '#FFFFFF'                      # 白底
INK = '#2C3E50'                      # 深蓝灰正文
ACCENT = '#2980B9'                   # 主强调蓝
HUB_COL = '#8A1B12'                  # hub标签深红
colorscale = [[0, '#85C4EB'], [0.5, '#2E9BD6'], [1, '#1763B5']]  # 高饱和蓝渐变（普通节点按度）
EDGE_RGBA = 'rgba(174,182,191,0.5)'  # 灰边（#AEB6BF，与原版一致）
norm = lambda v: (np.log(v) - np.log(1)) / (np.log(D.max()) - np.log(1))  # LogNorm 0..1
node_size = (np.sqrt(D) * 13 + 4) * 2.2   # 放大供3D
node_c = np.array([(np.log(v) - np.log(1)) / (np.log(D.max()) - np.log(1)) for v in D])

top_idx = sorted(range(len(nodes)), key=lambda i: -D[i])[:12]
hub_names = set(nodes[i] for i in top_idx)

# 坐标范围（与六视图一致的裁剪）
xs = np.percentile(X, [3, 97]); ys = np.percentile(Y, [3, 97]); zs = np.percentile(Z, [3, 97])
cx, cy, cz = (xs[0]+xs[1])/2, (ys[0]+ys[1])/2, (zs[0]+zs[1])/2
span = max(xs[1]-xs[0], ys[1]-ys[0], zs[1]-zs[0])

# ---------- 边按关系类型分组 ----------
from collections import defaultdict
rel_groups = defaultdict(list)
for r in d:
    rel_groups[r['relation']].append(r)
rel_order = sorted(rel_groups.keys(), key=lambda k: -len(rel_groups[k]))

# 12类关系配色（白底可读的冷色系，无黄）
rel_colors = {
    'is_a': '#0D57A1', 'part_of': '#2E8B57', 'has_property': '#2E97B5',
    'used_for': '#6B7A8C', 'synonym_of': '#9C6ADE', 'consists_of': '#7E9CC0',
    'operates_with': '#E67E22', 'measures': '#4A7FB5', 'defined_by': '#9BB0C8',
    'located_in': '#3E8EAD', 'controls': '#C0392B', 'causes': '#C79A6B',
}

# ---------- 构建 Plotly 图 ----------
fig = go.Figure()

# 1) 节点（含hub光晕两层：用两个 scatter，一大一透明）
hub_mask = np.array([n in hub_names for n in nodes])
non_hub = ~hub_mask
node_size = (np.sqrt(D) * 13 + 4) * 2.2
hub_size = (np.sqrt(D[hub_mask]) * 13 + 4) * 3.4
# 普通节点：蓝色（按度对数渐变）
fig.add_trace(go.Scatter3d(
    x=X[non_hub], y=Y[non_hub], z=Z[non_hub], mode='markers',
    marker=dict(size=node_size[non_hub], color=node_c[non_hub], colorscale=colorscale,
                cmin=0, cmax=1, opacity=0.92, line=dict(width=0)),
    text=[f'<b>{n}</b><br>度(degree): {node_deg[n]}' for n in nodes if n not in hub_names],
    hoverinfo='text', name='普通术语节点', showlegend=True))
# hub 节点：红色（红蓝交织）
fig.add_trace(go.Scatter3d(
    x=X[hub_mask], y=Y[hub_mask], z=Z[hub_mask], mode='markers',
    marker=dict(size=hub_size, color='#E03028', opacity=0.95, line=dict(width=0)),
    text=[f'<b>{n}</b><br>度(degree): {node_deg[n]}' for n in nodes if n in hub_names],
    hoverinfo='text', name='枢纽节点(hub)', showlegend=True))
# hub 光晕（两圈红，收敛不挡阅读）
fig.add_trace(go.Scatter3d(
    x=X[hub_mask], y=Y[hub_mask], z=Z[hub_mask], mode='markers',
    marker=dict(size=hub_size * 2.2, color='#E03028', opacity=0.10, line=dict(width=0)),
    hoverinfo='skip', showlegend=False))
fig.add_trace(go.Scatter3d(
    x=X[hub_mask], y=Y[hub_mask], z=Z[hub_mask], mode='markers',
    marker=dict(size=hub_size * 1.3, color='#E03028', opacity=0.28, line=dict(width=0)),
    hoverinfo='skip', showlegend=False))
# hub 标签（深红）
fig.add_trace(go.Scatter3d(
    x=[X[i] for i in top_idx], y=[Y[i] for i in top_idx], z=[Z[i] for i in top_idx],
    mode='text', text=[nodes[i] for i in top_idx],
    textfont=dict(color=HUB_COL, size=11, family='Arial', weight='bold'),
    hoverinfo='skip', showlegend=False))

# 2) 每条关系类型一条边迹线（支持筛选）
for rel in rel_order:
    rs = rel_groups[rel]
    ex, ey, ez = [], [], []
    hover_txt = []
    for r in rs:
        if r['subject'] not in pos or r['object'] not in pos:
            continue
        sx, sy, sz = pos[r['subject']]
        ox, oy, oz = pos[r['object']]
        ex += [sx, ox, None]; ey += [sy, oy, None]; ez += [sz, oz, None]
        hover_txt.append(f'{r["subject"]} —[{rel}]→ {r["object"]}<br>置信度 {r["confidence"]}')
    # 灰色边（原版风格），仅按关系类型控制显示/隐藏
    fig.add_trace(go.Scatter3d(
        x=ex, y=ey, z=ez, mode='lines',
        line=dict(color=EDGE_RGBA, width=1.4),
        text=hover_txt, hoverinfo='text', name=f'{rel} ({len(rs)})',
        visible=True))

# ---------- 六视角相机预设 ----------
presets = {
    '整体视图': dict(eye=dict(x=2.15, y=1.55, z=1.0), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    '旋转视角': dict(eye=dict(x=-1.85, y=-1.7, z=0.9), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    '俯视视角': dict(eye=dict(x=0, y=0, z=3.0), center=dict(x=0, y=0, z=0), up=dict(x=0, y=1, z=0)),
    '核心放大': dict(eye=dict(x=0.95, y=0.55, z=0.62), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    '骨干骨架': dict(eye=dict(x=1.9, y=0.35, z=0.95), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
}
radar = pos.get('RADAR')
if radar is not None:
    presets['RADAR近景'] = dict(
        eye=dict(x=(radar[0]-cx)/span*2.0 + 0.6, y=(radar[1]-cy)/span*2.0 + 0.4, z=(radar[2]-cz)/span*1.8 + 0.5),
        center=dict(x=(radar[0]-cx)/span, y=(radar[1]-cy)/span, z=(radar[2]-cz)/span),
        up=dict(x=0, y=0, z=1))

# ---------- 布局（深色 + 左侧控制面板） ----------
fig.update_layout(
    title=dict(text='航空术语知识图谱 3D 交互视图（节点 2184 · 关系 2475 · 12 类语义关系）',
               font=dict(color=INK, size=20), x=0.04, xanchor='left'),
    template=None, paper_bgcolor=BG, plot_bgcolor=BG,
    height=850,
    updatemenus=[
        # 关系类型筛选（左侧竖排按钮组）
        dict(type='dropdown', direction='down', x=0.01, y=1.14, xanchor='left', yanchor='top',
             showactive=True, active=0,
             font=dict(color='#1F3446', size=12),
             bgcolor='#EAF1F9', bordercolor='#7E9CC0', borderwidth=1,
             buttons=[dict(label=f'全部关系 ({sum(len(v) for v in rel_groups.values())}条)',
                           method='update',
                           args=[{'visible': [True] * 5 + [True] * len(rel_order)}]),
                      *[dict(label=f'{rel} ({len(rel_groups[rel])}条)',
                             method='update',
                             args=[{'visible': [True] * 5 +
                                   [i == idx for i in range(len(rel_order))]}])
                        for idx, rel in enumerate(rel_order)]],
        ),
        # 六视角预设
        dict(type='buttons', direction='right', x=0.04, y=1.02, xanchor='left', yanchor='top',
             font=dict(color='#1F3446', size=12),
             bgcolor='#EAF1F9', bordercolor='#7E9CC0', borderwidth=1,
             buttons=[dict(label=name, method='relayout',
                           args=[{'scene.camera': cam}]) for name, cam in presets.items()]),
    ],
    annotations=[
        dict(text='<b>关系类型筛选</b>', x=0.01, y=1.135, xref='paper', yref='paper',
             showarrow=False, font=dict(color=ACCENT, size=13)),
        dict(text='<b>视角</b>', x=0.04, y=1.005, xref='paper', yref='paper',
             showarrow=False, font=dict(color=ACCENT, size=13)),
        dict(text='拖动旋转 · 滚轮缩放 · 悬停查看关系详情',
             x=0.99, y=1.14, xref='paper', yref='paper', xanchor='right',
             showarrow=False, font=dict(color='#6B7A8C', size=12)),
    ],
    legend=dict(x=0.01, y=0.01, bgcolor='rgba(255,255,255,0.85)', font=dict(color=INK, size=11),
                bordercolor='#CBD3DB', borderwidth=1),
    scene=dict(
        bgcolor=BG,
        xaxis=dict(showbackground=False, visible=False),
        yaxis=dict(showbackground=False, visible=False),
        zaxis=dict(showbackground=False, visible=False),
        camera=dict(eye=dict(x=2.15, y=1.55, z=1.0)),
        aspectmode='cube',
    ),
)

# 保存
out = '航空术语知识图谱_3D交互.html'
fig.write_html(out, include_plotlyjs='inline', full_html=True, config={'scrollZoom': True})
print('OK 已输出:', out)
print('节点', len(nodes), '| 关系', sum(len(v) for v in rel_groups.values()),
      '| hub标签', len(top_idx), '| 关系类型', len(rel_order))
