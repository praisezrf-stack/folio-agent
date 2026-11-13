"""
素材已就位：data/corpus/langgraph-core-concepts.md。照指南文档 §2 写 src/scripts/ingest.py：

读文件 → 标题感知切片：按 ## 标题边界切，单块超 1200 字符再按段落二次切，代码块（``` 围栏）绝不能拦腰切断——这份文档 8 个章节 + 7 个代码块，正好是实战
幂等：先 DELETE FROM documents WHERE filename = %s（外键级联会清掉 chunks）再插，重跑不翻倍
验收：入库后 10~20 个 chunk；然后拿指南里那 4 个测试查询跑检索——特别是 怎么让模型决定要不要调用工具？（问题用词和文档完全不同，还能命中“工具调用循环”章节才算过关）和 怎么实现人工审核后再执行？
写完把 chunk 切分结果（每块的字数和所属章节）和检索输出贴我。这一步过了，⑤ 就只是“循环调 ingest 灌全量 + 写 ask.py”了。
"""

from folioAgent.rag.parser import parser
from folioAgent.rag.splitter import splitter_loader
from folioAgent.db.ingestion_repository import save_chunks, save_doc
from folioAgent.db.store import get_db_connect


def parse_doc():
    with get_db_connect() as conn:
        document_id = save_doc(conn)
        print("=== 文档存储完成 ===")
    # 解析文档并切片
    content_list: list = parser()
    print(f"=== 文件解析完成 ===")
    # 存储文档

    for content in content_list:
        title, embedded_chunks = splitter_loader(content["content"])
        data = [
            (
                document_id,
                chunk["chunk_content"],
                str(chunk["vector"]),
                index,
            )
            for index, chunk in enumerate(embedded_chunks)
        ]
        # 存储chunk
        with get_db_connect() as conn:
            save_chunks(conn, data)


if __name__ == "__main__":
    parse_doc()


