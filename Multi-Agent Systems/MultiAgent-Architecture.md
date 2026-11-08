# Multi-Agent Architectures & Design Patterns

## 1. Why Do We Need Different Architectures?

Imagine building an AI-powered software development system.

A user asks:

> Build a REST API for managing student records.

The task includes several responsibilities:

-   Requirement analysis
-   Backend code generation
-   Code review
-   Testing
-   Final report

When multiple agents are involved, we need to decide:

-   Which agent executes?
-   In what order do agents execute?
-   How do agents communicate?
-   Who coordinates the overall task?
-   What happens when an agent needs another agent's help?

These decisions are part of **agent architecture and design patterns**.

This topic covers five major patterns.

## 2. Sequential Architecture (Pipeline)

In a sequential architecture, agents execute in a fixed sequence. Each
agent receives the previous agent's output.

### Architecture

``` text
Requirement Agent
       |
       v
Developer Agent
       |
       v
Code Reviewer
       |
       v
Testing Agent
       |
       v
Final Result
```

### Code example

``` python
def requirement_agent(task):
    return {
        "requirements": [
            "Create student API",
            "Add student records",
            "Retrieve student records"
        ]
    }


def developer_agent(requirements):
    return {
        "code": "Student API implementation",
        "requirements": requirements
    }


def reviewer_agent(code):
    return {
        "review": "Code structure looks acceptable",
        "code": code
    }


def testing_agent(review):
    return {
        "test_status": "passed",
        "review": review
    }


def run_pipeline(task):
    requirements = requirement_agent(task)
    code = developer_agent(requirements)
    review = reviewer_agent(code)
    tests = testing_agent(review)

    return tests
```

### When to use

-   Document processing.
-   Content generation.
-   Code generation followed by review.
-   Data processing pipelines.

### Limitation

If one stage fails, downstream stages may be blocked. This simple
pipeline also does not support dynamic delegation.

## 3. Supervisor Architecture

This is an important pattern in multi-agent systems.

A central **Supervisor Agent** decides:

-   Which agent should execute?
-   Who should receive a task?
-   In what order should agents execute?
-   Is the task complete?
-   Should an agent be executed again?

### Architecture

``` text
                 Supervisor Agent
                Central decision maker
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
         Research    Developer     Testing
          Agent       Agent         Agent
             |           |           |
             +-----------+-----------+
                         |
                  Results returned
                   to supervisor
```

Unlike a fixed sequential architecture, a supervisor can dynamically
choose the next agent.

### Code example

``` python
def research_agent(task):
    return "Requirements researched"


def developer_agent(task):
    return "Code generated"


def testing_agent(task):
    return "Tests passed"


AGENTS = {
    "research": research_agent,
    "developer": developer_agent,
    "testing": testing_agent
}


def supervisor(task):
    result = {}

    result["research"] = AGENTS["research"](task)

    result["developer"] = AGENTS["developer"](
        result["research"]
    )

    result["testing"] = AGENTS["testing"](
        result["developer"]
    )

    return result
```

**Important:** This is still a simplified supervisor with fixed routing.
A real LLM-powered supervisor selects agents dynamically based on task
context.

### When to use

-   Complex tasks requiring multiple specialized agents.
-   Dynamic task delegation.
-   Systems where one component must maintain overall control.
-   Enterprise workflows.

## 4. Network / Decentralized Architecture

In this architecture, agents can communicate directly with one another.

A single central supervisor is not necessarily required.

### Example architecture

``` text
     Agent A: Research
        /          \
       v            v
Agent B: Analysis  Agent C: Validation
       \            /
        v          v
        Agent D: Execution
```

Agents can communicate with other authorized agents according to defined
routing rules.

Example interaction:

1.  Research Agent finds a problem.
2.  It sends the information to Analysis Agent.
3.  Analysis Agent asks Validation Agent to verify it.
4.  Validation Agent sends feedback to Research Agent.

This allows more flexible coordination.

### When to use

-   Collaborative research.
-   Systems where agents need to negotiate or exchange information.
-   Distributed decision-making.

### Limitation

Coordination, debugging, and loop control become harder. Communication
permissions and termination conditions are essential.

## 5. Hierarchical Architecture

Think of a large company:

``` text
CEO
 |
 +-- Department Heads
       |
       +-- Team Leads
              |
              +-- Employees
```

Similarly, agents can be organized into multiple levels.

### Example architecture

``` text
                 Main Supervisor
                  /           \
                 v             v
         Research Manager  Development Manager
             /      \          /       \
            v        v        v         v
        Research  Research  Coding    Testing
         Agent A   Agent B   Agent    Agent
```

The main supervisor delegates work to managers. Managers further
delegate to specialized agents.

### When to use

-   Large-scale research systems.
-   Complex enterprise automation.
-   Large tasks that can be decomposed into subprojects.

### Limitation

More layers mean more communication overhead, latency, and potential
failure points.

## 6. Handoff Architecture

Handoff is different from the supervisor pattern.

An agent can transfer control to another specialized agent when it
determines that the other agent is better suited to handle the request.

### Example: Customer support system

``` text
                 Customer
                    |
                    v
                Triage Agent
                    |
          +---------+----------+
          |         |          |
          v         v          v
       Billing  Technical    Refund
        Agent     Agent       Agent
```

Examples:

-   Billing issue → Billing Agent.
-   Technical issue → Technical Agent.
-   Refund request → Refund Agent.

The receiving agent takes responsibility for the next stage.

**Important distinction:** A handoff transfers control. It does not
necessarily mean that both agents are working simultaneously.

## 7. Architecture Comparison

  Pattern        Control              Best suited for
  -------------- -------------------- ---------------------
  Sequential     Fixed sequence       Pipelines
  Supervisor     Central controller   Dynamic delegation
  Network        Distributed          Collaboration
  Hierarchical   Multiple levels      Large tasks
  Handoff        Control transfer     Specialized routing

### Advanced concept

These patterns are not mutually exclusive. A real system can combine
supervisor, hierarchical, and parallel execution patterns.

## 8. Connect This to Our Customer Support Agent

Remember the original single-agent architecture:

``` text
Customer
   |
   v
Single AI Agent
   |
   +---- get_order_status()
   |
   +---- create_support_ticket()
   |
   v
Backend + PostgreSQL
```

We could expand it into a multi-agent system:

``` text
                  Customer
                     |
                     v
               Supervisor Agent
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
  Triage Agent   Order Agent  Billing Agent
                     |
                     v
                Refund Agent
                     |
                     v
                Final Response
```

However, do not introduce multiple agents just for the sake of adding
agents. The original two-tool customer support system is better as a
single agent.

Multi-agent architecture becomes justified when responsibilities and
workflows become sufficiently complex.

## 9. Quick Revision

-   **Sequential:** Agents execute in a predefined order; each stage
    receives the previous stage's output.
-   **Supervisor:** A central agent coordinates work and chooses which
    agent should execute.
-   **Network:** Agents communicate directly according to defined
    routing rules; a central supervisor is not necessarily required.
-   **Hierarchical:** A main supervisor delegates to managers, who
    delegate to specialized agents.
-   **Handoff:** One agent transfers control to another specialized
    agent.
-   These patterns can be combined in one system.
-   More agents and more coordination layers introduce additional
    latency, cost, complexity, and failure points.

**Core takeaway:** Architecture determines how agents are organized, how
control flows, and how they coordinate. Choose the simplest architecture
that reliably handles the task.
