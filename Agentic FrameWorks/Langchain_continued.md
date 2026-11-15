# Agent Frameworks --- Topic 3/10: Models, Prompts and Output Parsers

This topic covers three important LangChain building blocks and how to
combine them into a working customer support analyzer.

In real-world AI applications, sending a prompt to an LLM is not enough.
You need to control:

1.  What instructions the model receives.
2.  How user input is injected.
3.  How conversation history is maintained.
4.  What format the model response should follow.
5.  How the output is safely used by a Python application.

------------------------------------------------------------------------

## 1. Understanding the Three Building Blocks

``` text
Prompt Template
Instructions + dynamic user input
        |
        v
Chat Model
Processes messages and generates a response
        |
        v
Output Parser
Converts output into the required format
        |
        v
Python Application
Uses the result
```

### Prompt Template

Combines instructions with dynamic user input.

### Chat Model

Processes the messages and generates a response.

### Output Parser

Converts model output into a format your application can consume.

------------------------------------------------------------------------

## 2. Prompt Engineering with LangChain

First, understand the three message types.

  Message   Responsibility
  --------- -------------------------------------
  System    Defines the AI's role and behaviour
  Human     Contains the user's input
  AI        Represents the assistant's response

Example:

``` python
messages = [
    ("system", "You are a Python programming tutor."),
    ("human", "Explain decorators in Python."),
    ("ai", "Decorators modify the behaviour of functions.")
]
```

The system message gives instructions. The human message contains the
query. The AI message represents an assistant response.

### What Is a Prompt Template?

Suppose you want to build a technical tutor.

Instead of hardcoding:

``` python
prompt = "Explain Python decorators."
```

You can create a reusable template:

``` python
prompt = "Explain {topic} in {language}."
```

The same template can now work with different inputs.

LangChain provides `ChatPromptTemplate` for this.

### Implementation

``` python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an experienced {role}. "
        "Explain concepts using practical examples."
    ),
    (
        "human",
        "Explain {topic} in {language}."
    )
])

formatted_prompt = prompt.invoke({
    "role": "Python tutor",
    "topic": "Decorators",
    "language": "simple English"
})

print(formatted_prompt)
```

### What happens internally?

The template receives three variables and generates actual messages.

Conceptually, the result is:

``` text
SystemMessage:
You are an experienced Python tutor.
Explain concepts using practical examples.

HumanMessage:
Explain Decorators in simple English.
```

**Important:** `prompt.invoke()` formats the prompt. It does not call
the LLM.

That distinction matters.

------------------------------------------------------------------------

## 3. Connect a Prompt Template with an LLM

Now combine the prompt and model.

``` python
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an experienced programming tutor."),
    ("human", "Explain {topic} with a practical example.")
])

chain = prompt | model

response = chain.invoke({
    "topic": "Python decorators"
})

print(response.content)
```

### What is the `|` symbol?

This is called **LCEL composition using the pipe operator**.

It connects the output of one component to the input of another.

``` text
Prompt Template
       |
       v
     Model
       |
       v
   AIMessage
```

We'll study LCEL properly in Topic 5.

------------------------------------------------------------------------

## 4. Dynamic Conversation History

Imagine your customer support agent.

Customer:

-   Where is my order?
-   Why is it delayed?
-   When will I receive it?

The model needs conversation history to understand what "it" refers to.

For this, LangChain provides `MessagesPlaceholder`.

``` python
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a customer support assistant."
    ),
    MessagesPlaceholder("chat_history", optional=True),
    (
        "human",
        "{question}"
    )
])
```

Invoke it:

``` python
result = prompt.invoke({
    "chat_history": [
        ("human", "Where is my order?"),
        ("ai", "Your order is currently delayed.")
    ],
    "question": "When will it arrive?"
})

print(result)
```

The resulting messages include the system instructions, previous
conversation, and current question.

`MessagesPlaceholder` inserts an existing list of messages into the
prompt.

**Production insight:** Conversation history should not grow
indefinitely. You need a token budget and a strategy for truncation,
summarization, or retrieval.

------------------------------------------------------------------------

## 5. The Problem with Normal LLM Output

Suppose you're building a customer support application.

You ask the LLM:

> Extract the customer's issue, priority, and whether a support ticket
> should be created.

The LLM might respond:

``` text
The customer is experiencing a delayed order.
This should be treated as high priority.
A support ticket is recommended.
```

This looks fine to a human.

But your Python application needs structured information:

``` python
{
    "issue": "Delayed order",
    "priority": "high",
    "create_ticket": True
}
```

This is where output parsers and structured outputs become useful.

------------------------------------------------------------------------

## 6. Output Parsers

An output parser converts model output into a format your application
can consume.

Some useful parsers:

  -----------------------------------------------------------------------
  Parser                              Purpose
  ----------------------------------- -----------------------------------
  `StrOutputParser`                   Extract plain text

  `JsonOutputParser`                  Parse JSON output

  `PydanticOutputParser`              Parse and validate against a
                                      Pydantic schema
  -----------------------------------------------------------------------

### A. `StrOutputParser`

``` python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | model | StrOutputParser()

response = chain.invoke({
    "topic": "PostgreSQL indexing"
})

print(response)
print(type(response))
```

This gives you a string rather than the full `AIMessage` object.

### B. `JsonOutputParser`

