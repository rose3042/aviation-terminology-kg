# -*- coding: utf-8 -*-
"""知识图谱 3D 交互 HTML v3.1 —— 导师版风格 + 视觉冲击力增强。
在 v3（完全按导师版：12彩边/三色节点/直标标签/富悬停/无大光晕）基础上增强：
  1) 节点更大，按深度(z)调透明度 → 立体感强；
  2) 边更粗(2.0)、更浓(opacity 0.72)，并升级为弧线（二次贝塞尔）→ 力导向图的曲线冲击；
  3) 标签更大加粗、标题更醒目、初始视角更戏剧化；
  4) 核心枢纽红节点保留紧贴节点的细红描边（无大光晕，不挡阅读）。
输出：航空术语知识图谱_3D交互.html
"""
import json, os, sys, re
from collections import Counter, defaultdict
import networkx as nx
import numpy as np
import plotly.graph_objects as go

sys.stdout.reconfigure(encoding='utf-8')

# ---------- 数据 ----------
relations = [r for r in json.load(open('merged_relations.json', encoding='utf-8')) if r.get('relation') != 'none']
nodes = sorted(set(n for r in relations for n in (r['subject'], r['object'])))

clean = json.load(open('auto_labels_clean.json', encoding='utf-8'))
term_def = {item['term']: item['definition'] for item in clean}
DPATH = r'D:\360MoveData\Users\叶丽娜\Desktop\dictionary_clean.txt'
if os.path.exists(DPATH):
    for line in open(DPATH, encoding='utf-8'):
        line = line.strip()
        m = re.match(r'^([A-Za-z][A-Za-z0-9\- ]*?(?:\([^)]+\))?)\.\s+(.+)$', line)
        if m:
            t, d = m.group(1).strip(), m.group(2).strip()
            if t not in term_def and len(d) >= 8:
                term_def[t] = d
print('节点', len(nodes), '| 定义覆盖', sum(1 for n in nodes if n in term_def), '/', len(nodes))

degree = Counter()
for r in relations:
    degree[r['subject']] += 1
    degree[r['object']] += 1

# ---------- 力导向 3D 布局（导师版参数） ----------
G = nx.Graph()
G.add_nodes_from(nodes)
for r in relations:
    G.add_edge(r['subject'], r['object'])
pos = nx.spring_layout(G, dim=3, seed=42, k=1.2, iterations=150)
xs_all = [c[0] for c in pos.values()]; ys_all = [c[1] for c in pos.values()]; zs_all = [c[2] for c in pos.values()]
scale = 20 / max(max(xs_all) - min(xs_all), max(ys_all) - min(ys_all), max(zs_all) - min(zs_all))
pos = {n: (v[0] * scale, v[1] * scale, v[2] * scale) for n, v in pos.items()}

X = np.array([pos[n][0] for n in nodes]); Y = np.array([pos[n][1] for n in nodes]); Z = np.array([pos[n][2] for n in nodes])
D = np.array([degree[n] for n in nodes])
xs = np.percentile(X, [3, 97]); ys = np.percentile(Y, [3, 97]); zs = np.percentile(Z, [3, 97])
cx, cy, cz = (xs[0]+xs[1])/2, (ys[0]+ys[1])/2, (zs[0]+zs[1])/2
span = max(xs[1]-xs[0], ys[1]-ys[0], zs[1]-zs[0])

# ---------- 弧线边：12类各一色（导师版色值） ----------
REL_COLORS = {
    'part_of': '#ff8c00', 'has_property': '#7c22d6', 'is_a': '#1f4fd8',
    'defined_by': '#6d28d9', 'used_for': '#00b08f', 'synonym_of': '#00c853',
    'operates_with': '#00a0b0', 'located_in': '#f5b700', 'consists_of': '#ef7b00',
    'measures': '#607a8a', 'controls': '#e4002b', 'causes': '#d81b60',
}

def arc_points(a, b, curvature=0.22, samples=14):
    """二次贝塞尔弧：中点沿法向抬高，形成柔和弧线（力导向图曲线感）。"""
    d = b - a
    mid = (a + b) / 2
    up = np.array([0.0, 0.0, 1.0])
    n = np.cross(d, up)
    if np.linalg.norm(n) < 1e-8:
        n = np.cross(d, np.array([1.0, 0.0, 0.0]))
    n = n / (np.linalg.norm(n) + 1e-8)
    ctrl = mid + n * (np.linalg.norm(d) * curvature)
    ts = np.linspace(0, 1, samples)
    pts = np.array([(1-t)**2 * a + 2*(1-t)*t * ctrl + t**2 * b for t in ts])
    return pts

