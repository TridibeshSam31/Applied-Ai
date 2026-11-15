# Module 4: Agent Frameworks --- Topic 8/10

## Conditional Routing, Loops and Checkpointing in LangGraph

So far, we have covered nodes, edges, state, and reducers in LangGraph.
Our graphs have mostly been predictable: one node executes after
another.

Real agents are not always linear.

**An agent may need to decide what happens next, when to call a tool,
when to reason again, and when to stop.** Conditional routing, loops,
and checkpointing help build these workflows.

------------------------------------------------------------------------

## 1. What is Conditional Routing?

A normal edge always sends execution to a fixed destination:

``` python
builder.add_edge("analyze", "respond")
```

This means that `respond` always executes after `analyze`.

A conditional edge lets a routing function choose the next node:

``` python
builder.add_conditional_edges(
    "analyze",
    route_request,
)
```

Example:

-   If the order is delayed → create a ticket.
-   If the order is not delayed → send a normal response.

### Basic syntax

``` python
def route_request(state):
    if state["is_delayed"]:
        return "create_ticket"

    return "respond"


builder.add_conditional_edges(
    "analyze",
    route_request,
    {
        "create_ticket": "create_ticket",
        "respond": "respond",
    },
)
```

The mapping connects the routing function's return value to a graph
node.

  Function return     Next node
  ------------------- -----------------
  `"create_ticket"`   `create_ticket`
  `"respond"`         `respond`

The routing function generally reads state and returns a destination. It
does not perform the business operation itself.

## 2. Build a conditional workflow

Let's create a practical Customer Support workflow.

``` python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. Define state
class SupportState(TypedDict):
    order_status: str
    is_delayed: bool
    ticket_created: bool
    response: str


# 2. Define nodes
def analyze_order(state: SupportState):
    print("[Analyze] Checking order status...")

    is_delayed = state["order_status"] == "delayed"

    return {
        "is_delayed": is_delayed
    }


def create_ticket(state: SupportState):
    print("[Ticket] Creating support ticket...")

    # Demo only. A real implementation should call
    # an authenticated backend service.
    return {
        "ticket_created": True
    }


def respond(state: SupportState):
    print("[Respond] Preparing customer response...")

    if state["ticket_created"]:
        message = "Your order is delayed. A support ticket has been created."
    elif state["is_delayed"]:
        message = "Your order is delayed."
    else:
        message = f"Your order is currently {state['order_status']}."

    return {
        "response": message
    }


# 3. Define routing function
def route_request(state: SupportState):
    if state["is_delayed"]:
        return "create_ticket"

    return "respond"


# 4. Build graph
builder = StateGraph(SupportState)

builder.add_node("analyze", analyze_order)
builder.add_node("create_ticket", create_ticket)
builder.add_node("respond", respond)

builder.add_edge(START, "analyze")

builder.add_conditional_edges(
    "analyze",
    route_request,
    {
        "create_ticket": "create_ticket",
        "respond": "respond",
    },
)

builder.add_edge("create_ticket", "respond")
builder.add_edge("respond", END)


# 5. Compile
graph = builder.compile()


# 6. Execute
result = graph.invoke({
    "order_status": "delayed",
    "is_delayed": False,
    "ticket_created": False,
    "response": "",
})

print(result["response"])
```

### Expected flow for a delayed order

``` text
START
  |
  v
ANALYZE
  |
  v
Is order delayed?
  |
  +---- YES ----> CREATE TICKET
  |                    |
  |                    v
  |                 RESPOND
  |
  +---- NO ------> RESPOND
                       |
                       v
                      END
```

Try changing:

``` python
"order_status": "delayed"
```

to:

``` python
"order_status": "shipped"
```

The ticket will not be created.

**Engineering lesson:** Keeping routing logic separate from node
business logic makes the graph easier to test and maintain.

## 3. Agent → Tool → Agent loop

Now let's understand an actual agent architecture.

An LLM agent receives a user's question and decides whether to:

1.  Answer directly, or
2.  Call a tool.

If it requests a tool call, the tool executes. Its result is returned to
the agent. The agent then decides whether another tool is needed or
whether it can produce the final answer.

``` text
        START
          |
          v
        AGENT (LLM)
          |
          v
      tools_condition
          |
       +--+--+
       |     |
    Tool call No tool call
       |     |
       v     v
    TOOL NODE END
       |
       v
      AGENT
       |
       v
   Decide again
```

LangGraph provides two useful utilities:

-   `ToolNode`: executes tool calls.
-   `tools_condition`: checks whether the latest AI response contains
    tool calls.

### Implementation

Install:

``` bash
pip install -U langgraph langchain langchain-openai
```

Create the tools and graph:

