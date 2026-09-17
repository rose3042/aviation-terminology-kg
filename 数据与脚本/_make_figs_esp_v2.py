# -*- coding: utf-8 -*-
"""
ESP v8k 图件改造 v2 —— 主文 9 图方案中需要新增/重绘的 6 张图（计划第一部分）。
生成（写 _fig_esp/）：
  覆写  fig_esp_registergap.png    （dot+stem → 柱状+落差箭头，英文语域鸿沟）
  覆写  fig_esp_baselines.png      （dot+stem → 柱状+词典上限虚线）
  新增  fig_esp_heatmap.png        （P/R/F₁ × [EN定义/EN真实3域/ZH真实3域]，现值表3/4/6）
  新增  fig_esp_threesys.png       （(a)表层密度 US vs EU + (b)模型F₁ US/EU/CN†）
  覆写  fig_esp_relation_dist.png  （旧附录A1 → 主文 Fig8，读 merged_relations.json）
  新增  fig_esp_kg_compound.png    （(a)全貌 (b)骨干deg≥5 (c)RADAR近景 (d)规模 352→2,184）

数据全部来自本文件顶部 CANON（与 _check_figdata.py 交叉断言 md 表 3/4/6/4c）。
安全约束（不可违背）：
  * 绝不改动 fig_esp_en_domains_prf.png / fig_esp_zh_domains_prf.png / fig_esp_pipeline.png 的生成。
  * 配色只用下方 PAL 色族；热力图保留用户喜欢的 红→黄→绿。
  * 全文无灰色块做“类别色”，灰色只做参考虚线/中性刻度。
用法: python -X utf8 _make_figs_esp_v2.py
"""
import sys, os, json, collections
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import font_manager

for _f in ['C:/Windows/Fonts/times.ttf']:
    pass  # Times New Roman 由 rcParams 名引用即可
font_manager.fontManager.addfont('C:/Windows/Fonts/msyh.ttc') if os.path.exists('C:/Windows/Fonts/msyh.ttc') else None
plt.rcParams['font.family'] = ['Times New Roman', 'SimSun', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['axes.edgecolor'] = '#444444'
plt.rcParams['xtick.color'] = '#333333'
plt.rcParams['ytick.color'] = '#333333'
plt.rcParams['text.color'] = '#111111'

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, '_fig_esp')
os.makedirs(OUT, exist_ok=True)

# ================= 单源调色板（用户定稿 v2：主色只留红+蓝；饱和度压低，对齐参考论文观感）
#   蓝 = 英文/欧体系（钢蓝灰阶）；红 = 中文腿 + 强调/落差（砖红阶）；灰仅限中性/KG 内。
#   2026-09-04：用户指出“参考论文里蓝和红饱和度都不高”→ 全套色相不变、饱和度下调。
PAL = {
    'EN_DEF':  '#3F5D78',   # 英文主色 深钢蓝（定义/训练域；BERT 本系统；EN F₁）
    'EN_REAL': '#7D98B1',   # 英文真实域 中钢蓝（EN R）
    'EN_PALE': '#B3C6D8',   # 浅钢蓝（弱基线 / EN P）
    'EU':      '#94ADC1',   # 欧洲体系 亮些的钢蓝（同一英文模型 → 蓝族浅阶）
    'ZH':      '#A0453A',   # 中文主色 砖红（CCAR 腿 / 中文模型 F₁）
    'ZH_MID':  '#C98D7E',   # 中文 R 中砖红
    'ZH_LT':   '#E9CBC0',   # 中文 P 浅砖红
    'ZH_BR':   '#8A3A2E',   # 中文更深砖红（对比/必要时）
    'GAP':     '#A0453A',   # 落差/强调 砖红 —— 与中文主红同色系
    'INK':     '#111111',
    'DASH':    '#666666',   # 参考虚线灰（中性）
    'RULE_L':  '#B3C6D8',   # 兼容旧 LIGHT 色
    'HUB':     '#A0453A',   # KG 枢纽（deg≥6）砖红
    'IMP':     '#4A6C8C',   # KG 重要（3–5）钢蓝
    'PERI':    '#A6B2BF',   # KG 外围（<3）灰 —— 唯一允许的灰阶色块
}
EN_DEF, EN_REAL, EN_PALE, EU = PAL['EN_DEF'], PAL['EN_REAL'], PAL['EN_PALE'], PAL['EU']
ZH, ZH_LT, ZH_BR, GAP = PAL['ZH'], PAL['ZH_LT'], PAL['ZH_BR'], PAL['GAP']
INK, DASH = PAL['INK'], PAL['DASH']

