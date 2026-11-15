# Module 5: Agent Evaluation --- Topic 6/7

# Agent Evaluation Frameworks and Experimentation

So far, we have implemented or studied the core evaluation concepts
ourselves:

-   Task success and performance metrics.
-   Golden datasets and test cases.
-   LLM-as-a-Judge.
-   Trajectory and tool evaluation.

But manually implementing every part of evaluation is not practical in
production.

Imagine you have 500 test cases and want to compare three different
agent versions.

You need:

1.  Dataset management.
2.  Execution tracing.
3.  Automated evaluators.
4.  Experiment tracking.
5.  Version comparison.
6.  Regression detection.

This is where evaluation frameworks become useful.

## 1. Important Frameworks

  -----------------------------------------------------------------------
  Framework                           Main focus
  ----------------------------------- -----------------------------------
  LangSmith                           Tracing, dataset management,
                                      experiments and evaluation for
                                      LangChain/LangGraph applications

  Ragas                               Evaluation metrics, datasets and
                                      workflows for RAG and agentic
                                      applications

  OpenAI Evals (legacy platform)      Model/application evaluation using
                                      datasets and graders

  Arize Phoenix                       Tracing, observability, evaluation
                                      and debugging for LLM applications
  -----------------------------------------------------------------------

These frameworks do not all solve exactly the same problem. Some focus
on tracing and experiments, others on specialized evaluation metrics,
and others on model/application evaluation workflows.

## 2. LangSmith --- Tracing, Experiments and Evaluation

`<badge color="success">`{=html}Recommended starting point for
LangGraph`</badge>`{=html}

LangSmith is useful when you want to inspect an agent's complete
execution and compare different versions.

It supports:

-   Dataset management.
-   Target functions.
-   Custom and prebuilt evaluators.
-   LLM-as-a-Judge.
-   Experiment comparison.
-   Offline and online evaluation.
-   Human feedback and annotation.

LangSmith evaluation fundamentally has three components:

``` text
       EVALUATION DATASET
       (Test inputs + references)
                 |
                 v
            TARGET FUNCTION
           (Your AI application)
                 |
                 v
              EVALUATORS
           (Rules / LLM judges)
                 |
                 v
           EXPERIMENT RESULTS
           (Scores + comparisons)
```

This structure is documented in LangSmith's evaluation quickstart.

### A. Dataset

Suppose we have this dataset:

``` python
dataset = [
    {
        "question": "Check ORD123",
        "customer_id": "C101",
        "expected_status": "delayed",
    },
    {
        "question": "Check ORD456",
        "customer_id": "C102",
        "expected_status": "shipped",
    },
]
```

### B. Target Function

A target function is the actual application you want to evaluate.

``` python
def target(inputs: dict) -> dict:
    result = run_customer_support_agent(
        query=inputs["question"],
        customer_id=inputs["customer_id"],
    )

    return {
        "response": result["response"],
        "tool_calls": result["tool_calls"],
    }
```

Here, `run_customer_support_agent()` is your actual agent entry point.

You can evaluate:

-   An individual LLM call.
-   A component.
-   The complete workflow.

### C. Evaluators

Example deterministic evaluator:

``` python
def status_evaluator(
    inputs: dict,
    outputs: dict,
    reference_outputs: dict,
) -> dict:
    expected = reference_outputs["expected_status"]
    actual = outputs["status"]

    return {
        "key": "status_correctness",
        "score": float(actual == expected),
    }
```

This checks an exact status. For this particular evaluation,
deterministic comparison is preferable to asking another LLM whether
`delayed` equals `shipped`.

### D. Experiment Comparison

Suppose you have two agent versions:

  Experiment     Prompt        Task success
  -------------- ----------- --------------
  Experiment A   Prompt v1              78%
  Experiment B   Prompt v2              88%
  Experiment C   Prompt v3              86%

LangSmith lets you compare experiments against datasets and inspect
individual failures, not just aggregate scores.

**Key takeaway:** LangSmith is especially useful when debugging and
comparing agent workflows, including LangGraph applications.

