# Topic 9: Agent Reliability & Error Handling

## 1. Why Agent Reliability Matters

Building an agent that works in a demo is relatively easy. Making it
work reliably in production is much harder.

Consider our Customer Support Agent. A user asks:

> Check my order status.

The agent decides to call:

``` python
get_order_status(order_id)
```

Several things can go wrong:

-   PostgreSQL is unavailable.
-   A database query times out.
-   The LLM generates invalid tool arguments.
-   A tool returns an error.
-   An OpenAI API request fails.
-   The agent repeatedly calls the same tool.

A production agent should handle these failures gracefully rather than
crashing or continuing indefinitely.

## 2. Five Major Failure Categories

  Failure category   Example                             Main solution
  ------------------ ----------------------------------- --------------------
  LLM failure        API timeout                         Retry with backoff
  Tool failure       Database unavailable                Error handling
  Invalid input      Incorrect UUID                      Schema validation
  Infinite loop      Repeated tool calls                 Iteration limits
  Duplicate action   Same support ticket created twice   Idempotency

These mechanisms address different problems. No single mechanism makes
an agent reliable by itself.

## 3. Retry Mechanism

Suppose a database is temporarily unavailable. Instead of failing
immediately, the application may retry the operation.

Example:

``` text
Request 1 → Timeout
Request 2 → Timeout
Request 3 → Success
```

However, retrying immediately and repeatedly can increase load on an
already unhealthy service.

### Exponential backoff

Exponential backoff increases the delay between retry attempts.

\[ delay = base `\times 2`{=tex}\^{attempt} \]

Example, using a base delay of one second:

    Attempt        Wait
  --------- -----------
          1    1 second
          2   2 seconds
          3   4 seconds
          4   8 seconds

Add **jitter**, a small random delay, to reduce the chance that many
clients retry simultaneously.

### Python example

``` python
import time
import random

def retry_operation(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()

        except ConnectionError:
            if attempt == max_retries - 1:
                raise

            delay = 2 ** attempt
            jitter = random.uniform(0, 0.5)

            time.sleep(delay + jitter)
```

Usage:

``` python
def fetch_order():
    # Simulate a database operation
    return "Order fetched"

result = retry_operation(fetch_order)
print(result)
```

This is a basic teaching example. Production implementations should use:

-   Bounded retries
-   Operation-specific exception handling
-   A total timeout budget
-   Jitter
-   Appropriate retry policies for each dependency

**Important:** Do not retry every exception. A validation error is not
going to disappear after three attempts. Retry transient failures, not
permanent failures.

Also consider whether the operation is safe to repeat. Retrying a write
operation without idempotency can create duplicate side effects.

## 4. Idempotency

Idempotency is one of the most important backend concepts for reliable
agents.

Suppose a customer clicks **Create support ticket**. The server
successfully creates the ticket, but the response is lost because of a
network issue.

The customer retries the request.

### Without idempotency

``` text
Request 1 → Ticket 101 created
Request 2 → Ticket 102 created
```

Two duplicate tickets now exist.

### With idempotency

``` text
Request 1 → Ticket 101 created
Request 2 → Existing Ticket 101 returned
```

The repeated request has the same effect as the original request.

### Idempotency key

The client supplies a unique key for the logical operation. The server
stores that key and associates it with the result.

For our project, this is why we added a unique `idempotency_key` to the
`SupportTicket` model.

The database uniqueness constraint is important: application-level
checks alone can be vulnerable to concurrent requests.

## 5. Circuit Breaker Pattern

Imagine PostgreSQL has been unavailable for five minutes. The agent
continues sending requests to it.

This wastes resources and increases latency.

A **circuit breaker** prevents an application from repeatedly calling a
dependency that appears unhealthy.

### Three circuit breaker states

1.  **Closed:** The dependency is considered healthy, so requests are
    allowed.
2.  **Open:** A failure threshold has been reached, so requests are
    rejected immediately rather than sent to the dependency.
3.  **Half-open:** After a cooldown period, a limited test request is
    allowed.

State transitions:

``` text
              Failure threshold reached
       ┌────────────────────────────────┐
       │                                v
   CLOSED ───────────────────────────> OPEN
      ^                                  |
      |                                  |
      | Success                          | Cooldown expires
      |                                  v
      └──────────────────────────── HALF-OPEN
                                         |
                                         | Test fails
                                         └──────────> OPEN
```

