# -*- coding: utf-8 -*-
"""对比三个词典候选在 real_corpus en 上的 gold 规模，判断 0.465 时代词典可能是哪版。"""
import json, re, os, sys
sys.stdout.reconfigure(encoding='utf-8')
base = os.path.dirname(os.path.abspath(__file__)); os.chdir(base)
HEAD = re.compile(r'^([A-Za-z][A-Za-z0-9\- ]*?(?:\([^)]+\))?)\.\s+(.+)$')
corpus = json.load(open('real_corpus.json', encoding='utf-8'))
en = [c for c in corpus if c['lang'] == 'en']

def pool_of(text):
    heads = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln: continue
        m = HEAD.match(ln)
        if m and 2 <= len(m.group(1)) <= 60 and len(m.group(2)) >= 8:
            heads.append(m.group(1).strip())
    pool = set()
    for t in heads:
        if 4 <= len(t) <= 40:
            pool.add(t)
            m = re.search(r'\(([^)]+)\)', t)
            if m and len(m.group(1)) >= 5 and ' ' in m.group(1):
                pool.add(m.group(1).strip())
    return pool, heads

def spans_count(text, pool):
    pats = {n: re.compile(r'(?<![\w-])' + re.escape(n) + r'(?![\w-])', re.IGNORECASE) for n in pool}
    tot = 0
    hit_words = {}
    for c in en:
        txt = c['text']
        kept = []
        for n in pats:
            for m in pats[n].finditer(txt):
                s, e = m.start(), m.end()
                if any(not (e <= ks or s >= ke) for ks, ke, _ in kept):
                    continue
                kept.append((s, e, n))
        tot += len(kept)
        for s, e, n in kept:
            hit_words[n] = hit_words.get(n, 0) + 1
    return tot, hit_words

D = r'D:\360MoveData\Users\叶丽娜\Desktop'
for f in ['dictionary_clean.txt', 'dictionary_clean_fixed.txt', 'dictionary_full.txt']:
    txt = open(os.path.join(D, f), encoding='utf-8').read()
    pool, heads = pool_of(txt)
    print(f'\n=== {f} ===')
    print(f'头词 {len(heads)} | pool {len(pool)}')
    tot, hits = spans_count(en, pool)
    print(f'real_corpus en gold spans(全词典匹配去重叠): {tot}  (1491句)')

# 当前词典 top 命中词（普通词伪头词嫌疑）
pool_cur, _ = pool_of(open(os.path.join(D, 'dictionary_clean.txt'), encoding='utf-8').read())
_, cur_hits = spans_count(en, pool_cur)
print('\n=== 当前 dictionary_clean.txt 命中 top 25（含 STOP 普通词的暴露程度）===')
for w, c in sorted(cur_hits.items(), key=lambda x: -x[1])[:25]:
    print(f'{w:35s} {c}')
