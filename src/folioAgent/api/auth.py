"""鉴权"""

from folioAgent.db.user_repository import get_user_by_name, create_user
import bcrypt
from fastapi import HTTPException


def login(name, password:str):
    if not name or not password:
        return {"code": 400, "msg": "请正确填写用户名或密码"}

    result = get_user_by_name(name)
    if not result:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
        )
    name, id, password_hash = result
    is_valid = bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
        )
    return {"code": 200, "name": name}


def register(name, password):
    pw = str(password).encode("utf-8")
    password_hash = bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")
    return create_user(name, password_hash)


if __name__ == "__main__":
    res = register("zrf", "abc123")
    print(res)
