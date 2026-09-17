import json
from neo4j import GraphDatabase
import requests

# 配置
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"  # 请替换为你自己的API Key

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# 1. 获取度最小的20个术语
def get_sparse_terms(limit=20):
    with driver.session() as session:
        result = session.run("""
            MATCH (n:Term)
            WITH n, size((n)-[]-()) AS degree
            RETURN n.name AS term
            ORDER BY degree ASC
            LIMIT $limit
        """, limit=limit)
        return [record["term"] for record in result]

sparse_terms = get_sparse_terms()
print(f"找到 {len(sparse_terms)} 个稀疏术语: {sparse_terms}")

# 2. 为每个稀疏术语调用 DeepSeek 抽取关系
def extract_relations(term):
    # 你需要从数据库或文件中获取该术语的定义，这里假设已有定义字典
    # 如果没有定义，可以跳过
    definition = ""  # 你需要补全获取定义的逻辑
    if not definition:
        return []
    prompt = f"""...（同之前的关系抽取 prompt）..."""
    # 调用 DeepSeek API...
    # 返回关系列表
    return []

# 3. 导入新关系
# ... 同之前的导入逻辑