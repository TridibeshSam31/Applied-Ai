# Agent Frameworks --- Topic 7/10

## State, Nodes, Edges and Reducers --- Deep Dive

This topic deepens the LangGraph fundamentals from Topic 6. The focus is
how multiple nodes update shared state, and how LangGraph handles
multiple updates to the same state field.

We will use the Customer Support Agent and parallel research workflows
as examples.

------------------------------------------------------------------------

## 1. State schema --- defining workflow data

The state schema defines the shared data contract inside a graph.

``` python
from typing_extensions import TypedDict

class SupportState(TypedDict):
    customer_message: str
    order_id: str
    order_status: str
    ticket_id: str
    response: str
```

`TypedDict` tells Python and type checkers which keys and value types
are expected.

**Important:** `TypedDict` is not runtime validation. If you need to
prevent invalid data at runtime, use Pydantic or explicit validation.

### Initial state

``` python
initial_state = {
    "customer_message": "My order is delayed",
    "order_id": "ORD-101",
    "order_status": "",
    "ticket_id": "",
    "response": "",
}
```

When the graph executes, this state is passed through different nodes.

## 2. Partial state updates

Suppose your graph has three nodes:

-   Order Node
-   Ticket Node
-   Response Node

The Order Node only needs to update the order status:

``` python
def order_node(state):
    return {
        "order_status": "delayed"
    }
```

The Ticket Node only needs to update the ticket ID:

``` python
def ticket_node(state):
    return {
        "ticket_id": "TICKET-501"
    }
```

The Response Node updates the final response:

``` python
def response_node(state):
    return {
        "response": (
            f"Your order is {state['order_status']}. "
            f"Ticket: {state['ticket_id']}"
        )
    }
```

None of these nodes returns the complete state. LangGraph applies the
returned updates to the existing state.

**Initial state:**

``` python
{
    "order_status": "",
    "ticket_id": "",
    "response": "",
}
```

**Order Node update:**

``` python
{"order_status": "delayed"}
```

**Ticket Node update:**

``` python
{"ticket_id": "TICKET-501"}
```

**State after both updates:**

``` python
{
    "order_status": "delayed",
    "ticket_id": "TICKET-501",
    "response": "",
}
```

Partial updates make nodes modular: each node only needs to return the
fields it owns or intends to update.

## 3. The real problem --- multiple nodes updating the same state

Imagine two independent research nodes execute in parallel:

``` python
def venue_agent(state):
    return {
        "recommendations": ["Convention Hall"]
    }


def hotel_agent(state):
    return {
        "recommendations": ["City Hotel"]
    }
```

Both nodes update the same `recommendations` field.

What should the final state contain?

-   `["Convention Hall"]`
-   `["City Hotel"]`
-   `["Convention Hall", "City Hotel"]`

LangGraph cannot infer which business meaning you intend. Without a
suitable reducer, multiple concurrent updates to the same state key can
cause an `InvalidUpdateError`.

**This is why reducers exist.**

## 4. What is a Reducer?

A reducer defines how LangGraph combines updates to a particular state
field.

Conceptually:

\[ `\text{New State}`{=tex} =
`\text{Reducer}`{=tex}(`\text{Existing State}`{=tex},
`\text{New Update}`{=tex}) \]

For example, Python's `operator.add` can perform list concatenation:

``` python
print(
    ["Convention Hall"] +
    ["City Hotel"]
)
```

Output:

``` python
["Convention Hall", "City Hotel"]
```

Now connect this behavior to LangGraph.

### Using `Annotated` and `operator.add`

``` python
import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class EventState(TypedDict):
    recommendations: Annotated[
        list[str],
        operator.add
    ]


def venue_agent(state: EventState):
    return {
        "recommendations": ["Convention Hall"]
    }


def hotel_agent(state: EventState):
    return {
        "recommendations": ["City Hotel"]
    }


builder = StateGraph(EventState)

builder.add_node("venue", venue_agent)
builder.add_node("hotel", hotel_agent)

builder.add_edge(START, "venue")
builder.add_edge(START, "hotel")

builder.add_edge("venue", END)
builder.add_edge("hotel", END)

graph = builder.compile()

result = graph.invoke({
    "recommendations": []
})

print(result)
```

