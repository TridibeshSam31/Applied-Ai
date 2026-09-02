# Parallel Tool Calls — LLM Fundamentals (Phase 2)

Ab tak jo kuch kiya:

```
search_customer() → get_invoice() → create_ticket()
```

Ye tha **Sequential Execution**, kyunki:

```
get_invoice() needs customer_id
create_ticket() needs invoice_id
```

**Dependencies thi.**

## Table of Contents

- [Problem with Sequential Execution](#problem-with-sequential-execution)
- [Parallel Execution](#parallel-execution)
- [When Can Tools Run in Parallel](#when-can-tools-run-in-parallel)
- [Visualizing Dependencies](#visualizing-dependencies)
- [How OpenAI Tool Calling Returns Multiple Calls](#how-openai-tool-calling-returns-multiple-calls)
- [Naive Execution](#naive-execution)
- [Async Execution](#async-execution)
- [What gather() Does](#what-gather-does)
- [Example](#example)
- [Tool Results Must Still Go Back to LLM](#tool-results-must-still-go-back-to-llm)
- [Conversation State After Parallel Calls](#conversation-state-after-parallel-calls)
- [What If One Tool Fails](#what-if-one-tool-fails)
- [gather() Failure Behavior](#gather-failure-behavior)
- [Parallelism Is Not Free](#parallelism-is-not-free)
- [Concurrency Limits](#concurrency-limits)
- [External APIs Make This Important](#external-apis-make-this-important)
- [Parallel vs Sequential Interview Question](#parallel-vs-sequential-interview-question)
- [Detecting Dependency](#detecting-dependency)
- [Real Enterprise Workflow](#real-enterprise-workflow)
- [Architecture](#architecture)
- [Production Concern: Duplicate Writes](#production-concern-duplicate-writes)
- [Read vs Write Tools](#read-vs-write-tools)
- [What Companies Actually Do](#what-companies-actually-do)
- [Mental Model](#mental-model)
- [Things You Must Remember](#things-you-must-remember)

## Problem with Sequential Execution

Imagine user poochta hai:

> "Get customer details, balance and recent orders."

Tools:
```
get_customer()
get_balance()
get_recent_orders()
```

Suppose har tool leta hai `500 ms`.

**Sequential:**
```
get_customer()      500ms
get_balance()       500ms
get_recent_orders() 500ms

Total = 1500ms
```

## Parallel Execution

Ye teen tools **independent** hain. Isliye:

```
               LLM
            /   |   \
           ↓    ↓    ↓
 customer balance orders
           ↓    ↓    ↓
        execute together
```

Time:
```
max(500,500,500) ≈ 500ms
```

`1500ms` ki jagah `500ms`. **Huge difference.**

## When Can Tools Run in Parallel

Simple rule:

**Agar tool A ko tool B ka output chahiye → NO parallel**

Example:
```
search_customer() → get_invoice()
```
Must be sequential.

**Agar tools ek-doosre pe depend nahi karte → YES parallel**

Example:
```
get_customer()
get_balance()
get_recent_orders()
```
Ye saath chal sakte hain.

## Visualizing Dependencies

**Sequential:**
```
A
↓
B
↓
C
```

**Parallel:**
```
     A
   / | \
  B  C  D
```

**Hybrid:**
```
search_customer
       │
       ▼
get_invoice

       +
get_recent_orders
       +
get_balance
```

Yahan `get_invoice`, `search_customer` pe depend karta hai, lekin `orders` aur `balance` independently chal sakte hain.

## How OpenAI Tool Calling Returns Multiple Calls

Model return kar sakta hai:

```json
[
  {
    "name": "get_customer",
    "arguments": {...}
  },
  {
    "name": "get_balance",
    "arguments": {...}
  },
  {
    "name": "get_recent_orders",
    "arguments": {...}
  }
]
```

Notice: `3 tool calls`, `same assistant response`. Ye ek hint hai: **ye potentially saath execute ho sakte hain.**

## Naive Execution

Zyadatar beginners ye karte hain:

```python
for tool_call in tool_calls:
    execute_tool(tool_call)
```

Matlab:
```
Tool 1 → wait
Tool 2 → wait
Tool 3 → wait
```

Sequential. Kaam toh karta hai, lekin slow hai.

## Async Execution

Python deta hai `asyncio`. Suppose:

```python
async def get_customer():
    ...

async def get_balance():
    ...

async def get_recent_orders():
    ...
```

Phir:

```python
results = await asyncio.gather(
    get_customer(),
    get_balance(),
    get_recent_orders()
)
```

**Sab saath start hote hain.**

## What gather() Does

Socho:
```
Start A
Start B
Start C
```

instead of:
```
A finish → B finish → C finish
```

Execution:
```
time = 0
A started
B started
C started

time = 500ms
A done
B done
C done
```

## Example

**Bina parallelism:**

```python
customer = get_customer()
balance = get_balance()
orders = get_recent_orders()
```

Latency: `1.5 sec`

**Parallel ke saath:**

```python
customer, balance, orders = await asyncio.gather(
    get_customer(),
    get_balance(),
    get_recent_orders()
)
```

Latency: `0.5 sec`

## Tool Results Must Still Go Back to LLM

Execution parallel hone ke bawajood:

```
Assistant
 ├── get_customer
 ├── get_balance
 └── get_recent_orders
```

Results:
```
Tool Result 1
Tool Result 2
Tool Result 3
```

Sab state mein add hote hain. Phir `LLM` sab kuch receive karta hai.

## Conversation State After Parallel Calls

```
User

Assistant
 ├── call_1
 ├── call_2
 └── call_3

Tool
 ├── result_1
 ├── result_2
 └── result_3
```

Phir: `Assistant Final Answer`

## What If One Tool Fails

Example:
```
get_customer → success
get_balance  → timeout
get_orders   → success
```

Result (balance ke liye):
```json
{
  "success": false,
  "error": "timeout"
}
```

LLM ab dekhta hai: customer available, orders available, balance unavailable — aur accordingly respond kar sakta hai.

## gather() Failure Behavior

By default:
```python
await asyncio.gather(...)
```

Agar ek task crash ho jaaye toh **poora gather fail ho sakta hai.**

Behtar:
```python
await asyncio.gather(
    ...,
    return_exceptions=True
)
```

Phir:
```
Task 1 result
Task 2 exception
Task 3 result
```

Har ek ko individually handle kar sakte ho.

## Parallelism Is Not Free

Suppose model `100 tools` request karta hai. Sabko simultaneously chalane se:

- DB overload
- APIs overload
- rate limits hit
- costs increase

**Limits chahiye.**

## Concurrency Limits

Example:
```python
semaphore = asyncio.Semaphore(10)
```

Matlab: **at most 10 tools simultaneously executing**, chahe `100 tool calls` aa jaayein.

## External APIs Make This Important

Suppose: `Salesforce API`, `Stripe API`, `Jira API`. Har network request `300-800ms` leti hai. Parallel execution responsiveness drastically improve karta hai.

## Parallel vs Sequential Interview Question

**Interviewer:** When should tools be parallelized?

**Correct answer:**

> "Only when there are no dependency relationships between them. If one tool's output is required as another tool's input, execution must remain sequential."

## Detecting Dependency

Suppose:
```
get_invoice(customer_id)
```
needs `customer_id` jo aata hai `search_customer()` se. Isliye: **dependency exists → no parallelism.**

Suppose:
```
get_weather()
get_news()
get_stock_price()
```
Ek-doosre se kuch nahi chahiye. Isliye: **independent → parallel possible.**

## Real Enterprise Workflow

User: **"Prepare customer summary."**

Agent decide kar sakta hai:
```
get_customer()
get_balance()
get_orders()
get_support_tickets()
```

Parallel:
```
           Agent
      /      |      |      \
     ↓       ↓      ↓       ↓
 customer balance orders tickets
      \       |      |      /
       \      |      |     /
           summary
```

**Massive latency reduction.**

## Architecture

```
                    LLM
                     │
            Multiple Tool Calls
                     │
                     ▼

         ┌─────────────────────┐
         │ Parallel Executor   │
         └─────────┬───────────┘
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼

   Tool A       Tool B       Tool C

      ▼            ▼            ▼

   Result A     Result B     Result C

      └────────────┼────────────┘
                   ▼

              Update State
                   ▼

                  LLM
```

## Production Concern: Duplicate Writes

Kabhi bhi ye parallelize mat karo bina side effects samjhe:

```
create_ticket()
update_ticket()
close_ticket()
```

Parallel writes **race conditions** create kar sakte hain. Example: `close_ticket()` aur `update_ticket()` saath chalne se final state unpredictable ban jaata hai.

## Read vs Write Tools

**Safe parallel candidates** (mostly reads):
```
get_customer
search_docs
get_balance
fetch_weather
```

**Dangerous** (writes, care chahiye):
```
create_ticket
update_ticket
delete_ticket
refund_payment
```

## What Companies Actually Do

Bahut saare production agent systems:

```
Parallelize READ operations
Serialize WRITE operations
```

Ye ek **very common pattern** hai.

## Mental Model

Socho:

```
Parallel = Speed Optimization
```

**Not**:
```
Reasoning Optimization
```

Model wahi reasoning karta hai — tu sirf waiting time reduce kar raha hai.

## Things You Must Remember

- **Sequential**: `A → B → C` — jab dependency exist kare, tab use karo.
- **Parallel**: `A, B, C` saath — jab independent ho, tab use karo.
- **Python**: `asyncio.gather()` main primitive hai.
- **Failure**: `return_exceptions=True` use karo.
- **Limits**: `Semaphore` use karo.
- **Writes**: careful raho — race conditions real hain.