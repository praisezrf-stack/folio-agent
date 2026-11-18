def save_chunks(connect, data):
    """存储chunks"""
    with connect.cursor() as cur:
        cur.executemany(
            """
    INSERT INTO chunks (document_id,content,embedding,chunk_index)
    VALUES(%s,%s,%s,%s)
    """,
            data,
        )
        print("完成")


def save_doc(connect, upload_url):
    with connect.cursor() as cur:
        data = [(file.get("name", ""), file.get("url", "")) for file in upload_url]
        source_path = [(d[1],) for d in data]
        cur.executemany(
            """
    DELETE FROM documents
    WHERE source_path=%s
    """,
            source_path,
        )
        print("=== 正在上传doc ===")

        cur.executemany(
            """
    INSERT INTO documents(filename,source_path)
    VALUES(%s,%s)
    RETURNING id
    """,
            data,
            returning=True,
        )
        document_ids = []
        if data:
            while True:
                row = cur.fetchall()
                document_ids.append(row[0])
                if not cur.nextset():
                    break
        return document_ids


def find_chunks(connect, emb_result):
    with connect.cursor() as cur:
        cur.execute(
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
        result = cur.fetchall()
        return result
