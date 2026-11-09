"""
要理解的三件事：

两表关系逼你显式建文档：先 INSERT INTO documents (filename, source_path) RETURNING id 拿到 doc_id，再插 chunks——这就是外键存在的意义
向量要转成字符串传：pgvector 接受 '[0.1,0.2,...]' 这种文本字面量，psycopg 里传 str(vec) 即可，不用装额外的适配器
3 条假句子要语义上明显不同：一条讲 LangGraph/StateGraph、一条讲天气、一条讲菜谱——这样才能看出检索是不是真的按“意思”匹配，而不是随机
"""

import psycopg
from folioAgent.config import require_env
from folioAgent.llm.gateway import get_embedder


emb = get_embedder()
with psycopg.connect(require_env('PG_DSN')) as conn:
   with conn.cursor() as cur:
        # 插入文档   
        cur.execute("""
INSERT INTO documents (filename,source_path)
VALUES('langgraph-core-concepts.docx','/Users/fang/learning/folio-agent/data/corpus/langgraph-core-concepts.docx')
RETURNING id;
""")
        result = cur.fetchone()
        doc_id = result[0]
        texts=[
            'LangGraph 的 StateGraph 用来构建有状态的 AI Agent 工作流',
            '今天北京天气晴朗，适合外出散步',
             "番茄炒鸡蛋需要准备鸡蛋、番茄和食盐",
        ]
        embeddings = emb.embed_documents(texts);
        for index, (embedding,content) in enumerate(zip(embeddings,texts)):
            # 插入切片
            cur.execute("""
    INSERT INTO chunks(document_id,content,embedding,chunk_index)
    VALUES(%s,%s,%s,%s)
    """,(doc_id,content,str(embedding),index))