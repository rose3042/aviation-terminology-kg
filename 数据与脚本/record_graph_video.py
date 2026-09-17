# -*- coding: utf-8 -*-
"""
知识图谱演示视频（matplotlib 渲染，不依赖浏览器）
三段式演示：整体旋转 → 拉近看枢纽 → 缓慢扫视关系。白底、清晰、可发给导师。
输出：知识图谱演示视频.mp4
用法：python record_graph_video.py
"""
import json, os, sys, subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import imageio_ffmpeg

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# C盘已满（仅剩几百MB）→ 把所有临时文件指到 D 盘，避免 ffmpeg/Python 往 C 盘写
_D_TMP = os.path.join(BASE, '_tmp_video')
os.makedirs(_D_TMP, exist_ok=True)
os.environ['TMP'] = _D_TMP
os.environ['TEMP'] = _D_TMP
os.environ['TMPDIR'] = _D_TMP

# 中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# ---------- 加载数据 ----------
rels = [r for r in json.load(open('merged_relations.json', encoding='utf-8'))
        if r.get('relation') != 'none']
nodes = sorted(set(n for r in rels for n in (r['subject'], r['object'])))

from collections import Counter
degree = Counter()
for r in rels:
    degree[r['subject']] += 1
    degree[r['object']] += 1

# ---------- 力导向 3D 布局（固定 seed 保证可复现） ----------
import networkx as nx
G = nx.Graph()
G.add_edges_from((r['subject'], r['object']) for r in rels)
pos = nx.spring_layout(G, dim=3, seed=42, k=1.2, iterations=150)

# 归一化
allc = np.array(list(pos.values()))
span = allc.max(axis=0) - allc.min(axis=0)
s = 20 / span.max()
pos = {n: tuple(v * s) for n, v in pos.items()}

# 边数据
REL_COLORS = {
    'synonym_of': '#1e8449',  'is_a': '#1f4e79',     'part_of': '#c05621',
    'has_property': '#6c3483','located_in': '#9a7d0a','controls': '#b03a2e',
    'operates_with': '#148f77','causes': '#b0255d',  'consists_of': '#a04000',
    'used_for': '#0e6655',    'measures': '#34495e', 'defined_by': '#5b2c6f',
}
by_type = {}
for r in rels:
    by_type.setdefault(r['relation'], []).append((r['subject'], r['object']))

# 节点大小与颜色（按度分级）
max_deg = max(degree.values())
node_size = {n: 30 + 90 * (degree.get(n, 0) / max_deg) ** 1.5 for n in nodes}
def tier(n):
    d = degree.get(n, 0)
    return 2 if d >= 8 else (1 if d >= 3 else 0)
tier_color = {2: '#e74c3c', 1: '#2980b9', 0: '#aeb6bf'}
node_color = [tier_color[tier(n)] for n in nodes]
# 给最高度 30 个节点标标签
top30 = {n for n, _ in degree.most_common(30) if degree.get(n, 0) >= 8}

# ---------- 渲染参数 ----------
FPS = 30
DURATION = 18
n_frames = FPS * DURATION
fig = plt.figure(figsize=(12, 8), dpi=110)
outdir = os.path.join(BASE, 'frames_tmp')
os.makedirs(outdir, exist_ok=True)

print(f"渲染 {n_frames} 帧...")

for i in range(n_frames):
    t = i / FPS
    fig.clf()
    ax = fig.add_subplot(111, projection='3d')

    # 相机运动
    if t < 8:          # 阶段1：整体旋转
        ang = (t / 8) * 2 * np.pi
        elev, azim = 22, np.degrees(ang)
        dist = 42
    elif t < 13:       # 阶段2：拉近
        prog = (t - 8) / 5
        ang = (t / 8) * 2 * np.pi
        elev, azim = 22 - 6 * prog, np.degrees(ang)
        dist = 42 - 16 * prog
    else:              # 阶段3：缓慢扫视
        ang = (t / 8) * 2 * np.pi + (t - 13) * 0.2
        elev, azim = 16, np.degrees(ang)
        dist = 26

    # 边（按类型着色）
    for rel, pairs in by_type.items():
        for s, o in pairs:
            if s in pos and o in pos:
                xs = [pos[s][0], pos[o][0]]
                ys = [pos[s][1], pos[o][1]]
                zs = [pos[s][2], pos[o][2]]
                ax.plot(xs, ys, zs, color=REL_COLORS.get(rel, '#555'),
                        linewidth=0.9, alpha=0.6)

    # 节点
    xs = [pos[n][0] for n in nodes]
    ys = [pos[n][1] for n in nodes]
    zs = [pos[n][2] for n in nodes]
    sizes = [node_size[n] for n in nodes]
    ax.scatter(xs, ys, zs, c=node_color, s=sizes, depthshade=True,
               edgecolors='#7f8c8d', linewidths=0.4)

    # 枢纽标签
    for n in top30:
        if n in pos:
            ax.text(pos[n][0], pos[n][1], pos[n][2] + 1.2, n,
                    fontsize=8, color='#2c3e50', ha='center')

    # 白底
    ax.set_facecolor('white')
    ax.grid(False)
    ax.xaxis.set_pane_color((1, 1, 1, 1))
    ax.yaxis.set_pane_color((1, 1, 1, 1))
    ax.zaxis.set_pane_color((1, 1, 1, 1))
    ax.xaxis.line.set_color('white')
    ax.yaxis.line.set_color('white')
    ax.zaxis.line.set_color('white')
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
    ax.view_init(elev=elev, azim=azim)
    ax.set_title('航空术语知识图谱 · 2184节点/2475关系', fontsize=15, pad=10, color='#2c3e50')

    fig.savefig(os.path.join(outdir, f'f_{i:04d}.png'),
                facecolor='white', bbox_inches='tight')
    if i % 45 == 0:
        print(f"  帧 {i}/{n_frames} (t={t:.1f}s)")

plt.close(fig)
print("帧渲染完成，合成视频...")

# ---------- 合成 MP4 ----------
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
video = os.path.join(BASE, '知识图谱演示视频.mp4')
cmd = [ffmpeg_exe, '-y', '-framerate', str(FPS),
       '-i', os.path.join(outdir, 'f_%04d.png'),
       '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20',
       '-r', str(FPS), video]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode == 0 and os.path.exists(video):
    print(f"✅ 视频已生成: {video}  ({os.path.getsize(video)/1024/1024:.1f}MB)")
    import shutil
    shutil.rmtree(outdir, ignore_errors=True)
    print("已清理临时帧")
else:
    print("合成失败，完整 stderr:")
    print(r.stderr[-3000:])
    print(f"（保留帧目录便于诊断: {outdir}）")