# ============== 唯一数据源（= 当前 md 表 3/4/6/4c + §4.3.1 逐句口径） ==============
# EN 各域 P/R/F₁（表4），ZH 各域 P/R/F₁（表6），EN 定义域（表3 顶行，P/R/F₁）
CANON = {
    'en_domains': {'reg': (0.620, 0.431, 0.508),
                   'ops': (0.623, 0.436, 0.513),
                   'maint': (0.657, 0.520, 0.581),
                   'all': (0.629, 0.450, 0.525)},          # P/R/F₁ 全实况
    'en_def': {'P': 0.756, 'R': 0.809, 'F1': 0.781},        # 表3 英文定义域（train）
    'zh_domains': {'reg': (0.973, 0.980, 0.977),
                   'ops': (0.943, 0.945, 0.944),
                   'ac':  (0.900, 0.930, 0.915),
                   'all': (0.943, 0.955, 0.949)},
    # 表 4c（密度 = matched spans/100 tokens；CN 密度为字符口径，不入图）
    # 2026-09-14 定案：密度池 12,052，已扣除 13 个残留碎片词条贡献的跨度（见 §3.4）。
    'threesys': {
        'reg':  {'us_d': 10.71, 'eu_d': 8.39,  'us_f1': 0.508, 'eu_f1': 0.424},
        'ops':  {'us_d': 11.55, 'eu_d': 10.12, 'us_f1': 0.513, 'eu_f1': 0.525},
        'maint':{'us_d': 14.06, 'eu_d': 7.83,  'us_f1': 0.581, 'eu_f1': 0.523},
    },
    'cn_f1': [0.977, 0.944, 0.915],                          # 表6/4c 中文腿（同语域）
    'pct_eu_vs_us': ['−22%', '−12%', '−44%'],                # §4.3.1 降幅＝聚合密度比（MWU 仍施于逐句密度）
    'baseline_en': {'rule': 0.001, 'gliner': 0.059, 'bilstm': 0.331, 'bert': 0.525},
    'baseline_zh': {'bilstm': 0.957, 'bert': 0.949},
    'def_f1': 0.781, 'real_overall_f1': 0.525, 'zh_overall_f1': 0.949,
    'kg': {'relations': 2475, 'nodes': 2184, 'n_types': 12,
           'is_a': 768, 'part_of': 390, 'synonym_of': 178,
           'base_nodes': 352, 'base_edges': 388,
           'hub_min_deg': 6, 'imp_min_deg': 3},
}

# ---------------- 通用工具 ----------------
def check_text_overflow(fig, name):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    bad = 0
    for ax in fig.axes:
        for t in ax.texts:
            if not t.get_text().strip():
                continue
            try:
                bb = t.get_window_extent(renderer=r)
            except Exception:
                continue
            if bb.x0 < -0.5 or bb.y0 < -0.5 or bb.x1 > W + 0.5 or bb.y1 > H + 0.5:
                bad += 1
                print(f'  ⚠ {name}: 文字出画布 {t.get_text()[:30]!r}')
    if bad:
        print(f'  → {name}: {bad} 处文字出界，需修正！')
    else:
        print(f'  ✓ {name}: 全部文字在画布内')

def SAVE(fig, name, check=True):
    if check:
        check_text_overflow(fig, name)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    try:
        fig.savefig(path.replace('.png', '.svg'), bbox_inches='tight', facecolor='white')
    except Exception:
        pass
    plt.close(fig)
    print('✓', path)

