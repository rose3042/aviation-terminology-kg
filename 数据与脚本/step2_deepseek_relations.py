# -*- coding: utf-8 -*-
"""
第二步：对候选对做"受控关系分类"（DeepSeek API，花少量钱）
只对 step1 里"有依据的共现对"调用模型，并用固定关系 schema 约束输出，
从根上避免之前的两个问题：全是 related_to（不约束） / 对象不在图谱（自由抽取）。

特点：
  - 批量：每个请求处理 BATCH_SIZE 对，省 token
  - 断点续传：中途断了重跑不浪费钱
  - 重试：网络/限流失败自动重试
  - 成本控制：MAX_PAIRS 限制，先小规模试跑
输出：relations.json  [{subject, object, relation, confidence, evidence}]
"""
import json, os, sys, time
from openai import OpenAI

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# ============================ 配置区（运行前必看） ============================
KEY = os.environ.get("DEEPSEEK_API_KEY", "")   # DeepSeek API Key（从环境变量读取，勿硬编码）
MODEL = "deepseek-chat"
BATCH_SIZE = 20          # 每请求处理的对数。想更省→调大(如40)；对超长定义→调小(如10)
MAX_PAIRS = 0            # 0 = 全部跑（337对全量）
SLEEP = 0.8              # 每请求间隔(秒)，防限流
RETRIES = 3              # 单请求失败重试次数

PAIRS_FILE = sys.argv[1] if len(sys.argv) > 1 else "cooccurrence_pairs_v3.json"
PROGRESS_FILE = "progress_classify.json"
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else "relations.json"   # 输出文件名(参数2)

# 固定关系 schema v2（12类）：方向已定（"A 是什么"），模型只能从中选
RELATION_SCHEMA = [
    "synonym_of: A 与 B 同义或近义，如 velocity 与 airspeed",
    "is_a: A 是 B 的一种/子类，如 aileron is_a flight control",
    "part_of: A 是 B 的组成部分，如 wing part_of aircraft",
    "has_property: A 具有属性/特征 B，如 aluminum has_property lightweight",
    "located_in: A 位于 B 之中/之上，如 beacon located_in wingtip",
    "controls: A 控制/调节 B，如 throttle controls engine power",
    "operates_with: A 与 B 协同工作/配套使用，如 radio operates_with antenna",
    "causes: A 导致/引发 B，如 icing causes lift loss",
    "consists_of: A 由 B 组成/构成，如 aircraft consists_of fuselage",
    "used_for: A 用于 B，如 fuel used_for engine",
    "measures: A 度量/衡量 B，如 airspeed measures aircraft velocity",
    "defined_by: A 的定义由 B 界定，如 airworthiness defined_by regulations",
    "none: 无明确关系或不确定",
]

SYSTEM_PROMPT = (
    "你是航空领域术语关系分类器，只能输出合法 JSON，不输出任何其他文字。"
    "对每一对术语 (A, B)，依据 A 的定义和 B 的含义，从固定关系类型中选择最合适的一个。"
    "关系方向已定义，直接判断即可。"
)

def build_user_prompt(batch):
    schema_text = "\n".join(f"- {s}" for s in RELATION_SCHEMA)
    lines = []
    for p in batch:
        # 定义截断到 400 字符，控制 token
        d = p["subject_def"][:400]
        lines.append(
            f'{{"id":{p["_i"]},"A":"{p["subject"]}","A_def":"{d}","B":"{p["object"]}"}}'
        )
    return (
        f"关系类型（只允许以下，绝不发明新标签）：\n{schema_text}\n\n"
        f"下面是 {len(batch)} 对待分类术语对：\n{json.dumps(lines, ensure_ascii=False)}\n\n"
        "请对每个 id 输出 JSON 数组，格式："
        '[{"id":<id>,"relation":"<上面的一种>","confidence":<0到1>,"evidence":"A定义中支持该关系的原句(简短)"}]'
    )


def classify_batch(client, batch):
    """返回 {id: {"relation":..,"confidence":..,"evidence":..}}，失败返回 {}"""
    for attempt in range(RETRIES):
        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(batch)},
                ],
                temperature=0.0,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )
            content = r.choices[0].message.content
            # 兼容返回 {relations:[...]} 或 [...]
            data = json.loads(content)
            if isinstance(data, dict) and "relations" in data:
                data = data["relations"]
            if isinstance(data, list):
                return {d["id"]: d for d in data if isinstance(d, dict) and "id" in d}
        except Exception as e:
            print(f"    第{attempt+1}次尝试失败: {e}")
            time.sleep(2 * (attempt + 1))
    return {}


# ============================ 主流程 ============================
client = OpenAI(api_key=KEY, base_url="https://api.deepseek.com")

with open(PAIRS_FILE, 'r', encoding='utf-8') as f:
    pairs = json.load(f)
print(f"候选关系对: {len(pairs)} 对")

if MAX_PAIRS and MAX_PAIRS < len(pairs):
    pairs = pairs[:MAX_PAIRS]
    print(f"成本控制：本次只处理前 {MAX_PAIRS} 对")

# 给每对一个稳定 id（用于断点续传去重）
for i, p in enumerate(pairs):
    p["_i"] = i

# 恢复进度
results = {}          # id -> {"subject","object","relation",...}
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        results = {int(k): v for k, v in json.load(f).items()}
    print(f"恢复进度：已完成 {len(results)}/{len(pairs)}")

# 分批处理
batches = [pairs[i:i + BATCH_SIZE] for i in range(0, len(pairs), BATCH_SIZE)]
total = len(batches)
for bi, batch in enumerate(batches, 1):
    new_ids = [p["_i"] for p in batch if p["_i"] not in results]
    if not new_ids:
        print(f"[{bi}/{total}] 本批已完成，跳过")
        continue
    print(f"[{bi}/{total}] 处理 {len(new_ids)} 对...")
    got = classify_batch(client, [p for p in batch if p["_i"] in new_ids])
    for p in batch:
        if p["_i"] in got:
            g = got[p["_i"]]
            rel = str(g.get("relation", "none")).strip()
            if rel not in [s.split(":")[0] for s in RELATION_SCHEMA]:
                rel = "none"     # 模型发明新标签 → 归为 none
            results[p["_i"]] = {
                "subject": p["subject"],
                "object": p["object"],
                "relation": rel,
                "confidence": float(g.get("confidence", 0)),
                "evidence": str(g.get("evidence", ""))[:200],
            }
    # 每批落盘（断点续传）
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False)
    if bi % 5 == 0 or bi == total:
        done = sum(1 for v in results.values())
        print(f"  进度 {done}/{len(pairs)}，已花 {bi} 个请求")
    time.sleep(SLEEP)

# 最终保存：按原顺序输出
final = [results[i] for i in range(len(pairs)) if i in results]
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(final, f, indent=1, ensure_ascii=False)

# 统计
from collections import Counter
cnt = Counter(r["relation"] for r in final)
print("=" * 55)
print(f"完成！有效结果 {len(final)} 条，分布：")
for rel, c in cnt.most_common():
    print(f"  {rel:12s} {c:5d}")
print(f"关系文件已保存: {OUTPUT_FILE}")
print(f"下一步: python step3_import_neo4j.py")
