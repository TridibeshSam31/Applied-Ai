# Module 3: Tool Calling & Tool Execution Architecture

> **Critical for building real agents**

ReAct taught us how an agent decides what to do. In this module, we will
understand how it interacts with external systems.

The most important distinction:

**An LLM can request a tool call, but your application executes that
tool.**

------------------------------------------------------------------------

## 1. What Is Tool Calling?

Tool calling is a capability through which an LLM can request that an
external function or capability be executed.

### Example: Fetching an Order

Suppose a user asks:

> Find the details of order #12345.

Your agent has access to a function:

``` python
def get_order(order_id: str):
    return database.get_order(order_id)
```

The model decides that it needs `get_order()` and generates a structured
tool-call request.

The application: 1. Receives the tool-call request. 2. Validates the
requested tool and its arguments. 3. Executes the corresponding
function. 4. Returns the result to the model. 5. Allows the model to
generate a response using that result.

### Tool Calling Architecture

``` text
1. USER
   "Find order #12345"
        |
        v
2. LLM
   Selects get_order
   Generates structured tool-call request
        |
        v
3. APPLICATION RUNTIME
   Validates arguments and permissions
        |
        v
4. TOOL EXECUTION
   Queries PostgreSQL
        |
        v
5. TOOL RESULT
   Order details returned to the LLM
        |
        v
6. FINAL RESPONSE
   "Your order is currently shipped."
```

The LLM chooses what it wants to do. The application controls whether
and how that action is performed.

------------------------------------------------------------------------

## 2. Tool Definition and JSON Schema

How does the LLM know what a tool does and which arguments it requires?

The application provides a **tool definition** describing the tool and
its input schema.

### Example

``` python
tools = [
    {
        "name": "get_order",
        "description": "Fetch an order using its order ID",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Unique order identifier"
                }
            },
            "required": ["order_id"],
            "additionalProperties": False
        }
    }
]
```

This is a simplified, provider-neutral representation. Actual
tool-definition formats differ across LLM APIs.

### Understanding the Fields

  -----------------------------------------------------------------------
  Field                               Purpose
  ----------------------------------- -----------------------------------
  `name`                              Tool identifier

  `description`                       Explains what the tool does and
                                      when it should be used

  `parameters`                        Defines accepted arguments

  `properties`                        Defines argument names and types

  `required`                          Lists mandatory arguments

  `additionalProperties`              Controls whether undeclared
                                      arguments are allowed
  -----------------------------------------------------------------------

### Why JSON Schema Matters

A schema helps constrain the structure of the model's tool-call
arguments.

For example, `get_order` expects an object containing an `order_id`
string. It should not receive an unrelated argument such as `password`.

**Important:** A schema helps constrain model output, but it does not
replace backend validation. Always validate inputs again in your
application before executing a tool.

------------------------------------------------------------------------

## 3. Tool Calling vs. Function Calling

You will hear both terms in AI engineering.

-   **Function calling** commonly describes a model's ability to produce
    structured requests to call functions.
-   **Tool calling** is the broader concept of invoking external
    capabilities, which may include functions, APIs, database
    operations, search, and other services.

In modern LLM APIs, these terms are often used interchangeably. The
exact terminology depends on the provider.

------------------------------------------------------------------------

## 4. Build a Basic Tool Execution Runtime

Let's implement the core execution architecture ourselves.

### Step 1 --- Define Tools

``` python
def get_order(order_id: str):
    orders = {
        "12345": {
            "status": "shipped",
            "amount": 1500
        }
    }

    return orders.get(order_id)


def create_ticket(issue: str):
    return {
        "ticket_id": "TICKET-101",
        "status": "created",
        "issue": issue
    }
```

These are simple demonstration functions. The order data is hardcoded,
and `create_ticket` does not persist a real ticket.

### Step 2 --- Create a Tool Registry

A **tool registry** maps tool names to executable functions.

``` python
tool_registry = {
    "get_order": get_order,
    "create_ticket": create_ticket
}
```

The registry gives the application a controlled way to look up an
executable function by name.

### Step 3 --- Execute the Requested Tool

``` python
def execute_tool(tool_name, arguments):
    if tool_name not in tool_registry:
        raise ValueError("Unknown tool")

    tool = tool_registry[tool_name]

    return tool(**arguments)
```

### Step 4 --- Test the Runtime

``` python
result = execute_tool(
    "get_order",
    {"order_id": "12345"}
)

print(result)
```

