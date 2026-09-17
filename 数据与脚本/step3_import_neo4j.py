# -*- coding: utf-8 -*-
"""
第三步：把 step2 的关系导入 Neo4j（去重，只建图谱内存在的节点）
  - 过滤 none 和低置信度关系
  - 只导入 subject/object 都在已有 Term 图谱中的关系（避免创建无关节点）
  - MERGE 保证不重复创建
运行前提：Neo4j Desktop 里已启动你的数据库（bolt://localhost:7687）
"""
import json, os, sys
from neo4j import GraphDatabase

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"        # 如密码不同请改

MIN_CONFIDENCE = 0.5         # 低于此置信度的丢弃
FILTER_NONE = True           # 丢弃 none 关系

with open("relations.json", 'r', encoding='utf-8') as f:
    relations = json.load(f)
print(f"step2 结果 {len(relations)} 条")

# 1. 过滤
keep = []
for r in relations:
    if r["relation"] == "none" and FILTER_NONE:
        continue
    if r["confidence"] < MIN_CONFIDENCE:
        continue
    keep.append(r)
print(f"过滤后 {len(keep)} 条")

# 2. 去重（同一 subject-relation-object 只留一条）
seen = set()
uniq = []
for r in keep:
    key = (r["subject"], r["relation"], r["object"])
    if key in seen:
        continue
    seen.add(key)
    uniq.append(r)
print(f"去重后 {len(uniq)} 条")

if not uniq:
    print("没有可导入的关系，结束。")
    sys.exit(0)

# 3. 连接并导入
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
created = skipped = 0

def import_rel(tx, subj, rel, obj):
    # 只匹配图谱中已存在的节点（你之前导入的 3210 个 Term）
    q = (
        "MATCH (a:Term {name: $subj}), (b:Term {name: $obj}) "
        "MERGE (a)-[:`" + rel + "`]->(b) "
        "RETURN count(a) AS n"
    )
    res = tx.run(q, subj=subj, obj=obj)
    return res.single()["n"] > 0

with driver.session() as session:
    for i, r in enumerate(uniq, 1):
        try:
            ok = session.execute_write(import_rel, r["subject"], r["relation"], r["object"])
            if ok:
                created += 1
            else:
                skipped += 1
        except Exception as e:
            skipped += 1
        if i % 100 == 0:
            print(f"  进度 {i}/{len(uniq)}")

driver.close()
print("=" * 55)
print(f"导入完成：成功 {created} 条，跳过 {skipped} 条（端点不在图谱/已存在）")
print("在 Neo4j 里查看：MATCH (a:Term)-[r]->(b:Term) RETURN a.name, type(r), b.name LIMIT 100")
