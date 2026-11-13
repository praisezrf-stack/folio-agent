# Agent 工作流与 RAG 入库实战指南

> 测试文档版本：1.0  
> 用途：验证 Markdown 标题感知切片、超过 1200 字符的二次切片、代码围栏保护、向量检索及重复入库。

## 01. Agent 的组成和执行入口

Agent 并不等于一段很长的提示词。一个可运行的 Agent 通常包含模型、状态、工具和控制流程：模型负责理解任务和决定下一步，状态负责保存当前运行所需的信息，工具负责访问外部能力，而控制流程负责决定什么时候继续、等待或结束。对于简单的问答任务，模型可能不需要使用工具；对于需要查找资料、计算或查询数据库的任务，系统需要明确允许模型调用哪些工具，并对每次调用的结果进行校验。

在工程实现中，“Agent 能回答什么”与“Agent 能执行什么”是两个不同的问题。模型能够在文本中写出 SQL，并不代表它已经执行了 SQL；模型能够描述天气，也不代表它已经读取最新气象数据。只有在工具真正被调用并返回结果以后，程序才能把这些结果作为已观察到的事实。

本节用于测试一个较短的章节是否会被保留为独立 Chunk，而不是被错误地丢弃。

## 02. 状态模型与节点传递

一个工作流需要明确约定状态结构。状态可以包含用户问题、检索结果、工具执行记录、当前轮次、是否需要人工审核以及最终答案。节点读取已有状态，产生需要更新的字段；在存在并行执行的情况下，不同节点对同一个字段的更新还可能需要合并规则。

下面是一个简化的 Python 状态定义，它展示了为什么要将“用户问题”和“运行记录”分开放置。代码主要用于说明结构，并非完整的 LangGraph 项目。

```python
from typing import TypedDict

class AgentState(TypedDict):
    question: str
    tool_required: bool
    tool_name: str | None
    observations: list[str]
    answer: str


def init_state(question: str) -> AgentState:
    return {
        "question": question,
        "tool_required": False,
        "tool_name": None,
        "observations": [],
        "answer": "",
    }
```

当一次执行恢复时，程序应该依据保存的状态继续，而不是在没有检查的情况下重新执行已经完成的外部副作用。比如一个“发送邮件”节点被再次调用，可能造成邮件重复发送。设计者通常需要给这类副作用设置唯一请求标识或业务幂等键。

## 03. 工具调用决策：模型怎样选择是否使用外部能力

在工具调用循环中，模型首先读取用户输入与已有上下文，再判断当前信息是否足以直接回答。如果答案依赖实时信息、私有数据库、文件系统或精确计算，模型可以生成结构化的工具调用请求；如果现有上下文已经充分，则可以直接生成最终答案。这个过程并不是程序简单地通过关键词寻找“工具”两个字，而是根据任务目标、可用工具说明和模型输出进行路由。

例如，用户问“公司上周有多少条新工单”，模型不能凭空猜一个数字。它应先选择查询工单的工具，接收结果，再组织最终回复。用户问“什么是工单”，往往不需要访问外部系统。工具选择权可以交给模型，但应用程序仍需限制工具名单、参数格式、权限范围、超时和最多调用次数。模型提出调用意图，不等于已经获得无限权限。

为了验证检索效果，知识库检索问题可以故意写成“怎么让模型决定要不要调用工具？”。虽然这句提问没有复述本节标题“工具调用决策”，但理想情况下应该检索到这里，而不是仅靠字面关键词命中其他章节。

下面这个示例特意写得比较长，**完整的代码围栏超过 500 字符**。你的切片器如果仅按长度切割，可能会在三反引号围栏中间拆开代码；测试要求是保留整个代码块，必要时允许单个 Chunk 大于 500 字符。

