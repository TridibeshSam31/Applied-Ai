# Conflict Resolution & Failure Handling

Multi-agent systems provide multiple perspectives and capabilities, but
multiple agents can also produce conflicting opinions, inconsistent
state updates, and execution failures.

Consider an Event Organizer system:

-   **Venue Agent:** Recommends Venue A for ₹50,000.
-   **Budget Agent:** Rejects Venue A because it exceeds the budget.
-   **Research Agent:** Cannot confirm Venue A's availability.
-   **Supervisor Agent:** Must make a decision using these results.

The system needs explicit conflict-resolution and failure-handling
policies.

------------------------------------------------------------------------

## 1. Types of Conflicts in Multi-Agent Systems

### A. Information Conflict

Two agents provide different answers to the same question.

``` text
Research Agent:
Venue A is available.

Verification Agent:
Venue A is unavailable.
```

**Problem:** Which source is correct? The system needs a way to verify
the information and determine which source has authority.

### B. Decision Conflict

Agents have different objectives.

``` text
Budget Agent:
Choose the cheapest vendor.

Quality Agent:
Choose the highest-rated vendor.
```

Both agents may be correct according to their own objectives, but the
workflow needs one final decision or an explicit trade-off.

### C. State Conflict

Two agents attempt to update the same shared-state field.

``` python
# Agent A
state["status"] = "approved"

# Agent B
state["status"] = "rejected"
```

If both updates happen concurrently, the final value may be
unpredictable or dependent on the orchestration and state-merge
behavior.

### D. Execution Conflict

Two agents attempt to modify the same external resource.

For example:

-   Agent A books Venue A.
-   Agent B simultaneously tries to book Venue A for another event.

This is not merely an LLM reasoning problem. It is also a
distributed-systems problem involving concurrency and resource
consistency.

------------------------------------------------------------------------

## 2. Conflict Resolution Strategies

Not every conflict should be resolved through voting. The appropriate
strategy depends on the type of conflict and the consequences of a wrong
decision.

### 1. Supervisor-Based Resolution

**Best suited to:** Centralized workflows.

A supervisor evaluates the agents' results and makes the final decision.

``` text
        Supervisor
         /      \
     Agent A  Agent B
```

### 2. Voting / Consensus

Multiple agents independently evaluate a result and vote.

Example: Three out of four agents approve a proposed answer.

**Important:** Consensus does not guarantee correctness. If all agents
use the same incorrect data or reasoning, majority voting can still
produce a wrong answer.

### 3. Priority-Based Resolution

Predefined rules determine which source or agent has authority.

Example: A verified booking API overrides an LLM's unsupported
assumption about availability.

### 4. Human-in-the-Loop

**Important for:** High-impact or unresolved decisions.

The system escalates a risky or unresolved decision to a human.

Example: A vendor contract or payment requires human approval.

------------------------------------------------------------------------

## 3. Implementing Conflict Resolution in Python

Let's build a small example in which three agents evaluate a vendor.

### Step 1 --- Define the agents

``` python
def budget_agent(vendor):
    if vendor["price"] <= 50000:
        return {"agent": "budget", "decision": "approve"}

    return {"agent": "budget", "decision": "reject"}


def quality_agent(vendor):
    if vendor["rating"] >= 4.0:
        return {"agent": "quality", "decision": "approve"}

    return {"agent": "quality", "decision": "reject"}


def reliability_agent(vendor):
    if vendor["verified"]:
        return {"agent": "reliability", "decision": "approve"}

    return {"agent": "reliability", "decision": "reject"}
```

### Step 2 --- Create a simple majority-vote supervisor

``` python
def supervisor(results):
    approvals = sum(
        result["decision"] == "approve"
        for result in results
    )

    if approvals >= 2:
        return "APPROVED"

    return "REJECTED"
```

### Step 3 --- Execute the agents

``` python
vendor = {
    "price": 45000,
    "rating": 4.5,
    "verified": False
}

results = [
    budget_agent(vendor),
    quality_agent(vendor),
    reliability_agent(vendor)
]

print(results)
print(supervisor(results))
```

### Expected output

``` text
[
    {'agent': 'budget', 'decision': 'approve'},
    {'agent': 'quality', 'decision': 'approve'},
    {'agent': 'reliability', 'decision': 'reject'}
]

APPROVED
```

But is this a good decision?

Not necessarily. The vendor is unverified. Two positive votes should not
override a mandatory verification requirement.

### Step 4 --- Add a mandatory verification rule

``` python
def supervisor(results):
    decisions = {
        result["agent"]: result["decision"]
        for result in results
    }

    # Mandatory verification rule
    if decisions["reliability"] == "reject":
        return "REJECTED"

    approvals = sum(
        decision == "approve"
        for decision in decisions.values()
    )

    return "APPROVED" if approvals >= 2 else "REJECTED"
```

Now verification has higher priority than a simple majority vote.

> **Production lesson:** Use hard business rules for non-negotiable
> constraints. Do not ask an LLM or a group of agents to vote on whether
> security, authorization, payment, or eligibility rules should be
> followed.

------------------------------------------------------------------------

## 4. Failure Handling --- When an Agent Stops Working

Conflicts are one problem; execution failures are another.

Consider this workflow:

``` text
Supervisor
    |
    ├── Research Agent      SUCCESS
    ├── Venue Agent         SUCCESS
    ├── Catering Agent      FAILED
    └── Budget Agent        WAITING
```

What should happen when the Catering Agent fails?

