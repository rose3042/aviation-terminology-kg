# -*- coding: utf-8 -*-
"""
ESP 投稿英文稿专用图（仿 Wang & Friginal 2025 风格：白底、细线、彩色、数值标注）
配色原则：英文=蓝系（定义域深蓝/真实域中蓝），中文=橙系（陶土橙/金/深橙红），
          全文无灰色系色块；英文原图（图6=en_domains_prf 蓝蓝红）配色保持不变。
每张图保存前做文字溢出自检：任何 text 超出 figure 画布边界都会打印 ⚠。
用法: py -3.9 -X utf8 _make_figs_esp.py
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, json, collections, os

plt.rcParams['font.family'] = ['Times New Roman', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['axes.edgecolor'] = '#444444'
plt.rcParams['xtick.color'] = '#333333'
plt.rcParams['ytick.color'] = '#333333'
plt.rcParams['text.color'] = '#111111'

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_fig_esp')
os.makedirs(OUT, exist_ok=True)

# ================= 彩色配色（无灰系色块） =================
EN_DEF  = '#1F4E79'   # 定义域（训练域）深蓝 —— 与英文原图一致
EN_REAL = '#4477AA'   # 英文真实语域 中蓝 —— 与英文原图一致
ZH      = '#D9654F'   # 中文主色 陶土橙红
ZH_P    = '#E8823A'   # 中文字 P 中橙
ZH_R    = '#F0B04C'   # 中文字 R 浅金
ZH_F1   = '#B8442F'   # 中文字 F1 深红橙
GAP     = '#C0392B'   # 掉点标注 红 —— 与英文原图一致
LIGHT   = '#9DC3E6'   # 浅蓝（基线图中"其他方法"）
INK     = '#111111'
FILL_KG = '#FFF4EC'   # KG 框浅橙填充

# 文字溢出自检：每个 text 的渲染框须落在 figure 画布内
def check_text_overflow(fig, name):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    bad = 0
    for ax in fig.axes:
        for t in ax.texts:
            if not t.get_text().strip():
                continue
            bb = t.get_window_extent(renderer=r)
            if bb.x0 < -0.5 or bb.y0 < -0.5 or bb.x1 > W + 0.5 or bb.y1 > H + 0.5:
                bad += 1
                print(f'  ⚠ {name}: 文字出画布边界 {t.get_text()[:36]!r}  bbox=({bb.x0:.0f},{bb.y0:.0f},{bb.x1:.0f},{bb.y1:.0f})')
    if bad:
        print(f'  → {name}: 共 {bad} 处文字出界，需修正！')
    else:
        print(f'  ✓ {name}: 全部文字在画布内')

def SAVE(fig, name, check=True):
    if check:
        check_text_overflow(fig, name)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(path.replace('.png', '.svg'), bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('✓', path)

# =========================================================
# Fig 1. 语域鸿沟：英文定义域→真实域 vs 中文同域
# =========================================================
fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.1), sharey=True)
fig.patch.set_facecolor('white')
y_lim = (0.0, 1.0)

# --- Panel A: English ---
ax = axes[0]
cats = ['Definitional\n(train)', 'Regulation', 'Operations', 'Maintenance']
vals = [0.78, 0.508, 0.513, 0.581]
x = np.arange(len(cats))
colors = [EN_DEF, EN_REAL, EN_REAL, EN_REAL]
for xi, v, c in zip(x, vals, colors):
    ax.plot([xi, xi], [0, v], color=c, lw=1.2, alpha=0.55, zorder=1)
    ax.scatter([xi], [v], s=46, color=c, zorder=3, edgecolor='white', lw=0.6)
    ax.text(xi, v + 0.045, f'{v:.2f}'.rstrip('0').rstrip('.'), ha='center', va='bottom',
            fontsize=8.5, color=c)
overall = 0.525
ax.plot([0, 3.4], [0.78, 0.78], ls='--', color=EN_DEF, lw=0.9, alpha=0.7, zorder=0)
ax.annotate('', xy=(0.05, overall), xytext=(0.05, 0.78),
            arrowprops=dict(arrowstyle='<->', color=GAP, lw=1.2))
ax.text(0.18, (0.78 + overall) / 2, 'ΔF1 = 0.26', color=GAP, fontsize=9, va='center', ha='left')
ax.set_title('English — cross-register', fontsize=10.5, pad=8)
ax.set_xticks(x); ax.set_xticklabels(cats, fontsize=8.5)
ax.set_ylabel('Entity-level F1', fontsize=9.5)
ax.set_ylim(y_lim); ax.set_xlim(-0.4, 3.4)
ax.tick_params(axis='x', length=0)
ax.spines[['top', 'right']].set_visible(False)
ax.axhline(0, color='#555555', lw=0.9)

# --- Panel B: Chinese（中文=橙系） ---
ax = axes[1]
cats = ['Regulation', 'Operations', 'Advisory\ncircular']
vals = [0.977, 0.944, 0.915]
x = np.arange(len(cats))
for xi, v in zip(x, vals):
    ax.plot([xi, xi], [0, v], color=ZH, lw=1.2, alpha=0.55, zorder=1)
    ax.scatter([xi], [v], s=46, color=ZH, zorder=3, edgecolor='white', lw=0.6)
    ax.text(xi, v + 0.045, f'{v:.3f}', ha='center', va='bottom', fontsize=8.5, color=ZH)
overall_zh = 0.949
ax.plot([0, 2.5], [overall_zh, overall_zh], ls='--', color=ZH, lw=0.9, alpha=0.7, zorder=0)
ax.text(2.78, overall_zh, 'overall 0.949', color=ZH, fontsize=8.5, va='center', ha='right')
ax.text(0.28, 0.42, 'ΔF1 ≈ 0', color=GAP, fontsize=9, va='center')
ax.set_title('Chinese — within-register', fontsize=10.5, pad=8)
ax.set_xticks(x); ax.set_xticklabels(cats, fontsize=8.5)
ax.set_ylim(y_lim); ax.set_xlim(-0.4, 3.0)
ax.tick_params(axis='x', length=0)
ax.spines[['top', 'right']].set_visible(False)
ax.axhline(0, color='#555555', lw=0.9)

fig.tight_layout(w_pad=2.2)
SAVE(fig, 'fig_esp_registergap.png')

# =========================================================
# Fig 2. 英文真实语域 P/R/F1 分组柱状（原图6内容，配色保持蓝蓝红不动）
# =========================================================
fig, ax = plt.subplots(figsize=(4.4, 3.0))
fig.patch.set_facecolor('white')
domains = ['Regulation', 'Operations', 'Maintenance']
P = [0.620, 0.623, 0.657]
R = [0.431, 0.436, 0.520]
F1 = [0.508, 0.513, 0.581]
width = 0.26
x = np.arange(len(domains))
bars = [
    (np.array(P), x - width, 'Precision', EN_DEF),
    (np.array(R), x, 'Recall', EN_REAL),
    (np.array(F1), x + width, 'F1', GAP),
]
for v, xi, label, c in bars:
    ax.bar(xi, v, width, label=label, color=c, edgecolor='white', lw=0.5, alpha=0.92)
    for xb, yb in zip(xi, v):
        ax.text(xb, yb + 0.012, f'{yb:.3f}', ha='center', va='bottom', fontsize=7.6, color=c)
ax.set_xticks(x); ax.set_xticklabels(domains, fontsize=9)
ax.set_ylabel('Score', fontsize=9.5)
ax.set_ylim(0, 0.85)
ax.set_yticks(np.arange(0, 0.81, 0.2))
ax.legend(frameon=False, fontsize=8, loc='upper left', ncol=3, bbox_to_anchor=(0, 1.02, 1, 0.14))
ax.spines[['top', 'right']].set_visible(False)
ax.tick_params(axis='x', length=0)
ax.axhline(0, color='#555555', lw=0.9)
ax.set_title('English real corpus (dictionary-matching gold)', fontsize=9.5, pad=8)
SAVE(fig, 'fig_esp_en_domains_prf.png')

# =========================================================
# Fig 3. 12 类关系分布（真实数据）
# =========================================================
rels = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'merged_relations.json'), encoding='utf-8'))
c = collections.Counter(r['relation'] for r in rels)
total = sum(c.values())
order = sorted(c.items(), key=lambda kv: kv[1])           # 升序，画成横向条形
labels = [f'{k} ({v}, {v/total*100:.1f}%)' for k, v in order]
counts = [v for _, v in order]
fig, ax = plt.subplots(figsize=(5.6, 3.4))
fig.patch.set_facecolor('white')
colors3 = [EN_DEF if k in ('is_a', 'part_of') else (EN_REAL if k == 'synonym_of' else LIGHT)
           for k, _ in order]
ax.barh(np.arange(len(labels)), counts, color=colors3, edgecolor='white', lw=0.5, height=0.62)
ax.set_yticks(np.arange(len(labels))); ax.set_yticklabels([k for k, _ in order], fontsize=8.5)
for yi, (k, v) in enumerate(order):
    ax.text(v + 8, yi, f'{v}  ({v/total*100:.1f}%)', va='center', fontsize=8, color='#444444')
ax.set_xlim(0, max(counts) * 1.28)
ax.set_xlabel('Number of relations (n = 2,475)', fontsize=9)
ax.set_title('Semantic relation types in the aviation terminology graph', fontsize=9.5, pad=8)
ax.spines[['top', 'right']].set_visible(False)
ax.tick_params(axis='y', length=0)
ax.axvline(0, color='#555555', lw=0.9)
fig.tight_layout()
SAVE(fig, 'fig_esp_relation_dist.png')

# =========================================================
# Fig 4. 中文真实语域 P/R/F1（与英文 Figure 2 镜像，橙系）
# =========================================================
fig, ax = plt.subplots(figsize=(4.4, 3.0))
fig.patch.set_facecolor('white')
domains = ['Regulation', 'Operations', 'Advisory\ncircular']
P = [0.973, 0.943, 0.900]
R = [0.980, 0.945, 0.930]
F1 = [0.977, 0.944, 0.915]
width = 0.26
x = np.arange(len(domains))
# 橙系（中文）：P 中橙、R 浅金、F1 深红橙，F1 最深（镜像英文图中 F1 最深）
bars = [
    (np.array(P), x - width, 'Precision', ZH_P),
    (np.array(R), x, 'Recall', ZH_R),
    (np.array(F1), x + width, 'F1', ZH_F1),
]
for v, xi, label, c in bars:
    ax.bar(xi, v, width, label=label, color=c, edgecolor='white', lw=0.5, alpha=0.92)
    for xb, yb in zip(xi, v):
        ax.text(xb, yb + 0.012, f'{yb:.3f}', ha='center', va='bottom', fontsize=7.6, color=c)
ax.set_xticks(x); ax.set_xticklabels(domains, fontsize=9)
ax.set_ylabel('Score', fontsize=9.5)
ax.set_ylim(0, 1.1)
ax.set_yticks(np.arange(0, 1.01, 0.2))
ax.legend(frameon=False, fontsize=8, loc='upper left', ncol=3, bbox_to_anchor=(0, 1.02, 1, 0.14))
ax.spines[['top', 'right']].set_visible(False)
ax.tick_params(axis='x', length=0)
ax.axhline(0, color='#555555', lw=0.9)
ax.set_title('Chinese real corpus (dictionary-matching gold)', fontsize=9.5, pad=8)
SAVE(fig, 'fig_esp_zh_domains_prf.png')

# =========================================================
# Fig 5. 双语多基线对照（EN 跨语域 vs ZH 同语域，无灰点）
# =========================================================
fig, axes = plt.subplots(1, 2, figsize=(7.6, 2.9), sharey=True)
fig.patch.set_facecolor('white')

# --- Panel A: English (cross-register) ---
ax = axes[0]
methods_en = ['Rule\nheuristic', 'BiLSTM-CRF', 'BERT', 'Dictionary\nmatching*']
vals_en = [0.001, 0.331, 0.525, 1.0]
x_en = np.arange(len(methods_en))
for xi, v in zip(x_en, vals_en):
    c = EN_REAL if xi == 2 else LIGHT
    ax.plot([xi, xi], [0, v], color=c, lw=1.2, alpha=0.6, zorder=1)
    ax.scatter([xi], [v], s=48, color=c, zorder=3, edgecolor='white', lw=0.6)
    ax.text(xi, v + 0.04, f'{v:.3f}', ha='center', va='bottom', fontsize=8, color=c)
ax.set_xticks(x_en); ax.set_xticklabels(methods_en, fontsize=7.8)
ax.set_title('English — cross-register', fontsize=10.5, pad=8)
ax.set_ylabel('Entity-level F1', fontsize=9.5)
ax.set_ylim(0, 1.16)
ax.tick_params(axis='x', length=0)
ax.spines[['top', 'right']].set_visible(False)
ax.axhline(0, color='#555555', lw=0.9)

# --- Panel B: Chinese (within-register，BiLSTM=橙 / BERT=蓝突出) ---
ax = axes[1]
methods_zh = ['BiLSTM-CRF', 'BERT']
vals_zh = [0.957, 0.949]
x_zh = np.arange(len(methods_zh))
for xi, v in zip(x_zh, vals_zh):
    c = ZH if xi == 0 else EN_REAL
    ax.plot([xi, xi], [0, v], color=c, lw=1.2, alpha=0.6, zorder=1)
    ax.scatter([xi], [v], s=48, color=c, zorder=3, edgecolor='white', lw=0.6)
    ax.text(xi, v + 0.04, f'{v:.3f}', ha='center', va='bottom', fontsize=8, color=c)
ax.set_xticks(x_zh); ax.set_xticklabels(methods_zh, fontsize=8.5)
ax.set_title('Chinese — within-register', fontsize=10.5, pad=8)
ax.set_ylim(0, 1.16); ax.set_xlim(-0.5, 1.6)
ax.tick_params(axis='x', length=0)
ax.spines[['top', 'right']].set_visible(False)
ax.axhline(0, color='#555555', lw=0.9)
fig.suptitle('Bilingual baseline comparison (real-corpus dictionary-matching gold)', fontsize=10, y=1.04)
fig.tight_layout(w_pad=2.0)
SAVE(fig, 'fig_esp_baselines.png')

# =========================================================
# Fig 6. 图谱规模对比（基础版 vs 全词典版）
# =========================================================
fig, ax = plt.subplots(figsize=(5.0, 2.7))
fig.patch.set_facecolor('white')
groups = ['Base version', 'Full-dictionary\npool']
nodes = [352, 2184]; edges = [388, 2475]
y = np.arange(len(groups))
h = 0.32
b1 = ax.barh(y - h/2, nodes, h, label='Nodes', color=EN_DEF, edgecolor='white', lw=0.5)
b2 = ax.barh(y + h/2, edges, h, label='Edges', color=EN_REAL, edgecolor='white', lw=0.5)
for b in list(b1) + list(b2):
    ax.text(b.get_width() + 55, b.get_y() + b.get_height()/2, f'{int(b.get_width())}',
            va='center', fontsize=8.5, color='#444444')
ax.set_yticks(y); ax.set_yticklabels(groups, fontsize=9)
ax.set_xlim(0, 3050)
ax.set_xlabel('Scale', fontsize=9.5)
ax.legend(frameon=False, fontsize=8, loc='lower right')
ax.spines[['top', 'right']].set_visible(False)
ax.tick_params(axis='y', length=0)
ax.axvline(0, color='#555555', lw=0.9)
fig.tight_layout()
SAVE(fig, 'fig_esp_kg_scale.png')

# =========================================================
# Fig 7. 技术路线（研究流程总览，五阶段 Z 形流程，彩色无灰、文字不溢出）
# =========================================================
fig, ax = plt.subplots(figsize=(8.9, 3.1))
fig.patch.set_facecolor('white')
ax.set_xlim(0, 104); ax.set_ylim(0, 32); ax.axis('off')

def box(x, y, w, h, title, sub, ec, fc='white', fs=8.5, sfs=7.2):
    ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec=ec, lw=0.9, zorder=2))
    ax.text(x + w/2, y + h - 3.2, title, ha='center', va='center', fontsize=fs, color=INK, zorder=3)
    if sub:
        ax.text(x + w/2, y + h - 6.4, sub, ha='center', va='center', fontsize=sfs, color='#444444', zorder=3)

def arrow(x1, y1, x2, y2, ec='#777777', ls='-', lw=1.1):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='-|>', color=ec, lw=lw, ls=ls, shrinkA=0, shrinkB=0), zorder=1)

# --- 左列：输入 ---
box(2, 17, 20, 13, 'Terminology dictionary', '14,670 entries → 3,210\n→ 2,739 canonical terms', EN_DEF)
box(2, 2, 20, 11, 'Real corpus', 'EN 1,491 · ZH 1,500\n(3 registers each)', EN_REAL)

# --- 中列：五阶段 2×2 布局（BERT→Cleaning→Co-occurrence→LLM Z 形） ---
box(27, 17, 29, 13, 'BERT term recognition', 'distant supervision ·\nsequence labeling', EN_DEF)
box(61, 17, 29, 13, 'Rule-based cleaning', 'normalization ·\nalias merging', EN_DEF)
box(27, 2, 29, 11, 'Co-occurrence mining', '3,737 candidate pairs', EN_REAL)
box(61, 2, 29, 11, 'LLM classification', '12-type schema ·\n187 API calls', EN_REAL)

# --- 右列：知识图谱（加宽框、title 缩字号，确保文字不溢出） ---
box(92, 2, 11.5, 28, 'Knowledge\ngraph', '', ZH, fc=FILL_KG, fs=7.5)
ax.text(97.75, 23.0, '2,184 nodes', ha='center', va='center', fontsize=7.4, color='#444444', zorder=3)
ax.text(97.75, 19.5, '2,475 edges', ha='center', va='center', fontsize=7.4, color='#444444', zorder=3)
ax.text(97.75, 16.0, '12 relations', ha='center', va='center', fontsize=7.4, color='#444444', zorder=3)
ax.text(97.75, 12.5, 'Neo4j · 3D', ha='center', va='center', fontsize=7.4, color='#444444', zorder=3)

# --- 主流程箭头（Z 形） ---
arrow(22, 23, 26.5, 23, ec=EN_DEF)          # Dictionary → BERT
arrow(56, 23, 60.5, 23, ec=EN_DEF)          # BERT → Cleaning
arrow(75.5, 16.8, 75.5, 13.2, ec=EN_REAL)    # Cleaning ↓ Co-occurrence（竖线）
arrow(56, 7.5, 60.5, 7.5, ec=EN_REAL)        # Co-occurrence → LLM
arrow(90, 7.5, 91.7, 7.5, ec=ZH)             # LLM → Knowledge graph

# --- 反馈回路：KG → 真实语料语域鸿沟评测（橙虚线） ---
ax.plot([90, 2], [1.3, 1.3], color=ZH, lw=0.9, ls=(0, (3, 2)), zorder=1)
arrow(2, 1.3, 1.2, 1.3, ec=ZH, ls=(0, (3, 2)))     # 左端箭头，指示回环
ax.text(46, 0.55, 'register-gap evaluation (feedback)', fontsize=7, color=ZH, ha='center')

fig.tight_layout()
SAVE(fig, 'fig_esp_pipeline.png')

print('\n全部 ESP 图已生成到 _fig_esp/')
