# 03 — JSON-RPC, Lifecycle and Capability Negotiation

MCP uses JSON-RPC 2.0 as its message format. Understanding the wire protocol is essential when SDK abstractions hide a bug.

## 1. JSON-RPC message categories

### Request
A request contains a method, parameters and an ID:

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/list",
  "params": {}
}
```

The ID correlates the response with the request.

### Successful response

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "tools": []
  }
}
```

The response uses the matching ID.

### Error response

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "error": {
    "code": -32602,
    "message": "Invalid params"
  }
}
```

### Notification
A notification has no ID and receives no JSON-RPC response:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

Do not attach an ID to a notification.

## 2. Common JSON-RPC error codes

| Code | Meaning |
|---:|---|
| -32700 | Parse error |
| -32600 | Invalid request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |

MCP implementations can define additional protocol-specific errors. Use the SDK/specification definitions rather than inventing codes.

## 3. Initialization lifecycle

A simplified lifecycle:

```text
Client                                  Server
  |                                       |
  |------ initialize ------------------->|
  |<----- initialize result --------------|
  |                                       |
  |------ notifications/initialized ---->|
  |                                       |
  |------ tools/list -------------------->|
  |<----- tools/list result --------------|
  |                                       |
  |------ tools/call -------------------->|
  |<----- tools/call result --------------|
  |                                       |
  |----------- close transport ---------->|
```

Initialization establishes protocol compatibility and negotiates capabilities. The client communicates its supported protocol version and capabilities; the server responds with the version and capabilities it supports. The client then sends the initialized notification.

Do not perform normal application operations before the required initialization sequence completes.

## 4. Protocol version negotiation

The client and server need a mutually supported protocol version. If they cannot agree, the connection should fail clearly rather than silently assuming semantics.

Engineering rules:
- pin SDK versions for reproducibility;
- log the negotiated protocol version;
- test against intended host clients;
- read version-specific specification changes;
- avoid relying on undocumented behaviour.

## 5. Capability negotiation

Capabilities communicate which optional features each side supports. A server may advertise tools, resources or prompts; a client may advertise capabilities related to features it can handle.

A client must not assume every server supports every optional feature. Capability negotiation is an extensibility mechanism, not a permissions system.

## 6. Listing and calling tools

Typical flow:
1. `tools/list` discovers tools.
2. The client inspects names, descriptions and schemas.
3. `tools/call` invokes a selected tool.

Example:

```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "tools/call",
  "params": {
    "name": "search_open_incidents",
    "arguments": {"limit": 10}
  }
}
```

Discovery is not authorization. A tool appearing in a list does not prove that every caller can access every record or invoke every argument combination.

## 7. Notifications and server-initiated messages

Notifications communicate events without expecting a response. Depending on supported capabilities, notifications can communicate changes or progress.

A robust client:
- registers handlers for supported notifications;
- avoids assuming exactly-once delivery across failures;
- reconciles state after reconnecting;
- keeps handlers fast and resilient.

## 8. Concurrency and request IDs

Multiple requests can be in flight. Completion order may differ from send order. For example, request 21 can take three seconds while request 22 takes 100 ms. Response 22 may arrive first.

Never correlate responses by arrival order. Use request IDs.

## 9. Debugging raw messages
- Capture sanitised messages.
- Preserve request IDs and method names.
- Redact tokens and personal data.
- Inspect initialization before tool calls.
- Verify negotiated version and capabilities.
- Separate transport, JSON-RPC and tool-execution failures.

## 10. Practical tasks
1. Write a request, success response, error response and notification.
2. Explain why notifications have no ID.
3. Draw initialization and capability negotiation.
4. Capture a `tools/list` exchange.
5. Cause an invalid-parameter error and identify the layer.
6. Simulate concurrent requests and verify response correlation.

## 11. Interview questions
- What is JSON-RPC?
- Request versus notification?
- Why initialize before normal operations?
- What does capability negotiation achieve?
- Why use IDs instead of response order?
- JSON-RPC error versus tool execution error?


---

## 12. Complete Production Implementation: Full JSON-RPC 2.0 Lifecycle Protocol Engine 💻

Below is an end-to-end Python implementation of an MCP server lifecycle protocol engine.
It features:
1. **The 3-Step Initialization Handshake:** `initialize` request $\to$ `capabilities` negotiation $\to$ `notifications/initialized` acknowledge.
2. **Strict State Machine:** Rejects calls before initialization with `-32002` (Server not initialized).
3. **Correlation ID Dispatcher:** Handles out-of-order, concurrent requests matching response `id` to request `id`.
4. **Tool Execution Errors vs Protocol Errors:** Cleanly distinguishes protocol/JSON errors (`-32600`, `-32601`, `-32602`) from domain execution failures (`isError: true` inside result).

```python
"""
mcp_json_rpc_lifecycle.py
Production Implementation of MCP JSON-RPC 2.0 Lifecycle and Capability Negotiation.
"""

