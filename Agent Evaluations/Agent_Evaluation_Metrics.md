# Module 5: Agent Evaluation --- Topic 2/7

# Agent Evaluation Metrics

Last lesson, we learned that an agent cannot be evaluated only on the
basis of its final response.

In this lesson, we will learn how to measure an agent's performance
using numbers.

Suppose you have built a customer support agent and have 100 test cases.
You want to answer:

-   How many tasks were successfully completed?
-   How often was the correct tool called?
-   How often does the agent hallucinate?
-   What is the average response time?
-   What is the cost per successful task?

Metrics help answer these questions.

## 1. Task Success Rate

**Core metric**

Task Success Rate measures how often an agent successfully completes the
task requested by the user.

Formula:

\[ `\text{Task Success Rate}`{=tex} =
`\frac{\text{Successful Tasks}}{\text{Total Tasks}}`{=tex}
`\times 100`{=tex} \]

Example:

-   Total test cases = 100
-   Successfully completed = 85

\[ `\frac{85}{100}`{=tex}`\times 100`{=tex} = 85% \]

`<text>`{=html}Task Success Rate: 85% --- 85 successful, 15
failed.`</text>`{=html}

Python implementation:

``` python
def task_success_rate(results):
    successful = sum(results)
    total = len(results)

    if total == 0:
        return 0

    return (successful / total) * 100


results = [
    True, True, False, True, True,
    True, False, True, True, True,
]

print(task_success_rate(results))
```

Expected output:

``` text
80.0
```

**Important:** Define success criteria before evaluation. If creating a
support ticket was required, a correct verbal response alone must not
count as a successful task.

## 2. Tool Call Accuracy

An agent may have multiple tools. Did it select the correct tool and
pass the correct arguments?

Example:

**User:**

``` text
Check the status of order ORD123.
```

**Expected:**

``` python
get_order_status(order_id="ORD123")
```

**Actual:**

``` python
get_order_status(order_id="ORD123")
```

This is correct.

But if the agent calls:

``` python
create_support_ticket(order_id="ORD123")
```

then its tool selection is incorrect.

### Basic formulas

Tool selection accuracy:

\[ `\text{Tool Selection Accuracy}`{=tex} =
`\frac{\text{Correct Tool Selections}}`{=tex}
{`\text{Total Tool Selection Decisions}`{=tex}} `\times 100`{=tex} \]

Argument accuracy:

\[ `\text{Argument Accuracy}`{=tex} =
`\frac{\text{Correct Tool Argument Sets}}`{=tex}
{`\text{Total Tool Calls}`{=tex}} `\times 100`{=tex} \]

Example:

  Test   Expected             Actual               Result
  ------ -------------------- -------------------- --------
  1      `get_order_status`   `get_order_status`   Pass
  2      `create_ticket`      `create_ticket`      Pass
  3      `get_order_status`   `cancel_order`       Fail
  4      `get_order_status`   `get_order_status`   Pass

Tool selection accuracy = 75%.

**Engineering distinction:** Tool selection accuracy and tool execution
success are different metrics. The agent may select the correct tool,
but execution can still fail because of a database timeout.

## 3. Trajectory Accuracy

This is a more advanced concept.

A **trajectory** is the sequence of steps an agent follows to complete a
task.

Suppose the expected workflow is:

``` text
User Request
     |
     v
get_order_status
     |
     v
Check delayed status
     |
     v
create_support_ticket
     |
     v
Final Response
```

Actual workflow:

``` text
User Request
     |
     v
get_order_status
     |
     v
get_customer_details
     |
     v
get_order_status
     |
     v
create_support_ticket
     |
     v
Final Response
```

Both workflows may produce the correct final result, but the actual
agent made unnecessary calls.

Trajectory evaluation checks:

-   Correct sequence of actions.
-   Unnecessary tool calls.
-   Missing steps.
-   Incorrect transitions.
-   Repeated or redundant actions.

