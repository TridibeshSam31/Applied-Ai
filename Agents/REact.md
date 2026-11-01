# Module 2: ReAct --- Reasoning + Acting

> **Core agent architecture**

## 1. What Is ReAct?

**ReAct** stands for **Reasoning and Acting**.

It is an approach in which an LLM alternates between: - Reasoning about
what it should do. - Taking an action using a tool. - Observing the
result. - Deciding what to do next.

Instead of generating an entire answer immediately, the model works
iteratively. Each new action can depend on the result of the previous
action.

### Example: Comparing City Populations

A user asks:

> Find the population of Delhi and calculate how many times larger it is
> than Jaipur.

The agent might perform the following steps:

1.  **Thought:** Determine what information is required. It needs
    population figures for both cities.
2.  **Action:** Search for Delhi's population using
    `search_population("Delhi")`.
3.  **Observation:** Receive a result: Delhi population = 16.8 million
    (illustrative figure).
4.  **Thought:** Recognize that Jaipur's population is still needed.
5.  **Action:** Search for Jaipur's population using
    `search_population("Jaipur")`.
6.  **Observation:** Receive a result: Jaipur population = 3.1 million
    (illustrative figure).
7.  **Final answer:** Calculate the ratio.

\[ `\frac{16.8}{3.1}`{=tex} `\approx 5.42`{=tex} \]

Delhi has approximately 5.42 times the population of Jaipur, based on
these illustrative figures.

> **Note:** The population figures above are illustrative, not a current
> or authoritative population comparison.

------------------------------------------------------------------------

## 2. The ReAct Execution Cycle

The general pattern is:

``` text
             User Input
                 |
                 v
           LLM Reasoning
                 |
                 v
            Select Action
                 |
                 v
            Execute Tool
                 |
                 v
           Observe Result
                 |
                 v
           Update Context
                 |
                 v
        LLM Reasoning Again
             /       \
      Another Action  Final Answer
             |
             +----> Execute Tool Again
```

### The Critical Idea

**The next action depends on the previous observation.**

For example, an agent searching for a flight might: - Search for
available flights. - Observe that all results exceed the user's
budget. - Decide to search nearby airports or different departure
times. - Observe the new results. - Present the best available options.

This makes execution dynamic rather than completely predefined.

------------------------------------------------------------------------

## 3. How Does ReAct Work Internally?

Consider an agent that has access to a weather-search tool.

The application provides the model with:

-   The user's request.
-   Available tool descriptions.
-   Tool parameter schemas.
-   Conversation context.

The model decides whether it can answer directly or needs to request a
tool call.

### Step 1: The Model Requests a Tool

A simplified representation of a tool-call request might look like:

``` json
{
  "tool_calls": [
    {
      "name": "get_weather",
      "arguments": {
        "city": "Delhi"
      }
    }
  ]
}
```

This is a conceptual representation of structured tool calling. Actual
response formats depend on the model API.

### Step 2: The Application Executes the Tool

``` python
def get_weather(city: str):
    return {
        "city": city,
        "temperature": 28,
        "condition": "Sunny"
    }
```

The application: 1. Receives the requested tool name and arguments. 2.
Checks whether the tool is allowed. 3. Validates the arguments. 4.
Executes the corresponding Python function. 5. Captures the result or
error.

### Step 3: The Result Is Sent Back to the Model

The application adds the tool result to the conversation or agent state.

The model can then: - Use the result to prepare a final response. -
Request another tool. - Ask the user for missing information.

The cycle continues until a stopping condition is reached.

### Important Distinction

**ReAct is an agent reasoning pattern, not a communication protocol or a
particular framework.**

It can be implemented using direct model APIs or frameworks such as
LangGraph and other agent orchestration libraries.

------------------------------------------------------------------------

## 4. ReAct vs. Traditional Workflows

  -----------------------------------------------------------------------
  Dimension               ReAct Agent             Traditional Workflow
  ----------------------- ----------------------- -----------------------
  Decision-making         Chooses actions         Steps are predefined
                          dynamically             

  Execution               Uses observations to    Follows configured
                          decide the next step    transitions

  Execution paths         Can take different      Usually follows defined
                          paths at runtime        paths

  Flexibility             More flexible           More constrained

  Predictability          Less predictable        More predictable

  Testing                 Requires careful        Easier to test
                          control and evaluation  deterministically
  -----------------------------------------------------------------------

### Which One Should You Use?

Neither is universally better.

**Use a traditional workflow when:** - The process is known in
advance. - Steps must execute in a specific order. - Predictability and
auditability are important. - The same input should generally produce
the same execution path.

