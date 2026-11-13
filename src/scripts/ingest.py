"""
素材已就位：data/corpus/langgraph-core-concepts.md。照指南文档 §2 写 src/scripts/ingest.py：

读文件 → 标题感知切片：按 ## 标题边界切，单块超 1200 字符再按段落二次切，代码块（``` 围栏）绝不能拦腰切断——这份文档 8 个章节 + 7 个代码块，正好是实战
幂等：先 DELETE FROM documents WHERE filename = %s（外键级联会清掉 chunks）再插，重跑不翻倍
验收：入库后 10~20 个 chunk；然后拿指南里那 4 个测试查询跑检索——特别是 怎么让模型决定要不要调用工具？（问题用词和文档完全不同，还能命中“工具调用循环”章节才算过关）和 怎么实现人工审核后再执行？
写完把 chunk 切分结果（每块的字数和所属章节）和检索输出贴我。这一步过了，⑤ 就只是“循环调 ingest 灌全量 + 写 ask.py”了。
"""

from folioAgent.rag.parser import parser
from folioAgent.rag.splitter import splitter_loader
from folioAgent.db.ingestion_repository import save_chunks, save_doc
from folioAgent.db.store import get_db_connect
from folioAgent.llm.gateway import get_embedder



def parse_doc():
    with get_db_connect() as conn:
        document_id = save_doc(conn)
        print("=== 文档存储完成 ===")
    # 解析文档并切片
    content_list: list = parser()
    print(f"=== 文件解析完成 ===")
    # 存储文档

    for content in content_list:
        title, embedded_chunks = splitter_loader(content["content"])
        data = [
            (
                document_id,
                chunk["chunk_content"],
                str(chunk["vector"]),
                index,
            )
            for index, chunk in enumerate(embedded_chunks)
        ]
        # 存储chunk
        with get_db_connect() as conn:
            save_chunks(conn, data)


if __name__ == "__main__":
    parse_doc()
    # 测试集
    q = [
        "怎么让模型自己判断要不要调用工具，并在工具执行完后继续回答？",
        "用户上一轮告诉了模型自己的名字，下一轮怎样让模型还记得？",
        "怎么让程序执行到一半先暂停，等人工审核通过后再接着执行？",
        "为什么每次收到新消息，之前的聊天记录就被覆盖了？该怎么保留？",
    ]
    emb = get_embedder()
    emb_result = emb.embed_documents(q)
    with get_db_connect() as conn:
        with conn.cursor() as cur:
           cur.execute("""
               SELECT content,
                   1 - (embedding <=> %s::vector) AS similarity
               FROM chunks
               WHERE 1 - (embedding <=> %s::vector)>=0.7
               ORDER BY embedding <=> %s::vector
               LIMIT 3
               """,(str(emb_result),str(emb_result),str(emb_result)))
           
       