There is no single universal trajectory-accuracy formula. Depending on
the task, you can use exact sequence matching, step-level
precision/recall, or semantic trajectory judging.

For example, exact matching:

``` python
expected = [
    "get_order_status",
    "create_support_ticket",
]

actual = [
    "get_order_status",
    "create_support_ticket",
]

trajectory_match = expected == actual
print(trajectory_match)
```

Output:

``` text
True
```

Exact matching is useful for deterministic workflows, but it can
unfairly penalize valid alternative paths.

## 4. Hallucination Rate

A hallucination occurs when an agent generates unsupported or false
information.

Example --- actual database data:

``` json
{
    "order_id": "ORD123",
    "status": "delayed"
}
```

Agent response:

``` text
Your order will be delivered tomorrow at 10 AM.
```

The database did not contain a delivery date or time. The agent made an
unsupported claim.

Basic formula:

\[ `\text{Hallucination Rate}`{=tex} =
`\frac{\text{Responses with Unsupported Claims}}`{=tex}
{`\text{Evaluated Responses}`{=tex}} `\times 100`{=tex} \]

Example:

-   100 responses evaluated.
-   8 contained unsupported claims.

Hallucination rate = 8%.

**Important:** Hallucination evaluation needs a clearly defined scope. A
response can contain one unsupported claim among several correct claims.
Claim-level evaluation is often more informative than simply marking the
entire response.

## 5. Latency

Latency measures how long the agent takes to generate a response.

Example:

  Request        Time
  --------- ---------
  1           1.2 sec
  2           2.5 sec
  3           1.8 sec
  4           3.0 sec
  5           1.5 sec

Average latency:

\[ `\text{Average Latency}`{=tex} =
`\frac{\sum \text{Request Times}}{\text{Total Requests}}`{=tex} \]

\[ = `\frac{1.2+2.5+1.8+3.0+1.5}{5}`{=tex} = 2`\text{ sec}`{=tex} \]

But average latency alone is not enough.

### Percentile latency

Suppose 100 users are using the agent:

-   **P50:** 50% of requests completed within this time.
-   **P95:** 95% of requests completed within this time.
-   **P99:** 99% of requests completed within this time.

Illustrative latency distribution:

  Percentile     Latency
  ------------ ---------
  P50            1.2 sec
  P95            4.8 sec
  P99            8.5 sec

These are example values, not benchmark results.

For production monitoring, P95 and P99 often reveal slow requests that
averages hide.

## 6. Token Usage and Cost

Every LLM call consumes tokens.

Tokens are generally divided into:

-   **Input tokens:** Prompt, context, tool definitions, and
    conversation history.
-   **Output tokens:** Generated response.

Example:

  Metric     Tokens
  -------- --------
  Input       2,000
  Output        500
  Total       2,500

For an agent, remember that one task may involve multiple LLM calls.

``` text
LLM Call 1 → 1,000 tokens
LLM Call 2 →   800 tokens
LLM Call 3 →   700 tokens

Total = 2,500 tokens
```

### Cost calculation

\[ `\text{Cost}`{=tex} =
`\frac{\text{Input Tokens}\times\text{Input Rate}}{1,000,000}`{=tex} +
`\frac{\text{Output Tokens}\times\text{Output Rate}}{1,000,000}`{=tex}
\]

Let's use hypothetical rates:

-   Input: \$0.50 per million tokens.
-   Output: \$2.00 per million tokens.
-   Input usage: 2,000 tokens.
-   Output usage: 500 tokens.

\[ `\text{Cost}`{=tex} = `\frac{2000 \times 0.50}{10^6}`{=tex} +
`\frac{500 \times 2}{10^6}`{=tex} \]

\[ = \$0.002 \]

Actual pricing depends on the model and provider. Cached input, tool
usage, and other charges may also affect the bill.

**Important metric: Cost per successful task.**