def panel_letter(ax, letter, x=0.014, y=0.95, bg=True):
    """面板字母 (a)(b)…，带括号、置于面板内侧左上角（2×2 布局也不会被裁）。
    2026-09-04 v3：用户反映 KG 组图四角 (a)(b)(c)(d) 看不清 → 字号 13→16、
    描边浅灰、白底更实，压缩成图后依旧可读。3D 面板自动走 text2D。"""
    kw = dict(fontsize=16, fontweight='bold', ha='left', va='top', color=INK, zorder=20)
    if bg:
        kw['bbox'] = dict(boxstyle='round,pad=0.14', fc='white', ec='#9AA7B4', lw=0.7, alpha=0.95)
    if hasattr(ax, 'get_zlim'):                       # Axes3D
        ax.text2D(x, y, f'({letter})', **kw)
    else:
        ax.text(x, y, f'({letter})', transform=ax.transAxes, **kw)

def val_label(ax, x, y, s, color, fs=8.2, va='bottom', ha='center'):
    ax.text(x, y, s, ha=ha, va=va, fontsize=fs, color=color)

# =========================================================
# Fig 5 (EN 重排)  register gap —— 柱状 + 落差箭头
# =========================================================
def fig_registergap():
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.15), sharey=True)
    fig.patch.set_facecolor('white')
    # --- (a) English: cross-register ---
    ax = axes[0]
    cats = ['Definitional\n(train)', 'Regulation', 'Operations', 'Maintenance']
    vals = [CANON['en_def']['F1'], *[CANON['en_domains'][k][2]
           for k in ('reg', 'ops', 'maint')]]                 # .781/.508/.513/.581
    cols = [EN_DEF, EN_REAL, EN_REAL, EN_REAL]
    x = np.arange(len(cats))
    ax.bar(x, vals, 0.56, color=cols, edgecolor='white', lw=0.5, zorder=2)
    for xi, v, c in zip(x, vals, cols):
        val_label(ax, xi, v + 0.02, f'{v:.3f}', c)
    overall = CANON['real_overall_f1']                         # 0.525
    # 参考虚线置于柱后（zorder 低），只露出间隙段；红双箭头标落差
    ax.axhline(overall, xmin=0.34, xmax=1.0, color=DASH, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.annotate('', xy=(0.5, overall), xytext=(0.5, CANON['def_f1']),
                arrowprops=dict(arrowstyle='<->', color=GAP, lw=1.15))
    ax.text(0.5, 0.84, f"ΔF₁ = {CANON['def_f1'] - overall:.3f}",
            ha='center', va='center', fontsize=9, color=GAP, fontweight='bold', zorder=5)
    ax.text(3.06, overall - 0.012, 'real overall', fontsize=7.4, color=DASH, ha='left', va='top')
    ax.set_xticks(x); ax.set_xticklabels(cats, fontsize=8.4)
    ax.set_ylabel('Entity-level F₁', fontsize=9.5)
    ax.set_ylim(0, 1.0); ax.set_xlim(-0.55, 3.7)
    ax.tick_params(axis='x', length=0)
    ax.spines[['top', 'right']].set_visible(False)
    ax.axhline(0, color='#555555', lw=0.9)
    panel_letter(ax, 'a')
    # --- (b) Chinese: within-register ---
    ax = axes[1]
    cats = ['Regulation', 'Operations', 'Advisory\ncircular']
    vals = [CANON['zh_domains'][k][2] for k in ('reg', 'ops', 'ac')]   # .977/.944/.915
    x = np.arange(len(cats))
    ax.bar(x, vals, 0.56, color=ZH, edgecolor='white', lw=0.5, zorder=2)
    for xi, v in zip(x, vals):
        val_label(ax, xi, v + 0.012, f'{v:.3f}', ZH)
    ax.axhline(CANON['zh_overall_f1'], color=DASH, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.text(2.75, CANON['zh_overall_f1'] + 0.018, 'overall 0.949', fontsize=7.4,
            color=DASH, ha='right', va='bottom')
    ax.set_xticks(x); ax.set_xticklabels(cats, fontsize=8.4)
    ax.set_ylim(0, 1.0); ax.set_xlim(-0.5, 3.0)
    ax.tick_params(axis='x', length=0)
    ax.spines[['top', 'right']].set_visible(False)
    ax.axhline(0, color='#555555', lw=0.9)
    panel_letter(ax, 'b')
    fig.tight_layout(w_pad=1.8)
    SAVE(fig, 'fig_esp_registergap.png')

# =========================================================
# Fig 7 (EN 重排)  baselines —— 柱状 + 词典上限虚线
# =========================================================
def fig_baselines():
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.1), sharey=True)
    fig.patch.set_facecolor('white')
    # --- (a) English cross-register ---
    # 2026-09-04：用户要“多几个对比”→ 加入真实零样本开集基线 GLiNER（表B.1 现值 0.059）。
    ax = axes[0]
    cats = ['Rule\nheuristic', 'GLiNER\n(zero-shot)', 'BiLSTM-\nCRF', 'BERT\n(this study)']
    vals = [CANON['baseline_en']['rule'], CANON['baseline_en']['gliner'],
            CANON['baseline_en']['bilstm'], CANON['baseline_en']['bert']]
    cols = ['#C9D7E5', '#A9BFD4', EN_REAL, EN_DEF]     # 浅→深 = 能力由弱到强，单色连续语义
    x = np.arange(len(cats))
    ax.bar(x, vals, 0.56, color=cols, edgecolor='white', lw=0.5, zorder=3)
    for xi, v, c in zip(x, vals, cols):
        ylab = max(v, 0.03)
        val_label(ax, xi, ylab + 0.025, f'{v:.3f}', c, fs=8.0)
    ax.set_xticks(x); ax.set_xticklabels(cats, fontsize=8.0)
    ax.set_ylabel('Entity-level F₁', fontsize=9.5)
    ax.set_ylim(0, 1.14)
    ax.axhline(1.0, color=DASH, lw=0.9, ls=(0, (4, 3)), zorder=2)
    ax.text(1.5, 1.05, 'dictionary ceiling (gold) = 1.000', fontsize=7.3, color=DASH,
            ha='center', va='bottom')
    ax.set_xlim(-0.5, 3.5)
    ax.tick_params(axis='x', length=0)
    ax.spines[['top', 'right']].set_visible(False)
    ax.axhline(0, color='#555555', lw=0.9)
    panel_letter(ax, 'a')
    # --- (b) Chinese within-register ---
    ax = axes[1]
    cats = ['BiLSTM-CRF', 'BERT\n(this study)']
    vals = [CANON['baseline_zh']['bilstm'], CANON['baseline_zh']['bert']]
    cols = [ZH_LT, ZH]
    x = np.arange(len(cats))
    ax.bar(x, vals, 0.42, color=cols, edgecolor='white', lw=0.5, zorder=3)
    for xi, v, c in zip(x, vals, cols):
        val_label(ax, xi, v + 0.012, f'{v:.3f}', c)
    ax.axhline(1.0, color=DASH, lw=0.9, ls=(0, (4, 3)), zorder=2)
    ax.text(1.0, 1.05, 'dictionary ceiling (gold) = 1.000', fontsize=7.3, color=DASH,
            ha='center', va='bottom')
    ax.set_xticks(x); ax.set_xticklabels(cats, fontsize=8.2)
    ax.set_ylim(0, 1.14); ax.set_xlim(-0.6, 1.6)
    ax.tick_params(axis='x', length=0)
    ax.spines[['top', 'right']].set_visible(False)
    ax.axhline(0, color='#555555', lw=0.9)
    panel_letter(ax, 'b')
    fig.tight_layout(w_pad=2.4)
    SAVE(fig, 'fig_esp_baselines.png')

