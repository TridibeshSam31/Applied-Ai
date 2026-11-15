# Topic 1/7 --- Fundamentals of Agent Evaluation

## 1. Why Do We Need Agent Evaluation?

Imagine that you have built a customer support agent.

**User:** \> Where is my order ORD123?

**Agent:** \> Your order has been delivered.

But the actual database status is `delayed`.

The response is grammatically correct and sounds professional, but it is
factually wrong.

**A fluent response does not necessarily mean a correct agent.**

Traditional software often has deterministic behavior that can be tested
with assertions:

``` python
def add(a, b):
    return a + b

assert add(2, 3) == 5
```

AI agents are more complex. The same input can lead to different
execution paths:

``` text
User Request
     |
     v
Agent Reasoning
     |
     v
Tool Selection
     |
     v
Tool Execution
     |
     v
Result Interpretation
     |
     v
Final Response
```

Every stage can fail. Therefore, evaluating only the final answer is
insufficient.

## 2. What Exactly Should We Evaluate?

Agent evaluation can be divided into five layers:

1.  **Task Success** --- Did the agent solve the user's problem?
2.  **Tool Selection and Execution** --- Did it choose and execute the
    correct tools?
3.  **Response Quality** --- Was the final answer accurate and relevant?
4.  **Efficiency** --- How much time and money did it consume?
5.  **Safety and Reliability** --- Did it respect permissions and handle
    failures?

### A. Task Success

Did the agent actually complete the requested task?

Example:

``` text
User: Check my order status.

Expected:
- Fetch the correct order.
- Return the actual status.
- Do not invent information.
```

An agent that returns a beautifully written but incorrect status has
failed.

### B. Tool Selection and Execution

Suppose the agent has these tools:

``` python
tools = [
    get_order_status,
    create_support_ticket,
    cancel_order,
]
```

The user asks:

``` text
Where is my order?
```

The expected tool call is:

``` python
get_order_status(order_id="ORD123")
```

If the agent calls `cancel_order()` instead, that is a tool-selection
failure.

Even when the correct tool is selected, incorrect arguments or failed
execution can still make the workflow unsuccessful.

### C. Response Quality

Evaluate whether the final response is:

-   Factually accurate.
-   Relevant to the query.
-   Clear and understandable.
-   Consistent with tool results.
-   Free from unsupported claims.

### D. Efficiency

An agent might successfully answer a question but make 12 unnecessary
LLM calls.

That is technically successful, but inefficient.

Evaluate:

-   Latency.
-   Token consumption.
-   API cost.
-   Number of tool calls.
-   Number of unnecessary execution steps.

### E. Safety and Reliability

Suppose a user asks:

``` text
Show me another customer's order details.
```

The agent must not expose another customer's data.

Similarly, ticket creation must not happen without satisfying backend
authorization and business rules.

An agent that completes tasks but violates security is not
production-ready.

## 3. Three Important Evaluation Approaches

### 1. Rule-Based Evaluation

Use deterministic assertions for things that have an objectively correct
answer.

``` python
def evaluate_order_status(actual, expected):
    return actual == expected


assert evaluate_order_status(
    "delayed",
    "delayed",
)
```

Best suited for:

-   Database outputs.
-   Tool arguments.
-   Authorization.
-   Required workflow steps.
-   Structured output validation.

### 2. LLM-as-a-Judge

Use another LLM to assess qualitative output.

Example:

``` text
Question:
Where is my order?

Expected answer:
Your order is delayed.

Actual answer:
Your package has not shipped yet and is delayed.

Judge:
Is the answer factually consistent with the expected answer?
```

An LLM judge can assess semantic quality, relevance, and helpfulness.

However, it can also be wrong, biased, or inconsistent. It needs
calibration against human-labelled examples.

### 3. Human Evaluation

Humans review agent outputs and execution traces.

Useful for:

-   Ambiguous queries.
-   Complex reasoning.
-   Safety-sensitive workflows.
-   Calibrating automated judges.

In practice, a strong evaluation system combines all three approaches.

## 4. The Difference Between Evaluating an LLM and an Agent

  LLM Evaluation            Agent Evaluation
  ------------------------- ------------------------------
  Text generation quality   Complete task execution
  Factual accuracy          Tool selection correctness
  Relevance                 Workflow correctness
  Instruction following     State transition correctness
  Response quality          Tool and action safety

An LLM can generate a perfect explanation but still be a poor agent if
it cannot use tools correctly.

**Agent evaluation must evaluate the entire execution trajectory, not
just the final response.**

## 5. Build a Tiny Evaluation System

Let's write a basic evaluator for our customer support agent.

``` python
def evaluate_agent_run(
    expected_status: str,
    actual_status: str,
    expected_tool: str,
    actual_tool: str,
    expected_answer_contains: str,
    actual_answer: str,
):
    results = {
        "task_accuracy": (
            expected_status == actual_status
        ),
        "tool_accuracy": (
            expected_tool == actual_tool
        ),
        "response_accuracy": (
            expected_answer_contains.lower()
            in actual_answer.lower()
        ),
    }

    results["passed"] = all(results.values())
    return results


result = evaluate_agent_run(
    expected_status="delayed",
    actual_status="delayed",
    expected_tool="get_order_status",
    actual_tool="get_order_status",
    expected_answer_contains="delayed",
    actual_answer="Your order is delayed.",
)

print(result)
```

Expected output:

``` python
{
    'task_accuracy': True,
    'tool_accuracy': True,
    'response_accuracy': True,
    'passed': True
}
```

Now deliberately introduce a failure:

``` python
actual_tool = "cancel_order"
```

The evaluator should return `tool_accuracy: False` and `passed: False`.

This is a primitive evaluator, not a complete production evaluation
framework. But it demonstrates an important principle:

**Evaluation requires an expected result, an observed result, and a
comparison method.**

## 6. Key Terminology

  -----------------------------------------------------------------------
  Term                                Meaning
  ----------------------------------- -----------------------------------
  Evaluation dataset                  Collection of test inputs and
                                      expected outcomes

  Ground truth                        Trusted expected answer or outcome

  Evaluator                           Logic that scores an agent run

  Trace                               Record of the agent's execution
                                      steps

  Trajectory                          Sequence of actions taken by an
                                      agent

  Regression testing                  Checking that old capabilities
                                      still work after changes

  Benchmark                           Standardized evaluation set or
                                      procedure
  -----------------------------------------------------------------------

## 7. Interview Questions

1.  Why is final-answer evaluation insufficient for AI agents?
2.  What's the difference between LLM evaluation and agent evaluation?
3.  When should you use rule-based evaluation instead of LLM-as-a-Judge?
4.  What is an execution trajectory?
5.  Can an agent have 100% task success but still be unsuitable for
    production? Explain.

------------------------------------------------------------------------

## Core Takeaway

A reliable agent is not judged only by how well it talks. It must
complete the task, use tools correctly, produce grounded responses,
operate efficiently, and respect safety constraints. Evaluate the full
execution path---not just the final text.
