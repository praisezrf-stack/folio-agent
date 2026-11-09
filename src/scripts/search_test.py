"""
检索
核心就一行 SQL 的知识：

sql

SELECT content, 1 - (embedding <=> %s::vector) AS similarity
FROM chunks ORDER BY embedding <=> %s::vector LIMIT 3
<=> 是余弦距离（0 最相似，越大越远），对应你建的 vector_cosine_ops HNSW 索引——排序算符必须和索引算符一致，否则索引白建
1 - 距离 转成相似度更好读（1 最像）
查询文本和入库文本必须用同一个 get_embedder() 实例产出的向量，模型不同则向量空间不兼容
验收标准：问“什么是 StateGraph？”，返回的第一条必须是讲 LangGraph 的那句，相似度明显高（比如 0.5+ 对 0.1 这种量级差）。
"""