# Agent Frameworks --- Topic 5/10

## Chains, Runnables and LCEL

LangChain's **LCEL (LangChain Expression Language)** lets you connect
components into reusable execution pipelines. In the previous topic, we
implemented tool calling. Here, we will learn how to compose multiple
LangChain components and understand the execution interfaces behind
them.

The familiar syntax is:

``` python
chain = prompt | model | parser
```

The pipe operator connects the output of one component to the input of
the next.

------------------------------------------------------------------------

## 1. What is a Chain?

A **chain** is a sequence of components connected together to perform a
task.

Example: a technical interview assistant.

1.  The user provides a topic.
2.  A prompt template prepares the model instructions.
3.  The LLM generates a response.
4.  An output parser converts the response into plain text.

### Execution flow

``` text
User input
   |
   v
Prompt template
   |
   v
LLM
   |
   v
Output parser
   |
   v
Final output
```

Without a chain, you manually call each component and pass its output to
the next one. With LCEL, you compose them into a single reusable
pipeline.

## 2. What is LCEL?

**LCEL** stands for **LangChain Expression Language**. It provides a
declarative way to compose LangChain components using the pipe operator
(`|`).

``` python
chain = prompt | model | parser
```

Think of it as a pipeline:

``` text
A  --->  B  --->  C
```

-   A produces output.
-   B receives A's output and produces another output.
-   C receives B's output.

This is similar to Unix pipes, where the output of one operation becomes
the input of the next.

## 3. First LCEL implementation

Let's implement a simple technical tutor.

Install the packages:

``` bash
pip install -U langchain langchain-openai python-dotenv
```

Create `main.py`:

``` python
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# 1. Initialize the model
model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    temperature=0,
)

# 2. Create the prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an experienced backend engineering tutor."),
    ("human", "Explain {topic} with a real-world example."),
])

# 3. Create the parser
parser = StrOutputParser()

# 4. Compose the chain
chain = prompt | model | parser

# 5. Execute the chain
result = chain.invoke({"topic": "PostgreSQL indexing"})
print(result)
```

### Execution contracts

  Stage    Input           Output
  -------- --------------- ------------------------------
  Prompt   Dictionary      Chat messages / prompt value
  Model    Chat messages   `AIMessage`
  Parser   `AIMessage`     String

**Key point:** Each component has an input and output contract. LCEL
connects compatible components.

## 4. What is a Runnable?

A **Runnable** is a common interface that LangChain components implement
so they can be executed and composed consistently.

Many LangChain components are Runnables:

-   Chat models
-   Prompt templates
-   Output parsers
-   Runnable sequences
-   Runnable parallel operations
-   Custom functions wrapped as Runnables

A Runnable commonly supports these methods:

  Method        Purpose
  ------------- ----------------------------------------
  `invoke()`    Execute one input
  `ainvoke()`   Execute asynchronously
  `batch()`     Execute multiple inputs
  `abatch()`    Execute multiple inputs asynchronously
  `stream()`    Stream output chunks
  `astream()`   Asynchronously stream output chunks

### A. `invoke()`

Executes the pipeline for one input.

``` python
result = chain.invoke({"topic": "Redis"})
print(result)
```

### B. `batch()`

Use `batch()` when you want to run the same pipeline for multiple
inputs.

``` python
results = chain.batch([
    {"topic": "Redis"},
    {"topic": "RabbitMQ"},
    {"topic": "PostgreSQL"},
])

for result in results:
    print(result)
```

Instead of calling `invoke()` separately for every input, `batch()`
accepts a collection of inputs.

### C. `stream()`

`stream()` yields output chunks progressively.

``` python
for chunk in chain.stream({"topic": "Microservices"}):
    print(chunk, end="", flush=True)
```

This streams the final chain output progressively.

### D. `ainvoke()`

Use `ainvoke()` when integrating the chain into an asynchronous
application.

``` python
import asyncio

async def main():
    result = await chain.ainvoke({"topic": "WebSockets"})
    print(result)

asyncio.run(main())
```

**Important:** These methods provide execution interfaces. They do not
guarantee that every underlying model provider supports every feature in
exactly the same way.

## 5. RunnableSequence