If the half-open test succeeds, the circuit closes. If it fails, the
circuit opens again.

A circuit breaker is different from a retry:

-   **Retry:** Try the operation again after a failure.
-   **Circuit breaker:** Stop sending requests to a dependency that is
    repeatedly failing.

## 6. Agent Iteration Limits

Consider an agent runtime:

``` python
for iteration in range(settings.max_agent_iterations):
    response = client.responses.create(...)
```

Why impose a maximum number of iterations?

An agent may get stuck in a repetitive loop:

``` text
LLM → Tool A
LLM → Tool A
LLM → Tool A
LLM → Tool A
...
```

An iteration limit protects against:

-   Unnecessary API costs
-   Repeated tool calls
-   Excessive latency
-   Endless agent execution

Iteration limits alone are not enough. A reliable runtime should also
enforce:

-   An overall deadline
-   A token or cost budget
-   Tool-specific timeouts

## 7. A Safer Tool Execution Layer

A tool should not be executed without safeguards. The following example
catches invalid arguments separately from unexpected execution failures.

``` python
import logging

logger = logging.getLogger(__name__)

def safe_execute_tool(
    tool_name,
    arguments,
    db,
    customer_id,
):
    try:
        result = execute_tool(
            tool_name=tool_name,
            arguments=arguments,
            db=db,
            customer_id=customer_id,
        )

        if not isinstance(result, dict):
            raise TypeError("Tool must return a dictionary")

        return result

    except (ValueError, TypeError, KeyError):
        logger.warning(
            "Invalid arguments for tool: %s",
            tool_name,
        )

        return {
            "success": False,
            "error": "Invalid tool arguments.",
        }

    except Exception:
        logger.exception(
            "Tool execution failed: %s",
            tool_name,
        )

        return {
            "success": False,
            "error": "Tool execution failed. Please try again later.",
        }
```

This implementation:

1.  Catches invalid arguments.
2.  Logs unexpected failures.
3.  Avoids exposing database internals to the LLM.
4.  Returns a structured error response.

A production improvement is to classify transient failures separately
from permanent failures before deciding whether to retry.

The example is a starting point, not a complete production execution
layer. It should be combined with input validation, authorization,
timeouts, retry policies, and idempotency where appropriate.

## 8. Interview Questions

### Q1. Why should we not retry every failed tool call?

Some failures are permanent, such as invalid input or authorization
errors. Retrying them wastes time and resources. Retries should target
transient failures.

### Q2. What is idempotency, and why is it important in AI agents?

Idempotency means repeating the same logical operation does not create
additional effects. It prevents duplicate actions when requests are
retried, such as creating multiple support tickets.

### Q3. What happens if an LLM repeatedly calls the same tool?

The agent can waste tokens, increase API costs, repeatedly query
services, and create excessive latency. Iteration limits and
loop-detection safeguards help control this.

### Q4. Explain exponential backoff.

It is a retry strategy in which the delay increases exponentially after
each failed attempt. Jitter can be added to prevent synchronized retries
from many clients.

### Q5. What is a circuit breaker?

A reliability pattern that stops requests to a dependency after repeated
failures. It uses closed, open, and half-open states to control when
requests are allowed again.

### Q6. What is the difference between retry and fallback?

-   **Retry:** Attempts the same operation again.
-   **Fallback:** Uses an alternative response, service, or execution
    path when the primary operation cannot succeed.

### Q7. Why should tool execution have timeouts?

Timeouts prevent a slow or unresponsive dependency from holding
resources indefinitely and help enforce an overall execution deadline.

### Q8. How would you prevent duplicate support tickets?

Use an idempotency key for each logical ticket-creation request, enforce
uniqueness in the database, and return the previously created result
when the same key is received again.

## 9. Quick Revision

  Concept                          What it protects against
  -------------------------------- -------------------------------------------
  Retry with exponential backoff   Temporary failures
  Jitter                           Synchronized retry spikes
  Idempotency                      Duplicate side effects
  Circuit breaker                  Repeated calls to an unhealthy dependency
  Iteration limits                 Repetitive or endless agent loops
  Timeouts and deadlines           Slow or unresponsive operations
  Schema validation                Invalid tool arguments
  Structured error responses       Uncontrolled error propagation

**Core takeaway:** A reliable agent does not assume that its LLM, tools,
database, or external APIs will always work. It validates inputs, limits
execution, handles failures, and protects side effects.