# =========================================================
# Fig 3 (新增)  heatmap —— P/R/F₁ × 7 列（表3/4/6 现值），红→黄→绿
# =========================================================
def fig_heatmap():
    data = np.array([
        # P 行
        [CANON['en_def']['P'], *[CANON['en_domains'][k][0] for k in ('reg', 'ops', 'maint')],
         *[CANON['zh_domains'][k][0] for k in ('reg', 'ops', 'ac')]],
        # R 行
        [CANON['en_def']['R'], *[CANON['en_domains'][k][1] for k in ('reg', 'ops', 'maint')],
         *[CANON['zh_domains'][k][1] for k in ('reg', 'ops', 'ac')]],
        # F₁ 行
        [CANON['en_def']['F1'], *[CANON['en_domains'][k][2] for k in ('reg', 'ops', 'maint')],
         *[CANON['zh_domains'][k][2] for k in ('reg', 'ops', 'ac')]],
    ])
    # 冷暖三段：低分＝钢蓝、中＝白、高分＝砖红（与全稿 EN蓝/ZH红 语义一致，无黄绿）
    cmap = mcolors.LinearSegmentedColormap.from_list(
        'bwr_muted', [PAL['EN_REAL'], '#F5F5F5', PAL['ZH']])
    fig, ax = plt.subplots(figsize=(9.8, 3.35))
    fig.patch.set_facecolor('white')
    im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=0.3, vmax=1.0, origin='upper', zorder=1)
    # 格内数值（近白中段用深字，两端用白字）
    for i in range(3):
        for j in range(7):
            v = data[i, j]
            ax.text(j, i, f'{v:.3f}', ha='center', va='center', fontsize=8.6,
                    color='white' if (v < 0.46 or v > 0.86) else '#141414',
                    zorder=3, fontweight='bold')
    # 组间分隔（EN 定义 | EN 真实 | ZH 真实）
    for xv in (0.5, 3.5):
        ax.axvline(xv, color='white', lw=2.4)
    # 顶部组标题（置于图像顶边上方，imshow 已占 -0.5..2.5，故扩 ylim）
    ax.set_ylim(3.0, -0.65)
    g = [
        (0.0, 'English — definitional (train)', EN_DEF),
        (2.0, 'English — real (cross-register)', EN_DEF),
        (5.0, 'Chinese — real (same-register)', ZH),
    ]
    for cx, label, col in g:
        ax.text(cx, 2.62, label, ha='center', va='bottom', fontsize=8.8, color=col, fontweight='bold')
    # 行/列标签
    ax.set_xticks(np.arange(7))
    ax.set_xticklabels(['Definitional', 'Regulation', 'Operations', 'Maintenance',
                        'Regulation', 'Operations', 'Advisory\ncircular'], fontsize=7.6)
    # ★ 2026-09-12 修正：origin='upper' 下第 0 行画在【顶部】y=0，
    #   故标签必须按 0,1,2 配对。原写 set_yticks([2,1,0]) 使标签整体错位一格：
    #   顶行(真值 P)被标成 F₁、底行(真值 F₁)被标成 P（中间 R 因行号对称而侥幸正确）。
    #   v9 已改用 _make_fig_heatmap_v9.fig_heatmap_v9()，此处同步修好以免再生成错图。
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(['P', 'R', 'F₁'], fontsize=9)
    ax.tick_params(length=0)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('Entity-level score', fontsize=8.5)
    cbar.ax.tick_params(labelsize=8)
    fig.tight_layout()
    SAVE(fig, 'fig_esp_heatmap.png')

