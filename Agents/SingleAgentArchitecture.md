# Module 7: Single-Agent Architecture

> **Architecture + implementation**

## 1. What Is Single-Agent Architecture?

A **single-agent system** uses one primary AI agent to understand a
user's goal, make decisions, use tools, maintain state, and complete
tasks.

It can use multiple tools, APIs, and databases without requiring
multiple autonomous agents.

### Example: AI Customer Support Assistant

One agent can: - Retrieve customer details. - Check order status. -
Process eligible refunds. - Create support tickets. - Send
notifications.

One agent controls the overall execution.

------------------------------------------------------------------------

## 2. Understand the Architecture

### Single-Agent System Architecture

``` text
                  User Interface
                Next.js / Chat UI
                        |
                        v
                   Backend API
              FastAPI / Request handling
                        |
                        v
                   Agent Runtime
                Controls execution loop
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
         LLM          Memory         State
      Reasoning      Retrieval      Progress
          |             |             |
          +-------------+-------------+
                        |
                        v
                   Tool Registry
                     Execution
                        |
                        v
                 External Systems
          PostgreSQL · External APIs
              Email · Business services
```

The **Agent Runtime** is the central component.

It coordinates the model, tools, memory, and state.

------------------------------------------------------------------------

## 3. Understand the Responsibilities

  Component       Responsibility
  --------------- ----------------------------------------
  LLM             Decide what to do
  Agent runtime   Control execution
  Tool registry   Map tool names to functions
  Memory          Retrieve relevant previous information
  State           Track current execution
  Database        Persist application data
  Backend API     Handle requests and authentication

**Remember:** The LLM is not the entire agent. The surrounding software
is what makes the system operational.

------------------------------------------------------------------------

## 4. Let's Build a Single-Agent System in Python

We'll start with a simplified architecture, without LangGraph.

Our agent will support two tools:

1.  `get_order_status()`
2.  `create_support_ticket()`

### Step 1: Define the Tools

``` python
def get_order_status(order_id: str):
    orders = {
        "12345": "delayed",
        "12346": "delivered"
    }

    return orders.get(order_id, "not_found")


def create_support_ticket(issue: str):
    return {
        "ticket_id": "TICKET-101",
        "status": "created",
        "issue": issue
    }
```

### Step 2: Create a Tool Registry

``` python
tool_registry = {
    "get_order_status": get_order_status,
    "create_support_ticket": create_support_ticket
}
```

### Step 3: Define the Agent State

We'll use the `AgentState` dataclass discussed earlier, adapted for this
workflow.

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

### Step 4: Implement the Execution Runtime

``` python
def run_agent(state: AgentState):
    # First action: retrieve order
    status = tool_registry["get_order_status"](
        state.order_id
    )

    state.order_status = status
    state.current_step = "ORDER_CHECKED"

    if status == "delayed":
        result = tool_registry["create_support_ticket"](
            "Order delivery delayed"
        )

        state.ticket_id = result["ticket_id"]
        state.current_step = "TICKET_CREATED"

    elif status == "not_found":
        state.current_step = "ORDER_NOT_FOUND"

    else:
        state.current_step = "COMPLETED"

    return state
```

### Step 5: Run It

``` python
state = AgentState(
    user_id="U101",
    order_id="12345"
)

final_state = run_agent(state)

print(final_state)
```

Expected result:

``` python
AgentState(
    user_id='U101',
    order_id='12345',
    order_status='delayed',
    ticket_id='TICKET-101',
    current_step='TICKET_CREATED'
)
```

### What We Just Built

We created a basic stateful, tool-enabled workflow.

But here's the catch: **This is not yet a fully autonomous LLM-powered
agent.**

Why?

Because the execution sequence is hardcoded:

``` python
status = get_order_status(...)

if status == "delayed":
    create_support_ticket(...)
```

The program decides the next action using fixed Python logic, not an
LLM.

That distinction matters.

------------------------------------------------------------------------

## 5. Convert This into a Real LLM-Powered Agent

The next architectural step is to replace the hardcoded decision-making
with an LLM.

The model receives: - User instructions. - Available tool
descriptions. - Current conversation context. - Relevant state.

It can then request a tool call.

Your runtime validates and executes the request, returns the result, and
asks the model what to do next.

### LLM-Powered Execution Flow

``` text
               User Request
                    |
                    v
               Agent Runtime
                    |
                    v
              LLM decides action
                    |
                    v
             Tool call requested?
                /         \
              Yes          No
               |            |
               v            v
         Validate tool   Final response
               |
               v
          Execute tool
               |
               v
          Update state
               |
               +------> LLM again
```

