"""初始化数据库

作用：建表。这一步会让你真正理解 RAG 的数据模型
要点：
CREATE EXTENSION IF NOT EXISTS vector —— 向量能力是扩展，不是内置
documents（文档表）+ chunks（切片表），chunks.document_id 外键关联——文档删了切片级联删
embedding vector(1024) —— 维度是硬约束，和 EMBED_DIM 配置绑定，插错维度直接报错
HNSW 索引（USING hnsw）—— 没它检索是全表扫描，有它才是“近似最近邻”查
PG_DSN 从 .env 读，别写死——和模型网关同一个道理

"""
