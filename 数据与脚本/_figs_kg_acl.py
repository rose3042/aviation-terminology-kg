# -*- coding: utf-8 -*-
"""知识图谱 ACL 克制风格重做（图13/图14/A1-A3）。
问题修复：
 1. 12 类关系高饱和彩虹色边 → 单色浅灰蓝细线（弱化噪声、突出拓扑）
 2. 红/蓝/灰三色节点保留（与正文"三色分级"一致）但柔和化
 3. 截图放大：单视图 10×8in@300dpi（原8.4×6.6@220）；zoom/closeup 截取范围缩小到 0.32/0.28 跨度
输出：
  _fig/kg_acl_view1..6.png（六视图，3000×2400px）
  _fig/fig_kg_grid_acl.png （图14 六视图大网格）
  _fig/fig13_kg_overall.png（图13 主图=view1 大版，3600×2700px）
"""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import matplotlib.patheffects as pe
from matplotlib import font_manager

for _f in ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf', 'C:/Windows/Fonts/simsun.ttc']:
    if os.path.exists(_f):
        font_manager.fontManager.addfont(_f)
matplotlib.rcParams['font.family'] = ['Times New Roman', 'Microsoft YaHei', 'SimHei', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

os.makedirs('_fig', exist_ok=True)

# ---------- 数据（与 HTML v3 严格一致） ----------
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

# ---------- ACL 克制配色（Okabe–Ito 体系派生；与正文三色分级一致） ----------
BG       = '#FFFFFF'
EDGE_C   = '#B9C7D9'   # 边：单一浅灰蓝（弱化12类彩边）
EDGE_LW  = 0.55
EDGE_ALPHA = 0.5
TIER_RGB = {2: (0.66, 0.22, 0.16),   # 核心枢纽(度≥6)：柔和深红（正文"红色"）
            1: (0.19, 0.42, 0.68),   # 重要术语(度3–5)：柔和蓝（正文"蓝色"）
            0: (0.63, 0.69, 0.76)}   # 一般术语(度<3)：浅灰（正文"灰色"）
TIER = [2 if deg[n] >= 6 else (1 if deg[n] >= 3 else 0) for n in nodes]
node_c = np.array([TIER_RGB[t] for t in TIER], dtype=float)
# 节点大小：度相关但克制（与 HTML 同公式）
node_size = np.array([((24 + 10*min(deg[n], 12)) / 220.0 * 72.0 / 2.0) ** 2 * np.pi for n in nodes])

# 标签：仅正文点名的 top 5 枢纽（避免糊）
LABEL_NODES = [n for n, _ in sorted(deg.items(), key=lambda kv: -kv[1])[:5]]
label_idx = [i for i, n in enumerate(nodes) if n in LABEL_NODES]
LABEL_C = '#374151'

lines = [[pos[u], pos[v]] for u, v in G.edges()]
xs = np.percentile(X, [3, 97]); ys = np.percentile(Y, [3, 97]); zs = np.percentile(Z, [3, 97])
cx, cy, cz = (xs[0]+xs[1])/2, (ys[0]+ys[1])/2, (zs[0]+zs[1])/2
span = max(xs[1]-xs[0], ys[1]-ys[0], zs[1]-zs[0])


def draw_view(elev, azim, out, figsize=(10, 8), dpi=300, subset=None,
              lim=None, proj='persp'):
    """单视图：白底 · 单色细边 · 三色节点 · 仅 top hub 标签。"""
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111, projection='3d')
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    if subset is None:
        mask = np.ones(len(nodes), bool)
        segs = lines
    else:
        mask = np.array([n in subset for n in nodes])
        segs = [[pos[u], pos[v]] for u, v in G.edges() if u in subset and v in subset]
    lc = Line3DCollection(segs, colors=EDGE_C, linewidths=EDGE_LW, alpha=EDGE_ALPHA)
    ax.add_collection3d(lc)

    # 三色节点，浅灰细描边（柔和，不抢戏）
    ax.scatter(X[mask], Y[mask], Z[mask], s=node_size[mask], c=node_c[mask],
               alpha=1.0, edgecolors='#E5EAF0', linewidths=0.35, depthshade=False)

    # top hub 标签：小字深灰 + 白色光晕
    for i in label_idx:
        if mask[i]:
            ax.text(X[i], Y[i], Z[i], nodes[i], fontsize=8, color=LABEL_C,
                    zorder=12, weight='bold', ha='center', va='bottom',
                    path_effects=[pe.withStroke(linewidth=2.5, foreground='white')])

    ax.view_init(elev=elev, azim=azim)
    ax.set_proj_type(proj)
    if lim is not None:
        ax.set_xlim(lim[0], lim[1]); ax.set_ylim(lim[0], lim[1]); ax.set_zlim(lim[0], lim[1])
    else:
        ax.set_xlim(xs[0], xs[1]); ax.set_ylim(ys[0], ys[1]); ax.set_zlim(zs[0], zs[1])
    ax.set_axis_off()
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.pane.set_facecolor(BG); a.pane.set_edgecolor('none'); a.pane.set_alpha(0)
    fig.savefig(out, dpi=dpi, facecolor=BG, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    print('OK', out)


# ---------- 六视图（截图显著放大） ----------
draw_view(20, 55, '_fig/kg_acl_view1_overall.png')
draw_view(14, -125, '_fig/kg_acl_view2_rotated.png')
draw_view(88, 0, '_fig/kg_acl_view3_top.png')
s4 = span * 0.32                       # 原 0.44 → 更聚焦
draw_view(30, 42, '_fig/kg_acl_view4_zoom.png', lim=(cx - s4, cx + s4))
core = {n for n in G if deg[n] >= 5}
draw_view(25, 70, '_fig/kg_acl_view5_backbone.png', subset=core)
hub = 'RADAR'
s6 = span * 0.28                       # 原 0.50 → 放大近景
hx, hy, hz = pos[hub]
draw_view(22, 28, '_fig/kg_acl_view6_closeup.png', lim=(hx - s6, hx + s6))

# ---------- 图13 主图（整体视图大版） ----------
draw_view(20, 55, '_fig/fig13_kg_overall.png', figsize=(12, 9), dpi=300)

# ---------- 图14 六视图大网格 ----------
import matplotlib.image as mpimg
views = [
    ('_fig/kg_acl_view1_overall.png',   '(a) 整体视图'),
    ('_fig/kg_acl_view2_rotated.png',   '(b) 旋转视角'),
    ('_fig/kg_acl_view3_top.png',       '(c) 俯视视角'),
    ('_fig/kg_acl_view4_zoom.png',      '(d) 核心连接簇放大'),
    ('_fig/kg_acl_view5_backbone.png',  '(e) 骨干网络（精简）'),
    ('_fig/kg_acl_view6_closeup.png',   '(f) RADAR 枢纽近景'),
]
fig, axes = plt.subplots(2, 3, figsize=(19, 12.5), dpi=200)
fig.patch.set_facecolor('white')
for ax, (fname, cap) in zip(axes.flat, views):
    img = mpimg.imread(fname)
    ax.imshow(img)
    ax.set_title(cap, fontsize=14, pad=8, color='#1F3446')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
fig.subplots_adjust(wspace=0.03, hspace=0.18, left=0.005, right=0.995, top=0.985, bottom=0.01)
fig.savefig('_fig/fig_kg_grid_acl.png', dpi=200, facecolor='white')
plt.close(fig)
print('OK _fig/fig_kg_grid_acl.png')
