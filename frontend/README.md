# Folio 前端

独立的 Vue 3 + Vite 项目。只有文档上传、文档问答和引用来源展示，不修改现有 Python 代码。使用普通 JSON 响应，不包含流式输出、登录或聊天记录持久化。打开页面会加载后端文档列表，刷新会清空对话。

## 启动

```bash
cd frontend
npm install
npm run dev
```

生产构建：`npm run build`，输出到 `dist/`。

## 对接接口

开发时默认通过 Vite 的 `/backend` 代理请求 `http://localhost:8000`，无须修改后端跨域设置。复制 `.env.example` 为 `.env.local` 后可用 `VITE_API_PROXY_TARGET` 更改后端地址，修改后重启开发服务。`VITE_API_BASE_URL` 默认是 `/backend`，也可改为后端完整地址（直连需要后端允许跨域）。生产部署需自行配置 `/backend` 反向代理，或者使用完整地址。

所有请求都在 `src/api.js`，可直接修改路径或字段。

### 上传文档

`POST /documents`，前端发送 `multipart/form-data`，文件字段名 `file`。选择多个文件时，前端逐个调用。按当前 `save_doc()` 返回的 ID 元组列表读取上传结果：

```json
{ "code": 200, "content": [[1]], "msg": "上传成功" }
```

`code` 不为 200 时显示后端的 `msg`。上传成功仅显示“已上传”，不代表文档已经解析并建立检索索引。

### 文档列表

`GET /documents?id=`。当前后端 `id` 为必填查询参数，因此查询全部时显式传空字符串。按当前仅查询 `filename` 的返回格式展示：

```json
[["产品说明.pdf"], ["项目介绍.md"]]
```

页面初始化时加载。由于列表没有返回 ID，这些历史文档只展示名称，暂不参与聊天；本次上传返回了 ID 的文档可用于聊天请求。

### 当前 Python 接口仍需补充

- `upload_files(file)` 将 `file` 识别为查询参数，无法接收前端的文件表单；需要用 `UploadFile` / `File` 接收文件，保存到服务端，再将真实的 `{name, url}` 传给 `save_doc()`。浏览器不能提供本地文件的真实绝对路径。
- 上传时数据库连接未提交、未关闭。需要提交事务，或用连接上下文管理事务。
- 列表建议同时返回 `id` 和 `filename`，方便刷新后继续对文档提问；届时前端的列表映射也需一起调整。
- 按 ID 查询时，SQL 参数应为 `(id,)`，当前传入的是单个字符串；`id` 也可设默认值，允许不传。
- 当前仅保存文档记录，没有执行解析、分块和索引；聊天接口也还未实现。

### 文档问答

`POST /api/chat`，仍是预留接口，当前 Python 尚未提供。请求为 JSON：

```json
{
  "question": "这份文档讲了什么？",
  "document_ids": [1],
  "history": [
    { "role": "user", "content": "之前的问题" },
    { "role": "assistant", "content": "之前的回答" }
  ]
}
```

`history` 只包含当前问题之前的对话；检索范围为本次页面中成功上传并返回 ID 的文档。

响应格式：

```json
{
  "answer": "文档主要介绍了……",
  "sources": [
    { "name": "产品说明.pdf", "content": "检索命中的原文片段……" }
  ]
}
```

没有来源时 `sources` 可以省略或返回空数组。回答和原文按纯文本显示。
