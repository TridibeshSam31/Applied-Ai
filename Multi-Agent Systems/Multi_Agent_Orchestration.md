# Orchestration, Delegation & Coordination

## 1. The Three Core Concepts

In previous topics, we covered:

-   What Multi-Agent Systems are.
-   Different agent architectures.
-   How agents communicate.
-   Message passing and shared state.

Now consider this question:

**If five agents are available, how does the system decide which agent
should work, who receives each task, and how their outputs are
combined?**

This is the job of orchestration, delegation, and coordination.

These concepts are related, but they are not the same.

### Orchestration

Managing the overall workflow.

Example: Deciding whether the Research Agent or Budget Agent should
execute first.

### Delegation

Assigning a task from one agent to another.

Example: A Supervisor assigns market research to the Research Agent.

### Coordination

Synchronizing the work of multiple agents.

Example: The Developer Agent should execute only after the Research
Agent has provided the requirements.

**Easy analogy:**

-   Orchestration = A project manager managing the overall project.
-   Delegation = The manager assigning a task.
-   Coordination = Team members synchronizing their work.

## 2. Understand Orchestration with a Real Example

Suppose we are building an AI-powered market research system.

User asks:

> Research the Indian EV market and prepare a competitor analysis.

We have four agents:

1.  Market Research Agent
2.  Competitor Analysis Agent
3.  Financial Analysis Agent
4.  Report Generation Agent

The Supervisor Agent decomposes the task and manages execution.

``` text
                 Supervisor Agent
             Decomposes and manages work
                         |
          +--------------+--------------+
          |                             |
          v                             v
   Market Research              Competitor Analysis
       Agent                         Agent
          |                             |
          +--------------+--------------+
                         |
                         v
              Financial Analysis Agent
                Uses both outputs
                         |
                         v
              Report Generation Agent
                Combines all results
```

Notice:

-   Market Research and Competitor Analysis can run independently.
-   Financial Analysis may need the outputs from both.
-   Report Generation combines the results.

Therefore, the system must understand **task dependencies**. This is a
major part of orchestration.

## 3. Task Decomposition

Before delegating, the supervisor needs to break a complex task into
smaller tasks.

Example:

``` text
Main Task:
Research Indian EV Market

Subtasks:
1. Research market size
2. Identify major competitors
3. Analyze competitor pricing
4. Analyze financial performance
5. Generate final report
```

### Why decompose tasks?

-   Smaller tasks are easier to execute.
-   Different agents can specialize.
-   Independent tasks can execute in parallel.
-   Failures can be isolated.
-   Results can be evaluated individually.

**Important:** Task decomposition and delegation are not identical.

-   Decomposition breaks a task into smaller pieces.
-   Delegation assigns those pieces to agents.

## 4. Task Dependencies and DAG

A Directed Acyclic Graph (DAG) represents tasks and their dependencies.

Suppose:

-   A = Market Research
-   B = Competitor Analysis
-   C = Financial Analysis
-   D = Final Report

Dependencies:

-   C requires A and B.
-   D requires C.

``` text
A: Market Research ─────┐
                        ├──> C: Financial Analysis ──> D: Final Report
B: Competitor Analysis ─┘
```

A and B can run in parallel. C waits for both. D waits for C.

This is called **dependency-aware execution**.

DAGs are important in workflow orchestration frameworks such as
LangGraph and other workflow engines.

## 5. Types of Orchestration

There are three execution strategies to understand.

### A. Sequential orchestration

One agent completes its task, then the next starts.

``` text
Agent A → Agent B → Agent C → Agent D
```

**Use when:** Each task depends on the previous task.

### B. Parallel orchestration

Independent agents execute concurrently.

``` text
          Supervisor
           /      \
          v        v
       Agent A   Agent B
          \        /
           \      /
            Result
```

**Use when:** Tasks are independent.

Benefits:

-   Lower overall execution time when tasks can overlap.
-   Better resource utilization.
-   Independent tasks do not need to wait for each other.

However, parallel execution increases resource usage and requires
careful handling of failures and shared data.

### C. Conditional orchestration

The next agent depends on the previous result.

``` text
          Supervisor
               |
               v
         Analysis Agent
               |
               v
            Decision
             /    \
            v      v
         Agent A  Agent B
```

Example:

-   If a customer requests a refund → Refund Agent.
-   If a customer reports a technical problem → Technical Support Agent.

This is **dynamic routing**.

## 6. Build a Simple Orchestrator in Python

First, we will build a simple market research workflow without
LangGraph. The goal is to understand the underlying mechanics.

### Step 1 --- Create specialized agents

``` python
def market_research_agent(task):
    print("Market Research Agent executing...")

    return {
        "market_size": "Large and growing",
        "market": "Indian EV market"
    }


def competitor_agent(task):
    print("Competitor Agent executing...")

    return {
        "competitors": [
            "Tata Motors",
            "Mahindra",
            "Ola Electric"
        ]
    }


def financial_agent(research, competitors):
    print("Financial Agent executing...")

    return {
        "market": research["market"],
        "competitors": competitors["competitors"],
        "analysis": "Financial analysis completed"
    }


def report_agent(financial_data):
    print("Report Agent executing...")

    return {
        "report": "Market research report generated",
        "financial_data": financial_data
    }
```

Each agent has a distinct responsibility.

### Step 2 --- Create the orchestrator

