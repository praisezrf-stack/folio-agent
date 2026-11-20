"""
注册 + 登录
"""

from folioAgent.db.store import db_server
from fastapi import HTTPException

def create_user(name, password_hash):
    if not name or not password_hash:
        return None
    user = get_user_by_name(name)
    if user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    result = db_server.fetch_one(
        """
INSERT INTO users(name,password_hash)
VALUES (%s,%s)
RETURNING id
""",
        (name, password_hash),
    )
    return result


def get_user_by_name(name):
    if not name:
        return None
    result = db_server.fetch_one(
        """
SELECT name,id,password_hash
FROM users 
WHERE name =%s
""",
        (name,),
    )
    return result