[
    '# **LangGraph 核心概念入门**\n\nLangGraph 是一个用于构建有状态、多角色 AI 应用的底层编排框架。它把 Agent 的运行过程建模为一张"图"（Graph）：节点（Node）负责执行具体逻辑，边（Edge）决定执行顺序，状态（State）在整个图中流转。与传统的链式调用（Chain）相比，LangGraph 最显著的特点是支持循环、分支和持久化，因此特别适合构建需要多轮工具调用、人工介入或复杂决策的 Agent 应用。\n\n## **StateGraph 与状态定义**\n\nStateGraph 是 LangGraph 的核心类，一切编排都从创建一张 StateGraph 开始。定义图的第一步是声明状态的结构——状态通常是一个 TypedDict 或 Pydantic 模型，其中最重要的字段是 messages，用于累积对话历史。\n\n## **StateGraph 与状态定义**\n\nfrom typing import Annotated\n\nfrom typing\\_extensions import TypedDict\n\nfrom langgraph.graph.message import add\\_messages\n\nclass State(TypedDict):\n\nmessages: Annotated[list, add\\_messages]\n\n这里的 Annotated[list, add\\_messages] 有特殊含义：add\\_messages 是一个 reducer（归约函数），规定"新消息如何合并进旧消息"。没有 reducer 的字段会被直接覆盖，有 reducer 的字段则按函数定义的方式追加。这个设计让"累积对话历史"这种最常见的操作变成了声明式配置。\n\n状态（State）是整个图的单一数据源：每个节点接收当前状态、返回对状态的局部更新，框架负责把更新合并回全局状态。理解了"节点只做局部更新"，就理解了 LangGraph 的编程模型。\n\nStateGraph 是 LangGraph 的核心类，一切编排都从创建一张 StateGraph 开始。定义图的第一步是声明状态的结构——状态通常是一个 TypedDict 或 Pydantic 模型，其中最重要的字段是 messages，用于累积对话历史。\n\n## **节点与边**\n\n节点是图中的执行单元，本质就是一个接收 State、返回状态更新的 Python 函数。节点内部可以做任何事：调用大模型、执行工具、访问数据库、请求人工输入。\n\nfrom langgraph.graph import StateGraph, START, END\n\ndef chatbot(state: State):\n\nreturn {"messages": [model.invoke(state["messages"])]}\n\ngraph = StateGraph(State)\n\ngraph.add\\_node("chatbot", chatbot)\n\ngraph.add\\_edge(START, "chatbot")\n\ngraph.add\\_edge("chatbot", END)\n\n边定义了节点之间的走向。普通边（add\\_edge）是固定的直线连接；条件边（add\\_conditional\\_edges）则根据当前状态动态决定下一个节点，这是实现"模型决定要不要调工具"这类分支逻辑的关键机制。\n\ndef should\\_continue(state: State):\n\nlast = state["messages"][-1]\n\nif last.tool\\_calls:\n\nreturn "tools"\n\nreturn END\n\ngraph.add\\_conditional\\_edges("chatbot", should\\_continue)\n\n编译图之后即可执行：graph.invoke({"messages": [...]}) 会从 START 出发，沿边流转，直到到达 END。执行过程中每一步的状态变化都可以通过 stream 模式实时观察，这也是调试复杂 Agent 的主要手段。\n\n## **工具调用循环**\n\nAgent 的经典形态是"模型-工具循环"：模型阅读对话历史，要么直接回答，要么发起工具调用（tool call）；工具结果作为新消息追加进状态，再次送回模型，如此往复，直到模型给出最终回答。在 LangGraph 中，这个循环由两部分组成：chatbot 节点负责模型推理，tools 节点负责实际执行工具，两者之间用条件边连接。\n\nfrom langgraph.prebuilt import ToolNode\n\ntool\\_node = ToolNode([get\\_weather, search\\_docs])\n\ngraph.add\\_node("tools", tool\\_node)\n\ngraph.add\\_conditional\\_edges("tools", lambda \\_: "chatbot")\n\nToolNode 是内置的批量工具执行节点：它读取最新消息里的 tool\\_calls，逐个执行，并把结果以 ToolMessage 的形式写回状态。循环必须有终止条件，否则模型可能无限次调用工具——常见的做法是在条件边里判断连续工具调用次数，超过上限强制走向 END。\n\n## **记忆与 Checkpointing**\n\nLangGraph 的持久化能力由 Checkpointer 提供。给图配置一个 checkpointer（如内存版 InMemorySaver 或生产级的 PostgresSaver）后，每个超级步（superstep）结束时完整状态都会被写入存储，从而带来两个关键能力。\n\n第一是多轮记忆：每个会话用一个 thread\\_id 标识，同一 thread 的多次 invoke 自动接续之前的对话历史，无需手动拼接消息列表。\n\nfrom langgraph.checkpoint.memory import InMemorySaver\n\ncheckpointer = InMemorySaver()\n\napp = graph.compile(checkpointer=checkpointer)\n\nconfig = {"configurable": {"thread\\_id": "user-42"}}\n\napp.invoke({"messages": [("user", "我叫小方")]}, config)\n\napp.invoke({"messages": [("user", "我叫什么？")]}, config)  # 模型能答出"小方"\n\n第二是时间旅行（Time Travel）：因为每个历史状态都被保存，可以回退到任意检查点、从那里重新执行，这对调试和做"假如当时换一种回答"的对比实验非常有用。\n\n## **人机协同（Human-in-the-loop）**\n\n企业场景中某些操作风险高（删数据、转账、发邮件），需要人工确认后才能执行。LangGraph 通过 interrupt 机制实现：在图执行到关键节点前暂停，把状态落盘，等待人工审核；人工批准后用 Command 恢复执行。\n\nfrom langgraph.types import interrupt, Command\n\ndef dangerous\\_action(state: State):\n\ndecision = interrupt({"action": state["pending\\_action"]})\n\nif decision["approved"]:\n\nreturn {"result": "已执行"}\n\nreturn {"result": "已取消"}\n\ninterrupt 与 checkpointer 配合工作：暂停点本身就是检查点，所以恢复时框架能精确接上之前的执行位置。这是 LangGraph 区别于简单链式框架的最大优势之一——长流程、可中断、可恢复。\n\n## **子图与多 Agent**\n\n当应用变大，可以把一张图作为另一个图的节点，即子图（Subgraph）。子图拥有独立的状态结构，通过输入输出的映射与父图衔接。多 Agent 架构通常就建立在子图之上：每个 Agent 是一张自带工具与提示词的小图，由一个"监督者"（Supervisor）节点根据任务动态路由给合适的 Agent，形成 supervisor 模式；或者各 Agent 之间按需互相移交控制权，形成 swarm 模式。\n\n子图的常见坑是状态结构不一致导致的键丢失：父图传给子图的字段，子图 State 里必须有对应定义，否则数据会被静默丢弃。调试多 Agent 系统时，先检查各层 State 定义是否对齐，往往比检查提示词更有效。\n\n## **流式输出**\n\nLangGraph 原生支持流式输出，gradio 或 Web 前端常用的体验（逐字上屏）依赖它。stream 模式有三种主要取值：values（每步输出完整状态）、updates（每步只输出增量）、messages（逐 token 输出模型文本）。构建聊天界面时通常组合使用 messages 流式呈现回答、updates 流式展示工具调用轨迹。\n\nfor chunk in app.stream({"messages": [...]}, config, stream\\_mode="messages"):\n\nchunk.pretty\\_print()\n\n流式能力与 checkpointer 正交，可以同时开启。生产环境中，后端服务通常把 LangGraph 的流式事件转换成 SSE 推给前端，这也是大多数 Agent 产品"打字机效果 + 工具过程折叠"的实现原理。\n\n## **常见错误与调试**\n\n初学者最常见的五类错误：一是忘记编译，add\\_node 之后必须 compile 才能调用；二是状态字段缺少 reducer，导致 messages 被覆盖而不是追加；三是工具循环没有终止条件，token 消耗失控；四是 checkpointer 的 thread\\_id 不传或多会话混用，造成"记忆串台"；五是子图与父图的状态键不一致，数据静默丢失。\n\n调试推荐顺序：先用 stream\\_mode="updates" 观察每个节点的实际输入输出；再检查 State 定义与 reducer；最后才考虑改提示词。绝大多数"模型不听话"的问题，根源都在状态流转而非提示词本身。'
]
