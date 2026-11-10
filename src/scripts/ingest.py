"""
素材已就位：data/corpus/langgraph-core-concepts.md。照指南文档 §2 写 src/scripts/ingest.py：

读文件 → 标题感知切片：按 ## 标题边界切，单块超 1200 字符再按段落二次切，代码块（``` 围栏）绝不能拦腰切断——这份文档 8 个章节 + 7 个代码块，正好是实战
幂等：先 DELETE FROM documents WHERE filename = %s（外键级联会清掉 chunks）再插，重跑不翻倍
验收：入库后 10~20 个 chunk；然后拿指南里那 4 个测试查询跑检索——特别是 怎么让模型决定要不要调用工具？（问题用词和文档完全不同，还能命中“工具调用循环”章节才算过关）和 怎么实现人工审核后再执行？
写完把 chunk 切分结果（每块的字数和所属章节）和检索输出贴我。这一步过了，⑤ 就只是“循环调 ingest 灌全量 + 写 ask.py”了。
""" 
def parse_doc():
    # TODO: 通过 HTTP 接口解析文档。
    raise NotImplementedError("待接入 MinerU HTTP 接口")
