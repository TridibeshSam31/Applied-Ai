# Parallel vs Sequential Agent Execution

Multi-agent systems are not just about creating multiple agents. They
also require choosing an execution strategy that is efficient and
respects task dependencies.

Consider an event-planning agent receiving this request:

> Organise a college tech fest for 500 students.

Possible tasks:

-   **Venue Agent:** Find venue options.
-   **Catering Agent:** Find food vendors.
-   **Budget Agent:** Estimate the total budget.

Should these agents run one after another or at the same time? The
answer depends on whether their tasks depend on one another.

------------------------------------------------------------------------

## 1. Sequential Execution

In sequential execution, one agent completes its task before the next
agent starts.

### Sequential workflow

1.  **Venue Agent** --- finds venue options.
2.  **Catering Agent** --- finds catering options using venue details.
3.  **Budget Agent** --- calculates the total cost.

**When to use it:** When the next agent depends on the previous agent's
output.

For example, the Budget Agent needs venue and catering prices before it
can calculate the total.

------------------------------------------------------------------------

## 2. Parallel Execution

In parallel-style execution, multiple independent agents execute
concurrently. The workflow waits for their results and then combines
them.

### Parallel workflow

-   **Event Request**
    -   Venue Agent --- finds venues.
    -   Catering Agent --- finds vendors.
    -   Decoration Agent --- finds decorators.
-   **Aggregator** --- combines all results.

**When to use it:** When agents do not depend on one another's outputs.

------------------------------------------------------------------------

## 3. Implementing the Concepts in Python

First, distinguish three terms:

-   **Sequential:** Tasks execute one after another.
-   **Concurrent:** Tasks make progress during overlapping time periods.
-   **Parallel:** Tasks literally execute at the same time, typically on
    multiple CPU cores.

For LLM agents making API calls, concurrency is especially useful
because they spend much of their time waiting for network responses.

### Step 1 --- Create independent agents

``` python
import asyncio

async def venue_agent():
    print("Venue agent started")
    await asyncio.sleep(3)
    return {
        "venue": "Convention Hall",
        "cost": 50000
    }

async def catering_agent():
    print("Catering agent started")
    await asyncio.sleep(2)
    return {
        "vendor": "Food Services",
        "cost": 30000
    }

async def decoration_agent():
    print("Decoration agent started")
    await asyncio.sleep(4)
    return {
        "vendor": "Creative Decor",
        "cost": 20000
    }
```

`asyncio.sleep()` simulates waiting for an external API. It does not
block the entire event loop.

### Step 2 --- Sequential execution

``` python
async def sequential_workflow():
    venue = await venue_agent()
    catering = await catering_agent()
    decoration = await decoration_agent()

    return [venue, catering, decoration]

asyncio.run(sequential_workflow())
```

Approximate total waiting time:

\[ T = 3 + 2 + 4 = 9 `\text{ seconds}`{=tex} \]

Each coroutine is awaited before the next one starts.

### Step 3 --- Concurrent execution with `asyncio.gather()`

``` python
async def parallel_workflow():
    results = await asyncio.gather(
        venue_agent(),
        catering_agent(),
        decoration_agent()
    )
    return results

results = asyncio.run(parallel_workflow())
print(results)
```

Approximate total waiting time:

\[ T `\approx `{=tex}`\max`{=tex}(3, 2, 4) = 4 `\text{ seconds}`{=tex}
\]

**Key insight:** Independent I/O-bound tasks can overlap, allowing the
workflow to finish much faster.

Actual timings vary because of network latency, scheduling, rate limits,
and other overhead.

### Expected output

``` text
Venue agent started
Catering agent started
Decoration agent started

[
    {'venue': 'Convention Hall', 'cost': 50000},
    {'vendor': 'Food Services', 'cost': 30000},
    {'vendor': 'Creative Decor', 'cost': 20000}
]
```

Even if tasks finish in a different order, `asyncio.gather()` returns
results in the same order as the awaitables were supplied.

