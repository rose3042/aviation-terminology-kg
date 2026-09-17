# -*- coding: utf-8 -*-
"""一次性核查：词典层（EN_POOL）里到底有多少非术语条目、漏掉了多少基本术语。

动机：20 句校准批上，人工标了 51 个 span、词典标了 115 个，只有 12 个重合。
要先判断这是"人工标歪了"还是"词典本身脏"，才能决定标注规则该往哪边对齐。
用完即弃，不进管线。
"""
import re, sys, collections
sys.argv = ['x']
sys.stdout.reconfigure(encoding='utf-8')
import _dict_spans as DS

P = r'D:\360MoveData\Users\叶丽娜\Desktop\dictionary_clean.txt'
lines = open(P, encoding='utf-8', errors='replace').read().splitlines()
print('词典文件总行数: %d' % len(lines))


def starts_with(w):
    return [(i, l[:110]) for i, l in enumerate(lines)
            if re.match(r'(?i)^' + re.escape(w) + r'\.\s', l)]


print('\n=== 1. 关键术语在词典文件里是否有独立条目（行首 "term. "）===')
for w in ['crewmember', 'fuel tank', 'program manager', 'rest period', 'airport',
          'flight', 'maintenance', 'made', 'available', 'pass', 'test', 'other',
          'person', 'work', 'changes', 'specified', 'applicable']:
    h = starts_with(w)
    tail = ('  首例→ ' + h[0][1]) if h else ''
    print('  %-16s 独立条目 %d 条%s' % (w, len(h), tail))

pool = DS.real_pool_from_build_script()
print('\nEN_POOL 规模: %d' % len(pool))

print('\n=== 2. EN_POOL 里的单词条目（单词条目不一定是脏的，但通用词一定是）===')
one = sorted([e for e in pool if len(e.split()) == 1])
print('  共 %d 条（占 %.1f%%）' % (len(one), 100.0 * len(one) / len(pool)))
print('  最短 50 条: ' + ' | '.join(sorted(one, key=len)[:50]))

print('\n=== 3. 明显是"定义续行"被误当术语的条目 ===')
BAD_PREFIX = ('a ', 'an ', 'the ', 'of ', 'to ', 'in ', 'on ', 'it ', 'may ', 'must ',
              'when ', 'if ', 'this ', 'that ', 'these ', 'those ', 'is ', 'are ',
              'can ', 'should ', 'will ', 'with ', 'for ', 'by ', 'as ', 'at ')
junk = sorted([e for e in pool if e.startswith(BAD_PREFIX) and len(e.split()) >= 2])
print('  以冠词/介词/助动词开头的多词条目: %d 条（占 %.1f%%）'
      % (len(junk), 100.0 * len(junk) / len(pool)))
for e in junk[:30]:
    print('     ', e)

print('\n=== 4. 反向：人工在这 20 句里标了、但词典没有的术语 ===')
import json
live = json.load(open('adapt/annotated_live.json', encoding='utf-8'))['sentences']
calib = json.load(open('adapt/calib20.json', encoding='utf-8'))
surf = collections.Counter()
for r in calib:
    t = r['text']
    for a, b in live[r['id']]['spans']:
        surf[t[a:b].strip().lower()] += 1
for s, c in surf.most_common():
    print('  %-42s ×%-2d  %s' % (s, c, '词典有' if s in pool else '★词典没有'))