```python
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Callable[[dict[str, Any]], Any]

@dataclass
class ToolDecision:
    need_tool: bool
    tool_name: str | None
    arguments: dict[str, Any]
    reason: str


def validate_decision(decision: ToolDecision, tools: dict[str, ToolSpec]) -> None:
    if not decision.need_tool:
        if decision.tool_name is not None:
            raise ValueError("不调用工具时不应指定 tool_name")
        return
    if not decision.tool_name:
        raise ValueError("要求调用工具时必须填写工具名")
    if decision.tool_name not in tools:
        raise ValueError(f"工具不在白名单内: {decision.tool_name}")
    if not isinstance(decision.arguments, dict):
        raise TypeError("工具参数必须是字典")


def execute_tool_decision(
    decision: ToolDecision,
    tools: dict[str, ToolSpec],
    max_attempts: int = 2,
) -> dict[str, Any]:
    validate_decision(decision, tools)
    if not decision.need_tool:
        return {"status": "skipped", "result": None, "reason": decision.reason}

    tool = tools[decision.tool_name]
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = tool.handler(decision.arguments)
            return {
                "status": "success",
                "tool": tool.name,
                "attempt": attempt,
                "result": result,
                "reason": decision.reason,
            }
        except (TimeoutError, ConnectionError) as exc:
            last_error = exc
    return {
        "status": "failed",
        "tool": tool.name,
        "error": str(last_error),
        "reason": decision.reason,
    }
```

代码里做了四件事：确认模型是否真的要求使用工具，检查工具是否在允许名单中，验证参数的基础结构，最后执行并记录结果。生产环境还需要更加严格的参数模式校验、权限控制和副作用重试策略，尤其不能在不具备幂等保障时随意重试付款、发布和删除操作。

一个经常出现的误解是“模型决定调用工具，就必须立刻执行”。实际上应用层可以先暂停、拒绝或改写请求，也可以要求人工审核。模型的决定仅是一项请求，应用程序才是最终的执行者。这条界限对安全性和可追溯性尤其重要。

## 04. 工具调用循环与终止条件

工具调用并不总是一次结束。一个典型循环是：模型作出下一步决策、执行工具、观察工具返回值、将观察值加入状态、再由模型判断继续调用还是给出最终答案。假如工具返回“没有找到”，模型可能换一个检索条件；如果工具返回足够的信息，模型就可以结束循环。系统必须设置最大步骤数或超时，防止模型在相同工具之间无限往返。

```python
def run_loop(model_step, tool_runner, initial_state, max_steps=5):
    state = initial_state
    for step in range(max_steps):
        decision = model_step(state)
        if decision["action"] == "final":
            return decision["answer"]
        if decision["action"] != "tool":
            raise ValueError("未知决策类型")
        observation = tool_runner(decision["tool"], decision["args"])
        state["observations"].append(observation)
    raise RuntimeError("超过最大执行步数，需要人工检查")
```

判断是否停止的依据不能仅仅是模型说“我完成了”。对于数据库写入、文件发布等任务，还应有可检验的完成条件，例如写入条数、返回的记录 ID、目标文件是否存在，以及操作是否已经提交事务。

## 05. 人工审核与执行前中断

人工审核适合有明显外部后果的操作：发送邮件、公开发布帖子、删除文件、修改权限或发起支付。在真正执行工具之前，系统可以先保存待执行的动作与参数，并将工作流暂停。审核人员确认之后，程序再读取审核决定，决定继续执行、修改参数或取消。这类模式通常称为 Human-in-the-loop（人在回路中）。

在 LangGraph 场景里，可以用中断机制暂停流程，并在获得审核结果后通过恢复命令继续。提问“怎么实现人工审核后再执行？”应该能够检索到本节，即使用户并没有在问题里写出 `interrupt` 或 `Command`。

```python
from langgraph.types import interrupt, Command


def approval_node(state):
    review = interrupt({
        "operation": state["pending_operation"],
        "arguments": state["pending_arguments"],
        "message": "请审核后决定是否执行",
    })
    if not review.get("approved", False):
        return {"status": "rejected"}
    return {"status": "approved"}

# 演示概念：调用方需要为图配置 checkpointer 和 thread_id。
# graph.invoke(Command(resume={"approved": True}), config=config)
```

人工审核的重点不只是弹出一个“确认”按钮，而是要确保被审核的参数与随后实际执行的参数一致。审核通过以后，如果系统又暗中修改了目标地址或权限范围，原先的审核就失去了意义。对于审核已经拒绝的动作，也不应在恢复运行时自动重试。

