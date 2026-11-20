# M2 开发文档：FastAPI 后端（Folio 第二层）

> 前置状态：M1 已结业（Agent 层完成：多格式 ingestion / 标题感知切片 / pgvector 检索 / 带引用问答）。
> 本文档对着你的真实代码写：`src/folioAgent/`（config、llm/gateway、rag/、db/）+ 根目录 `main.py`。
> 工作方式：你写代码，文档给「做什么、为什么、坑在哪」，每步带自测。

---

## 0. M2 在架构里的位置

```
[前端 M3] ──HTTP──> [M2 后端网关] ──函数调用──> [M1 Agent 层]
                     JWT / 会话 / SSE            rag/ db/ llm/
                     ↑ 本文档要建的就是这一层
```

M2 的核心原则（来自架构文档，也是面试题答案）：**Agent 不做鉴权，权限由后端算好再往下传**。
你的 `find_chunks` / `create_model` 会原样复用——M2 只是在它们外面套一层"治理壳"。

## 1. 完成标准（DoD，全部打勾才结业）

- [ ] ① 注册/登录可用，返回 JWT；错误密码返回 401
- [ ] ② 无 token 访问 /chat 返回 401；带过期 token 也返回 401
- [ ] ③ 提问后 messages 表能看到 user/assistant 两条记录，重开会话不丢历史
- [ ] ④ /chat/stream 用 curl 能看到逐段输出（SSE 格式）
- [ ] ⑤ `docker compose up -d` 一键起 backend + postgres（+redis）
- [ ] ⑥ 同一问题连续问 6 次，第 6 次被限流（429）

## 2. 环境准备（10 分钟）

**依赖**（你已装 fastapi/uvicorn/python-multipart，还差两个）：

```bash
uv add pyjwt bcrypt
```

- `pyjwt`：签发/校验 JWT
- `bcrypt`：密码哈希。**故意不用 passlib**——passlib 1.7.4 与新版 bcrypt 不兼容（会报 `password cannot be longer than 72 bytes` 附近的错），直接用 bcrypt 原生 API：`bcrypt.hashpw(pw, bcrypt.gensalt())` / `bcrypt.checkpw(pw, hash)`

**`.env` 新增两个键**：

```bash
JWT_SECRET=随机长字符串（openssl rand -hex 32 生成）
JWT_EXPIRE_HOURS=24
REDIS_URL=redis://localhost:6379/0
```

**compose**：把 `src/folioAgent/docker/compose.yml` 里的服务名 `folioAgent` 改成 `postgres`（跑的是数据库却叫 agent，三个月后的你会困惑），并新增 redis 服务（镜像 `redis:7-alpine`，健康检查 `redis-cli ping`）。

## 3. 代码结构规划（对着现有结构长，不推倒重来）

```
src/folioAgent/
    config.py            # 加 jwt_secret / jwt_expire / redis_url 字段
    security.py          # 新建：密码哈希 + JWT 签发/校验（T2/T3）
    auth/
        __init__.py
        routes.py        # 注册/登录路由（T2）
        dependencies.py  # get_current_user 依赖（T3）
    chat/
        __init__.py
        routes.py        # /chat 与 /chat/stream（T5/T6）
        service.py       # 编排：检索→prompt→模型（复用 M1 的 find_chunks）
    db/
        store.py         # 已有，不动
        ingestion_repository.py   # 已有 find_chunks，不动
        chat_repository.py        # 新建：会话与消息的读写（T4）
        schema.py        # 新建：users/conversations/messages 建表（T1）
main.py                  # 收口：include 各路由，只留 app 装配
```

要点：`main.py` 从"什么都干"变成"只做装配"——现在它里面的 `/documents` 上传接口调 `save_doc(get_db_connect(), files)`，传的是 `UploadFile` 对象而 `save_doc` 期望 dict，**这个接口现在是坏的**。M2 先注释掉它，文件上传放到 M4（要接 MinIO，现在不值得做）。

## 4. 任务卡

### T1 建三张表（约 30 分钟）

在 `db/schema.py` 写建表 DDL，提供一个 `init_tables(conn)` 函数，让启动时自动执行（幂等：全部 `IF NOT EXISTS`）：