# =========================================================
# Fig 6 (新增)  three-system probe —— (a)密度 US vs EU (b)模型F₁ US/EU/CN†
# =========================================================
def fig_threesys():
    ts = CANON['threesys']
    regs = ['Regulation', 'Operations', 'Maintenance']
    us_d = [ts[r]['us_d'] for r in ('reg', 'ops', 'maint')]
    eu_d = [ts[r]['eu_d'] for r in ('reg', 'ops', 'maint')]
    us_f = [ts[r]['us_f1'] for r in ('reg', 'ops', 'maint')]
    eu_f = [ts[r]['eu_f1'] for r in ('reg', 'ops', 'maint')]
    cn_f = CANON['cn_f1']

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.5), gridspec_kw={'width_ratios': [1, 1.28]})
    fig.patch.set_facecolor('white')
    # --- (a) surface density: U.S. vs Europe ---
    ax = axes[0]
    x = np.arange(3); w = 0.36
    b1 = ax.bar(x - w/2, us_d, w, color=EN_DEF, edgecolor='white', lw=0.5, label='U.S. (eCFR)', zorder=3)
    b2 = ax.bar(x + w/2, eu_d, w, color=EU, edgecolor='white', lw=0.5, label='Europe (EASA)', zorder=3)
    for xi, (u, e) in enumerate(zip(us_d, eu_d)):
        val_label(ax, xi - w/2, u + 0.55, f'{u:.2f}'.rstrip('0').rstrip('.'), EN_DEF, fs=7.6)
        val_label(ax, xi + w/2, e + 0.55, f'{e:.2f}'.rstrip('0').rstrip('.'), EN_REAL, fs=7.6)
    for xi, (u, e, pc) in enumerate(zip(us_d, eu_d, CANON['pct_eu_vs_us'])):
        ax.text(xi, max(u, e) + 1.9, pc, ha='center', fontsize=8.2, color='#555555')
    ax.text(1.0, 17.1, '(decline: aggregate density; Mann–Whitney U per sentence)',
            fontsize=6.4, color='#777777', ha='center', va='top', style='italic')
    ax.set_xticks(x); ax.set_xticklabels(regs, fontsize=8.4)
    ax.set_ylabel('Matched spans per 100 tokens', fontsize=8.6)
    ax.set_ylim(0, 17.8)
    # 图例置顶外（(a) 字母已内移到左上，避免相撞）
    ax.legend(frameon=False, fontsize=7.6, loc='lower center',
              bbox_to_anchor=(0.35, 1.02), ncol=1, handlelength=1.2, columnspacing=1.2)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='x', length=0)
    ax.axhline(0, color='#555555', lw=0.9)
    panel_letter(ax, 'a')
    # --- (b) model F₁: U.S. vs Europe vs China† ---
    ax = axes[1]
    x = np.arange(3); w = 0.26
    ax.bar(x - w, us_f, w, color=EN_DEF, edgecolor='white', lw=0.5, label='U.S. (eCFR)', zorder=3)
    ax.bar(x, eu_f, w, color=EU, edgecolor='white', lw=0.5, label='Europe (EASA)', zorder=3)
    cn = ax.bar(x + w, cn_f, w, color=ZH, edgecolor='white', lw=0.5, label='China (CCAR)†', zorder=3)
    for xi, (u, e, c) in enumerate(zip(us_f, eu_f, cn_f)):
        val_label(ax, xi - w, u + 0.02, f'{u:.3f}', EN_DEF, fs=7.6)
        val_label(ax, xi, e + 0.02, f'{e:.3f}', EN_REAL, fs=7.6)
        val_label(ax, xi + w, c + 0.02, f'{c:.3f}', ZH, fs=7.6)
        ax.text(xi + w, 1.045, '†', ha='center', fontsize=9, color=ZH)   # 中文行标记
    # 2026-09-14：该注原在 y=1.065，与 y=1.045 的三枚 † 标记重叠（旧瑕疵），上移至 † 之上
    ax.text(1.0, 1.13, 'Europe vs. U.S. model ΔF₁: −0.084 / +0.012 / −0.058', fontsize=6.4,
            color='#555555', ha='center', va='bottom')
    # 2026-09-04：加定义域训练 F₁ 参考虚线（表3 现值 0.781）→ 展示跨语域/跨体系损失的真实锚点
    ax.axhline(CANON['def_f1'], color=DASH, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax.text(2.35, CANON['def_f1'] + 0.015, 'definition-trained F₁ = 0.781',
            fontsize=7.0, color='#444444', ha='right', va='bottom')
    ax.set_xticks(x); ax.set_xticklabels(regs, fontsize=8.4)
    ax.set_ylabel('Entity-level F₁', fontsize=9)
    ax.set_ylim(0, 1.22)
    ax.legend(frameon=False, fontsize=7.4, loc='lower center', bbox_to_anchor=(0.5, 1.01),
              ncol=3, handlelength=1.2, columnspacing=1.1)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='x', length=0)
    ax.axhline(0, color='#555555', lw=0.9)
    panel_letter(ax, 'b')
    fig.tight_layout(w_pad=2.6)
    SAVE(fig, 'fig_esp_threesys.png')

