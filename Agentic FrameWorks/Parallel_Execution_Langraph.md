# Module 4: Agent Frameworks --- Topic 9/10

## Streaming, Async Execution and Parallel Graph Execution in LangGraph

So far, we have learned how to build agents, execute tools, use
conditional routing, create loops, and checkpoint graph state.

Now consider an important production problem:

Suppose your AI agent takes 15 seconds to generate a response. Should
the user stare at a blank screen for 15 seconds?

**No.** We should deliver the response progressively. We should also
execute independent tasks concurrently to reduce latency.

This topic covers three concepts:

1.  Streaming --- progressively delivering a response.
2.  Async execution --- performing I/O operations without blocking the
    event loop.
3.  Parallel graph execution --- executing independent nodes in the same
    graph superstep.

------------------------------------------------------------------------

## 1. What is Streaming?

### Normal execution

``` python
response = model.invoke("Explain AI agents")
print(response.content)
```

The complete response becomes available after the model finishes.

### Streaming execution

``` python
for chunk in model.stream("Explain AI agents"):
    print(chunk.content, end="", flush=True)
```

The output arrives in chunks.

Illustrative comparison:

``` text
Normal response:
Wait...
Complete response appears at once.

Streaming response:
AI
AI agents
AI agents use tools
AI agents use tools to perform tasks.
```

Streaming is particularly useful for:

-   Chat applications
-   Coding agents
-   Long-running research agents
-   AI-powered IDEs
-   Real-time customer support

### LangChain model streaming

``` python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="YOUR_AVAILABLE_MODEL",
    temperature=0,
)

for chunk in model.stream("Explain tool calling"):
    print(chunk.content, end="", flush=True)
```

Important distinction:

  Method        Behavior
  ------------- --------------------------------
  `invoke()`    Complete response
  `stream()`    Response chunks
  `ainvoke()`   Asynchronous complete response
  `astream()`   Asynchronous response chunks

## 2. LangGraph streaming

LangGraph provides its own streaming mechanism.

Three useful streaming modes:

  Mode         What it streams
  ------------ ----------------------------------
  `updates`    State updates produced by nodes
  `values`     Full state after each graph step
  `messages`   LLM message/token chunks

### A. Updates mode

``` python
for chunk in graph.stream(
    initial_state,
    stream_mode="updates",
):
    print(chunk)
```

Suppose your graph has:

``` text
START → analyze → respond → END
```

You can receive updates as individual nodes finish.

Illustrative output:

``` python
{"analyze": {"is_delayed": True}}
{"respond": {"response": "Your order is delayed."}}
```

Notice: `updates` does not necessarily mean token-by-token LLM
streaming. It streams node updates.

### B. Values mode

``` python
for chunk in graph.stream(
    initial_state,
    stream_mode="values",
):
    print(chunk)
```

This gives you the full state after each step.

For example:

``` python
{
    "order_status": "delayed",
    "is_delayed": True,
    "ticket_created": False,
    "response": "",
}
```

The next state update may include the generated response.

### C. Messages mode

For token-level LLM streaming:

``` python
for message_chunk, metadata in graph.stream(
    initial_state,
    stream_mode="messages",
):
    print(message_chunk.content, end="", flush=True)
```

This is useful when you want to show LLM-generated text as it arrives.

**Important:** `messages` mode may emit chunks from multiple LLM calls
in a graph. Inspect metadata, such as the node name, to distinguish
which node produced them.

## 3. Async execution --- why do we need it?

Imagine your agent needs to:

1.  Fetch order details from PostgreSQL.
2.  Call an external shipping API.
3.  Fetch customer details from another service.

These operations spend time waiting for I/O.

### Synchronous execution

``` python
order = get_order()
shipping = get_shipping()
customer = get_customer()
```

Each operation waits for the previous one to finish.

### Asynchronous execution

``` python
order, shipping, customer = await asyncio.gather(
    get_order(),
    get_shipping(),
    get_customer(),
)
```

Independent asynchronous I/O operations can overlap.

Illustrative timeline:

``` text
SYNCHRONOUS

get_order      [------]
get_shipping           [------]
get_customer                  [------]


ASYNCHRONOUS

get_order      [------]
get_shipping   [------]
get_customer   [------]
```

This is concurrency, not necessarily CPU parallelism.

### Basic Python async example

