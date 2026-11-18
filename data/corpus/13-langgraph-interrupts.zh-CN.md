<!--
Source-URL: https://docs.langchain.com/oss/python/langgraph/interrupts.md
HTML-URL: https://docs.langchain.com/oss/python/langgraph/interrupts
Downloaded: 2026-11-17 10:02:55 Asia/Shanghai
Original-Language: English
Official-Section: LangGraph > Capabilities
Category: capability
-->

> ## 文档索引
> 完整文档索引：https://docs.langchain.com/llms.txt
> 在进一步阅读之前，可使用此文件发现所有可用页面。

# 中断

中断允许你在特定位置暂停图执行，等待外部输入后再继续。这支持需要外部输入才能推进的人工介入模式。触发中断时，LangGraph 通过其[持久化](https://docs.langchain.com/oss/python/langgraph/persistence.md)层保存图状态，并无限期等待，直到你恢复执行。

中断通过在图节点的任意位置调用 `interrupt()` 函数实现。该函数接受任意可 JSON 序列化的值，并将其呈现给调用方。准备好继续时，使用 `Command` 重新调用图以恢复执行；其中的恢复输入会成为节点内 `interrupt()` 调用的返回值。

与在特定节点前后暂停的静态断点不同，中断是**动态的**：可以放在代码的任意位置，也可以根据应用逻辑有条件地触发。

* **检查点保存执行位置：**检查点保存器写入精确的图状态，方便稍后恢复，即使处于错误状态也可以。
* **`thread_id` 是你的指针：**设置 `config={"configurable": {"thread_id": ...}}`，告诉检查点保存器加载哪个状态。
* **中断负载通过 `stream.interrupts` 呈现：**使用[事件流](https://docs.langchain.com/oss/python/langgraph/event-streaming.md)（`graph.stream_events(..., version="v3")`）时，传给 `interrupt()` 的值出现在 `stream.interrupts` 上；运行暂停等待输入时，`stream.interrupted` 为 `True`。

你选择的 `thread_id` 实际上就是持久化游标。复用它会恢复同一个检查点；使用新值会启动状态为空的全新线程。

## 使用 `interrupt` 暂停

[`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 函数暂停图执行，并向调用方返回一个值。在节点中调用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 时，LangGraph 保存当前图状态，等待你通过输入恢复执行。

要使用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt)，需要：

1. 用于持久化图状态的**检查点保存器**（生产环境使用持久型检查点保存器）
2. 配置中的**线程 ID**，使运行时知道从哪个状态恢复
3. 在希望暂停的位置调用 `interrupt()`（负载必须可 JSON 序列化）

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langgraph.types import interrupt

def approval_node(state: State):
    # Pause and ask for approval
    approved = interrupt("Do you approve this action?")

    # When you resume, Command(resume=...) returns that value here
    return {"approved": approved}
```

调用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 时，会发生以下过程：

1. 在调用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 的位置**挂起图执行**

2. 使用检查点保存器**保存状态**，以便稍后恢复执行。生产环境应使用持久型检查点保存器（例如以数据库为后端）

3. **向调用方返回值**：使用[事件流](https://docs.langchain.com/oss/python/langgraph/event-streaming.md)（`graph.stream_events(..., version="v3")`）时通过 `stream.interrupts` 返回；使用默认 `invoke()` API 时通过 `__interrupt__` 返回。该值可以是任意可 JSON 序列化的值（字符串、对象、数组等）

4. **图无限期等待**，直到你提供响应以恢复执行

5. 恢复时，**将响应传回节点**，作为 `interrupt()` 调用的返回值

## 恢复中断

中断暂停执行后，通过带有恢复值的 `Command` 再次调用图，即可恢复。恢复值会传回 `interrupt` 调用，使节点能够利用外部输入继续执行。

对于可能中断的图，推荐使用[事件流](https://docs.langchain.com/oss/python/langgraph/event-streaming.md)来驱动：它通过 `stream.interrupts` 和 `stream.interrupted` 呈现中断，并通过 `stream.output` 暴露最终状态。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langgraph.types import Command

# Initial run - hits the interrupt and pauses
# thread_id is the persistent pointer (stores a stable ID in production)
config = {"configurable": {"thread_id": "thread-1"}}
stream = graph.stream_events({"input": "data"}, config=config, version="v3")

# Drain the stream to drive the run; stream.output awaits the final state.
final = stream.output

# stream.interrupted is True when the run paused for human input, and
# stream.interrupts contains the payloads passed to interrupt().
if stream.interrupted:
    print(stream.interrupts)
    # > (Interrupt(value='Do you approve this action?'),)

# Resume with the human's response
# The resume payload becomes the return value of interrupt() inside the node
resumed = graph.stream_events(Command(resume=True), config=config, version="v3")
final = resumed.output
```

> [card] [查看示例追踪](https://smith.langchain.com/public/cd7406ad-294e-4d98-b0ae-d9ed7930e117/r)
>
> 打开此示例的公开 LangSmith 运行记录。

> [!NOTE]
>
> 默认的 `graph.invoke(...)` API 仍然可用，通过 `result["__interrupt__"]` 呈现中断。不需要流式投影时可使用它；否则优先使用 `graph.stream_events(..., version="v3")`。

**关于恢复的要点：**

* 恢复时必须使用中断发生时的**同一线程 ID**
* 传给 `Command(resume=...)` 的值成为 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 调用的返回值
* 恢复时，会从调用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 的节点的开头重新执行，因此 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 之前的任何代码都会再次运行
* 可以传入任意可 JSON 序列化的恢复值；指定类型化 `response_schema` 时，该值需要通过验证

> [!WARNING]
>
> `Command(resume=...)` 是**唯一**用于作为 `invoke()`／`stream()`／`stream_events()` 输入的 `Command` 模式。其他 `Command` 参数（`update`、`goto`、`graph`）用于[从节点函数返回](https://docs.langchain.com/oss/python/langgraph/graph-api.md#command)。不要将 `Command(update=...)` 作为输入来继续多轮对话——应传入普通的输入字典。

## 定义中断响应模式

[`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 的 `response_schema` 参数描述恢复图时预期的输入。客户端可以据此渲染类型化输入表单。

> [!NOTE]
>
> 中断响应模式需要 `langgraph>=1.2.12`。

传入 Pydantic 模型类、来自 `typing_extensions` 的 `TypedDict` 或数据类，以验证恢复值。LangGraph 将类型转换为 JSON Schema，并将其包含在 `Interrupt.response_schema` 中，与中断的 `value` 负载分离。返回给调用方的中断及检查点任务中的中断都可访问该模式。

此示例使用 LangGraph 中断测试中的审批模式：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from typing import Any

from pydantic import BaseModel
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph
from langgraph.types import Command, interrupt


class Decision(BaseModel):
    approved: bool
    note: str | None = None


class State(TypedDict):
    answer: Any


def node(state: State) -> State:
    answer = interrupt({"question": "approve?"}, response_schema=Decision)
    return {"answer": answer}


graph = (
    StateGraph(State)
    .add_node("node", node)
    .add_edge(START, "node")
    .compile(checkpointer=InMemorySaver())
)
config = {"configurable": {"thread_id": "1"}}

result = graph.invoke({"answer": None}, config)
pending = result["__interrupt__"][0]
assert pending.response_schema == Decision.model_json_schema()

result = graph.invoke(Command(resume={"approved": True}), config)
assert result["answer"] == Decision(approved=True)
```

指定类型化模式后，`interrupt()` 返回经过验证的对象：Pydantic 模型实例、`TypedDict` 对应的字典或数据类实例。适用 Pydantic 的验证与类型转换规则。无效输入会抛出 `pydantic.ValidationError`；可以使用同一线程 ID，传入更正后的 `Command(resume=...)` 重试。

也可以将 JSON Schema 字典作为 `response_schema` 传入。LangGraph 原样暴露该字典，但**不会**据此验证恢复值。省略 `response_schema` 时，其值为 `None`，恢复值直接透传，不进行模式验证。

Studio 将中断响应模式渲染为类型化输入字段，而不是 JSON 编辑器。下面的 Studio 组件预览使用包含审批、备注和数值金额字段的示例数据。

![Studio 中断表单，包含审批开关、备注字段以及设为 125.50 的金额字段](https://mintcdn.com/langchain-5e9cc07a/u62GP5wl5NeQqwjE/images/langgraph-interrupt-response-schema.png?fit=max\&auto=format\&n=u62GP5wl5NeQqwjE\&q=85\&s=b10304786d356849862616a60b74aa3d)

## 常见模式

中断最关键的能力是暂停执行并等待外部输入。它适用于多种场景，包括：

* &#x20;[审批工作流](#approve-or-reject)：执行关键操作（API 调用、数据库变更、金融交易）前暂停
* &#x20;[处理多个中断](#handling-multiple-interrupts)：在一次调用中恢复多个中断时，将中断 ID 与恢复值配对
* &#x20;[审核与编辑](#review-and-edit-state)：继续执行前，让人工审核和修改大语言模型输出或工具调用
* &#x20;[中断工具调用](#interrupts-in-tools)：工具调用执行前暂停，以供审核和编辑
* &#x20;[验证人工输入](#validating-human-input)：进入下一步之前暂停，以验证人工输入

### 带人工介入（HITL）中断的流式输出

构建带人工介入工作流的交互式智能体时，可以使用[事件流](https://docs.langchain.com/oss/python/langgraph/event-streaming.md)，在处理中断的同时并发消费消息块和状态快照。

循环使用 `graph.stream_events(..., version="v3")` 返回的类型化投影，直到运行完成：

* 通过 `stream.messages` 逐 token 流式输出 AI 响应
* 通过 `stream.values` 观察每一步的状态快照
* 通过 `stream.interrupted` 检测中断，从 `stream.interrupts` 读取负载
* 使用 `Command(resume=...)` 再次调用 `stream_events` 恢复执行，重复上述过程，直到 `stream.interrupted` 为假

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langgraph.types import Command

stream_input: dict | Command = initial_input

while True:
    stream = graph.stream_events(stream_input, config=config, version="v3")

    # Stream LLM message chunks (including any in subgraphs) as they arrive.
    for message in stream.messages:
        for token in message.text:
            display_streaming_content(token)

    # After the run finishes (or pauses), check for interrupts and resume.
    if not stream.interrupted:
        final_state = stream.output
        break

    interrupt_info = stream.interrupts[0].value
    user_response = get_user_input(interrupt_info)
    stream_input = Command(resume=user_response)
```

> [card] [查看示例追踪](https://smith.langchain.com/public/acab7c09-a2a5-46f3-96fb-15bd36c8df80/r)
>
> 打开此示例的公开 LangSmith 运行记录。

* **`stream.messages`**：以内容块形式返回的聊天模型输出；迭代各个 `message.text` 获取 token 增量。对于嵌套子图，从 `stream.subgraphs[*].messages` 读取消息块。
* **`stream.values`**：每一步后的完整状态快照
* **`stream.interrupted` / `stream.interrupts`**：每次运行后检查图是否暂停，并从 `stream.interrupts` 读取负载
* **`Command(resume=...)`**：作为下一次 `stream_events` 输入以恢复；循环直到运行完成且不再中断

### 处理多个中断

并行分支同时中断时（例如扇出到多个分别调用 `interrupt()` 的节点），可能需要在一次调用中恢复多个中断。
此时，请将每个中断 ID 映射到它对应的恢复值。
这能确保每个响应在运行时与正确的中断配对。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from typing import Annotated, TypedDict
import operator

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    vals: Annotated[list[str], operator.add]


def node_a(state):
    answer = interrupt("question_a")
    return {"vals": [f"a:{answer}"]}


def node_b(state):
    answer = interrupt("question_b")
    return {"vals": [f"b:{answer}"]}


graph = (
    StateGraph(State)
    .add_node("a", node_a)
    .add_node("b", node_b)
    .add_edge(START, "a")
    .add_edge(START, "b")
    .add_edge("a", END)
    .add_edge("b", END)
    .compile(checkpointer=InMemorySaver())
)

config = {"configurable": {"thread_id": "1"}}

# Step 1: stream events to drive the run; both parallel nodes hit interrupt() and pause
stream = graph.stream_events({"vals": []}, config, version="v3")
_ = stream.output  # drive the stream to completion
# stream.interrupts contains the pending Interrupt payloads
print(stream.interrupts)
# > (Interrupt(value='question_a', id='...'), Interrupt(value='question_b', id='...'))

# Step 2: resume all pending interrupts at once
resume_map = {
    i.id: f"answer for {i.value}" for i in stream.interrupts
}
resumed = graph.stream_events(Command(resume=resume_map), config, version="v3")

print("Final state:", resumed.output)
# Final state: {'vals': ['a:answer for question_a', 'b:answer for question_b']}
```

> [card] [查看示例追踪](https://smith.langchain.com/public/abe5fd52-e2d3-41fc-ab1d-c812bc885c3e/r)
>
> 打开此示例的公开 LangSmith 运行记录。

### 批准或拒绝

中断最常见的用途之一是在关键操作前暂停并请求批准。例如，你可能希望请人工批准 API 调用、数据库变更或其他重要决策。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from typing import Literal
from langgraph.types import interrupt, Command

def approval_node(state: State) -> Command[Literal["proceed", "cancel"]]:
    # Pause execution; payload shows up on stream.interrupts (with stream_events) or result["__interrupt__"] (with invoke)
    is_approved = interrupt({
        "question": "Do you want to proceed with this action?",
        "details": state["action_details"]
    })

    # Route based on the response
    if is_approved:
        return Command(goto="proceed")  # Runs after the resume payload is provided
    else:
        return Command(goto="cancel")
```

恢复图时，传入 `True` 表示批准，`False` 表示拒绝：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
# To approve
graph.stream_events(Command(resume=True), config=config, version="v3").output

# To reject
graph.stream_events(Command(resume=False), config=config, version="v3").output
```

> [accordion] 完整示例
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from typing import Literal, Optional, TypedDict
>
> from langgraph.checkpoint.memory import InMemorySaver
> from langgraph.graph import END, START, StateGraph
> from langgraph.types import Command, interrupt
>
>
> class ApprovalState(TypedDict):
>     action_details: str
>     status: Optional[Literal["pending", "approved", "rejected"]]
>
>
> def approval_node(state: ApprovalState) -> Command[Literal["proceed", "cancel"]]:
>     # Expose details so the caller can render them in a UI
>     decision = interrupt(
>         {
>             "question": "Approve this action?",
>             "details": state["action_details"],
>         }
>     )
>
>     # Route to the appropriate node after resume
>     return Command(goto="proceed" if decision else "cancel")
>
>
> def proceed_node(state: ApprovalState):
>     return {"status": "approved"}
>
>
> def cancel_node(state: ApprovalState):
>     return {"status": "rejected"}
>
>
> builder = StateGraph(ApprovalState)
> builder.add_node("approval", approval_node)
> builder.add_node("proceed", proceed_node)
> builder.add_node("cancel", cancel_node)
> builder.add_edge(START, "approval")
> builder.add_edge("proceed", END)
> builder.add_edge("cancel", END)
>
> # Use a more durable checkpointer in production
> checkpointer = InMemorySaver()
> graph = builder.compile(checkpointer=checkpointer)
>
> config = {"configurable": {"thread_id": "approval-123"}}
> initial = graph.stream_events(
>     {"action_details": "Transfer $500", "status": "pending"},
>     config=config,
>     version="v3",
> )
> _ = initial.output  # drive the stream to completion
> print(initial.interrupts)  # -> (Interrupt(value={'question': ..., 'details': ...}),)
>
> # Resume with the decision; True routes to proceed, False to cancel
> resumed = graph.stream_events(Command(resume=True), config=config, version="v3")
> print(resumed.output["status"])
> ```
>
> > [card] [查看示例追踪](https://smith.langchain.com/public/125fbf83-2cf8-4dc7-a148-94f39bc31b8a/r)
> >
> > 打开此示例的公开 LangSmith 运行记录。

### 审核和编辑状态

有时，你希望在继续前让人工审核和编辑部分图状态。这适用于纠正大语言模型、补充缺失信息或进行调整。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langgraph.types import interrupt

def review_node(state: State):
    # Pause and show the current content for review (payload surfaces on stream.interrupts)
    edited_content = interrupt({
        "instruction": "Review and edit this content",
        "content": state["generated_text"]
    })

    # Update the state with the edited version
    return {"generated_text": edited_content}
```

恢复时，提供编辑后的内容：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
graph.stream_events(
    Command(resume="The edited and improved text"),  # Value becomes the return from interrupt()
    config=config,
    version="v3",
).output
```

> [accordion] 完整示例
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from typing import TypedDict
>
> from langgraph.checkpoint.memory import MemorySaver
> from langgraph.graph import END, START, StateGraph
> from langgraph.types import Command, interrupt
>
>
> class ReviewState(TypedDict):
>     generated_text: str
>
>
> def review_node(state: ReviewState):
>     # Ask a reviewer to edit the generated content
>     updated = interrupt(
>         {
>             "instruction": "Review and edit this content",
>             "content": state["generated_text"],
>         }
>     )
>     return {"generated_text": updated}
>
>
> builder = StateGraph(ReviewState)
> builder.add_node("review", review_node)
> builder.add_edge(START, "review")
> builder.add_edge("review", END)
>
> checkpointer = MemorySaver()
> graph = builder.compile(checkpointer=checkpointer)
>
> config = {"configurable": {"thread_id": "review-42"}}
> initial = graph.stream_events(
>     {"generated_text": "Initial draft"}, config=config, version="v3"
> )
> _ = initial.output  # drive the stream to completion
> print(initial.interrupts)  # -> (Interrupt(value={'instruction': ..., 'content': ...}),)
>
> # Resume with the edited text from the reviewer
> final_state = graph.stream_events(
>     Command(resume="Improved draft after review"),
>     config=config,
>     version="v3",
> )
> print(final_state.output["generated_text"])  # -> "Improved draft after review"
> ```
>
> > [card] [查看示例追踪](https://smith.langchain.com/public/0698f1a4-d39f-459b-be4c-1d189f830d06/r)
> >
> > 打开此示例的公开 LangSmith 运行记录。

### 工具中的中断

也可以直接在工具函数内放置中断。这样，工具每次被调用时都会暂停等待批准，并允许在实际执行前人工审核和编辑工具调用。

首先，定义一个使用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 的工具：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool
from langgraph.types import interrupt

@tool
def send_email(to: str, subject: str, body: str):
    """Send an email to a recipient."""

    # Pause before sending; payload surfaces on stream.interrupts when using event streaming
    response = interrupt({
        "action": "send_email",
        "to": to,
        "subject": subject,
        "body": body,
        "message": "Approve sending this email?"
    })

    if response.get("action") == "approve":
        # Resume value can override inputs before executing
        final_to = response.get("to", to)
        final_subject = response.get("subject", subject)
        final_body = response.get("body", body)
        return f"Email sent to {final_to} with subject '{final_subject}'"
    return "Email cancelled by user"
```

当你希望将审批逻辑与工具本身放在一起，使其能在图的不同位置复用时，这种方式很有用。大语言模型可以正常调用工具，每次调用都会因中断而暂停执行，让你批准、编辑或取消操作。

> [accordion] 完整示例
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import sqlite3
> import operator
> from typing import TypedDict, Annotated, Literal
> from langchain.tools import tool
> from langchain_anthropic import ChatAnthropic
> from langgraph.checkpoint.sqlite import SqliteSaver
> from langgraph.graph import StateGraph, START, END
> from langgraph.types import Command, interrupt
> from langchain.messages import AnyMessage, SystemMessage, ToolMessage
>
>
> class AgentState(TypedDict):
>     messages: Annotated[list[AnyMessage], operator.add]
>
>
> @tool
> def send_email(to: str, subject: str, body: str):
>     """Send an email to a recipient."""
>
>     # Pause before sending; payload surfaces on stream.interrupts when using event streaming
>     response = interrupt({
>         "action": "send_email",
>         "to": to,
>         "subject": subject,
>         "body": body,
>         "message": "Approve sending this email?",
>     })
>
>     if response.get("action") == "approve":
>         final_to = response.get("to", to)
>         final_subject = response.get("subject", subject)
>         final_body = response.get("body", body)
>
>         # Actually send the email (your implementation here)
>         print(f"[send_email] to={final_to} subject={final_subject} body={final_body}")
>         return f"Email sent to {final_to}"
>
>     return "Email cancelled by user"
>
>
> model = ChatAnthropic(model="claude-sonnet-4-6").bind_tools([send_email])
> tools_by_name = {"send_email": send_email}
>
>
> def agent_node(state: AgentState):
>     # LLM may decide to call the tool; interrupt pauses before sending
>     result = model.invoke(state["messages"])
>     return {"messages": [result]}
>
> def tool_node(state: AgentState):
>     """Performs the tool call"""
>     result = []
>     for tool_call in state["messages"][-1].tool_calls:
>         tool = tools_by_name[tool_call["name"]]
>         observation = tool.invoke(tool_call["args"])
>         result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
>     return {"messages": result}
>
> def should_continue(state: AgentState) -> Literal["tool_node", END]:
>     """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
>     messages = state["messages"]
>     last_message = messages[-1]
>
>     if last_message.tool_calls:
>         return "tool_node"
>     return END
>
> builder = StateGraph(AgentState)
> builder.add_node("agent", agent_node)
> builder.add_node("tool_node", tool_node)
>
> builder.add_edge(START, "agent")
> builder.add_conditional_edges("agent", should_continue, ["tool_node", END])  # Routes to "tools" or END
> builder.add_edge("tool_node", "agent")  # Loop back after tools
>
> checkpointer = SqliteSaver(
>     sqlite3.connect("tool-approval.db", check_same_thread=False)
> )
> graph = builder.compile(checkpointer=checkpointer)
>
> config = {"configurable": {"thread_id": "email-workflow"}}
> initial = graph.stream_events(
>     {
>         "messages": [
>             {"role": "user", "content": "Send an email to alice@example.com about the meeting"}
>         ]
>     },
>     config=config,
>     version="v3",
> )
> initial.output  # drive the stream to completion
> print(initial.interrupts)  # -> (Interrupt(value={'action': 'send_email', ...}),)
>
> # Resume with approval and optionally edited arguments
> resumed = graph.stream_events(
>     Command(resume={"action": "approve", "subject": "Updated subject"}),
>     config=config,
>     version="v3",
> )
> print(resumed.output["messages"][-1])  # -> Tool result returned by send_email
> ```

### 验证人工输入

有时需要验证人工输入，并在无效时重新提问。推荐方式是：**每次节点调用只调用一次** `interrupt()`，将错误消息存入状态后从节点返回，再使用**条件边**循环返回该节点，直到获得有效值。

> [!WARNING]
>
> **避免在单个节点内部使用 `while True` + `interrupt()` 循环。**由于每次恢复都会从节点开头重新运行（见[中断规则](#rules-of-interrupts)），一个多次调用 `interrupt()` 的循环会让每次恢复都重放所有此前的迭代：第一次恢复重放 1 次迭代，第二次重放 2 次，依此类推。

正确的模式：

1. 将重新提问的问题保存在状态中（例如 `pending_question`）。
2. 在节点中**恰好调用一次** `interrupt()`，传入状态中的当前问题。
3. 若回答无效，返回更新后的 `pending_question`，使下一次调用重新提问。
4. 使用 `add_conditional_edges` 路由回该节点，直到收集到有效值。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class FormState(TypedDict):
    age: int | None
    pending_question: str | None


def get_age_node(state: FormState):
    question = state.get("pending_question") or "What is your age?"
    answer = interrupt(question)  # called exactly once per invocation
    if isinstance(answer, int) and answer > 0:
        return {"age": answer, "pending_question": None}
    return {"pending_question": f"'{answer}' is not a valid age. Please enter a positive number."}


def route(state: FormState):
    return END if state.get("age") is not None else "collect_age"


builder = StateGraph(FormState)
builder.add_node("collect_age", get_age_node)
builder.add_edge(START, "collect_age")
builder.add_conditional_edges("collect_age", route)
```

在此示例中，无效回答使节点返回更新后的问题。在同一次图运行中，条件边会再次调用该节点，这次新调用在 `interrupt()` 处暂停。稍后恢复时，节点仍从开头重新运行，因此 `interrupt()` 之前的代码会再次执行。参见[中断规则](#rules-of-interrupts)。

> [accordion] 完整示例
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from typing import TypedDict
>
> from langgraph.checkpoint.memory import InMemorySaver
> from langgraph.graph import END, START, StateGraph
> from langgraph.types import Command, interrupt
>
>
> class FormState(TypedDict):
>     age: int | None
>     pending_question: str | None
>
>
> def get_age_node(state: FormState):
>     question = state.get("pending_question") or "What is your age?"
>     answer = interrupt(question)  # called exactly once per node invocation
>     print(f"I got {answer}")  # runs exactly once per resume
>     if isinstance(answer, int) and answer > 0:
>         return {"age": answer, "pending_question": None}
>     return {"pending_question": f"'{answer}' is not a valid age. Please enter a positive number."}
>
>
> def route(state: FormState):
>     # Loop back to collect_age until we have a valid age
>     return END if state.get("age") is not None else "collect_age"
>
>
> builder = StateGraph(FormState)
> builder.add_node("collect_age", get_age_node)
> builder.add_edge(START, "collect_age")
> builder.add_conditional_edges("collect_age", route)
>
> checkpointer = InMemorySaver()
> graph = builder.compile(checkpointer=checkpointer)
>
> config = {"configurable": {"thread_id": "form-1"}}
> first = graph.stream_events({"age": None, "pending_question": None}, config=config, version="v3")
> _ = first.output  # drive the stream to completion
> print(first.interrupts)  # -> (Interrupt(value='What is your age?', ...),)
>
> # Provide invalid data; the node re-prompts via the conditional edge
> retry = graph.stream_events(Command(resume="thirty"), config=config, version="v3")
> _ = retry.output
> print(retry.interrupts)  # -> (Interrupt(value="'thirty' is not a valid age...", ...),)
>
> # Provide valid data; route() returns END and the graph finishes
> final = graph.stream_events(Command(resume=30), config=config, version="v3")
> print(final.output["age"])  # -> 30
> ```

## 中断规则

在节点中调用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 时，LangGraph 通过抛出异常挂起执行，通知运行时暂停。该异常沿调用栈向上传播，由运行时捕获；运行时随后通知图保存当前状态并等待外部输入。

恢复执行时（即提供所需输入后），运行时会从头重新启动整个节点，而不是从调用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 的精确代码行继续。因此，所有在 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 之前运行的代码都会再次执行。为确保中断按预期工作，需要遵循以下重要规则。

### 不要用 try/except 包裹 `interrupt` 调用

[`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 通过抛出特殊异常在调用点暂停执行。如果将 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 放进 try/except 块，就会捕获这个异常，中断将无法传回图。

* ✅ 将 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 调用与容易出错的代码分开
* ✅ 在 try/except 块中使用特定的异常类型

```python Separating logic theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ✅ Good: interrupting first, then handling
    # error conditions separately
    interrupt("What's your name?")
    try:
        fetch_data()  # This can fail
    except Exception as e:
        print(e)
    return state
```

```python Explicit exception handling theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ✅ Good: catching specific exception types
    # will not catch the interrupt exception
    try:
        name = interrupt("What's your name?")
        fetch_data()  # This can fail
    except NetworkException as e:
        print(e)
    return state
```

* 🔴 不要用未指定异常类型的 try/except 块包裹 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 调用

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ❌ Bad: wrapping interrupt in bare try/except
    # will catch the interrupt exception
    try:
        interrupt("What's your name?")
    except Exception as e:
        print(e)
    return state
```

### 不要重新排列节点内的 `interrupt` 调用

单个节点中使用多个中断很常见，但如果处理不慎，可能导致意外行为。

节点包含多个中断调用时，LangGraph 会为执行该节点的任务维护一份专属恢复值列表。每次恢复都从节点开头开始。遇到每个中断时，LangGraph 检查任务的恢复列表中是否存在匹配值。匹配**严格基于索引**，因此节点内中断调用的顺序十分重要。

* ✅ 在各次节点执行之间保持 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 调用一致

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ✅ Good: interrupt calls happen in the same order every time
    name = interrupt("What's your name?")
    age = interrupt("What's your age?")
    city = interrupt("What's your city?")

    return {
        "name": name,
        "age": age,
        "city": city
    }
```

* 🔴 不要在节点中有条件地跳过 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 调用
* 🔴 不要用各次执行之间不确定的逻辑循环调用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt)，包括 `while True` 验证循环。请改用条件边（见[验证人工输入](#validating-human-input)）

```python Skipping interrupts theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ❌ Bad: conditionally skipping interrupts changes the order
    name = interrupt("What's your name?")

    # On first run, this might skip the interrupt
    # On resume, it might not skip it - causing index mismatch
    if state.get("needs_age"):
        age = interrupt("What's your age?")

    city = interrupt("What's your city?")

    return {"name": name, "city": city}
```

```python Looping interrupts theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ❌ Bad: looping based on non-deterministic data
    # The number of interrupts changes between executions
    results = []
    for item in state.get("dynamic_list", []):  # List might change between runs
        result = interrupt(f"Approve {item}?")
        results.append(result)

    return {"results": results}
```

### 不要在 `interrupt` 调用中返回复杂值

复杂值是否可以序列化取决于所用检查点保存器（例如函数就无法序列化）。为使图适应任何部署方式，最佳实践是只使用能够合理序列化的值。

* ✅ 向 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 传入简单的可 JSON 序列化类型
* ✅ 传入包含简单值的字典／对象

```python Simple values theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ✅ Good: passing simple types that are serializable
    name = interrupt("What's your name?")
    count = interrupt(42)
    approved = interrupt(True)

    return {"name": name, "count": count, "approved": approved}
```

```python Structured data theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ✅ Good: passing dictionaries with simple values
    response = interrupt({
        "question": "Enter user details",
        "fields": ["name", "email", "age"],
        "current_values": state.get("user", {})
    })

    return {"user": response}
```

* 🔴 不要向 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 传入函数、类实例或其他复杂对象

```python Functions theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def validate_input(value):
    return len(value) > 0

def node_a(state: State):
    # ❌ Bad: passing a function to interrupt
    # The function cannot be serialized
    response = interrupt({
        "question": "What's your name?",
        "validator": validate_input  # This will fail
    })
    return {"name": response}
```

```python Class instances theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
class DataProcessor:
    def __init__(self, config):
        self.config = config

def node_a(state: State):
    processor = DataProcessor({"mode": "strict"})

    # ❌ Bad: passing a class instance to interrupt
    # The instance cannot be serialized
    response = interrupt({
        "question": "Enter data to process",
        "processor": processor  # This will fail
    })
    return {"result": response}
```

### `interrupt` 之前执行的副作用必须幂等

由于中断通过重新运行所在节点实现，理想情况下，所有在 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 之前执行的副作用都应是幂等的。幂等意味着同一操作重复执行多次，结果不会超出首次执行带来的变化。

例如，节点中可能有一个更新记录的 API 调用。如果在该调用之后调用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt)，节点每次恢复时该 API 都会重复运行，可能覆盖最初更新或创建重复记录。

* ✅ 在 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 前使用幂等操作
* ✅ 将副作用放在 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 之后
* ✅ 尽可能将副作用放入独立节点

在下方“批准后执行”的示例中，只有审批通过才运行副作用。如果节点在副作用已提交后、完成之前失败，重试节点仍可能重复该副作用。请使用幂等操作，或在外部系统中对写入进行去重。

```python Idempotent operations theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ✅ Good: using upsert operation which is idempotent
    # Running this multiple times will have the same result
    db.upsert_user(
        user_id=state["user_id"],
        status="pending_approval"
    )

    approved = interrupt("Approve this change?")

    return {"approved": approved}
```

```python Side effects after interrupt theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ✅ Good: placing side effect after the interrupt
    # Approval gates this side effect; retries still need idempotency
    approved = interrupt("Approve this change?")

    if approved:
        db.create_audit_log(
            user_id=state["user_id"],
            action="approved"
        )

    return {"approved": approved}
```

```python Separating into different nodes theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def approval_node(state: State):
    # ✅ Good: only handling the interrupt in this node
    approved = interrupt("Approve this change?")

    return {"approved": approved}

def notification_node(state: State):
    # ✅ Good: side effect happens in a separate node
    # Approval gates this side effect; retries still need idempotency
    if (state.approved):
        send_notification(
            user_id=state["user_id"],
            status="approved"
        )

    return state
```

* 🔴 不要在 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 之前执行非幂等操作
* 🔴 不要在未检查记录是否存在的情况下创建新记录

```python Creating records theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ❌ Bad: creating a new record before interrupt
    # This will create duplicate records on each resume
    audit_id = db.create_audit_log({
        "user_id": state["user_id"],
        "action": "pending_approval",
        "timestamp": datetime.now()
    })

    approved = interrupt("Approve this change?")

    return {"approved": approved, "audit_id": audit_id}
```

```python Appending to lists theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_a(state: State):
    # ❌ Bad: appending to a list before interrupt
    # This will add duplicate entries on each resume
    db.append_to_history(state["user_id"], "approval_requested")

    approved = interrupt("Approve this change?")

    return {"approved": approved}
```

## 与作为函数调用的子图一起使用

在节点中调用子图时，如果子图触发 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt)，父图会从调用子图的**节点开头**恢复执行。同样，**子图**也会从调用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 的节点开头恢复。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
def node_in_parent_graph(state: State):
    some_code()  # <-- This will re-execute when resumed
    # Invoke a subgraph as a function.
    # The subgraph contains an `interrupt` call.
    subgraph_result = subgraph.invoke(some_input)
    # ...

def node_in_subgraph(state: State):
    some_other_code()  # <-- This will also re-execute when resumed
    result = interrupt("What's your name?")
    # ...
```

## 使用中断调试

为调试和测试图，可以将静态中断作为断点，逐个节点单步执行。静态中断在节点执行前或执行后的指定位置触发。可以在编译图时通过 `interrupt_before` 和 `interrupt_after` 设置。

> [!NOTE]
>
> **不推荐**将静态中断用于人工介入工作流。请改用 [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) 函数。

> [tab] 编译时
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> graph = builder.compile(
>     interrupt_before=["node_a"],  # [!code highlight]
>     interrupt_after=["node_b", "node_c"],  # [!code highlight]
>     checkpointer=checkpointer,
> )
>
> # Pass a thread ID to the graph
> config = {
>     "configurable": {
>         "thread_id": "some_thread"
>     }
> }
>
> # Run the graph until the breakpoint
> graph.invoke(inputs, config=config)  # [!code highlight]
>
> # Resume the graph
> graph.invoke(None, config=config)  # [!code highlight]
> ```
>
> 1. 在 `compile` 阶段设置断点。
> 2. `interrupt_before` 指定在节点执行之前暂停的位置。
> 3. `interrupt_after` 指定在节点执行之后暂停的位置。
> 4. 启用断点需要检查点保存器。
> 5. 图运行直到命中第一个断点。
> 6. 将输入设为 `None` 即可恢复图；图会继续运行直到下一个断点。

> [tab] 运行时
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> config = {
>     "configurable": {
>         "thread_id": "some_thread"
>     }
> }
>
> # Run the graph until the breakpoint
> graph.invoke(
>     inputs,
>     interrupt_before=["node_a"],  # [!code highlight]
>     interrupt_after=["node_b", "node_c"],  # [!code highlight]
>     config=config,
> )
>
> # Resume the graph
> graph.invoke(None, config=config)  # [!code highlight]
> ```
>
> 1. 调用 `graph.invoke` 时传入 `interrupt_before` 和 `interrupt_after` 参数。这属于运行时配置，每次调用都可以更改。
> 2. `interrupt_before` 指定在节点执行之前暂停的位置。
> 3. `interrupt_after` 指定在节点执行之后暂停的位置。
> 4. 图运行直到命中第一个断点。
> 5. 将输入设为 `None` 即可恢复图；图会继续运行直到下一个断点。

> [!TIP]
>
> 要调试中断，请使用 [LangSmith](https://docs.langchain.com/langsmith/observability.md)。

### 使用 LangSmith Studio

可以在运行图之前，通过 [LangSmith Studio](https://docs.langchain.com/langsmith/studio.md) 的界面为图设置静态中断。也可以使用界面检查执行中任意位置的图状态。

![静态中断界面示意图](https://mintcdn.com/langchain-5e9cc07a/dL5Sn6Cmy9pwtY0V/oss/images/static-interrupt.png?fit=max\&auto=format\&n=dL5Sn6Cmy9pwtY0V\&q=85\&s=5aa4e7cea2ab147cef5b4e210dd6c4a1)

***

[连接这些文档](https://docs.langchain.com/use-these-docs.md) ，通过 MCP 将其接入你选择的智能体，以获取实时答案。

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/langgraph/interrupts.mdx) 或[提交问题](https://github.com/langchain-ai/docs/issues/new/choose).
