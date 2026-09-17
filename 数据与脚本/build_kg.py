import json
from py2neo import Graph, Node, Relationship

# --- 1. 连接Neo4j数据库 (请修改为你的密码) ---
# 默认用户名通常是 'neo4j'[reference:4]
graph = Graph("bolt://localhost:7687", auth=("neo4j", "你的密码"))

# --- 2. 清空旧数据，准备开始 ---
graph.run("MATCH (n) DETACH DELETE n")
print("旧数据已清除。")

# --- 3. 从你的标注文件中创建节点 ---
nodes_dict = {}
count = 0

# 读取你的标注文件，创建每个术语节点
with open('annotations_500.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    text = item['data']['text']
    term = text.split('.')[0].strip()  # 提取术语名称
    if term not in nodes_dict:
        term_node = Node("Term", name=term)
        graph.create(term_node)
        nodes_dict[term] = term_node
        count += 1
    if count % 100 == 0:
        print(f"已创建 {count} 个节点...")

print(f"共创建 {count} 个术语节点。")

# --- 4. 创建 HAS_DEFINITION 关系 ---
print("开始创建 HAS_DEFINITION 关系...")
rel_count = 0
for item in data:
    text = item['data']['text']
    term = text.split('.')[0].strip()
    # 提取定义部分：第一个句点之后的内容
    definition = text.split('.', 1)[1].strip()
    if term in nodes_dict:
        # 创建 Definition 节点
        def_node = Node("Definition", text=definition)
        graph.create(def_node)
        # 创建关系
        rel = Relationship(nodes_dict[term], "HAS_DEFINITION", def_node)
        graph.create(rel)
        rel_count += 1

print(f"已创建 {rel_count} 条 HAS_DEFINITION 关系。")
print("知识图谱构建完成！")