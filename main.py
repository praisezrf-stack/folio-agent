from fastapi import FastAPI,UploadFile,File
from folioAgent.db.ingestion_repository import save_doc
from folioAgent.db.store import get_db_connect

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents")
def upload_files(file:UploadFile=File()):
    if not file:
        return {"code": 403, "msg": "请上传文件"}
    files = []
    if not isinstance(file, list):
        files = [file]
    else:
        files = file
    ids = save_doc(get_db_connect(), files)
    if ids:
        return {"code": 200, "content": ids, "msg": "上传成功"}
    return {"code": 400, "msg": "上传失败"}


@app.get("/documents")
def get_doc(id):
    with get_db_connect() as conn:
        with conn.cursor() as cur:
            if not id:
                cur.execute("""
    SELECT filename,
    id
    FROM documents
    """)
            else:
                cur.execute(
                    """
                    SELECT filename,
                    id
                    FROM documents
                    WHERE id=%s
                """,
                    id,
                )
            return cur.fetchall()