## 06. 检查点、恢复与重复执行保护

长任务可能经历模型超时、进程重启、人工等待或网络中断。检查点可以保存工作流某一时刻的状态，让下一次执行有机会从已保存的位置恢复。一个检查点一般与会话或线程标识关联；多个检查点表示不同执行时刻的快照，不等于多个用户，也不意味着存储了多份完整业务文档。

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

builder = StateGraph(AgentState)
# 根据实际节点补充 add_node() / add_edge() 后再 compile。
# 这里仅演示 checkpointer 的配置位置。
checkpointer = InMemorySaver()
# graph = builder.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "demo-thread-001"}}
```

需要特别注意，检查点能够帮助恢复状态，却不自动确保所有外部副作用只执行一次。例如某个节点先调用外部支付接口成功，随后进程崩溃而没有记录成功状态，恢复后如果再次执行同样调用，就可能造成重复付款。这时需要业务幂等键、操作记录和必要的人工核查，而不能只依赖状态快照。

## 07. 向量检索、相似度与来源引用

RAG 的入库阶段把文档切成多个 Chunk，再使用 Embedding 模型把文本映射为向量。提问阶段必须使用兼容的向量模型处理问题，然后根据距离或相似度检索相关 Chunk。检索到的内容只是候选证据，最终回答还要判断证据是否充分、是否来自用户有权限查看的文档，以及是否需要明确指出无法确定的部分。

PostgreSQL 的 pgvector 扩展支持余弦距离查询。对于已有 chunks 和 documents 两张表的知识库，可以从数据库读取文本、来源与相似度排序结果。下面的 SQL 只是示例，查询参数必须使用驱动的参数绑定方式传入。

```sql
SELECT
    c.id,
    c.document_id,
    c.chunk_index,
    c.content,
    d.filename,
    c.embedding <=> %s AS cosine_distance
FROM chunks AS c
JOIN documents AS d ON d.id = c.document_id
ORDER BY c.embedding <=> %s
LIMIT 5;
```

当问题的措辞和文档标题完全不同，向量检索仍可能找到语义相关的章节，但不能保证一定正确。测试时不仅要看“能否返回结果”，还要检查正确章节是否进入 Top-K、错误结果是否被排除，以及答案是否能引用对应文档和 Chunk。

## 08. 文档重新入库、事务与错误处理

重复导入同一个文件时，系统需要明确“同一份文档”的判定标准。单用户本地实验可以使用稳定的 source_path 识别文档，删除旧 documents 记录时利用 ON DELETE CASCADE 清理旧 chunks，然后插入新 documents 与新 chunks。真实产品还可能需要区分不同用户、不同知识库、文件版本和内容哈希。

为了防止旧内容被删掉而新 Chunk 还没插入，删除旧文档、插入新文档和写入新 Chunk 应使用同一个数据库事务。解析 PDF、切片和调用 Embedding 服务可能耗时较久，通常应该先完成这些外部处理，再开启较短的数据库写入事务。

```python
import psycopg


def persist_one_document(dsn, filename, source_path, chunks):
    if not chunks:
        raise ValueError("拒绝用空切片覆盖已有文档")
    # 以下演示事务边界；真实代码需按数据库实际字段准备参数。
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE source_path = %s", (source_path,))
            cur.execute(
                "INSERT INTO documents (filename, source_path) VALUES (%s, %s) RETURNING id",
                (filename, source_path),
            )
            document_id = cur.fetchone()[0]
            rows = [
                (document_id, item["content"], item["embedding"], i)
                for i, item in enumerate(chunks)
            ]
            cur.executemany(
                "INSERT INTO chunks (document_id, content, embedding, chunk_index) VALUES (%s, %s, %s, %s)",
                rows,
            )
    return document_id
```

验收不能只看程序没有报错。应该检查每份文档对应的 Chunk 条数、顺序、文本长度、向量维度，以及重复运行之后文档数和 Chunk 数是否翻倍。还应人为制造一次写入失败，确认数据库事务回滚后旧数据仍然存在。文件系统或对象存储里的实际文件不属于 PostgreSQL 事务，不能假设数据库回滚就会自动撤销外部上传。
