# Agent Frameworks --- Tools and Tool Calling with LangChain

Tool calling is a core concept in LangChain and agentic applications.

An LLM can generate text, but by itself it cannot directly query your
PostgreSQL database, send an email, or fetch an order status from an
external API. Tools bridge this gap by exposing application functions
through a defined name, description, and input schema.

This topic implements a Customer Support Agent with:

-   `get_order_status()` --- retrieves order status.
-   `create_support_ticket()` --- requests ticket creation.
-   An LLM that decides when to request a tool.
-   A Python backend that validates and executes tool requests.

------------------------------------------------------------------------

## 1. What Is a Tool?

A **tool** is an ordinary function exposed to an LLM through a defined
name, description, and input schema.

Example:

``` python
def get_weather(city: str):
    return f"Weather information for {city}"
```

Normally, Python code calls it directly:

``` python
result = get_weather("Delhi")
```

In an agentic application, the LLM can be given the tool definition. The
model can then decide whether the user's question requires that tool.

**Important:** The LLM does not directly execute the function. The model
generates a tool-call request. Your application validates that request
and executes the function.

------------------------------------------------------------------------

## 2. Tool Calling Architecture

``` text
User
"Where is order ORD-101?"
        |
        v
LLM
Decides whether a tool is needed
        |
        v
Tool Call Request
get_order_status(order_id="ORD-101")
        |
        v
Python Backend
Validates and executes the function
        |
        v
Tool Result
Order status returned from database
        |
        v
LLM
Uses result to generate final response
```

There are two distinct responsibilities:

-   **LLM:** Selects the tool and proposes arguments.
-   **Backend:** Validates, authorizes, and executes the requested
    operation.

Never trust the model's arguments blindly.

------------------------------------------------------------------------

## 3. Create Your First LangChain Tool

LangChain provides the `@tool` decorator.

Install the packages from previous topics if you have not already:

``` bash
pip install -U langchain langchain-openai python-dotenv pydantic
```

Create `tools.py`:

``` python
from langchain.tools import tool


@tool
def get_order_status(order_id: str) -> str:
    """
    Retrieve the current status of an order
    using its order ID.
    """
    # Simulated database response
    orders = {
        "ORD-101": {
            "status": "shipped",
            "delivery_date": "2026-11-12"
        },
        "ORD-102": {
            "status": "delayed",
            "delivery_date": "2026-11-14"
        }
    }

    order = orders.get(order_id)

    if not order:
        return "Order not found."

    return str(order)
```

### Understand the implementation

**1. `@tool`**

Converts a Python function into a LangChain tool.

**2. Function name**

`get_order_status` becomes the tool's name.

**3. Type hints**

`order_id: str` helps define the expected argument schema.

**4. Docstring**

The description tells the model what the tool does. A vague description
can cause poor tool selection.

The resulting tool exposes a schema conceptually similar to:

``` json
{
  "name": "get_order_status",
  "description": "Retrieve the current status of an order using its order ID.",
  "parameters": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string"
      }
    },
    "required": ["order_id"]
  }
}
```

This schema makes the function discoverable to the model.

------------------------------------------------------------------------

## 4. Inspect Your Tool Schema

You can inspect the generated schema:

``` python
from tools import get_order_status

print(get_order_status.name)
print(get_order_status.description)
print(get_order_status.args_schema.model_json_schema())
```

This is useful for debugging.

For example, if the model repeatedly passes an incorrect argument,
inspect the tool schema and description before blaming the model.

------------------------------------------------------------------------

## 5. Bind Tools to the LLM

We have converted a Python function into a tool, but the model does not
yet know that the tool is available.

Use `bind_tools()`.

Create `main.py`:

``` python
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from tools import get_order_status

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    temperature=0
)

# Make the tool available to the model
model_with_tools = model.bind_tools([
    get_order_status
])

response = model_with_tools.invoke(
    "Where is my order ORD-101?"
)

print(response)
```

### What is happening?

`bind_tools()` tells the model which tools it can request, including
their descriptions and schemas.

It does **not** execute those tools.