```sql
users(
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT now()
)
conversations(
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT DEFAULT '新会话',
    created_at TIMESTAMPTZ DEFAULT now()
)
messages(
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,        -- 'user' / 'assistant'
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
)
```

**为什么三张表、为什么这个外键方向**：用户删号→会话级联删→消息跟着没，数据不残留（和 M1 的 documents→chunks 级联同一个思路）。

自测：启动后 `psql -c '\dt'` 能看到 5 张表。

### T2 注册/登录（约 1 小时）

`security.py` 两个函数 + `auth/routes.py` 两个路由：

- `hash_password(raw) -> str`、`verify_password(raw, hash) -> bool`（bcrypt）
- `POST /auth/register`：用户名+密码 JSON 入参 → 查重（`UNIQUE` 冲突要捕获，返回 409 而不是 500）→ 落库 → 201
- `POST /auth/login`：验证通过 → 签发 JWT → 返回 `{"access_token": ..., "token_type": "bearer"}`

**JWT 的三段结构**（理解了才能校验）：header.payload.signature。payload 里放 `{"sub": user_id, "exp": 过期时间戳}`。签发用 `jwt.encode(payload, JWT_SECRET, algorithm="HS256")`——secret 只在服务端，客户端拿到 token 也改不了 payload（改了签名对不上）。

自测：curl 注册 → 登录 → 拿到三段式 token；用错密码拿到 401。

### T3 JWT 校验依赖（约 1 小时）

`auth/dependencies.py`：

```python
def get_current_user(authorization: str = Header(...)) -> User:
    # 1. 取 "Bearer xxx" 里的 xxx
    # 2. jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    # 3. 捕获 jwt.ExpiredSignatureError → 401 "token 过期"
    #    捕获 jwt.InvalidTokenError   → 401 "token 无效"
    # 4. 用 sub 里的 user_id 查库确认用户存在
```

路由上挂 `user = Depends(get_current_user)`。**统一异常处理**：校验失败抛 `HTTPException(401, ...)`，别返回 200 加个错误字段——HTTP 状态码本身就是契约。

**必踩的坑**：`algorithms` 参数必须显式写。不写的话某些库版本默认接受多种算法，攻击者可以用 `alg: none` 伪造 token——这是 JWT 最经典的漏洞，写上这条既是安全也是面试谈资。

自测：无 token 访问受保护接口 → 401；伪造 token → 401；真 token → 200。

### T4 会话 CRUD（约 1 小时）

`db/chat_repository.py` 四个函数（raw SQL，和 M1 的 repository 风格一致，**不引入 ORM**——你现在 psycopg 写得正顺，ORM 是另一套心智模型，M4 之后再考虑）：

- `create_conversation(conn, user_id)` → id
- `list_conversations(conn, user_id)` → 侧边栏列表
- `get_messages(conn, conversation_id)` → 历史消息
- `append_message(conn, conversation_id, role, content)`

`chat/routes.py` 挂三个路由（全部 `Depends(get_current_user)`）：`POST /conversations`、`GET /conversations`、`GET /conversations/{id}/messages`。

**安全细节**：查会话时 SQL 必须带 `AND user_id = %s`——否则任何登录用户能读任何人的会话（IDOR，越权访问，企业级安全的高频考点）。

### T5 /chat 同步接口（约 1.5 小时，M1 能力的第一次 HTTP 化）

`chat/service.py` 编排函数——把 ask.py 的逻辑搬进来，但**历史由数据库管**：

```
入参: user, conversation_id, question
1. append_message(user)                        # 先落用户消息
2. history = get_messages(...)                 # 取最近 N 条历史
3. rows = find_chunks(conn, embed(question))   # 复用 M1 的检索
4. prompt = system提示词 + 参考资料(rows) + history + question
5. answer = model.invoke(messages)
6. append_message(assistant)                   # 再落模型消息
7. 返回 {answer, sources: rows}
```

`chat/routes.py`：`POST /chat`，`Depends(get_current_user)`，返回 JSON。

**开工前必须先清的两个 M1 遗留**（不然后端一启动就出事）：

