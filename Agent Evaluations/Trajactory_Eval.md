# Module 5: Agent Evaluation --- Topic 5/7

# Trajectory Evaluation and Tool Evaluation

So far, we have learned how to evaluate:

-   Whether the agent's final answer is correct.
-   Whether the task was successfully completed.
-   How to measure response quality using LLM-as-a-Judge.

But an important problem remains:

**If the agent's final answer is correct, does that mean it worked
correctly?**

Not necessarily.

Suppose the user asks:

> Check my order and create a support ticket if it's delayed.

The agent's final response is:

> Your support ticket has been created.

The response may be correct, but the agent might have:

-   Never checked the order status.
-   Created a ticket randomly.
-   Accessed the wrong customer's order.

Therefore, we need to evaluate the agent's complete execution process.

## 1. What Is an Agent Trajectory?

A **trajectory** is the sequence of actions, tool calls, observations,
and decisions taken by an agent while completing a task.

Example:

``` text
USER REQUEST
     |
     v
AGENT REASONING
     |
     v
get_order_status("ORD123")
     |
     v
TOOL OBSERVATION
Status = delayed
     |
     v
AGENT REASONING
     |
     v
create_support_ticket("ORD123")
     |
     v
TOOL OBSERVATION
Ticket = TKT501
     |
     v
FINAL RESPONSE
```

This complete execution path is the agent's trajectory.

A trajectory can be represented as:

\[ `\tau `{=tex}= (s_0,a_0,o_1,a_1,o_2,`\ldots`{=tex},a_n) \]

Where:

-   (s_0): Initial state.
-   (a_i): Agent action.
-   (o_i): Observation returned by the environment or tool.
-   (`\tau`{=tex}): Complete trajectory.

For evaluation, we inspect this sequence instead of looking only at the
final answer.

## 2. What Exactly Should We Evaluate?

Trajectory evaluation can be divided into several dimensions:

  -----------------------------------------------------------------------
  Dimension                           What we check
  ----------------------------------- -----------------------------------
  Tool selection                      Was the correct tool selected?

  Argument correctness                Were correct arguments passed?

  Execution order                     Were tools called in the right
                                      sequence?

  Tool necessity                      Were unnecessary calls avoided?

  Observation handling                Did the agent interpret tool
                                      results correctly?

  Termination                         Did the agent stop at the right
                                      time?

  Task completion                     Did the complete workflow succeed?
  -----------------------------------------------------------------------

Let's understand each with examples.

### A. Tool Selection Accuracy

**User:**

``` text
Check the status of ORD123.
```

Available tools:

``` python
get_order_status()
create_support_ticket()
cancel_order()
```

Expected:

``` python
get_order_status("ORD123")
```

Actual:

``` python
get_order_status("ORD123")
```

`<badge color="success">`{=html}Pass`</badge>`{=html}

If the agent calls `cancel_order()` instead, it is a tool-selection
failure.

### B. Argument Correctness

Correct tool selection is not enough.

Expected:

``` python
get_order_status(order_id="ORD123")
```

Actual:

``` python
get_order_status(order_id="ORD999")
```

The tool is correct, but the argument is wrong.

This is why tool selection accuracy and argument accuracy must be
measured separately.

### C. Execution Order

Expected:

1.  Get order status.
2.  Check if delayed.
3.  Create support ticket if eligible.

Incorrect:

1.  Create support ticket.
2.  Get order status.

If ticket creation depends on eligibility, execution order matters.

### D. Tool Necessity

Suppose the user asks:

``` text
What is the status of ORD123?
```

The agent executes:

``` python
get_order_status()
get_customer_details()
get_order_status()
get_shipping_history()
```

Only one tool call was necessary.

Unnecessary calls increase:

-   Latency.
-   API cost.
-   Failure probability.
-   Security exposure.

### E. Observation Handling

Tool returns:

``` json
{
  "order_id": "ORD123",
  "status": "delayed"
}
```

Agent says:

``` text
Your order has been delivered.
```

Tool execution was successful, but the agent interpreted the observation
incorrectly.

This is an **observation-grounding failure**.

## 3. Build a Trajectory Evaluator

Let's implement a small evaluator.

Suppose every agent run stores its tool trace.

File: `evaluation/trajectory.py`