``` python
import os

from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


# 1. Define state
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# 2. Define tools
@tool
def get_order_status(order_id: str) -> str:
    """Get the current status of an order."""
    # Demo implementation
    return f"Order {order_id} is delayed."


@tool
def create_support_ticket(order_id: str) -> str:
    """Create a support ticket for an order."""
    # Demo implementation
    return f"Ticket created for order {order_id}."


tools = [
    get_order_status,
    create_support_ticket,
]


# 3. Initialize model and bind tools
model = ChatOpenAI(
    model=os.environ["OPENAI_MODEL"],
    temperature=0,
)

model_with_tools = model.bind_tools(tools)


# 4. Define agent node
def agent(state: AgentState):
    response = model_with_tools.invoke(state["messages"])

    return {
        "messages": [response]
    }


# 5. Build graph
builder = StateGraph(AgentState)

builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")

builder.add_conditional_edges(
    "agent",
    tools_condition,
)

builder.add_edge("tools", "agent")


# 6. Compile
graph = builder.compile()


# 7. Execute
result = graph.invoke({
    "messages": [
        HumanMessage(
            content="Check order ORD-123 and create a support ticket if it is delayed."
        )
    ]
})

print(result["messages"][-1].content)
```

Set `OPENAI_MODEL` to a model available to your API account. Also
configure the API key in your environment.

### Understanding `tools_condition`

``` python
builder.add_conditional_edges(
    "agent",
    tools_condition,
)
```

`tools_condition` checks the latest AI message:

-   Tool calls present → route to the `"tools"` node.
-   No tool calls → route to `END`.

Then:

``` python
builder.add_edge("tools", "agent")
```

After tool execution, control returns to the agent.

This is an actual agent loop.

**Security warning:** `ToolNode` executes tool calls, but authorization,
customer ownership checks, payment validation, and other security
controls must live in your backend. Never blindly trust the LLM.

## 4. Infinite loops and recursion limits

Loops are powerful, but they can be dangerous.

Imagine:

``` text
Agent → Tool → Agent → Tool → Agent → Tool → ...
```

If the agent never produces a final answer, the graph may continue
executing.

LangGraph allows you to configure a recursion limit:

``` python
from langgraph.errors import GraphRecursionError

try:
    result = graph.invoke(
        initial_state,
        config={
            "recursion_limit": 10
        },
    )
except GraphRecursionError:
    print("Graph exceeded its recursion limit.")
```

This limits graph execution supersteps. It does **not** guarantee
exactly ten LLM calls.

### Production safeguards

-   Define a maximum tool-call count.
-   Set tool execution timeouts.
-   Limit retry counts.
-   Handle invalid tool arguments.
-   Handle `GraphRecursionError`.
-   Make loop termination conditions deterministic.

**Never rely only on the LLM to stop itself.**

## 5. Checkpointing --- saving agent progress

Suppose a user interacts with an agent:

``` text
User: Where is my order?

Agent: Let me check.

Agent → get_order_status()

Tool: Order is delayed.

Agent: Your order is delayed.
```

Now the user asks:

``` text
User: Create a support ticket.
```

If you have not saved the previous conversation state, you may need to
provide the previous context again.

Checkpointing addresses this problem.

**Checkpointing means persisting graph state during workflow
execution.**

LangGraph checkpointers save state snapshots associated with a thread.

### In-memory checkpointing

``` python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

graph = builder.compile(
    checkpointer=checkpointer
)
```

Now provide a `thread_id`:

``` python
config = {
    "configurable": {
        "thread_id": "customer-101"
    }
}

result = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="Check my order ORD123"
            )
        ]
    },
    config=config,
)
```

Send the next message in the same thread:

``` python
result = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="Create a support ticket."
            )
        ]
    },
    config=config,
)
```

The saved state for the same thread is loaded and combined with the new
input as the graph executes.

`InMemorySaver` is useful for development, but its data can be lost when
the process or server restarts.

## 6. `thread_id`, `checkpoint_id`, and persistence

Do not confuse these concepts.

  Term              Meaning
  ----------------- ------------------------------------------------
  `thread_id`       Identity of a conversation or workflow
  `checkpoint_id`   Identity of a particular saved state snapshot
  Checkpointer      Mechanism that saves and loads state snapshots

Example:

``` text
thread_id = customer-101

Checkpoint 1 → User asks order status
Checkpoint 2 → Agent calls order tool
Checkpoint 3 → Tool returns delayed
Checkpoint 4 → Agent responds
```

A thread can have multiple checkpoints.

You can inspect the latest state:

``` python
state_snapshot = graph.get_state(config)

print(state_snapshot.values)
```

### Uses of checkpointing

