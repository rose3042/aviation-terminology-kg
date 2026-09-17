# -*- coding: utf-8 -*-
"""知识图谱六视图静态图 v3.1 —— 用 plotly 构建 + Edge 无头截屏渲染（与 HTML 完全同源）。
同一份数据/配色/弧线/三色节点，固定六视角相机 → PNG → 组合 2×3 网格。
输出：_fig/kg2_view1..6_plotly.png + _fig/fig_kg_grid_v2.png
"""
import json, os, sys, subprocess
from collections import Counter, defaultdict
import numpy as np
import networkx as nx
import plotly.graph_objects as go

sys.stdout.reconfigure(encoding='utf-8')

# ---------- 数据（与 HTML 严格一致） ----------
relations = [r for r in json.load(open('merged_relations.json', encoding='utf-8')) if r.get('relation') != 'none']
nodes = sorted(set(n for r in relations for n in (r['subject'], r['object'])))

degree = Counter()
for r in relations:
    degree[r['subject']] += 1
    degree[r['object']] += 1

G = nx.Graph()
G.add_nodes_from(nodes)
for r in relations:
    G.add_edge(r['subject'], r['object'])
pos = nx.spring_layout(G, dim=3, seed=42, k=1.2, iterations=150)
xs_all = [c[0] for c in pos.values()]; ys_all = [c[1] for c in pos.values()]; zs_all = [c[2] for c in pos.values()]
scale = 20 / max(max(xs_all) - min(xs_all), max(ys_all) - min(ys_all), max(zs_all) - min(zs_all))
pos = {n: (v[0]*scale, v[1]*scale, v[2]*scale) for n, v in pos.items()}

REL_COLORS = {
    'part_of': '#ff8c00', 'has_property': '#7c22d6', 'is_a': '#1f4fd8',
    'defined_by': '#6d28d9', 'used_for': '#00b08f', 'synonym_of': '#00c853',
    'operates_with': '#00a0b0', 'located_in': '#f5b700', 'consists_of': '#ef7b00',
    'measures': '#607a8a', 'controls': '#e4002b', 'causes': '#d81b60',
}
TIER_RGB = {2: (230, 0, 18), 1: (0, 87, 217), 0: (170, 180, 194)}
top_hubs = [n for n, _ in sorted(degree.items(), key=lambda kv: -kv[1])[:80] if degree[n] >= 8][:20]

def arc_points(a, b, curvature=0.22, samples=14):
    d = b - a
    mid = (a + b) / 2
    up = np.array([0.0, 0.0, 1.0])
    n = np.cross(d, up)
    if np.linalg.norm(n) < 1e-8:
        n = np.cross(d, np.array([1.0, 0.0, 0.0]))
    n = n / (np.linalg.norm(n) + 1e-8)
    ctrl = mid + n * (np.linalg.norm(d) * curvature)
    ts = np.linspace(0, 1, samples)
    return np.array([(1-t)**2 * a + 2*(1-t)*t * ctrl + t**2 * b for t in ts])

def build_fig(subset=None):
    fig = go.Figure()
    by_rel = defaultdict(list)
    for r in relations:
        by_rel[r['relation']].append((r['subject'], r['object']))
    for rel, pairs in sorted(by_rel.items(), key=lambda kv: -len(kv[1])):
        ex, ey, ez = [], [], []
        for s, o in pairs:
            if s not in pos or o not in pos:
                continue
            if subset is not None and (s not in subset or o not in subset):
                continue
            pts = arc_points(np.array(pos[s]), np.array(pos[o]))
            ex += list(pts[:, 0]) + [None]; ey += list(pts[:, 1]) + [None]; ez += list(pts[:, 2]) + [None]
        if not ex:
            continue
        fig.add_trace(go.Scatter3d(
            x=ex, y=ey, z=ez, mode='lines',
            line=dict(color=REL_COLORS.get(rel, '#888'), width=2.2), opacity=0.85,
            hoverinfo='skip', showlegend=False))
    in_sub = nodes if subset is None else [n for n in nodes if n in subset]
    nx_, ny_, nz_, nc_, ns_ = [], [], [], [], []
    for n in in_sub:
        dg = degree[n]
        tier = 2 if dg >= 6 else (1 if dg >= 3 else 0)
        r, g, b = TIER_RGB[tier]
        nx_.append(pos[n][0]); ny_.append(pos[n][1]); nz_.append(pos[n][2])
        nc_.append(f'rgb({r},{g},{b})')
        ns_.append(24 + 10 * min(dg, 12))
    fig.add_trace(go.Scatter3d(
        x=nx_, y=ny_, z=nz_, mode='markers+text',
        text=[n if n in top_hubs else '' for n in in_sub],
        textposition='top center',
        textfont=dict(size=13, color='#111827', weight='bold'),
        hoverinfo='skip',
        marker=dict(size=ns_, color=nc_,
                    line=dict(width=1.4, color='#ffffff'), symbol='circle')))
    fig.update_layout(
        paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
        margin=dict(b=5, l=5, r=5, t=5),
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor='#ffffff', aspectmode='cube'))
    return fig