When you write:

``` python
chain = prompt | model | parser
```

LangChain composes the components into a sequential Runnable pipeline.

Conceptually, the same composition can be expressed explicitly:

``` python
from langchain_core.runnables import RunnableSequence

chain = RunnableSequence(
    prompt,
    model,
    parser,
)
```

Both approaches represent sequential composition. The pipe syntax is
more convenient.

### What happens internally?

``` text
Input dictionary
      |
      v
ChatPromptTemplate
      |
      v
ChatPromptValue
      |
      v
ChatOpenAI
      |
      v
AIMessage
      |
      v
StrOutputParser
      |
      v
Python string
```

Notice how the data type changes at each stage. This is why
understanding input and output contracts matters.

## 6. RunnableParallel

Imagine that your application needs to perform two independent tasks on
the same input:

-   Generate a short explanation.
-   Generate interview questions.

These tasks do not depend on each other's results, so they can be run
concurrently. `RunnableParallel` is designed for this kind of
composition.

### Implementation

``` python
from langchain_core.runnables import RunnableParallel

# Explanation prompt
explanation_prompt = ChatPromptTemplate.from_template(
    "Explain {topic} with a practical example."
)

# Interview prompt
interview_prompt = ChatPromptTemplate.from_template(
    "Generate 3 interview questions about {topic}."
)

# Two independent chains
explanation_chain = (
    explanation_prompt
    | model
    | StrOutputParser()
)

interview_chain = (
    interview_prompt
    | model
    | StrOutputParser()
)

# Run both branches concurrently
parallel_chain = RunnableParallel(
    explanation=explanation_chain,
    questions=interview_chain,
)

result = parallel_chain.invoke({
    "topic": "PostgreSQL indexing"
})

print("EXPLANATION:")
print(result["explanation"])

print("\nINTERVIEW QUESTIONS:")
print(result["questions"])
```

The output has this structure:

``` python
{
    "explanation": "...",
    "questions": "...",
}
```

Both branches receive the same input dictionary. They execute
concurrently, and their results are collected into one dictionary.

**Production consideration:** Two model calls mean two API requests.
Parallel execution can reduce latency, but it can also increase
simultaneous API usage and cost. Apply concurrency limits where
necessary.

## 7. RunnableLambda --- connecting your own Python functions

Sometimes you need custom processing after a model response, such as:

-   Counting words
-   Removing unnecessary whitespace
-   Transforming output
-   Applying business logic

You can convert an ordinary Python function into a Runnable using
`RunnableLambda`.

``` python
from langchain_core.runnables import RunnableLambda

def count_words(text: str):
    return {
        "text": text,
        "word_count": len(text.split()),
    }

word_counter = RunnableLambda(count_words)

result = word_counter.invoke(
    "LangChain helps developers build LLM applications"
)

print(result)
```

Expected output:

``` python
{
    "text": "LangChain helps developers build LLM applications",
    "word_count": 7,
}
```

You can also connect it to a model pipeline:

``` python
analysis_chain = (
    prompt
    | model
    | StrOutputParser()
    | RunnableLambda(count_words)
)
```

Now the chain generates text and then performs custom Python processing.

## 8. RunnablePassthrough --- passing data forward

Sometimes you want to preserve the original input while also generating
additional information.

`RunnablePassthrough` passes its input through unchanged.

``` python
from langchain_core.runnables import RunnablePassthrough

passthrough = RunnablePassthrough()

result = passthrough.invoke({
    "topic": "Redis",
    "level": "beginner",
})

print(result)
```

Output:

``` python
{
    "topic": "Redis",
    "level": "beginner",
}
```

It becomes particularly useful with `RunnableParallel` and
`RunnablePassthrough.assign()`.

### `RunnablePassthrough.assign()`

This allows you to preserve existing dictionary fields and add newly
computed fields.

``` python
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

chain = RunnablePassthrough.assign(
    word_count=RunnableLambda(
        lambda data: len(data["text"].split())
    )
)

result = chain.invoke({
    "text": "AI agents can use external tools"
})

print(result)
```

Output:

``` python
{
    "text": "AI agents can use external tools",
    "word_count": 7,
}
```

