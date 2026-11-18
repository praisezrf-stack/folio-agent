<!--
Source-URL: https://docs.langchain.com/oss/python/langgraph/persistence.md
HTML-URL: https://docs.langchain.com/oss/python/langgraph/persistence
Downloaded: 2026-11-17 10:02:55 Asia/Shanghai
Original-Language: English
Official-Section: LangGraph > Capabilities
Category: capability
-->

> ## 文档索引
> 完整文档索引：https://docs.langchain.com/llms.txt
> 在进一步阅读之前，可使用此文件发现所有可用页面。

# 持久化

> LangGraph 的持久化层通过检查点保存器为智能体提供短期记忆，通过存储提供长期记忆。

持久化使 LangGraph 应用能够在单次图运行结束后保留有用的信息。当智能体需要延续对话、中断后恢复、从故障中恢复，或跨交互记住信息时，这一点就非常重要。

LangGraph 提供两个互补的持久化系统：

* **[检查点保存器](https://docs.langchain.com/oss/python/langgraph/checkpointers.md)**将某个线程的图状态持久化为检查点。它适用于短期、线程范围内的记忆，包括对话连续性、人工介入工作流、时间旅行和容错。
* **[存储](https://docs.langchain.com/oss/python/langgraph/stores.md)**在图状态之外持久化应用自定义的数据。它适用于长期、跨线程的记忆，包括用户偏好、事实和共享知识。

大多数应用可以同时使用两者：[检查点保存器](https://docs.langchain.com/oss/python/langgraph/checkpointers.md)追踪当前线程，[存储](https://docs.langchain.com/oss/python/langgraph/stores.md)则追踪跨线程的持久信息。

## 快速入门

编译图时配置检查点保存器、存储，或同时配置两者：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

checkpointer = InMemorySaver()
store = InMemoryStore()

graph = builder.compile(checkpointer=checkpointer, store=store)

result = graph.invoke(
    {"messages": [{"role": "user", "content": "Hi, my name is Bob."}]},
    {"configurable": {"thread_id": "thread-1"}},
)
```

> [!NOTE]
>
> **Agent Server 会自动处理持久化**
> 使用 [Agent Server](https://docs.langchain.com/langsmith/agent-server.md) 时，不需要手动实现或配置检查点保存器和存储。服务器会在后台处理持久化基础设施。

## 检查点保存器与存储的对比

| | 检查点保存器 | 存储 |
| - | - | - |
| 持久化内容 | 图状态快照 | 应用自定义的键值数据 |
| 范围 | 单个线程 | 跨线程 |
| 记忆类型 | 短期、线程范围内的记忆 | 长期、跨线程记忆 |
| 适用场景 | 对话连续性、人工介入、时间旅行和容错 | 用户偏好、事实和共享知识 |
| 访问方式 | 在图配置中传入 `thread_id` | 从节点或应用代码中读取和写入条目 |
| 完整指南 | [检查点保存器](https://docs.langchain.com/oss/python/langgraph/checkpointers.md) | [存储](https://docs.langchain.com/oss/python/langgraph/stores.md) |

## 常见问题排查

### PostgresSaver：`thread_id` 过长

使用 `PostgresSaver`（或 `AsyncPostgresSaver`）时，`thread_id` 存储在一个长度受限的列中。如果 `thread_id` 超出列大小，就会出现数据库错误。

**解决方法：**将 `thread_id` 的值保持在 255 个字符以内。如果需要确定性的 ID，可以使用 UUID 或哈希值：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain_core.utils.uuid import uuid7
config = {"configurable": {"thread_id": str(uuid7())[:255]}}
```

### `MemorySaver` 无法在重启后保留数据

`MemorySaver` 和 `InMemorySaver` 将检查点保存在内存中。进程重启后，所有检查点都会丢失。

**解决方法：**生产环境使用持久化检查点保存器：

* `PostgresSaver`：基于 PostgreSQL，支持异步
* `SqliteSaver`：基于本地文件的存储，适用于开发环境

### 检查点无限增长

在长时间的对话中，检查点会不断累积。这会增加延迟和存储成本。

**解决方法：**定期清理旧检查点，或设置保留策略：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string("postgresql://...")
checkpointer.setup()  # Creates tables with indexes
# Consider adding a cron job to delete checkpoints older than N days
```

### 从父图访问子图状态

子图更新状态时，父图可能无法立即看到变化。这是因为每个子图都管理自己的检查点命名空间。

**解决方法：**对于需要跨越图边界的数据，使用[通过 Store 共享状态](https://docs.langchain.com/oss/python/langgraph/stores.md)的方式，或配置子图将数据写入父图的检查点。

## 后续步骤

* [使用检查点保存器](https://docs.langchain.com/oss/python/langgraph/checkpointers.md)持久化并检查线程状态。
* [使用存储](https://docs.langchain.com/oss/python/langgraph/stores.md)跨线程持久化长期保留的数据。

***

[连接这些文档](https://docs.langchain.com/use-these-docs.md) ，通过 MCP 将其接入你选择的智能体，以获取实时答案。

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/langgraph/persistence.mdx) 或[提交问题](https://github.com/langchain-ai/docs/issues/new/choose).
