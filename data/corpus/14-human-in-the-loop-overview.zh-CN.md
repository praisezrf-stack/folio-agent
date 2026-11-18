<!--
Source-URL: https://docs.langchain.com/oss/python/concepts/human-in-the-loop.md
HTML-URL: https://docs.langchain.com/oss/python/concepts/human-in-the-loop
Downloaded: 2026-11-17 10:02:55 Asia/Shanghai
Original-Language: English
Official-Section: Learn > Conceptual overviews
Category: conceptual-overview
-->

> ## 文档索引
> 完整文档索引：https://docs.langchain.com/llms.txt
> 在进一步阅读之前，可使用此文件发现所有可用页面。

# 人工介入概览

> 智能体如何暂停工具调用以供人工审核，以及逐次调用中断与批量中断有何不同。

人工介入（Human-in-the-loop，HITL）会在工具调用执行前暂停智能体，让人进行审核。审核者可以批准调用、编辑参数、拒绝并提供反馈，或者代替工具作答。对于难以撤销或需要批准的操作，例如删除记录、发送电子邮件或写入文件，应使用此机制。

在 [LangChain](https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md) 中通过 [`HumanInTheLoopMiddleware`](https://reference.langchain.com/python/langchain/agents/middleware/human_in_the_loop/HumanInTheLoopMiddleware) 添加审核，或在 [Deep Agents](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop.md) 中使用 `interrupt_on` 参数。中间件通过以下两种模式之一暂停：

* **逐次调用**：每个需要审核的工具调用分别暂停一次。
* **批量**：每个模型轮次暂停一次，覆盖该轮次中的全部工具调用。批量模式是当前默认模式。

> [!NOTE]
>
> 逐次调用模式需要 `langchain>=1.4.6`。Deep Agents 使用批量模式。

## 从暂停到恢复的完整审批流程

无论采用哪种模式，每次审批都遵循相同的步骤：

1. 模型提出一个或多个工具调用。
2. 中间件根据你的 `interrupt_on` 策略检查每个调用。需要审核的调用通过[中断](https://reference.langchain.com/python/langgraph/types/interrupt)暂停智能体。
3. [检查点保存器](https://docs.langchain.com/oss/python/langgraph/persistence.md)保存智能体状态，因此运行可以停止并在稍后恢复，甚至可以在另一个进程中恢复。
4. 应用向审核者展示待处理调用，并收集每个调用的决策。
5. 使用 `Command(resume=...)` 恢复智能体。中间件应用每个决策，然后智能体继续运行。

决策有以下四种类型：

| 决策类型 | 说明 | 使用场景示例 |
| - | - | - |
| ✅ `approve` | 按照智能体提出的原始参数执行工具。 | 原样发送电子邮件草稿 |
| ✏️ `edit` | 在执行前修改工具参数。 | 发送邮件前更改收件人 |
| ❌ `reject` | 完全跳过该工具调用，并向智能体返回拒绝反馈。 | 拒绝删除文件并解释原因 |
| 💬 `respond` | 对于“询问用户”类工具，跳过执行，直接将人工消息作为模拟的工具结果返回。 | 直接回答 `"ask_user"` 提问 |

本页示例使用一个配有三个工具的智能体。`write_file` 允许所有决策类型；`execute_sql` 只允许 `approve` 和 `reject`；`read_data` 无需审核即可运行。在同一轮中，模型调用这三个工具。

## 分别审核每个工具调用

在逐次调用模式下，每个需要审核的工具调用在开始时都会单独暂停：

```mermaid theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
sequenceDiagram
    participant App as Your app
    participant Agent
    participant Tools

    App->>Agent: invoke(user message)
    Agent->>Tools: write_file, execute_sql, read_data
    Tools-->>Agent: read_data result (not gated, runs right away)
    Tools-->>App: interrupt for write_file
    Tools-->>App: interrupt for execute_sql
    App->>Agent: resume {write_file ID: approve, execute_sql ID: reject}
    Note over Agent: Each answer is checked against its response_schema before it is saved
    Agent->>Tools: run write_file
    Agent-->>App: final result
```

每个中断值都描述一个调用，并带有 `type: "tool_approval"`。`execute_sql` 的中断如下：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
{
    "type": "tool_approval",
    "tool_call_id": "call_sql",
    "name": "execute_sql",
    "args": {"query": "DELETE FROM orders WHERE created_at < '2025-01-01'"},
    "description": "Tool execution requires approval\n\nTool: execute_sql\nArgs: {'query': \"DELETE FROM orders WHERE created_at < '2025-01-01'\"}",
}
```

每个中断还带有 [`response_schema`](https://docs.langchain.com/oss/python/langgraph/interrupts#define-an-interrupt-response-schema)，即描述该调用接受哪些回答的 JSON 模式。对于 `execute_sql`，模式允许 `approve` 和 `reject`；对于 `write_file`，还允许 `respond` 和 `edit`。`edit` 分支包含 `write_file` 自身的参数模式。客户端可以根据模式渲染表单，而不必硬编码决策类型。[LangChain 指南](https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md#read-the-response-schema)展示了各类决策的模式。

对每个中断，以中断 ID 为键给出一个决策：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
Command(resume={
    write_file_interrupt.id: {"type": "approve"},
    execute_sql_interrupt.id: {"type": "reject", "message": "Archive the rows before deleting them."},
})
```

LangGraph 在保存之前会拒绝无效回答，因此审核者可以修正后重新回答。未回答的中断仍处于待处理状态，因此审核者可以逐个回答。

## 一次审核整个轮次

在批量模式下，中间件在模型响应后、任何工具运行前暂停一次。即使 `read_data` 不受审批控制，它也必须等待审核。一个中断会在 `action_requests` 中列出所有受审批控制的调用，并在独立的 `review_configs` 列表中列出各调用允许的决策：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
{
    "action_requests": [
        {"name": "write_file", "args": {"path": "orders_archive.csv", "content": "id,total\n1,20\n"}, "description": "..."},
        {"name": "execute_sql", "args": {"query": "DELETE FROM orders WHERE created_at < '2025-01-01'"}, "description": "..."},
    ],
    "review_configs": [
        {"action_name": "write_file", "allowed_decisions": ["approve", "edit", "reject", "respond"]},
        {"action_name": "execute_sql", "allowed_decisions": ["approve", "reject"]},
    ],
}
```

用一个决策列表作答，其顺序必须与 `action_requests` 一致：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
Command(resume={"decisions": [
    {"type": "approve"},
    {"type": "reject", "message": "Archive the rows before deleting them."},
]})
```

该中断没有 `response_schema`。只有在 LangGraph 已保存回答、且中间件实际应用决策时，中间件才会检查各决策。

## 对比批量模式的问题

批量模式按位置将回答与调用匹配，且只在保存后才检查各回答。下表逐行展示示例智能体在批量模式下遇到的问题，以及逐次调用模式如何避免这些问题：

| 批量模式中的情况 | 发生的问题 | 逐次调用模式中的情况 |
| - | - | - |
| 决策按位置与调用匹配 | 审核者本想批准 `write_file`、拒绝 `execute_sql`，却发送了 `[reject, approve]`。结果 `DELETE` 被执行。 | 每个决策以该调用的中断 ID 为键。 |
| 允许的决策位于 `review_configs` 中 | 客户端需要按位置配对两个列表，并为每种决策类型硬编码按钮。 | 每个中断的 `response_schema` 列出其决策与可编辑参数。 |
| 回答先保存，再检查 | 对两个调用只给一个决策会触发 `ValueError: Number of human decisions (1) does not match number of hanging tool calls (2).`。更正后的回答仍报相同错误，导致线程卡住。 | 先检查回答。修正后可再次回答。 |
| 编辑后的参数不检查 | 编辑 `write_file` 时即使没有 `content`，工具仍会执行，模型收到的却是一个并非它自己提出的调用的错误。 | 编辑会被拒绝，错误为 `edit.edited_action.args.content Field required`。 |

## 选择中断模式

| | 逐次调用 | 批量（默认） |
| - | - | - |
| **暂停时机** | 每个受审批控制的工具调用开始时 | 模型响应后、任何工具运行前 |
| **每轮中断数** | 每个受审批控制的工具调用各一次 | 整轮一次 |
| **本轮不受审批控制的调用** | 立即运行 | 等待审核 |
| **回答方式** | 每个中断一个决策，以中断 ID 为键 | 决策列表，按位置匹配 |
| **最适合** | 新智能体、每次调用一张审批卡片或一条消息、基于模式构建的表单 | 已读取 `action_requests` 的审批界面 |

新建智能体时请使用逐次调用模式。LangChain 计划在下一个主要版本中将其设为默认模式。

如果你的审批界面仍读取批量格式，例如采用 [`useStream` 审批模式](https://docs.langchain.com/oss/python/langchain/frontend/human-in-the-loop)构建的界面，则继续使用批量模式。

逐次调用模式还会改变中间件顺序和包含多个回答的恢复行为。切换前，请阅读[为逐次调用审核安排中间件顺序](https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md#order-middleware-for-per-call-review)和[按 ID 恢复各个调用](https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md#resume-each-call-by-id)。

## 另请参阅

* [LangChain 中的人工介入](https://docs.langchain.com/oss/python/langchain/human-in-the-loop.md)：配置中间件，并回答各种决策类型。
* [Deep Agents 中的人工介入](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop.md)：对深度智能体及其子智能体进行审批。
* [定义中断响应模式](https://docs.langchain.com/oss/python/langgraph/interrupts.md#define-an-interrupt-response-schema)：LangGraph 如何检查恢复值。

***

[连接这些文档](https://docs.langchain.com/use-these-docs.md) ，通过 MCP 将其接入你选择的智能体，以获取实时答案。

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/concepts/human-in-the-loop.mdx) 或[提交问题](https://github.com/langchain-ai/docs/issues/new/choose).