This is useful when you need to enrich an existing state-like dictionary
without discarding its original fields.

## 9. RunnableBranch --- conditional execution

What if your application should execute different chains depending on
the input?

Example:

-   Beginner → simple explanation
-   Advanced → technical explanation

`RunnableBranch` supports conditional routing.

``` python
from langchain_core.runnables import RunnableBranch

beginner_chain = (
    ChatPromptTemplate.from_template(
        "Explain {topic} in very simple terms."
    )
    | model
    | StrOutputParser()
)

advanced_chain = (
    ChatPromptTemplate.from_template(
        "Explain {topic} with advanced technical details."
    )
    | model
    | StrOutputParser()
)

branch = RunnableBranch(
    (
        lambda x: x["level"] == "beginner",
        beginner_chain,
    ),
    advanced_chain,  # Default branch
)

result = branch.invoke({
    "topic": "Redis",
    "level": "beginner",
})

print(result)
```

The first matching condition determines the selected branch. The last
Runnable is the default branch.

This is conditional routing --- a concept that becomes especially useful
when studying LangGraph.

## 10. Putting everything together

The following example combines parallel chains and custom
post-processing into one pipeline.

``` python
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Assumes `model` has already been initialized.

parser = StrOutputParser()

# Branch 1: Explain the topic
explanation = (
    ChatPromptTemplate.from_template(
        "Explain {topic} for a backend engineer."
    )
    | model
    | parser
)

# Branch 2: Generate interview questions
questions = (
    ChatPromptTemplate.from_template(
        "Generate 3 interview questions about {topic}."
    )
    | model
    | parser
)

# Execute both branches concurrently
parallel = RunnableParallel(
    explanation=explanation,
    questions=questions,
)

# Add custom processing
def summarize_output(data):
    return {
        "explanation": data["explanation"],
        "questions": data["questions"],
        "explanation_words": len(
            data["explanation"].split()
        ),
    }

final_chain = (
    parallel
    | RunnableLambda(summarize_output)
)

result = final_chain.invoke({
    "topic": "PostgreSQL indexing"
})

print(result)
```

### Components used

-   `ChatPromptTemplate`
-   `ChatOpenAI`
-   `StrOutputParser`
-   `RunnableParallel`
-   `RunnableLambda`
-   `RunnableSequence` through the pipe operator

This demonstrates how LCEL composition can turn smaller components into
a more capable pipeline.

## 11. Important concepts for production

  -----------------------------------------------------------------------
  Concept                             What to remember
  ----------------------------------- -----------------------------------
  `RunnableSequence`                  Executes components sequentially

  `RunnableParallel`                  Runs independent branches
                                      concurrently

  `RunnableLambda`                    Wraps custom Python logic

  `RunnablePassthrough`               Passes input through unchanged

  `RunnablePassthrough.assign()`      Adds computed fields while
                                      preserving existing dictionary
                                      fields

  `RunnableBranch`                    Routes inputs conditionally
  -----------------------------------------------------------------------

### Three warnings

1.  Parallel branches should not independently mutate the same shared
    object.
2.  Parallel model calls can hit API rate limits and increase cost.
3.  A chain is not automatically an autonomous agent. A chain can be
    completely deterministic, with no model-driven tool selection or
    planning.

## 12. Interview questions

1.  What is LCEL and why does LangChain use it?
2.  What is the difference between `RunnableSequence` and
    `RunnableParallel`?
3.  What does `RunnableLambda` do?
4.  Why would you use `RunnablePassthrough.assign()`?
5.  How does `RunnableBranch` work?
6.  Is every LangChain chain an AI agent?
7.  What happens if one branch of a `RunnableParallel` fails?

------------------------------------------------------------------------

## Engineering takeaway

Think in terms of **contracts and composition**:

-   Each Runnable accepts an input and returns an output.
-   Sequential composition connects one output to the next component.
-   Parallel composition runs independent work and collects the results.
-   Lambda and passthrough components let you integrate ordinary
    application logic.
-   Branches introduce conditional routing.

A well-composed chain is reusable and testable, but it is not
automatically an agent. Keep business rules, validation, authorization,
and side-effect control in your application code.