# =========================================================
# Fig 8 (旧附录 A1 回正文)  12 类关系分布 —— 读 merged_relations.json
# =========================================================
def fig_relation_dist():
    rels = json.load(open(os.path.join(BASE, 'merged_relations.json'), encoding='utf-8'))
    c = collections.Counter(r['relation'] for r in rels)
    total = sum(c.values())
    assert total == CANON['kg']['relations'], f"relation 总数 {total} != 2475"
    order = sorted(c.items(), key=lambda kv: kv[1])
    labels = [k for k, _ in order]
    counts = [v for _, v in order]
    fig, ax = plt.subplots(figsize=(6.3, 3.5))
    fig.patch.set_facecolor('white')
    colors3 = [EN_DEF if k in ('is_a', 'part_of')
               else (EN_REAL if k == 'synonym_of' else EN_PALE) for k in labels]
    ax.barh(np.arange(len(labels)), counts, color=colors3, edgecolor='white', lw=0.5, height=0.64)
    ax.set_yticks(np.arange(len(labels))); ax.set_yticklabels(labels, fontsize=8.5)
    for yi, (k, v) in enumerate(order):
        ax.text(v + 12, yi, f'{v} ({v/total*100:.1f}%)', va='center', fontsize=8, color='#444444')
    ax.set_xlim(0, max(counts) * 1.26)
    ax.set_xlabel(f'Number of validated relations (n = {total:,})', fontsize=8.8)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.axvline(0, color='#555555', lw=0.9)
    fig.tight_layout()
    SAVE(fig, 'fig_esp_relation_dist.png')