``` python
def orchestrator(user_task):
    # Step 1: Run independent tasks
    research = market_research_agent(user_task)
    competitors = competitor_agent(user_task)

    # Step 2: Run the dependent task
    financial = financial_agent(
        research,
        competitors
    )

    # Step 3: Generate the final report
    report = report_agent(financial)

    return report


result = orchestrator("Research Indian EV market")
print(result)
```

This version runs the two independent research functions one after
another, then runs the dependent work.

Research and Competitor Analysis do not depend on each other, so we can
improve the workflow by running them concurrently.

### Step 3 --- Parallel execution using `asyncio`

``` python
import asyncio


async def market_research_agent(task):
    print("Market Research Agent started...")
    await asyncio.sleep(2)

    return {
        "market_size": "Large and growing"
    }


async def competitor_agent(task):
    print("Competitor Agent started...")
    await asyncio.sleep(2)

    return {
        "competitors": [
            "Tata Motors",
            "Mahindra"
        ]
    }


async def financial_agent(research, competitors):
    print("Financial Agent started...")

    return {
        "research": research,
        "competitors": competitors
    }


async def orchestrator(task):
    # Run independent agents concurrently
    research, competitors = await asyncio.gather(
        market_research_agent(task),
        competitor_agent(task)
    )

    # Wait for both results before continuing
    financial = await financial_agent(
        research,
        competitors
    )

    return financial


async def main():
    result = await orchestrator(
        "Research Indian EV market"
    )

    print(result)


asyncio.run(main())
```

Expected execution order:

``` text
Market Research Agent started...
Competitor Agent started...

Financial Agent started...
```

Both independent tasks execute concurrently. Financial Analysis waits
for both results.

**Important:** This is still a simplified orchestration simulation.
Actual LLM-powered agents would have their own prompts, tools, model
calls, and structured outputs.

## 7. Dynamic Delegation

So far, we manually selected which agent to call:

``` python
research = market_research_agent(task)
```

But imagine users can make different requests:

-   Research the EV market.
-   Analyze company finances.
-   Compare smartphone competitors.

We do not want to hardcode a separate workflow for every possible
request.

We need **dynamic delegation**: the supervisor decides which agent is
relevant.

### Simple routing by agent name

``` python
AGENTS = {
    "research": market_research_agent,
    "competitor": competitor_agent,
}


def delegate(task, agent_name):
    agent = AGENTS.get(agent_name)

    if agent is None:
        raise ValueError("Unknown agent")

    return agent(task)
```

Usage:

``` python
result = delegate(
    "Research Indian EV market",
    "research"
)
```

This demonstrates routing by agent name.

In a real system, an LLM-powered supervisor can select an agent based on
the user's request. However, the backend must validate that the selected
agent is authorized and available.

## 8. Important Production Concepts

  Concept             Why it matters
  ------------------- ------------------------------------------------------
  Task Queue          Manages pending agent tasks
  Dependency Graph    Tracks which task waits for another
  Timeout             Prevents agents from running indefinitely
  Retry               Recovers from temporary failures
  Result Validation   Ensures outputs meet expected schemas
  Task Status         Tracks pending, running, completed, and failed tasks
  Idempotency         Avoids duplicate side effects
  Cancellation        Stops unnecessary downstream work

### Dependency-aware failure handling

Suppose Market Research fails. Should Financial Analysis still run?

Usually not, because it depends on the Market Research result.

But an independent Competitor Analysis task could still finish.

A good orchestrator understands these dependencies rather than blindly
executing every agent.

## 9. Connection with LangGraph

The concepts we studied map to LangGraph terminology:

  What we learned                       LangGraph concept
  ------------------------------------- ---------------------
  Shared workflow data                  State
  Individual agent or processing step   Node
  Execution path                        Edge
  Dynamic routing                       Conditional Edge
  Workflow execution structure          Graph
  Persistent execution state            Checkpointer
  Task coordination                     Graph orchestration

This is why it is useful to understand the underlying concepts before
using LangGraph. Otherwise, you might learn how to write `add_node()`
and `add_edge()` without understanding what those operations represent.

## 10. Interview Questions

Make sure you can answer:

1.  What is the difference between orchestration and delegation?
2.  What is task decomposition?
3.  What is a DAG, and why is it useful?
4.  What is the difference between sequential and parallel execution?
5.  How does a supervisor dynamically delegate tasks?
6.  What happens if one agent fails in a parallel workflow?
7.  Why do we need dependency tracking?
8.  How do you prevent duplicate execution of a delegated task?

## 11. Quick Revision

-   **Orchestration:** Manages the overall workflow.
-   **Delegation:** Assigns a task to an agent.
-   **Coordination:** Synchronizes work between agents.
-   **Task decomposition:** Breaks a complex task into smaller tasks.
-   **DAG:** Represents tasks and their dependencies.
-   **Sequential orchestration:** Executes tasks in a fixed order.
-   **Parallel orchestration:** Runs independent tasks concurrently.
-   **Conditional orchestration:** Chooses the next task based on a
    result.
-   **Dynamic delegation:** Selects an agent based on task context.
-   **Production orchestration:** Also needs timeouts, retries,
    validation, task status, idempotency, and cancellation.

**Core takeaway:** A good orchestrator does more than call agents. It
understands task dependencies, delegates work to the right agents,
coordinates execution, and handles failures without blindly continuing
the workflow.