Official guide: [LangSmith Evaluation
Documentation](https://docs.smith.langchain.com/)

## 3. Ragas --- Specialized Evaluation Metrics

Ragas is particularly useful for RAG and agent/tool evaluation.

Ragas provides evaluation metrics for RAG systems, agentic workflows,
tool usage, and general LLM applications.

Its documented agent/tool metrics include:

  Metric                Purpose
  --------------------- -----------------------------------------------
  Tool Call Accuracy    Did the agent make the correct tool call?
  Tool Call F1          Precision/recall-based tool-call evaluation
  Agent Goal Accuracy   Did the agent achieve the requested goal?
  Topic Adherence       Did the agent stay within the intended topic?

It also includes RAG metrics such as:

-   Faithfulness.
-   Context Precision.
-   Context Recall.

### When should you use Ragas?

Suppose you are building a research agent that:

1.  Searches documents.
2.  Retrieves evidence.
3.  Uses tools.
4.  Produces an answer.

Ragas can help evaluate whether:

-   The agent achieved its goal.
-   The correct tools were called.
-   Retrieved context supports the answer.
-   The generated response is factually correct.

Basic installation:

``` bash
pip install ragas
```

**Important:** Ragas has evolved its APIs, metrics, and dataset
abstractions. Do not blindly copy old tutorials using legacy imports.
Start with the current stable documentation and choose metrics based on
your actual evaluation task.

Official guide: [Ragas Documentation](https://docs.ragas.io/)

## 4. OpenAI Evals --- Important 2026 Status

`<badge color="warning">`{=html}Legacy platform --- check migration
status`</badge>`{=html}

The legacy OpenAI Evals platform has supported:

-   String checks.
-   Text similarity.
-   Model-based graders.
-   Python code graders.
-   Evaluation datasets and runs.

However, the source material states that the current official
documentation has announced deprecation of the legacy Evals platform:

-   October 31, 2026: Existing Evals become read-only.
-   November 30, 2026: Platform shutdown is scheduled.

**As of November 15, 2026**, the recommendation in these notes is not to
start a new project on the legacy OpenAI Evals platform.

Relevant official references:

-   Agent evaluation guidance.
-   Evaluation best practices.

Distinguish the legacy Evals platform from broader evaluation concepts
and trace-based workflows described in OpenAI's documentation.

## 5. Arize Phoenix --- Observability and Evaluation

Arize Phoenix focuses on understanding what is happening inside LLM
applications.

Useful capabilities include:

-   Tracing LLM calls.
-   Inspecting tool execution.
-   Reviewing intermediate steps.
-   Evaluating outputs.
-   Debugging failures.
-   Integrating with common LLM frameworks.

Example:

``` text
Agent Run
   |
   +---- LLM Call
   |
   +---- Tool Call
   |
   +---- Database Query
   |
   +---- Final Response
              |
              v
          Phoenix Trace
              |
              v
        Inspect & Evaluate
```

Phoenix is useful when you want observability and evaluation in a system
that is not necessarily built using LangChain or LangGraph.

Documentation: [Arize Phoenix
Documentation](https://arize.com/docs/phoenix)

## 6. Framework Comparison

  -----------------------------------------------------------------------
  Framework               Main strength           Best use
  ----------------------- ----------------------- -----------------------
  LangSmith               Tracing and experiment  LangGraph / LLM
                          management              workflows

  Ragas                   Specialized evaluation  RAG and agent/tool
                          metrics                 evaluation

  OpenAI legacy Evals     Model/application       Existing legacy eval
                          graders                 workflows

  Arize Phoenix           Observability and       Debugging and tracing
                          evaluation              
  -----------------------------------------------------------------------

### Recommended learning path

**Primary: LangSmith**

Use it to inspect traces, manage datasets, and compare agent versions.

**Secondary: Ragas**

Use it to explore specialized agent and tool metrics.

**Additional: Custom Python evaluators**

Use deterministic assertions for business rules, authorization, database
results, and side effects.

Do not try to master all four simultaneously. Understanding evaluation
principles is more valuable than collecting framework names.

## 7. Build a Repeatable Experiment Workflow

This is the most important practical concept in this lesson.

Suppose you want to improve your customer support agent.

You have three hypotheses:

-   **H1:** A better system prompt will improve tool selection.
-   **H2:** A stronger model will improve response accuracy.
-   **H3:** Limiting unnecessary tool calls will reduce latency and
    cost.

You need a repeatable experiment.

``` text
              GOLDEN DATASET
                  |
           +------+-------+
           |      |       |
           v      v       v
        Agent A Agent B Agent C
        Prompt  New     Optimized
        v1      Model   Routing
           |      |       |
           v      v       v
        Evaluate Evaluate Evaluate
           |      |       |
           +------+-------+
                  |
                  v
           COMPARE METRICS
                  |
                  v
             ERROR ANALYSIS
                  |
                  v
             SELECT WINNER
                  |
                  v
             REGRESSION TEST
```

### Example experiment results

These numbers are hypothetical:

  Metric                Agent A   Agent B   Agent C
  ------------------- --------- --------- ---------
  Task success              78%       88%       90%
  Tool accuracy             85%       91%       94%
  P95 latency              4.2s      5.1s      3.8s
  Cost/task             \$0.010   \$0.018   \$0.012
  Safety violations           0         0         0

Which agent wins?

Agent C appears strongest in this example: it has the highest task
success and tool accuracy, lower latency than A and B, and no observed
safety violations.

But do not make a production decision based only on aggregate numbers.
Check:

-   Number of test cases.
-   Statistical uncertainty.
-   Performance across different test categories.
-   Severity of individual failures.
-   Whether all experiments used the same dataset and conditions.

## 8. Implement a Basic Experiment Runner Yourself

Frameworks automate many parts of this workflow, but you should
understand the underlying engineering.

### Project structure

``` text
agent-evaluation/
│
├── datasets/
│   └── customer_support.json
│
├── evaluators/
│   ├── task_evaluator.py
│   └── tool_evaluator.py
│
├── experiments/
│   └── runner.py
│
└── results/
```

### Step 1: Define two agent versions

For demonstration, use mock agents. These are not real LLM agents.

``` python
def agent_v1(query):
    return {
        "status": "delayed",
        "tool": "get_order_status",
    }


def agent_v2(query):
    return {
        "status": "delayed",
        "tool": "get_order_status",
    }
```

### Step 2: Define the evaluator

``` python
def evaluate_agent(agent, dataset):
    passed = 0
    results = []

    for case in dataset:
        output = agent(case["input"])

        task_correct = (
            output["status"] == case["expected_status"]
        )

        tool_correct = (
            output["tool"] == case["expected_tool"]
        )

        success = task_correct and tool_correct

        if success:
            passed += 1

        results.append({
            "id": case["id"],
            "success": success,
        })

    score = passed / len(dataset) if dataset else 0

    return {
        "task_success_rate": score * 100,
        "results": results,
    }
```

### Step 3: Run experiments

``` python
dataset = [
    {
        "id": "TC001",
        "input": "Check ORD123",
        "expected_status": "delayed",
        "expected_tool": "get_order_status",
    },
    {
        "id": "TC002",
        "input": "Check ORD456",
        "expected_status": "shipped",
        "expected_tool": "get_order_status",
    },
]

experiments = {
    "agent_v1": agent_v1,
    "agent_v2": agent_v2,
}

for name, agent in experiments.items():
    result = evaluate_agent(agent, dataset)
    print(name, result["task_success_rate"])
```

This is a tiny evaluation harness.

For a real implementation, the agent output must come from your actual
application. You would also record:

-   Model and prompt versions.
-   Tool-call traces.
-   Token usage and cost.
-   Latency.
-   Evaluator versions.
-   Dataset version.
-   Failure details.

If the model is nondeterministic, repeat runs where appropriate.

## 9. Offline vs Online Evaluation

Another important framework concept.

### Offline Evaluation

You run a fixed dataset against your agent before deployment.

``` text
Golden Dataset
      |
      v
   Agent v2
      |
      v
  Evaluators
      |
      v
   Pass / Fail
```

Purpose:

-   Benchmarking.
-   Regression testing.
-   Prompt comparisons.
-   Model selection.

### Online Evaluation

You evaluate actual production interactions.

``` text
Real User
    |
    v
Production Agent
    |
    v
Execution Trace
    |
    v
Online Evaluator
    |
    v
Monitoring & Review
```

Purpose:

-   Detect real-world failures.
-   Find unexpected input patterns.
-   Monitor quality changes.
-   Identify emerging edge cases.

LangSmith supports both offline and online evaluation workflows.

**Strong engineering practice:** Run offline evaluation before
deployment and online monitoring after deployment.

## 10. Framework Selection Exercise

Suppose you are building three systems:

  System   What are you building?
  -------- ------------------------------------------------------------
  A        LangGraph customer support agent
  B        RAG application with document retrieval
  C        Framework-independent agent where you need detailed traces

Suggested choices:

-   **A → LangSmith**
-   **B → Ragas**
-   **C → Arize Phoenix**

These are recommendations, not hard restrictions. Their capabilities
overlap, and you can combine them.

------------------------------------------------------------------------

## Core Takeaway

Evaluation frameworks help operationalize the principles we have
learned: datasets, traces, evaluators, experiments, and regression
checks. Choose tools based on the problem rather than trying to use
every framework. For a LangGraph-based learning project, start with
LangSmith, add Ragas when specialized RAG or agent metrics are needed,
and retain custom deterministic checks for business-critical behavior.
