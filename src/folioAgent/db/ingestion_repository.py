from folioAgent.config import require_env
from folioAgent.config import upload_url



def save_chunks(connect,data):
    """存储chunks"""
    print('=== 开始存储chunks ===')
    with connect.cursor() as cur:
        cur.executemany(
            """
    INSERT INTO chunks (document_id,content,embedding,chunk_index)
    VALUES(%s,%s,%s,%s)
    """,
            data,
        )
        print('完成')

def save_doc(connect):
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
            returning=True
        )
        result = cur.fetchone()

        return result[0]
