"""
users        → 谁在用你的系统（用户名 + 密码）
conversations→ 每次聊天是一个会话（属于哪个用户）
messages     → 会话里的每一条消息（属于哪个会话）
"""

from folioAgent.db.store import db_server


def main():
    # 创建users
    db_server.execute("""
CREATE TABLE IF NOT EXISTS users(
id BIGSERIAL PRIMARY KEY,
name TEXT NOT NULL CHECK (name<>''),
password_hash TEXT NOT NULL CHECK (password_hash<>''),
created_at TIMESTAMPTZ DEFAULT NOW()
)
""")
    # 创建会话表
    db_server.execute("""
CREATE TABLE IF NOT EXISTS conversations(
id BIGSERIAL PRIMARY KEY,
user_id BIGINT NOT NULL  REFERENCES users(id) ON DELETE CASCADE,
title TEXT NOT NULL CHECK (title<>''),
created_at TIMESTAMPTZ DEFAULT NOW()
)
""")
    # 消息表
    db_server.execute("""
CREATE TABLE IF NOT EXISTS messages(
id BIGSERIAL PRIMARY KEY,
role TEXT NOT NULL,
content TEXT NOT NULL CHECK (content<>''),
conversation_id BIGINT NOT NULL  REFERENCES conversations(id) ON DELETE CASCADE,
created_at TIMESTAMPTZ DEFAULT NOW()
)
""")

if __name__ == "__main__":
    main()