``` python
import asyncio

async def get_order():
    print("Fetching order...")
    await asyncio.sleep(2)
    return "Order fetched"


async def get_shipping():
    print("Fetching shipping...")
    await asyncio.sleep(3)
    return "Shipping fetched"


async def main():
    results = await asyncio.gather(
        get_order(),
        get_shipping(),
    )

    print(results)


asyncio.run(main())
```

Expected output:

``` text
Fetching order...
Fetching shipping...
['Order fetched', 'Shipping fetched']
```

Approximate execution time: 3 seconds, not 5 seconds, because both
functions spend their waiting time concurrently.

**Important:** `asyncio.gather()` is useful for independent asynchronous
operations. It does not automatically make CPU-heavy Python functions
faster. By default, it returns results in input order, not completion
order.

## 4. Async execution in LangChain

LangChain provides asynchronous methods.

``` python
import asyncio
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="YOUR_AVAILABLE_MODEL"
)

async def main():
    response = await model.ainvoke(
        "Explain LangGraph"
    )

    print(response.content)


asyncio.run(main())
```

For streaming:

``` python
async def main():
    async for chunk in model.astream(
        "Explain AI agents"
    ):
        print(chunk.content, end="", flush=True)


asyncio.run(main())
```

Use asynchronous methods when your application is already using an async
runtime, such as FastAPI.

## 5. Parallel graph execution in LangGraph

Now the most important part.

Suppose you are building a research agent. It needs to investigate:

-   Technical feasibility
-   Performance implications
-   Security risks

These three tasks do not depend on each other.

### Sequential execution

``` text
START
  |
  v
Technical Research
  |
  v
Performance Research
  |
  v
Security Research
  |
  v
Summary
  |
  v
END
```

### Parallel execution

``` text
             START
               |
         +-----+-----+
         |     |     |
         v     v     v
      Technical Performance Security
      Research  Research   Research
         |     |     |
         +-----+-----+
               |
               v
             Summary
               |
               v
              END
```

LangGraph can execute nodes in the same superstep concurrently when the
graph structure permits it.

### Complete implementation

``` python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. Define state
class ResearchState(TypedDict):
    topic: str
    technical: str
    performance: str
    security: str
    summary: str


# 2. Define nodes
def technical_research(state: ResearchState):
    print("Technical research started")

    return {
        "technical": (
            f"Technical analysis of {state['topic']}"
        )
    }


def performance_research(state: ResearchState):
    print("Performance research started")

    return {
        "performance": (
            f"Performance analysis of {state['topic']}"
        )
    }


def security_research(state: ResearchState):
    print("Security research started")

    return {
        "security": (
            f"Security analysis of {state['topic']}"
        )
    }


def summarize(state: ResearchState):
    print("Summary started")

    summary = "\n".join([
        state["technical"],
        state["performance"],
        state["security"],
    ])

    return {
        "summary": summary
    }


# 3. Build graph
builder = StateGraph(ResearchState)

builder.add_node("technical", technical_research)
builder.add_node("performance", performance_research)
builder.add_node("security", security_research)
builder.add_node("summary", summarize)

# Fan-out: all three branches can run in the same superstep.
builder.add_edge(START, "technical")
builder.add_edge(START, "performance")
builder.add_edge(START, "security")

# Join: summary runs after all three upstream nodes finish.
builder.add_edge(
    ["technical", "performance", "security"],
    "summary",
)

builder.add_edge("summary", END)


# 4. Compile and execute
graph = builder.compile()

result = graph.invoke({
    "topic": "AI coding agents",
    "technical": "",
    "performance": "",
    "security": "",
    "summary": "",
})

print("\nFINAL SUMMARY:")
print(result["summary"])
```

### Understand the critical part

Fan-out:

``` python
builder.add_edge(START, "technical")
builder.add_edge(START, "performance")
builder.add_edge(START, "security")
```

All three nodes are reachable from `START` and can execute in the same
superstep.

Join:

``` python
builder.add_edge(
    ["technical", "performance", "security"],
    "summary",
)
```

This creates a join: `summary` runs after all three upstream nodes have
completed.

**Important rule:** Parallel nodes should generally update separate
state keys, as in this example. If multiple parallel nodes write to the
same state key without a suitable reducer, LangGraph can raise an
`InvalidUpdateError`.

## 6. Concurrency vs Parallelism

