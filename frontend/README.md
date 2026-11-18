# Folio 前端

独立的 Vue 3 + Vite 项目。只有文档上传、文档问答和引用来源展示，不修改或依赖现有 Python 代码。使用普通 JSON 响应，不包含流式输出、登录、数据库或聊天记录持久化。刷新页面会清空当前文档列表和对话。

## 启动

```bash
cd frontend
npm install
npm run dev
```

生产构建：`npm run build`，输出到 `dist/`。

## 对接接口

默认请求 `http://localhost:8000`。如需更改，复制 `.env.example` 为 `.env.local`，设置 `VITE_API_BASE_URL`，然后重启开发服务。后端需要允许前端开发地址的跨域请求（Vite 默认是 `http://localhost:5173`）。

所有请求都在 `src/api.js`，可直接修改路径或字段。

### 上传文档

`POST /api/documents`，请求为 `multipart/form-data`，文件字段名 `file`。选择多个文件时，前端逐个调用。

```json
{ "id": "doc-1" }
```

成功返回表示该文档已可检索；如果后端有异步解析流程，需要之后再接入处理状态查询。前端不限制文件类型，由后端决定支持的格式。

### 文档问答

`POST /api/chat`，请求为 JSON：

```json
{
  "question": "这份文档讲了什么？",
  "document_ids": ["doc-1"],
  "history": [
    { "role": "user", "content": "之前的问题" },
    { "role": "assistant", "content": "之前的回答" }
  ]
}
```

`history` 只包含当前问题之前的对话；检索范围为本次页面中成功上传的所有文档。

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
