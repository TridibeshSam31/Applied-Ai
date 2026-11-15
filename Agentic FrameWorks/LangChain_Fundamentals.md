# Agent Frameworks --- Topic 2/10: LangChain Fundamentals

This topic introduces LangChain's core building blocks and shows how to
create a working LLM application using Python and OpenAI.

An important distinction: **LangChain is not an LLM.** It provides an
integration layer and reusable abstractions between your application and
model providers.

------------------------------------------------------------------------

## 1. LangChain Architecture

Imagine a customer asks:

> Explain why my order might be delayed.

The application flow looks like this:

``` text
User Input
"Why is my order delayed?"
        |
        v
LangChain Application
Prompt construction, model call, output handling
        |
        v
Chat Model
OpenAI / Anthropic / other provider
        |
        v
Model Response
Generated explanation
```

LangChain provides reusable components for this flow.

It does not automatically know your order database or business rules.
Those integrations are still your responsibility to build.

------------------------------------------------------------------------

## 2. Core Components

  Component          Responsibility
  ------------------ ------------------------------------------------
  Models             Connect to language models
  Messages           Represent system, user, and assistant messages
  Prompt templates   Construct reusable prompts
  Output parsers     Convert model output into usable formats
  Tools              Allow models to request external actions
  Runnables          Compose components into execution pipelines

These components will be studied individually in upcoming topics. For
now, understand how they fit together.

------------------------------------------------------------------------

## 3. Set Up Your LangChain Environment

We'll use Python and OpenAI as the model provider for the first
implementation.

### Step 1 --- Create a project

``` powershell
mkdir langchain-learning
cd langchain-learning

python -m venv venv
```

### Step 2 --- Activate the virtual environment on Windows

``` powershell
venv\Scripts\activate
```

### Step 3 --- Install dependencies

``` bash
pip install -U langchain langchain-openai python-dotenv
```

Why these three packages?

  Package              Purpose
  -------------------- ----------------------------------------
  `langchain`          Main framework
  `langchain-openai`   OpenAI model integration
  `python-dotenv`      Load environment variables from `.env`

The OpenAI integration is maintained as a separate package, so
installing only `langchain` is not sufficient for using `ChatOpenAI`.

### Step 4 --- Project structure

``` text
langchain-learning/
│
├── .env
├── .gitignore
├── requirements.txt
└── main.py
```

Generate `requirements.txt` after installing the dependencies:

``` bash
pip freeze > requirements.txt
```

------------------------------------------------------------------------

## 4. Configure Your API Key

Create a `.env` file:

``` env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.5
```

Use a model name available to your API account. `gpt-5.5` is an example
from the source notes; if your API account does not support it, replace
it with an available model.

Create `.gitignore`:

``` gitignore
venv/
.env
__pycache__/
*.pyc
```

**Important:** A ChatGPT subscription and OpenAI API billing are
separate. You need API access and billing configured on the API platform
to execute these examples.

------------------------------------------------------------------------

## 5. Your First LangChain Application

Create `main.py`:

``` python
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Initialize the chat model
model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    temperature=0
)

# Send a request to the model
response = model.invoke(
    "Explain what an AI agent is in simple terms."
)

# Display the response
print(response.content)
```

Run the application:

``` bash
python main.py
```

### Understand the important lines

**1. `load_dotenv()`**

Loads environment variables from `.env` into the process environment.

**2. `ChatOpenAI()`**

Creates a LangChain chat model wrapper. It handles communication with
the OpenAI API.

**3. `temperature=0`**

Controls randomness in generation. Lower temperature generally produces
more consistent responses, though it does not guarantee identical
outputs.

**4. `model.invoke()`**

Sends input to the model and waits for a response.

**5. `response.content`**

Extracts the generated message content.

The integration supports synchronous invocation, asynchronous
invocation, and streaming.

------------------------------------------------------------------------

## 6. Three Important Execution Methods

LangChain provides multiple ways to interact with models.

### A. `invoke()` --- Normal Execution

``` python
response = model.invoke("What is MCP?")
print(response.content)
```

It waits until the model returns its response.

### B. `ainvoke()` --- Asynchronous Execution

``` python
import asyncio

async def main():
    response = await model.ainvoke(
        "Explain multi-agent architecture."
    )

    print(response.content)


asyncio.run(main())
```

Useful when your FastAPI application needs non-blocking model calls or
runs multiple independent requests concurrently.

### C. `stream()` --- Streaming Execution

``` python
for chunk in model.stream(
    "Explain how LangGraph works."
):
    print(chunk.content, end="", flush=True)
```

Instead of waiting for the entire response, you receive chunks as they
arrive.

This is useful for chat interfaces where the user sees the answer being
generated progressively.

### Understand the difference

  Method        Behaviour
  ------------- --------------------------------
  `invoke()`    Wait for complete response
  `ainvoke()`   Asynchronous complete response
  `stream()`    Receive response chunks
  `astream()`   Asynchronous streaming

------------------------------------------------------------------------

## 7. What Exactly Does LangChain Return?

A common beginner mistake is assuming `model.invoke()` directly returns
a Python string.

It returns an `AIMessage` object.

For example:

``` python
response = model.invoke("Hello")

print(type(response))
print(response.content)
print(response.usage_metadata)
print(response.response_metadata)
```

You can inspect:

-   **`content`:** Generated text or other content blocks.
-   **`usage_metadata`:** Token usage information, when provided.
-   **`response_metadata`:** Provider-specific response information.

This matters when you start tracking token usage, API costs, and
execution traces.

------------------------------------------------------------------------

## Quick Revision

  -----------------------------------------------------------------------
  Concept                             What it does
  ----------------------------------- -----------------------------------
  LangChain                           Provides reusable abstractions for
                                      LLM applications

  `ChatOpenAI`                        Connects your LangChain application
                                      to an OpenAI chat model

  `load_dotenv()`                     Loads environment variables from
                                      `.env`

  `invoke()`                          Performs a synchronous model call

  `ainvoke()`                         Performs an asynchronous model call

  `stream()`                          Yields response chunks
                                      synchronously

  `astream()`                         Yields response chunks
                                      asynchronously

  `AIMessage`                         Object returned by a chat model
                                      invocation

  `usage_metadata`                    Provides token-usage information
                                      when available

  `response_metadata`                 Contains provider-specific response
                                      information
  -----------------------------------------------------------------------

**Engineering takeaway:** LangChain does not replace the model or your
backend logic. It provides reusable interfaces for connecting model
calls and application components. Understand what `invoke()`,
`ainvoke()`, `stream()`, and `AIMessage` do before moving on to chains,
tools, and more complex workflows.
