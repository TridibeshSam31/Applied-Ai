# Shared State & Memory Across Agents

## 1. Why Do Agents Need Shared State?

Imagine a system with three agents:

-   Research Agent
-   Developer Agent
-   Testing Agent

The Research Agent discovers requirements. The Developer Agent needs
those requirements to generate code. The Testing Agent needs the
generated code to test it.

How do agents share this information?

This is where **Shared State** and **Memory** become important.

## 2. What Is Shared State?

Shared State is a common data structure in which multiple agents can
read and update information during a workflow.

Example:

``` python
state = {
    "user_request": "Build a student management API",
    "requirements": [],
    "generated_code": None,
    "test_results": None,
    "current_status": "started"
}
```

Multiple agents can access this state:

``` text
               Shared State
           Common workflow data
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
     Research   Developer    Testing
      Agent       Agent       Agent
        |           |           |
   Updates       Updates     Updates
 requirements     code    test results
```

Each agent reads relevant information and contributes its output.

Think of Shared State as a common workspace for all agents.

## 3. Implement Shared State

### Step 1 --- Define the state

In Python, we can use `TypedDict`.

``` python
from typing import TypedDict


class AgentState(TypedDict):
    user_request: str
    requirements: list[str]
    generated_code: str
    test_results: str
    current_status: str
```

Create the initial state:

``` python
state: AgentState = {
    "user_request": "Build student management API",
    "requirements": [],
    "generated_code": "",
    "test_results": "",
    "current_status": "started"
}
```

### Step 2 --- Research Agent

The Research Agent discovers requirements and returns its state updates.

``` python
def research_agent(state: AgentState):
    requirements = [
        "Create student endpoint",
        "Get student endpoint",
        "Update student endpoint",
        "Delete student endpoint"
    ]

    return {
        "requirements": requirements,
        "current_status": "research_completed"
    }
```

**Notice:** The agent does not return the complete state. It returns
only the fields it wants to update.

### Step 3 --- Developer Agent

The Developer Agent reads the requirements from the existing state.

``` python
def developer_agent(state: AgentState):
    requirements = state["requirements"]

    code = f"""
    # Student API
    # Requirements:
    {requirements}

    def create_student():
        pass

    def get_student():
        pass

    def update_student():
        pass

    def delete_student():
        pass
    """

    return {
        "generated_code": code,
        "current_status": "development_completed"
    }
```

### Step 4 --- Testing Agent

``` python
def testing_agent(state: AgentState):
    code = state["generated_code"]

    if not code:
        return {
            "test_results": "No code available"
        }

    return {
        "test_results": "Basic checks completed"
    }
```

### Step 5 --- Execute the workflow

``` python
state.update(research_agent(state))
state.update(developer_agent(state))
state.update(testing_agent(state))

print(state)
```

All three agents have now contributed to the same workflow state.

**Important:** This is a sequential simulation. The agents are not
independently LLM-powered. It demonstrates the shared-state mechanism.

## 4. Shared State vs Memory

Do not confuse these concepts.

-   **Shared State:** Information used within the current workflow.
-   **Memory:** Information retained from past interactions or
    experiences.

Example user request:

> Check my order and create a ticket if it is delayed.

Shared state:

``` python
state = {
    "customer_id": "customer-123",
    "order_status": "delayed",
    "ticket_created": False
}
```

This represents information for the current execution.

Memory:

``` python
memory = {
    "customer_preference": "Email notifications",
    "previous_issue": "Late delivery",
    "preferred_language": "English"
}
```

This information may be useful in future conversations.

  Shared State                   Memory
  ------------------------------ -------------------------------------
  Current workflow information   Retained information
  Execution-specific             Can persist across executions
  Task progress                  Past interactions and knowledge
  Often temporary                Often long-term
  Used for coordination          Used for personalization and recall

Memory itself can also be shared across agents, but access should be
controlled.

## 5. Types of Memory Across Agents

### A. Shared Memory

Multiple agents access common information.

Example: Research Agent and Financial Agent both access the same
verified market research.

### B. Private Memory

An individual agent maintains its own information.

Examples:

-   Research Agent remembers previously investigated sources.
-   Coding Agent remembers its implementation conventions.

### C. Episodic Memory

Stores information about past events or executions.

Example:

``` text
Previous execution:
- Research completed
- Code generated
- Testing failed
- Developer fixed the issue
```

### D. Semantic Memory

Stores reusable facts and knowledge.

Examples:

``` text
PostgreSQL supports ACID transactions.
FastAPI supports dependency injection.
```

**Architectural consideration:** Shared memory does not mean every agent
should have unrestricted access to every piece of information.

## 6. Concurrent State Updates: The Write Conflict Problem

