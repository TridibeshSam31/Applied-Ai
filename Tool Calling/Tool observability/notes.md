# Tool Observability & Reliability — LLM Fundamentals (Phase 2)

Security ke baad ab **observability**.

Kyunki production mein sirf ye jaanna kaafi nahi hai:

> "Agent failed."

Tujhe jaanna hoga:

```
WHY?
WHERE?
HOW LONG?
HOW MANY TIMES?
HOW MUCH DID IT COST?
```

## Table of Contents

- [What Is Observability](#what-is-observability)
- [Tool Logs](#tool-logs)
- [What Should You Log](#what-should-you-log)
- [Metrics](#metrics)
- [p50 / p95 / p99](#p50--p95--p99)
- [Tracing an Agent](#tracing-an-agent)
- [Request ID vs Run ID vs Tool Call ID](#request-id-vs-run-id-vs-tool-call-id)
- [Agent Trajectory](#agent-trajectory)
- [Reliability Metrics](#reliability-metrics)
- [Cost Observability](#cost-observability)
- [Reliability Budget](#reliability-budget)
- [Circuit Breaker](#circuit-breaker)
- [Tool Health](#tool-health)
- [Observability Code](#observability-code)
- [Better Architecture](#better-architecture)

## What Is Observability

Three classic pillars:

```
Logs
Metrics
Traces
```

AI agents ke liye ek aur add karo:

```
LLM + Tool + Agent trajectory
```

## Tool Logs

Har execution kuch aisa produce karna chahiye:

```json
{
  "request_id": "req_123",
  "tool": "get_invoice",
  "status": "success",
  "latency_ms": 182,
  "attempt": 1
}
```

Failure ke liye:

```json
{
  "request_id": "req_123",
  "tool": "get_invoice",
  "status": "timeout",
  "latency_ms": 5000,
  "attempt": 2
}
```

## What Should You Log

At minimum:

```
request_id
user/session ID
agent run ID
step number
tool name
tool call ID
arguments (sanitized)
status
latency
attempt
error type
timestamp
```

**Blindly mat log karo:**
```
password
API keys
tokens
private customer information
```

**Observability khud ek security risk ban sakti hai.**

## Metrics

Logs individual events batate hain. **Metrics patterns batate hain.**

Useful metrics:
```
tool_call_total
tool_success_total
tool_failure_total
tool_timeout_total
tool_latency
tool_retry_total
```

Example:
```
get_invoice
Success rate: 98.2%
p95 latency: 420ms
Timeout rate: 0.8%
```

## p50 / p95 / p99

Sirf average latency use mat karo.

Suppose requests:
```
100ms
110ms
120ms
130ms
5000ms
```

Average: `1072ms` — dekhne mein terrible lagta hai. Lekin **most users ko ~100ms mila.**

Iske bajaye:
```
p50 → typical request
p95 → 95% requests are faster than this
p99 → tail latency
```

Production systems ke liye **tail latency bahut matter karti hai.**

## Tracing an Agent

Yahin se agent observability powerful ban jaati hai.

User:
> "Find Rahul's overdue invoice and create a ticket."

Trace:

```
RUN req_123
│
├── LLM call #1
│    └── 420ms
│
├── Tool: search_customer
│    └── 180ms
│
├── LLM call #2
│    └── 390ms
│
├── Tool: get_invoice
│    └── 240ms
│
├── LLM call #3
│    └── 350ms
│
├── Tool: create_ticket
│    └── 310ms
│
└── Final response
```

Ab tu answer kar sakta hai: **Latency kahan se aayi?**

## Request ID vs Run ID vs Tool Call ID

Inko mix mat karo.

**Request ID** — incoming request identify karta hai:
```
req_123
```

**Agent Run ID** — complete agent execution identify karta hai:
```
run_456
```

**Tool Call ID** — ek particular tool invocation identify karta hai:
```
call_789
```

Relationship:

```
Request
  │
  └── Agent Run
        ├── Tool Call
        ├── Tool Call
        └── Tool Call
```

## Agent Trajectory

AI systems ke liye, execution trajectory store karo:

```
User input
 ↓
LLM decision
 ↓
Tool call
 ↓
Tool result
 ↓
LLM decision
 ↓
Tool call
 ↓
Final answer
```

Example:

```json
{
  "run_id": "run_123",
  "steps": [
    {
      "step": 1,
      "action": "search_customer"
    },
    {
      "step": 2,
      "action": "get_invoice"
    },
    {
      "step": 3,
      "action": "create_ticket"
    }
  ]
}
```

Ye baad mein **Phase 7 Agent Evals** mein extremely useful ban jaata hai.

## Reliability Metrics

Tools ke liye track karo:

**Success rate**
```
successful_calls / total_calls
```

**Error rate**
```
failed_calls / total_calls
```

**Retry rate**
```
retried_calls / total_calls
```

**Timeout rate**
```
timeouts / total_calls
```

**Tool selection accuracy** — baad mein, evals mein:
```
correct_tool_calls / total_tool_calls
```

## Cost Observability

Yaad hai Phase 1 ka token/cost tracking? Ek agent multiple LLM calls kar sakta hai:

```
LLM call #1
LLM call #2
LLM call #3
LLM call #4
```

Toh total cost sirf ek request ka nahi hai. Track karo:

```
LLM cost
+
Embedding cost
+
Tool/API cost
+
Retries
```

Example:

```json
{
  "run_id": "run_123",
  "llm_cost": 0.012,
  "tool_cost": 0.004,
  "total_cost": 0.016
}
```

## Reliability Budget

Suppose agent karta hai:

```
LLM → Tool A → Tool B → Tool C
```

Agar har component ka 99% success rate hai:

```
0.99 × 0.99 × 0.99 ≈ 97%
```

Jaise-jaise workflows lambe hote hain, **reliability drop ho sakti hai.** Isiliye agent systems ko chahiye:

```
retries
fallbacks
validation
timeouts
good tool design
evals
```

## Circuit Breaker

Suppose external invoice API poori tarah down hai. Bina protection ke:

```
Agent → invoice API → fail → retry → fail → retry → fail → ...
```

Hazaaron requests ek broken dependency ko hammer karte rahenge.

**Circuit breaker:**

```
Normal
  ↓
Failures increase
  ↓
OPEN
  ↓
Stop sending requests
  ↓
Wait
  ↓
HALF-OPEN
  ↓
Test request
  ↓
Success → CLOSED
Failure → OPEN
```

Ye tere system aur dependency ko protect karta hai. Zaroori nahi aaj hi full circuit breaker implement karo, lekin concept samajhna zaroori hai.

## Tool Health

Health track kar sakte ho:

```
Tool                  Health
──────────────────────────────
search_customer       🟢
get_invoice           🟡
create_ticket         🟢
send_notification     🔴
```

Based on:
```
latency
error rate
timeout rate
dependency status
```

Agent orchestration potentially ye info use kar sakta hai.

## Observability Code

Simple decorator:

```python
import time
import logging

logger = logging.getLogger(__name__)


async def observed_tool(tool_name, tool_fn, *args, **kwargs):

    start = time.perf_counter()

    try:
        result = await tool_fn(*args, **kwargs)

        latency = time.perf_counter() - start

        logger.info(
            "tool_success",
            extra={
                "tool": tool_name,
                "latency_ms": latency * 1000
            }
        )

        return result

    except Exception as exc:

        latency = time.perf_counter() - start

        logger.error(
            "tool_failure",
            extra={
                "tool": tool_name,
                "latency_ms": latency * 1000,
                "error": type(exc).__name__
            }
        )

        raise
```

Ab har tool execution observable hai.

## Better Architecture

Ab tak tera Phase 2 backend conceptually aisa dikhna chahiye:

```
                         USER
                           │
                           ▼
                          LLM
                           │
                     Tool Selection
                           │
                           ▼
                    ┌──────────────┐
                    │ Tool Registry│
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Validate   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Authorize    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Execute      │
                    └──────┬───────┘
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
               Success            Error
                  │                 │
                  │           Retry / Timeout
                  │                 │
                  └────────┬────────┘
                           ▼
                    Structured Result
                           │
                           ▼
                      Update State
                           │
                           ▼
                          LLM
                           │
                           ▼
                       Response

                 ┌─────────────────────┐
                 │   OBSERVABILITY     │
                 │ logs / metrics /    │
                 │ traces / cost       │
                 └─────────────────────┘
```

**Yehi basically tera manual tool-calling engine hai.**