The model may return an `AIMessage` containing a tool call.

Inspect it:

``` python
print(response.content)
print(response.tool_calls)
```

Example conceptual tool-call output:

``` python
[
    {
        "name": "get_order_status",
        "args": {
            "order_id": "ORD-101"
        },
        "id": "call_123",
        "type": "tool_call"
    }
]
```

The model has requested the tool, but the Python function has not
necessarily run yet.

------------------------------------------------------------------------

## 6. Execute the Tool

LangChain tools can be invoked directly:

``` python
tool_call = response.tool_calls[0]

result = get_order_status.invoke(
    tool_call["args"]
)

print(result)
```

Output:

``` text
{'status': 'shipped', 'delivery_date': '2026-11-12'}
```

This is the actual function execution.

### Distinguish the operations

  Operation               What happens
  ----------------------- ------------------------------------
  `bind_tools()`          Makes tools available to the model
  `response.tool_calls`   Shows requested tool calls
  `tool.invoke()`         Executes the Python tool

------------------------------------------------------------------------

## 7. Complete Tool-Calling Loop

A proper agent should not stop after executing one tool. It should send
the result back to the model so the model can generate a final response.

Here is a simple manual implementation:

``` python
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage
)

from tools import get_order_status

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    temperature=0
)

tools = [get_order_status]

tools_by_name = {
    tool.name: tool
    for tool in tools
}

model_with_tools = model.bind_tools(tools)

messages = [
    SystemMessage(
        content=(
            "You are a helpful customer support assistant. "
            "Use tools when order information is needed."
        )
    ),
    HumanMessage(
        content="Where is my order ORD-101?"
    )
]

# Step 1: Ask the model
response = model_with_tools.invoke(messages)

# Step 2: Process tool calls
for tool_call in response.tool_calls:
    selected_tool = tools_by_name[tool_call["name"]]

    tool_result = selected_tool.invoke(
        tool_call["args"]
    )

    # Step 3: Send tool output back to the conversation
    messages.append(response)
    messages.append(
        ToolMessage(
            content=str(tool_result),
            tool_call_id=tool_call["id"]
        )
    )

# Step 4: Ask model to generate final response
final_response = model_with_tools.invoke(messages)

print(final_response.content)
```

Expected response (wording can vary):

``` text
Your order ORD-101 has been shipped.
Its expected delivery date is November 12, 2026.
```

### Understand the complete cycle

1.  User sends a question.
2.  Model requests a tool.
3.  Backend executes the tool.
4.  Tool result goes back into the conversation.
5.  Model interprets the result.
6.  Model generates the final answer.

This is the basic tool-calling cycle behind many AI agents.

**Limitation of this teaching example:** It assumes a single round of
tool calls. A production agent needs a bounded loop to handle multiple
rounds, errors, invalid arguments, and calls that do not return a final
answer.

------------------------------------------------------------------------

## 8. Multiple Tools

A customer support agent needs more than one capability.

Let's add a ticket creation tool:

``` python
from langchain.tools import tool


@tool
def create_support_ticket(
    order_id: str,
    issue: str
) -> str:
    """
    Request creation of a support ticket
    for an eligible customer order.
    """
    # Simulated implementation only.
    return (
        f"Ticket creation requested for {order_id}. "
        f"Issue: {issue}"
    )
```

Now bind both tools:

``` python
tools = [
    get_order_status,
    create_support_ticket
]

model_with_tools = model.bind_tools(tools)
```

The model can choose between these tools based on the user's request.

### Critical backend engineering rule

**Do not let the LLM decide whether a customer is authorized to create a
ticket.**

Your actual backend must independently verify:

-   The customer owns the order.
-   The order is eligible for support.
-   The customer is authenticated.
-   The operation is idempotent.
-   The request has valid arguments.

The tool above is only a demonstration. It does not implement these
protections.

------------------------------------------------------------------------

## 9. Tool Calling vs Normal Function Calling