# ---------- 六视角 ----------
views = [
    ('_fig/kg2_view1_overall_plotly.png',  dict(eye=dict(x=1.55, y=1.05, z=0.8),  center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)), None),
    ('_fig/kg2_view2_rotated_plotly.png',  dict(eye=dict(x=-1.3, y=-1.2, z=0.7), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)), None),
    ('_fig/kg2_view3_top_plotly.png',      dict(eye=dict(x=0, y=0, z=2.4),       center=dict(x=0, y=0, z=0), up=dict(x=0, y=1, z=0)), None),
    ('_fig/kg2_view4_zoom_plotly.png',     dict(eye=dict(x=0.68, y=0.4, z=0.45), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)), None),
    ('_fig/kg2_view5_backbone_plotly.png', dict(eye=dict(x=1.35, y=0.25, z=0.7), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
     {n for n in G if degree[n] >= 5}),
    ('_fig/kg2_view6_closeup_plotly.png',  None, None),
]
if 'RADAR' in pos:
    rx, ry, rz = pos['RADAR']
    views[5] = ('_fig/kg2_view6_closeup_plotly.png',
                dict(eye=dict(x=rx*0.09+0.4, y=ry*0.09+0.28, z=rz*0.09+0.35),
                     center=dict(x=rx*0.05, y=ry*0.05, z=rz*0.05), up=dict(x=0, y=0, z=1)), None)

# 生成六份带固定相机的小HTML（CDN plotly，体积小）
html_files = []
for i, (path, cam, subset) in enumerate(views):
    fig = build_fig(subset)
    if cam is not None:
        fig.update_layout(scene=dict(camera=cam))
    hf = f'_fig/_view{i+1}.html'
    fig.write_html(hf, include_plotlyjs='cdn', full_html=True)
    html_files.append(hf)
    print('HTML', hf)

# Edge 无头截屏
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
for (path, cam, subset), hf in zip(views, html_files):
    url = 'file:///' + os.path.abspath(hf).replace('\\', '/')
    abs_out = os.path.abspath(path).replace('\\', '/')
    cmd = [EDGE, '--headless=new', '--disable-gpu', '--enable-unsafe-swiftshader',
           '--virtual-time-budget=20000', '--window-size=1280,1000',
           '--screenshot=' + abs_out, url]
    subprocess.run(cmd, capture_output=True, timeout=120)
    print('PNG', path, os.path.getsize(path) if os.path.exists(path) else 'FAIL')

# ---------- 组合 2×3 网格 ----------
from PIL import Image, ImageDraw, ImageFont
def font(sz):
    for fp in ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf']:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, sz)
    return ImageFont.load_default()

titles = ['(a) 整体视图', '(b) 旋转视角', '(c) 俯视视角', '(d) 核心连接簇放大', '(e) 骨干网络（精简）', '(f) RADAR 枢纽近景']
imgs = [Image.open(p) for p, _, _ in views]
tw, th = imgs[0].size
gap = 14
grid_w = tw * 3 + gap * 4
grid_h = th * 2 + gap * 3 + 48
grid = Image.new('RGB', (grid_w, grid_h), 'white')
for idx, im in enumerate(imgs):
    r, c = divmod(idx, 3)
    x = gap + c * (tw + gap)
    y = gap + r * (th + gap)
    grid.paste(im, (x, y))
    d = ImageDraw.Draw(grid)
    tf = font(34)
    bb = d.textbbox((0, 0), titles[idx], font=tf)
    d.text((x + tw//2 - (bb[2]-bb[0])//2, y + th + 6), titles[idx], font=tf, fill='#1F3446')
grid.save('_fig/fig_kg_grid_v2.png')
print('OK fig_kg_grid_v2.png', grid.size)