rel_groups = defaultdict(list)
for r in relations:
    rel_groups[r['relation']].append(r)
rel_order = sorted(rel_groups.keys(), key=lambda k: -len(rel_groups[k]))

fig = go.Figure()
edge_trace_names = []
for rel in rel_order:
    color = REL_COLORS.get(rel, '#888')
    ex, ey, ez, hover_txt = [], [], [], []
    for r in rel_groups[rel]:
        if r['subject'] not in pos or r['object'] not in pos:
            continue
        pts = arc_points(np.array(pos[r['subject']]), np.array(pos[r['object']]))
        ex += list(pts[:, 0]) + [None]
        ey += list(pts[:, 1]) + [None]
        ez += list(pts[:, 2]) + [None]
        hover_txt.append(f'{r["subject"]} —[{rel}]→ {r["object"]}<br>置信度 {r["confidence"]}')
    fig.add_trace(go.Scatter3d(
        x=ex, y=ey, z=ez, mode='lines',
        line=dict(color=color, width=2.2),
        opacity=0.85, text=hover_txt, hoverinfo='text',
        name=f'{rel} ({len(rel_groups[rel])})', visible=True))
    edge_trace_names.append(rel)

# ---------- 节点：三色分级 + 更大 + 实色不透明 + 白描边（红蓝重叠不再发黑） ----------
def node_tier(d):
    return 2 if d >= 6 else (1 if d >= 3 else 0)

tier_rgb = {2: (230, 0, 18), 1: (0, 87, 217), 0: (170, 180, 194)}  # 正红/深蓝/灰
tier_name = {2: '核心枢纽', 1: '重要术语', 0: '一般术语'}
node_size = [24 + 10 * min(degree[n], 12) for n in nodes]     # 更大
# 实色不透明：半透明节点叠加会混合成脏色（红×蓝→暗紫黑），故去掉深度透明度
node_color = []
for i, n in enumerate(nodes):
    r, g, b = tier_rgb[node_tier(degree[n])]
    node_color.append(f'rgb({r},{g},{b})')

top_hubs = {n for n, _ in degree.most_common(80) if degree[n] >= 8}
node_text = [n if n in top_hubs else '' for n in nodes]

node_hover = []
for n in nodes:
    d = term_def.get(n, '')
    d_short = d[:120] + ('...' if len(d) > 120 else '')
    tier = node_tier(degree[n])
    node_hover.append(f"<b>{n}</b><br><span style='color:#555'>[{tier_name[tier]}]</span> | 连接度: {degree[n]}<br>{d_short}")

fig.add_trace(go.Scatter3d(
    x=X, y=Y, z=Z, mode='markers+text',
    text=node_text, textposition='top center',
    textfont=dict(size=16, color='#111827', weight='bold'),
    hovertext=node_hover, hoverinfo='text',
    marker=dict(size=node_size, color=node_color,
                line=dict(width=1.4, color='#ffffff'), symbol='circle'),
    name='术语节点', showlegend=True))

