# Module 5: Agent Evaluation --- Topic 7/7

# Production Agent Evaluation: Monitoring, Regression Testing and CI/CD

This is the final topic of the Agent Evaluation module.

So far, we have covered:

1.  Evaluation fundamentals.
2.  Evaluation metrics.
3.  Dataset and test-case design.
4.  LLM-as-a-Judge.
5.  Trajectory and tool evaluation.
6.  Evaluation frameworks and experimentation.

Now we connect these concepts to production engineering.

**Core question:** Your agent is 95% accurate in development. How do you
ensure it remains reliable after deployment?

The answer is **continuous evaluation**.

## 1. Offline Evaluation vs Online Evaluation

### Offline Evaluation

You test the agent against a fixed dataset before deployment.

``` text
Golden Dataset
      |
      v
 Agent Version
      |
      v
  Evaluators
      |
      v
Evaluation Report
      |
      v
Deployment Decision
```

### Online Evaluation

You monitor and evaluate actual user interactions in production.

``` text
Real User Requests
       |
       v
 Production Agent
       |
       v
 Execution Traces
       |
       v
 Online Evaluation
       |
       v
 Monitoring Dashboard
       |
       v
 Alerts / Investigation
```

  Offline                   Online
  ------------------------- --------------------------------
  Fixed dataset             Real interactions
  Pre-deployment testing    Post-deployment monitoring
  Reproducible conditions   Variable real-world conditions
  Regression detection      Production issue detection

Both are required. Offline evaluation alone cannot guarantee real-world
behavior.

## 2. Production Monitoring --- What Should We Monitor?

Tracking only task success rate is insufficient in production.

Divide metrics into four groups.

### A. Quality Metrics

-   Task success rate.
-   Response correctness.
-   Tool selection accuracy.
-   Hallucination rate.
-   Human escalation rate.

### B. Performance Metrics

-   Average latency.
-   P95/P99 latency.
-   Tool execution latency.
-   Timeout rate.

### C. Cost Metrics

-   Input tokens.
-   Output tokens.
-   LLM cost per request.
-   Cost per successful task.

### D. Safety and Reliability

-   Unauthorized tool attempts.
-   Policy violations.
-   Duplicate side effects.
-   Failed executions.
-   Retry rate.

### Illustrative Production Dashboard

  Metric           Example value
  -------------- ---------------
  Task success               91%
  Tool success               97%
  P95 latency               3.2s
  Cost / task            \$0.012

These are illustrative values, not live measurements or production
benchmarks.

## 3. Tracing --- The Foundation of Production Debugging

Monitoring tells you **what** problem occurred. Tracing helps you
understand **where** it occurred.

Suppose a user reports:

> My support ticket was never created.

You only have the final response log:

``` text
Your support ticket has been created.
```

This is not enough to identify the actual problem.

But if you have a complete trace:

``` text
RUN-101
  |
  v
Agent Node              SUCCESS
  |
  v
get_order_status        SUCCESS
  |
  v
Eligibility Check       SUCCESS
  |
  v
create_support_ticket   FAILED
  |
  v
Agent Node              SUCCESS
  |
  v
Final Response          INCORRECT
```

Now you can identify that ticket creation failed, but the agent still
returned a false confirmation.

### Trace vs Span

-   **Trace:** The complete execution record for one request.
-   **Span:** An individual operation within that request.

Example:

``` text
Trace: customer-support-request
│
├── Span: agent_reasoning
│
├── Span: get_order_status
│
├── Span: database_query
│
├── Span: create_support_ticket
│
└── Span: final_response
```

OpenTelemetry is useful for production tracing.