``` python
from langchain_core.output_parsers import JsonOutputParser

json_parser = JsonOutputParser()

json_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Return only valid JSON with keys "
        "'issue' and 'priority'."
    ),
    ("human", "{customer_message}")
])

json_chain = json_prompt | model | json_parser

result = json_chain.invoke({
    "customer_message": "My order is 3 days late."
})

print(result)
```

Expected conceptual output:

``` python
{
    "issue": "Delayed order",
    "priority": "high"
}
```

Remember: parsing JSON and validating business correctness are two
different things.

------------------------------------------------------------------------

## 7. Pydantic --- The Important Part

Pydantic is particularly useful for backend engineering.

It allows you to define a schema and validate data against it.

Suppose your customer support agent must return:

-   Issue description
-   Priority
-   Whether a ticket should be created

Define a Pydantic model:

``` python
from pydantic import BaseModel, Field
from typing import Literal


class SupportAnalysis(BaseModel):
    issue: str = Field(
        description="Customer's problem"
    )

    priority: Literal[
        "low",
        "medium",
        "high"
    ]

    create_ticket: bool
```

### Use LangChain's structured output support

``` python
structured_model = model.with_structured_output(
    SupportAnalysis
)

result = structured_model.invoke(
    "My order is 5 days late. Please help."
)

print(result)
print(result.issue)
print(result.priority)
print(result.create_ticket)
```

The model is instructed to produce data conforming to the schema, using
the provider's supported structured-output mechanism.

This is different from simply asking the LLM to write JSON and hoping it
follows your instructions.

The returned result is a validated Pydantic object when the provider
integration supports this mode.

> **Important backend concept:** Pydantic validates the shape and types
> of the output. It does not prove that the model's claims are factually
> correct or that creating a ticket is authorized.

For example, `create_ticket=True` is only an LLM recommendation. Your
backend must independently check order ownership, eligibility, and
authorization before creating anything.

------------------------------------------------------------------------

## 8. Complete Mini-Project: Customer Support Analyzer

Let's combine everything.

### Project structure

``` text
support-analyzer/
│
├── main.py
├── schemas.py
├── prompts.py
└── .env
```

### `schemas.py`

``` python
from pydantic import BaseModel, Field
from typing import Literal


class SupportAnalysis(BaseModel):
    issue: str = Field(
        description="Customer's issue"
    )

    priority: Literal[
        "low",
        "medium",
        "high"
    ]

    create_ticket: bool
```

### `prompts.py`

``` python
from langchain_core.prompts import ChatPromptTemplate

support_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a customer support analyst.
        Analyse the customer's message.
        Identify the problem, assign priority
        and recommend whether a support ticket
        should be created.
        """
    ),
    (
        "human",
        "{customer_message}"
    )
])
```

### `main.py`

``` python
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from prompts import support_prompt
from schemas import SupportAnalysis

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    temperature=0
)

structured_model = model.with_structured_output(
    SupportAnalysis
)

chain = support_prompt | structured_model


def main():
    message = input("Customer message: ")

    result = chain.invoke({
        "customer_message": message
    })

    print("\nSupport Analysis")
    print("----------------")
    print("Issue:", result.issue)
    print("Priority:", result.priority)
    print("Create ticket:", result.create_ticket)


if __name__ == "__main__":
    main()
```

### Example input

``` text
My order has not arrived even though
the delivery date was three days ago.
```

### Example output

``` text
Support Analysis
----------------

Issue: Delayed order
Priority: high
Create ticket: True
```

This is a small but meaningful LLM application: reusable prompts, a
model, structured output, and Pydantic validation.

------------------------------------------------------------------------

## 9. Common Mistakes to Avoid

  -----------------------------------------------------------------------
  Mistake                             Correct understanding
  ----------------------------------- -----------------------------------
  `prompt.invoke()` calls the LLM     It formats the prompt

  Every LLM response is a string      Chat models return message objects

  JSON parsing guarantees valid data  Schema validation is a separate
                                      step

  Pydantic guarantees factual         It validates structure and
  accuracy                            constraints

  Model decides whether an action is  Backend enforces authorization
  authorized                          

  Conversation history can grow       Manage token budgets
  forever                             
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 10. Interview Questions

1.  What is the difference between a `SystemMessage` and a
    `HumanMessage`?
2.  What does `ChatPromptTemplate` do?
3.  Why do we use `MessagesPlaceholder`?
4.  What's the difference between `JsonOutputParser` and
    `PydanticOutputParser`?
5.  What is the difference between parsing JSON and validating
    structured output?
6.  Why is `model.with_structured_output()` useful?
7.  Why should an LLM not directly control sensitive backend actions?

------------------------------------------------------------------------

## Quick Revision

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  `ChatPromptTemplate`                Creates reusable message templates

  `MessagesPlaceholder`               Inserts conversation history

  `prompt.invoke()`                   Formats the prompt into messages

  LCEL `\|`                           Composes components into a pipeline

  `StrOutputParser`                   Extracts plain text

  `JsonOutputParser`                  Parses JSON output

  `Pydantic`                          Validates data against a schema

  `with_structured_output()`          Requests model output conforming to
                                      a schema
  -----------------------------------------------------------------------

**Engineering takeaway:** Structured output makes LLM responses easier
to integrate into backend systems, but valid structure is not the same
as factual correctness or authorization. Always validate business rules
and permissions in your backend.
