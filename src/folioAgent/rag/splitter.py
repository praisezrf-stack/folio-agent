from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    ExperimentalMarkdownSyntaxTextSplitter,
)
from folioAgent.llm.gateway import get_embedder
from pathlib import Path

embedder = get_embedder()


# 嵌入
def embed_fn(chunks):
    if isinstance(chunks,list):
        res = embedder.embed_documents(chunks)
    else:
        res = embedder.embed_query(chunks)
    return res


# 切片
def splitter_loader(content):
    md_splitter = ExperimentalMarkdownSyntaxTextSplitter(
        headers_to_split_on=[("#", "一级标题"), ("##", "二级标题")]
    )

    # 递归字符串分割器
    splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\n\n",
            "\n",
            "。",
            "！",
            "？",  # 句子
            "；",
            "，",
            "、",  # 更短的片段
            " ",
            "",
        ],
        chunk_size=500,
        chunk_overlap=100,
    )
    docs = md_splitter.split_text(content)
    title = ""
    embedded_chunks = []
    for doc in docs:
        if not title:
            title = doc.metadata.get("一级标题")
        page_content = doc.page_content
        if len(page_content) > 1200 and 'Code' not in doc.metadata:
            chunks = splitter.split_text(page_content)
        else:
            chunks = [page_content]
        for chunk in chunks:
            print(isinstance(chunk,list))
            embedded_chunks.append(
                {
                    "vector": embed_fn(chunk),
                    "chunk_content": chunk,
                }
            )
    return title, embedded_chunks

if __name__=="__main__":
    r = splitter_loader(Path("/Users/fang/learning/folio-agent/src/scripts/test.md").read_text())
    print(r)