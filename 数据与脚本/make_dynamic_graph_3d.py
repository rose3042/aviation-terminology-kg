# -*- coding: utf-8 -*-
"""
生成 3D 动态交互式航空术语知识图谱（HTML，Plotly Scatter3d）
v2 升级：力导向3D布局 + 节点按连接度分级着色 + 大节点光晕 + 丰富交互
支持 360° 旋转、滚轮缩放、点击查看定义、图例筛选关系类型。
输出：aviation_kg_dynamic_3d.html
"""
import json, os, sys, math
from collections import Counter, defaultdict

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# ------------------------------------------------------------------
# 1. 读取数据
# ------------------------------------------------------------------
def load_relations():
    for fn in ['merged_relations.json', 'relations_core_v2.json', 'relations.json']:
        if os.path.exists(fn):
            with open(fn, 'r', encoding='utf-8') as f:
                rels = json.load(f)
            rels = [r for r in rels if r.get('relation') != 'none']
            print(f"读取 {fn}: {len(rels)} 条有效关系")
            return rels
    raise FileNotFoundError("没有找到关系文件")

relations = load_relations()

with open('auto_labels_clean.json', 'r', encoding='utf-8') as f:
    clean = json.load(f)
term_def = {item['term']: item['definition'] for item in clean}

# 词典定义兜底（全词典匹配池里的对象术语可能不在 clean 集里）
import re
DESKTOP = r'D:\360MoveData\Users\叶丽娜\Desktop'
for fn in ['dictionary_clean.txt', 'dictionary_full.txt']:
    p = os.path.join(DESKTOP, fn)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            for line in f.read().splitlines():
                line = line.strip()
                m = re.match(r'^([A-Za-z][A-Za-z0-9\- ]*?(?:\([^)]+\))?)\.\s+(.+)$', line)
                if m:
                    t, d = m.group(1).strip(), m.group(2).strip()
                    if t not in term_def and len(d) >= 8:
                        term_def[t] = d
        print(f"已加载词典定义补充: {fn}")
        break

nodes = sorted(set(n for r in relations for n in (r['subject'], r['object'])))
print(f"节点: {len(nodes)}, 边: {len(relations)}")

degree = Counter()
for r in relations:
    degree[r['subject']] += 1
    degree[r['object']] += 1

max_deg = max(degree.values()) if degree else 1

# ------------------------------------------------------------------
# 2. 3D 力导向布局
# ------------------------------------------------------------------
import plotly.graph_objects as go
import networkx as nx

G = nx.Graph()
G.add_nodes_from(nodes)
for r in relations:
    G.add_edge(r['subject'], r['object'])

# 力导向 3D 布局：提高 k 值让 hub 更明显，iterations 更多让布局稳定
# v3：k 1.2→1.7、iterations 150→300，节点分布更散，密集核心不再糊成一团
pos = nx.spring_layout(G, dim=3, seed=42, k=1.7, iterations=300)
# 归一化到合理范围
all_coords = list(pos.values())
xs_all = [c[0] for c in all_coords]
ys_all = [c[1] for c in all_coords]
zs_all = [c[2] for c in all_coords]
scale = 20 / max(max(xs_all) - min(xs_all), max(ys_all) - min(ys_all), max(zs_all) - min(zs_all))
pos = {n: (v[0]*scale, v[1]*scale, v[2]*scale) for n, v in pos.items()}

# ------------------------------------------------------------------
# 3. 边轨迹（按关系类型着色，细而优雅）
# ------------------------------------------------------------------
REL_COLORS = {
    'is_a':        '#5B7FB5',  # 蓝
    'part_of':     '#E8A33D',  # 橙
    'consists_of': '#C77DB3',  # 粉紫
    'has_property': '#8AB17D', # 绿
    'located_in':  '#5BA89E',  # 青
    'controls':    '#C96A5E',  # 珊瑚红
    'operates_with': '#7D8FC4',# 蓝紫
    'causes':      '#D58B8B',  # 浅玫红
    'used_for':    '#6FA0A8',  # 蓝灰
    'measures':    '#9A86C9',  # 紫
    'defined_by':  '#8A8FB0',  # 灰蓝
    'synonym_of':  '#7BA86A',  # 鼠尾草绿
}
by_type = defaultdict(list)
for r in relations:
    by_type[r['relation']].append((r['subject'], r['object']))

edge_traces = []
for rel, pairs in by_type.items():
    color = REL_COLORS.get(rel, '#888')
    xs, ys, zs = [], [], []
    for s, o in pairs:
        if s in pos and o in pos:
            x0, y0, z0 = pos[s]
            x1, y1, z1 = pos[o]
            xs.extend([x0, x1, None])
            ys.extend([y0, y1, None])
            zs.extend([z0, z1, None])
    edge_traces.append(go.Scatter3d(
        x=xs, y=ys, z=zs, mode='lines',
        line=dict(width=1.0, color=color),
        hoverinfo='none',
        opacity=0.22,          # v3：细而透明，2475条边叠在一起不再发黑
        name=f'{rel} ({len(pairs)})',
    ))

