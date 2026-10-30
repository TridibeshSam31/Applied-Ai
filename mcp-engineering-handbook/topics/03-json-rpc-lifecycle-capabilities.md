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