1. `splitter.py` 顶层 `embedder = get_embedder()` → 改函数内懒加载。后端启动会 import 这个模块，2GB 模型跟着加载，服务起来要十几秒
2. `parser.py` 顶层 `TOKEN = require_env("MINERU_API_KEY")` → 懒加载。import 时强校验环境变量，任何部署环境少一个 key 整个服务起不来

自测：登录 → 建会话 → 提问 → 回答带引用；`GET /conversations/{id}/messages` 能看到两条记录。

### T6 SSE 流式接口（约 1.5 小时，M2 的技术亮点）

`POST /chat/stream`，同 T5 逻辑但第 5 步换 `model.stream(messages)`，用 `StreamingResponse` 逐段推送：

```python
def gen():
    for chunk in model.stream(messages):
        yield f"data: {json.dumps({'delta': chunk.content}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

return StreamingResponse(gen(), media_type="text/event-stream")
```

**必须知道的三个坑**：

1. `media_type="text/event-stream"` 不写，浏览器收不到流
2. SSE 消息以 `\n\n`（两个换行）结尾才算一条完整事件——一个 `\n` 不行
3. 每条 data 里 `ensure_ascii=False`，否则中文变 `\uXXXX`，前端要自己解码

**为什么先落库再流式**：流式过程中客户端可能断开（关浏览器），生成一半的答案丢了——所以完整答案在生成器结束后仍要 `append_message` 落库（放 try/finally 里），保证历史完整。

自测：`curl -N -X POST .../chat/stream -H "Authorization: Bearer ..." -d '{"question":"什么是checkpointer"}'`，终端里能看到文字一段一段冒出来。

### T7 限流 + compose 扩容（约 1 小时）

限流（架构文档里 L5 治理层的最小实现）：`chat/routes.py` 里每次提问前 `redis.incr(f"rate:{user.id}")`，超过阈值（比如 5 次/分钟）抛 429。带过期时间的计数器，`redis.expire(key, 60)`。

compose 加 `backend` 服务（T8 的容器化一起做）：

```yaml
backend:
    build: ..            # 需要在项目根写 Dockerfile
    ports: ["8000:8000"]
    env_file: ../.env    # 注意 PG_DSN 里的 host 要改成 postgres（compose 服务名）
    depends_on: postgres(healthy), redis(healthy)
```

**Dockerfile 五行**（uv 官方镜像 `ghcr.io/astral-sh/uv:python3.14-bookworm-slim`，`uv sync --frozen`，`uvicorn main:app --host 0.0.0.0`）。

**最经典的坑**：容器里 `localhost` 是容器自己，不是你的 Mac——`.env` 里 `PG_DSN` 的 host 要换 `postgres`、`REDIS_URL` 的 host 换 `redis`。别把生产 .env 提交进 git。

### T8 全链路自测（30 分钟）

写一个 `scripts/smoke_test.sh`，串起完整用户旅程：注册 → 登录 → 建会话 → 同步提问 → 流式提问 → 查历史 → 连问 6 次触发 429。跑通 = DoD 全打勾。

## 5. 坑速查表

| 坑 | 症状 | 解法 |
|---|---|---|
| passlib + 新 bcrypt 不兼容 | 注册时报 72 bytes 相关错误 | 直接用 `bcrypt` 库 |
| jwt.decode 不写 algorithms | token 被伪造也没报错 | 显式 `algorithms=["HS256"]` |
| SSE 忘 media_type | curl 卡住不输出 | `text/event-stream` |
| SSE 单换行 | 前端收不到事件 | 每条以 `\n\n` 结尾 |
| 容器内 localhost | backend 连不上数据库 | host 用 compose 服务名 `postgres` |
| main.py import splitter | 启动加载 2GB 模型 | splitter/parser 改懒加载（T5 前必做） |
| UNIQUE 冲突 | 重复注册返回 500 | 捕获 `UniqueViolation` 返回 409 |
| 会话查询不带 user_id | A 用户能读 B 的会话 | SQL 永远带 `AND user_id=%s` |

## 6. M2 之后的预告

M3 前端（Vite+React：登录页、SSE 聊天、会话列表、引用折叠展示）→ M4 加固（审计页、20 条评测集、DeepAgents 复杂任务）。M2 做扎实，M3 的前端只需要消费你现在定义的接口契约。