# ---------- 六视角相机预设（更戏剧化的初始视角） ----------
presets = {
    '整体视图': dict(eye=dict(x=1.55, y=1.05, z=0.8),  center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    '旋转视角': dict(eye=dict(x=-1.3, y=-1.2, z=0.7), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    '俯视视角': dict(eye=dict(x=0, y=0, z=2.4),       center=dict(x=0, y=0, z=0), up=dict(x=0, y=1, z=0)),
    '核心放大': dict(eye=dict(x=0.68, y=0.4, z=0.45), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
    '骨干骨架': dict(eye=dict(x=1.35, y=0.25, z=0.7), center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1)),
}
radar = pos.get('RADAR')
if radar is not None:
    rcx, rcy, rcz = (radar[0]-cx)/span, (radar[1]-cy)/span, (radar[2]-cz)/span
    presets['RADAR近景'] = dict(
        eye=dict(x=rcx*1.9 + 0.4, y=rcy*1.9 + 0.28, z=rcz*1.7 + 0.35),
        center=dict(x=rcx, y=rcy, z=rcz), up=dict(x=0, y=0, z=1))

# ---------- 布局 ----------
n_edge = len(edge_trace_names)
fig.update_layout(
    title=dict(text='✈️  航空术语知识图谱（节点 2184 · 关系 2475 · 12 类语义关系）',
               font=dict(color='#0d1b2a', size=26, weight='bold'), x=0.04, xanchor='left'),
    paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
    height=1200,
    showlegend=True,
    legend=dict(font=dict(color='#1f2937', size=13, weight='bold'), bgcolor='rgba(255,255,255,0.85)',
                bordercolor='#cbd5e1', borderwidth=1, x=1.0, y=1.0, xanchor='right', yanchor='top'),
    updatemenus=[
        dict(type='dropdown', direction='down', x=0.01, y=1.05, xanchor='left', yanchor='top',
             showactive=True, active=0,
             font=dict(color='#1f2937', size=12, weight='bold'), bgcolor='#eaf1f9',
             bordercolor='#7e9cc0', borderwidth=1,
             buttons=[dict(label='全部关系 (2475条)', method='update',
                           args=[{'visible': [True] * (n_edge + 1)}]),
                      *[dict(label=f'{rel} ({len(rel_groups[rel])}条)', method='update',
                             args=[{'visible': [True] + [i == idx for i in range(n_edge)]}])
                        for idx, rel in enumerate(edge_trace_names)]]),
        dict(type='buttons', direction='right', x=0.01, y=1.0, xanchor='left', yanchor='top',
             font=dict(color='#1f2937', size=12, weight='bold'), bgcolor='#eaf1f9',
             bordercolor='#7e9cc0', borderwidth=1,
             buttons=[dict(label=name, method='relayout',
                           args=[{'scene.camera': cam}]) for name, cam in presets.items()]),
    ],
    annotations=[
        dict(text='<b>关系筛选</b>', x=0.01, y=1.045, xref='paper', yref='paper',
             showarrow=False, font=dict(color='#2980b9', size=13, weight='bold')),
        dict(text='<b>视角</b>', x=0.01, y=0.995, xref='paper', yref='paper',
             showarrow=False, font=dict(color='#2980b9', size=13, weight='bold')),
        dict(text='拖动旋转 · 滚轮缩放 · 悬停查看类别/定义 · 点击图例筛选关系',
             x=0.99, y=1.045, xref='paper', yref='paper', xanchor='right',
             showarrow=False, font=dict(color='#64748b', size=12)),
    ],
    scene=dict(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        bgcolor='#ffffff',
        camera=dict(eye=dict(x=1.55, y=1.05, z=0.8), up=dict(x=0, y=0, z=1)),
    ),
    margin=dict(b=10, l=10, r=10, t=90),
)

# ---------- 自动旋转（鼠标一动即停） ----------
auto_rotate_js = """
<script>
document.addEventListener('DOMContentLoaded', function(){
  var gd = document.querySelector('.plotly-graph-div');
  if(!gd) return;
  var rotating = true; var anim = null;
  function stop(){ rotating = false; if(anim) cancelAnimationFrame(anim); }
  ['mousedown','touchstart','wheel'].forEach(function(ev){
    document.addEventListener(ev, function(){ stop(); }, {passive:true});
  });
  var last = null;
  function rotate(t){
    if(!rotating) return;
    if(!last) last = t;
    var dt = (t-last)/1000; last = t;
    if(gd._fullLayout && gd._fullLayout.scene && gd._fullLayout.scene.camera){
      var el = gd._fullLayout.scene.camera;
      if(el && el.eye){
        var a = Math.max(0.05, dt * 0.18);
        var x = el.eye.x*Math.cos(a) + el.eye.z*Math.sin(a);
        var z = -el.eye.x*Math.sin(a) + el.eye.z*Math.cos(a);
        try { Plotly.relayout(gd, 'scene.camera', {eye:{x:x, y:el.eye.y, z:z}}); } catch(e){}
      }
    }
    anim = requestAnimationFrame(rotate);
  }
  anim = requestAnimationFrame(rotate);
});
</script>
"""
out = '航空术语知识图谱_3D交互.html'
html = fig.to_html(include_plotlyjs='inline', full_html=True, config={'scrollZoom': True})
html = html.replace('</body>', auto_rotate_js + '</body>')
open(out, 'w', encoding='utf-8').write(html)
print('OK 已输出:', out)
print('节点', len(nodes), '| 关系', len(relations), '| 弧线边', sum(len(v) for v in rel_groups.values()),
      '| 红/蓝/灰', sum(1 for n in nodes if node_tier(degree[n])==2),
      sum(1 for n in nodes if node_tier(degree[n])==1), sum(1 for n in nodes if node_tier(degree[n])==0))