------------------------------------------------------------------------

## 4. The Real-World Problem: Dependencies

Imagine that the Budget Agent requires all three results.

It cannot execute at the same time as the other agents because its
required inputs do not exist yet.

The correct architecture is a **hybrid workflow**.

### Hybrid execution

1.  Event Request
2.  Venue Agent, Catering Agent, and Decoration Agent execute
    concurrently.
3.  Budget Agent runs after all three results arrive.
4.  Final Event Plan is produced.

### Implementation

``` python
async def budget_agent(results):
    total = sum(item["cost"] for item in results)

    return {
        "total_budget": total
    }


async def event_workflow():
    results = await asyncio.gather(
        venue_agent(),
        catering_agent(),
        decoration_agent()
    )

    budget = await budget_agent(results)

    return {
        "vendors": results,
        "budget": budget
    }


print(asyncio.run(event_workflow()))
```

This pattern is common in multi-agent workflows: perform independent
work concurrently, then execute dependent work after the required
results are available.

------------------------------------------------------------------------

## 5. Production Considerations

The examples above are educational. Production agents need additional
safeguards.

  Problem                          Solution
  -------------------------------- ------------------------------------
  API takes too long               Timeout
  Too many simultaneous calls      Semaphore
  One agent fails                  Explicit failure policy
  API rate limit                   Retry with backoff
  Shared state gets overwritten    Return results and merge centrally
  Results arrive in random order   Use stable task identifiers

### A. Limit concurrent agents

You should not launch 1,000 LLM requests simultaneously.

``` python
semaphore = asyncio.Semaphore(3)

async def limited_agent(agent):
    async with semaphore:
        return await agent()
```

This limits the number of tasks inside the protected section to three at
a time.

### B. Handle failures

By default, `asyncio.gather()` propagates an exception from a failed
task. Other submitted tasks are not automatically cancelled just because
that exception was propagated.

If you need to collect both successes and failures:

``` python
results = await asyncio.gather(
    venue_agent(),
    catering_agent(),
    decoration_agent(),
    return_exceptions=True
)

for result in results:
    if isinstance(result, Exception):
        print("Agent failed:", result)
    else:
        print("Agent result:", result)
```

`return_exceptions=True` does not automatically recover failed agents.
You must decide whether to retry, skip, or abort the workflow.

------------------------------------------------------------------------

## 6. What Happens Inside LangGraph?

The same concepts map to LangGraph:

  Concept                      LangGraph
  ---------------------------- -------------------------
  Agent execution              Node
  Sequential execution         Normal edge
  Parallel execution           Multiple outgoing paths
  Conditional execution        Conditional edge
  Shared workflow data         State
  Combining parallel updates   Reducer

A key detail: if multiple parallel nodes update the same state field,
LangGraph needs an appropriate reducer or a conflict can occur. Do not
assume concurrent state updates automatically merge safely.

------------------------------------------------------------------------

## 7. Interview Questions

1.  What is the difference between concurrency and parallelism?
2.  Why is `asyncio.gather()` useful for LLM agents?
3.  When would sequential execution be better than parallel execution?
4.  What happens if one coroutine fails inside `asyncio.gather()`?
5.  Why might running 100 agents in parallel be a bad design?

------------------------------------------------------------------------

## Quick Revision

  -----------------------------------------------------------------------
  Execution strategy      How it works            Best suited for
  ----------------------- ----------------------- -----------------------
  Sequential              One task runs after     Tasks with dependencies
                          another                 

  Concurrent /            Independent tasks       Independent I/O-bound
  parallel-style          overlap                 tasks

  Hybrid                  Parallel tasks followed Real workflows with
                          by dependent sequential both independent and
                          tasks                   dependent stages
  -----------------------------------------------------------------------

**Engineering takeaway:** Do not parallelise everything blindly.
Identify dependencies first, run independent I/O-bound tasks
concurrently, and combine their results at a controlled point in the
workflow.
