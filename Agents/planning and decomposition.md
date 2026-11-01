# Module 4: Planning & Task Decomposition in AI Agents

> **Core agent engineering concept**

So far, we've learned that an agent can reason, call tools, and observe
results.

But what happens when a user gives a complex task that requires ten
different actions?

The agent needs a plan.

------------------------------------------------------------------------

## 1. What Is Planning?

**Planning** is the process through which an AI agent converts a
high-level goal into smaller, executable tasks and determines how to
complete them.

### Example: Preparing an Investment Report

A user says:

> Research a company, analyse its financial performance, and prepare an
> investment report.

An agent should not treat this as one simple action. It can decompose
the goal into smaller tasks:

``` text
              High-Level Goal
       Prepare an investment report
                    |
                    v
              Task Decomposition
                    |
       +------------+------------+
       |            |            |
       v            v            v
  Research       Collect       Analyse
  company      financial data  performance
       |            |            |
       +------------+------------+
                    |
                    v
             Prepare Report
                    |
                    v
               Final Output
```

This process is called **Task Decomposition**.

Breaking a complex objective into smaller tasks makes execution easier
to manage, validate, retry, and track.

------------------------------------------------------------------------

## 2. Different Planning Strategies

There isn't just one way to plan a task.

### A. Sequential Planning

Tasks execute one after another.

``` text
       Get User Details
              |
              v
        Verify Identity
              |
              v
      Check Account Balance
              |
              v
      Process Transaction
              |
              v
       Return Confirmation
```

**Use it when:** One task depends on the result of the previous task.

For example, you should not process a transaction before verifying the
user and checking the required conditions.

### B. Parallel Planning

Independent tasks execute simultaneously.

``` text
             User Request
                  |
          +-------+-------+
          |       |       |
          v       v       v
       Weather  News   Stock Data
          |       |       |
          +-------+-------+
                  |
                  v
            Final Summary
```

**Why is this useful?**

Suppose three API calls take:

-   Weather: 2 seconds
-   News: 3 seconds
-   Stock data: 4 seconds

Sequential execution takes approximately:

\[ 2 + 3 + 4 = 9 `\text{ seconds}`{=tex} \]

Parallel execution takes approximately:

\[ `\max`{=tex}(2, 3, 4) = 4 `\text{ seconds}`{=tex} \]

These are illustrative estimates, excluding orchestration overhead and
other delays.

**Use it when:** Tasks are independent and can safely execute at the
same time.

### C. Hierarchical Planning

A complex goal is broken into smaller goals, which are further divided
into executable tasks.

``` text
          Build an E-commerce Application
                       |
                +------+------+
                |             |
             Backend        Frontend
                |             |
             +--+--+       +--+--+
             |     |       |     |
            Auth  Orders   UI   Cart
             |     |       |     |
           Tasks Tasks   Tasks Tasks
```

**Use it when:** The problem is too complex to solve as a single flat
sequence.

Hierarchical planning helps organize large tasks into manageable
subgoals and workstreams.

### D. Dynamic Planning

The agent modifies its plan based on new observations.

Example:

1.  Agent searches for a hotel.
2.  The hotel is unavailable.
3.  Agent observes the failure.
4.  It searches for alternatives.
5.  It compares the alternatives.
6.  It updates the plan based on the available options.

**Use it when:** The environment is unpredictable and new information
can change the best execution strategy.

------------------------------------------------------------------------

## 3. Planning vs. ReAct

This is an important interview distinction.

  -----------------------------------------------------------------------
  Dimension               ReAct                   Planning
  ----------------------- ----------------------- -----------------------
  Main idea               Think → Act → Observe   Create a task execution
                                                  strategy

  Focus                   Selecting the next      Organizing multiple
                          action                  tasks toward a goal

  Execution               Often decides one       Can create a multi-step
                          action at a time        plan upfront

  Nature                  Reactive                Goal-oriented and
                                                  potentially
                                                  anticipatory

  Adaptation              Uses observations to    Can revise the plan
                          decide what happens     when new observations
                          next                    arrive
  -----------------------------------------------------------------------

### How Do They Work Together?

A production agent can combine both approaches:

-   **Planning** decides the overall strategy.
-   **ReAct** executes individual steps using tools and observations.
-   **Replanning** updates the strategy when an unexpected result
    changes what should happen next.

