# Topic 1 --- Why Agent Frameworks Exist

## 1. The Problem with Building Agents from Scratch

Imagine you are building an AI customer support agent.

You may need to implement:

1.  LLM API integration.
2.  Prompt management.
3.  Tool definitions.
4.  Tool calling and execution.
5.  Conversation history.
6.  State management.
7.  Retry and error handling.
8.  Conditional routing.
9.  Workflow persistence.
10. Human approval.

If you implement all of these from scratch in every project, development
becomes slower.

For example, without a framework, you may need to write your own agent
loop:

``` python
while True:
    response = call_llm(messages, tools)

    if response.has_tool_call:
        tool_result = execute_tool(
            response.tool_call
        )
        messages.append(tool_result)
    else:
        print(response.text)
        break
```

This approach is not wrong. In fact, building an agent loop yourself is
an excellent way to learn the fundamentals.

The problem appears when the application becomes more complex:

-   Multiple tools
-   Multiple agents
-   Conditional execution
-   Long-running workflows
-   Persistent state
-   Retries and recovery
-   Human approval

This is where agent frameworks become useful.

------------------------------------------------------------------------

## 2. What Is an Agent Framework?

An **agent framework** is a software library that provides reusable
abstractions for building, orchestrating, and managing AI-powered
applications.

In simple terms:

**You do not have to implement every common building block manually. A
framework provides reusable components and abstractions.**

  Without a framework              With a framework
  -------------------------------- ----------------------------
  Manually manage prompts          Prompt templates
  Manually integrate models        Model integrations
  Manually define tool schemas     Tool abstractions
  Manually build workflows         Graphs and chains
  Manually manage state            State abstractions
  Manually implement persistence   Checkpointing integrations

Remember: using a framework does not automatically guarantee
reliability. Business rules, security, validation, and testing are still
your responsibility.

------------------------------------------------------------------------

## 3. The Three Approaches You Must Understand

### A. Build from Scratch

Use Python, APIs, asynchronous programming, and custom orchestration to
build your own agent system.

-   **Advantage:** Maximum control.
-   **Best when:** You need custom behavior, lightweight systems, or a
    deep understanding of the underlying mechanics.

### B. LangChain

Provides abstractions for models, prompts, tools, structured outputs,
and integrations.

-   **Focus:** LLM application development.
-   **Useful when:** Connecting models with tools and external data.

### C. LangGraph

Provides graph-based orchestration with state, nodes, edges, cycles,
persistence, and human-in-the-loop capabilities.

-   **Focus:** Complex agent workflows.
-   **Useful when:** Building multi-step, stateful, and controllable
    agent systems.

------------------------------------------------------------------------

## 4. LangChain vs LangGraph --- Understand the Difference

This is one of the most important distinctions in this module.

Imagine a customer support workflow.

User asks:

> Where is my order?

### Using LangChain

-   Define the model.
-   Give it a prompt.
-   Connect tools.
-   Let it retrieve order details.
-   Generate a response.

### Using LangGraph

-   Create workflow state.
-   Define an agent node.
-   Define a tool-execution node.
-   Add conditional routing.
-   Add retry or validation nodes.
-   Save workflow checkpoints.
-   Resume interrupted workflows.

### Visual comparison

**LangChain-style flow**

``` text
Prompt
  |
  v
LLM
  |
  v
Tools
  |
  v
Response
```

**LangGraph-style workflow**

``` text
Agent Node
    |
    v
Tool Node
    |
    v
Validation Node
    |
    +---- Can branch, loop, and resume
```

Technically, LangChain also supports more complex execution patterns,
and LangGraph can use LangChain components. They are not competing
products that you must choose between.

A useful mental model:

-   **LangChain =** Components and integrations for LLM applications.
-   **LangGraph =** Explicit control over stateful agent workflows.

------------------------------------------------------------------------

## 5. Understand with a Small Example

Suppose we want to create a customer support workflow.

Without a framework, you can manually control the behavior:

``` python
def customer_support_agent(user_message):
    order = get_order_status(user_message)

    if order["status"] == "delayed":
        ticket = create_support_ticket(order["id"])

        return {
            "message": "Your order is delayed.",
            "ticket": ticket
        }

    return {
        "message": "Your order is on track."
    }
```

This is deterministic code, not a complete LLM agent.

Now imagine customers can ask:

-   Where is my order?
-   Can I cancel it?
-   Why is my refund delayed?
-   Can I raise a complaint?

The number of possible workflows increases.

You may now need:

-   Intent understanding.
-   Tool selection.
-   State management.
-   Conditional routing.
-   Error handling.

This is where LangChain and LangGraph become useful.

------------------------------------------------------------------------

## 6. Which One Should You Choose?

  Requirement                              Recommended approach
  ---------------------------------------- ---------------------------
  Simple API-based AI application          Direct model SDK
  Custom lightweight agent                 Build from scratch
  LLM + tools + integrations               LangChain
  Stateful multi-step agent                LangGraph
  Human approval and resumable workflows   LangGraph
  Complex custom business logic            Framework + custom Python

### Recommendation

Do not become dependent on a framework. You should be able to explain
what happens underneath it.

For a customer support agent:

-   A **direct SDK implementation** is excellent for understanding tool
    calling.
-   **LangGraph** becomes useful when you introduce more complex
    routing, retries, approval, and persistence.

------------------------------------------------------------------------

## Quick Revision

  -----------------------------------------------------------------------
  Approach                            Main purpose
  ----------------------------------- -----------------------------------
  Build from scratch                  Maximum control and understanding
                                      of the fundamentals

  LangChain                           Reusable components and
                                      integrations for LLM applications

  LangGraph                           Explicit orchestration of stateful,
                                      multi-step workflows
  -----------------------------------------------------------------------

**Engineering takeaway:** Frameworks reduce the amount of infrastructure
you need to write repeatedly, but they do not remove your responsibility
for architecture, business rules, security, validation, and testing.
Learn the underlying agent loop first; adopt abstractions when
complexity justifies them.