Five common failure-handling mechanisms are:

  Mechanism         Purpose
  ----------------- -----------------------------------------------
  Retry             Attempt the failed operation again
  Timeout           Stop waiting indefinitely
  Fallback          Use an alternative source or approach
  Circuit breaker   Temporarily stop calling an unhealthy service
  Escalation        Ask a human or higher-level controller

### A. Retry with Exponential Backoff

Suppose an external API temporarily returns an error.

Instead of retrying every millisecond, progressively increase the delay
between attempts.

``` python
import asyncio


async def call_agent(agent, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await agent()

        except Exception as error:
            if attempt == max_retries - 1:
                raise

            delay = 2 ** attempt

            print(f"Retrying in {delay}s: {error}")
            await asyncio.sleep(delay)
```

With `max_retries=3`, this code makes at most three total attempts, with
delays of:

  Retry number     Delay before retry
  -------------- --------------------
  1                          1 second
  2                         2 seconds

In real applications, add **jitter** to prevent many clients from
retrying simultaneously.

Also, do not blindly retry non-idempotent operations. A booking request
might have succeeded on the server even if the response was lost.

### B. Timeout

An agent should not block the workflow forever.

``` python
async def safe_agent(agent):
    try:
        return await asyncio.wait_for(
            agent(),
            timeout=10
        )

    except asyncio.TimeoutError:
        return {
            "status": "failed",
            "reason": "Agent timed out"
        }
```

The workflow can now handle a timeout as an explicit failure result
rather than waiting indefinitely.

### C. Fallback

If the primary research provider fails, use a backup provider.

``` python
async def research_with_fallback():
    try:
        return await primary_research_agent()

    except Exception:
        return await backup_research_agent()
```

A fallback must produce compatible output and provide trustworthy data.
Otherwise, it may simply replace one failure with another.

### D. Circuit Breaker

Suppose a vendor API has failed repeatedly.

Should the system continue sending requests to it?

No. A circuit breaker temporarily blocks requests to an unhealthy
service. After a cooldown, it allows a limited test request to check
whether the service has recovered.

#### Circuit breaker states

  State           Behavior
  --------------- --------------------------------------------------------
  **CLOSED**      Requests are allowed normally.
  **OPEN**        Requests are blocked after failures cross a threshold.
  **HALF-OPEN**   Limited test requests are allowed after a cooldown.

State transitions:

``` text
CLOSED
  |
  | Failure threshold reached
  v
OPEN
  |
  | Cooldown expires
  v
HALF-OPEN
  |
  | Success       | Failure
  v               v
CLOSED            OPEN
```

This is especially useful when agents depend on external APIs or
microservices.

------------------------------------------------------------------------

## 5. Production Architecture

A production workflow can combine orchestration, failure handling,
conflict resolution, and human approval.

``` text
             Supervisor / Orchestrator
              Assigns and monitors tasks
                         |
             +-----------+-----------+
             |                       |
       Research Agent           Vendor Agent
       Retry + timeout          Fallback + timeout
             |                       |
             +-----------+-----------+
                         |
                  Conflict Resolver
               Rules, priorities, consensus
                         |
             Validation / Human Approval
              Validate critical decisions
                         |
                    Final Result
```

The supervisor assigns tasks and monitors execution. Individual agents
use appropriate failure-handling mechanisms. A conflict resolver applies
rules and priorities, while critical decisions can be sent for human
approval before execution.

------------------------------------------------------------------------

## 6. Connection to a Customer Support Agent

These concepts also apply to a single-agent customer support system.

Imagine this sequence:

1.  The LLM requests `create_support_ticket()`.
2.  PostgreSQL experiences a temporary failure.
3.  The tool call fails.
4.  The agent retries the operation.

There is a potential problem: the first request might have created the
ticket even though the response was lost.

If the system blindly retries, it might create duplicate tickets.

### Solution: Idempotency

-   Give the operation a stable idempotency key.
-   Enforce uniqueness in the database.
-   Return the existing ticket when the same operation is repeated.
-   Handle concurrent duplicate requests safely.

This is a backend engineering concept that matters just as much in
agentic systems as it does in distributed systems.

------------------------------------------------------------------------

## 7. Interview Questions

1.  Why is majority voting not always reliable?
2.  What is the difference between retry and fallback?
3.  Explain the three circuit breaker states.
4.  Why should non-idempotent operations not be blindly retried?
5.  When should a multi-agent system escalate to a human?

------------------------------------------------------------------------

## Quick Revision

  -----------------------------------------------------------------------
  Concept                             Core idea
  ----------------------------------- -----------------------------------
  Information conflict                Agents disagree about facts

  Decision conflict                   Agents optimize for different
                                      objectives

  State conflict                      Agents update the same shared-state
                                      field

  Execution conflict                  Agents compete to modify an
                                      external resource

  Supervisor                          Central component evaluates agent
                                      results

  Voting / consensus                  Combines multiple agent decisions

  Priority-based resolution           Applies predefined source or rule
                                      authority

  Human-in-the-loop                   Escalates important decisions

  Retry                               Attempts an operation again

  Timeout                             Limits how long the workflow waits

  Fallback                            Uses an alternative provider or
                                      approach

  Circuit breaker                     Stops calls to an unhealthy
                                      dependency

  Idempotency                         Makes repeated requests safe from
                                      duplicate effects
  -----------------------------------------------------------------------

**Engineering takeaway:** Reliable multi-agent systems need more than
good prompts. They need explicit decision rules, controlled retries,
timeouts, fallbacks, circuit breakers, and idempotent external
operations. Hard business constraints must remain authoritative even
when agents disagree.
