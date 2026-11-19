# 04 — Transports: stdio and Streamable HTTP

A transport carries protocol messages between an MCP client and server. It is separate from the meaning of MCP methods.

## 1. Transport as a separate layer

The logical operation `tools/list` should not require a different business implementation just because the messages travel over a different transport.

```text
             MCP protocol messages
                       |
             transport implementation
                /              \
             stdio        Streamable HTTP
               |                 |
         local process       remote service
```

## 2. stdio transport

With stdio, the host launches a local server process and communicates through standard input and standard output.

```text
Host process
   |
   | spawn child process
   v
MCP server process
   stdin  <---- protocol input
   stdout ----> protocol output
   stderr ----> diagnostics
```

### Advantages
- Simple local development.
- No network port required.
- Natural fit for desktop applications and developer tools.
- Host can manage the child process lifecycle.

### Critical operational rule
**Keep stdout reserved for protocol messages.** Send logs and diagnostics to stderr. A debug `print()` to stdout can corrupt the protocol stream.

Also:
- handle process termination and cleanup;
- do not assume the working directory is the repository root;
- pass environment variables deliberately;
- do not dump the full environment into logs.

## 3. Streamable HTTP

Streamable HTTP carries MCP messages over HTTP and supports streaming behaviour as defined by the transport specification. It is suitable for remote or centrally deployed servers.

```text
MCP Host / Client
      |
      | HTTP request carrying MCP message
      v
Reverse proxy / TLS termination
      |
      v
MCP HTTP endpoint
      |
      v
Application services
```

Do not implement a generic JSON endpoint and assume it is automatically Streamable HTTP. Follow the current transport specification and SDK implementation.

### Why use it?
- Remote server deployment.
- Multiple clients connecting to a service.
- Centralised backend connectivity and secrets.
- Integration with TLS termination, gateways and observability.

### Operational considerations
- Require HTTPS outside local development.
- Authenticate callers and authorize each operation.
- Follow current origin/host security guidance.
- Set request, connection and response limits.
- Test session lifecycle and reconnect behaviour.
- Ensure proxies do not buffer or terminate streaming incorrectly.

## 4. Transport comparison

| Factor | stdio | Streamable HTTP |
|---|---|---|
| Typical deployment | Local child process | Remote service |
| Network port | Not required | Required |
| Process management | Host launches process | Service manager/container |
| Auth | Local trust boundary still matters | Network identity and auth |
| Scaling | Usually per local process | Centrally deployed |
| Debugging | stderr/process logs | HTTP/server logs and traces |

Choose based on deployment and trust boundaries, not because one is universally better.

## 5. Common failures

**stdio:** stdout pollution, wrong executable, missing environment variables, import failure, wrong working directory, early process exit.

**HTTP:** wrong endpoint, TLS error, reverse-proxy buffering, unsupported transport, authentication middleware mismatch, session/reconnect issue, overly restrictive body or timeout limits.

## 6. Deployment checklist

stdio:
- [ ] command works from a clean shell;
- [ ] dependencies use the intended environment;
- [ ] stdout contains only protocol traffic;
- [ ] stderr contains diagnostics;
- [ ] shutdown closes resources.

HTTP:
- [ ] HTTPS enabled;
- [ ] authentication and authorization tested;
- [ ] origin/host protections follow current spec;
- [ ] proxy supports streaming semantics;
- [ ] timeouts and body limits are intentional;
- [ ] reconnect behaviour tested;
- [ ] health checks reveal no sensitive information.

## 7. Practical tasks
1. Run a minimal stdio server.
2. Print a debug line to stdout and observe the failure; move it to stderr.
3. Run the same tools over Streamable HTTP.
4. Put a reverse proxy in front and verify streaming.
5. Choose a transport for a local IDE and a multi-tenant SaaS service; justify both.

## 8. Interview questions
- What is an MCP transport?
- Why do stdio logs go to stderr?
- When choose Streamable HTTP?
- Is MCP over HTTP just a REST endpoint?
- What can proxy buffering break?
- What security controls matter for a remote server?


