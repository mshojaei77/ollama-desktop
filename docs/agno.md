# What is Agno?

> **Agno is a full-stack framework for building Multi-Agent Systems with memory, knowledge and reasoning.**

Engineers and researchers use Agno to build the 5 levels of Agentic Systems:

* **Level 1:** Agents with tools and instructions ([example](/introduction/agents#level-1%3A-agents-with-tools-and-instructions)).
* **Level 2:** Agents with knowledge and storage ([example](/introduction/agents#level-2%3A-agents-with-knowledge-and-storage)).
* **Level 3:** Agents with memory and reasoning ([example](/introduction/agents#level-3%3A-agents-with-memory-and-reasoning)).
* **Level 4:** Agent Teams that can reason and collaborate ([example](/introduction/multi-agent-systems#level-4%3A-agent-teams-that-can-reason-and-collaborate)).
* **Level 5:** Agentic Workflows with state and determinism ([example](/introduction/multi-agent-systems#level-5%3A-agentic-workflows-with-state-and-determinism)).

**Example:** Level 1 Reasoning Agent that uses the YFinance API to answer questions:

```python Reasoning Finance Agent
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools

reasoning_agent = Agent(
    model=Claude(id="claude-sonnet-4-20250514"),
    tools=[
        ReasoningTools(add_instructions=True),
        YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True),
    ],
    instructions="Use tables to display data.",
    markdown=True,
)
```

<Accordion title="Watch the reasoning finance agent in action">
  <video autoPlay muted controls className="w-full aspect-video" style={{ borderRadius: "8px" }} src="https://mintlify.s3.us-west-1.amazonaws.com/agno/videos/reasoning_finance_agent.mp4" />
</Accordion>

# Getting Started

If you're new to Agno, learn how to build your [first Agent](/introduction/agents), chat with it on the [playground](/introduction/playground) and [monitor](/introduction/monitoring) it on [app.agno.com](https://app.agno.com).

<CardGroup cols={3}>
  <Card title="Your first Agents" icon="user-astronaut" iconType="duotone" href="/introduction/agents">
    Learn how to build Agents with Agno
  </Card>

  <Card title="Agent Playground" icon="comment-dots" iconType="duotone" href="introduction/playground">
    Chat with your Agents using a beautiful Agent UI
  </Card>

  <Card title="Agent Monitoring" icon="rocket-launch" iconType="duotone" href="introduction/monitoring">
    Monitor your Agents on [agno.com](https://app.agno.com)
  </Card>
</CardGroup>

After that, dive deeper into the [concepts below](/introduction#dive-deeper) or explore the [examples gallery](/examples) to build real-world applications with Agno.

# Why Agno?

Agno will help you build best-in-class, highly-performant agentic systems, saving you hours of research and boilerplate. Here are some key features that set Agno apart:

* **Model Agnostic**: Agno provides a unified interface to 23+ model providers, no lock-in.
* **Highly performant**: Agents instantiate in **\~3μs** and use **\~6.5Kib** memory on average.
* **Reasoning is a first class citizen**: Reasoning improves reliability and is a must-have for complex autonomous agents. Agno supports 3 approaches to reasoning: Reasoning Models, `ReasoningTools` or our custom `chain-of-thought` approach.
* **Natively Multi-Modal**: Agno Agents are natively multi-modal, they accept text, image, audio and video as input and generate text, image, audio and video as output.
* **Advanced Multi-Agent Architecture**: Agno provides an industry leading multi-agent architecture (**Agent Teams**) with reasoning, memory, and shared context.
* **Built-in Agentic Search**: Agents can search for information at runtime using 20+ vector databases. Agno provides state-of-the-art Agentic RAG, **fully async and highly performant.**
* **Built-in Memory & Session Storage**: Agents come with built-in `Storage` & `Memory` drivers that give your Agents long-term memory and session storage.
* **Structured Outputs**: Agno Agents can return fully-typed responses using model provided structured outputs or `json_mode`.
* **Pre-built FastAPI Routes**: After building your Agents, serve them using pre-built FastAPI routes. 0 to production in minutes.
* **Monitoring**: Monitor agent sessions and performance in real-time on [agno.com](https://app.agno.com).

# Dive deeper

Agno is a battle-tested framework with a state of the art reasoning and multi-agent architecture, read the following guides to learn more:

<CardGroup cols={3}>
  <Card title="Agents" icon="user-astronaut" iconType="duotone" href="/agents">
    Learn how to build lightning fast Agents.
  </Card>

  <Card title="Teams" icon="microchip" iconType="duotone" href="/teams">
    Build autonomous multi-agent teams.
  </Card>

  <Card title="Models" icon="cube" iconType="duotone" href="/models">
    Use any model, any provider, no lock-in.
  </Card>

  <Card title="Tools" icon="screwdriver-wrench" iconType="duotone" href="/tools">
    100s of tools to extend your Agents.
  </Card>

  <Card title="Reasoning" icon="brain-circuit" iconType="duotone" href="/reasoning">
    Make Agents "think" and "analyze".
  </Card>

  <Card title="Knowledge" icon="server" iconType="duotone" href="/knowledge">
    Give Agents domain-specific knowledge.
  </Card>

  <Card title="Vector Databases" icon="spider-web" iconType="duotone" href="/vectordb">
    Store and search your knowledge base.
  </Card>

  <Card title="Storage" icon="database" iconType="duotone" href="/storage">
    Persist Agent session and state in a database.
  </Card>

  <Card title="Memory" icon="lightbulb" iconType="duotone" href="/agents/memory">
    Remember user details and session summaries.
  </Card>

  <Card title="Embeddings" icon="network-wired" iconType="duotone" href="/embedder">
    Generate embeddings for your knowledge base.
  </Card>

  <Card title="Workflows" icon="diagram-project" iconType="duotone" href="/workflows">
    Deterministic, stateful, multi-agent workflows.
  </Card>

  <Card title="Evals" icon="shield" iconType="duotone" href="/evals">
    Evaluate, monitor and improve your Agents.
  </Card>
</CardGroup>


# What are Agents?

> **Agents are AI programs that operate autonomously.**

Traditional software follows a pre-programmed sequence of steps. Agents dynamically determine their course of action using a machine learning **model**, its core components are:

* **Model:** controls the flow of execution. It decides whether to reason, act or respond.
* **Tools:** enable an Agent to take actions and interact with external systems.
* **Instructions:** are how we program the Agent, teaching it how to use tools and respond.

Agents also have **memory**, **knowledge**, **storage** and the ability to **reason**:

* **Reasoning:** enables Agents to "think" before responding and "analyze" the results of their actions (i.e. tool calls), this improves reliability and quality of responses.
* **Knowledge:** is domain-specific information that the Agent can **search at runtime** to make better decisions and provide accurate responses (RAG). Knowledge is stored in a vector database and this **search at runtime** pattern is known as Agentic RAG/Agentic Search.
* **Storage:** is used by Agents to save session history and state in a database. Model APIs are stateless and storage enables us to continue conversations from where they left off. This makes Agents stateful, enabling multi-turn, long-term conversations.
* **Memory:** gives Agents the ability to store and recall information from previous interactions, allowing them to learn user preferences and personalize their responses.

<Check>Let's build a few Agents to see how they work.</Check>

## Level 1: Agents with tools and instructions

The simplest Agent has a model, a tool and instructions. Let's build an Agent that can fetch data using the `yfinance` library, along with instructions to display the results in a table.

```python level_1_agent.py
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.yfinance import YFinanceTools

agent = Agent(
    model=Claude(id="claude-sonnet-4-20250514"),
    tools=[YFinanceTools(stock_price=True)],
    instructions="Use tables to display data. Don't include any other text.",
    markdown=True,
)
agent.print_response("What is the stock price of Apple?", stream=True)
```

Create a virtual environment, install dependencies, export your API key and run the Agent.

<Steps>
  <Step title="Setup your virtual environment">
    <CodeGroup>
      ```bash Mac
      uv venv --python 3.12
      source .venv/bin/activate
      ```

      ```bash Windows
      uv venv --python 3.12
      .venv/Scripts/activate
      ```
    </CodeGroup>
  </Step>

  <Step title="Install dependencies">
    <CodeGroup>
      ```bash Mac
      uv pip install -U agno anthropic yfinance
      ```

      ```bash Windows
      uv pip install -U agno anthropic yfinance
      ```
    </CodeGroup>
  </Step>

  <Step title="Export your Anthropic key">
    <CodeGroup>
      ```bash Mac
      export ANTHROPIC_API_KEY=sk-***
      ```

      ```bash Windows
      setx ANTHROPIC_API_KEY sk-***
      ```
    </CodeGroup>
  </Step>

  <Step title="Run the agent">
    ```shell
    python agent_with_tools.py
    ```
  </Step>
</Steps>

<Note>
  Set `debug_mode=True` or `export AGNO_DEBUG=true` to see the system prompt and user messages.
</Note>

## Level 2: Agents with knowledge and storage

**Knowledge:** While models have a large amount of training data, we almost always need to give them domain-specific information to make better decisions and provide accurate responses (RAG). We store this information in a vector database and let the Agent **search** it at runtime.

**Storage:** Model APIs are stateless and `Storage` drivers save chat history and state to a database. When the Agent runs, it reads the chat history and state from the database and add it to the messages list, resuming the conversation and making the Agent stateful.

In this example, we'll use:

* `UrlKnowledge` to load Agno documentation to LanceDB, using OpenAI for embeddings.
* `SqliteStorage` to save the Agent's session history and state in a database.

```python level_2_agent.py
from agno.agent import Agent
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.url import UrlKnowledge
from agno.models.anthropic import Claude
from agno.storage.sqlite import SqliteStorage
from agno.vectordb.lancedb import LanceDb, SearchType

# Load Agno documentation in a knowledge base
# You can also use `https://docs.agno.com/llms-full.txt` for the full documentation
knowledge = UrlKnowledge(
    urls=["https://docs.agno.com/introduction.md"],
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs",
        search_type=SearchType.hybrid,
        # Use OpenAI for embeddings
        embedder=OpenAIEmbedder(id="text-embedding-3-small", dimensions=1536),
    ),
)

# Store agent sessions in a SQLite database
storage = SqliteStorage(table_name="agent_sessions", db_file="tmp/agent.db")

agent = Agent(
    name="Agno Assist",
    model=Claude(id="claude-sonnet-4-20250514"),
    instructions=[
        "Search your knowledge before answering the question.",
        "Only include the output in your response. No other text.",
    ],
    knowledge=knowledge,
    storage=storage,
    add_datetime_to_instructions=True,
    # Add the chat history to the messages
    add_history_to_messages=True,
    # Number of history runs
    num_history_runs=3,
    markdown=True,
)

if __name__ == "__main__":
    # Load the knowledge base, comment out after first run
    # Set recreate to True to recreate the knowledge base if needed
    agent.knowledge.load(recreate=False)
    agent.print_response("What is Agno?", stream=True)
```

Install dependencies, export your `OPENAI_API_KEY` and run the Agent

<Steps>
  <Step title="Install new dependencies">
    <CodeGroup>
      ```bash Mac
      uv pip install -U lancedb tantivy openai sqlalchemy
      ```

      ```bash Windows
      uv pip install -U lancedb tantivy openai sqlalchemy
      ```
    </CodeGroup>
  </Step>

  <Step title="Run the agent">
    ```shell
    python level_2_agent.py
    ```
  </Step>
</Steps>

## Level 3: Agents with memory and reasoning

* **Reasoning:** enables Agents to **"think" & "analyze"**, improving reliability and quality. `ReasoningTools` is one of the best approaches to improve an Agent's response quality.
* **Memory:** enables Agents to classify, store and recall user preferences, personalizing their responses. Memory helps the Agent build personas and learn from previous interactions.

```python level_3_agent.py
from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.anthropic import Claude
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools

memory = Memory(
    # Use any model for creating and managing memories
    model=Claude(id="claude-sonnet-4-20250514"),
    # Store memories in a SQLite database
    db=SqliteMemoryDb(table_name="user_memories", db_file="tmp/agent.db"),
    # We disable deletion by default, enable it if needed
    delete_memories=True,
    clear_memories=True,
)

agent = Agent(
    model=Claude(id="claude-sonnet-4-20250514"),
    tools=[
        ReasoningTools(add_instructions=True),
        YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True),
    ],
    # User ID for storing memories, `default` if not provided
    user_id="ava",
    instructions=[
        "Use tables to display data.",
        "Include sources in your response.",
        "Only include the report in your response. No other text.",
    ],
    memory=memory,
    # Let the Agent manage its memories
    enable_agentic_memory=True,
    markdown=True,
)

if __name__ == "__main__":
    # This will create a memory that "ava's" favorite stocks are NVIDIA and TSLA
    agent.print_response(
        "My favorite stocks are NVIDIA and TSLA",
        stream=True,
        show_full_reasoning=True,
        stream_intermediate_steps=True,
    )
    # This will use the memory to answer the question
    agent.print_response(
        "Can you compare my favorite stocks?",
        stream=True,
        show_full_reasoning=True,
        stream_intermediate_steps=True,
    )
```

Run the Agent

```shell
python level_3_agent.py
```

<Tip>You can use the `Memory` and `Reasoning` separately, you don't need to use them together.</Tip>


# OpenAI Like

> Learn how to use OpenAI-like models in Agno.

Many providers like Together, Groq, Sambanova, etc support the OpenAI API format. Use the `OpenAILike` model to access them by replacing the `base_url`.

## Example

<CodeGroup>
  ```python agent.py
  from os import getenv
  from agno.agent import Agent, RunResponse
  from agno.models.openai.like import OpenAILike

  agent = Agent(
      model=OpenAILike(
          id="mistralai/Mixtral-8x7B-Instruct-v0.1",
          api_key=getenv("TOGETHER_API_KEY"),
          base_url="https://api.together.xyz/v1",
      )
  )

  # Print the response in the terminal
  agent.print_response("Share a 2 sentence horror story.")
  ```
</CodeGroup>

## Params

<Snippet file="model-openai-like-reference.mdx" />

`OpenAILike` also support all the params of [OpenAIChat](/reference/models/openai)


# What are Tools?

> Tools are functions that helps Agno Agents to interact with the external world.

Tools make agents - "agentic" by enabling them to interact with external systems like searching the web, running SQL, sending an email or calling APIs.

Agno comes with 80+ pre-built toolkits, but in most cases, you will write your own tools. The general syntax is:

```python
import random

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool


@tool(show_result=True, stop_after_tool_call=True)
def get_weather(city: str) -> str:
    """Get the weather for a city."""
    # In a real implementation, this would call a weather API
    weather_conditions = ["sunny", "cloudy", "rainy", "snowy", "windy"]
    random_weather = random.choice(weather_conditions)

    return f"The weather in {city} is {random_weather}."


agent = Agent(
    model=OpenAIChat(model="gpt-4o-mini"),
    tools=[get_weather],
    markdown=True,
)
agent.print_response("What is the weather in San Francisco?", stream=True)
```

<Tip>
  In the example above, the `get_weather` function is a tool. When it is called, the tool result will be shown in the output because we set `show_result=True`.

  Then, the Agent will stop after the tool call because we set `stop_after_tool_call=True`.
</Tip>

### Using the Toolkit Class

The `Toolkit` class provides a way to manage multiple tools with additional control over their execution. You can specify which tools should stop the agent after execution and which should have their results shown.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.googlesearch import GoogleSearchTools

agent = Agent(
    model=OpenAIChat(id="gpt-4.5-preview"),
    tools=[
        GoogleSearchTools(
            stop_after_tool_call_tools=["google_search"],
            show_result_tools=["google_search"],
        )
    ],
    show_tool_calls=True,
)

agent.print_response("What's the latest about gpt 4.5?", markdown=True)
```

In this example, the `GoogleSearchTools` toolkit is configured to stop the agent after executing the `google_search` function and to show the result of this function.

Read more about:

* [Available Toolkits](/tools/toolkits)
* [Using functions as tools](/tools/tool-decorator)


# What are Tools?

> Tools are functions that helps Agno Agents to interact with the external world.

Tools make agents - "agentic" by enabling them to interact with external systems like searching the web, running SQL, sending an email or calling APIs.

Agno comes with 80+ pre-built toolkits, but in most cases, you will write your own tools. The general syntax is:

```python
import random

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool


@tool(show_result=True, stop_after_tool_call=True)
def get_weather(city: str) -> str:
    """Get the weather for a city."""
    # In a real implementation, this would call a weather API
    weather_conditions = ["sunny", "cloudy", "rainy", "snowy", "windy"]
    random_weather = random.choice(weather_conditions)

    return f"The weather in {city} is {random_weather}."


agent = Agent(
    model=OpenAIChat(model="gpt-4o-mini"),
    tools=[get_weather],
    markdown=True,
)
agent.print_response("What is the weather in San Francisco?", stream=True)
```

<Tip>
  In the example above, the `get_weather` function is a tool. When it is called, the tool result will be shown in the output because we set `show_result=True`.

  Then, the Agent will stop after the tool call because we set `stop_after_tool_call=True`.
</Tip>

### Using the Toolkit Class

The `Toolkit` class provides a way to manage multiple tools with additional control over their execution. You can specify which tools should stop the agent after execution and which should have their results shown.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.googlesearch import GoogleSearchTools

agent = Agent(
    model=OpenAIChat(id="gpt-4.5-preview"),
    tools=[
        GoogleSearchTools(
            stop_after_tool_call_tools=["google_search"],
            show_result_tools=["google_search"],
        )
    ],
    show_tool_calls=True,
)

agent.print_response("What's the latest about gpt 4.5?", markdown=True)
```

In this example, the `GoogleSearchTools` toolkit is configured to stop the agent after executing the `google_search` function and to show the result of this function.

Read more about:

* [Available Toolkits](/tools/toolkits)
* [Using functions as tools](/tools/tool-decorator)

# What is Knowledge?

> Knowledge is domain-specific information that the Agent can search at runtime to make better decisions (dynamic few-shot learning) and provide accurate responses (agentic RAG).

Knowledge is stored in a vector db and this searching on demand pattern is called Agentic RAG.

<Accordion title="Dynamic Few-Shot Learning: Text2Sql Agent" icon="database">
  Example: If we're building a Text2Sql Agent, we'll need to give the table schemas, column names, data types, example queries, common "gotchas" to help it generate the best-possible SQL query.

  We're obviously not going to put this all in the system prompt, instead we store this information in a vector database and let the Agent query it at runtime.

  Using this information, the Agent can then generate the best-possible SQL query. This is called dynamic few-shot learning.
</Accordion>

**Agno Agents use Agentic RAG** by default, meaning if you add `knowledge` to an Agent, it will search this knowledge base, at runtime, for the specific information it needs to achieve its task.

The pseudo steps for adding knowledge to an Agent are:

```python
from agno.agent import Agent, AgentKnowledge

# Create a knowledge base for the Agent
knowledge_base = AgentKnowledge(vector_db=...)

# Add information to the knowledge base
knowledge_base.load_text("The sky is blue")

# Add the knowledge base to the Agent and
# give it a tool to search the knowledge base as needed
agent = Agent(knowledge=knowledge_base, search_knowledge=True)
```

We can give our agent access to the knowledge base in the following ways:

* We can set `search_knowledge=True` to add a `search_knowledge_base()` tool to the Agent. `search_knowledge` is `True` **by default** if you add `knowledge` to an Agent.
* We can set `add_references=True` to automatically add references from the knowledge base to the Agent's prompt. This is the traditional 2023 RAG approach.

<Tip>
  If you need complete control over the knowledge base search, you can pass your own `retriever` function with the following signature:

  ```python
  def retriever(agent: Agent, query: str, num_documents: Optional[int], **kwargs) -> Optional[list[dict]]:
    ...
  ```

  This function is called during `search_knowledge_base()` and is used by the Agent to retrieve references from the knowledge base.
  For more details check out the [Custom Retriever](../knowledge/custom_retriever) page.
</Tip>

## Vector Databases

While any type of storage can act as a knowledge base, vector databases offer the best solution for retrieving relevant results from dense information quickly. Here's how vector databases are used with Agents:

<Steps>
  <Step title="Chunk the information">
    Break down the knowledge into smaller chunks to ensure our search query
    returns only relevant results.
  </Step>

  <Step title="Load the knowledge base">
    Convert the chunks into embedding vectors and store them in a vector
    database.
  </Step>

  <Step title="Search the knowledge base">
    When the user sends a message, we convert the input message into an
    embedding and "search" for nearest neighbors in the vector database.
  </Step>
</Steps>

## Loading the Knowledge Base

Before you can use a knowledge base, it needs to be loaded with embeddings that will be used for retrieval.

### Asynchronous Loading

Many vector databases support asynchronous operations, which can significantly improve performance when loading large knowledge bases. You can leverage this capability using the `aload()` method:

```python
import asyncio

from agno.agent import Agent
from agno.knowledge.pdf import PDFKnowledgeBase, PDFReader
from agno.vectordb.qdrant import Qdrant

COLLECTION_NAME = "pdf-reader"

vector_db = Qdrant(collection=COLLECTION_NAME, url="http://localhost:6333")

# Create a knowledge base with the PDFs from the data/pdfs directory
knowledge_base = PDFKnowledgeBase(
    path="data/pdf",
    vector_db=vector_db,
    reader=PDFReader(chunk=True),
)

# Create an agent with the knowledge base
agent = Agent(
    knowledge=knowledge_base,
    search_knowledge=True,
)

if __name__ == "__main__":
    # Comment out after first run
    asyncio.run(knowledge_base.aload(recreate=False))

    # Create and use the agent
    asyncio.run(agent.aprint_response("How to make Thai curry?", markdown=True))
```

Using `aload()` ensures you take full advantage of the non-blocking operations, concurrent processing, and reduced latency that async vector database operations offer. This is especially valuable in production environments with high throughput requirements.

For more details on vector database async capabilities, see the [Vector Database Introduction](/vectordb/introduction).

Use one of the following knowledge bases to simplify the chunking, loading, searching and optimization process:

* [ArXiv knowledge base](/knowledge/arxiv): Load ArXiv papers to a knowledge base
* [Combined knowledge base](/knowledge/combined): Combine multiple knowledge bases into 1
* [CSV knowledge base](/knowledge/csv): Load local CSV files to a knowledge base
* [CSV URL knowledge base](/knowledge/csv-url): Load CSV files from a URL to a knowledge base
* [Document knowledge base](/knowledge/document): Load local docx files to a knowledge base
* [JSON knowledge base](/knowledge/json): Load JSON files to a knowledge base
* [LangChain knowledge base](/knowledge/langchain): Use a Langchain retriever as a knowledge base
* [PDF knowledge base](/knowledge/pdf): Load local PDF files to a knowledge base
* [PDF URL knowledge base](/knowledge/pdf-url): Load PDF files from a URL to a knowledge base
* [S3 PDF knowledge base](/knowledge/s3_pdf): Load PDF files from S3 to a knowledge base
* [S3 Text knowledge base](/knowledge/s3_text): Load text files from S3 to a knowledge base
* [Text knowledge base](/knowledge/text): Load text/docx files to a knowledge base
* [Website knowledge base](/knowledge/website): Load website data to a knowledge base
* [Wikipedia knowledge base](/knowledge/wikipedia): Load wikipedia articles to a knowledge base

# Recursive Chunking

Recursive chunking is a method of splitting documents into smaller chunks by recursively applying a chunking strategy. This is useful when you want to process large documents in smaller, manageable pieces.

```python
from agno.agent import Agent
from agno.document.chunking.recursive import RecursiveChunking
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=PgVector(table_name="recipes_recursive_chunking", db_url=db_url),
    chunking_strategy=RecursiveChunking(),
)
knowledge_base.load(recreate=False)  # Comment out after first run

agent = Agent(
    knowledge_base=knowledge_base,
    search_knowledge=True,
)

agent.print_response("How to make Thai curry?", markdown=True)

```

## Recursive Chunking Params

<Snippet file="chunking-recursive.mdx" />
# Document Chunking

Document chunking is a method of splitting documents into smaller chunks based on document structure like paragraphs and sections. It analyzes natural document boundaries rather than splitting at fixed character counts. This is useful when you want to process large documents while preserving semantic meaning and context.

## Usage

```python
from agno.agent import Agent
from agno.document.chunking.document import DocumentChunking
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=PgVector(table_name="recipes_document_chunking", db_url=db_url),
    chunking_strategy=DocumentChunking(),
)
knowledge_base.load(recreate=False)  # Comment out after first run

agent = Agent(
    knowledge_base=knowledge_base,
    search_knowledge=True,
)

agent.print_response("How to make Thai curry?", markdown=True)

```

## Document Chunking Params

<Snippet file="chunking-document.mdx" />

# What are Vector Databases?

> Vector databases enable us to store information as embeddings and search for "results similar" to our input query using cosine similarity or full text search. These results are then provided to the Agent as context so it can respond in a context-aware manner using Retrieval Augmented Generation (RAG).

Here's how vector databases are used with Agents:

<Steps>
  <Step title="Chunk the information">
    Break down the knowledge into smaller chunks to ensure our search query
    returns only relevant results.
  </Step>

  <Step title="Load the knowledge base">
    Convert the chunks into embedding vectors and store them in a vector
    database.
  </Step>

  <Step title="Search the knowledge base">
    When the user sends a message, we convert the input message into an
    embedding and "search" for nearest neighbors in the vector database.
  </Step>
</Steps>

Many vector databases also support hybrid search, which combines the power of vector similarity search with traditional keyword-based search. This approach can significantly improve the relevance and accuracy of search results, especially for complex queries or when dealing with diverse types of data.

Hybrid search typically works by:

1. Performing a vector similarity search to find semantically similar content.
2. Conducting a keyword-based search to identify exact or close matches.
3. Combining the results using a weighted approach to provide the most relevant information.

This capability allows for more flexible and powerful querying, often yielding better results than either method alone.

<Card title="⚡ Asynchronous Operations">
  <p>Several vector databases support asynchronous operations, offering improved performance through non-blocking operations, concurrent processing, reduced latency, and seamless integration with FastAPI and async agents.</p>

  <Tip className="mt-4">
    When building with Agno, use the <code>aload</code> methods for async knowledge base loading in production environments.
  </Tip>
</Card>

## Supported Vector Databases

The following VectorDb are currently supported:

* [PgVector](/vectordb/pgvector)\*
* [Cassandra](/vectordb/cassandra)
* [ChromaDb](/vectordb/chroma)
* [Couchbase](/vectordb/couchbase)\*
* [Clickhouse](/vectordb/clickhouse)
* [LanceDb](/vectordb/lancedb)\*
* [Milvus](/vectordb/milvus)
* [MongoDb](/vectordb/mongodb)
* [Pinecone](/vectordb/pinecone)\*
* [Qdrant](/vectordb/qdrant)
* [Singlestore](/vectordb/singlestore)
* [Weaviate](/vectordb/weaviate)

\*hybrid search supported

Each of these databases has its own strengths and features, including varying levels of support for hybrid search and async operations. Be sure to check the specific documentation for each to understand how to best leverage their capabilities in your projects.
# LanceDB Agent Knowledge

## Setup

```shell
pip install lancedb
```

## Example

```python agent_with_knowledge.py
import typer
from typing import Optional
from rich.prompt import Prompt

from agno.agent import Agent
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType

# LanceDB Vector DB
vector_db = LanceDb(
    table_name="recipes",
    uri="/tmp/lancedb",
    search_type=SearchType.keyword,
)

# Knowledge Base
knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=vector_db,
)

def lancedb_agent(user: str = "user"):
    run_id: Optional[str] = None

    agent = Agent(
        run_id=run_id,
        user_id=user,
        knowledge=knowledge_base,
        show_tool_calls=True,
        debug_mode=True,
    )

    if run_id is None:
        run_id = agent.run_id
        print(f"Started Run: {run_id}\n")
    else:
        print(f"Continuing Run: {run_id}\n")

    while True:
        message = Prompt.ask(f"[bold] :sunglasses: {user} [/bold]")
        if message in ("exit", "bye"):
            break
        agent.print_response(message)

if __name__ == "__main__":
    # Comment out after first run
    knowledge_base.load(recreate=True)

    typer.run(lancedb_agent)
```

<Card title="Async Support ⚡">
  <div className="mt-2">
    <p>
      LanceDB also supports asynchronous operations, enabling concurrency and leading to better performance.
    </p>

    ```python async_lance_db.py
    # install lancedb - `pip install lancedb`
    import asyncio

    from agno.agent import Agent
    from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
    from agno.vectordb.lancedb import LanceDb

    # Initialize LanceDB
    vector_db = LanceDb(
        table_name="recipes",
        uri="tmp/lancedb",  # You can change this path to store data elsewhere
    )

    # Create knowledge base
    knowledge_base = PDFUrlKnowledgeBase(
        urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
        vector_db=vector_db,
    )
    agent = Agent(knowledge=knowledge_base, show_tool_calls=True, debug_mode=True)

    if __name__ == "__main__":
        # Load knowledge base asynchronously
        asyncio.run(knowledge_base.aload(recreate=False))  # Comment out after first run

        # Create and use the agent asynchronously
        asyncio.run(agent.aprint_response("How to make Tom Kha Gai", markdown=True))
    ```

    <Tip className="mt-4">
      Use <code>aload()</code> and <code>aprint\_response()</code> methods with <code>asyncio.run()</code> for non-blocking operations in high-throughput applications.
    </Tip>
  </div>
</Card>

## LanceDb Params

<Snippet file="vectordb_lancedb_params.mdx" />

## Developer Resources

* View [Cookbook (Sync)](https://github.com/agno-agi/agno/blob/main/cookbook/agent_concepts/knowledge/vector_dbs/lance_db/lance_db.py)
* View [Cookbook (Async)](https://github.com/agno-agi/agno/blob/main/cookbook/agent_concepts/knowledge/vector_dbs/lance_db/async_lance_db.py)
# What are Embedders?

> Learn how to use embedders with Agno to convert complex information into vector representations.

An Embedder converts complex information into vector representations, allowing it to be stored in a vector database. By transforming data into embeddings, the embedder enables efficient searching and retrieval of contextually relevant information. This process enhances the responses of language models by providing them with the necessary business context, ensuring they are context-aware. Agno uses the `OpenAIEmbedder` as the default embedder, but other embedders are supported as well. Here is an example:

```python
from agno.agent import Agent, AgentKnowledge
from agno.vectordb.pgvector import PgVector
from agno.embedder.openai import OpenAIEmbedder

# Create knowledge base
knowledge_base=AgentKnowledge(
    vector_db=PgVector(
        db_url=db_url,
        table_name=embeddings_table,
        embedder=OpenAIEmbedder(),
    ),
    # 2 references are added to the prompt
    num_documents=2,
),

# Add information to the knowledge base
knowledge_base.load_text("The sky is blue")

# Add the knowledge base to the Agent
agent = Agent(knowledge_base=knowledge_base)
```

The following embedders are supported:

* [OpenAI](/embedder/openai)
* [Gemini](/embedder/gemini)
* [Ollama](/embedder/ollama)
* [Voyage AI](/embedder/voyageai)
* [Azure OpenAI](/embedder/azure_openai)
* [Mistral](/embedder/mistral)
* [Fireworks](/embedder/fireworks)
* [Together](/embedder/together)
* [HuggingFace](/embedder/huggingface)
* [Qdrant FastEmbed](/embedder/qdrant_fastembed)
# Ollama Embedder

The `OllamaEmbedder` can be used to embed text data into vectors locally using Ollama.

<Note>The model used for generating embeddings needs to run locally. In this case it is `openhermes` so you have to [install `ollama`](https://ollama.com/download) and run `ollama pull openhermes` in your terminal.</Note>

## Usage

```python cookbook/embedders/ollama_embedder.py
from agno.agent import AgentKnowledge
from agno.vectordb.pgvector import PgVector
from agno.embedder.ollama import OllamaEmbedder

# Embed sentence in database
embeddings = OllamaEmbedder(id="openhermes").get_embedding("The quick brown fox jumps over the lazy dog.")

# Print the embeddings and their dimensions
print(f"Embeddings: {embeddings[:5]}")
print(f"Dimensions: {len(embeddings)}")

# Use an embedder in a knowledge base
knowledge_base = AgentKnowledge(
    vector_db=PgVector(
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        table_name="ollama_embeddings",
        embedder=OllamaEmbedder(),
    ),
    num_documents=2,
)
```

## Params

| Parameter       | Type                       | Default        | Description                                                               |
| --------------- | -------------------------- | -------------- | ------------------------------------------------------------------------- |
| `model`         | `str`                      | `"openhermes"` | The name of the model used for generating embeddings.                     |
| `dimensions`    | `int`                      | `4096`         | The dimensionality of the embeddings generated by the model.              |
| `host`          | `str`                      | -              | The host address for the API endpoint.                                    |
| `timeout`       | `Any`                      | -              | The timeout duration for API requests.                                    |
| `options`       | `Any`                      | -              | Additional options for configuring the API request.                       |
| `client_kwargs` | `Optional[Dict[str, Any]]` | -              | Additional keyword arguments for configuring the API client. Optional.    |
| `ollama_client` | `Optional[OllamaClient]`   | -              | An instance of the OllamaClient to use for making API requests. Optional. |

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/blob/main/cookbook/agent_concepts/knowledge/embedders/ollama_embedder.py)
