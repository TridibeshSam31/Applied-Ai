# Module 5: Agent Evaluation --- Topic 4/7

# LLM-as-a-Judge: Evaluating One AI Agent Using Another LLM

So far, we have studied rule-based metrics and evaluation datasets.

But consider this problem.

**Expected answer:**

> Your order is delayed. A support ticket has been created.

**Actual answer:**

> Unfortunately, your order hasn't arrived yet. I've raised a support
> request to help resolve the delay.

Both answers are semantically correct, but exact string matching may
fail.

So how can we automatically judge the quality of an AI agent's response?

This is where **LLM-as-a-Judge** is useful.

## 1. What Is LLM-as-a-Judge?

LLM-as-a-Judge is an evaluation technique in which one LLM evaluates the
output of another LLM or AI agent.

``` text
             USER QUERY
                 |
                 v
            AI AGENT (A)
                 |
                 v
          GENERATED RESPONSE
                 |
                 v
          EVALUATOR LLM (B)
                 |
                 v
           EVALUATION SCORE
                 |
                 v
          PASS / FAIL + REASON
```

Example --- Agent A:

``` text
Your order ORD123 is delayed.
Your support ticket has been created.
```

Judge B receives:

-   Original user query.
-   Expected outcome.
-   Actual agent response.
-   Relevant tool execution results.

The judge evaluates whether the agent fulfilled the task.

**Important:** Do not give the judge only the actual response. It also
needs sufficient context and trusted evidence.

## 2. Why Do We Need an LLM Judge?

Consider these two responses.

**Response A:**

``` text
Your order is delayed.
```

**Response B:**

``` text
Your order hasn't been delivered yet.
According to the latest order status, it is delayed.
```

If the expected outcome is `delayed`, both responses are potentially
correct.

Rule-based string matching:

``` python
expected = "Your order is delayed."
actual = "Your order hasn't been delivered yet."

print(expected == actual)
```

Output:

``` text
False
```

Semantic evaluation can recognize that the second response communicates
the same fact.

LLM judges are useful for evaluating:

-   Semantic correctness.
-   Relevance.
-   Instruction following.
-   Helpfulness.
-   Completeness.
-   Explanation quality.
-   Open-ended responses.

However, exact database values, authorization decisions, and financial
side effects should still be verified deterministically.

## 3. Evaluation Rubric --- How Should the Judge Evaluate?

Do not simply tell the judge:

``` text
Evaluate this response.
```

That is a vague instruction. Different evaluations may become
inconsistent.

Instead, define a scoring rubric.

  Dimension                 Score Meaning
  ----------------------- ------- -------------------------------------
  Factual correctness        1--5 Does it match trusted evidence?
  Relevance                  1--5 Does it address the query?
  Completeness               1--5 Does it cover required information?
  Clarity                    1--5 Is it understandable?
  Instruction following      1--5 Did it follow requirements?

### Example rubric

**Factual correctness**

-   1: Major factual errors.
-   2: Multiple unsupported claims.
-   3: Partially correct.
-   4: Mostly correct.
-   5: Fully supported by evidence.

**Relevance**

-   1: Completely unrelated.
-   3: Partially addresses the question.
-   5: Directly addresses the request.

A defined rubric makes evaluation more consistent.

## 4. Build Your First LLM Judge

Let's implement a basic evaluator using Python, Pydantic, and LangChain.

Install dependencies:

``` bash
pip install -U langchain langchain-openai pydantic python-dotenv
```

Set your API key in an environment variable, for example
`OPENAI_API_KEY`, and use a model available to your API account.

### Step 1: Define the evaluation schema

File: `evaluation/schemas.py`

``` python
from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    factual_correctness: int = Field(ge=1, le=5)
    relevance: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    instruction_following: int = Field(ge=1, le=5)
    reasoning: str
    passed: bool
```

What is happening?

-   `BaseModel`: Defines the structured output.
-   `ge=1`: Minimum score is 1.
-   `le=5`: Maximum score is 5.
-   `reasoning`: The judge's explanation.
-   `passed`: The judge's final decision.

Pydantic ensures that the returned structure follows the schema. It does
not guarantee that the judge's assessment is correct.

### Step 2: Create the judge prompt

File: `evaluation/judge.py`

