# AI Agents --- Module 1: Foundations

## 1. What Exactly Is an AI Agent?

An **AI Agent** is a system that uses an AI model to understand a goal,
decide what action to take, execute that action using available tools,
observe the result, and continue until the goal is achieved or it needs
to stop.

### Example: Finding a Flight

Suppose you ask:

> Find the cheapest flight from Delhi to Bangalore next Friday and
> summarize the options.

A normal LLM: - Generates an answer based on patterns and information
learned during training. - Cannot reliably check live flight prices
unless it has access to an external data source or tool.

An AI Agent: 1. Understands the objective. 2. Identifies that live
flight information is required. 3. Calls a flight-search tool. 4.
Observes the returned results. 5. Compares prices and other relevant
details. 6. Calls another tool if additional information is needed. 7.
Produces a final response.

### The Agent Loop

``` text
             User Goal
                 |
                 v
          LLM: Reason & Decide
                 |
                 v
        Select and Execute Tool
                 |
                 v
          Observe Tool Result
                 |
                 v
          Continue or Finish?
             /         \
          Continue     Finish
             |            |
             v            v
        Repeat Loop   Final Response
```

The key idea is that an agent can use the result of one action to decide
what to do next.

------------------------------------------------------------------------

## 2. AI Agent vs. LLM vs. Chatbot vs. Workflow

This distinction is important in interviews and when designing
AI-powered systems.

  -----------------------------------------------------------------------
  Concept                 What it does            Example: Customer
                                                  Support Refund
  ----------------------- ----------------------- -----------------------
  **LLM**                 Understands and         Explains the refund
                          generates language.     policy.

  **Chatbot**             Provides a              Asks for the order ID
                          conversational          and answers questions.
                          interface.              

  **Workflow**            Executes predefined     Verifies the order →
                          steps in a fixed or     checks eligibility →
                          configured sequence.    processes the refund.

  **AI Agent**            Dynamically chooses     Decides whether it
                          actions based on        needs an order lookup,
                          context and tool        policy lookup, more
                          results.                information, or
                                                  escalation.
  -----------------------------------------------------------------------

### Important Nuance

An agent can operate inside a workflow. These concepts are not mutually
exclusive.

A workflow is generally more predictable because its steps are defined
in advance. An agent has more flexibility because it can choose among
available actions at runtime.

**Do not use an agent when a deterministic workflow is sufficient.**
Extra autonomy can introduce latency, cost, unpredictability, and
additional failure modes.

------------------------------------------------------------------------

## 3. The Five Fundamental Components of an AI Agent

An agent commonly contains five core components:

### 1. Model

The LLM responsible for interpreting context, reasoning about the task,
and deciding what to do next.

Examples: GPT models, Claude models, and Gemini models.

### 2. Instructions

System-level instructions that define the agent's: - Role and
objective - Expected behavior - Constraints and safety rules - Tool-use
guidelines - Output format

### 3. Tools

External capabilities the model can request through the application.

Examples: - REST API calls - Database queries - Web search - File
operations - Code execution - Email or calendar operations

A tool gives the agent a way to interact with systems beyond the model's
own generated text.

### 4. State / Memory

Information retained so the agent can work with relevant context.

-   **State** usually refers to information maintained during a task or
    conversation, such as the current goal, tool results, and progress.
-   **Memory** often refers to information retained beyond the current
    step or session, when the application is designed to persist it.

State and memory are related, but they are not identical.

### 5. Control Loop

The logic that determines what happens after each model response.

It typically: 1. Sends the current context to the model. 2. Checks
whether the model requested a tool or produced a final answer. 3.
Validates and executes any requested tool. 4. Adds the tool result to
the conversation or state. 5. Repeats until the task is complete or a
stopping condition is reached.

------------------------------------------------------------------------

## 4. A Simple Agent Implementation

Before using frameworks such as LangGraph or an agent SDK, understand
the underlying control flow.