-   Resume a conversation.
-   Continue an interrupted workflow.
-   Resume execution after human approval.
-   Debug long-running workflows.
-   Inspect prior workflow state.

### Persistence vs long-term memory

This is an important interview distinction.

  -----------------------------------------------------------------------
  Checkpointing                       Long-term memory
  ----------------------------------- -----------------------------------
  Saves workflow state                Stores useful user information

  Thread-specific snapshots           User-, profile-, or entity-specific
                                      knowledge

  Helps resume execution              Helps personalize future
                                      conversations

  Structured workflow state           Often searchable records or
                                      embeddings
  -----------------------------------------------------------------------

Examples:

-   **Checkpoint:** The agent has fetched the order status but has not
    yet responded.
-   **Long-term memory:** The user prefers email notifications.

These solve different problems.

## 7. Production checkpointing

`InMemorySaver` does not provide durable production persistence.

For production, use a persistent database-backed checkpointer. The
LangGraph ecosystem provides a PostgreSQL checkpointer.

Install:

``` bash
pip install -U langgraph-checkpoint-postgres "psycopg[binary,pool]"
```

Basic setup:

``` python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = os.environ["DATABASE_URL"]

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()

    graph = builder.compile(
        checkpointer=checkpointer
    )

    config = {
        "configurable": {
            "thread_id": "customer-101"
        }
    }

    result = graph.invoke(
        initial_state,
        config=config,
    )
```

This is a simplified setup.

In a real application:

-   Read database credentials from environment variables or a secret
    manager.
-   Configure connection pooling.
-   Manage checkpointer lifecycle through application startup and
    shutdown.
-   Bind thread access to an authenticated user.
-   Avoid storing unnecessary sensitive data in checkpoints.

If a user guesses another user's `thread_id`, their data must not become
accessible. The backend must enforce authorization.

## 8. Human-in-the-loop --- a powerful use of checkpointing

Suppose an agent wants to process a refund.

A refund is a financial operation, so the agent should not execute it
without the required approval.

### Workflow

``` text
User requests refund
        |
        v
Agent evaluates request
        |
        v
Human approval required
        |
        v
Workflow pauses
        |
        v
Checkpoint saved
        |
        v
Human approves
        |
        v
Workflow resumes
        |
        v
Refund tool executes
```

LangGraph provides mechanisms such as `interrupt()` and
`Command(resume=...)` to build human-approval workflows. A checkpointer
must be configured for this pattern.

The detailed implementation can be covered in the production agent
workflows module.

------------------------------------------------------------------------

## 9. Key concepts recap

  -----------------------------------------------------------------------
  Concept                             Key takeaway
  ----------------------------------- -----------------------------------
  Conditional edge                    Chooses the next node based on
                                      state or routing logic

  Routing function                    Returns a destination; does not
                                      perform the business operation

  `ToolNode`                          Executes tool calls

  `tools_condition`                   Routes based on whether the latest
                                      AI message requests tools

  Agent loop                          Sends tool results back to the
                                      agent for another decision

  Recursion limit                     Caps graph supersteps

  Checkpointing                       Persists graph state snapshots

  `thread_id`                         Identifies a workflow or
                                      conversation thread

  `checkpoint_id`                     Identifies a particular saved
                                      snapshot

  `InMemorySaver`                     Development-oriented in-memory
                                      checkpointer

  PostgreSQL checkpointer             Durable database-backed checkpoint
                                      storage

  `interrupt()`                       Supports pausing for human input or
                                      approval
  -----------------------------------------------------------------------

## 10. Interview questions

1.  What is the difference between a normal edge and a conditional edge?
2.  What does a routing function return?
3.  How does the Agent → Tool → Agent loop work?
4.  What are `ToolNode` and `tools_condition`?
5.  What is the purpose of a recursion limit?
6.  Does `recursion_limit=10` mean exactly ten LLM calls?
7.  What is checkpointing in LangGraph?
8.  What is the difference between `thread_id` and `checkpoint_id`?
9.  How is checkpointing different from long-term memory?
10. Why is `InMemorySaver` unsuitable for durable production
    persistence?
11. Why must a backend authorize access to a thread?
12. How does checkpointing support human-in-the-loop workflows?

------------------------------------------------------------------------

## Engineering takeaway

A production agent needs more than an LLM and tools:

-   **Conditional routing** controls which path executes.
-   **Loops** let an agent use tool results and reason again.
-   **Execution limits** prevent runaway workflows.
-   **Checkpointing** preserves workflow progress.
-   **Authorization** protects thread and tool access.
-   **Human approval** gates sensitive operations.

The LLM can propose the next action, but your graph and backend must
control what is allowed to execute.