Consider two agents executing simultaneously.

Initial state:

``` python
state = {
    "research_result": None,
    "competitor_result": None
}
```

Research Agent updates:

``` python
state["research_result"] = "Market is growing"
```

Competitor Agent updates:

``` python
state["competitor_result"] = "Tata and Mahindra"
```

In this example, both update different keys, so no conflict occurs.

But imagine both agents update the same key:

``` python
# Agent A
state["analysis"] = "Market growing"

# Agent B
state["analysis"] = "Market declining"
```

Which value should survive?

This is a **write conflict**.

### Possible solutions

1.  Assign different state keys to different agents.
2.  Use controlled merge functions.
3.  Use append-only lists for independent results.
4.  Use locks or transactional updates when necessary.
5.  Define an explicit conflict-resolution strategy.

### Example: Merge instead of overwrite

``` python
def merge_results(old_results, new_results):
    return old_results + new_results


results = []

results = merge_results(
    results,
    ["Market research completed"]
)

results = merge_results(
    results,
    ["Competitor research completed"]
)

print(results)
```

Output:

``` python
[
    "Market research completed",
    "Competitor research completed"
]
```

This avoids losing independent results.

However, simple list merging is not sufficient for every concurrent
system. Production systems need deterministic merge semantics and
careful handling of duplicate updates.

## 7. How LangGraph Uses Shared State

LangGraph uses a shared state schema to pass information between graph
nodes.

  Our concept            LangGraph
  ---------------------- ------------------
  Shared State           State schema
  Agent function         Node
  Agent execution path   Edge
  Conditional routing    Conditional Edge
  State update rules     Reducers
  Persistent state       Checkpointer

### Reducers

A reducer defines how updates to a particular state field should be
combined.

Example:

``` python
from typing import Annotated
from typing_extensions import TypedDict
import operator


class AgentState(TypedDict):
    user_request: str
    results: Annotated[list[str], operator.add]
```

Here, `operator.add` acts as a reducer for the `results` field.

If one node returns:

``` python
{"results": ["Research completed"]}
```

And another returns:

``` python
{"results": ["Competitor analysis completed"]}
```

The updates can be combined:

``` python
[
    "Research completed",
    "Competitor analysis completed"
]
```

This is particularly useful when multiple parallel nodes contribute to
the same state field.

**Important:** LangGraph reducers govern how state updates are combined.
They do not automatically solve every business-level conflict or
guarantee database consistency.

## 8. Practical Architecture: Our Customer Support Agent

Let's connect everything to the single-agent project.

Customer asks:

> My order is delayed. Check its status and raise a ticket.

Our agent execution state could look like:

``` python
state = {
    "customer_id": "customer-123",
    "user_message": "My order is delayed",
    "order_id": "order-456",
    "order_status": None,
    "ticket_id": None,
    "tool_calls": [],
    "current_step": "checking_order",
    "final_response": None
}
```

Execution:

``` text
User Request
     |
     v
Agent Runtime
     |
     v
Shared Execution State
     |
     v
get_order_status()
     |
     v
Update order_status
     |
     v
create_support_ticket()
     |
     v
Update ticket_id
     |
     v
Generate final response
```

Even in a single-agent system, structured state is useful.

When we later convert this into a multi-agent architecture, multiple
specialized nodes can contribute to a shared workflow state.

## 9. Important Interview Concepts

  Concept             What you should understand
  ------------------- ---------------------------------------
  Shared State        Common execution data
  Private State       Agent-specific information
  Long-term Memory    Information retained across sessions
  Short-term Memory   Information used in current context
  State Reducer       Combines state updates
  State Conflict      Multiple agents update the same field
  Checkpointing       Saves execution state for recovery
  State Persistence   Stores state beyond process memory

**Important distinction:** Checkpointing is not the same as long-term
memory. A checkpoint usually captures workflow progress so execution can
resume.

## 10. Quick Revision

-   Shared State is common execution data accessible to multiple agents.
-   Agents can return partial state updates rather than complete state
    objects.
-   Memory retains useful information from past interactions or
    experiences.
-   Shared, private, episodic, and semantic memory represent different
    memory designs.
-   Concurrent updates to the same field can create write conflicts.
-   Merge functions, reducers, locks, and explicit conflict-resolution
    rules help manage updates.
-   LangGraph uses state schemas and reducers to manage workflow state.
-   Checkpointing saves workflow progress for recovery; it is not
    equivalent to long-term memory.
-   Access to shared memory should be controlled.

**Core takeaway:** Shared State coordinates what agents know during the
current workflow. Memory helps retain information beyond that workflow.
A reliable system needs clear state ownership, controlled access, and
well-defined update and merge rules.