Output:

``` python
{
    "status": "shipped",
    "amount": 1500
}
```

This is the core idea behind the execution layer of many agent systems.

### What Is Missing?

This minimal implementation is useful for understanding the concept, but
it is not production-ready.

For example: - It does not validate arguments against a schema. - It
does not authenticate the requesting user. - It does not enforce
per-user permissions. - It does not handle timeouts. - It does not
distinguish read-only tools from tools with side effects. - It does not
provide structured error handling or audit logs.

------------------------------------------------------------------------

## 5. Production-Level Tool Execution

Imagine your agent has access to:

-   `get_balance()`
-   `transfer_money()`
-   `delete_account()`
-   `send_email()`

Would you allow the LLM to execute all these functions without
restrictions?

**Absolutely not.**

A production execution runtime needs multiple safeguards.

### Production Safeguards

  Safeguard           Why it matters
  ------------------- -------------------------------------------
  Schema validation   Reject malformed arguments
  Authentication      Identify the requesting user or service
  Authorization       Verify permission to perform the action
  Input validation    Reject invalid or malicious inputs
  Timeout             Prevent indefinitely running tools
  Rate limiting       Prevent abuse and excessive requests
  Idempotency         Prevent duplicate side effects
  Audit logging       Record important actions for traceability
  Human approval      Add control for sensitive operations

### Authentication vs. Authorization

These are related but different:

-   **Authentication:** Who is making the request?
-   **Authorization:** Is that requester allowed to perform this action?

For example, a user may be authenticated but still not have permission
to delete another user's account.

### Idempotency

Suppose a model requests `transfer_money()` and the application
experiences a network timeout.

The application may not know whether the transfer succeeded. If it
blindly retries, the user could be charged twice.

An idempotency key can help ensure that repeated requests for the same
logical operation do not create duplicate side effects.

### Human Approval

For consequential operations such as transferring money or deleting an
account, the application may require explicit human approval before
execution.

**Important:** A tool description saying "only admins can delete
accounts" does not enforce admin permissions. Your backend must
independently authenticate the requester and enforce authorization.

------------------------------------------------------------------------

## 6. Parallel Tool Calling

Parallel tool calling allows an application to execute multiple
independent tool calls concurrently.

### Example

Suppose a user asks:

> Get my order details and check the current weather in Delhi.

The two operations are independent.

An agent may request both tools in one model response:

``` python
tool_calls = [
    {
        "name": "get_order",
        "arguments": {"order_id": "12345"}
    },
    {
        "name": "get_weather",
        "arguments": {"city": "Delhi"}
    }
]
```

The application can execute them concurrently.

### Async Implementation

``` python
import asyncio


async def run_parallel(tool_calls):
    tasks = [
        execute_async_tool(
            call["name"],
            call["arguments"]
        )
        for call in tool_calls
    ]

    return await asyncio.gather(*tasks)
```

`execute_async_tool()` is intentionally left as an application-specific
async dispatcher. It must perform the same validation and permission
checks as the normal execution path.

`asyncio.gather()` runs the awaitables concurrently and returns their
results in input order.

### Why Parallelize?

If two independent operations each take approximately two seconds:

-   Sequential execution may take approximately four seconds.
-   Concurrent execution may take approximately two seconds, excluding
    overhead.

These are illustrative timings. Actual latency depends on the tools and
infrastructure.

### Important Rules

-   Only parallelize independent operations.
-   Do not parallelize operations that depend on one another.
-   Handle partial failures.
-   Apply separate timeouts and permission checks.
-   Consider rate limits and downstream service capacity.

For example, `get_order()` must finish before `cancel_order()` can
safely use its result to determine what should be cancelled.

------------------------------------------------------------------------

## 7. Tool Calling vs. MCP

Since we have already studied MCP, connect the concepts.

  -----------------------------------------------------------------------
  Dimension               Tool Calling            MCP
  ----------------------- ----------------------- -----------------------
  Primary purpose         Model requests tool     Standardized
                          execution               client-server protocol
                                                  for exposing
                                                  capabilities

  Main role               Model-facing tool       Communication and
                          interface and execution capability discovery
                          request                 between clients and
                                                  servers

  Capabilities            Commonly functions,     Tools, resources, and
                          APIs, and other tools   prompts

  Communication           Depends on the LLM API  Uses JSON-RPC 2.0
                          and application         

  Execution               Application runtime     MCP server exposes
                          executes the requested  capabilities and
                          tool                    handles requests
  -----------------------------------------------------------------------

