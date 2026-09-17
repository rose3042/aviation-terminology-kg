# -*- coding: utf-8 -*-
"""
第一步B：用 Dale Crane 权威词典做术语白名单降噪
原理：auto_labels 数据的原始来源就是 Dale Crane 词典，任何"术语"只要不在这个权威词典里
就高度可疑（普通英文词/噪音）。用词典全量解析出术语表，作为白名单，过滤掉白名单外的候选对。

输入：
  - Dale Crane 词典文本（dictionary_clean.txt / dictionary_full.txt，位于桌面）
  - auto_labels_clean.json（2739条）
  - cooccurrence_pairs_v2.json（782对）
输出：
  - filtered_pairs.json（过滤白名单外的候选对）
  - 控制台：白名单大小、被过滤数、噪音示例
"""
import json, os, sys, re

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
DESKTOP = r'D:\360MoveData\Users\叶丽娜\Desktop'

# ------------------------------------------------------------------
# 1. 从 Dale Crane 词典解析出权威术语表（白名单）
# ------------------------------------------------------------------
def parse_dictionary(path):
    """解析词典文本 → (term, definition) 列表。每行 '术语. 定义'，定义可能跨行。"""
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    entries = []
    # 按句点切分：每个"术语. "开头的新条目
    # 简单策略：按行，行首如果是"X. "且X是短词/缩写，视为新条目
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # 匹配 "TERM. definition..." 或 "TERM (full name). definition"
        m = re.match(r'^([A-Za-z][A-Za-z0-9\- ]*?(?:\([^)]+\))?)\.\s+(.+)$', line)
        if m:
            term, definition = m.group(1).strip(), m.group(2).strip()
            # 术语长度合理（排除太长/太短的噪音）
            if 2 <= len(term) <= 60 and len(definition) >= 8:
                entries.append((term, definition))
    # 去重
    seen = set()
    uniq = []
    for t, d in entries:
        tl = t.lower()
        if tl in seen:
            continue
        seen.add(tl)
        uniq.append((t, d))
    return uniq

# 尝试多个词典文件，取覆盖最大的
dict_path = None
for fn in ['dictionary_clean.txt', 'dictionary_clean_fixed.txt', 'dictionary_full.txt']:
    p = os.path.join(DESKTOP, fn)
    if os.path.exists(p):
        entries = parse_dictionary(p)
        print(f"词典 {fn}: 解析出 {len(entries)} 条")
        if len(entries) > 3000:
            dict_path = p
            break
if dict_path is None:
    # 用解析结果最多的
    best = 0
    for fn in ['dictionary_clean.txt', 'dictionary_clean_fixed.txt', 'dictionary_full.txt']:
        p = os.path.join(DESKTOP, fn)
        if os.path.exists(p):
            e = parse_dictionary(p)
            if len(e) > best:
                best, entries, dict_path = len(e), e, p
    print(f"选用词典 {dict_path}: {len(entries)} 条")

# 构建白名单（含括号全称别名 + 归一化变体）
whitelist = set()
for term, _ in entries:
    tl = term.lower()
    whitelist.add(tl)
    # 归一化变体：去括号、去标点、折叠空格
    nt = re.sub(r'\s*\([^)]*\)', ' ', term).strip().lower()
    nt = re.sub(r'[^a-z0-9 ]', ' ', nt)
    nt = re.sub(r'\s+', ' ', nt).strip()
    if nt:
        whitelist.add(nt)
    # 括号全称也加入白名单
    m = re.search(r'\(([^)]+)\)', term)
    if m and len(m.group(1)) > 3:
        whitelist.add(m.group(1).lower())
        whitelist.add(re.sub(r'[^a-z0-9 ]', ' ', m.group(1)).strip())
# 额外：把 auto_labels_clean 里的术语也加入（它本身就是从词典来的，只是格式不同）
with open('auto_labels_clean.json', 'r', encoding='utf-8') as f:
    clean = json.load(f)
for item in clean:
    tl = item['term'].lower()
    whitelist.add(tl)
    nt = re.sub(r'\s*\([^)]*\)', ' ', item['term']).strip().lower()
    nt = re.sub(r'[^a-z0-9 ]', ' ', nt)
    nt = re.sub(r'\s+', ' ', nt).strip()
    if nt:
        whitelist.add(nt)
print(f"白名单规模: {len(whitelist)}")

# ------------------------------------------------------------------
# 2. 过滤候选对
# ------------------------------------------------------------------
with open('cooccurrence_pairs_v2.json', 'r', encoding='utf-8') as f:
    pairs = json.load(f)
print(f"候选对: {len(pairs)}")

def norm_key(term):
    """归一化术语名用于白名单匹配：去括号、去标点、折叠空格"""
    t = re.sub(r'\s*\([^)]*\)', ' ', term).strip().lower()
    t = re.sub(r'[^a-z0-9 ]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

# 双白名单：精确匹配 + 包含匹配（核心词）
def in_whitelist(key, whitelist):
    """key 规范化后，要么精确在白名单，要么白名单里有含它的（核心词命中）"""
    if not key:
        return False
    if key in whitelist:
        return True
    # 包含匹配：白名单里有 这个 key 包含的连续子串（如 "advisory circular" in "AC advisory circular"? 反了）
    # 改为：key 的每个词都在白名单的某个条目里出现过？太松。
    # 用"key 整体是某个白名单条目的后缀"（如 'system' 在 'fuel system' 里）
    words = key.split()
    if len(words) >= 2:
        # 检查去掉一个词后是否命中（处理 'administrator faa' -> 'administrator'）
        for i in range(len(words)):
            sub = ' '.join(words[:i] + words[i+1:])
            if sub in whitelist:
                return True
    return False

keep = []
dropped = []
for p in pairs:
    subj, obj = p['subject'], p['object']
    sk, ok = norm_key(subj), norm_key(obj)
    if in_whitelist(sk, whitelist) and in_whitelist(ok, whitelist):
        keep.append(p)
    else:
        dropped.append(p)

print(f"保留: {len(keep)}  过滤: {len(dropped)}")
if dropped:
    print("\n被过滤示例（前 15）:")
    for p in dropped[:15]:
        print(f"  {p['subject']} → {p['object']}")

with open('filtered_pairs.json', 'w', encoding='utf-8') as f:
    json.dump(keep, f, indent=1, ensure_ascii=False)
print(f"\n已保存 filtered_pairs.json ({len(keep)} 对)")