``` python
from dataclasses import dataclass


@dataclass
class ToolCall:
    name: str
    arguments: dict


def evaluate_trajectory(
    expected_calls: list[ToolCall],
    actual_calls: list[ToolCall],
):
    expected_names = [
        call.name for call in expected_calls
    ]

    actual_names = [
        call.name for call in actual_calls
    ]

    selection_correct = (
        expected_names == actual_names
    )

    argument_correct = (
        expected_calls == actual_calls
    )

    return {
        "tool_selection_correct": selection_correct,
        "arguments_correct": argument_correct,
        "trajectory_exact_match": (
            selection_correct and argument_correct
        ),
    }


if __name__ == "__main__":
    expected = [
        ToolCall(
            name="get_order_status",
            arguments={"order_id": "ORD123"},
        ),
        ToolCall(
            name="create_support_ticket",
            arguments={"order_id": "ORD123"},
        ),
    ]

    actual = [
        ToolCall(
            name="get_order_status",
            arguments={"order_id": "ORD123"},
        ),
        ToolCall(
            name="create_support_ticket",
            arguments={"order_id": "ORD123"},
        ),
    ]

    print(evaluate_trajectory(expected, actual))
```

Expected output:

``` python
{
    'tool_selection_correct': True,
    'arguments_correct': True,
    'trajectory_exact_match': True
}
```

Now change the actual second argument to:

``` python
arguments={"order_id": "ORD999"}
```

Tool selection remains correct, but argument correctness fails.

### Important limitation

This evaluator uses exact sequence matching. But exact matching is not
always appropriate.

Consider:

**Expected:**

``` text
get_order_status → create_support_ticket
```

**Actual:**

``` text
get_order_status → validate_ticket_eligibility → create_support_ticket
```

If `validate_ticket_eligibility` is an approved additional step, the
actual trajectory may be perfectly valid.

Therefore, real evaluation systems often use:

-   Required-step checks.
-   Forbidden-action checks.
-   Partial trajectory matching.
-   Semantic trajectory evaluation.
-   State-transition validation.

## 4. Precision, Recall and F1 for Tool Calls

Suppose expected tools are:

``` python
expected = [
    "get_order_status",
    "create_support_ticket",
]
```

Actual tools:

``` python
actual = [
    "get_order_status",
    "get_customer_details",
    "create_support_ticket",
]
```

Here:

-   True positives (TP) = 2.
-   False positives (FP) = 1.
-   False negatives (FN) = 0.

### Precision

Measures how many selected tools were actually needed.

\[ Precision = `\frac{TP}{TP+FP}`{=tex} \]

\[ = `\frac{2}{3}`{=tex}=0.667 \]

### Recall

Measures how many required tools were selected.

\[ Recall = `\frac{TP}{TP+FN}`{=tex} \]

\[ = `\frac{2}{2}`{=tex}=1 \]

### F1 Score

The harmonic mean of precision and recall.

\[ F1 = 2 `\times `{=tex}`\frac{Precision \times Recall}`{=tex}
{Precision+Recall} \]

\[ F1 = 0.80 \]

`<text>`{=html}Illustrative tool-call evaluation:`</text>`{=html}

  Metric        Score
  ----------- -------
  Recall         1.00
  Precision      0.67
  F1 score       0.80

This is an illustrative calculation using tool names as sets. Duplicate
calls and execution order require additional metrics.

Python implementation:

``` python
def calculate_tool_metrics(expected, actual):
    expected_set = set(expected)
    actual_set = set(actual)

    tp = len(expected_set & actual_set)
    fp = len(actual_set - expected_set)
    fn = len(expected_set - actual_set)

    precision = (
        tp / (tp + fp)
        if tp + fp else 0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn else 0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    return {
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "f1": round(f1, 2),
    }
```

**Important:** Set-based precision/recall ignore order and duplicate
calls. They are useful for a simple baseline, not a complete trajectory
evaluator.

## 5. Tool Execution Evaluation

Now consider a separate problem.

Suppose the agent selects the correct tool:

``` python
get_order_status("ORD123")
```

But the PostgreSQL connection times out.

This is not a tool-selection failure.

We need to measure tool execution reliability separately.

Useful metrics:

  -----------------------------------------------------------------------
  Metric                              Meaning
  ----------------------------------- -----------------------------------
  Tool execution success rate         Percentage of successful tool
                                      executions

  Tool timeout rate                   Percentage of timed-out calls

  Tool error rate                     Percentage of calls returning
                                      errors

  Retry rate                          Percentage of calls requiring
                                      retries

  Duplicate execution rate            Repeated side effects for the same
                                      logical action
  -----------------------------------------------------------------------

Example:

``` python
tool_runs = [
    "success",
    "success",
    "timeout",
    "success",
    "error",
    "success",
]

success_count = tool_runs.count("success")

success_rate = (
    success_count / len(tool_runs)
) * 100

print(success_rate)
```

Output:

``` text
66.66666666666666
```

A production evaluator should distinguish transient infrastructure
failures from incorrect agent decisions.

## 6. Trajectory Evaluation vs Final Answer Evaluation

  Final Answer Evaluation   Trajectory Evaluation
  ------------------------- ---------------------------
  Checks final response     Checks complete execution
  Accuracy of claims        Correct tool selection
  Relevance                 Correct arguments
  Completeness              Execution order
  Language quality          Unnecessary actions
  Grounding                 Observation handling