This is the architecture we'll implement in our coding sessions using a
real LLM API.

------------------------------------------------------------------------

## 6. Single-Agent vs. Multi-Agent

An important design question: When should you use one agent, and when
should you use several?

  -----------------------------------------------------------------------
  Single-Agent                        Multi-Agent
  ----------------------------------- -----------------------------------
  One central decision-maker          Multiple specialized agents

  Simpler orchestration               More complex orchestration

  Easier debugging                    More coordination overhead

  Shared execution context            Communication between agents

  Good for bounded tasks              Useful for complex, separable
                                      responsibilities
  -----------------------------------------------------------------------

### Engineering Advice

Don't use multiple agents just because the framework supports them. A
well-designed single agent is often more reliable and cheaper.

Use multiple agents when responsibilities are genuinely separable and
the benefits justify the additional coordination, latency, and failure
modes.

------------------------------------------------------------------------

## 7. Common Architectural Mistakes

1.  **Putting all business logic inside the LLM prompt.** Business rules
    should be enforced by application code.
2.  **Giving the model unrestricted access to tools.** Use tool
    allowlists and backend authorization.
3.  **Mixing memory, state, and application data.** Give each a clear
    responsibility.
4.  **Having no maximum iteration limit.** Bound the execution loop.
5.  **Failing to handle tool errors.** Return structured errors and
    define retry behavior.
6.  **Not tracking execution traces.** Log tool calls, outcomes, and
    important state transitions.
7.  **Using multiple agents where ordinary functions would work.** Keep
    the architecture as simple as the problem allows.

These are real engineering problems, not merely theoretical interview
questions.

------------------------------------------------------------------------

## 8. Key Takeaways

-   A single-agent system uses one primary agent to coordinate the task.
-   One agent can use many tools and external services.
-   The agent runtime coordinates the LLM, tools, memory, and state.
-   The LLM is only one component of the complete system.
-   A hardcoded tool workflow is stateful automation, not necessarily an
    autonomous LLM-powered agent.
-   A real LLM-powered agent selects actions at runtime through tool
    calls.
-   Start with a single agent unless multiple autonomous decision-makers
    solve a clear architectural need.

------------------------------------------------------------------------

## 9. Interview Questions

### Q1. What is single-agent architecture?

It is an architecture in which one primary AI agent coordinates
reasoning, tool use, state, and task execution. It can still interact
with many external tools and services.

### Q2. Can a single agent use multiple tools?

Yes. A single agent can have access to multiple tools through a registry
or another tool-dispatch mechanism. Multiple tools do not imply multiple
agents.

### Q3. What is the responsibility of the agent runtime?

The runtime manages the execution loop: it sends context to the model,
handles tool-call requests, validates and executes tools, updates state,
and determines when to return a final response.

### Q4. Is the Python example in this module a fully autonomous agent?

No. Its next action is determined by hardcoded Python conditions. It
demonstrates stateful tool execution, but the LLM is not dynamically
selecting actions.

### Q5. What is the difference between single-agent and multi-agent architecture?

A single-agent system has one primary decision-maker. A multi-agent
system has multiple agents, often with specialized responsibilities,
that must coordinate or communicate.

### Q6. When should you choose a single agent?

Choose one when the task has a bounded scope and one decision-maker can
handle the required tools and responsibilities without excessive
complexity.

### Q7. Why is the agent runtime important?

It provides the control and safety layer around the model. It handles
execution, tool validation, state updates, errors, and stopping
conditions.

------------------------------------------------------------------------

## 10. Quick Revision

  -----------------------------------------------------------------------
  Term                                Remember
  ----------------------------------- -----------------------------------
  Single-agent architecture           One primary agent coordinates the
                                      task

  Agent runtime                       Controls the model/tool execution
                                      loop

  Tool registry                       Maps tool names to implementations

  State                               Tracks current execution

  Memory                              Retrieves useful previous
                                      information

  Hardcoded workflow                  Application logic predetermines the
                                      steps

  LLM-powered agent                   Model selects actions dynamically

  Multi-agent architecture            Multiple agents coordinate
                                      responsibilities
  -----------------------------------------------------------------------

**Core architecture to remember:**

``` text
User Request
     |
     v
Backend API
     |
     v
Agent Runtime <----> State / Memory
     |
     v
    LLM
     |
     v
Tool Request
     |
     v
Validate + Execute
     |
     v
Update State
     |
     +----> LLM continues
     |
     v
Final Response
```

**Interview one-liner:** A single-agent architecture uses one primary
decision-maker, coordinated by an application runtime, to reason, invoke
multiple tools, manage state, and complete a task.
