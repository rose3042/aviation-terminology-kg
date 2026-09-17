# -*- coding: utf-8 -*-
"""
第三步（v2）：用 DeepSeek 对整本词典的【完整定义】做术语自动标注（LLM 弱监督）
目的：解决 500 条人工标注每条只有 1 个 TERM 的稀疏问题。
关键修正（v1→v2）：
  - v1 误用了 auto_labels_clean.json 里被截断的短定义（平均35字符）
  - v2 改用 full_definitions.json（完整定义，平均105字符，与人工标注同源）
  - 每条 text = "术语. 完整定义"（与 annotations_500 同格式），主题术语本身也标注
输出：annotations_llm_full.json
      [{ "data": {"text": 完整句},
         "annotations": [{"result": [{"value": {"start":..,"end":..,"text":..,"labels":["TERM"]}}]}] }]

用法：
  python step3_llm_annotate_terms.py test    # 只标注前 5 条并打印，验证质量（不写最终文件）
  python step3_llm_annotate_terms.py all     # 全量 16279 条（断点续传，可中断重跑）
"""
import json, os, sys, time, re
from openai import OpenAI

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# ============================ 配置区 ============================
KEY = os.environ.get("DEEPSEEK_API_KEY", "")   # DeepSeek API Key（从环境变量读取，勿硬编码）
MODEL = "deepseek-chat"
BATCH_SIZE = 8             # 完整定义较长，8 条/批较稳
SLEEP = 0.8
RETRIES = 3

DATA_FILE = 'full_definitions.json'          # 16279 条 {term, definition} 完整定义
PROGRESS_FILE = 'progress_llm_annotate_full.json'
OUTPUT_FILE = 'annotations_llm_full.json'

SYSTEM_PROMPT = (
    "你是航空术语识别专家。对每条约\"术语+定义\"的文本，找出文本中出现的所有航空专业术语。\n"
    "要求：\n"
    "1. 只输出【文本里真实出现】的术语，必须是原文的子串，绝不可编造原文没有的词；\n"
    "2. 包含：缩写（VOR、ILS、RADAR）、复合术语（instrument landing system）、"
    "设备/部件/系统/单位/标准名称；\n"
    "3. 排除：普通英语单词、动词、介词、形容词；\n"
    "4. 主题术语（条目开头那个术语，可能带括号变体）一定标注；\n"
    "5. 文本里除了主题术语没有其他术语时输出空数组 []。\n"
    "输出 JSON，格式：[{\"id\":<id>,\"terms\":[\"原文子串1\",\"原文子串2\",...]}]"
)

def build_prompt(batch):
    lines = [{"id": i, "text": f"{item['term']}. {item['definition']}"} for i, item in batch]
    return ("下面是若干条航空术语及定义，请对每条提取文本中出现的所有航空专业术语：\n"
            + json.dumps(lines, ensure_ascii=False))

def annotate_batch(client, batch):
    """返回 {id: [术语列表]}，失败返回 {}"""
    for attempt in range(RETRIES):
        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_prompt(batch)},
                ],
                temperature=0.0,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )
            content = r.choices[0].message.content
            data = json.loads(content)
            if isinstance(data, dict):
                data = data.get("terms", data.get("results", []))
            if isinstance(data, list):
                out = {}
                for d in data:
                    if isinstance(d, dict) and "id" in d:
                        out[d["id"]] = d.get("terms", [])
                return out
        except Exception as e:
            print(f"    第{attempt+1}次尝试失败: {e}")
            time.sleep(2 * (attempt + 1))
    return {}