# ------------------------------------------------------------------
# 4. 节点轨迹（连接度分级着色 + 大小）
# ------------------------------------------------------------------
# 节点按连接度分 3 级：hub(>=6), mid(3-5), leaf(<3)
def node_tier(n):
    d = degree.get(n, 0)
    if d >= 6: return 2
    elif d >= 3: return 1
    return 0

node_x = [pos[n][0] for n in nodes]
node_y = [pos[n][1] for n in nodes]
node_z = [pos[n][2] for n in nodes]
node_size = [6 + 3 * min(degree.get(n, 0), 10) for n in nodes]    # v3：缩小，密集核心少重叠

# 颜色：BERT 论文淡色系三档 + 同色系深描边（浅底深边，重叠不再发黑）
tier_color  = {2: '#F4CCCC', 1: '#C6D9F1', 0: '#E8EAED'}   # 淡红(枢纽)/淡蓝(重要)/浅灰(一般)
tier_border = {2: '#C55A50', 1: '#4E7AB5', 0: '#9AA5B1'}
node_color  = [tier_color[node_tier(n)] for n in nodes]
node_border = [tier_border[node_tier(n)] for n in nodes]

# 只给最顶层的枢纽（度>=8）显示标签，最多 80 个，避免糊成一团
TOP_HUBS = {n for n, _ in degree.most_common(80) if degree.get(n, 0) >= 8}
node_text = []
for n in nodes:
    if n in TOP_HUBS:
        node_text.append(n)
    else:
        node_text.append('')

node_hover = []
for n in nodes:
    d = term_def.get(n, '')
    d_short = d[:120] + ('...' if len(d) > 120 else '')
    tier = {2: '核心枢纽', 1: '重要术语', 0: '一般术语'}[node_tier(n)]
    node_hover.append(f"<b>{n}</b><br><span style='color:#555'>[{tier}]</span> | 连接度: {degree.get(n,0)}<br>{d_short}")

node_trace = go.Scatter3d(
    x=node_x, y=node_y, z=node_z,
    mode='markers+text',
    text=node_text,
    textposition='top center',
    textfont=dict(size=12, color='#2c3e50'),     # 深色标签，白底清晰
    hovertext=node_hover,
    hoverinfo='text',
    marker=dict(size=node_size, color=node_color,
                line=dict(width=0.8, color=node_border),
                opacity=0.92,
                symbol='circle'),
)

# ------------------------------------------------------------------
# 5. 图例 + 布局（白底浅色，清晰专业）
# ------------------------------------------------------------------
fig = go.Figure(data=edge_traces + [node_trace])

fig.update_layout(
    title=dict(
        text='✈️  航空术语知识图谱（2184节点 · 2475关系）',
        font=dict(size=22, color='#2c3e50'),
    ),
    showlegend=True,
    legend=dict(font=dict(size=12, color='#2c3e50'), bgcolor='rgba(255,255,255,0.8)'),
    paper_bgcolor='#ffffff',
    plot_bgcolor='#ffffff',
    margin=dict(b=10, l=10, r=10, t=70),
    scene=dict(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        bgcolor='#ffffff',
        camera=dict(
            eye=dict(x=1.15, y=1.15, z=1.05),  # 更近，看得更清楚
            up=dict(x=0, y=0, z=1),
        ),
    ),
    height=1200,              # 更高画布
    autosize=True,
)

# 注入自定义 JS：
# 1) 自动缓慢旋转：仅在用户"没碰图"时生效；一旦鼠标按下/触摸/滚轮即永久停止，把控制权完全还给用户
# 2) plotly.js 内嵌进 HTML（include_plotlyjs=True），离线也能交互
auto_rotate_js = """
<script>
document.addEventListener('DOMContentLoaded', function(){
  var gd = document.querySelector('.plotly-graph-div');
  if(!gd) return;
  var rotating = true;
  var anim = null;
  function stop(){
    rotating = false;
    if(anim) cancelAnimationFrame(anim);
  }
  // 用户一交互就永久停止自动旋转，避免动画抢走控制权
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
        // 从当前视角缓慢绕垂直轴旋转，速度很慢，不打扰用户
        var a = Math.max(0.05, dt * 0.15);
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
with open(os.path.join(BASE, 'aviation_kg_dynamic_3d.html'), 'w', encoding='utf-8') as f:
    # include_plotlyjs=True 把整个 plotly.js 内嵌进 HTML，离线可交互
    html = fig.to_html(include_plotlyjs=True, full_html=True)
    html = html.replace('</body>', auto_rotate_js + '</body>')
    f.write(html)

print(f"✅ 3D图谱已生成: aviation_kg_dynamic_3d.html")
print(f"   节点 {len(nodes)}, 边 {len(relations)}, 关系类型 {len(by_type)} 种")
print(f"   支持：360°拖拽旋转 / 滚轮缩放 / 点击查看定义 / 图例筛选 / 自动旋转")
