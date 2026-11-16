from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    ExperimentalMarkdownSyntaxTextSplitter,
)
from folioAgent.llm.gateway import get_embedder
from pathlib import Path
import re

embedder = get_embedder()


# 嵌入
def embed_fn(chunks):
    if isinstance(chunks, list):
        res = embedder.embed_documents(chunks)
    else:
        res = embedder.embed_query(chunks)
    return res


# 切片
def splitter_loader(content):
    # 正则匹配，去掉content中的\\_，因为thread_id会被转成thread\\_id
    content = re.sub(r"\\+_", "_", content)
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
        headings = [doc.metadata.get("一级标题", ""), doc.metadata.get("二级标题", "")]
        prefix = "\n\n".join(headings)
        page_content = doc.page_content
        if len(page_content) > 1200 and "Code" not in doc.metadata:
            chunks = splitter.split_text(page_content)
        else:
            chunks = [page_content]
        for chunk in chunks:
            chunk_content = prefix + chunk
            embedded_chunks.append(
                {
                    "vector": embed_fn(chunk_content),
                    "chunk_content": chunk_content,
                }
            )
    return title, embedded_chunks


if __name__ == "__main__":
    r = splitter_loader(
        Path("/Users/fang/learning/folio-agent/src/scripts/test.md").read_text()
    )
