from folioAgent.db.store import db_server


def save_chunks(data):
    """存储chunks"""
    db_server.executemany(
        """
    INSERT INTO chunks (document_id,content,embedding,chunk_index)
    VALUES(%s,%s,%s,%s)
    """,
        data,
    )
    print("完成")


def save_doc(upload_url):
    data = [(file.get("name", ""), file.get("url", "")) for file in upload_url]
    source_path = [(d[1],) for d in data]
    db_server.executemany(
        """
    DELETE FROM documents
    WHERE source_path=%s
    """,
        source_path,
    )
    print("=== 正在上传doc ===")

    document_ids: list = db_server.executemany(
        """
    INSERT INTO documents(filename,source_path)
    VALUES(%s,%s)
    RETURNING id
    """,
        data,
        returning=True,
    )

    return document_ids


def find_chunks(emb_result):
    result = db_server.execute(
        """
                    SELECT c.content,
                    c.chunk_index,
                    d.filename,
                    1 - (embedding <=> %s::vector)
                    FROM chunks AS c
                    JOIN documents AS d ON c.document_id = d.id
                    WHERE 1 - (embedding <=> %s::vector) >=0.5
                    ORDER BY embedding <=> %s::vector
                    LIMIT 5
                    """,
        (str(emb_result), str(emb_result), str(emb_result)),
    )
    return result
