# Module 6: State Management in AI Agents

> **Important for LangGraph and production agents**

## 1. What Exactly Is State?

Imagine you're building an AI customer support agent.

A customer says:

1.  My order ID is 12345.
2.  Check its delivery status.
3.  It's delayed. Create a support ticket.
4.  Tell me the ticket ID.

How does the agent remember the order ID between these steps?

It needs **State**.

State is the structured collection of information representing the
current condition and progress of an agent or workflow.

Example:

``` python
state = {
    "user_id": "U101",
    "order_id": "12345",
    "order_status": "delayed",
    "ticket_id": None,
    "messages": [],
    "current_step": "check_order"
}
```

As the agent executes tasks, this state changes.

------------------------------------------------------------------------

## 2. State vs. Memory vs. Context

These three concepts are frequently confused.

  -----------------------------------------------------------------------
  Concept                 Meaning                 Example
  ----------------------- ----------------------- -----------------------
  State                   Current execution       Current order ID
                          information             

  Memory                  Information retained    Customer prefers
                          for future use          English

  Context                 Information supplied to User message + relevant
                          the LLM for a           memories + instructions
                          particular request      
  -----------------------------------------------------------------------

Think of it this way:

-   **State** tells you where the agent currently is.
-   **Memory** tells you what the agent knows from previous
    interactions.
-   **Context** tells you what the model can see right now.

They can overlap, but they are not interchangeable.

------------------------------------------------------------------------

## 3. How State Changes During Execution

Let's track our customer support example.

### State Transitions

  ----------------------------------------------------------------------------------
  Step              State update                 Order status      Ticket
  ----------------- ---------------------------- ----------------- -----------------
  1\. Initial state Order ID not known           Unknown           Not created

  2\. User provides `order_id = "12345"`         Unknown           Not created
  ID                                                               

  3\. Order lookup  `order_status = "delayed"`   Delayed           Not created

  4\. Ticket        `ticket_id = "TICKET-101"`   Delayed           TICKET-101
  creation                                                         

  5\. Task          Workflow marked complete     Delayed           TICKET-101
  completed                                                        
  ----------------------------------------------------------------------------------

The state gets updated after each operation.

This is particularly useful when an agent has multiple tools, multiple
steps, or multiple execution paths.

------------------------------------------------------------------------

## 4. Let's Code: State Management Without Any Framework

First, we'll implement it ourselves.

### Step 1: Define the Initial State

``` python
state = {
    "order_id": "12345",
    "order_status": None,
    "ticket_id": None,
    "current_step": "START"
}
```

### Step 2: Create Functions That Update State

``` python
def fetch_order(state):
    order_id = state["order_id"]

    # Simulated database response
    order = {
        "id": order_id,
        "status": "delayed"
    }

    state["order_status"] = order["status"]
    state["current_step"] = "ORDER_FETCHED"

    return state
```

### Step 3: Create a Support Ticket

``` python
def create_ticket(state):
    if state["order_status"] != "delayed":
        return state

    state["ticket_id"] = "TICKET-101"
    state["current_step"] = "TICKET_CREATED"

    return state
```

### Step 4: Execute the Workflow

``` python
state = fetch_order(state)
state = create_ticket(state)

print(state)
```

Output:

``` python
{
    "order_id": "12345",
    "order_status": "delayed",
    "ticket_id": "TICKET-101",
    "current_step": "TICKET_CREATED"
}
```

Congratulations, you've implemented a basic stateful workflow without
using LangGraph.

Notice that we haven't used an LLM yet. That's intentional: state
management is a software engineering concept independent of AI.

------------------------------------------------------------------------

## 5. State Management with Python Dataclasses

Using dictionaries is convenient, but large applications need stronger
structure.

Python's `dataclasses` help us define structured state.

``` python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentState:
    user_id: str
    order_id: Optional[str] = None
    order_status: Optional[str] = None
    ticket_id: Optional[str] = None
    messages: list = field(default_factory=list)
    current_step: str = "START"
```

Create an instance:

``` python
state = AgentState(
    user_id="U101",
    order_id="12345"
)

state.order_status = "delayed"
state.ticket_id = "TICKET-101"

print(state)
```

### Why Use `default_factory=list`?

Mutable defaults should not be shared between different instances. Each
agent state should have its own message list.

For larger applications, you can also use Pydantic models for validation
and typed data structures.

------------------------------------------------------------------------

## 6. Persistence: What If the Server Crashes?

This is where state management becomes interesting.

Imagine: - An agent has completed 4 out of 7 tasks. - Your server
crashes. - The process restarts.

If state existed only in RAM, the agent might lose its progress.

We need **persistence**.

### Common Options

  Technology               Use
  ------------------------ ----------------------------------
  Redis                    Fast state storage and caching
  PostgreSQL               Durable workflow state
  SQLite                   Local development and prototypes
  LangGraph Checkpointer   Persisting graph execution state

### Simple PostgreSQL Example

Conceptually, you might store workflow state in a table:

``` sql
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    state JSONB NOT NULL,
    status TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

Save state:

``` python
import json

state = {
    "order_id": "12345",
    "current_step": "TICKET_CREATED",
    "ticket_id": "TICKET-101"
}

cursor.execute(
    """
    INSERT INTO agent_runs (id, user_id, state, status)
    VALUES (%s, %s, %s, %s)
    """,
    (
        run_id,
        "U101",
        json.dumps(state),
        "IN_PROGRESS"
    )
)