Documentation: [OpenTelemetry
Tracing](https://opentelemetry.io/docs/concepts/signals/traces/)

**Security rule:** Do not log API keys, authentication tokens,
passwords, or unnecessary personal data in traces. Redact sensitive
fields.

## 4. Regression Testing --- What to Check After an Agent Update

Suppose Agent v1 successfully completes 90% of tasks.

You improve the system prompt and release Agent v2.

New results:

  Metric                  v1     v2
  ------------------- ------ ------
  Task success           90%    94%
  Tool accuracy          92%    96%
  P95 latency           3.0s   4.5s
  Safety violations        0      2

Is v2 better?

**Not necessarily.** Overall quality improved, but safety violations
were introduced and latency also increased.

Regression testing ensures that new changes do not break existing
functionality.

Common changes that require regression tests:

-   System prompt modification.
-   Model upgrade.
-   Tool schema modification.
-   New tool introduction.
-   Database schema changes.
-   LangGraph workflow changes.
-   Memory or checkpointing changes.

### Regression Test Workflow

``` text
             Code Change
                  |
                  v
              Run Tests
                  |
                  v
           Run Golden Dataset
                  |
                  v
            Compare Results
                  |
           +------+------+
           |             |
           v             v
         PASS           FAIL
           |             |
           v             v
         Deploy     Block Release
```

**Important:** Keep adding newly discovered failure cases to the golden
dataset. Otherwise, the evaluation dataset becomes outdated.

## 5. CI/CD Integration for Agent Evaluation

Suppose you push code to GitHub.

A normal CI pipeline might look like this:

``` text
Git Push
   |
   v
Install Dependencies
   |
   v
Run Unit Tests
   |
   v
Run Integration Tests
   |
   v
Build Application
   |
   v
Deploy
```

For an agent application, add evaluation and regression stages:

``` text
Git Push
   |
   v
Unit Tests
   |
   v
Integration Tests
   |
   v
Agent Evaluation
   |
   v
Regression Checks
   |
   v
Quality Gates
   |
   +---- PASS ----> Deploy
   |
   +---- FAIL ----> Block Deployment
```

### Example GitHub Actions Pipeline

File: `.github/workflows/agent-evaluation.yml`

``` yaml
name: Agent Evaluation

on:
  pull_request:
  push:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run unit tests
        run: |
          pytest tests/unit

      - name: Run agent evaluation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python -m evaluation.run

      - name: Check evaluation thresholds
        run: |
          python -m evaluation.quality_gate
```

This workflow assumes your repository has those test directories and
Python modules. You need to implement them; GitHub Actions will not
automatically know how to evaluate your agent.

### What Is a Quality Gate?

A quality gate is a set of predefined criteria that must be satisfied
before deployment.

Example:

``` python
def quality_gate(metrics):
    assert metrics["task_success_rate"] >= 90
    assert metrics["tool_accuracy"] >= 95
    assert metrics["safety_violations"] == 0
    assert metrics["p95_latency"] <= 5.0

    print("Evaluation passed")
```

The thresholds above are illustrative. Real thresholds should be
established from your baseline, business requirements, sample size, and
risk level.

**Important:** Safety violations should not be hidden by a high average
score. Treat critical safety failures as hard deployment blockers.

## 6. Online Evaluation and Production Feedback Loops

Offline tests cannot cover every possible user request.

Production users will create new scenarios that your original dataset
never anticipated.

Example:

``` text
User: My order was marked delivered,
but I never received it.
```

Perhaps your original dataset tested only delayed and shipped orders.
This new interaction can reveal a missing scenario.

A good feedback loop:

``` text
         REAL USER INTERACTIONS
                  |
                  v
           Collect Execution Traces
                  |
                  v
           Evaluate / Human Review
                  |
                  v
           Identify Failure Patterns
                  |
                  v
           Create New Test Cases
                  |
                  v
           Update Evaluation Dataset
                  |
                  v
           Improve Agent
                  |
                  v
           Regression Evaluation
                  |
                  v
                New Release
```

This is how evaluation becomes continuous instead of a one-time
activity.

### Human Feedback

You can collect:

-   User thumbs up/down.
-   Support-team review.
-   Human-labelled correct/incorrect responses.
-   Escalation outcomes.
-   Confirmed task completion.

But remember: a user giving a thumbs-up does not necessarily mean the
agent's database action was correct. User feedback is one signal, not
ground truth for every metric.

## 7. Canary Releases and Rollback

Suppose Agent v2 passed offline evaluation.

Should you immediately route 100% of users to it?

Not necessarily. Use a canary release.

``` text
               Production Traffic
                     |
                +----+----+
                |         |
                v         v
             Agent v1   Agent v2
               95%        5%
                |         |
                +----+----+
                     |
                     v
               Compare Metrics
                     |
                +----+----+
                |         |
                v         v
             Healthy   Degraded
                |         |
                v         v
         Increase Traffic Rollback
```

Canary releases help detect problems that offline tests missed.

Monitor:

-   Task success.
-   Error rates.
-   Latency.
-   Cost.
-   Safety incidents.

For agent systems, do not compare only aggregate averages. Break metrics
down by task category, tool, and severity.

## 8. Production Evaluation Architecture

Connect everything into one architecture:

``` text
                 USER
                   |
                   v
              FASTAPI BACKEND
                   |
                   v
              AGENT WORKFLOW
                   |
           +-------+-------+
           |               |
           v               v
        LLM Calls       Tool Calls
           |               |
           +-------+-------+
                   |
                   v
               TRACE STORE
                   |
             +-----+-----+
             |           |
             v           v
        Online Metrics Human Review
             |           |
             +-----+-----+
                   |
                   v
             EVALUATION SYSTEM
                   |
             +-----+-----+
             |           |
             v           v
        Quality Reports New Test Cases
                         |
                         v
                    GOLDEN DATASET
                         |
                         v
                  OFFLINE EVALUATION
                         |
                         v
                     CI/CD GATE
                         |
                         v
                      DEPLOYMENT
```

This is the architecture of a continuous evaluation system.

## 9. Production Evaluation Checklist

Use this checklist whenever you release a new agent version.

-   [ ] Golden dataset is version-controlled.
-   [ ] Unit and integration tests pass.
-   [ ] Tool arguments and permissions are tested.
-   [ ] Trajectory evaluation is completed.
-   [ ] LLM judge is calibrated.
-   [ ] Task success threshold is met.
-   [ ] Critical safety violations are zero.
-   [ ] Latency and cost limits are met.
-   [ ] Production traces redact sensitive data.
-   [ ] Rollback strategy is ready.

## 10. Practical Project: Build a Production Agent Evaluation Pipeline

For this entire module, build a small **Agent Evaluation Pipeline**.

### Suggested Project Structure

``` text
agent-evaluation/
│
├── app/
│   └── customer_support_agent.py
│
├── datasets/
│   ├── golden.jsonl
│   └── adversarial.jsonl
│
├── evaluators/
│   ├── task_success.py
│   ├── tool_accuracy.py
│   ├── trajectory.py
│   └── llm_judge.py
│
├── experiments/
│   └── runner.py
│
├── monitoring/
│   └── metrics.py
│
├── tests/
│   └── test_regression.py
│
└── .github/
    └── workflows/
        └── agent-evaluation.yml
```

Your final system should be able to:

1.  Run an agent against a golden dataset.
2.  Record execution traces.
3.  Evaluate tool calls and trajectories.
4.  Use an LLM judge for qualitative evaluation.
5.  Calculate task success, latency, and cost.
6.  Compare two agent versions.
7.  Fail CI when critical quality gates are violated.

This is a much stronger engineering exercise than simply learning the
names of evaluation frameworks.

------------------------------------------------------------------------

## Final Takeaway

Production agent evaluation is not a one-time benchmark. It is a
continuous engineering loop:

**Evaluate before deployment → Monitor after deployment → Investigate
failures → Add test cases → Improve → Re-evaluate → Release safely.**

The goal is not merely to build an agent that performs well once. The
goal is to build a system whose behavior remains measurable, debuggable,
and reliable as prompts, models, tools, data, and user behavior change.