### How They Work Together

An MCP server can expose tools to an MCP client.

The AI application can discover those tools and make suitable
capabilities available to an LLM. When the model requests a tool call,
the application routes that request through the appropriate execution
path.

They solve related but different problems:

-   **Tool calling:** How the model requests an action.
-   **MCP:** How an application communicates with external capability
    providers in a standardized way.

------------------------------------------------------------------------

## 8. Interview Questions

Make sure you can answer these without memorizing definitions.

### Q1. Why doesn't an LLM directly execute a Python function?

The LLM generates a structured tool-call request. The application
runtime receives the request, validates it, and executes the
corresponding function. This separation provides control over
permissions, validation, and side effects.

### Q2. What happens if an LLM generates invalid tool arguments?

The application should validate the arguments against the expected
schema and business rules. If validation fails, it should reject the
request and return a structured error or ask the model to correct the
arguments.

### Q3. What is a tool registry?

A tool registry maps tool identifiers to their executable
implementations. It allows the application to look up and dispatch an
approved tool by name.

### Q4. How do you prevent an agent from calling unauthorized tools?

Use an allowlist, authenticate the requester, enforce authorization in
the backend, validate arguments, and restrict access to sensitive
operations. Never rely only on the model's instructions.

### Q5. When should parallel tool calling be avoided?

Avoid it when one operation depends on the result of another, when
operations conflict, or when concurrent execution could cause unsafe
side effects.

### Q6. What is the difference between a tool call and its result?

A tool call is the model's structured request to execute a particular
tool with arguments. A tool result is the output returned by the
application after executing that tool.

### Q7. How would you prevent duplicate payment execution?

Use a server-side idempotency key tied to the logical payment request,
persist the operation's status, and ensure retries return the original
result rather than creating another payment. Also use authorization,
transaction handling, and audit logging.

------------------------------------------------------------------------

## 9. Your Engineering Assignment

### Build a Mini Tool Execution Runtime

Implement a small Python tool execution system without using an agent
framework.

**Required tools:** 1. `get_order(order_id)` --- fetch an order. 2.
`get_weather(city)` --- return weather information from a real API or a
clearly identified mock. 3. `create_ticket(issue)` --- create a support
ticket.

**Required architecture:**

``` text
Tool Definitions
       |
       v
   Tool Registry
       |
       v
  Tool Dispatcher
       |
       v
 Validation + Permission Checks
       |
       v
  Tool Execution
       |
       v
 Structured Tool Result
```

**Requirements:** - \[ \] Implement a tool registry. - \[ \] Implement a
dispatcher that selects tools by name. - \[ \] Validate required
arguments and reject unexpected arguments. - \[ \] Handle unknown tools
and execution errors. - \[ \] Add a timeout mechanism. - \[ \] Execute
two independent tool calls concurrently. - \[ \] Return structured
results. - \[ \] Add basic logging for tool execution.

**Stretch goals:** - Add a per-tool permission policy. - Add idempotency
for `create_ticket`. - Add unit tests for valid calls, invalid
arguments, unknown tools, timeouts, and partial failures. - Connect the
runtime to an LLM API so the model can request tools dynamically.

**Deliverable:** A working mini tool execution runtime with a README
explaining its architecture and design decisions.

------------------------------------------------------------------------

## 10. Quick Revision

  Term                 Remember
  -------------------- -------------------------------------------------
  Tool calling         Model requests an external action
  Tool definition      Describes a tool and its input schema
  JSON Schema          Defines the expected structure of arguments
  Tool registry        Maps tool names to executable functions
  Dispatcher           Routes a tool request to its implementation
  Validation           Checks arguments and business rules
  Authentication       Establishes who is making the request
  Authorization        Checks whether the requester has permission
  Idempotency          Prevents duplicate side effects
  Parallel execution   Runs independent tools concurrently
  MCP                  Standardized protocol for exposing capabilities

**Core architecture to remember:**

``` text
LLM requests tool
       |
       v
Application receives request
       |
       v
Validate tool + arguments + permissions
       |
       v
Execute approved function
       |
       v
Return structured result to LLM
       |
       v
LLM continues or produces final answer
```

**Interview one-liner:** Tool calling is the model-facing mechanism for
requesting external actions, while the application runtime is
responsible for securely validating, dispatching, and executing those
actions.