# =========================================================
# Fig 9 (新增, 替换旧 fig13_kg_overall)  KG 复合图
#   (a) 全貌  (b) 骨干 (deg≥5)  (c) RADAR 近景  (d) 规模 352/388 → 2,184/2,475
#   复用 _figs_kg_acl.py 同参数（spring_layout seed42, k1.2），配色：枢纽红/中层蓝/外围灰
# =========================================================
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import matplotlib.patheffects as pe
import networkx as nx

KG_TIER = {
    2: PAL['HUB'],    # 枢纽 deg≥6 红
    1: PAL['IMP'],    # 重要 3–5 蓝
    0: PAL['PERI'],   # 外围 <3 灰（KG 内唯一灰色块）
}

def _kg():
    d = json.load(open(os.path.join(BASE, 'merged_relations.json'), encoding='utf-8'))
    G = nx.Graph()
    for r in d:
        G.add_edge(r['subject'], r['object'])
    deg = dict(G.degree())
    pos = nx.spring_layout(G, dim=3, seed=42, k=1.2, iterations=150)
    xs = [c[0] for c in pos.values()]; ys = [c[1] for c in pos.values()]; zs = [c[2] for c in pos.values()]
    scale = 20 / max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    pos = {n: (v[0] * scale, v[1] * scale, v[2] * scale) for n, v in pos.items()}
    nodes = list(G.nodes())
    X = np.array([pos[n][0] for n in nodes])
    Y = np.array([pos[n][1] for n in nodes])
    Z = np.array([pos[n][2] for n in nodes])
    D = np.array([deg[n] for n in nodes])
    tier = np.array([2 if dg >= CANON['kg']['hub_min_deg']
                     else (1 if dg >= CANON['kg']['imp_min_deg'] else 0) for dg in D])
    node_col = np.array([KG_TIER[t] for t in tier])
    node_size = np.array([((24 + 10 * min(dg, 12)) / 220.0 * 72.0 / 2.0) ** 2 * np.pi for dg in D]) * 0.82
    top5 = [n for n, _ in sorted(deg.items(), key=lambda kv: -kv[1])[:5]]
    lines = [[pos[u], pos[v]] for u, v in G.edges()]
    xs_p = np.percentile(X, [3, 97]); ys_p = np.percentile(Y, [3, 97]); zs_p = np.percentile(Z, [3, 97])
    cx, cy, cz = ((xs_p[0] + xs_p[1]) / 2, (ys_p[0] + ys_p[1]) / 2, (zs_p[0] + zs_p[1]) / 2)
    span = max(xs_p[1] - xs_p[0], ys_p[1] - ys_p[0], zs_p[1] - zs_p[0])
    return dict(G=G, deg=deg, pos=pos, nodes=nodes, X=X, Y=Y, Z=Z, D=D, tier=tier,
                node_col=node_col, node_size=node_size, top5=top5, lines=lines,
                cx=cx, cy=cy, cz=cz, span=span,
                xs=xs_p, ys=ys_p, zs=zs_p)

