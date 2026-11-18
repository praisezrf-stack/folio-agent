<!--
Source-URL: https://docs.langchain.com/oss/python/langgraph/checkpointers.md
HTML-URL: https://docs.langchain.com/oss/python/langgraph/checkpointers
Downloaded: 2026-11-17 10:02:55 Asia/Shanghai
Original-Language: English
Official-Section: LangGraph > Capabilities
Category: capability
-->

> ## 文档索引
> 完整文档索引：https://docs.langchain.com/llms.txt
> 在进一步阅读之前，可使用此文件发现所有可用页面。

# 检查点保存器

> LangGraph 检查点保存器在每一步将图状态保存为检查点，从而支持持久化、人工介入和容错执行。

检查点保存器在每个超级步保存图状态快照，并按**线程**组织。为图配置检查点保存器并编译，即可启用人工介入工作流、时间旅行调试、容错执行和对话记忆。

![检查点示意图](https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/checkpoints.jpg?fit=max\&auto=format\&n=-_xGPoyjhyiDWTPJ\&q=85\&s=966566aaae853ed4d240c2d0d067467c)

> [!NOTE]
>
> **Agent Server 自动处理检查点保存**
> 使用 [Agent Server](https://docs.langchain.com/langsmith/agent-server.md) 时，无须手动实现或配置检查点保存器。服务器会在后台处理所有持久化基础设施。

> [!TIP]
>
> 使用 [LangSmith](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-langgraph-checkpointers) 追踪已保存检查点的状态，调试智能体如何跨会话恢复。按照[追踪快速入门](https://docs.langchain.com/langsmith/trace-with-langgraph.md)完成设置。

## 为什么使用检查点保存器

以下功能需要检查点保存器：

* **人工介入**：检查点保存器允许人工检查、中断和批准图的步骤，从而支持[人工介入工作流](https://docs.langchain.com/oss/python/langgraph/interrupts.md)。此类工作流需要检查点保存器，因为人必须能够查看图在任意时刻的状态，而在人工更新状态后，图必须能够恢复执行。示例参见[中断](https://docs.langchain.com/oss/python/langgraph/interrupts.md)。
* **记忆**：检查点保存器允许在多次交互之间保留[“记忆”](https://docs.langchain.com/oss/python/concepts/memory.md)。对于反复发生的人机交互（例如对话），后续消息可以发送到同一线程，该线程会记住此前的消息。关于如何使用检查点保存器添加和管理对话记忆，参见[添加记忆](https://docs.langchain.com/oss/python/langgraph/add-memory.md)。
* **时间旅行**：检查点保存器支持[“时间旅行”](https://docs.langchain.com/oss/python/langgraph/use-time-travel.md)，允许用户重放过去的图执行，以审核和／或调试特定步骤。此外，它使你能够在任意检查点分叉图状态，探索其他执行轨迹。
* **容错**：检查点保存支持容错和错误恢复：如果某个超级步中一个或多个节点失败，可以从最后一个成功步骤重新启动图。

- **待处理写入**：当图节点在某个[超级步](#super-steps)的执行途中失败时，LangGraph 会保存该超级步中其他已成功节点的待处理检查点写入。从这个超级步恢复图执行时，不必重新运行那些成功节点。

## 核心概念

### 线程

线程通过唯一 ID（线程标识符）标记检查点保存器保存的检查点，包含一系列[运行](https://docs.langchain.com/langsmith/runs.md)的累积状态。每次运行执行时，助手底层图的[状态](https://docs.langchain.com/oss/python/langgraph/graph-api.md#state)都会持久化到该线程。

调用带有检查点保存器的图时，**必须**在配置的 `configurable` 部分指定 `thread_id`：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
{"configurable": {"thread_id": "1"}}
```

可以检索线程的当前状态和历史状态。要持久化状态，必须在执行运行之前创建线程。LangSmith API 提供多个端点，用于创建和管理线程及线程状态。更多详情见 [API 参考](https://reference.langchain.com/python/langsmith/)。

检查点保存器使用 `thread_id` 作为存储和检索检查点的主键。没有它，就无法保存状态，也无法在[中断](https://docs.langchain.com/oss/python/langgraph/interrupts.md)后恢复执行，因为检查点保存器需要通过 `thread_id` 加载保存的状态。

#### 选择如何继续线程

`thread_id` 标识已保存的状态。输入和 `checkpoint_id` 决定一次调用是开始新工作、恢复未完成工作，还是重放历史。仅复用线程 ID，并不意味着执行会从暂停处恢复。

配置检查点保存器且线程已存在时，请按目标选择调用方式：

| 目标 | 调用方式 | 执行行为 |
| - | - | - |
| 提交新输入 | `graph.invoke(input, config)` | 将输入应用于已保存状态，并从入口开始执行。 |
| 出错后继续 | `graph.invoke(None, config)` | 加载最新检查点并重试未完成工作。不传 `checkpoint_id`。 |
| 回答 `interrupt()` | `graph.invoke(Command(resume=answer), config)` | 提供中断的返回值。被中断节点从头重新开始。 |
| 重放历史 | `graph.invoke(None, snapshot.config)` | 使用 `get_state_history()` 返回的快照，重新执行该检查点之后的节点。 |

新输入不会清空线程。LangGraph 使用状态的[归约函数](https://docs.langchain.com/oss/python/langgraph/graph-api.md#reducers)应用输入。若要从空状态开始，请使用新的 `thread_id`。

如果最新检查点没有未完成工作，恢复操作会直接返回已保存结果，不运行节点。可运行示例参见[恢复中断](https://docs.langchain.com/oss/python/langgraph/interrupts.md#resuming-interrupts)和[重放历史](https://docs.langchain.com/oss/python/langgraph/use-time-travel.md#replay)。包装其他框架时的入口恢复规则，参见[函数式 API 概览](https://docs.langchain.com/oss/python/langgraph/functional-api.md#run-and-resume)。

### 检查点

线程在某个特定时刻的状态称为检查点。检查点是在每个[超级步](#super-steps)保存的图状态快照，表示为 `StateSnapshot` 对象（完整字段参考见 [StateSnapshot 字段](#statesnapshot-fields)）。

#### 超级步

LangGraph 在每个**超级步**边界创建检查点。超级步是图的一次“时钟滴答”，在其中执行为该步调度的所有节点（可能并行执行）。对于 `START -> A -> B -> END` 这样的顺序图，输入、节点 A 和节点 B 各自对应独立超级步，每个超级步结束后都会生成检查点。理解超级步边界对[时间旅行](https://docs.langchain.com/oss/python/langgraph/use-time-travel.md)很重要，因为只能从检查点（即超级步边界）恢复执行。

除超级步检查点外，LangGraph 还会在**节点（任务）级别**持久化写入。超级步内每个节点完成时，其输出会作为任务条目写入检查点保存器的 `checkpoint_writes` 表，并关联正在进行中的检查点。这些逐任务写入使[待处理写入](#pending-writes)恢复成为可能：同一超级步内另一个节点失败时，成功节点的写入已经持久化，恢复时无需重新执行它们。超级步全部完成后，再提交完整状态快照。

LangGraph 也会持久化超级步内各次节点执行的写入。这些写入以任务形式保存，用于容错：若同一超级步内另一个节点失败，恢复时无需重新计算成功节点的写入。这些任务写入并不是完整的 `StateSnapshot` 检查点，因此时间旅行仍从超级步边界的完整检查点恢复。

检查点会被持久化，可在之后恢复线程状态。

下面看看按以下方式调用一个简单图时，会保存哪些检查点：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

class State(TypedDict):
    foo: str
    bar: Annotated[list[str], add]

def node_a(state: State):
    return {"foo": "a", "bar": ["a"]}

def node_b(state: State):
    return {"foo": "b", "bar": ["b"]}


workflow = StateGraph(State)
workflow.add_node(node_a)
workflow.add_node(node_b)
workflow.add_edge(START, "node_a")
workflow.add_edge("node_a", "node_b")
workflow.add_edge("node_b", END)

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}
graph.invoke({"foo": "", "bar":[]}, config)
```

图运行后，将恰好产生 4 个检查点：

* 空检查点，下一个待执行节点为 [`START`](https://reference.langchain.com/python/langgraph/constants/START)
* 包含用户输入 `{'foo': '', 'bar': []}` 的检查点，下一个待执行节点为 `node_a`
* 包含 `node_a` 输出 `{'foo': 'a', 'bar': ['a']}` 的检查点，下一个待执行节点为 `node_b`
* 包含 `node_b` 输出 `{'foo': 'b', 'bar': ['a', 'b']}` 的检查点，没有下一个待执行节点

注意，`bar` 通道的值包含两个节点的输出，因为此示例为 `bar` 通道定义了归约函数。

#### 检查点命名空间

每个检查点都有 `checkpoint_ns`（检查点命名空间）字段，标识它属于哪个图或子图：

* **`""`**（空字符串）：检查点属于父图（根图）。
* **`"node_name:uuid"`**：检查点属于以该节点身份调用的子图。对于嵌套子图，命名空间使用 `|` 分隔符连接（例如 `"outer_node:uuid|inner_node:uuid"`）。

可以在节点内部通过配置访问检查点命名空间：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain_core.runnables import RunnableConfig

def my_node(state: State, config: RunnableConfig):
    checkpoint_ns = config["configurable"]["checkpoint_ns"]
    # "" for the parent graph, "node_name:uuid" for a subgraph
```

关于子图状态和检查点的更多内容，参见[子图](https://docs.langchain.com/oss/python/langgraph/use-subgraphs.md)。

## 获取和更新状态

### 获取状态

与已保存的图状态交互时，**必须**指定[线程标识符](#threads)。调用 `graph.get_state(config)` 可查看图的*最新*状态。它返回一个 `StateSnapshot` 对象，对应配置中线程 ID 关联的最新检查点；若同时提供该线程的检查点 ID，则返回相应检查点。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
# get the latest state snapshot
config = {"configurable": {"thread_id": "1"}}
graph.get_state(config)

# get a state snapshot for a specific checkpoint_id
config = {"configurable": {"thread_id": "1", "checkpoint_id": "1ef663ba-28fe-6528-8002-5a559208592c"}}
graph.get_state(config)
```

在此示例中，`get_state` 的输出如下：

```
StateSnapshot(
    values={'foo': 'b', 'bar': ['a', 'b']},
    next=(),
    config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28fe-6528-8002-5a559208592c'}},
    metadata={'source': 'loop', 'writes': {'node_b': {'foo': 'b', 'bar': ['b']}}, 'step': 2},
    created_at='2024-08-29T19:19:38.821749+00:00',
    parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f9-6ec4-8001-31981c2c39f8'}},
    tasks=()
)
```

#### StateSnapshot 字段

| 字段 | 类型 | 说明 |
| - | - | - |
| `values` | `dict` | 此检查点的状态通道值。 |
| `next` | `tuple[str, ...]` | 接下来执行的节点名。空元组 `()` 表示图已完成。 |
| `config` | `dict` | 包含 `thread_id`、`checkpoint_ns` 和 `checkpoint_id`。 |
| `metadata` | `dict` | 执行元数据。包含 `source`（`"input"`、`"loop"` 或 `"update"`）、`writes`（节点输出）及 `step`（超级步计数器）。 |
| `created_at` | `str` | 检查点创建时的 ISO 8601 时间戳。 |
| `parent_config` | `dict \| None` | 前一个检查点的配置。首个检查点为 `None`。 |
| `tasks` | `tuple[PregelTask, ...]` | 此步骤待执行的任务。每个任务都有 `id`、`name`、`error`、`interrupts`，还可带有 `state`（使用 `subgraphs=True` 时的子图快照）。 |

### 获取状态历史

调用 [`graph.get_state_history(config)`](https://reference.langchain.com/python/langgraph/graphs/#langgraph.graph.state.CompiledStateGraph.get_state_history)，可获取指定线程的完整图执行历史。它返回与配置中线程 ID 关联的 `StateSnapshot` 对象列表。需要注意，检查点按时间倒序排列，最新的检查点／`StateSnapshot` 位于列表最前面。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
config = {"configurable": {"thread_id": "1"}}
list(graph.get_state_history(config))
```

在此示例中，[`get_state_history`](https://reference.langchain.com/python/langgraph/graphs/#langgraph.graph.state.CompiledStateGraph.get_state_history) 的输出如下：

```
[
    StateSnapshot(
        values={'foo': 'b', 'bar': ['a', 'b']},
        next=(),
        config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28fe-6528-8002-5a559208592c'}},
        metadata={'source': 'loop', 'writes': {'node_b': {'foo': 'b', 'bar': ['b']}}, 'step': 2},
        created_at='2024-08-29T19:19:38.821749+00:00',
        parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f9-6ec4-8001-31981c2c39f8'}},
        tasks=(),
    ),
    StateSnapshot(
        values={'foo': 'a', 'bar': ['a']},
        next=('node_b',),
        config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f9-6ec4-8001-31981c2c39f8'}},
        metadata={'source': 'loop', 'writes': {'node_a': {'foo': 'a', 'bar': ['a']}}, 'step': 1},
        created_at='2024-08-29T19:19:38.819946+00:00',
        parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f4-6b4a-8000-ca575a13d36a'}},
        tasks=(PregelTask(id='6fb7314f-f114-5413-a1f3-d37dfe98ff44', name='node_b', error=None, interrupts=()),),
    ),
    StateSnapshot(
        values={'foo': '', 'bar': []},
        next=('node_a',),
        config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f4-6b4a-8000-ca575a13d36a'}},
        metadata={'source': 'loop', 'writes': None, 'step': 0},
        created_at='2024-08-29T19:19:38.817813+00:00',
        parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f0-6c66-bfff-6723431e8481'}},
        tasks=(PregelTask(id='f1b14528-5ee5-579c-949b-23ef9bfbed58', name='node_a', error=None, interrupts=()),),
    ),
    StateSnapshot(
        values={'bar': []},
        next=('__start__',),
        config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f0-6c66-bfff-6723431e8481'}},
        metadata={'source': 'input', 'writes': {'foo': ''}, 'step': -1},
        created_at='2024-08-29T19:19:38.816205+00:00',
        parent_config=None,
        tasks=(PregelTask(id='6d27aa2e-d72b-5504-a36f-8620e54a76dd', name='__start__', error=None, interrupts=()),),
    )
]
```

![状态示意图](https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/get_state.jpg?fit=max\&auto=format\&n=-_xGPoyjhyiDWTPJ\&q=85\&s=38ffff52be4d8806b287836295a3c058)

#### 查找特定检查点

可以筛选状态历史，找到符合特定条件的检查点：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
history = list(graph.get_state_history(config))

# Find the checkpoint before a specific node executed
before_node_b = next(s for s in history if s.next == ("node_b",))

# Find a checkpoint by step number
step_2 = next(s for s in history if s.metadata["step"] == 2)

# Find checkpoints created by update_state
forks = [s for s in history if s.metadata["source"] == "update"]

# Find the checkpoint where an interrupt occurred
interrupted = next(
    s for s in history
    if s.tasks and any(t.interrupts for t in s.tasks)
)
```

#### 列出所有线程

要查看检查点保存器为哪些线程保存了状态，例如构建管理或调试视图，请在列出检查点时省略 `thread_id`：

`graph.get_state_history(config)` 要求 `config` 包含 `thread_id`，且只返回一个线程的历史。请对传给 `compile` 的同一个检查点保存器调用 `.list`，并设置 `config=None`：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
# config=None returns checkpoints across every thread
for checkpoint_tuple in checkpointer.list(None):
    print(checkpoint_tuple.config["configurable"]["thread_id"])
```

传入 `None`，不要传 `{}`。[`SqliteSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.sqlite.SqliteSaver) 将任何非 `None` 配置都视为线程筛选条件，缺少 `thread_id` 时会报错。异步图使用 `.alist(None)`。此方式适用于 [`InMemorySaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.memory.InMemorySaver)、[`SqliteSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.sqlite.SqliteSaver) 和 [`PostgresSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.postgres.PostgresSaver)。`.list` 仍然为每个检查点返回一行，而非每个线程一行；因此需要自行按 `thread_id` 分组，构建线程列表。

### 重放

重放会重新执行过去某个检查点之后的步骤。调用图时传入此前的 `checkpoint_id`，即可重新运行该检查点之后的节点。检查点之前的节点会跳过（结果已保存）。检查点之后的节点重新执行，包括所有大语言模型调用、API 请求或[中断](https://docs.langchain.com/oss/python/langgraph/interrupts.md)——重放时中断始终会再次触发。

重放历史执行的完整说明和代码示例，见[时间旅行](https://docs.langchain.com/oss/python/langgraph/use-time-travel.md)。

![重放示意图](https://mintcdn.com/langchain-5e9cc07a/dL5Sn6Cmy9pwtY0V/oss/images/re_play.png?fit=max\&auto=format\&n=dL5Sn6Cmy9pwtY0V\&q=85\&s=d7b34b85c106e55d181ae1f4afb50251)

### 更新状态

可以使用 [`update_state`](https://reference.langchain.com/python/langgraph/graphs/#langgraph.graph.state.CompiledStateGraph.update_state) 编辑图状态。这会使用更新后的值创建新检查点，而不是修改原检查点。更新与节点更新的处理方式相同：如果定义了[归约函数](https://docs.langchain.com/oss/python/langgraph/graph-api.md#reducers)，值会经过归约函数处理，因此带归约函数的通道会*累积*值，而不是覆盖。

可以选择指定 `as_node`，控制本次更新被视为来自哪个节点，从而影响接下来执行哪个节点。详情见[时间旅行：`as_node`](https://docs.langchain.com/oss/python/langgraph/use-time-travel#from-a-specific-node)。

![状态更新示意图](https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/checkpoints_full_story.jpg?fit=max\&auto=format\&n=-_xGPoyjhyiDWTPJ\&q=85\&s=a52016b2c44b57bd395d6e1eac47aa36)

## 持久可靠性模式

LangGraph 支持三种持久可靠性模式，让你在性能与数据一致性之间取得平衡。调用任何图执行方法时，都可以指定此模式：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
graph.stream(
    {"input": "test"},
    durability="sync"
)
```

以下模式按持久可靠性从低到高排列：

* `"exit"`：仅在图执行退出时持久化变更——无论正常完成、出错，还是因人工介入中断而退出。对长时间运行的图而言性能最佳，但不保存中间状态，因此无法在执行途中从系统故障（如进程崩溃）恢复。

* `"async"`：在下一步执行的同时异步持久化变更。性能和持久可靠性较好，但进程在执行期间崩溃时，仍有小概率未能写入检查点。

* `"sync"`：在下一步开始前同步持久化变更。这保证 LangGraph 写入每个检查点后才继续执行，持久可靠性高，但有一定性能开销。

### 新线程的首个持久检查点

对于新线程，持久可靠性模式还决定第一个用户节点执行前会提交哪些检查点。内部 `__start__` 超级步先运行；步骤 `0` 是该超级步之后写入的循环检查点。

* `"exit"`：直到运行结束才存在检查点。运行期间崩溃，将不会留下该线程的记录。

* `"async"`：在第一个用户节点执行前开始写入输入检查点，但不等待写入完成。首个用户节点可能在任何检查点提交之前就运行。

* `"sync"`：在第一个用户节点执行前，提交输入检查点（步骤 `-1`）和步骤 `0` 检查点。

> [!WARNING]
>
> 在任何模式下，若在首个检查点持久化完成前崩溃，线程就与从未被调用过的线程无法区分：两种情况下 `get_tuple()` 都返回 `None`，而 `invoke(None, config)` 会抛出 `EmptyInputError`。如果需要区分“从未接受”与“已接受但丢失”，请在检查点保存器之外记录请求受理情况，例如在调用 `invoke` 之前，先向自己的存储提交一条发件箱记录。

## 优化检查点存储

默认情况下，LangGraph 检查点会在每个超级步写入所有状态通道的完整值。对于累积大量数据的长生命周期线程（如多轮对话），存储量可能随时间显著增长。

[`DeltaChannel`](https://reference.langchain.com/python/langgraph/channels/delta/DeltaChannel) 只存储增量，而不是完整累积值，因此能显著缩小以追加为主的通道的检查点大小。用法及存储与延迟的权衡，见 [DeltaChannel](https://docs.langchain.com/oss/python/langgraph/pregel.md#deltachannel)。

> [!WARNING]
>
> `DeltaChannel` 需要 `langgraph>=1.2`，当前处于测试阶段。未来版本可能更改 API。

## 检查点保存器库

底层检查点保存由符合 [`BaseCheckpointSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.base.BaseCheckpointSaver) 接口的检查点保存器对象实现。LangGraph 提供多种实现，均以独立、可安装的库形式提供。

> [!NOTE]
>
> 可用提供商见[检查点保存器集成](https://docs.langchain.com/oss/python/integrations/checkpointers/index.md)。

* `langgraph-checkpoint`：检查点保存器的基础接口（[`BaseCheckpointSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.base.BaseCheckpointSaver)），以及序列化／反序列化接口（[`SerializerProtocol`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.serde.base.SerializerProtocol)）。包含供实验使用的内存检查点保存器实现（[`InMemorySaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.memory.InMemorySaver)）。LangGraph 已随附 `langgraph-checkpoint`。
* `langgraph-checkpoint-sqlite`：使用 SQLite 数据库的 LangGraph 检查点保存器实现（[`SqliteSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.sqlite.SqliteSaver) / [`AsyncSqliteSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver)）。适合实验和本地工作流，需要单独安装。
* `langgraph-checkpoint-postgres`：使用 Postgres 数据库的高级检查点保存器（[`PostgresSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.postgres.PostgresSaver) / [`AsyncPostgresSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.postgres.aio.AsyncPostgresSaver)），LangSmith 使用此实现。适合生产环境，需要单独安装。
* `langgraph-checkpoint-mongodb`：使用 MongoDB 的高级检查点保存器（`MongoDBSaver` / `AsyncMongoDBSaver`）。适合生产环境，需要单独安装。
* `langchain-azure-cosmosdb`：使用 Azure Cosmos DB for NoSQL 的 LangGraph 检查点保存器实现（[`CosmosDBSaverSync`](https://reference.langchain.com/python/langchain-azure-cosmosdb/) / [`CosmosDBSaver`](https://reference.langchain.com/python/langchain-azure-cosmosdb/)）。适合 Azure 生产环境，支持同步和异步操作以及 Microsoft Entra ID 认证。需要单独安装。

### 检查点保存器接口

每个检查点保存器都符合 [`BaseCheckpointSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.base.BaseCheckpointSaver) 接口，并实现以下方法：

* `.put`——存储检查点及其配置和元数据。
* `.put_writes`——存储与检查点关联的中间写入（即[待处理写入](#pending-writes)）。
* `.get_tuple`——根据给定配置（`thread_id` 和 `checkpoint_id`）获取检查点元组，用于填充 `graph.get_state()` 中的 `StateSnapshot`。
* `.list`——列出匹配给定配置和筛选条件的检查点，用于填充 `graph.get_state_history()` 的状态历史。传入 `config=None` 可跨所有线程列出检查点。参见[列出所有线程](#list-every-thread)。

若检查点保存器与异步图执行一起使用（即通过 `.ainvoke`、`.astream`、`.abatch` 执行图），则使用上述方法的异步版本（`.aput`、`.aput_writes`、`.aget_tuple`、`.alist`）。

> [!NOTE]
>
> 异步运行图时，可以使用 [`InMemorySaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.memory.InMemorySaver)，或 Sqlite／Postgres 检查点保存器的异步版本——[`AsyncSqliteSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver) / [`AsyncPostgresSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.postgres.aio.AsyncPostgresSaver)。

### 序列化器

检查点保存器保存图状态时，需要将状态中的通道值序列化。这由序列化器对象完成。

`langgraph_checkpoint` 定义了实现序列化器的[协议](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.serde.base.SerializerProtocol)，并提供默认实现（[`JsonPlusSerializer`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.serde.jsonplus.JsonPlusSerializer)），可处理多种类型，包括 LangChain 和 LangGraph 基础类型、日期时间、枚举等。

#### 使用 `pickle` 序列化

默认序列化器 [`JsonPlusSerializer`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.serde.jsonplus.JsonPlusSerializer) 底层使用 ormsgpack 和 JSON，并不适合所有对象类型。

对于 msgpack 编码器当前不支持的对象（例如 Pandas 数据帧），如果希望回退到 pickle，可以使用 [`JsonPlusSerializer`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.serde.jsonplus.JsonPlusSerializer) 的 `pickle_fallback` 参数：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# ... Define the graph ...
graph.compile(
    checkpointer=InMemorySaver(serde=JsonPlusSerializer(pickle_fallback=True))
)
```

#### 加密

检查点保存器可选择加密所有持久化状态。要启用加密，将 [`EncryptedSerializer`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.serde.encrypted.EncryptedSerializer) 实例传给任意 [`BaseCheckpointSaver`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.base.BaseCheckpointSaver) 实现的 `serde` 参数。创建加密序列化器最简单的方式是 [`from_pycryptodome_aes`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.serde.encrypted.EncryptedSerializer.from_pycryptodome_aes)：它从 `LANGGRAPH_AES_KEY` 环境变量读取 AES 密钥（也可接受 `key` 参数）：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
import sqlite3

from langgraph.checkpoint.serde.encrypted import EncryptedSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

serde = EncryptedSerializer.from_pycryptodome_aes()  # reads LANGGRAPH_AES_KEY
checkpointer = SqliteSaver(sqlite3.connect("checkpoint.db"), serde=serde)
```

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langgraph.checkpoint.serde.encrypted import EncryptedSerializer
from langgraph.checkpoint.postgres import PostgresSaver

serde = EncryptedSerializer.from_pycryptodome_aes()
checkpointer = PostgresSaver.from_conn_string("postgresql://...", serde=serde)
checkpointer.setup()
```

在 LangSmith 上运行时，只要存在 `LANGGRAPH_AES_KEY` 就会自动启用加密，因此只需提供该环境变量。若要使用其他加密方案，可实现 [`CipherProtocol`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.serde.base.CipherProtocol)，并将其提供给 [`EncryptedSerializer`](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.serde.encrypted.EncryptedSerializer)。

## 构建自定义检查点保存器

> [!TIP]
>
> 构建过程中，使用[一致性测试套件](#testing-with-the-conformance-suite)验证实现。它涵盖全部五个基础方法和包括增量通道在内的扩展能力。发布前请在 CI 中运行。

本节介绍如何为自定义存储后端从零实现 `BaseCheckpointSaver`。如果已有可用的检查点保存器，仅需添加增量通道支持，可跳至[增量通道支持](#delta-channel-support)。

### 概览

LangGraph 的持久化层基于两个存储抽象：

* **检查点表**——每个超级步一行；保存序列化后的图状态（`channel_values`、`channel_versions`、`versions_seen`），并链接到父检查点。
* **写入表**——超级步内每个节点输出一行；保存与检查点关联的 `(task_id, channel, value)` 元组。

检查点保存器管理这两个表。`put` 写入检查点行；`put_writes` 写入节点输出行；`get_tuple` 将两者读回 `CheckpointTuple`。

### 基础契约

继承 `BaseCheckpointSaver` 并实现以下五个方法。所有方法都是必需的；缺少任意基础方法都会在运行时抛出 `NotImplementedError`。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)

class MyCheckpointer(BaseCheckpointSaver):
    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        ...

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        ...

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        ...

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        ...
        yield  # make this an async generator

    async def adelete_thread(self, thread_id: str) -> None:
        ...
```

#### put / aput

存储一行检查点。返回包含已存储 `checkpoint_id` 的更新配置。

关键要求：

* 使用 `self.serde.dumps_typed(checkpoint)` 序列化检查点——它处理所有 LangGraph 原生类型，包括增量通道使用的 `_DeltaSnapshot` 数据块。
* 完整保存 `metadata`，不要删除未知键。LangGraph 会在次要版本中添加新的元数据字段（如增量通道使用的 `counters_since_delta_snapshot`）；丢弃它们会使功能在没有报错的情况下失效。
* 将 `config["configurable"].get("checkpoint_id")` 保存为父检查点 ID，以便 `get_tuple` 填充 `parent_config`。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
async def aput(self, config, checkpoint, metadata, new_versions):
    thread_id = config["configurable"]["thread_id"]
    checkpoint_ns = config["configurable"]["checkpoint_ns"]
    checkpoint_id = checkpoint["id"]
    parent_id = config["configurable"].get("checkpoint_id")

    type_, blob = self.serde.dumps_typed(checkpoint)
    serialized_metadata = self.serde.dumps_typed(metadata)

    await self.db.execute(
        "INSERT INTO checkpoints (...) VALUES (...)",
        thread_id, checkpoint_ns, checkpoint_id, parent_id,
        type_, blob, *serialized_metadata,
    )
    return {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": checkpoint_id,
        }
    }
```

#### put\_writes / aput\_writes

存储当前超级步中单个任务的节点输出行。这些行通过 `(thread_id, checkpoint_ns, checkpoint_id)` 与检查点关联。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
async def aput_writes(self, config, writes, task_id, task_path=""):
    thread_id = config["configurable"]["thread_id"]
    checkpoint_ns = config["configurable"]["checkpoint_ns"]
    checkpoint_id = config["configurable"]["checkpoint_id"]

    rows = []
    for idx, (channel, value) in enumerate(writes):
        type_, blob = self.serde.dumps_typed(value)
        final_idx = WRITES_IDX_MAP.get(channel, idx)
        rows.append((thread_id, checkpoint_ns, checkpoint_id,
                      task_id, task_path, final_idx, channel, type_, blob))

    await self.db.executemany("INSERT INTO writes (...) VALUES (...)", rows)
```

从 `langgraph.checkpoint.base` 导入 `WRITES_IDX_MAP`。它将特殊通道（`__error__`、`__interrupt__` 等）映射到保留的负索引，防止与常规写入索引冲突。

#### get\_tuple / aget\_tuple

获取一个检查点。配置可以包含：

* **不提供 `checkpoint_id`**——返回线程与命名空间下的最新检查点。
* **提供特定 `checkpoint_id`**——返回该精确检查点。

**两条路径都必须正确工作。**指定 ID 的路径用于时间旅行；更关键的是，它还在每次图调用时用于重建增量通道状态（见[增量通道支持](#delta-channel-support)）。指定 ID 的查询出错会无声地破坏增量通道状态。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
async def aget_tuple(self, config):
    thread_id = config["configurable"]["thread_id"]
    checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
    checkpoint_id = config["configurable"].get("checkpoint_id")

    if checkpoint_id:
        row = await self.db.fetchone(
            "SELECT * FROM checkpoints "
            "WHERE thread_id=? AND checkpoint_ns=? AND checkpoint_id=?",
            thread_id, checkpoint_ns, checkpoint_id,
        )
    else:
        row = await self.db.fetchone(
            "SELECT * FROM checkpoints "
            "WHERE thread_id=? AND checkpoint_ns=? "
            "ORDER BY checkpoint_id DESC LIMIT 1",
            thread_id, checkpoint_ns,
        )

    if row is None:
        return None

    writes = await self.db.fetchall(
        "SELECT task_id, channel, type, value FROM writes "
        "WHERE thread_id=? AND checkpoint_ns=? AND checkpoint_id=? "
        "ORDER BY task_id, idx",
        thread_id, checkpoint_ns, row["checkpoint_id"],
    )
    pending_writes = [
        (w["task_id"], w["channel"], self.serde.loads_typed((w["type"], w["value"])))
        for w in writes
    ]

    checkpoint = self.serde.loads_typed((row["type"], row["blob"]))
    metadata = self.serde.loads_typed((row["metadata_type"], row["metadata"]))

    parent_config = None
    if row["parent_checkpoint_id"]:
        parent_config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": row["parent_checkpoint_id"],
            }
        }

    return CheckpointTuple(
        config={
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": row["checkpoint_id"],
            }
        },
        checkpoint=checkpoint,
        metadata=metadata,
        parent_config=parent_config,
        pending_writes=pending_writes,
    )
```

> [!WARNING]
>
> **指定 ID 查询的正确性取决于行键／索引设计。**如果存储使用不包含 `checkpoint_id` 的时间排序键（如反向时间戳），就无法按 ID 直接读取行。必须将 `checkpoint_id` 编码到行键中，或建立辅助索引。每次查询都扫描并按值筛选虽能工作，但无法良好扩展。

#### list / alist

返回某线程的检查点，最新的在前。遵循 `before`（只返回早于该配置 `checkpoint_id` 的检查点）和 `limit`。

#### delete\_thread / adelete\_thread

删除某线程的全部检查点和写入。检查点行与写入行都必须删除。

### 行键／索引设计

检查点的存储和索引方式直接影响正确性与性能。

**推荐模式（SQL）：**

```sql theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
CREATE TABLE checkpoints (
    thread_id          TEXT NOT NULL,
    checkpoint_ns      TEXT NOT NULL DEFAULT '',
    checkpoint_id      TEXT NOT NULL,   -- ULID, lexicographically sortable newest-last
    parent_checkpoint_id TEXT,
    type               TEXT,
    checkpoint         BYTEA,
    metadata           JSONB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

CREATE TABLE writes (
    thread_id     TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id       TEXT NOT NULL,
    task_path     TEXT NOT NULL DEFAULT '',
    idx           INTEGER NOT NULL,
    channel       TEXT NOT NULL,
    type          TEXT,
    value         BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, task_path, idx)
);
```

由于 `checkpoint_id` 是 ULID，可以按字典序排序——值越大，时间越新。“获取最新”使用 `ORDER BY checkpoint_id DESC LIMIT 1`；“按 ID 获取”则按主键等值查询。

**非 SQL 存储：**遵循相同原则。无论使用何种键方案，按 `(thread_id, checkpoint_ns, checkpoint_id)` 直接查询都必须达到 O(1) 或接近的复杂度。避免采用只能扫描线程所有行才能按 ID 找到检查点的设计。

### 序列化

对检查点、写入和元数据，始终使用 `self.serde`（继承自 `BaseCheckpointSaver`，默认为 `JsonPlusSerializer`）。不要直接使用 `pickle` 处理元数据——虽能工作，但 `JsonPlusSerializer` 输出人类可读，版本处理也更好。

`JsonPlusSerializer` 自动处理所有 LangGraph 原生类型：

* `_DeltaSnapshot`——增量通道使用的哨兵数据块（msgpack 扩展代码 7）
* Pydantic v2 模型、数据类、numpy 数组、日期时间、枚举等

若编写自定义序列化器，确保能够对 `langgraph.checkpoint.serde.types` 中的 `_DeltaSnapshot` 进行正确的序列化与反序列化往返。

### 扩展能力

这些方法是可选的，但能启用额外的 Agent Server 功能。如果存储后端能够高效支持，就实现它们。

| 方法 | 启用的功能 |
| - | - |
| `adelete_for_runs` | 回滚多任务策略 |
| `acopy_thread` | 高效线程分叉 |
| `aprune` | 线程历史清理 |
| `aget_delta_channel_history` | 高效重建增量通道状态（见下文） |

Agent Server 在启动时自动检测检查点保存器实现了哪些能力，并启用对应功能。

### 增量通道支持

> [!NOTE]
>
> **DeltaChannel 处于测试阶段。**设计稳定之前，API 和磁盘表示格式可能变化。

`DeltaChannel` 是一种归约通道，在检查点数据块中仅保存哨兵值（`MISSING`），而不是完整通道值。状态通过归约函数重放祖先写入来重建。对于 `messages` 等随时间累积的通道，每步检查点数据块的大小由 O(N) 降为 O(1)。

#### 运行时需要什么

加载某个检查点时，如果其增量通道未包含在 `channel_values` 中，LangGraph 会调用 `saver.get_delta_channel_history(config=config, channels=[...])`。对于每个通道，返回：

* **`writes`**——祖先链中该通道的全部写入，最早的在前，追溯到最近的快照为止。
* **`seed`**（可选）——最近一个具有快照的祖先中存储的 `_DeltaSnapshot` 数据块；若一直遍历到根仍未找到快照，则不存在该项。

之后运行时调用 `channel.from_checkpoint(seed)` 和 `channel.replay_writes(writes)` 重建当前值。

#### 默认实现

`BaseCheckpointSaver` 提供默认的 `get_delta_channel_history`，可与任何正确的 `get_tuple` 实现配合使用：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
# Simplified from BaseCheckpointSaver
def get_delta_channel_history(self, *, config, channels):
    target = self.get_tuple(config)          # load the head checkpoint
    cursor = target.parent_config            # walk from its parent
    collected = {ch: [] for ch in channels}
    seed = {}
    remaining = set(channels)

    while cursor and remaining:
        tup = self.get_tuple(cursor)         # ← requires correct by-id lookup
        if tup is None:
            break
        for write in reversed(tup.pending_writes or []):
            if write[1] in remaining:
                collected[write[1]].append(write)
        for ch in list(remaining):
            if ch in tup.checkpoint["channel_values"]:
                seed[ch] = tup.checkpoint["channel_values"][ch]
                remaining.discard(ch)
        cursor = tup.parent_config

    return {
        ch: {"writes": list(reversed(collected[ch])), **({"seed": seed[ch]} if ch in seed else {})}
        for ch in channels
    }
```

**关键依赖：**调用 `get_tuple(cursor)` 时始终指定特定 `checkpoint_id`（父检查点的 ID）。如果该查询返回 `None`，遍历立即停止，所有增量通道都会无声地重建为空，不会报错。因此，`get_tuple` 中按特定 ID 查询的路径必须正确。

#### 性能优化重写

默认遍历会为每个祖先检查点发起一次 `get_tuple` 调用。对于查询能力较好的后端，可重写 `get_delta_channel_history`（及其异步版本），用两次查询获取祖先链与写入：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
async def aget_delta_channel_history(self, *, config, channels):
    if not channels:
        return {}

    thread_id = config["configurable"]["thread_id"]
    checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
    checkpoint_id = config["configurable"]["checkpoint_id"]

    # Stage 1: stream ancestors newest-first until every channel has a seed
    ancestors = await self.db.fetchall(
        "SELECT checkpoint_id, parent_checkpoint_id, type, checkpoint "
        "FROM checkpoints "
        "WHERE thread_id=? AND checkpoint_ns=? AND checkpoint_id < ? "
        "ORDER BY checkpoint_id DESC",
        thread_id, checkpoint_ns, checkpoint_id,
    )

    chain_by_ch: dict[str, list[str]] = {ch: [] for ch in channels}
    seed_by_ch: dict[str, Any] = {}
    remaining = set(channels)
    cur_id = config["configurable"]["checkpoint_id"]

    for row in ancestors:
        if not remaining:
            break
        parent_id = row["parent_checkpoint_id"]
        ckpt = self.serde.loads_typed((row["type"], row["checkpoint"]))
        cv = ckpt.get("channel_values") or {}
        for ch in list(remaining):
            chain_by_ch[ch].append(row["checkpoint_id"])
            if ch in cv:
                seed_by_ch[ch] = cv[ch]
                remaining.discard(ch)
        cur_id = parent_id

    # Stage 2: fetch writes for each channel's ancestor chain in one query
    result: dict[str, DeltaChannelHistory] = {}
    for ch in channels:
        chain = chain_by_ch[ch]
        if not chain:
            entry: DeltaChannelHistory = {"writes": []}
            if ch in seed_by_ch:
                entry["seed"] = seed_by_ch[ch]
            result[ch] = entry
            continue

        write_rows = await self.db.fetchall(
            f"SELECT checkpoint_id, task_id, idx, type, value FROM writes "
            f"WHERE thread_id=? AND checkpoint_ns=? AND channel=? "
            f"AND checkpoint_id IN ({','.join('?' * len(chain))})"
            f"ORDER BY checkpoint_id, task_id, idx",
            thread_id, checkpoint_ns, ch, *chain,
        )
        writes_by_cid: dict[str, list[PendingWrite]] = {}
        for row in write_rows:
            cid = row["checkpoint_id"]
            value = self.serde.loads_typed((row["type"], row["value"]))
            writes_by_cid.setdefault(cid, []).append((row["task_id"], ch, value))

        # chain is newest-first; iterate oldest-first to get correct replay order
        collected: list[PendingWrite] = []
        for cid in reversed(chain):
            collected.extend(writes_by_cid.get(cid, []))

        entry = {"writes": collected}
        if ch in seed_by_ch:
            entry["seed"] = seed_by_ch[ch]
        result[ch] = entry

    return result
```

#### 增量通道的清理

`DeltaChannel` 状态并非完整包含于单个检查点中，而是依赖从当前检查点向前到最近 `_DeltaSnapshot` 的祖先写入链。若实现 `prune` 或 `delete_for_runs`，不得删除仍被保留检查点的增量通道所依赖的写入行。

安全选项：

1. **先遍历，再清理**——对于每个计划保留的检查点，遍历祖先链，将到最近 `_DeltaSnapshot` 为止的所有写入行标记为不可删除。
2. **清理前强制创建快照**——在要保留的检查点中重写 `channel_values[ch] = _DeltaSnapshot(reconstructed_value)`，然后即可自由删除祖先。
3. **对含增量通道的线程跳过清理**——若尚不需要清理，这是短期内最安全的选项。

#### 复制含增量通道的线程

实现 `copy_thread` 时，要复制完整祖先链，而不只是最新检查点。对于每个增量通道，目标线程都必须拥有至少追溯到一个 `_DeltaSnapshot` 的写入行，否则这些通道在复制后会重建为空。

### 使用一致性测试套件测试

`langgraph-checkpoint-conformance` 按完整契约验证实现，包括增量通道历史：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
pip install langgraph-checkpoint-conformance
```

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
import asyncio
from langgraph.checkpoint.conformance import checkpointer_test, validate

@checkpointer_test(name="MyCheckpointer")
async def my_checkpointer():
    async with MyCheckpointer.create() as saver:
        yield saver

async def main():
    report = await validate(my_checkpointer)
    report.print_report()
    # Fails the process if any base capability is missing or broken
    if not report.passed_all_base():
        raise RuntimeError("Checkpointer failed conformance suite")

asyncio.run(main())
```

测试套件自动检测检查点保存器实现了哪些扩展能力（包括 `aget_delta_channel_history`），并为每项能力运行相应测试。发布前应将其作为 CI 的一部分运行。

***

[连接这些文档](https://docs.langchain.com/use-these-docs.md) ，通过 MCP 将其接入你选择的智能体，以获取实时答案。

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/langgraph/checkpointers.mdx) 或[提交问题](https://github.com/langchain-ai/docs/issues/new/choose).