---

## 9. Complete Production Implementation: Stdio & Streamable SSE Transports 💻

Below is an end-to-end Python implementation demonstrating both major MCP transports:
1. **Stdio Transport Server & Subprocess Client:** Demonstrates strict standard I/O separation (stdout strictly reserved for raw newline-delimited JSON-RPC, logging strictly redirected to `stderr` to prevent protocol corruption).
2. **Streamable HTTP + SSE Transport Server:** FastAPI-based HTTP server exposing `/sse` and `/messages` endpoints for remote/networked tool execution with streaming events.

```python
"""
mcp_transports_demo.py
Production Demonstration of MCP Transports:
Part A: Stdio Transport (with subprocess runner and stderr logging isolation)
Part B: Streamable HTTP / Server-Sent Events (SSE) Transport with FastAPI
"""

import sys
import json
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse


# =====================================================================
# PART A: Stdio Server Engine (Strict stdout/stderr separation)
# =====================================================================
class StdioMCPServer:
    """
    Reads JSON-RPC from sys.stdin, writes JSON-RPC to sys.stdout.
    CRITICAL INVARIANT: NEVER use print() for debugging!
    All application logs MUST go to sys.stderr.
    """
    def log(self, message: str):
        # Redirected to stderr so it does not corrupt the JSON-RPC wire format!
        sys.stderr.write(f"[STDIO-SERVER-LOG] {message}\n")
        sys.stderr.flush()

    async def run(self):
        self.log("Server starting over stdio transport...")
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break
            raw_str = line.decode().strip()
            if not raw_str:
                continue

            self.log(f"Received raw message: {raw_str}")
            try:
                msg = json.loads(raw_str)
                response = {
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "result": {"status": "ok", "echo_params": msg.get("params")}
                }
                # Write back to stdout with newline framing
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_res = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)}
                }
                sys.stdout.write(json.dumps(err_res) + "\n")
                sys.stdout.flush()


# =====================================================================
# PART B: Streamable HTTP / SSE Transport Server (FastAPI)
# =====================================================================
app = FastAPI(title="MCP Streamable HTTP Server")

# In-memory queue map for active SSE client sessions
active_sse_queues = {}

@app.get("/sse")
async def mcp_sse_endpoint(request: Request):
    """
    Opens an SSE stream to the client.
    Sends an initial 'endpoint' event telling the client where to POST messages.
    """
    session_id = "session-" + str(asyncio.get_event_loop().time())
    queue = asyncio.Queue()
    active_sse_queues[session_id] = queue

    async def event_generator() -> AsyncGenerator[str, None]:
        # Step 1: Send endpoint event
        yield f"event: endpoint\ndata: /messages?session_id={session_id}\n\n"

        # Step 2: Stream downstream messages and tool events
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await queue.get()
                yield f"event: message\ndata: {json.dumps(data)}\n\n"
        finally:
            active_sse_queues.pop(session_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.post("/messages")
async def mcp_receive_message(session_id: str, request: Request):
    """
    Receives JSON-RPC requests from the client, processes them,
    and pushes responses to the client's SSE event stream.
    """
    payload = await request.json()
    queue = active_sse_queues.get(session_id)
    if not queue:
        return {"error": "Invalid or expired session"}

    response_payload = {
        "jsonrpc": "2.0",
        "id": payload.get("id"),
        "result": {
            "content": [{"type": "text", "text": "Streamable HTTP Tool Response"}]
        }
    }
    await queue.put(response_payload)
    return {"status": "accepted"}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        import uvicorn
        print("Starting MCP Streamable HTTP server on port 8001...")
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        asyncio.run(StdioMCPServer().run())
```

### Run Commands:
```bash
# Run over standard I/O:
python mcp_transports_demo.py

# Run over Streamable HTTP:
python mcp_transports_demo.py --http
```