def _kg_panel(ax, K, elev, azim, subset=None, lim=None, labels=()):
    G, pos = K['G'], K['pos']
    nodes = K['nodes']
    if subset is None:
        mask = np.ones(len(nodes), bool)
        segs = K['lines']
    else:
        mask = np.array([n in subset for n in nodes])
        segs = [[pos[u], pos[v]] for u, v in G.edges() if u in subset and v in subset]
    lc = Line3DCollection(segs, colors='#A7B8C9', linewidths=0.5, alpha=0.42)
    ax.add_collection3d(lc)
    ax.scatter(K['X'][mask], K['Y'][mask], K['Z'][mask], s=K['node_size'][mask],
               c=K['node_col'][mask], alpha=1.0, edgecolors='#E8EDF2', linewidths=0.3,
               depthshade=False)
    for i, n in enumerate(nodes):
        if n in labels and mask[i]:
            ax.text(K['X'][i], K['Y'][i], K['Z'][i], n, fontsize=7, color='#2B3A48',
                    zorder=12, weight='bold', ha='center', va='bottom',
                    path_effects=[pe.withStroke(linewidth=2.4, foreground='white')])
    ax.view_init(elev=elev, azim=azim)
    ax.set_proj_type('persp')
    if lim is None:
        ax.set_xlim(K['xs'][0], K['xs'][1]); ax.set_ylim(K['ys'][0], K['ys'][1]); ax.set_zlim(K['zs'][0], K['zs'][1])
    else:
        ax.set_xlim(lim); ax.set_ylim(lim); ax.set_zlim(lim)
    ax.set_axis_off()
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.pane.set_facecolor('white'); a.pane.set_edgecolor('none'); a.pane.set_alpha(0)

def fig_kg_compound():
    K = _kg()
    fig = plt.figure(figsize=(11.8, 9.6))
    fig.patch.set_facecolor('white')
    # (a) 全貌
    ax = fig.add_subplot(2, 2, 1, projection='3d')
    _kg_panel(ax, K, 20, 55, labels=K['top5'])
    panel_letter(ax, 'a')
    # (b) 骨干 (deg≥5)
    core = {n for n in K['G'] if K['deg'][n] >= 5}
    ax = fig.add_subplot(2, 2, 2, projection='3d')
    _kg_panel(ax, K, 25, 70, subset=core)
    panel_letter(ax, 'b')
    # (c) RADAR 近景
    hub = K['top5'][0]                       # RADAR
    s6 = K['span'] * 0.28
    hx, hy, hz = K['pos'][hub]
    ax = fig.add_subplot(2, 2, 3, projection='3d')
    _kg_panel(ax, K, 22, 28, lim=(hx - s6, hx + s6), labels=(hub,))
    panel_letter(ax, 'c')
    # (d) 规模对比（旧附录 A2）
    ax = fig.add_subplot(2, 2, 4)
    groups = ['Base graph', 'Full dictionary pool']
    nodes = [CANON['kg']['base_nodes'], CANON['kg']['nodes']]
    edges = [CANON['kg']['base_edges'], CANON['kg']['relations']]
    y = np.arange(len(groups)); h = 0.32
    ax.barh(y - h / 2, nodes, h, label='Nodes', color=EN_DEF, edgecolor='white', lw=0.5)
    ax.barh(y + h / 2, edges, h, label='Relations', color=EN_REAL, edgecolor='white', lw=0.5)
    for b in ax.patches:
        wv = b.get_width()
        ax.text(wv + 60, b.get_y() + b.get_height() / 2, f'{int(wv):,}',
                va='center', fontsize=8.2, color='#444444')
    ax.set_yticks(y); ax.set_yticklabels(groups, fontsize=9)
    ax.set_xlim(0, 3200)
    ax.set_xlabel('Count', fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc='lower right')
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.axvline(0, color='#555555', lw=0.9)
    panel_letter(ax, 'd')
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.04, wspace=0.05, hspace=0.12)
    path = os.path.join(OUT, 'fig_esp_kg_compound.png')
    # 3D 坐标轴的 tight bbox 会异常膨胀 → 按 figsize 原尺寸输出
    fig.savefig(path, dpi=300, facecolor='white')
    plt.close(fig)
    print('✓', path)

# =========================================================
if __name__ == '__main__':
    fig_registergap()
    fig_baselines()
    fig_heatmap()
    fig_threesys()
    fig_relation_dist()
    fig_kg_compound()
    print('\n✅ v2 图件全部生成到 _fig_esp/')
