# 05 — Building MCP Servers and Clients with Python

This session moves from protocol concepts to implementation. Use the official Python SDK and pin the version used by your project.

## 1. Project setup

Suggested layout:

```text
mcp-demo/
├── pyproject.toml
├── src/mcp_demo/
│   ├── server.py
│   ├── services.py
│   └── client.py
└── tests/
    ├── test_services.py
    └── test_server_contract.py
```

Create an isolated environment:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install "mcp"
```

For a real repository, pin a tested SDK version in `pyproject.toml` or a lock file. Avoid unbounded production dependencies.

## 2. FastMCP concept

The Python SDK provides higher-level abstractions that reduce boilerplate. FastMCP-style decorators can register functions as tools, resources or prompts. The SDK handles protocol details such as message parsing and dispatch.

It does not remove the need to understand schemas, lifecycle, transport, authorization or errors.

## 3. Small tool server

Illustrative pattern; verify imports and run configuration against your installed SDK version.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("math-service")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b

@mcp.tool()
def calculate_percentage(value: float, percent: float) -> dict:
    """Calculate a percentage without changing external state."""
    if value < 0:
        raise ValueError("value must be non-negative")
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return {
        "base": value,
        "percent": percent,
        "result": round(value * percent / 100, 2),
    }

if __name__ == "__main__":
    mcp.run()
```

## 4. Keep domain logic outside decorators

```python
# services.py
def calculate_refund(total: float, percent: float) -> float:
    if total < 0:
        raise ValueError("total cannot be negative")
    if not 0 <= percent <= 100:
        raise ValueError("percent must be 0..100")
    return round(total * percent / 100, 2)
```

```python
# server.py
from mcp.server.fastmcp import FastMCP
from .services import calculate_refund

mcp = FastMCP("refund-calculator")

@mcp.tool()
def propose_refund(total: float, percent: float) -> dict:
    """Calculate a refund proposal. Does not issue a payment."""
    amount = calculate_refund(total, percent)
    return {"proposed_amount": amount, "payment_issued": False}
```

Now the domain function can be unit-tested without starting an MCP connection.

## 5. Resources and prompts

Register a resource when exposing addressable data and a prompt when exposing a reusable message template. The following is conceptual pseudocode; check the exact decorator signatures for your SDK release.

```python
@mcp.resource("policy://refunds")
def refund_policy() -> str:
    return "Refunds require eligibility validation and approval."
```

```python
@mcp.prompt()
def explain_ticket(ticket_id: str) -> str:
    return f"Explain ticket {ticket_id}: summary, impact, next action."
```

Do not present pseudocode as guaranteed copy-paste code. Protocol concepts are more stable than SDK APIs.

## 6. Client lifecycle

A client generally:
1. creates a stdio or HTTP transport;
2. opens transport streams/session;
3. creates an MCP client session;
4. initializes the session;
5. lists tools;
6. calls a selected tool;
7. closes session and transport.

Illustrative async shape:

```python
import asyncio

async def main():
    # Create the transport using the SDK's current API.
    # Open the transport streams.
    # Create ClientSession(read_stream, write_stream).
    # await session.initialize()
    # tools = await session.list_tools()
    # result = await session.call_tool("add", {"a": 2, "b": 3})
    # Close session and transport using context managers.
    pass

if __name__ == "__main__":
    asyncio.run(main())
```

Use the official SDK client example for exact imports and context-manager syntax in your pinned version.

## 7. Async and resource management

MCP servers often call network APIs and databases. Async helps with concurrent I/O; it does not automatically accelerate CPU-heavy work.

- Use async libraries for async I/O.
- Do not block the event loop with long synchronous calls.
- Use database connection pools.
- Set timeouts on outbound calls.
- Close clients and pools on shutdown.
- Bound concurrency to protect dependencies.

## 8. Testing strategy

**Unit:** domain calculations, validation, permission decisions, transformations.

**Contract:** tool names, descriptions, required schema, result structure and error behaviour.

**Integration:** actual SDK client connects, initialization succeeds, tools are discoverable, calls reach services, resources/prompts behave correctly.

**Negative:** malformed arguments, unknown tool, unauthenticated caller, forbidden tenant, timeout and dependency outage.

## 9. Practical tasks
1. Build `add`, `multiply` and `percentage`.
2. Add constraints and useful descriptions.
3. Add a read-only resource.
4. Write a client that lists tools and calls `add`.
5. Unit-test domain functions.
6. Add an integration test using an MCP client session.
7. Pin the SDK version and document the launch command.

## 10. Interview questions
- What does FastMCP abstract away?
- Why separate domain logic from tool handlers?
- Why initialize a client session?
- Unit test versus contract test?
- Why are downstream timeouts necessary?
- Does async make CPU-bound code faster?
