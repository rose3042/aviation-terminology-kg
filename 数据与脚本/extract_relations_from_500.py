import json
import time
import os
from openai import OpenAI

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "your_api_key_here")
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

RELATION_TYPES = [
    "synonym_of", "abbreviation_of", "opposite_of", "superseded_by",
    "is_a", "instance_of", "part_of", "consists_of", "contains",
    "measures", "controls", "used_for", "calculates", "provides",
    "affects", "causes", "defined_by", "governed_by"
]

# 中间状态文件
PROGRESS_FILE = "progress_500.json"
OUTPUT_FILE = "extracted_relations_500.json"

# 读取标注数据
with open('annotations_500.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

term_def = {}
for item in data:
    text = item['data']['text']
    if '.' not in text:
        continue
    term = text.split('.')[0].strip()
    definition = text.split('.', 1)[1].strip()
    term_def[term] = definition

print(f"共加载 {len(term_def)} 个术语")

# 加载已有进度（断点续传）
processed_terms = set()
all_relations = []
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        progress = json.load(f)
        processed_terms = set(progress.get("processed_terms", []))
        all_relations = progress.get("all_relations", [])
    print(f"恢复进度，已处理 {len(processed_terms)} 个术语，已有 {len(all_relations)} 条关系")
else:
    print("首次运行，从头开始")

def extract_relations_with_retry(term, definition, retries=3):
    prompt = f"""你是一个航空术语关系抽取专家。请从以下定义中提取与术语“{term}”相关的所有关系。

定义：{definition}

你只能从以下关系类型中选择：
{', '.join(RELATION_TYPES)}

注意：
- 只输出严格合法的 JSON，格式为：
  {{"relations": [{{"tail": "目标术语", "type": "关系类型"}}, ...]}}
- 如果没有发现任何关系，输出 {{"relations": []}}

请开始："""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个严格的关系抽取器，只输出纯 JSON。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return result.get("relations", [])
        except Exception as e:
            print(f"  尝试 {attempt+1}/{retries} 失败: {e}")
            time.sleep(2)
    return []

# 遍历所有术语
total = len(term_def)
for idx, (term, definition) in enumerate(term_def.items(), start=1):
    if term in processed_terms:
        print(f"跳过 {idx}/{total}: {term} (已处理)")
        continue
    print(f"处理 {idx}/{total}: {term}")
    relations = extract_relations_with_retry(term, definition)
    for rel in relations:
        all_relations.append({
            "subject": term,
            "relation": rel["type"],
            "object": rel["tail"]
        })
    processed_terms.add(term)
    # 每处理5条保存一次进度
    if idx % 5 == 0 or idx == total:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "processed_terms": list(processed_terms),
                "all_relations": all_relations
            }, f, indent=2)
        print(f"  进度已保存，当前共 {len(all_relations)} 条关系")
    time.sleep(0.5)

# 最终保存
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(all_relations, f, indent=2, ensure_ascii=False)

print(f"\n抽取完成！共得到 {len(all_relations)} 条三元组。")
print(f"已保存至 {OUTPUT_FILE}")

# 清理进度文件（可选）
os.remove(PROGRESS_FILE)