For example, planning might decide to research a company's financial
performance, competitors, and market. ReAct can execute each research
step, observe the results, and request additional information when
necessary.

------------------------------------------------------------------------

## 4. How Do Agents Actually Create Plans?

Let's understand a simplified implementation.

Suppose the objective is:

``` text
Prepare a market research report.
```

The LLM might generate a structured plan:

``` json
{
  "goal": "Prepare market research report",
  "tasks": [
    {
      "id": 1,
      "task": "Research competitors",
      "depends_on": []
    },
    {
      "id": 2,
      "task": "Research market size",
      "depends_on": []
    },
    {
      "id": 3,
      "task": "Compare competitors",
      "depends_on": [1]
    },
    {
      "id": 4,
      "task": "Generate report",
      "depends_on": [2, 3]
    }
  ]
}
```

### Understanding `depends_on`

The `depends_on` field defines task dependencies.

-   Task 1 and Task 2 have no dependencies, so they can run
    simultaneously.
-   Task 3 depends on Task 1, so it must wait for Task 1.
-   Task 4 depends on Tasks 2 and 3, so both must finish before it can
    run.

This is a representation of a **Directed Acyclic Graph (DAG)**.

------------------------------------------------------------------------

## 5. Understanding DAGs in Agent Planning

A **Directed Acyclic Graph (DAG)** is a directed graph that contains no
directed cycles.

It consists of:

-   **Nodes:** Individual tasks.
-   **Directed edges:** Dependencies between tasks.
-   **Acyclic structure:** Following directed edges can never lead back
    to the same node.

### Task Dependency Graph

``` text
   Task 1                         Task 2
Competitor                     Research market
 research                          size
     |                               |
     v                               |
   Task 3                            |
Compare competitors                  |
     |                               |
     +---------------+---------------+
                     |
                     v
                   Task 4
               Generate report
```

### Why Are DAGs Useful?

They help you:

1.  Execute independent tasks concurrently.
2.  Understand task dependencies.
3.  Detect circular dependencies.
4.  Recover from failed tasks.
5.  Track execution progress.
6.  Determine which tasks are ready to execute.

### Real-World Applications

DAGs are also used in: - Workflow orchestration systems. - Distributed
computing. - Data engineering pipelines. - Build systems. - Dependency
management.

The same dependency model is useful when an AI agent needs to coordinate
multiple tasks.

------------------------------------------------------------------------

## 6. Implementing a Simple Task Planner in Python

Let's create a basic dependency-aware execution structure.

### Step 1 --- Define the Tasks

``` python
tasks = {
    "research_competitors": [],
    "research_market": [],

    "compare_competitors": [
        "research_competitors"
    ],

    "generate_report": [
        "research_market",
        "compare_competitors"
    ]
}
```

Each dictionary key represents a task. Its value contains the tasks that
must be completed first.

### Step 2 --- Find Ready Tasks

``` python
def get_ready_tasks(completed):
    ready = []

    for task, dependencies in tasks.items():
        if task in completed:
            continue

        if all(dep in completed for dep in dependencies):
            ready.append(task)

    return ready
```

### Step 3 --- Check the Initial Tasks

``` python
completed = set()

print(get_ready_tasks(completed))
```

Output:

``` python
[
    "research_competitors",
    "research_market"
]
```

Both tasks are ready because neither has dependencies.

### Step 4 --- Update the Completed Tasks

Suppose both research tasks have finished:

``` python
completed = {
    "research_competitors",
    "research_market"
}

print(get_ready_tasks(completed))
```

Output:

``` python
[
    "compare_competitors"
]
```

The comparison task is now ready because its dependency has completed.

After `compare_competitors` finishes, `generate_report` becomes ready.

### What Does This Implementation Teach Us?

It demonstrates the core idea of dependency-aware scheduling:

-   Identify tasks whose dependencies are complete.
-   Execute those tasks.
-   Update the completed-task set.
-   Identify the next set of ready tasks.

**Limitation:** This is a simplified scheduler, not a complete
production task planner. It does not execute tasks, manage concurrency,
persist progress, handle failures, or detect cycles.

------------------------------------------------------------------------

## 7. Important Planning Problems

