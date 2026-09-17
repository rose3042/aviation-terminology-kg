# -*- coding: utf-8 -*-
"""KG六视图网格（2×3）→ fig_kg_grid.png。"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
matplotlib.rcParams['font.family'] = ['Times New Roman', 'SimSun']

views = [
    ('kg_3d_view1_default.png', '(a) 整体视图（默认视角）'),
    ('kg_3d_view2_rotated.png', '(b) 旋转视角'),
    ('kg_3d_view3_elevated.png', '(c) 俯视视角'),
    ('kg_3d_view4_zoom.png', '(d) 核心连接簇放大'),
    ('kg_3d_view5_clean.png', '(e) 精简展示（去背景）'),
    ('kg_3d_view5_closeup.png', '(f) 近景特写（细粒度拓扑）'),
]

fig, axes = plt.subplots(2, 3, figsize=(13.2, 7.6), dpi=300)
fig.patch.set_facecolor('white')
for ax, (fname, cap) in zip(axes.flat, views):
    img = mpimg.imread(os.path.join('_kg_shots', fname))
    ax.imshow(img)
    ax.set_title(cap, fontsize=10.5, pad=6, color='#1F3446')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
fig.subplots_adjust(wspace=0.05, hspace=0.14, left=0.01, right=0.99, top=0.97, bottom=0.02)
fig.savefig('_fig/fig_kg_grid.png', dpi=300, facecolor='white')
plt.close(fig)
print('OK fig_kg_grid.png')
