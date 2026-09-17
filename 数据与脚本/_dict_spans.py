# -*- coding: utf-8 -*-
"""给标注池的每一句预先算出**词典口径**的术语字符区间，供标注页的「参考」面板当提示。

⚠ 这不是我（模型）对术语的判断，是 `adapt_gold`（= 池 B，`_easa_model_eval.py` 同源）
   的机械匹配结果 —— 也就是**论文里评估集 1,491 句金标准、以及 0.525 那组数字所用的同一口径**。
   面板上必须写明：词典口径 ≠ 人工口径，人工金标准的 entity micro-F1 只有 0.279。
   所以它只能当线索，不能直接采纳。

## 2026-09-14 修正（一处口径、一处匹配器）

1. **口径来源改为单一来源。** 本脚本原先把池从 `_build_real_corpus.py` 里抠出来自己重建，
   而那是 12,902 项的**近亲副本**；论文现值出自 `_easa_model_eval.py` 的池（**12,908 项**，
   见 `adapt_gold.POOL_DIGEST_V1`）。两个池差 6 项 —— 面板与金标准本就不该是两份各自维护的池。
   现在直接 `import adapt_gold`，口径只有一处。

2. **匹配器换了。** 原先用一条按长度降序的大 alternation 正则，它是 leftmost-first，
   只在**每个位置**取最长；而金标准的 `find_spans` 是全局长度降序 + 拒绝重叠。
   两者在 60 句里就能差出 1 句。既然面板的全部意义就是"预览金标准会标什么"，
   现在直接调 `adapt_gold.find_spans` —— 不再各写一份正则等它漂移。

代价：`find_spans` 是逐词循环（~1.3 万条 × 每句），比 alternation 慢约 3 个数量级。
500 句量级可接受，但要有耐心；进度会打印。

用法:
    python _dict_spans.py                       # 写 adapt/pool_dict_spans.json
    python _dict_spans.py --check               # 只核口径，不写文件
"""

import argparse, json, os, sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

import adapt_gold

P_POOL = 'adapt/pool_to_annotate.json'
OUT = 'adapt/pool_dict_spans.json'


def spans_of(text):
    """区间用金标准的 find_spans —— 面板与金标准必须逐字同口径。"""
    return [[s, e] for s, e, _ in adapt_gold.find_spans(text)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    sync = adapt_gold.verify_sync()
    print(sync)
    if sync.startswith('⚠'):
        raise SystemExit('✗ 词典口径与论文现值不符 —— 面板一旦给出提示就是错的，拒绝继续。')
    print('  池 B 共 %d 项（= 论文 0.525 的口径）' % len(adapt_gold.POOL))

    if args.check:
        return

    if not os.path.exists(P_POOL):
        raise SystemExit('✗ 找不到标注池：%s' % P_POOL)
    items = json.load(open(P_POOL, encoding='utf-8'))

    out, n_terms, n_sent_with = {}, 0, 0
    overlap = []
    for i, it in enumerate(items, 1):
        if i % 50 == 0 or i == len(items):
            print('   … %d/%d' % (i, len(items)), flush=True)
        sp = spans_of(it['text'])
        if sp:
            n_sent_with += 1
        n_terms += len(sp)
        out[str(it['id'])] = sp
        # 自检：金标准的不重叠保证。find_spans 显式拒绝重叠，这里验它真的守住了 ——
        # 面板画出两个叠在一起的区间就是坏数据，不能等标注员发现。
        for a, b in zip(sp, sp[1:]):
            if b[0] < a[1]:
                overlap.append((it['id'], a, b))
                break
    if overlap:
        raise SystemExit('✗ 面板区间出现重叠（金标准本不该有），例：%s' % overlap[:3])

    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print('✓ 已写 %s' % OUT)
    print('   覆盖 %d / %d 句（%d 句词典没命中任何术语）｜ 命中总数 %d 个'
          % (n_sent_with, len(items), len(items) - n_sent_with, n_terms))
    print('   ⚠ 面板上必须标注：词典口径 ≠ 人工口径（人工金 standard micro-F1 = 0.279）')


if __name__ == '__main__':
    main()