As an AI engineer, you need to understand these failure scenarios.

  -----------------------------------------------------------------------
  Problem                             Possible Solution
  ----------------------------------- -----------------------------------
  Bad task decomposition              Validate the generated plan and
                                      check task completeness

  Circular dependencies               Perform DAG cycle detection

  Repeated tasks                      Use unique task IDs and
                                      deduplication

  Failed task                         Apply controlled retries or replan

  Infinite planning                   Set maximum planning iterations and
                                      execution budgets

  Context overflow                    Summarize and persist relevant
                                      state

  Unnecessary tasks                   Apply relevance checks and
                                      execution budgets

  Missing dependencies                Validate that every referenced
                                      dependency exists

  Invalid execution order             Use topological sorting or
                                      dependency-aware scheduling
  -----------------------------------------------------------------------

### Why Plan Validation Matters

Never blindly trust an LLM-generated plan.

Before executing it, your application should check:

-   Every task has a valid and unique ID.
-   Every dependency references an existing task.
-   The graph contains no cycles.
-   The plan contains enough information to execute each task.
-   The requested operations are permitted.
-   The plan fits within time, token, and execution budgets.

A valid DAG does not automatically mean a good plan. You must also
validate whether the tasks actually achieve the user's objective.

------------------------------------------------------------------------

## 8. Key Takeaways

-   Planning converts high-level goals into smaller executable tasks.
-   Task decomposition makes complex objectives manageable.
-   Sequential planning handles dependent operations.
-   Parallel planning improves efficiency for independent operations.
-   Hierarchical planning organizes complex goals into subgoals.
-   Dynamic planning allows the agent to adapt to new observations.
-   DAGs represent task dependencies and help determine execution order.
-   Planning and ReAct can work together.
-   LLM-generated plans must be validated before execution.

------------------------------------------------------------------------

## 9. Interview Questions

### Q1. What is task decomposition?

Task decomposition is the process of breaking a high-level objective
into smaller tasks that can be executed, monitored, and validated
independently or in coordination.

### Q2. What is the difference between sequential and parallel planning?

Sequential planning executes tasks in an order where later tasks may
depend on earlier results. Parallel planning executes independent tasks
concurrently to reduce total execution time.

### Q3. What is hierarchical planning?

Hierarchical planning breaks a complex goal into subgoals and further
divides those subgoals into smaller executable tasks.

### Q4. What is dynamic planning?

Dynamic planning allows an agent to revise its execution strategy when
new information, unexpected results, or failures change what should
happen next.

### Q5. What is a DAG and why is it useful?

A Directed Acyclic Graph represents tasks as nodes and dependencies as
directed edges, without cycles. It helps determine execution order,
identify parallel tasks, and track dependencies.

### Q6. How can you detect circular dependencies?

Use a graph cycle-detection algorithm, such as depth-first search with
visiting states, or use topological sorting. If topological sorting
cannot process every node, the graph contains a cycle.

### Q7. How does planning work with ReAct?

Planning creates the overall strategy. ReAct executes individual actions
and observes results. If an observation invalidates the current
strategy, the agent can replan.

### Q8. Why should an LLM-generated plan be validated?

The model may generate missing dependencies, duplicate tasks, invalid
actions, or circular dependencies. Backend validation prevents an
invalid or unsafe plan from being executed.

------------------------------------------------------------------------

## 10. Quick Revision

  Term                    Remember
  ----------------------- ----------------------------------------------------
  Planning                Creating an execution strategy for a goal
  Task decomposition      Breaking a goal into smaller tasks
  Sequential planning     Execute dependent tasks in order
  Parallel planning       Execute independent tasks concurrently
  Hierarchical planning   Break goals into subgoals and tasks
  Dynamic planning        Revise the plan based on observations
  DAG                     Directed graph with no cycles
  Dependency              A task that must finish before another can proceed
  Scheduler               Determines which tasks are ready to execute
  Replanning              Updating the strategy when circumstances change

**Core concept to remember:**

``` text
High-Level Goal
       |
       v
Task Decomposition
       |
       v
Dependency Graph (DAG)
       |
       v
Validate Plan
       |
       v
Schedule Ready Tasks
       |
       v
Execute + Observe
       |
       v
Complete or Replan
```

**Interview one-liner:** Planning enables an AI agent to transform a
complex goal into a dependency-aware execution strategy, while
scheduling determines which tasks can safely run and when.