import json
import asyncio
from typing import Dict, Any, Optional


class MCPProtocolError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class MCPLifecycleServer:
    def __init__(self):
        # State machine: UNINITIALIZED -> INITIALIZING -> READY -> SHUTTING_DOWN
        self.state = "UNINITIALIZED"
        self.client_capabilities = {}
        self.server_capabilities = {
            "tools": {"listChanged": False},
            "resources": {"subscribe": True},
            "prompts": {"listChanged": False}
        }

    async def handle_message(self, raw_json: str) -> Optional[str]:
        try:
            msg = json.loads(raw_json)
        except json.JSONDecodeError:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error: Invalid JSON"}
            })

        msg_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params", {})

        # 1. Notifications have no 'id'
        if msg_id is None:
            self._handle_notification(method, params)
            return None

        # 2. Requests require responses
        try:
            result = await self._route_request(method, params)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            })
        except MCPProtocolError as err:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": err.code, "message": err.message, "data": err.data}
            })
        except Exception as exc:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32603, "message": f"Internal error: {str(exc)}"}
            })

    def _handle_notification(self, method: str, params: Dict[str, Any]):
        if method == "notifications/initialized":
            if self.state == "INITIALIZING":
                self.state = "READY"
                print(">>> [Server Lifecycle] Received notifications/initialized. Server is now READY.")
            else:
                print(f">>> [Server Lifecycle Warning] Received unexpected initialized notification in state: {self.state}")

    async def _route_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Step 1: Handshake enforcement
        if self.state == "UNINITIALIZED":
            if method == "initialize":
                self.state = "INITIALIZING"
                self.client_capabilities = params.get("capabilities", {})
                protocol_version = params.get("protocolVersion", "2024-11-05")
                print(f">>> [Handshake] Negotiating with client protocolVersion: {protocol_version}")
                return {
                    "protocolVersion": "2024-11-05",
                    "capabilities": self.server_capabilities,
                    "serverInfo": {"name": "LifecycleDemoServer", "version": "1.0.0"}
                }
            else:
                raise MCPProtocolError(-32002, "Server not initialized. Client must call 'initialize' first.")

        if self.state != "READY":
            raise MCPProtocolError(-32002, "Server handshake incomplete. Waiting for notifications/initialized.")

        # Step 2: Normal operation routes
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "calculate_risk_score",
                        "description": "Calculates risk score for customer balance",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"balance": {"type": "number"}},
                            "required": ["balance"]
                        }
                    }
                ]
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            if tool_name != "calculate_risk_score":
                raise MCPProtocolError(-32601, f"Tool '{tool_name}' not found.")

            if "balance" not in args:
                raise MCPProtocolError(-32602, "Invalid params: 'balance' is required.")

            balance = args["balance"]
            # Domain execution result
            risk = "HIGH" if balance > 50000 else "LOW"
            return {
                "content": [{"type": "text", "text": f"Calculated risk: {risk}"}],
                "isError": False
            }

        raise MCPProtocolError(-32601, f"Method '{method}' not found.")


# =====================================================================
# Verification Lifecycle Client
# =====================================================================
async def run_lifecycle_verification():
    server = MCPLifecycleServer()

    print("\n--- Test 1: Calling tools before initialization (Expect failure -32002) ---")
    res1 = await server.handle_message(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}
    }))
    print("Server Response:", res1)

    print("\n--- Test 2: Handshake Step 1 (Client calls 'initialize') ---")
    res2 = await server.handle_message(json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"roots": {"listChanged": True}},
            "clientInfo": {"name": "TestClient", "version": "1.0"}
        }
    }))
    print("Server Response:", res2)

    print("\n--- Test 3: Handshake Step 2 (Client sends initialized notification) ---")
    await server.handle_message(json.dumps({
        "jsonrpc": "2.0", "method": "notifications/initialized", "params": {}
    }))

    print("\n--- Test 4: Tool execution after successful handshake ---")
    res4 = await server.handle_message(json.dumps({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "calculate_risk_score", "arguments": {"balance": 75000}}
    }))
    print("Server Response:", res4)


if __name__ == "__main__":
    asyncio.run(run_lifecycle_verification())
```

### Run Command:
```bash
python mcp_json_rpc_lifecycle.py
```
