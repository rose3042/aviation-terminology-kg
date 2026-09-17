# -*- coding: utf-8 -*-
"""知识图谱增强可视化 v3（与HTML v3.1同一风格）：白底·12类关系彩边·三色节点·无大光晕。
与 HTML 版配色/分级严格一致：
  边：12类关系各用高饱和独立色；
  节点：核心枢纽(度>=6)红#e60023 / 重要术语(3-5)蓝#1f6fe0 / 一般术语(<3)灰#aab4c2；
  标签：top枢纽术语名，深色加粗。
输出 _fig/kg2_view1..6.png + 组合网格 _fig/fig_kg_grid_v2.png
"""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib import font_manager
for _f in ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf', 'C:/Windows/Fonts/simsun.ttc']:
    if os.path.exists(_f):
        font_manager.fontManager.addfont(_f)
matplotlib.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

os.makedirs('_fig', exist_ok=True)

# ---------- 数据（与HTML一致：唯一度） ----------
d = json.load(open('merged_relations.json', encoding='utf-8'))
G = nx.Graph()
for r in d:
    G.add_edge(r['subject'], r['object'])
deg = dict(G.degree())
pos = nx.spring_layout(G, dim=3, seed=42, k=1.2, iterations=150)
xs_all = [c[0] for c in pos.values()]; ys_all = [c[1] for c in pos.values()]; zs_all = [c[2] for c in pos.values()]
scale = 20 / max(max(xs_all) - min(xs_all), max(ys_all) - min(ys_all), max(zs_all) - min(zs_all))
pos = {n: (v[0]*scale, v[1]*scale, v[2]*scale) for n, v in pos.items()}

nodes = list(G.nodes())
X = np.array([pos[n][0] for n in nodes])
Y = np.array([pos[n][1] for n in nodes])
Z = np.array([pos[n][2] for n in nodes])
D = np.array([deg[n] for n in nodes])

# ---------- 配色（与HTML v3.1一致：高饱和） ----------
BG = '#FFFFFF'
REL_COLORS = {
    'part_of': '#ff9f1c', 'has_property': '#8e2de2', 'is_a': '#2962ff',
    'defined_by': '#7c3aed', 'used_for': '#00c2a3', 'synonym_of': '#00e676',
    'operates_with': '#00bcd4', 'located_in': '#ffd000', 'consists_of': '#ff8f00',
    'measures': '#78909c', 'controls': '#ff1744', 'causes': '#e91e63',
}
TIER_RGB = {2: (230, 0, 35), 1: (31, 111, 224), 0: (170, 180, 194)}   # 红/蓝/灰
TIER = [2 if deg[n] >= 6 else (1 if deg[n] >= 3 else 0) for n in nodes]
node_c = np.array([TIER_RGB[t] for t in TIER], dtype=float) / 255.0
# 节点大小：与HTML同公式的像素→点换算
node_size = [((24 + 10*min(deg[n], 12)) / 220.0 * 72.0 / 2.0) ** 2 * np.pi for n in nodes]
node_size = np.array(node_size)

# 直接标注 top hub（度>=8，最多取20个避免糊）—— 与HTML同候选
top_hubs = {n for n, _ in sorted(deg.items(), key=lambda kv: -kv[1])[:80] if deg[n] >= 8}
label_idx = [i for i, n in enumerate(nodes) if n in top_hubs][:20]
HUB_C = '#111827'

# 边按关系类型分组（每类一色）
from collections import defaultdict
rel_groups = defaultdict(list)
for r in d:
    rel_groups[r['relation']].append((r['subject'], r['object']))
edge_color = []
for r in d:
    edge_color.append(REL_COLORS.get(r['relation'], '#888888'))
# 度>=6红色节点（核心枢纽）
hub_mask = np.array(TIER) == 2

# 坐标范围
xs = np.percentile(X, [3, 97]); ys = np.percentile(Y, [3, 97]); zs = np.percentile(Z, [3, 97])
cx, cy, cz = (xs[0]+xs[1])/2, (ys[0]+ys[1])/2, (zs[0]+zs[1])/2
span = max(xs[1]-xs[0], ys[1]-ys[0], zs[1]-zs[0])