These terms are related, but do not confuse their responsibilities.

  -----------------------------------------------------------------------
  Normal Python function              LLM tool calling
  ----------------------------------- -----------------------------------
  Developer selects function          Model can request a function

  Arguments supplied by code          Model proposes arguments

  Function executes directly          Backend executes after receiving
                                      request

  No LLM required                     LLM participates in selection
  -----------------------------------------------------------------------

For example:

``` python
# Normal function call
get_order_status.invoke({
    "order_id": "ORD-101"
})
```

Versus:

``` python
# LLM requests a tool
response = model_with_tools.invoke(
    "Check order ORD-101"
)
```

The second involves model reasoning and tool selection.

**Interview point:** Tool calling is not the same as an LLM executing
arbitrary Python code. The model produces a structured request, and the
application decides whether and how to execute it.

------------------------------------------------------------------------

## 10. Handling Multiple Tool Calls Correctly

There is a subtle bug in the earlier teaching implementation:
`messages.append(response)` was inside the loop. If the model requests
multiple tools at once, the same assistant message would be appended
multiple times.

Correct pattern:

``` python
# Append the assistant's tool-call message once
messages.append(response)

for tool_call in response.tool_calls:
    selected_tool = tools_by_name[tool_call["name"]]

    try:
        result = selected_tool.invoke(
            tool_call["args"]
        )
    except Exception as error:
        result = f"Tool execution failed: {error}"

    messages.append(
        ToolMessage(
            content=str(result),
            tool_call_id=tool_call["id"]
        )
    )
```

This correctly associates every tool result with its corresponding
tool-call ID.

### What if the model requests another tool after receiving the first result?

Then you need a loop.

A bounded implementation:

``` python
MAX_ITERATIONS = 5

for iteration in range(MAX_ITERATIONS):
    response = model_with_tools.invoke(messages)

    if not response.tool_calls:
        print(response.content)
        break

    messages.append(response)

    for tool_call in response.tool_calls:
        tool = tools_by_name.get(tool_call["name"])

        if tool is None:
            result = "Unknown tool requested."
        else:
            try:
                result = tool.invoke(tool_call["args"])
            except Exception as error:
                result = f"Tool failed: {error}"

        messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
        )
else:
    print("Maximum tool iterations reached.")
```

This is still a teaching implementation. Production code should also
validate arguments, enforce permissions, control retries, and handle
malformed tool calls.

------------------------------------------------------------------------

## 11. What About LangGraph's `ToolNode`?

LangChain also provides `ToolNode`, which is especially useful when
building workflows using LangGraph.

It handles tool execution as a graph node.

Conceptually:

``` text
Agent Node
Model decides whether to call a tool
        |
        v
Conditional Routing
Tool call present?
        |
        v
ToolNode
Execute tools
        |
        v
Back to Agent
Interpret tool results and continue

If no tool is required:
        |
        v
Final Response
```

We'll implement this properly when we reach the LangGraph topics.

------------------------------------------------------------------------

## 12. Interview Questions

1.  What does the `@tool` decorator do?
2.  What is the difference between `bind_tools()` and `invoke()`?
3.  Does an LLM directly execute a Python tool?
4.  Why do we need `ToolMessage` and `tool_call_id`?
5.  Why should tool execution be controlled by the backend?
6.  Why do we need a maximum iteration limit in an agent loop?
7.  What happens when a tool throws an exception?

------------------------------------------------------------------------

## Quick Revision

  Concept                 Responsibility
  ----------------------- --------------------------------------------------
  `@tool`                 Converts a Python function into a LangChain tool
  Tool schema             Describes the tool's name, inputs, and purpose
  `bind_tools()`          Makes tools available to the model
  `response.tool_calls`   Contains the model's requested tool calls
  `tool.invoke()`         Executes the tool
  `ToolMessage`           Returns tool output to the conversation
  `tool_call_id`          Associates a tool result with its request
  Bounded agent loop      Limits repeated model/tool cycles
  `ToolNode`              Executes tools as a node in a LangGraph workflow

**Engineering takeaway:** The model proposes an action; your backend
owns execution. Validate arguments, enforce authorization, handle
errors, and bound the tool loop. Never confuse a tool-call request with
a successfully executed operation.