connection.commit()
```

In a real implementation, use parameterized queries, transactions, and
appropriate connection management.

------------------------------------------------------------------------

## 7. What Is Checkpointing?

**Checkpointing** means saving the execution state at particular points
so that execution can resume later.

### Example

``` text
Task 1: Completed
       |
       v
Checkpoint 1 saved
       |
       v
Task 2: Completed
       |
       v
Checkpoint 2 saved
       |
       v
Task 3: Server crashes
       |
       v
Server restarts
       |
       v
Restore Checkpoint 2
       |
       v
Continue from Task 3
```

This is especially important for: - Long-running agents. - Multi-step
workflows. - Human approval processes. - Unreliable external APIs. -
Multi-agent systems.

**Important:** Restoring state doesn't automatically make external
actions safe to repeat. You still need idempotency to prevent duplicate
payments, emails, or tickets.

------------------------------------------------------------------------

## 8. State Management in LangGraph

Now let's connect this to the framework we'll learn later.

LangGraph uses a shared state schema that nodes read and update.

### Define the State

``` python
from typing import TypedDict


class AgentState(TypedDict):
    user_message: str
    order_id: str
    order_status: str
    response: str
```

### Create a Node

``` python
def check_order(state: AgentState):
    order_id = state["order_id"]

    status = "delayed"  # Simulated lookup

    return {
        "order_status": status
    }
```

Notice something important:

The node returns a dictionary containing the state updates.

LangGraph manages how those updates are applied to the graph's shared
state.

We'll implement a complete LangGraph workflow in the framework module,
including nodes, edges, conditional routing, and checkpointing.

------------------------------------------------------------------------

## 9. Production-Level Concepts You Must Know

  Concept               Why it matters
  --------------------- --------------------------------
  Typed state           Prevent inconsistent data
  State transitions     Control workflow progression
  Persistence           Survive process restarts
  Checkpointing         Resume interrupted executions
  Concurrency control   Avoid conflicting updates
  Idempotency           Prevent duplicate side effects
  State isolation       Prevent cross-user data leaks
  Versioning            Handle changes in state schema

### Keep State Focused

State should contain execution data, not necessarily every piece of
information the agent has ever encountered.

For example, an order-support workflow might need: - Current user and
order identifiers. - Order lookup result. - Ticket creation result. -
Current workflow step. - Relevant messages or task metadata.

It does not need to copy the user's entire long-term profile into every
workflow state.

------------------------------------------------------------------------

## 10. Key Takeaways

-   State represents the current condition and progress of an agent or
    workflow.
-   State changes as nodes, tools, and workflow steps execute.
-   State, memory, and context are related but different.
-   Dictionaries are useful for simple implementations; dataclasses and
    typed schemas provide more structure.
-   In-memory state is lost when the process stops unless it is
    persisted.
-   Checkpointing saves execution progress so an interrupted workflow
    can resume.
-   Idempotency is still needed when resuming workflows that perform
    external side effects.
-   LangGraph nodes read shared state and return updates.
-   Production state needs validation, isolation, concurrency control,
    and versioning.

------------------------------------------------------------------------

## 11. Interview Questions

### Q1. What is state in an AI agent?

State is the structured information representing the current condition
and progress of an agent or workflow. It can contain task inputs,
intermediate results, execution status, and other information needed by
later steps.

### Q2. What is the difference between state, memory, and context?

State represents current execution information. Memory preserves
information for future use. Context is the information supplied to the
LLM for a particular request.

### Q3. Why is state management important in multi-step agents?

It allows different steps and tools to share relevant information, track
progress, and make decisions based on previous execution results.

### Q4. Why use dataclasses instead of dictionaries?

Dataclasses provide a structured representation with declared fields and
type annotations. They make state easier to understand and maintain as
an application grows.

### Q5. What happens to in-memory state when a server crashes?

It is lost when the process terminates. To recover progress, the
application must persist state somewhere durable.

### Q6. What is checkpointing?

Checkpointing saves execution state at particular points so an
interrupted workflow can restore a previous checkpoint and continue.

### Q7. Does checkpointing prevent duplicate tool execution?

No. A resumed workflow may repeat an external action if it cannot
determine whether that action already succeeded. Idempotency and durable
operation tracking help prevent duplicate side effects.

### Q8. How does LangGraph manage state?

LangGraph defines a shared state schema. Nodes read the current state
and return updates, which the graph applies according to its state and
reducer configuration.

------------------------------------------------------------------------

## 12. Quick Revision

  Term               Remember
  ------------------ -----------------------------------------------
  State              Current execution information
  Memory             Information retained for future use
  Context            Information supplied to the model now
  State transition   Change in workflow state
  Dataclass          Structured Python state representation
  Persistence        Saving state beyond process memory
  Checkpointing      Saving execution progress for recovery
  Checkpointer       Component that saves and restores graph state
  Idempotency        Preventing duplicate side effects
  State isolation    Keeping different users' state separate

**Core architecture to remember:**

``` text
Initial State
     |
     v
Execute Node / Tool
     |
     v
Return State Updates
     |
     v
Apply State Changes
     |
     v
Persist / Checkpoint
     |
     v
Next Node or Resume Later
```

**Interview one-liner:** State management gives an agent a structured
representation of its current execution, allowing steps to share data,
track progress, and recover from interruptions when state is persisted
and checkpointed.
