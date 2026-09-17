# -*- coding: utf-8 -*-
"""
第一步增强版（v2）：利用括号全称 + See/aka 交叉参照，大幅提升候选关系对数量
相比 v1 的三处升级：
  1. 括号全称注册：'ILS (instrument landing system)' → 注册 "instrument landing system" 别名，
     定义里出现别名也算共现
  2. 词形还原：wings/winged/winging → wing（简单后缀规则，不引入额外依赖）
  3. See/aka 交叉参照：'See runway end identifier lights' → 术语 ↔ 目标 直接出候选对
输出：
  cooccurrence_pairs_v2.json   ← 给 step2 用（含 subject_def）
  see_also_pairs.json          ← 天然的 see-also 关系（不花钱直接得）
  控制台统计
"""
import json, os, sys, re
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

with open('auto_labels_clean.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

terms = {}          # 规范名 -> 定义
for item in data:
    terms[item['term']] = item['definition']

# ------------------------------------------------------------------
# 1. 注册别名（括号全称）
# ------------------------------------------------------------------
alias_map = {}      # 别名(小写) -> 规范术语名
for term in terms:
    m = re.search(r'\((.*?)\)', term)
    if m:
        alias = m.group(1).strip()
        if 2 < len(alias) < 60 and ' ' not in alias.replace(' ', '')[:0]:  # 长度合理
            alias_map[alias.lower()] = term
            # 别名本身也作为可匹配对象（全称本身可能被定义提到）

# 可匹配的名字集合：规范名 + 括号别名
match_names = list(terms.keys()) + list(alias_map.keys())
# 长优先
match_names.sort(key=len, reverse=True)

# 去重：别名可能与规范名重复
seen = set()
uniq_names = []
for n in match_names:
    nl = n.lower()
    if nl in seen:
        continue
    seen.add(nl)
    uniq_names.append(n)

def make_pattern(name):
    return re.compile(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', re.IGNORECASE)

patterns = {n: make_pattern(n) for n in uniq_names}

# 简单词形还原：wings/winged→wing；仅用于名词后缀
SUFFIX = {
    's': '', 'es': '', 'ies': 'y', 'ed': '', 'ing': '',
    'ers': 'er', 'or': 'or', 'ation': 'ation',
}

def plural_variants(name):
    """返回该术语的常见变形，用于匹配定义中的复数/动名词形式"""
    variants = {name}
    if name.endswith('s') and len(name) > 3:
        variants.add(name[:-1])
    if name.endswith('es'):
        variants.add(name[:-2])
    if name.endswith('ing') and len(name) > 5:
        variants.add(name[:-3] + 'e')   # winging -> winge? 不完美，主要靠原词
    if name.endswith('ed') and len(name) > 4:
        variants.add(name[:-2])
    return variants

# 构建"变形 -> 规范名"映射（只对长度>=5的术语）
stem_map = {}
for name in terms:
    if len(name) < 5:
        continue
    for v in plural_variants(name):
        if len(v) >= 4:
            stem_map.setdefault(v.lower(), name)

# ------------------------------------------------------------------
# 2. 共现扫描（含变形匹配）
# ------------------------------------------------------------------
def scan_definition(defn):
    """返回定义中命中的规范术语名列表"""
    hits = []
    dl = defn.lower()
    for name in uniq_names:
        if patterns[name].search(defn):
            hits.append(name)
    # 变形匹配（只对未命中的，避免重复）
    for stem, canon in stem_map.items():
        if canon.lower() in [h.lower() for h in hits]:
            continue
        if re.search(r'(?<![\w-])' + re.escape(stem) + r'(?![\w-])', dl):
            hits.append(canon)
    return hits

pairs = []
occurrences = Counter()
for subj, definition in terms.items():
    hits = scan_definition(definition)
    for obj in hits:
        obj_canon = alias_map.get(obj.lower(), obj) if obj.lower() in alias_map else obj
        if obj_canon == subj:
            continue
        pairs.append((subj, obj_canon))
        occurrences[obj_canon] += 1

# ------------------------------------------------------------------
# 3. See / Also known as 交叉参照（天然关系，不花钱）
#    目标术语优先匹配"括号全称别名"（如 See air data computer → ADC (air data computer)）
# ------------------------------------------------------------------
see_also = []
# 别名 -> 规范名 的映射，含反向（全称 -> 缩写）
name_to_canon = {}
for term in terms:
    name_to_canon[term.lower()] = term
for alias, canon in alias_map.items():
    name_to_canon[alias.lower()] = canon

for subj, definition in terms.items():
    for m in re.finditer(r'\bSee\s+([A-Za-z][A-Za-z\s\-()]*?)[.,]?\s*$', definition):
        target = m.group(1).strip().rstrip('.,')
        if len(target) < 2 or len(target) > 60:
            continue
        key = target.lower()
        resolved = name_to_canon.get(key, None)
        # 尝试去掉尾词再匹配（如 "air data computer." -> "air data computer"）
        if resolved is None and key.endswith('.'):
            resolved = name_to_canon.get(key[:-1], None)
        see_also.append({
            'subject': subj,
            'object': resolved if resolved else target,   # 匹配到规范名就规范化，否则保留原文
            'kind': 'see_also',
            'resolved': bool(resolved),
        })

# ------------------------------------------------------------------
# 4. 输出
# ------------------------------------------------------------------
print("=" * 55)
print(f"术语总数            : {len(terms)}")
print(f"括号别名注册         : {len(alias_map)} 个")
print(f"共现候选关系对(v2)   : {len(pairs)}  (v1为376)")
if pairs:
    uniq_s = len(set(s for s, _ in pairs))
    print(f"有关系的术语数       : {uniq_s} ({uniq_s / len(terms) * 100:.1f}%)")
    print(f"整体密度             : {len(pairs) / len(terms):.2f}")
print(f"See/aka 交叉参照     : {len(see_also)} 条")

# 保存
out = [{"subject": s, "object": o, "subject_def": terms[s]} for s, o in pairs]
with open('cooccurrence_pairs_v2.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
with open('see_also_pairs.json', 'w', encoding='utf-8') as f:
    json.dump(see_also, f, indent=1, ensure_ascii=False)
print(f"已保存 cooccurrence_pairs_v2.json ({len(out)} 对)")
print(f"已保存 see_also_pairs.json ({len(see_also)} 条)")

# 示例
if pairs:
    print("\n示例候选对（前 15）:")
    for s, o in pairs[:15]:
        print(f"  {s}  →  {o}")
if see_also:
    print("\nSee 交叉参照示例（前 10）:")
    for r in see_also[:10]:
        print(f"  {r['subject']}  --see_also-->  {r['object']}")