def locate_terms(text, terms):
    """把 LLM 给出的术语文本定位为字符偏移（大小写不敏感，第一个出现，去重叠）"""
    spans = []
    used = set()
    # 按长度从长到短匹配，避免 ILS 抢占 instrument landing system 的短前缀
    for t in sorted(terms, key=len, reverse=True):
        t = str(t).strip()
        if len(t) < 2:
            continue
        low = text.lower()
        tl = t.lower()
        idx = low.find(tl)
        if idx < 0:
            # 尝试去除尾部句点等标点再匹配
            t2 = re.sub(r'[.,;]$', '', t)
            if len(t2) >= 2:
                idx = text.lower().find(t2.lower())
                t = t2
            if idx < 0:
                continue
        # 跳过与已标区间重叠的位置
        if any(idx < e and idx + len(t) > s for s, e in used):
            continue
        used.add((idx, idx + len(t)))
        spans.append({"start": idx, "end": idx + len(t),
                      "text": text[idx:idx + len(t)], "labels": ["TERM"]})
    spans.sort(key=lambda s: s["start"])
    return spans

def full_text(item):
    """每条完整文本 = '术语. 定义'（与人工标注同格式）"""
    return f"{item['term']}. {item['definition']}"

def ensure_head_term(text, spans, term):
    """本地兜底：确保主题术语（带括号变体）一定在标注里，LLM 漏了则补上"""
    candidates = [term]
    # 去掉括号变体再试
    cand2 = re.sub(r'\s*\(.*?\)\s*$', '', term)
    if cand2 != term:
        candidates.append(cand2)
    for cand in candidates:
        idx = text.lower().find(cand.lower())
        if idx >= 0:
            if not any(idx < s["end"] and idx + len(cand) > s["start"] for s in spans):
                spans.append({"start": idx, "end": idx + len(cand),
                              "text": text[idx:idx + len(cand)], "labels": ["TERM"]})
                spans.sort(key=lambda s: s["start"])
                return True
    return False

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    data = json.load(open(DATA_FILE, encoding='utf-8'))
    print(f"完整定义: {len(data)} 条")

    client = OpenAI(api_key=KEY, base_url="https://api.deepseek.com")

    if mode == "test":
        # 只跑前 5 条验证质量，不写最终文件
        for item in data[:5]:
            got = annotate_batch(client, [(0, item)])
            terms = got.get(0, [])
            text = full_text(item)
            spans = locate_terms(text, terms)
            ensure_head_term(text, spans, item['term'])
            print("\n" + "=" * 60)
            print(f"文本: {text[:200]}")
            print(f"LLM识别: {terms}")
            print(f"定位后: {[s['text'] for s in spans]}")
        print("\n验证完成。质量OK的话运行: python step3_llm_annotate_terms.py all")
        return

    # ===== 全量模式 =====
    results = {}   # _i -> {"data":.., "annotations":..}
    if os.path.exists(PROGRESS_FILE):
        results = {int(k): v for k, v in json.load(open(PROGRESS_FILE, encoding='utf-8')).items()}
        print(f"恢复进度: {len(results)}/{len(data)}")

    batches = [list(enumerate(data))[i:i + BATCH_SIZE] for i in range(0, len(data), BATCH_SIZE)]
    total = len(batches)
    for bi, batch in enumerate(batches, 1):
        todo = [(i, item) for i, item in batch if i not in results]
        if not todo:
            continue
        got = annotate_batch(client, todo)
        for i, item in todo:
            text = full_text(item)
            terms = got.get(i, [])
            spans = locate_terms(text, terms) if terms else []
            ensure_head_term(text, spans, item['term'])   # 兜底主题术语
            results[i] = {
                "data": {"text": text},
                "annotations": [{"result": spans}],
                "term": item['term'],
            }
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False)
        if bi % 10 == 0 or bi == total:
            n_terms = sum(len(a["annotations"][0]["result"]) for a in results.values())
            print(f"[{bi}/{total}] 进度 {len(results)}/{len(data)}，已标术语 {n_terms} 个")
        time.sleep(SLEEP)

    # 输出（去掉临时 term 字段，与 annotations_500 完全同构）
    final = []
    for i in range(len(data)):
        if i in results:
            d = results[i]
            final.append({"data": d["data"], "annotations": d["annotations"]})
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=1)
    n_terms = sum(len(a["annotations"][0]["result"]) for a in final)
    print(f"✅ 全量完成: {len(final)} 条, 共标注 {n_terms} 个术语 → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