**Use ReAct when:** - The next action depends on information discovered
at runtime. - The task requires choosing among multiple tools. - The
agent must adapt to unexpected results. - The exact execution path
cannot be fully predefined.

### Production Engineering Insight

Production systems frequently combine both approaches.

For example, a customer-support system might use: - A deterministic
workflow for authentication and refund eligibility. - A ReAct agent to
retrieve relevant documentation or decide whether a query needs
escalation.

This balances flexibility with control.

------------------------------------------------------------------------

## 5. Limitations of ReAct

This is where interviewers test whether you understand engineering
rather than just definitions.

### 1. Infinite Loops

The agent repeatedly calls tools without making meaningful progress.

**Mitigation:** Set maximum iteration limits, detect repeated calls, and
define explicit stopping conditions.

### 2. Invalid Tool Calls

The model requests a tool that does not exist or supplies malformed
arguments.

**Mitigation:** Use tool allowlists, schema validation, and clear error
responses.

### 3. Poor Action Selection

The model chooses an inappropriate tool or makes an incorrect decision
based on the available context.

**Mitigation:** Improve tool descriptions, constrain available actions,
and evaluate decisions against representative test cases.

### 4. Latency

Every additional model call and tool execution increases response time.

**Mitigation:** Limit unnecessary iterations, use efficient models where
appropriate, and parallelize independent operations when safe.

### 5. Cost

More iterations generally mean more model calls and token consumption.

**Mitigation:** Set budgets for model calls and tokens, and avoid
unnecessary reasoning cycles.

### 6. Security Risks

Untrusted tool output can contain instructions designed to manipulate
subsequent model behavior. This is a form of prompt injection.

**Mitigation:** - Treat tool output as untrusted data. - Enforce
permissions outside the model. - Never rely on the model alone for
authorization. - Require human approval for consequential actions. -
Restrict access to sensitive tools and data.

------------------------------------------------------------------------

## 6. Engineering Safeguards Checklist

Before deploying a ReAct-based agent, consider the following:

-   [ ] Maximum iteration limit
-   [ ] Tool allowlist
-   [ ] Argument and schema validation
-   [ ] Tool execution timeouts
-   [ ] Authentication and authorization checks
-   [ ] Error handling and retry policy
-   [ ] Token and cost budgets
-   [ ] Repeated-action or loop detection
-   [ ] Human approval for consequential actions
-   [ ] Structured execution traces and logging
-   [ ] Evaluation against representative tasks

------------------------------------------------------------------------

## 7. Key Takeaways

-   ReAct means **Reasoning + Acting**.
-   It follows an iterative cycle: **Thought → Action → Observation**.
-   The next action is selected using the latest observation.
-   The application executes tool calls; the LLM requests them.
-   ReAct provides flexibility but introduces latency, cost, and control
    challenges.
-   Traditional workflows are preferable for predictable, predefined
    processes.
-   Production systems can combine workflows and agents.

------------------------------------------------------------------------

## 8. Interview Questions

### Q1. What is ReAct?

ReAct is an approach to agent design in which a language model
alternates between reasoning about a task, taking actions through tools,
and observing their results to decide what to do next.

### Q2. What is the difference between ReAct and a traditional workflow?

A traditional workflow follows predefined steps or transitions. A ReAct
agent dynamically selects its next action based on the current context
and observations.

### Q3. Does ReAct require tools?

Not necessarily in every implementation, but tool use is a central part
of many practical ReAct agents. Tools let the agent interact with
external systems and obtain information or perform actions.

### Q4. What is an observation in ReAct?

An observation is the result returned after an action, such as an API
response, database result, search result, or tool error. The model uses
it to decide the next step.

### Q5. How do you prevent an agent from looping forever?

Use maximum iteration limits, execution budgets, repeated-action
detection, timeouts, and explicit stopping conditions.

### Q6. Is ReAct a framework?

No. ReAct is a reasoning and action pattern. It can be implemented using
model APIs or orchestration frameworks.

### Q7. Why might a workflow be better than ReAct?

A workflow is often easier to test, audit, and predict when the required
process is already known. ReAct adds flexibility but also adds
uncertainty, latency, and cost.

------------------------------------------------------------------------

## 9. Quick Revision

  Term              Remember
  ----------------- ----------------------------------------------------
  ReAct             Reasoning + Acting
  Thought           Decide what information or action is needed
  Action            Request and execute a tool
  Observation       Receive the tool result
  Context update    Make the result available for the next model step
  Iteration limit   Prevent unbounded execution
  Tool validation   Ensure requested tools and arguments are permitted

**Core pattern to remember:**

``` text
Reason → Act → Observe → Update Context → Reason Again
```

**Interview one-liner:** ReAct makes an agent adaptive by allowing it to
choose its next action based on the results of its previous actions.
