<!--
Source-URL: https://docs.langchain.com/oss/python/langchain/tools.md
HTML-URL: https://docs.langchain.com/oss/python/langchain/tools
Downloaded: 2026-11-16 19:21:15 Asia/Shanghai
Original-Language: English
-->

> ## 文档索引
> 完整文档索引：https://docs.langchain.com/llms.txt
> 在进一步阅读之前，可使用此文件发现所有可用页面。

# 工具

> 定义工具，让 LangChain 智能体能够获取实时数据、执行代码、查询外部数据库并采取行动。

工具扩展了[智能体](https://docs.langchain.com/oss/python/langchain/agents.md)的能力，让它们能够获取实时数据、执行代码、查询外部数据库，并在现实世界中采取行动。

从底层看，工具是输入和输出定义明确的可调用函数，它们会被传给[聊天模型](https://docs.langchain.com/oss/python/langchain/models.md)。模型根据对话上下文决定何时调用工具，以及提供哪些输入参数。

> [!TIP]
>
> 关于模型如何处理工具调用，参见[工具调用](https://docs.langchain.com/oss/python/langchain/models.md#tool-calling)。使用 [LangSmith](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-langchain-tools) 追踪工具调用并调试错误。按照[追踪快速入门](https://docs.langchain.com/langsmith/trace-with-langchain.md)完成设置。
>
> 我们还建议设置 [LangSmith Engine](https://docs.langchain.com/langsmith/engine.md)，它会监控追踪记录、发现问题并提出修复建议。

## 创建工具

### 基本工具定义

创建工具最简单的方法是使用 [`@tool`](https://reference.langchain.com/python/langchain-core/tools/convert/tool) 装饰器。默认情况下，函数的文档字符串会成为工具说明，帮助模型理解何时使用它：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    return f"Found {limit} results for '{query}'"
```

类型提示是**必需的**，因为它定义工具的输入模式。文档字符串应信息充分且简洁，帮助模型理解工具用途。

> [!NOTE]
>
> **服务端工具使用：**一些聊天模型提供在服务端执行的内置工具（网页搜索、代码解释器）。详情见[服务端工具使用](#server-side-tool-use)。

> [!WARNING]
>
> 工具名称优先使用 `snake_case`（例如用 `web_search` 而非 `Web Search`）。一些模型提供商无法正确处理含空格或特殊字符的名称，或会报错并拒绝它们。只使用字母、数字、下划线和连字符，有助于提高不同提供商之间的兼容性。

### 自定义工具属性

#### 自定义工具名称

默认工具名称来自函数名。如果需要更具描述性的名称，可以覆盖它：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
@tool("web_search")  # Custom name
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

print(search.name)  # web_search
```

#### 自定义工具说明

覆盖自动生成的工具说明，更清晰地引导模型：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
@tool("calculator", description="Performs arithmetic calculations. Use this for any math problems.")
def calc(expression: str) -> str:
    """Evaluate mathematical expressions."""
    return str(eval(expression))
```

### 高级模式定义

使用 Pydantic 模型或 JSON 模式定义复杂输入：

```python Pydantic model theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from pydantic import BaseModel, Field
from typing import Literal

class WeatherInput(BaseModel):
    """Input for weather queries."""
    location: str = Field(description="City name or coordinates")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="Temperature unit preference"
    )
    include_forecast: bool = Field(
        default=False,
        description="Include 5-day forecast"
    )

@tool(args_schema=WeatherInput)
def get_weather(location: str, units: str = "celsius", include_forecast: bool = False) -> str:
    """Get current weather and optional forecast."""
    temp = 22 if units == "celsius" else 72
    result = f"Current weather in {location}: {temp} degrees {units[0].upper()}"
    if include_forecast:
        result += "\nNext 5 days: Sunny"
    return result
```

```python JSON Schema theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
weather_schema = {
    "type": "object",
    "properties": {
        "location": {"type": "string"},
        "units": {"type": "string"},
        "include_forecast": {"type": "boolean"}
    },
    "required": ["location", "units", "include_forecast"]
}

@tool(args_schema=weather_schema)
def get_weather(location: str, units: str = "celsius", include_forecast: bool = False) -> str:
    """Get current weather and optional forecast."""
    temp = 22 if units == "celsius" else 72
    result = f"Current weather in {location}: {temp} degrees {units[0].upper()}"
    if include_forecast:
        result += "\nNext 5 days: Sunny"
    return result
```

### 保留的参数名称

以下参数名称为保留名称，不能用作工具参数。使用这些名称会导致运行时错误。

| 参数名称 | 用途 |
| - | - |
| `config` | 保留用于在内部向工具传递 `RunnableConfig` |
| `runtime` | 保留用于 `ToolRuntime` 参数（访问状态、上下文和存储） |

要访问运行时信息，应使用 [`ToolRuntime`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.ToolRuntime) 参数，不要将自己的参数命名为 `config` 或 `runtime`。

如果你使用 `InjectedState`、`InjectedStore`、`get_runtime()` 或 `InjectedToolCallId`，参见[从旧注入模式迁移](#migrate-from-older-injection-patterns)。

## 访问上下文

当工具能够访问对话历史、用户数据、持久记忆等运行时信息时，其能力最强。本节介绍如何在工具内部访问和更新这些信息。

工具可通过 [`ToolRuntime`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.ToolRuntime) 参数访问运行时信息，它提供：

| 组件 | 说明 | 使用场景 |
| - | - | - |
| **状态** | 短期记忆——存在于当前对话中的可变数据（消息、计数器、自定义字段） | 访问对话历史、追踪工具调用次数 |
| **上下文** | 调用时传入的不可变配置（用户 ID、会话信息） | 根据用户身份个性化响应 |
| **存储** | 长期记忆——跨对话保留的持久数据 | 保存用户偏好、维护知识库 |
| **流写入器** | 在工具执行期间发出实时更新 | 显示长时间操作的进度 |
| **执行信息** | 当前执行的身份与重试信息（线程 ID、运行 ID、尝试次数） | 访问线程／运行 ID、根据重试状态调整行为 |
| **服务器信息** | 在 LangSmith Agent Server 上运行时的服务器专属元数据（助手 ID、图 ID、已认证用户） | 访问助手 ID、图 ID 或已认证用户信息 |
| **配置** | 当前执行的 [`RunnableConfig`](https://reference.langchain.com/python/langchain-core/runnables/config/RunnableConfig) | 访问回调、标签和元数据 |
| **工具调用 ID** | 当前工具调用的唯一标识符 | 关联日志和模型调用中的工具调用 |

```mermaid theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
graph LR
    %% Runtime Context
    subgraph "🔧 Tool Runtime Context"
        A[Tool Call] --> B[ToolRuntime]
        B --> C[State Access]
        B --> D[Context Access]
        B --> E[Store Access]
        B --> F[Stream Writer]
    end

    %% Available Resources
    subgraph "📊 Available Resources"
        C --> G[Messages]
        C --> H[Custom State]
        D --> I[User ID]
        D --> J[Session Info]
        E --> K[Long-term Memory]
        E --> L[User Preferences]
    end

    %% Tool Capabilities
    subgraph "⚡ Enhanced Tool Capabilities"
        M[Context-Aware Tools]
        N[Stateful Tools]
        O[Memory-Enabled Tools]
        P[Streaming Tools]
    end

    %% Connections
    G --> M
    H --> N
    I --> M
    J --> M
    K --> O
    L --> O
    F --> P

    classDef trigger fill:#F6FFDB,stroke:#6E8900,stroke-width:2px,color:#2E3900
    classDef process fill:#E5F4FF,stroke:#006DDD,stroke-width:2px,color:#030710
    classDef output fill:#EBD0F0,stroke:#885270,stroke-width:2px,color:#441E33
    classDef neutral fill:#F2FAFF,stroke:#40668D,stroke-width:2px,color:#2F4B68

    class A trigger
    class B,C,D,E,F process
    class G,H,I,J,K,L neutral
    class M,N,O,P output
```

### 短期记忆（状态）

状态表示在一次对话期间存在的短期记忆。它包括消息历史，以及你在[图状态](https://docs.langchain.com/oss/python/langgraph/graph-api.md#state)中定义的任意自定义字段。

#### 访问状态

在工具签名中添加 `runtime: ToolRuntime` 以访问状态。调用时，[`ToolNode`](https://reference.langchain.com/python/langgraph/agents/#langgraph.prebuilt.tool_node.ToolNode) 自动注入该值；发送给模型的工具模式中不包含此参数。通过 `runtime.state` 读取当前对话状态：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool, ToolRuntime
from langchain.messages import HumanMessage

@tool
def get_last_user_message(runtime: ToolRuntime) -> str:
    """Get the most recent message from the user."""
    messages = runtime.state["messages"]

    # Find the last human message
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.content

    return "No user messages found"

# Access custom state fields
@tool
def get_user_preference(
    pref_name: str,
    runtime: ToolRuntime
) -> str:
    """Get a user preference value."""
    preferences = runtime.state.get("user_preferences", {})
    return preferences.get(pref_name, "Not set")
```

> [!WARNING]
>
> `runtime` 参数对模型隐藏。在上方示例中，模型只能在工具模式中看到 `pref_name`。

#### 更新状态

使用 [`Command`](https://reference.langchain.com/python/langgraph/types/Command) 更新智能体状态。这适用于需要更新自定义状态字段的工具。
在更新中包含一条 `ToolMessage`，以便模型看到工具调用结果：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.agents import AgentState
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command


class CustomState(AgentState):
    user_name: str


@tool
def set_user_name(new_name: str, runtime: ToolRuntime[None, CustomState]) -> Command:
    """Set the user's name in the conversation state."""
    return Command(
        update={
            "user_name": new_name,
            "messages": [
                ToolMessage(
                    content=f"User name set to {new_name}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
```

> [card] [查看示例追踪](https://smith.langchain.com/public/d29da0cb-a0f6-4a14-b976-9f4154e46c4c/r)
>
> 打开此示例的公开 LangSmith 运行记录。

> [!TIP]
>
> 工具更新状态变量时，考虑为这些字段定义[归约函数](https://docs.langchain.com/oss/python/langgraph/graph-api.md#reducers)。由于大语言模型可以并行调用多个工具，归约函数决定并发工具调用更新同一状态字段时如何解决冲突。

### 上下文

上下文提供调用时传入的不可变配置数据。可用于用户 ID、会话详细信息，或在对话期间不应改变的应用专属设置。

> [!NOTE]
>
> `thread_id`（通过 `config={"configurable": {"thread_id": ...}}` 传入）确定*对话*的范围，即消息历史和检查点；`context` 则承载工具和中间件在调用时读取的*每次运行专属*数据。持久化需要[检查点保存器](https://docs.langchain.com/oss/python/langchain/short-term-memory.md)。生产环境通常为每次对话使用稳定的 `thread_id`，并在每次 invoke 时传入 `context` 对象。

通过 `runtime.context` 访问上下文。配置[检查点保存器](https://docs.langchain.com/oss/python/langchain/short-term-memory.md)，并在传入 `context` 时使用稳定的 `thread_id`，使对话在多次调用之间持久保留：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain_core.utils.uuid import uuid7
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver


USER_DATABASE = {
    "user123": {
        "name": "Alice Johnson",
        "account_type": "Premium",
        "balance": 5000,
        "email": "alice@example.com",
    },
    "user456": {
        "name": "Bob Smith",
        "account_type": "Standard",
        "balance": 1200,
        "email": "bob@example.com",
    },
}


@dataclass
class UserContext:
    user_id: str


@tool
def get_account_info(runtime: ToolRuntime[UserContext]) -> str:
    """Get the current user's account information."""
    user_id = runtime.context.user_id

    if user_id in USER_DATABASE:
        user = USER_DATABASE[user_id]
        return (
            f"Account holder: {user['name']}\n"
            f"Type: {user['account_type']}\n"
            f"Balance: ${user['balance']}"
        )
    return "User not found"


model = ChatOpenAI(model="gpt-6.1-sol")
agent = create_agent(
    model,
    tools=[get_account_info],
    context_schema=UserContext,
    checkpointer=InMemorySaver(),
    system_prompt="You are a financial assistant.",
)

thread_id = str(uuid7())
config = {"configurable": {"thread_id": thread_id}}
context = UserContext(user_id="user123")

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's my current balance?"}]},
    config=config,
    context=context,
)
print(result["messages"][-1].content_blocks)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What was my balance again?"}]},
    config=config,
    context=context,
)
print(result["messages"][-1].content_blocks)
```

> [card] [查看示例追踪](https://smith.langchain.com/public/71fda0a0-84cc-4eb8-83a1-611ebbd675a5/r)
>
> 打开此示例的公开 LangSmith 运行记录。

### 长期记忆（存储）

[`BaseStore`](https://reference.langchain.com/python/langchain-core/stores/BaseStore) 提供跨对话保留的持久存储。与状态（短期记忆）不同，保存到存储的数据在之后的会话中仍然可用。

通过 `runtime.store` 访问存储。存储使用命名空间／键的模式组织数据：

> [!TIP]
>
> 生产部署应使用 [`PostgresStore`](https://reference.langchain.com/python/langgraph/store/#langgraph.store.postgres.PostgresStore)、`MongoDBStore` 或 `RedisStore` 等持久存储实现，而不是 `InMemoryStore`。配置详情见[记忆文档](https://docs.langchain.com/oss/python/langgraph/add-memory.md)。

```python expandable theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langgraph.store.memory import InMemoryStore
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain_openai import ChatOpenAI

# Access memory
@tool
def get_user_info(user_id: str, runtime: ToolRuntime) -> str:
    """Look up user info."""
    store = runtime.store
    user_info = store.get(("users",), user_id)
    return str(user_info.value) if user_info else "Unknown user"

# Update memory
@tool
def save_user_info(user_id: str, name: str, age: int, email: str, runtime: ToolRuntime) -> str:
    """Save user info."""
    store = runtime.store
    store.put(("users",), user_id, {"name": name, "age": age, "email": email})
    return "Successfully saved user info."

model = ChatOpenAI(model="gpt-6.1-sol")

store = InMemoryStore()
agent = create_agent(
    model,
    tools=[get_user_info, save_user_info],
    store=store
)

# First session: save user info
agent.invoke({
    "messages": [{"role": "user", "content": "Save the following user: userid: abc123, name: Foo, age: 25, email: foo@langchain.dev"}]
})

# Second session: get user info
agent.invoke({
    "messages": [{"role": "user", "content": "Get user info for user with id 'abc123'"}]
})
# Here is the user info for user with ID "abc123":
# - Name: Foo
# - Age: 25
# - Email: foo@langchain.dev
```

### 流写入器

在工具执行期间流式发送实时更新。这适用于在长时间操作期间向用户提供进度反馈。

使用 `runtime.stream_writer` 发出自定义更新：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool, ToolRuntime

@tool
def get_weather(city: str, runtime: ToolRuntime) -> str:
    """Get weather for a given city."""
    writer = runtime.stream_writer

    # Stream custom updates as the tool executes
    writer(f"Looking up data for city: {city}")
    writer(f"Acquired data for city: {city}")

    return f"It's always sunny in {city}!"
```

> [!NOTE]
>
> 如果在工具内部使用 `runtime.stream_writer`，该工具必须在 LangGraph 执行上下文中调用。更多详情参见[流式输出](https://docs.langchain.com/oss/python/langchain/streaming.md)。

### 执行信息

在工具中通过 `runtime.execution_info` 访问线程 ID、运行 ID 和重试状态：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool, ToolRuntime

@tool
def log_execution_context(runtime: ToolRuntime) -> str:
    """Log execution identity information."""
    info = runtime.execution_info
    print(f"Thread: {info.thread_id}, Run: {info.run_id}")  # [!code highlight]
    print(f"Attempt: {info.node_attempt}")
    return "done"
```

> [!NOTE]
>
> 需要 `deepagents>=0.5.0`（或 `langgraph>=1.1.5`）。

### 服务器信息

工具在 Agent Server 上运行时，通过 `runtime.server_info` 访问助手 ID、图 ID 和已认证用户：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool, ToolRuntime

@tool
def get_assistant_scoped_data(runtime: ToolRuntime) -> str:
    """Fetch data scoped to the current assistant."""
    server = runtime.server_info
    if server is not None:
        print(f"Assistant: {server.assistant_id}, Graph: {server.graph_id}")  # [!code highlight]
        if server.user is not None:
            print(f"User: {server.user.identity}")  # [!code highlight]
    return "done"
```

当工具不在 Agent Server 上运行时（例如本地开发或测试），`server_info` 为 `None`。

> [!NOTE]
>
> 需要 `deepagents>=0.5.0`（或 `langgraph>=1.1.5`）。

> [accordion] 从旧注入模式迁移
>
> 较早的示例使用 `InjectedState`、`InjectedStore`、`get_runtime()` 或 `InjectedToolCallId`。请改用 [`ToolRuntime`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.ToolRuntime)，通过一个显式接口统一访问状态、上下文、存储和执行元数据。
>
> #### 旧模式
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from langchain.tools import tool, InjectedState
>
> @tool
> def summarize(state: InjectedState) -> str:
>     """Summarize the conversation."""
>     messages = state["messages"]
>     return f"Conversation length: {len(messages)} messages."
> ```
>
> #### 推荐模式
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from langchain.tools import tool, ToolRuntime
>
> @tool
> def summarize(runtime: ToolRuntime) -> str:
>     """Summarize the conversation."""
>     messages = runtime.state["messages"]
>     return f"Conversation length: {len(messages)} messages."
> ```
>
> 智能体级迁移（例如 `create_react_agent` 和自定义状态）参见 [LangChain v1 迁移指南](https://docs.langchain.com/oss/python/migrate/langchain-v1.md)。

## 工具执行

在 LangChain 中，工具由智能体使用（例如通过 [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_agent)），工具错误处理通过[中间件](https://docs.langchain.com/oss/python/langchain/middleware.md)配置。

对于 LangGraph 工作流，工具执行由 [`ToolNode`](https://reference.langchain.com/python/langgraph/agents/#langgraph.prebuilt.tool_node.ToolNode) 处理。Graph API 用法参见 [ToolNode](https://docs.langchain.com/oss/python/langgraph/workflows-agents.md#toolnode)，其中包括工具如何访问当前图状态及运行范围内的上下文。

### 工具返回值

可以为工具选择不同的返回值：

* 返回 `string`，用于人类可读的结果。
* 返回 `object`，用于需要模型解析的结构化结果。
* 需要写入状态时，返回 `Command`，并可附带消息。

#### 返回字符串

当工具应提供纯文本，供模型读取并在下一次响应中使用时，返回字符串。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"It is currently sunny in {city}."
```

> [card] [查看示例追踪](https://smith.langchain.com/public/9c20937f-20e4-4ed2-adfa-eeda6fd63997/r)
>
> 打开此示例的公开 LangSmith 运行记录。

行为：

* 返回值被转换为 `ToolMessage`。
* 模型看到文本后决定下一步操作。
* 不会更改智能体状态字段，除非模型或另一个工具之后这样做。

当结果天然就是人类可读文本时，使用此方式。

#### 返回对象

当工具产生需要模型检查的结构化数据时，返回对象（例如 `dict`）。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool


@tool
def get_weather_data(city: str) -> dict:
    """Get structured weather data for a city."""
    return {
        "city": city,
        "temperature_c": 22,
        "conditions": "sunny",
    }
```

> [card] [查看示例追踪](https://smith.langchain.com/public/2f82d8ae-bcf6-4b6d-94ee-0d724c30fa98/r)
>
> 打开此示例的公开 LangSmith 运行记录。

行为：

* 对象被序列化，并作为工具输出返回。
* 模型可以读取特定字段并据此推理。
* 与返回字符串类似，这不会直接更新图状态。

当后续推理更适合使用明确字段而非自由文本时，使用此方式。

#### 返回多模态内容

工具并不限于纯文本。模型支持多模态工具结果时，工具可以返回[标准内容块](https://docs.langchain.com/oss/python/langchain/messages.md#standard-content-blocks)，使模型在一次工具结果中接收文本、图像及其他媒体。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool


@tool
def capture_screenshot() -> list[dict]:
    """Capture a screenshot of the current page."""
    return [
        {"type": "text", "text": "Screenshot of the current page:"},
        {"type": "image", "url": "https://example.com/page.png"},
    ]
```

行为：

* 返回值被转换为带有多模态 `content` 的 `ToolMessage`。
* 工具运行后，使用 `message.content_blocks` 读取归一化的内容块列表。
* 模型必须支持所返回的模态。返回图像、音频或视频前，请检查[模型能力](https://docs.langchain.com/oss/python/integrations/chat.md)。

块类型与提供商特有要求参见[多模态消息](https://docs.langchain.com/oss/python/langchain/messages.md#multimodal)。

返回图像或混合内容的 MCP 工具也以相同方式转换。参见[多模态内容](https://docs.langchain.com/oss/python/langchain/mcp/tools.md#multimodal-content)。

#### 返回 Command

工具需要更新图状态（例如设置用户偏好或应用状态）时，返回 [`Command`](https://reference.langchain.com/python/langgraph/types/Command)。
当 `Command` 的目标为当前图时，在更新中包含一条工具调用 ID 与当前调用匹配的 `ToolMessage`。
消息历史中的每个工具调用都必须有对应的 `ToolMessage`。

使用 `runtime.tool_call_id` 作为 `tool_call_id` 参数。`ToolNode` 强制执行此要求：若更新中没有与工具调用匹配的 `ToolMessage`，就会抛出 `ValueError`。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command


@tool
def set_language(language: str, runtime: ToolRuntime) -> Command:
    """Set the preferred response language."""
    return Command(
        update={
            "preferred_language": language,
            "messages": [
                ToolMessage(
                    content=f"Language set to {language}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
```

行为：

* 命令使用 `update` 更新状态。
* 更新后的状态可供同一次运行中的后续步骤使用。
* 对可能被并行工具调用更新的字段使用归约函数。

当工具不仅返回数据，还修改智能体状态时，使用此方式。

#### 从工具直接返回

在工具上设置直接返回，以短路智能体循环：智能体立即将工具输出返回给调用方，不再将结果送回模型作进一步处理。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI


@tool(return_direct=True)
def fetch_order_status(order_id: str) -> str:
    """Fetch the current status of a customer order."""
    # In production, query your order management system here
    return f"Order {order_id} is shipped and will arrive in 2 days."


agent = create_agent(
    ChatOpenAI(model="gpt-5.4-mini"),
    tools=[fetch_order_status],
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "What is the status of order #12345?"}]
})
# The agent returns the tool output directly without another LLM call:
# "Order 12345 is shipped and will arrive in 2 days."
```

> [card] [查看示例追踪](https://smith.langchain.com/public/0a2f53f6-eaea-4092-b86b-c4e0a41998bc/r)
>
> 打开此示例的公开 LangSmith 运行记录。

行为：

* 工具正常执行，输出包装为 `ToolMessage`。
* 智能体停止循环，将工具输出作为最终响应返回，跳过额外模型调用。
* **多个并行工具调用：**模型在一个步骤中调用多个工具时，会先执行全部工具。所有工具结束后，只有该批次中**每个**工具都设置了 `return_direct=True`，智能体才会路由到 `END`。最终响应包含该步骤调用的所有工具的 `ToolMessage` 输出。

适用情况：

* 工具输出就是完整、可直接交付用户的答案（例如返回可直接展示结果的查询）。
* 不需要额外推理时，希望避免额外模型调用。
* 需要确定性、未经修改的输出：模型不能改写、总结工具结果，也不能据此采取行动。

> [!WARNING]
>
> 由于模型不会处理工具输出，`return_direct=True` 不适用于结果仍需进一步推理、总结或与其他工具调用串联的工具。

> [!WARNING]
>
> **混合并行调用：**如果模型同时调用一个 `return_direct=True` 工具和其他未设置 `return_direct=True` 的工具，智能体**不会**在该步骤后退出。它会带着该批次的所有 `ToolMessage` 返回模型，让模型对全部结果进行推理。只有该步骤的每次工具调用都设置 `return_direct=True` 时，`return_direct` 才会短路循环。

#### 同时使用 Command 与 return\_direct

设置了 `return_direct=True` 的工具也可以返回 [`Command`](https://reference.langchain.com/python/langgraph/types/Command)，在智能体退出前更新图状态。与普通返回值不同，`Command` 不会自动转换为 `ToolMessage`。当 `Command` 的目标为当前图时（未设置 `graph` 或值为 `None`），应在 `Command.update` 中包含与该工具调用的 `tool_call_id` 匹配的 `ToolMessage`。若省略，`ToolNode` 会抛出 `ValueError`，因为消息历史中的每个 `AIMessage` 工具调用都必须有对应的 `ToolMessage`。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command


@tool(return_direct=True)
def fetch_and_store_order(order_id: str, runtime: ToolRuntime) -> Command:
    """Fetch order status and store it in state."""
    status = f"Order {order_id} is shipped and will arrive in 2 days."
    return Command(
        update={
            "last_order_status": status,
            # Must include a ToolMessage so the message history stays valid
            "messages": [
                ToolMessage(
                    content=status,
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
```

若要改为写入父图，设置 `graph=Command.PARENT`。此时由于执行会完全离开当前图，因此不再要求提供 `ToolMessage`。

### 错误处理

使用 LangChain 智能体[中间件](https://docs.langchain.com/oss/python/langchain/middleware.md)处理工具错误，重试失败的工具调用或返回自定义错误消息：

```python Google theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from collections.abc import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest


@wrap_tool_call
def handle_tool_errors(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """Convert tool exceptions into ToolMessages the model can handle."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({e})",
            tool_call_id=request.tool_call["id"],
        )


agent = create_agent(
    model="google_genai:gemini-4-hydrogen",
    tools=[],
    middleware=[handle_tool_errors],
)
```

```python OpenAI theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from collections.abc import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest


@wrap_tool_call
def handle_tool_errors(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """Convert tool exceptions into ToolMessages the model can handle."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({e})",
            tool_call_id=request.tool_call["id"],
        )


agent = create_agent(
    model="openai:gpt-6.1-sol",
    tools=[],
    middleware=[handle_tool_errors],
)
```

```python Anthropic theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from collections.abc import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest


@wrap_tool_call
def handle_tool_errors(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """Convert tool exceptions into ToolMessages the model can handle."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({e})",
            tool_call_id=request.tool_call["id"],
        )


agent = create_agent(
    model="anthropic:claude-sonnet-5",
    tools=[],
    middleware=[handle_tool_errors],
)
```

```python OpenRouter theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from collections.abc import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest


@wrap_tool_call
def handle_tool_errors(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """Convert tool exceptions into ToolMessages the model can handle."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({e})",
            tool_call_id=request.tool_call["id"],
        )


agent = create_agent(
    model="openrouter:z-ai/glm-5.2",
    tools=[],
    middleware=[handle_tool_errors],
)
```

```python Fireworks theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from collections.abc import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest


@wrap_tool_call
def handle_tool_errors(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """Convert tool exceptions into ToolMessages the model can handle."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({e})",
            tool_call_id=request.tool_call["id"],
        )


agent = create_agent(
    model="fireworks:accounts/fireworks/models/glm-5p2",
    tools=[],
    middleware=[handle_tool_errors],
)
```

```python Baseten theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from collections.abc import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest


@wrap_tool_call
def handle_tool_errors(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """Convert tool exceptions into ToolMessages the model can handle."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({e})",
            tool_call_id=request.tool_call["id"],
        )


agent = create_agent(
    model="baseten:zai-org/GLM-5.2",
    tools=[],
    middleware=[handle_tool_errors],
)
```

```python Ollama theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from collections.abc import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest


@wrap_tool_call
def handle_tool_errors(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """Convert tool exceptions into ToolMessages the model can handle."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({e})",
            tool_call_id=request.tool_call["id"],
        )


agent = create_agent(
    model="ollama:north-mini-code-1.0",
    tools=[],
    middleware=[handle_tool_errors],
)
```

### 状态注入

工具通过 [`ToolRuntime`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.ToolRuntime) 访问图状态。状态、上下文、存储与流式 API 参见[访问上下文](#access-context)。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool, ToolRuntime

@tool
def get_message_count(runtime: ToolRuntime) -> str:
    """Get the number of messages in the conversation."""
    messages = runtime.state["messages"]
    return f"There are {len(messages)} messages."
```

关于从工具访问状态、上下文及长期记忆的更多详情，参见[访问上下文](#access-context)。

## 动态工具选择

使用动态工具时，智能体可用的工具集合在运行时修改，而非预先全部固定。并非每种工具都适合所有情况。工具过多可能使模型不堪重负（上下文过载）并增加错误；工具过少又限制能力。动态工具选择允许根据认证状态、用户权限、功能开关或对话阶段调整可用工具集。

根据是否预先知道工具，有两种方法：

> [tab] 筛选预注册工具
>
> 若创建智能体时已知所有可能用到的工具，可以预先注册，并根据状态、权限或上下文动态筛选向模型开放的工具。
>
> > [tab] 状态
> >
> > 只有对话达到特定里程碑后才启用高级工具：
> >
> > ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> > from langchain.agents import create_agent
> > from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
> > from typing import Callable
> >
> > @wrap_model_call
> > def state_based_tools(
> >     request: ModelRequest,
> >     handler: Callable[[ModelRequest], ModelResponse]
> > ) -> ModelResponse:
> >     """Filter tools based on conversation State."""
> >     # Read from State: check if user has authenticated
> >     state = request.state
> >     is_authenticated = state.get("authenticated", False)
> >     message_count = len(state["messages"])
> >
> >     # Only enable sensitive tools after authentication
> >     if not is_authenticated:
> >         tools = [t for t in request.tools if t.name.startswith("public_")]
> >         request = request.override(tools=tools)
> >     elif message_count < 5:
> >         # Limit tools early in conversation
> >         tools = [t for t in request.tools if t.name != "advanced_search"]
> >         request = request.override(tools=tools)
> >
> >     return handler(request)
> >
> > agent = create_agent(
> >     model="gpt-6.1-sol",
> >     tools=[public_search, private_search, advanced_search],
> >     middleware=[state_based_tools]
> > )
> > ```
>
> > [tab] 存储
> >
> > 根据存储中的用户偏好或功能开关筛选工具：
> >
> > ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> > from dataclasses import dataclass
> > from langchain.agents import create_agent
> > from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
> > from typing import Callable
> > from langgraph.store.memory import InMemoryStore
> >
> > @dataclass
> > class Context:
> >     user_id: str
> >
> > @wrap_model_call
> > def store_based_tools(
> >     request: ModelRequest,
> >     handler: Callable[[ModelRequest], ModelResponse]
> > ) -> ModelResponse:
> >     """Filter tools based on Store preferences."""
> >     user_id = request.runtime.context.user_id
> >
> >     # Read from Store: get user's enabled features
> >     store = request.runtime.store
> >     feature_flags = store.get(("features",), user_id)
> >
> >     if feature_flags:
> >         enabled_features = feature_flags.value.get("enabled_tools", [])
> >         # Only include tools that are enabled for this user
> >         tools = [t for t in request.tools if t.name in enabled_features]
> >         request = request.override(tools=tools)
> >
> >     return handler(request)
> >
> > agent = create_agent(
> >     model="gpt-6.1-sol",
> >     tools=[search_tool, analysis_tool, export_tool],
> >     middleware=[store_based_tools],
> >     context_schema=Context,
> >     store=InMemoryStore()
> > )
> > ```
>
> > [tab] 运行时上下文
> >
> > 根据运行时上下文中的用户权限筛选工具：
> >
> > ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> > from dataclasses import dataclass
> > from langchain.agents import create_agent
> > from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
> > from typing import Callable
> >
> > @dataclass
> > class Context:
> >     user_role: str
> >
> > @wrap_model_call
> > def context_based_tools(
> >     request: ModelRequest,
> >     handler: Callable[[ModelRequest], ModelResponse]
> > ) -> ModelResponse:
> >     """Filter tools based on Runtime Context permissions."""
> >     # Read from Runtime Context: get user role
> >     if request.runtime is None or request.runtime.context is None:
> >         # If no context provided, default to viewer (most restrictive)
> >         user_role = "viewer"
> >     else:
> >         user_role = request.runtime.context.user_role
> >
> >     if user_role == "admin":
> >         # Admins get all tools
> >         pass
> >     elif user_role == "editor":
> >         # Editors can't delete
> >         tools = [t for t in request.tools if t.name != "delete_data"]
> >         request = request.override(tools=tools)
> >     else:
> >         # Viewers get read-only tools
> >         tools = [t for t in request.tools if t.name.startswith("read_")]
> >         request = request.override(tools=tools)
> >
> >     return handler(request)
> >
> > agent = create_agent(
> >     model="gpt-6.1-sol",
> >     tools=[read_data, write_data, delete_data],
> >     middleware=[context_based_tools],
> >     context_schema=Context
> > )
> > ```
>
> 此方法最适合：
>
> * 编译／启动时已知所有可能的工具
> * 希望根据权限、功能开关或对话状态筛选
> * 工具本身静态，但可用性动态变化
>
> 更多示例参见[动态选择工具](https://docs.langchain.com/oss/python/langchain/middleware/custom.md#dynamically-selecting-tools)。

> [tab] 运行时注册工具
>
> 工具在运行时被发现或创建时（例如从 MCP 服务器加载、根据用户数据生成，或从远程注册中心获取），需要动态注册工具并处理其执行。
>
> 这需要两个中间件钩子：
>
> 1. `wrap_model_call`——将动态工具添加到请求中
> 2. `wrap_tool_call`——处理动态添加工具的执行
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from langchain.tools import tool
> from langchain.agents import create_agent
> from langchain.agents.middleware import AgentMiddleware, ModelRequest, ToolCallRequest
>
> # A tool that will be added dynamically at runtime
> @tool
> def calculate_tip(bill_amount: float, tip_percentage: float = 20.0) -> str:
>     """Calculate the tip amount for a bill."""
>     tip = bill_amount * (tip_percentage / 100)
>     return f"Tip: ${tip:.2f}, Total: ${bill_amount + tip:.2f}"
>
> class DynamicToolMiddleware(AgentMiddleware):
>     """Middleware that registers and handles dynamic tools."""
>
>     def wrap_model_call(self, request: ModelRequest, handler):
>         # Add dynamic tool to the request
>         # This could be loaded from an MCP server, database, etc.
>         updated = request.override(tools=[*request.tools, calculate_tip])
>         return handler(updated)
>
>     def wrap_tool_call(self, request: ToolCallRequest, handler):
>         # Handle execution of the dynamic tool
>         if request.tool_call["name"] == "calculate_tip":
>             return handler(request.override(tool=calculate_tip))
>         return handler(request)
>
> agent = create_agent(
>     model="gpt-6.1-sol",
>     tools=[get_weather],  # Only static tools registered here
>     middleware=[DynamicToolMiddleware()],
> )
>
> # The agent can now use both get_weather AND calculate_tip
> result = agent.invoke({
>     "messages": [{"role": "user", "content": "Calculate a 20% tip on $85"}]
> })
> ```
>
> 此方法最适合：
>
> * 运行时发现工具（例如来自 MCP 服务器）
>
> * 根据用户数据或配置动态生成工具
>
> * 与外部工具注册中心集成
>
> > [!NOTE]
> >
> > 运行时注册的工具必须使用 `wrap_tool_call` 钩子，因为智能体需要知道如何执行不在原始工具列表中的工具。没有它，智能体就不知道如何调用动态添加的工具。

## 无本地实现工具（Headless tools）

某些工具应在**用户应用运行的位置**（通常为浏览器）执行，而不是在当前进程中执行。**无本地实现工具**是你在**服务器**上随智能体注册的工具定义，包含名称、说明和参数模式。其**实现**仅在**客户端**注册，并在简短的中断／恢复握手后执行。

这不同于函数体在服务器上运行的普通工具，也不同于模型提供商远程执行内置工具的[服务端工具使用](#server-side-tool-use)。

### 何时使用无本地实现工具

当工作依赖仅在客户端存在的**环境、设备或界面**时使用。例如：

* **浏览器 API：**Geolocation、IndexedDB、Clipboard、Canvas 2D、文件选择器、Battery API 等。
* **隐私与本地性：**数据留在设备上（例如 IndexedDB 中的本地“记忆”）。
* **延迟：**纯本地操作不需要额外的服务器往返请求。
* **结构化、安全的副作用：**优先使用许多小型、有类型定义的工具（例如每个画布基础操作对应一个工具），而不是向 `eval` 发送任意代码。

### 此模式如何工作

在两种运行时中，模型看到的都是可正常调用的工具，但实际执行发生在服务器进程之外。

1. 使用 `langchain.tools` 中的 `tool(name=..., description=..., args_schema=...)` **定义**无本地实现工具。此类工具仅有模式，没有进程内实现。
2. 将工具**注册**到 `create_agent` 或 LangGraph 图，让模型正常调用。
3. 工具被调用时，**处理**中断负载。图不会在本地执行工具，而会暂停并给出形如 `{"type": "tool", "tool_call": {"id", "name", "args"}}` 的负载。
4. 应用、其他服务或人工步骤执行操作后，**恢复**图。对于浏览器流程，可在前端镜像同一模式，并在那里附加 `.implement(...)`。

> [!NOTE]
>
> 在 Python 中仅提供 `name`、`description` 和 `args_schema` 调用 `tool(...)` 时，LangChain 返回 `HeadlessTool`。Python 端没有 `.implement()` API。

模型调用这类工具时，运行会**中断**，而不是本地执行工具。应用可以检查负载，在正确环境中执行操作（例如浏览器、其他服务或人工审核步骤），再携带工具结果**恢复**图。使用受支持的 JS SDK 钩子时，它们能够检测这类工具中断，运行匹配的客户端实现，并代你提交恢复命令。

使用可选的 **`onTool`** 回调观察生命周期事件（`start`、`success`、`error`），为加载指示器或提示消息等界面反馈提供依据。

> [card] [无本地实现工具的前端模式](https://docs.langchain.com/oss/python/langchain/frontend/headless-tools.md)
>
> 查看使用 `useStream` 在客户端执行仅有模式定义的工具的端到端示例。

## 预构建工具

LangChain 为网页搜索、代码解释、数据库访问等常见任务提供了大量预构建工具和工具包。这些即用型工具可直接集成到智能体，无须编写自定义代码。

按类别组织的全部可用工具，参见[工具与工具包](https://docs.langchain.com/oss/python/integrations/tools.md)集成页面。

## 来自 MCP 服务器的工具

[模型上下文协议（MCP）](https://modelcontextprotocol.io)是一种开放协议，标准化应用向语言模型开放工具的方式。无需手动编写工具，只需连接 MCP 服务器，将其公布的工具适配为 LangChain 工具，就能像其他工具一样传给智能体。

[`MCPAdapter`](https://reference.langchain.com/python/langchain/mcp/adapter/MCPAdapter) 发现服务器工具并将其转换为 LangChain 工具。打开适配器，调用 `list_tools()`，将结果传给 [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_agent)：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.agents import create_agent
from langchain.mcp import MCPAdapter

async with MCPAdapter("https://example.com/mcp") as adapter:
    tools = await adapter.list_tools()
    agent = create_agent("claude-sonnet-4-6", tools)
```

> [!NOTE]
>
> `langchain.mcp` 命名空间需要 `langchain[mcp]>=1.4.0`，目前为测试版，API 可能变化。

传输方式、认证、多服务器及工具结果处理，参见[模型上下文协议（MCP）](https://docs.langchain.com/oss/python/langchain/mcp.md)。

## 服务端工具使用

一些聊天模型具有由模型提供商在服务端执行的内置工具，包括网页搜索、代码解释器等能力，无需自行定义或托管工具逻辑。

启用和使用这些内置工具的详情，请参阅各个[聊天模型集成页面](https://docs.langchain.com/oss/python/integrations/providers)和[工具调用文档](https://docs.langchain.com/oss/python/langchain/models.md#server-side-tool-use)。

***

[连接这些文档](https://docs.langchain.com/use-these-docs.md) ，通过 MCP 将其接入你选择的智能体，以获取实时答案。

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/tools.mdx) 或[提交问题](https://github.com/langchain-ai/docs/issues/new/choose).