Expected result:

``` python
{
    "recommendations": [
        "Convention Hall",
        "City Hotel",
    ]
}
```

The reducer combines the parallel updates instead of treating them as
conflicting replacements.

**Important:** This reducer is suitable for append-only results. It does
not automatically solve duplicate entries, conflicting decisions, or
business-level consistency.

## 5. Understanding `Annotated`

Let's break down this declaration:

``` python
recommendations: Annotated[
    list[str],
    operator.add
]
```

  Part                Meaning
  ------------------- ---------------------------
  `recommendations`   State field name
  `list[str]`         Expected data type
  `operator.add`      Reducer function metadata

`Annotated` allows you to attach additional metadata to a type.
LangGraph uses that metadata to determine how updates to the field
should be merged.

Without the reducer:

``` python
recommendations: list[str]
```

The default behavior is to replace the existing value when a node
updates the field.

With the reducer:

``` python
recommendations: Annotated[
    list[str],
    operator.add
]
```

The new list is combined with the existing list.

## 6. Custom reducers

You are not restricted to `operator.add`. You can write your own
reducer.

Suppose you want to combine results while avoiding duplicates:

``` python
def merge_unique(old: list, new: list) -> list:
    return list(dict.fromkeys(old + new))
```

Use it in the state schema:

``` python
from typing import Annotated
from typing_extensions import TypedDict


class EventState(TypedDict):
    recommendations: Annotated[
        list[str],
        merge_unique
    ]
```

Example:

``` python
old = ["Convention Hall", "City Hotel"]
new = ["City Hotel", "Open Ground"]

print(merge_unique(old, new))
```

Output:

``` python
[
    "Convention Hall",
    "City Hotel",
    "Open Ground",
]
```

This preserves the first occurrence of each item.

### Where this is useful

-   Search results from multiple agents
-   Research findings
-   Logs and event collections
-   Tool execution traces

**Caution:** A reducer should be deterministic and designed for the data
it merges. Do not use list concatenation to resolve competing decisions
such as `approved` versus `rejected`.

## 7. `add_messages` --- managing conversation history

This is one of the most useful LangGraph reducers for LLM applications.

Suppose your agent maintains a conversation:

``` text
User: Where is my order?
AI: Your order is delayed.
User: Can you create a ticket?
```

You need to maintain the messages as the workflow executes.

LangGraph provides `add_messages`:

``` python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage


class AgentState(TypedDict):
    messages: Annotated[
        list[AnyMessage],
        add_messages
    ]
```

### How it works

Initial state:

``` python
{
    "messages": [
        HumanMessage(
            content="Where is my order?"
        )
    ]
}
```

A node returns:

``` python
{
    "messages": [
        AIMessage(
            content="Your order is delayed."
        )
    ]
}
```

After the reducer, the conversation contains both messages:

``` text
HumanMessage: Where is my order?
AIMessage: Your order is delayed.
```

### `operator.add` vs `add_messages`

  Feature                              `operator.add`     `add_messages`
  ------------------------------------ ------------------ ---------------------------------
  Purpose                              Generic addition   Conversation message management
  List concatenation                   Yes                Yes, with additional semantics
  Message ID handling                  No                 Yes
  Existing message replacement by ID   No                 Yes

`add_messages` is not merely list concatenation. It handles message IDs,
including updating an existing message when a matching ID is supplied.

For tool-calling agents, this is particularly useful because assistant
tool-call messages and corresponding tool results must remain associated
correctly.

## 8. Parallel execution and reducers

Connect this with the Multi-Agent Systems module.

Imagine three agents working simultaneously:

-   Research Agent
-   Venue Agent
-   Catering Agent

All three return findings into one shared list.

``` text
Shared State
recommendations = []

       /       |       \
      v        v        v
 Research    Venue   Catering
  Agent      Agent    Agent
      \        |        /
       \       |       /
             Reducer
                |
                v
       Combined State
       All findings collected
```

One subtle point: parallel nodes in LangGraph generally execute within
the same superstep. Their updates are collected and applied according to
the channel's reducer.

Do not rely on the order of parallel execution to determine business
priority. If order matters, include explicit priorities or identifiers
in the results and sort them in a later node.

## 9. Reducers don't solve every state conflict

