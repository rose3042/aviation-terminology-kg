# -*- coding: utf-8 -*-
"""解析 _dict_tsv/*.tsv → 左右分栏文本 + 词条候选。
   布局：每页左右两栏，左=英文（词头+定义），右=中文译文。
   输出：
     _dict_cols/pXXX.en.txt / pXXX.zh.txt   分栏按行文本
     _dict_zh_index.json                      中文译文串（去空格，供检索）
"""
import glob, json, os, sys
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
from collections import defaultdict

OUT = '_dict_cols'
os.makedirs(OUT, exist_ok=True)

def split_page(tsv_path):
    """返回 ([(y, en_words)], [(y, zh_words)], page_width)"""
    en_lines, zh_lines = [], []
    W = 0
    lines = defaultdict(list)          # (block,par,line) -> [(x,y,w,h,text)]
    try:
        raw = open(tsv_path, encoding='utf-8').read()
    except FileNotFoundError:
        return None
    for ln in raw.splitlines()[1:]:
        c = ln.split('\t')
        if len(c) < 12:
            continue
        try:
            lv, bl, pa, li = int(c[0]), int(c[2]), int(c[3]), int(c[4])
            x, y, w, h = int(c[6]), int(c[7]), int(c[8]), int(c[9])
            txt = c[11]
        except Exception:
            continue
        W = max(W, x + w)
        if txt.strip():
            lines[(bl, pa, li)].append((x, y, w, h, txt))
    for key in sorted(lines):
        ws = sorted(lines[key], key=lambda r: r[0])
        ys = [r[1] for r in ws]
        y = min(ys)
        if not ws:
            continue
        en = ' '.join(r[4] for r in ws if r[0] < W / 2)
        zh = ''.join(r[4] for r in ws if r[0] >= W / 2)   # 中文无空格
        if en.strip():
            en_lines.append((y, en))
        if zh.strip():
            zh_lines.append((y, zh))
    return en_lines, zh_lines, W

# 主循环：解析已生成的 tsv
tsvs = sorted(glob.glob('_dict_tsv/p*.tsv'))
zh_index = []
done = 0
for tp in tsvs:
    out_en = os.path.join(OUT, os.path.basename(tp).replace('.tsv', '.en.txt'))
    out_zh = os.path.join(OUT, os.path.basename(tp).replace('.tsv', '.zh.txt'))
    if os.path.exists(out_en) and os.path.exists(out_zh):
        # 已解析，仅收集索引
        zh_index.append(open(out_zh, encoding='utf-8').read())
        done += 1
        continue
    res = split_page(tp)
    if res is None:
        continue
    en_lines, zh_lines, W = res
    with open(out_en, 'w', encoding='utf-8') as f:
        f.write('\n'.join(f'{y}\t{t}' for y, t in en_lines))
    with open(out_zh, 'w', encoding='utf-8') as f:
        f.write('\n'.join(f'{y}\t{t}' for y, t in zh_lines))
    zh_index.append('\n'.join(t for y, t in zh_lines))
    done += 1
    if done % 50 == 0:
        print(f'解析进度: {done}/{len(tsvs)}', flush=True)

# 构建去空格索引（中文译文连续串）
zh_flat = ''.join(zh_index).replace('\n', '')
json.dump({'zh_flat': zh_flat, 'pages': len(tsvs)}, open('_dict_zh_index.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(f'完成: 解析 {done} 页, 中文索引 {len(zh_flat)} 字符')