``` python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from evaluation.schemas import EvaluationResult


model = ChatOpenAI(
    model="YOUR_AVAILABLE_MODEL",
    temperature=0,
)

judge_model = model.with_structured_output(EvaluationResult)

judge_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are an independent AI evaluator.

        Evaluate the agent's response using:
        1. Factual correctness
        2. Relevance
        3. Completeness
        4. Instruction following

        Use the provided reference evidence.

        Rules:
        - Do not reward unsupported claims.
        - Do not assume missing information.
        - Treat the reference evidence as the source of truth.
        - Evaluate the response against the expected outcome.
        - A response can be concise and still be complete.
        - Do not reward verbosity by itself.
        - Set passed to true only when all critical requirements
          are satisfied and no material factual error exists.

        Return scores from 1 to 5.
        """
    ),
    (
        "human",
        """
        User query:
        {query}

        Expected outcome:
        {expected_outcome}

        Reference evidence:
        {evidence}

        Actual agent response:
        {actual_response}
        """
    ),
])

judge_chain = judge_prompt | judge_model


def evaluate_response(
    query: str,
    expected_outcome: str,
    evidence: str,
    actual_response: str,
) -> EvaluationResult:
    return judge_chain.invoke({
        "query": query,
        "expected_outcome": expected_outcome,
        "evidence": evidence,
        "actual_response": actual_response,
    })
```

Replace `YOUR_AVAILABLE_MODEL` with a model supported by your API
account.

### Step 3: Run the evaluator

File: `evaluation/run_judge.py`

``` python
from evaluation.judge import evaluate_response


result = evaluate_response(
    query="Where is my order ORD123?",
    expected_outcome=(
        "Inform the customer that the order is delayed."
    ),
    evidence=(
        "Database record: ORD123 status = delayed."
    ),
    actual_response=(
        "Your order ORD123 is delayed."
    ),
)

print(result.model_dump())
```

Illustrative output:

``` python
{
    "factual_correctness": 5,
    "relevance": 5,
    "completeness": 5,
    "instruction_following": 5,
    "reasoning": "The response accurately reflects the database status.",
    "passed": True
}
```

The scores are examples, not guaranteed model outputs.

## 5. Weighted Scoring

Not every evaluation dimension has equal importance.

For customer support:

-   Factual correctness: 40%.
-   Relevance: 20%.
-   Completeness: 20%.
-   Instruction following: 20%.

Formula:

\[ S = 0.4F + 0.2R + 0.2C + 0.2I \]

Where:

-   \(F\) = factual correctness.
-   \(R\) = relevance.
-   \(C\) = completeness.
-   \(I\) = instruction following.

Suppose:

  Dimension                 Score
  ----------------------- -------
  Factual correctness           5
  Relevance                     4
  Completeness                  4
  Instruction following         5

\[ S = 0.4(5)+0.2(4)+0.2(4)+0.2(5) \]

\[ S = 4.6/5 \]

`<text>`{=html}Weighted evaluation score: 4.6 / 5 --- 92% of the maximum
weighted score.`</text>`{=html}

But here is an important engineering decision:

**A high average score must not hide a critical failure.**

For example, factual correctness = 1 should probably fail the evaluation
even if all other scores are 5.

Use hard gates for critical dimensions:

``` python
def calculate_score(result):
    score = (
        0.4 * result.factual_correctness
        + 0.2 * result.relevance
        + 0.2 * result.completeness
        + 0.2 * result.instruction_following
    )

    passed = (
        score >= 4.0
        and result.factual_correctness >= 4
        and result.passed
    )

    return {
        "score": round(score, 2),
        "passed": passed,
    }
```

The `passed` field from the judge is still a model judgment. For
critical requirements, combine this with deterministic checks rather
than relying on the judge alone.

## 6. Major Problem: LLM Judge Bias

LLM-as-a-Judge is powerful, but it should not be trusted blindly. There
are several known judge failure modes.

### A. Position Bias

Suppose the judge must compare two responses.

Sometimes it may favor whichever response appears first or second.

Solutions:

-   Randomize response order.
-   Evaluate both orderings.
-   Measure whether the verdict changes.

### B. Verbosity Bias

A judge may give unnecessarily long responses a better score.

Example:

-   Response A: Short, accurate answer.
-   Response B: Long, repetitive answer with unsupported claims.

The judge should evaluate factual evidence instead of length.

### C. Self-Preference Bias

A judge may favor responses that resemble its own writing style or
outputs.