Suppose two agents return:

``` python
# Agent A
{"decision": "approved"}

# Agent B
{"decision": "rejected"}
```

Would `operator.add` solve this?

No. These are competing decisions, not values that should be
concatenated.

A better design:

``` python
class DecisionState(TypedDict):
    agent_decisions: Annotated[
        list[str],
        operator.add
    ]
    final_decision: str
```

Each agent writes to `agent_decisions`.

A separate supervisor node evaluates the collected results and updates
`final_decision`.

This is a safer architecture.

**Engineering principle:** Collect evidence first. Resolve conflicting
decisions explicitly afterward.

## 10. Complete practical implementation

Build a mini research workflow using parallel nodes and a custom
reducer.

Create `main.py`:

``` python
import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. Define shared state
class ResearchState(TypedDict):
    topic: str
    findings: Annotated[
        list[str],
        operator.add
    ]
    summary: str


# 2. Define independent agents
def technical_research(state: ResearchState):
    print("[Technical Agent] Researching...")

    return {
        "findings": [
            "PostgreSQL supports B-tree indexes.",
            "Indexes can speed up read queries.",
        ]
    }


def performance_research(state: ResearchState):
    print("[Performance Agent] Researching...")

    return {
        "findings": [
            "Indexes add storage overhead.",
            "Indexes can slow down write operations.",
        ]
    }


# 3. Define summary node
def summarize(state: ResearchState):
    print("[Summary Agent] Combining findings...")

    summary = "\n".join(
        f"- {finding}"
        for finding in state["findings"]
    )

    return {
        "summary": summary
    }


# 4. Build graph
builder = StateGraph(ResearchState)

builder.add_node("technical", technical_research)
builder.add_node("performance", performance_research)
builder.add_node("summary", summarize)

builder.add_edge(START, "technical")
builder.add_edge(START, "performance")

# Both parallel branches must finish before summary runs.
builder.add_edge("technical", "summary")
builder.add_edge("performance", "summary")

builder.add_edge("summary", END)


# 5. Compile and execute
graph = builder.compile()

result = graph.invoke({
    "topic": "PostgreSQL indexing",
    "findings": [],
    "summary": "",
})

print("\nFINAL SUMMARY:")
print(result["summary"])
```

Expected output:

``` text
[Technical Agent] Researching...
[Performance Agent] Researching...
[Summary Agent] Combining findings...

FINAL SUMMARY:
- PostgreSQL supports B-tree indexes.
- Indexes can speed up read queries.
- Indexes add storage overhead.
- Indexes can slow down write operations.
```

**Implementation note:** The example uses `operator.add`, so make sure
to include `import operator` at the top of the file. The order of the
first two agents' execution is not guaranteed. The important part is
that the summary node runs after both parallel branches have completed.

## 11. What you've learned

  -----------------------------------------------------------------------
  Concept                             Key takeaway
  ----------------------------------- -----------------------------------
  State schema                        Defines workflow data

  Partial updates                     Nodes return only changed fields

  Reducer                             Defines how updates are combined

  `Annotated`                         Attaches reducer metadata

  `operator.add`                      Combines list updates

  Custom reducer                      Implements application-specific
                                      merging

  `add_messages`                      Manages conversation message
                                      updates

  Parallel state updates              Require appropriate reducers when
                                      multiple nodes update the same
                                      field
  -----------------------------------------------------------------------

### Interview questions

1.  What is a reducer in LangGraph?
2.  What is the difference between default state updates and
    reducer-based updates?
3.  What does `Annotated` do?
4.  Why would you use `add_messages` instead of `operator.add`?
5.  What happens when two parallel nodes update the same field without a
    reducer?
6.  Why shouldn't you use `operator.add` to resolve conflicting business
    decisions?

------------------------------------------------------------------------

## Engineering takeaway

Reducers define how updates to a state field are merged. They are not a
substitute for business-level conflict resolution.

-   Use partial updates to keep nodes focused.
-   Use reducers for well-defined merge behavior.
-   Use `add_messages` for conversation message state.
-   Use explicit supervisor or validation logic for competing decisions.
-   Do not assume parallel execution order.

Before building more complex agents, understand exactly which node owns
each state field and how concurrent updates should be combined.