Consider this scenario.

Two agents return exactly the same response:

``` text
Your order is delayed.
```

**Agent A:**

``` text
get_order_status("ORD123")
→ Read delayed status
→ Respond
```

**Agent B:**

``` text
get_order_status("ORD999")
→ Ignore result
→ Guess delayed status
→ Respond
```

A final-response evaluator might score both similarly if it does not
inspect evidence.

Trajectory evaluation exposes the difference.

## 7. Frameworks for Trajectory and Tool Evaluation

Some useful tools in this ecosystem:

### LangSmith

`<text color="secondary" size="sm">`{=html}Trace inspection, tool-call
visibility, datasets, experiments and evaluators.`</text>`{=html}

Documentation: https://docs.smith.langchain.com/

### Arize Phoenix

`<text color="secondary" size="sm">`{=html}Tracing, spans, tool
execution inspection and evaluation.`</text>`{=html}

Documentation: https://arize.com/docs/phoenix

### OpenTelemetry

`<text color="secondary" size="sm">`{=html}Distributed traces, spans,
attributes and instrumentation across services.`</text>`{=html}

Documentation: https://opentelemetry.io/docs/

One distinction: OpenTelemetry is primarily an observability standard
and instrumentation ecosystem, not a complete agent evaluation framework
by itself.

## 8. What Does a Real Agent Trace Look Like?

A trace should contain enough information to reconstruct what happened.

Example:

``` json
{
  "run_id": "RUN101",
  "thread_id": "CUSTOMER101",
  "steps": [
    {
      "type": "agent",
      "node": "agent",
      "status": "success"
    },
    {
      "type": "tool",
      "name": "get_order_status",
      "arguments": {
        "order_id": "ORD123"
      },
      "result": {
        "status": "delayed"
      },
      "status": "success",
      "duration_ms": 120
    },
    {
      "type": "tool",
      "name": "create_support_ticket",
      "arguments": {
        "order_id": "ORD123"
      },
      "result": {
        "ticket_id": "TKT501"
      },
      "status": "success",
      "duration_ms": 180
    }
  ],
  "final_status": "success"
}
```

This is a simplified illustrative schema, not a prescribed tracing
standard.

In production, be careful not to log passwords, access tokens, payment
details, or unnecessary personal information. Redact sensitive tool
arguments and outputs.

## 9. Advanced Concept: Expected vs Valid Trajectory

A common mistake is assuming every task has only one correct execution
path.

Suppose the user asks:

``` text
Check ORD123 and create a ticket if delayed.
```

**Valid trajectory A:**

``` text
get_order_status
→ create_support_ticket
→ respond
```

**Valid trajectory B:**

``` text
get_order_status
→ validate_ticket_eligibility
→ create_support_ticket
→ respond
```

Both can be correct.

But this trajectory is invalid:

``` text
create_support_ticket
→ get_order_status
→ respond
```

Why?

Because the agent performed a side effect before checking eligibility.

This gives us an important evaluation principle:

**Evaluate required conditions and safety constraints, not just one
hardcoded sequence of tool calls.**

For example:

``` python
def validate_ticket_workflow(calls):
    names = [call.name for call in calls]

    if "create_support_ticket" not in names:
        return True

    if "get_order_status" not in names:
        return False

    status_index = names.index("get_order_status")
    ticket_index = names.index("create_support_ticket")

    return status_index < ticket_index
```

This is still a simplified check. A real evaluator must also validate
the actual status, customer ownership, eligibility, and ticket creation
result.

## 10. Practical Assignment

Build a trajectory evaluator for these three scenarios.

### Scenario A --- Correct Execution

``` text
get_order_status(ORD123)
→ status = delayed
→ create_support_ticket(ORD123)
→ success
```

### Scenario B --- Unnecessary Tool Call

``` text
get_order_status(ORD123)
→ get_customer_details(C101)
→ status = shipped
→ response
```

### Scenario C --- Unsafe Execution

``` text
create_support_ticket(ORD123)
→ get_order_status(ORD123)
→ response
```

Your evaluator should identify:

  Check                       A      B                   C
  --------------------------- ------ ------------------- ------
  Correct status check        Pass   Pass                Pass
  Unnecessary calls           Pass   Fail                Pass
  Correct execution order     Pass   Pass                Fail
  Task-specific correctness   Pass   Depends on policy   Fail

------------------------------------------------------------------------

## Core Takeaway

Final-answer evaluation tells you what the agent said. Trajectory
evaluation tells you what the agent actually did.

A production-grade evaluator must inspect tool selection, arguments,
execution order, unnecessary actions, observation handling, and side
effects. Prefer validating required conditions and safety constraints
over blindly enforcing one exact sequence.