Solutions:

-   Use different models for generation and judging where practical.
-   Validate against human-labelled examples.
-   Compare results across judges.

### D. Prompt Sensitivity

Minor changes to the judge prompt can change its scores.

Solutions:

-   Version-control judge prompts.
-   Maintain fixed calibration examples.
-   Track evaluation changes.

### E. Judge Hallucination

The judge itself may produce incorrect reasoning.

Example --- trusted evidence:

``` text
Order status: delayed
```

Agent:

``` text
Your order is delayed.
```

The judge incorrectly claims that the order is shipped.

This is why ground-truth evidence and independent verification matter.

## 7. Judge Calibration

Calibration means checking whether the judge's decisions agree with
trusted human evaluations.

Suppose humans evaluate 100 responses:

  Result                               Count
  ---------------------------------- -------
  Human says pass, judge says pass        75
  Human says fail, judge says fail        15
  Human says pass, judge says fail         5
  Human says fail, judge says pass         5

Overall agreement:

\[ `\text{Agreement}`{=tex} = `\frac{75+15}{100}`{=tex}`\times100`{=tex}
= 90% \]

But agreement alone is not enough. A judge can achieve misleadingly high
agreement if most cases belong to one class.

Also evaluate:

-   Precision.
-   Recall.
-   False positive rate.
-   False negative rate.
-   Cohen's kappa or another chance-adjusted agreement metric.

For safety-critical failures, false passes deserve particular attention.

**A judge is another ML system. It needs evaluation too.**

## 8. Pointwise vs Pairwise Evaluation

Two common approaches:

### Pointwise Evaluation

Evaluate one response independently.

``` text
Query + Expected Outcome + Response
                 |
                 v
               Judge
                 |
                 v
              Score: 4/5
```

Useful for:

-   Regression testing.
-   Quality scoring.
-   Evaluating large datasets.

### Pairwise Evaluation

Compare two responses for the same query.

``` text
          Same User Query
                |
          +-----+-----+
          |           |
       Agent A     Agent B
          |           |
          +-----+-----+
                |
                v
               Judge
                |
                v
         A wins / B wins / Tie
```

Example:

  Response   Text
  ---------- ---------------------------------------------------
  A          Your order is delayed.
  B          Your order is delayed, and I've created a ticket.

If ticket creation was required and actually succeeded, B is more
complete.

Pairwise evaluation is useful when comparing:

-   Prompt versions.
-   Different models.
-   Agent architectures.
-   Tool-selection strategies.

However, pairwise preference does not prove factual correctness. Both
responses could be wrong.

## 9. Where Should LLM-as-a-Judge Be Used?

  Evaluation problem               Recommended approach
  -------------------------------- --------------------------------------------
  Exact database status            Rule-based
  Correct customer authorization   Backend assertions
  Semantic response quality        LLM judge
  Tool arguments                   Rule-based
  Complex response completeness    LLM judge + reference
  Security violations              Deterministic checks + adversarial testing
  Overall task success             Combined evaluation

**Recommendation: Build a hybrid evaluator.**

``` text
                AGENT RUN
                    |
            +-------+-------+
            |               |
            v               v
       Rule Evaluator   LLM Judge
            |               |
            v               v
       Exact Checks    Quality Scores
            |               |
            +-------+-------+
                    |
                    v
             Final Evaluation
```

Do not use an LLM to check something a simple database assertion can
verify perfectly.

## 10. Practical Assignment

Create five test cases for your customer support agent and evaluate
their final responses using an LLM judge.

Include:

1.  Correct order status.
2.  Incorrect order status.
3.  Unsupported delivery-time claim.
4.  Correct ticket confirmation.
5.  Response that ignores the user's question.

For each case, store:

``` python
{
    "test_case_id": "TC001",
    "judge_scores": {},
    "judge_reasoning": "",
    "human_label": None,
    "final_verdict": None,
}
```

Later, compare human labels against judge verdicts to measure judge
reliability.

------------------------------------------------------------------------

## Core Takeaway

LLM-as-a-Judge helps evaluate semantic response quality, completeness,
relevance, and instruction following when exact matching is too rigid.
But the judge is itself an imperfect model. Ground it in trusted
evidence, define a clear rubric, calibrate it against human labels, and
use deterministic checks for exact facts, permissions, and side effects.
A robust evaluation system is hybrid---not judge-only.
