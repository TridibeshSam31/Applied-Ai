# Agent Frameworks --- Topic 6/10

## LangGraph Fundamentals

LangGraph is one of the most important parts of the Agent Frameworks
module.

So far, we have used LangChain to:

-   Connect an LLM.
-   Create prompts.
-   Generate structured output.
-   Define and execute tools.
-   Compose Runnables and pipelines.

However, consider a Customer Support Agent that must:

1.  Analyse the user's message.
2.  Retrieve order details.
3.  Check whether the order is delayed.
4.  Create a support ticket if the order is delayed.
5.  Otherwise, tell the customer the order status.
6.  Retry if a tool fails.

This is not simply a linear chain. It involves conditions, loops, shared
state, and multiple execution paths.

**LangGraph is designed to orchestrate stateful workflows of this
kind.**

------------------------------------------------------------------------

## 1. What is LangGraph?

LangGraph is a graph-based orchestration framework for building
stateful, controllable AI workflows and agents.

Official documentation: [LangGraph
overview](https://docs.langchain.com/oss/python/langgraph/overview)

A normal chain might look like this:

``` text
Prompt → LLM → Parser → Output
```

A LangGraph workflow can include branches and cycles:

``` text
          START
            |
            v
        Agent Node
            |
            v
       Tool Required?
          /    \
        Yes     No
         |       |
         v       v
      Tool Node  END
         |
         v
     Agent Node
```

The key differences:

-   A normal chain generally executes a defined sequence.
-   LangGraph allows branching, looping, state updates, and resumable
    execution.

LangGraph is not a replacement for the LLM. It is an orchestration layer
around model calls and application logic.

## 2. The four core concepts

LangGraph revolves around four important building blocks.

### 1. State

Stores the data shared across workflow nodes.

Examples: customer message, order details, and ticket status.

### 2. Nodes

Functions that perform individual operations.

Examples: analyse request, retrieve order, and validate eligibility.

### 3. Edges

Define which node executes next.

Example: after order retrieval, route to validation.

### 4. Graph

Connects state, nodes, and edges into an executable workflow.

We will understand each by writing code.

## 3. State --- the shared data of a graph

State is the data structure that moves through your workflow.

For the Customer Support Agent:

``` python
from typing_extensions import TypedDict

class SupportState(TypedDict):
    customer_message: str
    order_id: str
    order_status: str
    response: str
```

Think of it as a dictionary with a defined structure.

Initial state:

``` python
state = {
    "customer_message": "Where is my order?",
    "order_id": "ORD-101",
    "order_status": "",
    "response": "",
}
```

When a node executes, it receives the current state and returns updates.

For example:

``` python
def retrieve_order(state: SupportState):
    order_status = "shipped"

    return {
        "order_status": order_status
    }
```

Notice that the node returns only the field it wants to update:

``` python
return {"order_status": "shipped"}
```

LangGraph applies that update to the graph state. A node does not need
to return every field each time.

**Before node execution:**

``` python
{
    "customer_message": "Where is my order?",
    "order_id": "ORD-101",
    "order_status": "",
    "response": "",
}
```

**Node returns:**

``` python
{"order_status": "shipped"}
```

**Updated state:**

``` python
{
    "customer_message": "Where is my order?",
    "order_id": "ORD-101",
    "order_status": "shipped",
    "response": "",
}
```

This is the central idea of `StateGraph`: nodes communicate by reading
shared state and returning partial state updates.

## 4. Nodes --- functions that do the work

A node is simply a Python function (or compatible Runnable) registered
in the graph.

Let's define three nodes:

``` python
def analyse_request(state: SupportState):
    print("Analysing customer request...")

    return {
        "order_id": "ORD-101"
    }


def retrieve_order(state: SupportState):
    print("Retrieving order...")

    return {
        "order_status": "shipped"
    }


def generate_response(state: SupportState):
    print("Generating response...")

    return {
        "response": (
            f"Your order {state['order_id']} "
            f"is currently {state['order_status']}."
        )
    }
```

Each function has a separate responsibility.

  Node                  Responsibility
  --------------------- -----------------------------
  `analyse_request`     Identify order information
  `retrieve_order`      Retrieve order status
  `generate_response`   Generate the final response

For now, these are deterministic functions, not LLM-powered agents. That
is intentional: first understand graph execution.

## 5. Edges --- controlling execution order

Nodes perform work. Edges determine what happens next.

Suppose we want this workflow:

``` text
START
  |
  v
Analyse Request
  |
  v
Retrieve Order
  |
  v
Generate Response
  |
  v
END
```

In LangGraph:

``` python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(SupportState)

builder.add_node("analyse", analyse_request)
builder.add_node("retrieve", retrieve_order)
builder.add_node("respond", generate_response)

builder.add_edge(START, "analyse")
builder.add_edge("analyse", "retrieve")
builder.add_edge("retrieve", "respond")
builder.add_edge("respond", END)
```

Special graph markers:

-   `START` --- virtual entry point of the graph.
-   `END` --- virtual terminal point.

You do not implement these yourself. LangGraph provides them.

## 6. Compile --- turning the graph into an executable workflow

So far, we have defined the graph structure, but we have not executed
it.

``` python
graph = builder.compile()
```

`compile()` validates and prepares the graph for execution.

Then invoke the compiled graph:

``` python
result = graph.invoke({
    "customer_message": "Where is my order?",
    "order_id": "",
    "order_status": "",
    "response": "",
})

print(result)
```

Expected output:

``` python
{
    "customer_message": "Where is my order?",
    "order_id": "ORD-101",
    "order_status": "shipped",
    "response": "Your order ORD-101 is currently shipped.",
}
```

Execution order:

``` text
Analysing customer request...
Retrieving order...
Generating response...
```

**Remember:** `StateGraph` is the builder. `compile()` produces the
executable graph. You call `invoke()` on the compiled graph, not on the
builder.

## 7. Complete runnable implementation

Install the packages:

``` bash
pip install -U langgraph typing_extensions
```

Create `main.py`:

``` python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. Define shared state
class SupportState(TypedDict):
    customer_message: str
    order_id: str
    order_status: str
    response: str


# 2. Define nodes
def analyse_request(state: SupportState):
    print("[Analyse] Understanding request...")

    # Simulated extraction.
    # A real application should extract this from the message
    # or receive it from trusted application context.
    return {
        "order_id": "ORD-101"
    }


def retrieve_order(state: SupportState):
    print("[Retrieve] Fetching order...")

    # Simulated database result
    orders = {
        "ORD-101": "shipped",
        "ORD-102": "delayed",
    }

    status = orders.get(state["order_id"], "not_found")

    return {
        "order_status": status
    }


def generate_response(state: SupportState):
    print("[Response] Generating final response...")

    if state["order_status"] == "not_found":
        message = f"We could not find order {state['order_id']}."
    else:
        message = (
            f"Your order {state['order_id']} "
            f"is currently {state['order_status']}."
        )

    return {
        "response": message
    }


# 3. Build the graph
builder = StateGraph(SupportState)

builder.add_node("analyse", analyse_request)
builder.add_node("retrieve", retrieve_order)
builder.add_node("respond", generate_response)

builder.add_edge(START, "analyse")
builder.add_edge("analyse", "retrieve")
builder.add_edge("retrieve", "respond")
builder.add_edge("respond", END)


# 4. Compile the graph
graph = builder.compile()


# 5. Execute the graph
result = graph.invoke({
    "customer_message": "Where is my order?",
    "order_id": "",
    "order_status": "",
    "response": "",
})


# 6. Read the result
print("\nFINAL RESULT:")
print(result["response"])
```

Expected output:

``` text
[Analyse] Understanding request...
[Retrieve] Fetching order...
[Response] Generating final response...

FINAL RESULT:
Your order ORD-101 is currently shipped.
```

**Important limitation:** The `analyse_request` node currently uses a
hardcoded order ID. In a real application, it would extract the ID from
the user's message or receive it from trusted application context. The
retrieval node would query PostgreSQL.

## 8. LangChain vs LangGraph

  -----------------------------------------------------------------------
  Feature                 LangChain               LangGraph
  ----------------------- ----------------------- -----------------------
  Prompt templates        Yes                     Can use LangChain
                                                  prompts

  Model integrations      Yes                     Can use LangChain
                                                  models

  Tool definitions        Yes                     Can use LangChain tools

  Sequential pipelines    Yes                     Yes

  Shared graph state      Not its primary         Core feature
                          abstraction             

  Conditional routing     Runnable patterns such  Graph edges
                          as `RunnableBranch`     

  Cycles and loops        Can be composed         Native graph control
                                                  flow

  Checkpointing           Integrations available  Core capability
  -----------------------------------------------------------------------

Neither is a replacement for the other. You can use LangChain components
inside LangGraph workflows.

## 9. Five mistakes beginners make

1.  **Thinking a node must be an LLM:** A node can be an ordinary Python
    function.
2.  **Thinking edges perform work:** Nodes perform work; edges control
    execution.
3.  **Mutating state everywhere:** Prefer returning partial state
    updates.
4.  **Forgetting compilation:** Follow the sequence build → compile →
    invoke.
5.  **Confusing state with persistent memory:** State is the data passed
    through graph execution. Persistence across executions requires a
    checkpointer.

------------------------------------------------------------------------

## Engineering takeaway

Understand the separation of responsibilities:

-   **State** carries workflow data.
-   **Nodes** perform work and return updates.
-   **Edges** control execution order and routing.
-   **The graph** defines the complete workflow.
-   **Compilation** prepares the graph for execution.

Start with deterministic nodes and understand the graph mechanics before
introducing LLMs, tools, retries, and persistence. That makes debugging
substantially easier.
