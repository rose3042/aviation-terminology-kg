import json
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"  # 如果密码不同请修改

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def create_relationship(tx, subj, rel, obj):
    query = f"MERGE (a:Term {{name: $subj}}) MERGE (b:Term {{name: $obj}}) MERGE (a)-[:`{rel}`]->(b)"
    tx.run(query, subj=subj, obj=obj)

with open('extracted_relations_500.json', 'r', encoding='utf-8') as f:
    triples = json.load(f)

print(f"共 {len(triples)} 条关系，开始导入...")

with driver.session() as session:
    for i, trip in enumerate(triples):
        session.execute_write(create_relationship, trip['subject'], trip['relation'], trip['object'])
        if (i+1) % 100 == 0:
            print(f"已导入 {i+1} 条")

driver.close()
print("导入完成！")