Interviewers frequently ask about this distinction.

  -----------------------------------------------------------------------
  Concurrency                         Parallelism
  ----------------------------------- -----------------------------------
  Multiple tasks make progress during Multiple tasks execute at the same
  overlapping periods                 instant

  Can happen on one CPU thread        Requires simultaneous execution
                                      resources

  Great for I/O-bound workloads       Useful for CPU-bound workloads

  Example: async API calls            Example: work distributed across
                                      CPU cores
  -----------------------------------------------------------------------

For AI applications, much of the waiting happens because of:

-   LLM API calls
-   Database queries
-   HTTP requests
-   External tools

Therefore, async concurrency is extremely useful.

But do not assume every graph with parallel branches will run faster.
API rate limits, database connection pools, and external service latency
can become bottlenecks.

## 7. Production considerations

Parallel execution has trade-offs.

  Problem                           Engineering solution
  --------------------------------- ---------------------------------------
  Too many API calls                Concurrency limits
  External API rate limits          Rate limiting and backoff
  One branch fails                  Explicit failure handling or fallback
  Slowest branch delays summary     Timeouts and partial-result policy
  Multiple nodes update same key    Reducers or separate state keys
  Duplicate side effects on retry   Idempotency

For example, use a semaphore to limit concurrent API calls:

``` python
import asyncio

semaphore = asyncio.Semaphore(5)

async def limited_api_call(task):
    async with semaphore:
        return await task()
```

This limits the number of concurrent operations to five, assuming
`task()` returns an awaitable.

For production systems, also use request timeouts and handle exceptions
deliberately.

## 8. How these concepts fit together

Imagine a real AI coding agent similar to Claude Code.

``` text
User Request
     |
     v
  Planner Agent
     |
     v
Conditional Routing
     |
     +------> Search Files
     |
     +------> Inspect Code
     |
     +------> Run Tests
                  |
                  v
              Merge Results
                  |
                  v
              Reasoning Agent
                  |
                  v
              Stream Response
                  |
                  v
                 END
```

The architecture combines:

-   Conditional routing to select actions.
-   Parallel execution for independent operations.
-   Async I/O for efficient waiting.
-   Streaming for responsive UX.
-   Checkpointing to recover workflow state.

This is the foundation of a production-grade agent workflow.

------------------------------------------------------------------------

## 9. Key concepts recap

  -----------------------------------------------------------------------
  Concept                             Key takeaway
  ----------------------------------- -----------------------------------
  Model streaming                     Delivers generated output
                                      progressively

  `updates` mode                      Streams node state updates

  `values` mode                       Streams full graph state after
                                      steps

  `messages` mode                     Streams LLM message chunks

  `ainvoke()`                         Asynchronous complete execution

  `astream()`                         Asynchronous output streaming

  Async concurrency                   Overlaps independent I/O waits

  Parallel graph execution            Runs independent nodes in the same
                                      superstep

  Fan-out                             Starts multiple branches

  Join                                Waits for upstream branches before
                                      continuing

  Semaphore                           Limits concurrent operations
  -----------------------------------------------------------------------

## 10. Interview questions

1.  What is the difference between model streaming and LangGraph
    `updates` streaming?
2.  What does `stream_mode="values"` return?
3.  When would you use `stream_mode="messages"`?
4.  What is the difference between `invoke()` and `ainvoke()`?
5.  Why is async execution useful for AI backends?
6.  What is the difference between concurrency and parallelism?
7.  How does LangGraph execute parallel nodes?
8.  What is fan-out and what is a join?
9.  Why should parallel nodes avoid writing to the same state key
    without a reducer?
10. How can you limit concurrent API calls?
11. Why might parallel execution fail to improve latency?
12. How do streaming, parallelism, and checkpointing complement each
    other?

------------------------------------------------------------------------

## Engineering takeaway

A responsive production agent needs more than a correct final answer:

-   **Streaming** improves perceived responsiveness.
-   **Async concurrency** reduces time spent waiting on independent I/O.
-   **Parallel graph execution** allows independent workflow branches to
    progress together.
-   **Reducers and separate state keys** make concurrent state updates
    predictable.
-   **Concurrency limits, timeouts, and idempotency** protect production
    systems.

Always measure actual latency and failure behavior. Parallelism is an
architectural tool, not a guarantee of faster execution.
