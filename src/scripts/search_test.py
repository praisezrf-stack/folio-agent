"""
要理解的三件事：

两表关系逼你显式建文档：先 INSERT INTO documents (title, source_path) RETURNING id 拿到 doc_id，再插 chunks——这就是外键存在的意义
向量要转成字符串传：pgvector 接受 '[0.1,0.2,...]' 这种文本字面量，psycopg 里传 str(vec) 即可，不用装额外的适配器
3 条假句子要语义上明显不同：一条讲 LangGraph/StateGraph、一条讲天气、一条讲菜谱——这样才能看出检索是不是真的按“意思”匹配，而不是随机
"""