<!--
Source-URL: https://docs.langchain.com/oss/python/langchain/models.md
HTML-URL: https://docs.langchain.com/oss/python/langchain/models
Downloaded: 2026-11-16 19:21:15 Asia/Shanghai
Original-Language: English
-->

> ## 文档索引
> 完整文档索引：https://docs.langchain.com/llms.txt
> 在进一步阅读之前，可使用此文件发现所有可用页面。

# 模型

> 初始化和配置作为 LangChain 智能体推理引擎的聊天模型，支持工具调用、结构化输出和多模态输入。

[大语言模型（LLM）](https://en.wikipedia.org/wiki/Large_language_model)是强大的 AI 工具，能够像人类一样理解和生成文本。它们用途广泛，无须为每项任务专门训练，就能撰写内容、翻译语言、总结和回答问题。

除文本生成外，许多模型还支持：

* &#x20;[工具调用](#tool-calling)——调用外部工具（例如数据库查询或 API 调用），并在响应中使用结果。
* &#x20;[结构化输出](#structured-output)——约束模型响应，使其遵循已定义的格式。
* &#x20;[多模态](#multimodal)——处理和返回文本以外的数据，例如图像、音频和视频。
* &#x20;[推理](#reasoning)——通过多步推理得出结论。

模型是[智能体](https://docs.langchain.com/oss/python/langchain/agents.md)的推理引擎。它们驱动智能体的决策过程，确定调用哪些工具、如何解读结果，以及何时提供最终答案。

所选模型的质量和能力直接影响智能体的基础可靠性与性能。不同模型擅长不同任务：一些更善于遵循复杂指令，一些更善于结构化推理，还有一些支持更大的上下文窗口，以处理更多信息。

LangChain 的标准模型接口让你能够访问许多不同提供商的集成，便于试验和切换模型，找到最适合使用场景的选择。

提供商特有的集成信息和能力，参见其[聊天模型页面](https://docs.langchain.com/oss/python/integrations/chat.md)。

> [!TIP]
>
> [LangSmith](https://docs.langchain.com/langsmith/observability.md) 追踪每次模型调用，方便你比较提供商、检查工具路由并调试故障。按照[追踪快速入门](https://docs.langchain.com/langsmith/trace-with-langchain.md)完成设置。
>
> 我们还建议设置 [LangSmith Engine](https://docs.langchain.com/langsmith/engine.md)，它会监控追踪记录、发现问题并提出修复建议。

## 基本用法

模型有两种使用方式：

1. **与智能体一起使用**——创建[智能体](https://docs.langchain.com/oss/python/langchain/agents.md#model)时，可以动态指定模型。
2. **独立使用**——不依赖智能体框架，直接在智能体循环之外调用模型，完成文本生成、分类或信息提取等任务。

两种场景使用相同的模型接口，因此你可以从简单用法开始，再按需扩展为更复杂的智能体工作流。

### 初始化模型

在 LangChain 中开始独立使用模型，最简单的方法是使用 [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model)，从所选聊天模型提供商初始化模型（示例见下文）：

> [tab] OpenAI
>
> 👉 阅读 [OpenAI 聊天模型集成文档](https://docs.langchain.com/oss/python/integrations/chat/openai/)
>
> ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> pip install -U "langchain[openai]"
> ```
>
> ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> uv add "langchain[openai]"
> ```
>
> ```python init_chat_model theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain.chat_models import init_chat_model
>
> os.environ["OPENAI_API_KEY"] = "sk-..."
>
> model = init_chat_model("gpt-6.1-sol")
> ```
>
> ```python Model Class theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain_openai import ChatOpenAI
>
> os.environ["OPENAI_API_KEY"] = "sk-..."
>
> model = ChatOpenAI(model="gpt-6.1-sol")
> ```

> [tab] Anthropic
>
> 👉 阅读 [Anthropic 聊天模型集成文档](https://docs.langchain.com/oss/python/integrations/chat/anthropic/)
>
> ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> pip install -U "langchain[anthropic]"
> ```
>
> ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> uv add "langchain[anthropic]"
> ```
>
> ```python init_chat_model theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain.chat_models import init_chat_model
>
> os.environ["ANTHROPIC_API_KEY"] = "sk-..."
>
> model = init_chat_model("claude-sonnet-4-6")
> ```
>
> ```python Model Class theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain_anthropic import ChatAnthropic
>
> os.environ["ANTHROPIC_API_KEY"] = "sk-..."
>
> model = ChatAnthropic(model="claude-sonnet-4-6")
> ```

> [tab] Azure
>
> 👉 阅读 [Azure 聊天模型集成文档](https://docs.langchain.com/oss/python/integrations/chat/azure_chat_openai/)
>
> ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> pip install -U "langchain[openai]"
> ```
>
> ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> uv add "langchain[openai]"
> ```
>
> ```python init_chat_model theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain.chat_models import init_chat_model
>
> os.environ["AZURE_OPENAI_API_KEY"] = "..."
> os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
> os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"
>
> model = init_chat_model(
>     "azure_openai:gpt-6.1-sol",
>     azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
> )
> ```
>
> ```python Model Class theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain_openai import AzureChatOpenAI
>
> os.environ["AZURE_OPENAI_API_KEY"] = "..."
> os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
> os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"
>
> model = AzureChatOpenAI(
>     model="gpt-6.1-sol",
>     azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
> )
> ```

> [tab] Google Gemini
>
> 👉 阅读 [Google GenAI 聊天模型集成文档](https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai/)
>
> ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> pip install -U "langchain[google-genai]"
> ```
>
> ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> uv add "langchain[google-genai]"
> ```
>
> ```python init_chat_model theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain.chat_models import init_chat_model
>
> os.environ["GOOGLE_API_KEY"] = "..."
>
> model = init_chat_model("google_genai:gemini-4-hydrogen")
> ```
>
> ```python Model Class theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain_google_genai import ChatGoogleGenerativeAI
>
> os.environ["GOOGLE_API_KEY"] = "..."
>
> model = ChatGoogleGenerativeAI(model="gemini-4-hydrogen")
> ```

> [tab] AWS Bedrock
>
> 👉 阅读 [AWS Bedrock 聊天模型集成文档](https://docs.langchain.com/oss/python/integrations/chat/bedrock/)
>
> ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> pip install -U "langchain[aws]"
> ```
>
> ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> uv add "langchain[aws]"
> ```
>
> ```python init_chat_model theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from langchain.chat_models import init_chat_model
>
> # Follow the steps here to configure your credentials:
> # https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html
>
> model = init_chat_model(
>     "us.anthropic.claude-sonnet-4-6",
>     model_provider="bedrock_converse",
> )
> ```
>
> ```python Model Class theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from langchain_aws import ChatBedrock
>
> model = ChatBedrock(model="us.anthropic.claude-sonnet-4-6")
> ```

> [tab] HuggingFace
>
> 👉 阅读 [HuggingFace 聊天模型集成文档](https://docs.langchain.com/oss/python/integrations/chat/huggingface/)
>
> ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> pip install -U "langchain[huggingface]"
> ```
>
> ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> uv add "langchain[huggingface]"
> ```
>
> ```python init_chat_model theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain.chat_models import init_chat_model
>
> os.environ["HUGGINGFACEHUB_API_TOKEN"] = "hf_..."
>
> model = init_chat_model(
>     "microsoft/Phi-3-mini-4k-instruct",
>     model_provider="huggingface",
>     temperature=0.7,
>     max_tokens=1024,
> )
> ```
>
> ```python Model Class theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
>
> os.environ["HUGGINGFACEHUB_API_TOKEN"] = "hf_..."
>
> llm = HuggingFaceEndpoint(
>     repo_id="microsoft/Phi-3-mini-4k-instruct",
>     temperature=0.7,
>     max_length=1024,
> )
> model = ChatHuggingFace(llm=llm)
> ```

> [tab] OpenRouter
>
> 👉 阅读 [OpenRouter 聊天模型集成文档](https://docs.langchain.com/oss/python/integrations/chat/openrouter/)
>
> ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> pip install -U "langchain-openrouter"
> ```
>
> ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> uv add "langchain-openrouter"
> ```
>
> ```python init_chat_model theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain.chat_models import init_chat_model
>
> os.environ["OPENROUTER_API_KEY"] = "sk-..."
>
> model = init_chat_model(
>     "auto",
>     model_provider="openrouter",
> )
> ```
>
> ```python Model Class theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import os
> from langchain_openrouter import ChatOpenRouter
>
> os.environ["OPENROUTER_API_KEY"] = "sk-..."
>
> model = ChatOpenRouter(model="auto")
> ```

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
response = model.invoke("Why do parrots talk?")
```

更多详情（包括如何传递模型[参数](#parameters)），参见 [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model)。

### 支持的提供商与模型

LangChain 通过专门的集成包支持所有主要模型提供商。每个提供商包都实现相同的标准接口，因此可以切换提供商而不重写应用逻辑。新的模型名称可以立即使用，无须更新 LangChain，因为提供商包直接将模型名称传给提供商 API。

浏览[受支持提供商完整列表](https://docs.langchain.com/oss/python/integrations/providers/overview.md)，或阅读[提供商与模型](https://docs.langchain.com/oss/python/concepts/providers-and-models.md)，从概念上了解提供商、包与模型名称在 LangChain 中如何协同。

### 主要方法

> [card] [调用](#invoke)
>
> 模型以消息为输入，生成完整响应后输出消息。

> [card] [流式输出](#stream)
>
> 调用模型，并在输出生成时实时流式返回。

> [card] [批处理](#batch)
>
> 批量向模型发送多个请求，提高处理效率。

> [!NOTE]
>
> 除聊天模型外，LangChain 还支持嵌入模型、向量存储等相关技术。详情见[集成页面](https://docs.langchain.com/oss/python/integrations/providers/overview.md)。

## 参数

聊天模型接受用于配置行为的参数。完整的受支持参数集合因模型和提供商而异，但标准参数包括：

**model** `string` *必填*

你希望在某个提供商处使用的具体模型名称或标识符。也可以使用 '{model_provider}:{model}' 格式，在同一个参数中指定模型及其提供商，例如 'openai:o1'。

**api\_key** `string`

用于向模型提供商进行身份认证的密钥，通常在注册模型访问权限时获得。一般通过设置环境变量来读取它。环境变量的值在程序外部设置，通常使用操作系统或微服务内置的功能。

**temperature** `number`

控制模型输出的随机性。值越高，响应越有创造性；值越低，响应越确定。

**max\_tokens** `number`

限制响应的 token 总数，从而控制输出长度。token 是模型读取和生成内容的基本单位；各提供商定义可能不同，一般可以代表一个完整单词或单词的一部分。

**timeout** `number`

等待模型响应的最长时间（秒），超时后取消请求。

**max\_retries** `number`（默认值：6）

请求因网络超时或速率限制等问题失败时，系统重新发送请求的最大尝试次数。重试使用带随机抖动的指数退避。网络错误、速率限制（429）和服务器错误（5xx）会自动重试。401（未授权）或 404 等客户端错误不会重试。对于不稳定网络上的长时间[智能体](https://docs.langchain.com/oss/python/deepagents/overview.md)任务，可考虑将其提高到 10–15。

使用 [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model) 时，通过内联 `**kwargs`（任意关键字参数）传递这些参数：

```python Initialize using model parameters theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
model = init_chat_model(
    "claude-sonnet-4-6",
    # Kwargs passed to the model:
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
    max_retries=6,  # Default; increase for unreliable networks
)
```

### 连接韧性

LangChain 聊天模型对失败的 API 请求自动进行指数退避重试。默认情况下，遇到网络错误、速率限制（429）和服务器错误（5xx），最多重试 **6 次**。401（未授权）或 404 等客户端错误不重试。

创建模型时可以调整 `max_retries` 和 `timeout`，然后将该实例传给 `create_agent`、`create_deep_agent`，或单独调用：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "google_genai:gemini-4-hydrogen",
    max_retries=10,  # Increase for unreliable networks (default: 6)
    timeout=120,  # Seconds; increase for slow connections
)
```

> [!TIP]
>
> 对于不稳定网络上的长时间智能体图，考虑提高 `max_retries`（例如 10–15），并配置[检查点保存器](https://docs.langchain.com/oss/python/langgraph/persistence.md)，以便在故障后保留进度。

> [!NOTE]
>
> 每个聊天模型集成还可能提供额外参数，用于控制提供商特有功能。
>
> 例如，[`ChatOpenAI`](https://reference.langchain.com/python/langchain-openai/chat_models/base/ChatOpenAI) 的 `use_responses_api` 决定使用 OpenAI Responses API 还是 Completions API。
>
> 要查看某个聊天模型支持的全部参数，请前往[聊天模型集成](https://docs.langchain.com/oss/python/integrations/chat.md)页面。

***

## 调用

必须调用聊天模型才能生成输出。主要有三种调用方式，各自适合不同场景。

### 单次调用

调用模型最直接的方法是使用 [`invoke()`](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel/invoke)，传入单条消息或消息列表。

```python Single message theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
response = model.invoke("Why do parrots have colorful feathers?")
print(response)
```

可以向聊天模型提供消息列表来表示对话历史。每条消息都有角色，模型据此辨别对话中消息的发送者。

关于角色、类型和内容的更多详情，参见[消息](https://docs.langchain.com/oss/python/langchain/messages.md)指南。

```python Dictionary format theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
conversation = [
    {"role": "system", "content": "You are a helpful assistant that translates English to French."},
    {"role": "user", "content": "Translate: I love programming."},
    {"role": "assistant", "content": "J'adore la programmation."},
    {"role": "user", "content": "Translate: I love building applications."}
]

response = model.invoke(conversation)
print(response)  # AIMessage("J'adore créer des applications.")
```

```python Message objects theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.messages import HumanMessage, AIMessage, SystemMessage

conversation = [
    SystemMessage("You are a helpful assistant that translates English to French."),
    HumanMessage("Translate: I love programming."),
    AIMessage("J'adore la programmation."),
    HumanMessage("Translate: I love building applications.")
]

response = model.invoke(conversation)
print(response)  # AIMessage("J'adore créer des applications.")
```

> [!NOTE]
>
> 如果调用的返回类型是字符串，请确认使用的是聊天模型而非旧式 LLM。旧式文本补全大语言模型直接返回字符串。LangChain 聊天模型名称带有“Chat”前缀，例如 [`ChatOpenAI`](https://reference.langchain.com/python/langchain-openai/chat_models/base/ChatOpenAI)(/oss/integrations/chat/openai)。

### 流式输出

大多数模型都能够在生成内容的同时流式输出。通过渐进展示输出，流式输出显著改善用户体验，尤其适用于较长响应。

调用 [`stream()`](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel/stream) 返回一个迭代器，即依次、逐步访问集合中每个条目的对象；它在输出块生成时立即产出。可以使用循环实时处理各数据块：

```python Basic text streaming theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
for chunk in model.stream("Why do parrots have colorful feathers?"):
    print(chunk.text, end="|", flush=True)
```

```python Stream tool calls, reasoning, and other content theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
for chunk in model.stream("What color is the sky?"):
    for block in chunk.content_blocks:
        if block["type"] == "reasoning" and (reasoning := block.get("reasoning")):
            print(f"Reasoning: {reasoning}")
        elif block["type"] == "tool_call_chunk":
            print(f"Tool call chunk: {block}")
        elif block["type"] == "text":
            print(block["text"])
        else:
            ...
```

[`invoke()`](#invoke) 在模型生成完整响应后返回单个 [`AIMessage`](https://reference.langchain.com/python/langchain-core/messages/ai/AIMessage)，而 `stream()` 返回多个 [`AIMessageChunk`](https://reference.langchain.com/python/langchain-core/messages/ai/AIMessageChunk) 对象，每个包含部分输出文本。重要的是，流中的各数据块可以通过相加聚合为完整消息：

```python Construct an AIMessage theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
full = None  # None | AIMessageChunk
for chunk in model.stream("What color is the sky?"):
    full = chunk if full is None else full + chunk
    print(full.text)

# The
# The sky
# The sky is
# The sky is typically
# The sky is typically blue
# ...

print(full.content_blocks)
# [{"type": "text", "text": "The sky is typically blue..."}]
```

聚合后的消息可以像 [`invoke()`](#invoke) 生成的消息一样使用，例如加入消息历史，再作为对话上下文传回模型。

> [!WARNING]
>
> 只有程序中的所有步骤都知道如何处理数据块流，流式输出才能工作。例如，一个必须先把全部输出存入内存才能处理的应用，就不具备流式处理能力。

> [accordion] 高级流式主题
>
> > [accordion] 流式事件
> >
> > LangChain 聊天模型也可以通过 `astream_events()` 流式输出语义事件。
> >
> > 这样可以更方便地根据事件类型及其他元数据筛选，并在后台聚合完整消息。示例见下文。
> >
> > ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> > async for event in model.astream_events("Hello"):
> >
> >     if event["event"] == "on_chat_model_start":
> >         print(f"Input: {event['data']['input']}")
> >
> >     elif event["event"] == "on_chat_model_stream":
> >         print(f"Token: {event['data']['chunk'].text}")
> >
> >     elif event["event"] == "on_chat_model_end":
> >         print(f"Full message: {event['data']['output'].text}")
> >
> >     else:
> >         pass
> > ```
> >
> > ```txt theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> > Input: Hello
> > Token: Hi
> > Token:  there
> > Token: !
> > Token:  How
> > Token:  can
> > Token:  I
> > ...
> > Full message: Hi there! How can I help today?
> > ```
> >
> > > [!TIP]
> > >
> > > 事件类型及其他详情，参见 [`astream_events()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.astream_events) 参考。
>
> > [accordion] “自动流式输出”聊天模型
> >
> > LangChain 在某些情况下自动启用流式模式，即使没有显式调用流式方法，也能简化聊天模型的流式输出。对于使用非流式 invoke 方法、却仍希望整个应用（包括聊天模型中间结果）流式输出的情况，这尤其有用。
> >
> > 例如在 [LangGraph 智能体](https://docs.langchain.com/oss/python/langchain/agents.md)中，可以在节点内调用 `model.invoke()`，但如果整体运行于流式模式，LangChain 会自动转为流式处理。
> >
> > #### 工作原理
> >
> > 对聊天模型执行 `invoke()` 时，如果 LangChain 检测到你正在尝试流式输出整个应用，就会自动切换到内部流式模式。对于调用 invoke 的代码而言，调用结果保持不变；但在聊天模型流式生成期间，LangChain 会负责在回调系统中触发 [`on_llm_new_token`](https://reference.langchain.com/python/langchain-core/callbacks/base/AsyncCallbackHandler/on_llm_new_token) 事件。
> >
> > 回调事件使 LangGraph 的 `stream()` 和 `astream_events()` 能够实时呈现聊天模型输出。

### 批处理

将一组相互独立的请求批量发送给模型，可以显著提升性能并降低成本，因为处理能够并行进行：

```python Batch theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
responses = model.batch([
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
])
for response in responses:
    print(response)
```

> [!NOTE]
>
> 本节介绍聊天模型的 [`batch()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch) 方法，它在客户端并行发起模型调用。
>
> 它**不同于**推理提供商支持的批处理 API，例如 [OpenAI](https://platform.openai.com/docs/guides/batch) 或 [Anthropic](https://platform.claude.com/docs/en/build-with-claude/batch-processing#message-batches-api) 的批处理 API。

默认情况下，[`batch()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch) 只在整批完成后返回最终输出。如果希望每个输入对应的输出一生成完成就收到，可通过 [`batch_as_completed()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch_as_completed) 流式获取结果：

```python Yield batch responses upon completion theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
for response in model.batch_as_completed([
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
]):
    print(response)
```

> [!NOTE]
>
> 使用 [`batch_as_completed()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch_as_completed) 时，结果到达顺序可能不同于输入顺序。每个结果包含输入索引，可据此匹配，并在需要时重建原顺序。

> [!TIP]
>
> 使用 [`batch()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch) 或 [`batch_as_completed()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch_as_completed) 处理大量输入时，可能需要控制最大并行调用数。可以在 [`RunnableConfig`](https://reference.langchain.com/python/langchain-core/runnables/config/RunnableConfig) 字典中设置 [`max_concurrency`](https://reference.langchain.com/python/langchain-core/runnables/config/RunnableConfig) 属性。
>
> ```python Batch with max concurrency theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> model.batch(
>     list_of_inputs,
>     config={
>         'max_concurrency': 5,  # Limit to 5 parallel calls
>     }
> )
> ```
>
> 全部受支持属性，参见 [`RunnableConfig`](https://reference.langchain.com/python/langchain-core/runnables/config/RunnableConfig) 参考。

批处理的更多详情，见[参考文档](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch)。

***

## 工具调用

模型可以请求调用工具，执行从数据库获取数据、搜索网页或运行代码等任务。工具由以下两部分组成：

1. 模式，包含工具名称、说明和／或参数定义（通常为 JSON 模式）
2. 要执行的函数或协程（能够暂停执行并在之后恢复的方法）。

> [!NOTE]
>
> 你可能会听到“函数调用”一词。我们将它与“工具调用”视为可互换用语。

以下是用户与模型之间的基本工具调用流程：

```mermaid theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
sequenceDiagram
    participant U as User
    participant M as Model
    participant T as Tools

    U->>M: "What's the weather in SF and NYC?"
    M->>M: Analyze request & decide tools needed

    par Parallel Tool Calls
        M->>T: get_weather("San Francisco")
        M->>T: get_weather("New York")
    end

    par Tool Execution
        T-->>M: SF weather data
        T-->>M: NYC weather data
    end

    M->>M: Process results & generate response
    M->>U: "SF: 72°F sunny, NYC: 68°F cloudy"
```

要让模型能够使用你定义的工具，必须通过 [`bind_tools`](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel/bind_tools) 绑定。之后调用模型时，模型可以按需选择调用任何已绑定工具。

一些模型提供商提供内置工具，即在服务端执行的工具，例如网页搜索和代码解释器。它们可以通过模型或调用参数启用（例如 [`ChatOpenAI`](https://docs.langchain.com/oss/python/integrations/chat/openai)、[`ChatAnthropic`](https://docs.langchain.com/oss/python/integrations/chat/anthropic)）。详情见相应[提供商参考](https://docs.langchain.com/oss/python/integrations/providers/overview.md)。

> [!TIP]
>
> 创建工具的详情及其他选项，参见[工具指南](https://docs.langchain.com/oss/python/langchain/tools.md)。

```python Binding user tools theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return f"It's sunny in {location}."


model_with_tools = model.bind_tools([get_weather])  # [!code highlight]

response = model_with_tools.invoke("What's the weather like in Boston?")
for tool_call in response.tool_calls:
    # View tool calls made by the model
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")
```

绑定用户自定义工具后，模型响应中包含的是执行工具的**请求**。独立于[智能体](https://docs.langchain.com/oss/python/langchain/agents.md)使用模型时，需要自行执行所请求的工具，并将结果返回给模型，用于后续推理。使用[智能体](https://docs.langchain.com/oss/python/langchain/agents.md)时，智能体循环会替你处理工具执行循环。

下面展示使用工具调用的一些常见方式。

> [accordion] 工具执行循环
>
> 模型返回工具调用时，需要执行工具并将结果传回模型。这形成一个对话循环，模型可以使用工具结果生成最终响应。LangChain 包含[智能体](https://docs.langchain.com/oss/python/langchain/agents.md)抽象，为你处理此编排过程。
>
> 下面是一个简单示例：
>
> ```python Tool execution loop theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> # Bind (potentially multiple) tools to the model
> tools = [get_weather]
> tools_by_name = {tool.name: tool for tool in tools}
> model_with_tools = model.bind_tools(tools)
>
> # Step 1: Model generates tool calls
> messages = [{"role": "user", "content": "What's the weather in Boston?"}]
> ai_msg = model_with_tools.invoke(messages)
> messages.append(ai_msg)
>
> # Step 2: Execute tools and collect results
> for tool_call in ai_msg.tool_calls:
>     # Execute the tool with the generated arguments
>     tool = tools_by_name[tool_call["name"]]
>     tool_result = tool.invoke(tool_call)
>     messages.append(tool_result)
>
> # Step 3: Pass results back to model for final response
> final_response = model_with_tools.invoke(messages)
> print(final_response.text)
> # "The current weather in Boston is 72°F and sunny."
> ```
>
> 工具返回的每个 [`ToolMessage`](https://reference.langchain.com/python/langchain-core/messages/tool/ToolMessage) 都包含与原始工具调用匹配的 `tool_call_id`，帮助模型将结果与请求关联。

> [accordion] 强制工具调用
>
> 默认情况下，模型可以根据用户输入自由选择使用哪个已绑定工具。但你也可能希望强制选择工具，确保模型使用某个特定工具，或给定列表中的**任意一个**工具：
>
> ```python Force use of any tool theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> model_with_tools = model.bind_tools([tool_1], tool_choice="any")
> ```
>
> ```python Force use of specific tools theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> model_with_tools = model.bind_tools([tool_1], tool_choice="tool_1")
> ```

> [accordion] 并行工具调用
>
> 许多模型支持在适当情况下并行调用多个工具，从而同时从不同来源收集信息。
>
> ```python Parallel tool calls theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> tools = [get_weather]
> tools_by_name = {tool.name: tool for tool in tools}
> model_with_tools = model.bind_tools(tools)
>
> response = model_with_tools.invoke(
>     "What's the weather in Boston and Tokyo?"
> )
>
>
> # The model may generate multiple tool calls
> print(response.tool_calls)
> # [
> #   {'name': 'get_weather', 'args': {'location': 'Boston'}, 'id': 'call_1'},
> #   {'name': 'get_weather', 'args': {'location': 'Tokyo'}, 'id': 'call_2'},
> # ]
>
>
> # Execute all tools (can be done in parallel with async)
> results = []
> for tool_call in response.tool_calls:
>     tool = tools_by_name[tool_call["name"]]
>     result = tool.invoke(tool_call)
>     results.append(result)
> ```
>
> 模型根据所请求操作之间的独立性，智能判断何时适合并行执行。
>
> > [!TIP]
> >
> > 大多数支持工具调用的模型默认启用并行工具调用。一些模型（包括 [OpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai) 和 [Anthropic](https://docs.langchain.com/oss/python/integrations/chat/anthropic)）允许禁用此功能。设置 `parallel_tool_calls=False` 即可：
> >
> > ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> > model.bind_tools([get_weather], parallel_tool_calls=False)
> > ```

> [accordion] 流式工具调用
>
> 流式响应期间，工具调用通过 [`ToolCallChunk`](https://reference.langchain.com/python/langchain-core/messages/tool/ToolCallChunk) 逐步构建。因此可以在生成过程中看到工具调用，而不必等待完整响应。
>
> ```python Streaming tool calls theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> for chunk in model_with_tools.stream(
>     "What's the weather in Boston and Tokyo?"
> ):
>     # Tool call chunks arrive progressively
>     for tool_chunk in chunk.tool_call_chunks:
>         if name := tool_chunk.get("name"):
>             print(f"Tool: {name}")
>         if id_ := tool_chunk.get("id"):
>             print(f"ID: {id_}")
>         if args := tool_chunk.get("args"):
>             print(f"Args: {args}")
>
> # Output:
> # Tool: get_weather
> # ID: call_SvMlU1TVIZugrFLckFE2ceRE
> # Args: {"lo
> # Args: catio
> # Args: n": "B
> # Args: osto
> # Args: n"}
> # Tool: get_weather
> # ID: call_QMZdy6qInx13oWKE7KhuhOLR
> # Args: {"lo
> # Args: catio
> # Args: n": "T
> # Args: okyo
> # Args: "}
> ```
>
> 可以累积数据块，构建完整的工具调用：
>
> ```python Accumulate tool calls theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> gathered = None
> for chunk in model_with_tools.stream("What's the weather in Boston?"):
>     gathered = chunk if gathered is None else gathered + chunk
>     print(gathered.tool_calls)
> ```

***

## 结构化输出

可以要求模型按给定模式的格式提供响应，以确保输出易于解析并用于后续处理。LangChain 支持多种模式类型，以及多种强制结构化输出的方法。

> [!TIP]
>
> 关于结构化输出，参见[结构化输出](https://docs.langchain.com/oss/python/langchain/structured-output.md)。

> [tab] Pydantic
>
> [Pydantic 模型](https://docs.pydantic.dev/latest/concepts/models/#basic-model-usage)提供最丰富的功能，包括字段验证、说明和嵌套结构。
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from pydantic import BaseModel, Field
>
> class Movie(BaseModel):
>     """A movie with details."""
>     title: str = Field(description="The title of the movie")
>     year: int = Field(description="The year the movie was released")
>     director: str = Field(description="The director of the movie")
>     rating: float = Field(description="The movie's rating out of 10")
>
> model_with_structure = model.with_structured_output(Movie)
> response = model_with_structure.invoke("Provide details about the movie Inception")
> print(response)  # Movie(title="Inception", year=2010, director="Christopher Nolan", rating=8.8)
> ```

> [tab] TypedDict
>
> Python 的 `TypedDict` 是比 Pydantic 模型更简单的替代方案，适合不需要运行时验证的情况。
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from typing_extensions import TypedDict, Annotated
>
> class MovieDict(TypedDict):
>     """A movie with details."""
>     title: Annotated[str, ..., "The title of the movie"]
>     year: Annotated[int, ..., "The year the movie was released"]
>     director: Annotated[str, ..., "The director of the movie"]
>     rating: Annotated[float, ..., "The movie's rating out of 10"]
>
> model_with_structure = model.with_structured_output(MovieDict)
> response = model_with_structure.invoke("Provide details about the movie Inception")
> print(response)  # {'title': 'Inception', 'year': 2010, 'director': 'Christopher Nolan', 'rating': 8.8}
> ```

> [tab] JSON Schema
>
> 提供 [JSON Schema](https://json-schema.org/understanding-json-schema/about)，可获得最大控制能力和互操作性。
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> import json
>
> json_schema = {
>     "title": "Movie",
>     "description": "A movie with details",
>     "type": "object",
>     "properties": {
>         "title": {
>             "type": "string",
>             "description": "The title of the movie"
>         },
>         "year": {
>             "type": "integer",
>             "description": "The year the movie was released"
>         },
>         "director": {
>             "type": "string",
>             "description": "The director of the movie"
>         },
>         "rating": {
>             "type": "number",
>             "description": "The movie's rating out of 10"
>         }
>     },
>     "required": ["title", "year", "director", "rating"]
> }
>
> model_with_structure = model.with_structured_output(
>     json_schema,
>     method="json_schema",
> )
> response = model_with_structure.invoke("Provide details about the movie Inception")
> print(response)  # {'title': 'Inception', 'year': 2010, ...}
> ```

> [!NOTE]
>
> **结构化输出的关键注意事项**
>
> * **方法参数**：一些提供商支持不同的结构化输出方法：
>   * `'json_schema'`：使用提供商提供的专用结构化输出功能。
>   * `'function_calling'`：通过强制发起遵循给定模式的[工具调用](#tool-calling)，获得结构化输出。
>   * `'json_mode'`：部分提供商在 `'json_schema'` 之前提供的方式。生成有效 JSON，但必须在提示词中描述模式。
> * **包含原始响应**：设置 `include_raw=True`，同时获取解析后输出和原始 AI 消息。
> * **验证**：Pydantic 模型提供自动验证；`TypedDict` 和 JSON Schema 需要手动验证。
> * **拒绝**：如果模型拒绝请求，结构化输出会抛出 `ModelRefusalError`。参见[处理模型拒绝](#handle-a-model-refusal)及[结构化输出](https://docs.langchain.com/oss/python/langchain/structured-output.md#model-refusal)。
>
> 受支持的方法和配置选项，参见[提供商集成页面](https://docs.langchain.com/oss/python/integrations/providers/overview.md)。

> [accordion] 示例：同时输出消息与解析后的结构
>
> 在返回解析结果的同时返回原始 [`AIMessage`](https://reference.langchain.com/python/langchain-core/messages/ai/AIMessage) 对象，有助于访问[token 数量](#token-usage)等响应元数据。为此，调用 [`with_structured_output`](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel/with_structured_output) 时设置 [`include_raw=True`](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel/with_structured_output)：
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from pydantic import BaseModel, Field
>
> class Movie(BaseModel):
>     """A movie with details."""
>     title: str = Field(description="The title of the movie")
>     year: int = Field(description="The year the movie was released")
>     director: str = Field(description="The director of the movie")
>     rating: float = Field(description="The movie's rating out of 10")
>
> model_with_structure = model.with_structured_output(Movie, include_raw=True)  # [!code highlight]
> response = model_with_structure.invoke("Provide details about the movie Inception")
> response
> # {
> #     "raw": AIMessage(...),
> #     "parsed": Movie(title=..., year=..., ...),
> #     "parsing_error": None,
> # }
> ```

> [accordion] 示例：嵌套结构
>
> 模式可以嵌套：
>
> ```python Pydantic BaseModel theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from pydantic import BaseModel, Field
>
> class Actor(BaseModel):
>     name: str
>     role: str
>
> class MovieDetails(BaseModel):
>     title: str
>     year: int
>     cast: list[Actor]
>     genres: list[str]
>     budget: float | None = Field(None, description="Budget in millions USD")
>
> model_with_structure = model.with_structured_output(MovieDetails)
> ```
>
> ```python TypedDict theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from typing_extensions import Annotated, TypedDict
>
> class Actor(TypedDict):
>     name: str
>     role: str
>
> class MovieDetails(TypedDict):
>     title: str
>     year: int
>     cast: list[Actor]
>     genres: list[str]
>     budget: Annotated[float | None, ..., "Budget in millions USD"]
>
> model_with_structure = model.with_structured_output(MovieDetails)
> ```

### 处理模型拒绝

提供商将拒绝（例如基于安全策略的拒绝）作为成功响应而非错误报告。普通模型调用返回带有[拒绝内容块](https://docs.langchain.com/oss/python/langchain/messages#content-block-reference)的消息。`with_structured_output` 会抛出来自 `langchain_core.exceptions` 的 [`ModelRefusalError`](https://reference.langchain.com/python/langchain-core/exceptions/ModelRefusalError)，而不是解析错误。错误对象的 `raw_message` 保存被拒绝的响应。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain_core.exceptions import ModelRefusalError

model_with_structure = model.with_structured_output(Movie)

try:
    response = model_with_structure.invoke("Provide details about the movie Inception")
except ModelRefusalError as error:
    print(error)  # Model refused to produce the requested output (category='cyber'): ...
    refused = error.raw_message
```

设置 `include_raw=True` 时，`with_structured_output` 将错误作为 `parsing_error` 返回，而不抛出：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
model_with_structure = model.with_structured_output(Movie, include_raw=True)
response = model_with_structure.invoke("Provide details about the movie Inception")
if isinstance(response["parsing_error"], ModelRefusalError):
    refused = response["raw"]
```

LangChain 能检测 OpenAI、Anthropic 和 Gemini 模型的拒绝。对于智能体，添加 [`ModelRefusalMiddleware`](https://docs.langchain.com/oss/python/langchain/middleware/built-in#model-refusal) 后，`create_agent` 中的 `response_format` 会抛出 `ModelRefusalError`；参见[结构化输出](https://docs.langchain.com/oss/python/langchain/structured-output.md#model-refusal)和[处理拒绝](https://docs.langchain.com/oss/python/langchain/middleware/built-in.md#handle-a-refusal)。

> [!NOTE]
>
> 拒绝处理需要 `langchain-core>=1.7.5`；Gemini 还需要 `langchain-google-genai>=4.4.3`。若将 `langchain-core` 升级到 1.7.5 或更高版本，也应升级到 `langchain-openai>=1.7.4`。较早版本在 Responses API 的结构化输出被拒绝时，会抛出通用 `ValueError`，而非 `OpenAIRefusalError`。

***

## 高级主题

### 模型能力配置

> [!NOTE]
>
> 模型能力配置需要 `langchain>=1.1`。

LangChain 聊天模型可以通过 `profile` 属性，暴露一个包含受支持功能和能力的字典：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
model.profile
# {
#   "max_input_tokens": 400000,
#   "image_inputs": True,
#   "reasoning_output": True,
#   "tool_calling": True,
#   ...
# }
```

完整字段集合，参见 [API 参考](https://reference.langchain.com/python/langchain-core/language_models/model_profile/ModelProfile)。

模型能力配置数据大多由 [models.dev](https://github.com/sst/models.dev) 项目提供，这是一个提供模型能力数据的开源项目。LangChain 为这些数据增加额外字段以供自身使用，并在上游项目演进时保持增强数据与其一致。

模型能力配置数据允许应用根据模型能力动态调整行为。例如：

1. [汇总中间件](https://docs.langchain.com/oss/python/langchain/middleware/built-in.md#summarization)可根据模型上下文窗口大小触发汇总。
2. `create_agent` 中的[结构化输出](https://docs.langchain.com/oss/python/langchain/structured-output.md)策略可自动推断（例如检查是否支持原生结构化输出功能）。
3. 可根据支持的[模态](#multimodal)和最大输入 token 数，对模型输入进行准入控制。
4. [Deep Agents Code](https://docs.langchain.com/oss/deepagents/code) 会将[交互式模型切换器](https://docs.langchain.com/oss/deepagents/code/providers.md#which-models-appear-in-the-switcher)筛选为其能力配置报告支持 `tool_calling` 和文本输入／输出的模型，并在选择器详情视图中显示上下文窗口大小与能力标记。

> [accordion] 更新或覆盖能力配置数据
>
> 模型能力配置数据缺失、陈旧或不正确时，可以更改。
>
> **选项 1（快速修复）**
>
> 可以使用任意有效的能力配置来实例化聊天模型：
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> custom_profile = {
>     "max_input_tokens": 100_000,
>     "tool_calling": True,
>     "structured_output": True,
>     # ...
> }
> model = init_chat_model("...", profile=custom_profile)
> ```
>
> `profile` 本身也是普通 `dict`，可以就地更新。如果模型实例被共享，考虑使用 `model_copy`，避免修改共享状态。
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> new_profile = model.profile | {"key": "value"}
> model.model_copy(update={"profile": new_profile})
> ```
>
> **选项 2（修复上游数据）**
>
> 数据主要来源于 [models.dev](https://models.dev/) 项目。这些数据会与 LangChain [集成包](https://docs.langchain.com/oss/python/integrations/providers/overview.md)中的额外字段和覆盖配置合并，并随包发布。
>
> 可以通过以下流程更新模型能力配置数据：
>
> 1. （如有需要）向 [models.dev](https://models.dev/) 的 [GitHub 仓库](https://github.com/sst/models.dev)提交拉取请求，更新源数据。
> 2. （如有需要）向 LangChain [集成包](https://docs.langchain.com/oss/python/integrations/providers/overview.md)提交拉取请求，更新 `langchain_<package>/data/profile_augmentations.toml` 中的额外字段和覆盖配置\`。
> 3. 使用 [`langchain-model-profiles`](https://pypi.org/project/langchain-model-profiles/) CLI 工具从 [models.dev](https://models.dev/) 拉取最新数据，合并增强数据并更新能力配置数据：
>
> ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> pip install -U langchain-model-profiles
> ```
>
> ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> uv add langchain-model-profiles
> ```
>
> ```bash theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> langchain-profiles refresh --provider <provider> --data-dir <data_dir>
> ```
>
> 此命令会：
>
> * 从 models.dev 下载 `<provider>` 的最新数据
> * 合并 `<data_dir>` 中 `profile_augmentations.toml` 的增强配置
> * 将合并后的能力配置写入 `<data_dir>` 中的 `_profiles.py`
>
> 例如，在 [LangChain 单体仓库](https://github.com/langchain-ai/langchain)的 [`libs/partners/anthropic`](https://github.com/langchain-ai/langchain/tree/master/libs/partners/anthropic) 目录中执行：
>
> ```bash theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> uv run --with langchain-model-profiles langchain-profiles refresh --provider anthropic --data-dir langchain_anthropic/data
> ```

> [!WARNING]
>
> 模型能力配置是测试版功能，其格式可能变化。

### 多模态

某些模型可以处理和返回图像、音频、视频等非文本数据。可以通过提供[内容块](https://docs.langchain.com/oss/python/langchain/messages.md#message-content)，向模型传入非文本数据。

> [!TIP]
>
> 所有底层具备多模态能力的 LangChain 聊天模型都支持：
>
> 1. 跨提供商的标准数据格式（参见[消息指南](https://docs.langchain.com/oss/python/langchain/messages.md)）
> 2. OpenAI [聊天补全](https://platform.openai.com/docs/api-reference/chat)格式
> 3. 相应提供商的任意原生格式（例如 Anthropic 模型接受 Anthropic 原生格式）

详情见消息指南的[多模态部分](https://docs.langchain.com/oss/python/langchain/messages.md#multimodal)。

一些模型可以将多模态数据作为响应的一部分返回（并非所有大语言模型都一样！）。如果请求模型这样做，返回的 [`AIMessage`](https://reference.langchain.com/python/langchain-core/messages/ai/AIMessage) 将包含多模态类型的内容块。

```python Multimodal output theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
response = model.invoke("Create a picture of a cat")
print(response.content_blocks)
# [
#     {"type": "text", "text": "Here's a picture of a cat"},
#     {"type": "image", "base64": "...", "mime_type": "image/jpeg"},
# ]
```

特定提供商的详情，参见[集成页面](https://docs.langchain.com/oss/python/integrations/providers/overview.md)。

### 推理

许多模型能够通过多步推理得出结论，即将复杂问题拆解为更小、更易处理的步骤。

**如果底层模型支持，**可以呈现此推理过程，以更好地理解模型如何得出最终答案。

```python Stream reasoning output theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
for chunk in model.stream("Why do parrots have colorful feathers?"):
    reasoning_steps = [r for r in chunk.content_blocks if r["type"] == "reasoning"]
    print(reasoning_steps if reasoning_steps else chunk.text)
```

```python Complete reasoning output theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
response = model.invoke("Why do parrots have colorful feathers?")
reasoning_steps = [b for b in response.content_blocks if b["type"] == "reasoning"]
print(" ".join(step["reasoning"] for step in reasoning_steps))
```

根据模型不同，有时可以指定应投入多少推理努力，也可以要求完全关闭推理。这可能表现为分类的推理“档位”（例如 `'low'` 或 `'high'`），或整数形式的 token 预算。

> [!NOTE]
>
> 标准参数 `reasoning_effort` 需要 `langchain-core>=1.5.2`，以及相应的合作伙伴包版本：`langchain-anthropic>=1.5.3`、`langchain-openai>=1.4.1`、`langchain-fireworks>=1.5.2`、`langchain-xai>=1.3.0`、`langchain-google-genai>=4.3.1` 或 `langchain-aws>=1.7.0`。

[`ChatOpenAI`](https://reference.langchain.com/python/langchain-openai/chat_models/base/ChatOpenAI)、[`ChatAnthropic`](https://reference.langchain.com/python/langchain-anthropic/chat_models/ChatAnthropic)、[`ChatFireworks`](https://reference.langchain.com/python/langchain-fireworks/chat_models/ChatFireworks)、[`ChatXAI`](https://reference.langchain.com/python/langchain-xai/chat_models/ChatXAI)、[`ChatGoogleGenerativeAI`](https://reference.langchain.com/python/langchain-google-genai/chat_models/ChatGoogleGenerativeAI) 和 [`ChatBedrockConverse`](https://reference.langchain.com/python/langchain-aws/chat_models/bedrock_converse/ChatBedrockConverse) 支持标准 `reasoning_effort` 参数。与 `temperature` 类似，可以在构造模型或每次调用时设置，各提供商会将其转换为自己的 API 格式：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-6")
response = model.invoke(
    "Why do parrots have colorful feathers?",
    reasoning_effort="high",
)
```

支持的推理档位和提供商文档中的默认值因模型而异。请检查模型的[能力配置](#model-profiles)，了解它支持的档位及默认值：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
model.profile["reasoning_effort_levels"]  # e.g. ['low', 'medium', 'high']
model.profile["reasoning_effort_default"]  # e.g. 'high'
```

一些提供商也接受 `reasoning_effort` 的原生别名（例如 `ChatAnthropic` 接受 `effort`，`ChatGoogleGenerativeAI` 接受 `thinking_level`）。提供商特有详情，参见[聊天模型集成](https://docs.langchain.com/oss/python/integrations/chat.md)页面。

更多详情，参见相应聊天模型的[集成页面](https://docs.langchain.com/oss/python/integrations/providers/overview.md)或[参考文档](https://reference.langchain.com/python/integrations/)。

### 本地模型

LangChain 支持在你自己的硬件上本地运行模型。这适用于数据隐私至关重要、希望调用自定义模型，或希望避免使用云模型所产生费用的场景。

[Ollama](https://docs.langchain.com/oss/python/integrations/chat/ollama) 是在本地运行聊天模型和嵌入模型最简单的方法之一。

### 提示词缓存

许多提供商提供提示词缓存功能，以减少重复处理相同 token 的延迟与成本。可以在三个层面使用缓存：

* **提供商隐式缓存：**若请求命中缓存，提供商会自动降低费用，无须配置。例如 [OpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai) 和 [Gemini](https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai)。
* **提供商级显式控制：**提供商允许手动指定缓存点，以获得更强控制能力或确保节省成本。这些控制与底层提供商／API 的行为一致。例如：
  * [`ChatOpenAI`](https://reference.langchain.com/python/langchain-openai/chat_models/base/ChatOpenAI)（通过 `prompt_cache_key`）
  * Anthropic 内容块的 [`cache_control`](https://docs.langchain.com/oss/python/integrations/chat/anthropic#prompt-caching)
  * [Gemini](https://reference.langchain.com/python/langchain-google-genai)。
  * AWS Bedrock 的 [`cachePoint`](https://docs.langchain.com/oss/python/integrations/chat/bedrock#prompt-caching) 块
* **LangChain 中间件：**对于智能体，中间件允许 LangChain 优化稳定系统提示词和工具内容的缓存。例如：
  * Anthropic 的 [`AnthropicPromptCachingMiddleware`](https://docs.langchain.com/oss/python/integrations/middleware/anthropic#prompt-caching)
  * AWS Bedrock 的 [`BedrockPromptCachingMiddleware`](https://docs.langchain.com/oss/python/integrations/middleware/aws#prompt-caching)

> [!WARNING]
>
> 提示词缓存通常仅在输入 token 数超过最低阈值后才会启用。详情见[提供商页面](https://docs.langchain.com/oss/python/integrations/chat.md)。

缓存使用情况会体现在模型响应的[用量元数据](https://docs.langchain.com/oss/python/langchain/messages.md#token-usage)中。

### 服务端工具使用

一些提供商支持服务端[工具调用](#tool-calling)循环：模型可以在单轮对话中与网页搜索、代码解释器等工具交互，并分析结果。

如果模型在服务端调用工具，响应消息内容会包含表示工具调用及其结果的内容。访问响应的[内容块](https://docs.langchain.com/oss/python/langchain/messages.md#standard-content-blocks)，会以不依赖提供商的格式返回服务端工具调用和结果：

```python Invoke with server-side tool use theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-5.4-mini")

tool = {"type": "web_search"}
model_with_tools = model.bind_tools([tool])

response = model_with_tools.invoke("What was a positive news story from today?")
print(response.content_blocks)
```

```python Result expandable theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
[
    {
        "type": "server_tool_call",
        "name": "web_search",
        "args": {
            "query": "positive news stories today",
            "type": "search"
        },
        "id": "ws_abc123"
    },
    {
        "type": "server_tool_result",
        "tool_call_id": "ws_abc123",
        "status": "success"
    },
    {
        "type": "text",
        "text": "Here are some positive news stories from today...",
        "annotations": [
            {
                "end_index": 410,
                "start_index": 337,
                "title": "article title",
                "type": "citation",
                "url": "..."
            }
        ]
    }
]
```

这代表单轮对话；不像客户端[工具调用](#tool-calling)那样需要传入关联的 [ToolMessage](https://docs.langchain.com/oss/python/langchain/messages.md#tool-message) 对象。

可用工具及用法详情，参见相应提供商的[集成页面](https://docs.langchain.com/oss/python/integrations/chat.md)。

### 模型异常

对于认证错误、速率限制、超时等常见模型故障，主要集成包会抛出来自 `langchain_core.exceptions` 的标准异常类型。这些异常同时继承 LangChain 基类和提供商 SDK 自己的异常类型，因此可以捕获任意一种：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.chat_models import init_chat_model
from langchain_core.exceptions import ModelTimeoutError

model = init_chat_model("openai:gpt-5.6-luna", timeout=0.0001)

try:
    response = model.invoke("Hello")
except ModelTimeoutError:
    print("caught")
```

每种类型都有 `is_retryable` 属性，[重试中间件](https://docs.langchain.com/oss/python/langchain/middleware/built-in.md#model-retry)默认遵循该属性。

> [accordion] 异常类型
>
> * [`ModelAuthenticationError`](https://reference.langchain.com/python/langchain-core/exceptions/ModelAuthenticationError)——API 密钥缺失、无效或过期（不可重试）
> * [`ModelPermissionDeniedError`](https://reference.langchain.com/python/langchain-core/exceptions/ModelPermissionDeniedError)——凭据缺少权限（不可重试）
> * [`ModelInvalidRequestError`](https://reference.langchain.com/python/langchain-core/exceptions/ModelInvalidRequestError)——提供商拒绝请求（不可重试）
> * [`ModelNotFoundError`](https://reference.langchain.com/python/langchain-core/exceptions/ModelNotFoundError)——未找到请求的模型（不可重试）
> * [`ModelRateLimitError`](https://reference.langchain.com/python/langchain-core/exceptions/ModelRateLimitError)——超出提供商速率限制（可重试）
> * [`ModelAPIError`](https://reference.langchain.com/python/langchain-core/exceptions/ModelAPIError)——提供商服务器故障（可重试）
> * [`ModelConnectionError`](https://reference.langchain.com/python/langchain-core/exceptions/ModelConnectionError)——无法连接提供商（可重试）
> * [`ModelTimeoutError`](https://reference.langchain.com/python/langchain-core/exceptions/ModelTimeoutError)——请求超时（可重试）
> * [`ContextOverflowError`](https://reference.langchain.com/python/langchain-core/exceptions/ContextOverflowError)——输入超出模型上下文限制（不可重试）

### 速率限制

许多聊天模型提供商限制特定时段内的调用次数。触发速率限制时，通常会收到提供商的速率限制错误响应，需要等待后才能继续请求。

为帮助管理速率限制，聊天模型集成在初始化时接受 `rate_limiter` 参数，以控制请求发起速率。

> [accordion] 初始化并使用速率限制器
>
> LangChain 内置了可选的 [`InMemoryRateLimiter`](https://reference.langchain.com/python/langchain-core/rate_limiters/InMemoryRateLimiter)。它是线程安全的，可供同一进程的多个线程共享。
>
> ```python Define a rate limiter theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from langchain.rate_limiters import InMemoryRateLimiter
>
> rate_limiter = InMemoryRateLimiter(
>     requests_per_second=0.1,  # 1 request every 10s
>     check_every_n_seconds=0.1,  # Check every 100ms whether allowed to make a request
>     max_bucket_size=10,  # Controls the maximum burst size.
> )
>
> model = init_chat_model(
>     model="gpt-6.1-sol",
>     model_provider="openai",
>     rate_limiter=rate_limiter  # [!code highlight]
> )
> ```
>
> > [!WARNING]
> >
> > 所提供的速率限制器只能限制单位时间内的请求次数，不能用于同时按请求大小进行限制。

### 基础 URL 与代理设置

对于实现 OpenAI Chat Completions API 的提供商，可以配置自定义基础 URL。

> [!WARNING]
>
> `model_provider="openai"`（或直接使用 `ChatOpenAI`）面向官方 OpenAI API 规范。路由器和代理的提供商特有字段可能无法被提取或保留。
>
> 对于 OpenRouter 和 LiteLLM，优先使用专门集成：
>
> * [通过 `ChatOpenRouter` 使用 OpenRouter](https://docs.langchain.com/oss/python/integrations/chat/openrouter)（`langchain-openrouter`）
> * [通过 `ChatLiteLLM` / `ChatLiteLLMRouter` 使用 LiteLLM](https://docs.langchain.com/oss/python/integrations/chat)（`langchain-litellm`）

> [accordion] 自定义基础 URL
>
> 许多模型提供商提供兼容 OpenAI 的 API（例如 [Together AI](https://www.together.ai/)、[vLLM](https://github.com/vllm-project/vllm)）。通过指定合适的 `base_url` 参数，可以使用 [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model) 接入这些提供商：
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> model = init_chat_model(
>     model="MODEL_NAME",
>     model_provider="openai",
>     base_url="BASE_URL",
>     api_key="YOUR_API_KEY",
> )
> ```
>
> > [!NOTE]
> >
> > 直接实例化聊天模型类时，参数名称可能因提供商而异。详情请查阅相应[参考文档](https://docs.langchain.com/oss/python/integrations/providers/overview.md)。

> [accordion] HTTP 代理配置
>
> 对于需要 HTTP 代理的部署，部分模型集成支持代理配置：
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from langchain_openai import ChatOpenAI
>
> model = ChatOpenAI(
>     model="gpt-6.1-sol",
>     openai_proxy="http://proxy.example.com:8080"
> )
> ```
>
> > [!NOTE]
> >
> > 不同集成的代理支持情况各异。代理配置选项请查阅特定模型提供商的[参考文档](https://docs.langchain.com/oss/python/integrations/providers/overview.md)。

### 对数概率

对某些模型，可在初始化时设置 `logprobs` 参数，使其返回 token 级对数概率，用于表示某个 token 出现的可能性：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
model = init_chat_model(
    model="gpt-6.1-sol",
    model_provider="openai"
).bind(logprobs=True)

response = model.invoke("Why do parrots talk?")
print(response.response_metadata["logprobs"])
```

### Token 用量

一些模型提供商将 token 用量信息作为调用响应的一部分返回。可用时，这些信息包含在相应模型生成的 [`AIMessage`](https://reference.langchain.com/python/langchain-core/messages/ai/AIMessage) 对象中。更多详情参见[消息](https://docs.langchain.com/oss/python/langchain/messages.md)指南。

> [!NOTE]
>
> 某些提供商 API，尤其是 OpenAI 和 Azure OpenAI 聊天补全 API，要求用户显式选择在流式场景中接收 token 用量数据。详情参见集成指南的[流式用量元数据](https://docs.langchain.com/oss/python/integrations/chat/openai#streaming-usage-metadata)部分。

可以使用回调或上下文管理器，追踪应用中跨模型的聚合 token 数，如下所示：

> [tab] 回调处理器
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from langchain.chat_models import init_chat_model
> from langchain_core.callbacks import UsageMetadataCallbackHandler
>
> model_1 = init_chat_model(model="gpt-5.4-mini")
> model_2 = init_chat_model(model="claude-haiku-4-5-20251001")
>
> callback = UsageMetadataCallbackHandler()
> result_1 = model_1.invoke("Hello", config={"callbacks": [callback]})
> result_2 = model_2.invoke("Hello", config={"callbacks": [callback]})
> print(callback.usage_metadata)
> ```
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> {
>     'gpt-5.4-mini': {
>         'input_tokens': 8,
>         'output_tokens': 10,
>         'total_tokens': 18,
>         'input_token_details': {'audio': 0, 'cache_read': 0},
>         'output_token_details': {'audio': 0, 'reasoning': 0}
>     },
>     'claude-haiku-4-5-20251001': {
>         'input_tokens': 8,
>         'output_tokens': 21,
>         'total_tokens': 29,
>         'input_token_details': {'cache_read': 0, 'cache_creation': 0}
>     }
> }
> ```

> [tab] 上下文管理器
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from langchain.chat_models import init_chat_model
> from langchain_core.callbacks import get_usage_metadata_callback
>
> model_1 = init_chat_model(model="gpt-5.4-mini")
> model_2 = init_chat_model(model="claude-haiku-4-5-20251001")
>
> with get_usage_metadata_callback() as cb:
>     model_1.invoke("Hello")
>     model_2.invoke("Hello")
>     print(cb.usage_metadata)
> ```
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> {
>     'gpt-5.4-mini': {
>         'input_tokens': 8,
>         'output_tokens': 10,
>         'total_tokens': 18,
>         'input_token_details': {'audio': 0, 'cache_read': 0},
>         'output_token_details': {'audio': 0, 'reasoning': 0}
>     },
>     'claude-haiku-4-5-20251001': {
>         'input_tokens': 8,
>         'output_tokens': 21,
>         'total_tokens': 29,
>         'input_token_details': {'cache_read': 0, 'cache_creation': 0}
>     }
> }
> ```

### 调用配置

调用模型时，可以通过 `config` 参数传入 [`RunnableConfig`](https://reference.langchain.com/python/langchain-core/runnables/config/RunnableConfig) 字典，提供额外配置，从而在运行时控制执行行为、回调与元数据追踪。

常见配置选项包括：

```python Invocation with config theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
response = model.invoke(
    "Tell me a joke",
    config={
        "run_name": "joke_generation",      # Custom name for this run
        "tags": ["humor", "demo"],          # Tags for categorization
        "metadata": {"user_id": "123"},     # Custom metadata
        "callbacks": [my_callback_handler], # Callback handlers
    }
)
```

以下情况下，这些配置值尤其有用：

* 使用 [LangSmith](https://docs.langchain.com/langsmith/observability.md) 追踪进行调试
* 实现自定义日志或监控
* 控制生产环境资源用量
* 跨复杂流水线追踪调用

> [accordion] 主要配置属性
>
> **run\_name** `string`
>
> 在日志和追踪中标识本次特定调用。子调用不继承。
>
> **tags** `string[]`
>
> 所有子调用都继承的标签，用于在调试工具中筛选和组织。
>
> **metadata** `object`
>
> 用于追踪额外上下文的自定义键值对，所有子调用都会继承。
>
> **max\_concurrency** `number`
>
> 使用 [`batch()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch) 或 [`batch_as_completed()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch_as_completed) 时，控制最大并行调用数。
>
> **callbacks** `array`
>
> 执行期间监控和响应事件的处理器。
>
> **recursion\_limit** `number`
>
> 链的最大递归深度，用于防止复杂流水线中的无限循环。

> [!TIP]
>
> 所有受支持属性，参见完整的 [`RunnableConfig`](https://reference.langchain.com/python/langchain-core/runnables/config/RunnableConfig) 参考。

### 可配置模型

通过指定 [`configurable_fields`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.configurable_fields)，也可以创建运行时可配置模型。如果不指定模型值，默认允许配置 `'model'` 和 `'model_provider'`。

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain.chat_models import init_chat_model

configurable_model = init_chat_model(temperature=0)

configurable_model.invoke(
    "what's your name",
    config={"configurable": {"model": "gpt-5-nano"}},  # Run with GPT-5-Nano
)
configurable_model.invoke(
    "what's your name",
    config={"configurable": {"model": "claude-sonnet-4-6"}},  # Run with Claude
)
```

> [accordion] 带默认值的可配置模型
>
> 可以创建带默认模型值的可配置模型，指定哪些参数可配置，并为可配置参数添加前缀：
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> first_model = init_chat_model(
>         model="gpt-5.4-mini",
>         temperature=0,
>         configurable_fields=("model", "model_provider", "temperature", "max_tokens"),
>         config_prefix="first",  # Useful when you have a chain with multiple models
> )
>
> first_model.invoke("what's your name")
> ```
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> first_model.invoke(
>     "what's your name",
>     config={
>         "configurable": {
>             "first_model": "claude-sonnet-4-6",
>             "first_temperature": 0.5,
>             "first_max_tokens": 100,
>         }
>     },
> )
> ```
>
> 关于 `configurable_fields` 和 `config_prefix` 的更多详情，参见 [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model) 参考。

> [accordion] 以声明式方式使用可配置模型
>
> 可以对可配置模型调用 `bind_tools`、`with_structured_output`、`with_configurable` 等声明式操作，并像普通实例化的聊天模型对象一样将其接入链中。
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> from pydantic import BaseModel, Field
>
>
> class GetWeather(BaseModel):
>     """Get the current weather in a given location"""
>
>         location: str = Field(description="The city and state, e.g. San Francisco, CA")
>
>
> class GetPopulation(BaseModel):
>     """Get the current population in a given location"""
>
>         location: str = Field(description="The city and state, e.g. San Francisco, CA")
>
>
> model = init_chat_model(temperature=0)
> model_with_tools = model.bind_tools([GetWeather, GetPopulation])
>
> model_with_tools.invoke(
>     "what's bigger in 2024 LA or NYC", config={"configurable": {"model": "gpt-5.4-mini"}}
> ).tool_calls
> ```
>
> ```
> [
>     {
>         'name': 'GetPopulation',
>         'args': {'location': 'Los Angeles, CA'},
>         'id': 'call_Ga9m8FAArIyEjItHmztPYA22',
>         'type': 'tool_call'
>     },
>     {
>         'name': 'GetPopulation',
>         'args': {'location': 'New York, NY'},
>         'id': 'call_jh2dEvBaAHRaw5JUDthOs7rt',
>         'type': 'tool_call'
>     }
> ]
> ```
>
> ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
> model_with_tools.invoke(
>     "what's bigger in 2024 LA or NYC",
>     config={"configurable": {"model": "claude-sonnet-4-6"}},
> ).tool_calls
> ```
>
> ```
> [
>     {
>         'name': 'GetPopulation',
>         'args': {'location': 'Los Angeles, CA'},
>         'id': 'toolu_01JMufPf4F4t2zLj7miFeqXp',
>         'type': 'tool_call'
>     },
>     {
>         'name': 'GetPopulation',
>         'args': {'location': 'New York City, NY'},
>         'id': 'toolu_01RQBHcE8kEEbYTuuS8WqY1u',
>         'type': 'tool_call'
>     }
> ]
> ```

### 动态模型选择

动态模型在运行时根据当前状态和上下文选择，从而支持复杂路由逻辑和成本优化。运行时是智能体的执行环境，包含在整个执行期间保留的不可变配置及上下文数据（例如用户 ID、会话详情或应用专属配置）。状态是流经智能体执行过程的数据，包括消息、自定义字段，以及任何需要在处理过程中追踪并可能修改的信息（例如用户偏好或工具用量统计）。

要使用动态模型，通过 [`@wrap_model_call`](https://reference.langchain.com/python/langchain/agents/middleware/types/wrap_model_call) 装饰器创建中间件，修改请求中的模型：

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse


basic_model = ChatOpenAI(model="gpt-5.4-mini")
advanced_model = ChatOpenAI(model="gpt-6.1-sol")

@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """Choose model based on conversation complexity."""
    message_count = len(request.state["messages"])

    if message_count > 10:
        # Use an advanced model for longer conversations
        model = advanced_model
    else:
        model = basic_model

    return handler(request.override(model=model))

agent = create_agent(
    model=basic_model,  # Default model
    tools=[],
    middleware=[dynamic_model_selection]
)
```

> [!WARNING]
>
> 使用结构化输出时，不支持预绑定模型（即已经调用过 [`bind_tools`](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel/bind_tools) 的模型）。如果需要结合动态模型选择与结构化输出，请确保传给中间件的模型未经预绑定。

> [!TIP]
>
> 模型配置详情，参见[模型](https://docs.langchain.com/oss/python/langchain/models.md)。动态模型选择模式，参见[中间件中的动态模型](https://docs.langchain.com/oss/python/langchain/middleware.md#dynamic-model)。

***

[连接这些文档](https://docs.langchain.com/use-these-docs.md) ，通过 MCP 将其接入你选择的智能体，以获取实时答案。

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/models.mdx) 或[提交问题](https://github.com/langchain-ai/docs/issues/new/choose).