The following is **conceptual Python pseudocode**, not a complete
runnable implementation:

``` python
def agent(user_goal):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful agent."
        },
        {
            "role": "user",
            "content": user_goal
        }
    ]

    while True:
        response = llm.generate(messages)

        if response.tool_call:
            # The application receives the requested tool call.
            tool_name = response.tool_call.name
            tool_arguments = response.tool_call.arguments

            # Validate and execute the requested tool.
            result = execute_tool(
                tool_name,
                tool_arguments
            )

            # Add the model's tool call and the tool result
            # to the conversation so the model can continue.
            messages.append(response)
            messages.append({
                "role": "tool",
                "content": str(result)
            })

        else:
            # No tool call: return the model's final response.
            return response.content
```

### What Is Happening Here?

1.  The application creates an initial conversation containing the
    system instructions and user goal.
2.  The model receives the conversation and decides whether it needs a
    tool.
3.  If a tool is requested, the application reads the tool name and
    arguments.
4.  The application validates the request and executes the corresponding
    function.
5.  The tool result is added to the conversation.
6.  The model receives the updated context and decides what to do next.
7.  If no further tool is needed, the application returns the final
    response.

### A Critical Engineering Detail

**The LLM does not directly execute the tool.**

The application is responsible for: - Receiving the model's tool-call
request. - Checking that the requested tool exists. - Validating the
arguments and permissions. - Executing the corresponding function. -
Handling errors and timeouts. - Returning the result to the model.

This separation matters because model output should not be treated as
trusted executable code.

A production implementation should also include: - A maximum number of
tool calls or loop iterations. - Tool argument validation. -
Authentication and authorization checks. - Timeouts and error
handling. - Logging and observability. - Human approval for sensitive
actions when appropriate.

------------------------------------------------------------------------

## 5. Key Takeaways

-   An LLM generates language; an agent uses a model as part of a larger
    action-taking system.
-   The agent loop is commonly described as **reason → act → observe →
    repeat**.
-   Tools let an agent interact with external systems.
-   The application, not the LLM, executes and controls tool calls.
-   State helps an agent track progress and context.
-   Workflows are often preferable when the process is known and
    deterministic.
-   More autonomy is not automatically better; it should solve a real
    problem.

------------------------------------------------------------------------

## 6. Interview Questions

### Q1. What is an AI Agent?

An AI Agent is a system that uses an AI model to interpret a goal,
choose actions, interact with tools, observe results, and continue until
it completes the task or reaches a stopping condition.

### Q2. What is the difference between an LLM and an AI Agent?

An LLM is a model that processes and generates content. An AI Agent is a
larger system that uses an LLM together with instructions, tools, state,
and a control loop to take actions toward a goal.

### Q3. Does an LLM execute tools directly?

No. The model produces a structured tool-call request. The application
validates the request, executes the corresponding function, and sends
the result back to the model.

### Q4. What is the agent loop?

It is the repeated process of reasoning, selecting and executing an
action, observing its result, and deciding whether to continue or
finish.

### Q5. Should every AI application be an agent?

No. If a fixed workflow or a direct LLM call can solve the problem
reliably, it may be simpler, cheaper, faster, and easier to test than an
autonomous agent.

------------------------------------------------------------------------

## 7. Quick Revision

  -----------------------------------------------------------------------
  Term                                Remember
  ----------------------------------- -----------------------------------
  LLM                                 The language model that interprets
                                      and generates content

  Agent                               A system that uses a model to
                                      pursue a goal through actions

  Tool                                An external function or capability
                                      available to the agent

  State                               Information maintained about the
                                      current task or interaction

  Memory                              Information retained for later use

  Control loop                        Logic that manages model calls,
                                      tool execution, and stopping
  -----------------------------------------------------------------------

**Core formula to remember:**

``` text
AI Agent = Model + Instructions + Tools + State/Memory + Control Loop
```