\[ `\text{Cost per Success}`{=tex} =
`\frac{\text{Total Evaluation Cost}}{\text{Successful Tasks}}`{=tex} \]

An agent that costs \$10 and completes 100 tasks is more cost-efficient
than one that costs \$20 for the same 100 tasks, assuming comparable
quality and safety.

## 7. Reliability and Tool Execution Metrics

Production agents also need operational metrics.

  Metric                        What it measures
  ----------------------------- ---------------------------------------------
  Tool execution success rate   How often tool execution succeeds
  Timeout rate                  How often operations exceed the timeout
  Retry rate                    How frequently retries occur
  Error rate                    Percentage of failed executions
  Escalation rate               How often human intervention is needed
  Safety violation rate         How often defined safety rules are violated

Example:

``` python
total_tool_calls = 200
successful_tool_calls = 190

tool_success_rate = (
    successful_tool_calls / total_tool_calls
) * 100

print(tool_success_rate)
```

Output:

``` text
95.0
```

Do not confuse tool execution success with task success. A tool may
execute perfectly but return a result that does not solve the user's
problem.

## 8. Build a Small Agent Evaluation Dashboard

Let's bring the metrics together.

Suppose we evaluate an agent on 100 test cases.

**Example evaluation results:**

  Metric                      Result Interpretation
  ------------------------- -------- ------------------------------------
  Task success rate              85% 85 of 100 tasks succeeded
  Tool selection accuracy        92% 92 correct selections
  Tool execution success         96% 96 successful tool executions
  Hallucination rate              6% 6 responses had unsupported claims
  Human escalation rate          12% 12 tasks needed human review

These are illustrative dataset values, not real benchmark results.

Notice something: task success is 85%, but tool execution success is
96%.

This tells us the problem may not be tool infrastructure. The agent
might be selecting the wrong tools, misunderstanding results, or
producing incorrect final answers.

Metrics help us identify where to investigate instead of randomly
changing prompts.

## 9. Which Metrics Matter Most?

Do not optimize every metric independently.

For a customer support agent, the priorities could be:

  Priority   Metric                                 Why
  ---------- -------------------------------------- ---------------------------------
  Critical   Task success rate                      Did it solve the problem?
  Critical   Safety violation rate                  Did it break access rules?
  High       Tool selection and argument accuracy   Did it act correctly?
  High       Hallucination rate                     Did it invent facts?
  High       P95 latency                            Is the experience fast enough?
  Medium     Cost per successful task               Is it economically viable?
  Medium     Escalation rate                        How often does it need a human?

A cheap, fast agent that leaks customer data is a failure. Safety is not
something you trade away for lower latency.

## 10. Practical Exercise

Your task: Write a function that calculates these three metrics:

1.  Task success rate.
2.  Tool execution success rate.
3.  Average latency.

Try this dataset:

``` python
runs = [
    {
        "task_success": True,
        "tool_success": True,
        "latency": 1.5,
    },
    {
        "task_success": True,
        "tool_success": True,
        "latency": 2.0,
    },
    {
        "task_success": False,
        "tool_success": True,
        "latency": 3.0,
    },
    {
        "task_success": True,
        "tool_success": False,
        "latency": 4.0,
    },
    {
        "task_success": False,
        "tool_success": False,
        "latency": 2.5,
    },
]
```

Expected values to verify your implementation:

-   Task success rate = 60%.
-   Tool execution success rate = 60%.
-   Average latency = 2.6 seconds.

------------------------------------------------------------------------

## Core Takeaway

Agent evaluation is not one score. It is a collection of metrics that
reveal whether an agent completes tasks, chooses and executes tools
correctly, stays grounded, responds quickly, uses resources efficiently,
and operates safely.

Use task success and safety to understand whether the agent is fit for
purpose. Use trajectory, latency, cost, and operational metrics to
understand how it behaves and where it needs improvement.