def draw_view(elev, azim, out, edge_alpha=0.85, lw=0.55, subset=None,
              lim=None, proj='persp', label_hubs=True):
    fig = plt.figure(figsize=(8.4, 6.6), dpi=220)
    ax = fig.add_subplot(111, projection='3d')
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    if subset is None:
        mask = np.ones(len(nodes), bool)
        lines = [[pos[u], pos[v]] for u, v in G.edges()]
        colors = edge_color
    else:
        mask = np.array([n in subset for n in nodes])
        lines = [[pos[u], pos[v]] for u, v in G.edges() if u in subset and v in subset]
        colors = [REL_COLORS.get(r['relation'], '#888') for r in d
                  if r['subject'] in subset and r['object'] in subset]
    lc = Line3DCollection(lines, colors=colors, linewidths=lw, alpha=edge_alpha)
    ax.add_collection3d(lc)

    # 三色节点（红/蓝/灰），无大光晕
    ax.scatter(X[mask], Y[mask], Z[mask], s=node_size[mask], c=node_c[mask],
               alpha=1.0, edgecolors='#3a4a5c', linewidths=0.4, depthshade=False)

    # 核心枢纽加一圈紧贴的深红描边（视觉冲击但不挡阅读）
    hm = hub_mask & mask
    if hm.any():
        ax.scatter(X[hm], Y[hm], Z[hm], s=node_size[hm] * 1.15,
                   c='none', edgecolors='#e60023', linewidths=0.8, depthshade=False)

    # top hub 标签（深色加粗，白底可读）
    if label_hubs:
        for i in label_idx:
            if mask[i]:
                ax.text(X[i], Y[i], Z[i], nodes[i], fontsize=7.6, color=HUB_C,
                        zorder=12, weight='bold')

    ax.view_init(elev=elev, azim=azim)
    ax.set_proj_type(proj)
    if lim is not None:
        ax.set_xlim(lim[0], lim[1]); ax.set_ylim(lim[0], lim[1]); ax.set_zlim(lim[0], lim[1])
    else:
        ax.set_xlim(xs[0], xs[1]); ax.set_ylim(ys[0], ys[1]); ax.set_zlim(zs[0], zs[1])
    ax.set_axis_off()
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.pane.set_facecolor(BG); a.pane.set_edgecolor('none')
        a.pane.set_alpha(0)
    fig.savefig(out, dpi=220, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print('OK', out)

# ---------- 六视角 ----------
draw_view(20, 55, '_fig/kg2_view1_overall.png')
draw_view(14, -125, '_fig/kg2_view2_rotated.png')
draw_view(88, 0, '_fig/kg2_view3_top.png')
s4 = span * 0.44
draw_view(30, 42, '_fig/kg2_view4_zoom.png', lim=(cx - s4, cx + s4))
core = {n for n in G if deg[n] >= 5}
draw_view(25, 70, '_fig/kg2_view5_backbone.png', subset=core, edge_alpha=0.9, lw=0.7)
hub = 'RADAR'
s6 = span * 0.5
hx, hy, hz = pos[hub]
draw_view(22, 28, '_fig/kg2_view6_closeup.png', lim=(hx - s6, hx + s6))

# ---------- 组合 2×3 网格 ----------
import matplotlib.image as mpimg
views = [
    ('_fig/kg2_view1_overall.png',  '(a) 整体视图'),
    ('_fig/kg2_view2_rotated.png',  '(b) 旋转视角'),
    ('_fig/kg2_view3_top.png',      '(c) 俯视视角'),
    ('_fig/kg2_view4_zoom.png',     '(d) 核心连接簇放大'),
    ('_fig/kg2_view5_backbone.png', '(e) 骨干网络（精简）'),
    ('_fig/kg2_view6_closeup.png',  '(f) RADAR 枢纽近景'),
]
fig, axes = plt.subplots(2, 3, figsize=(13.6, 8.0), dpi=200)
fig.patch.set_facecolor('white')
for ax, (fname, cap) in zip(axes.flat, views):
    img = mpimg.imread(fname)
    ax.imshow(img)
    ax.set_title(cap, fontsize=10.5, pad=6, color='#1F3446')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
fig.subplots_adjust(wspace=0.04, hspace=0.16, left=0.01, right=0.99, top=0.96, bottom=0.02)
fig.savefig('_fig/fig_kg_grid_v2.png', dpi=200, facecolor='white')
plt.close(fig)
print('OK fig_kg_grid_v2.png')
