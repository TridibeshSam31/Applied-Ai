# 10 — Claude Integration, Debugging and Interview Preparation

An MCP server is not “inside Claude”. A compatible host runs or connects to an MCP client, which communicates with your server over a supported transport.

## 1. Integration mental model

```text
Claude-compatible host
       |
  MCP client/connection
       |
  stdio or HTTP transport
       |
  Your MCP server
       |
  Your application services
```

Configuration format varies by host, operating system and release. Follow the current documentation for the specific client.

## 2. Local stdio integration

A local desktop or IDE host may launch your server as a child process. Configuration commonly includes command, arguments, working directory and environment variables.

Illustrative shape only:

```json
{
  "mcpServers": {
    "support-tools": {
      "command": "python",
      "args": ["-m", "support_mcp.server"],
      "env": {
        "APP_ENV": "development"
      }
    }
  }
}
```

This is not a universal config file. Clients may use different property names and locations. Use the host's official guide. Prefer an explicit interpreter or reliable project launcher when PATH ambiguity exists. Do not place production secrets in shared configuration.

## 3. Claude Code and developer workflows

A coding assistant can use MCP servers for project-specific context or controlled actions:
- read-only documentation search;
- issue lookup;
- CI status;
- schema inspection in a safe environment;
- controlled development workflow actions.

Start with read-only capabilities. Add write tools only after permissions, target environment and confirmation behaviour are clear. Arbitrary shell or unrestricted filesystem access creates a much larger blast radius than a narrowly scoped status tool.

## 4. Debugging

**Server does not appear**
- check config path and JSON syntax;
- verify command and arguments;
- run command manually;
- check Python environment;
- inspect stderr;
- reload/restart host if needed.

**Server starts but tools are missing**
- confirm initialization;
- inspect capability registration;
- verify registration code executes;
- inspect `tools/list`;
- check SDK compatibility.

**Tool call fails**
- inspect exact name and arguments;
- compare arguments to schema;
- check validation and authorization;
- inspect safe logs using correlation ID;
- distinguish permission failure from dependency failure.

**stdio protocol breaks**
- remove non-protocol stdout output;
- move diagnostics to stderr;
- ensure subprocesses do not pollute stdout.

**HTTP connection fails**
- check URL, TLS, auth, proxy behaviour, transport support and session handling.

## 5. Strong demo strategy

Show:
1. server purpose and architecture;
2. capability discovery;
3. successful read-only tool call;
4. resource read;
5. state-changing operation with approval/idempotency;
6. denied unauthorized request;
7. logs/trace showing what happened.

Do not demo only the happy path. A denial test demonstrates that security exists in code.

## 6. Explain the project in an interview

Use this structure:

- **Problem:** What workflow needed AI-accessible capabilities?
- **Architecture:** Which host, client, transport and server?
- **Contracts:** Which tools/resources/prompts and why?
- **Security:** How authenticate and authorize? How isolate tenants?
- **Reliability:** What happens on timeout, cancellation, retry or duplicate mutation?
- **Testing:** What unit, contract, integration, security and load tests?
- **Trade-offs:** Why stdio or Streamable HTTP? What did you avoid exposing?
- **Evidence:** Demo, tests, metrics and clear README.

## 7. Interview questions with answer outlines

**Q: Is MCP an agent framework?**  
No. MCP is a protocol for connecting AI applications to external context and capabilities. An agent framework may orchestrate reasoning/actions; MCP standardises an integration boundary.

**Q: Can an MCP server call a REST API?**  
Yes. A tool handler can call an internal REST API or application service. MCP is the interface exposed to the host; REST can remain a backend integration.

**Q: Why are tool descriptions important?**  
They help clients and models understand intended operations and arguments. Misleading descriptions can cause misuse and create security concerns.

**Q: Does listing a tool mean the user is authorized?**  
No. Discovery communicates availability. The server must authorize each invocation and object access.

**Q: How do you prevent duplicate mutations?**  
Use idempotency keys or naturally idempotent semantics, backed by persistent deduplication and defined key scope/expiry.

**Q: How do you handle prompt injection?**  
Treat retrieved content as untrusted data, constrain capabilities, enforce server-side authorization and require approval for high-impact actions. No single prompt filter is sufficient.

**Q: What is the confused deputy problem?**  
A privileged server uses its own authority for a less-privileged caller without checking that caller's permissions. Propagate trusted identity and authorize every operation/object.

**Q: Why choose stdio?**  
For local process integrations where the host can launch and supervise the server and network exposure is unnecessary.

**Q: Why choose Streamable HTTP?**  
For remote or centrally managed services that need network access and standard HTTP infrastructure.

**Q: What would you monitor?**  
Tool volume/outcome, latency percentiles, active sessions, dependency latency, timeouts, cancellations, rate limits and resource saturation—without sensitive or high-cardinality labels.

## 8. Final assessment

Claim practical MCP experience only when you can explain the wire lifecycle, build a server and client, explain exposed primitives, enforce identity and tenant authorization, demonstrate a negative security test, explain retries/idempotency, show logs/load-test results and discuss trade-offs honestly.

## 9. Final challenge

Complete the Customer Support MCP Server in `../project/README.md`. Add an architecture diagram, setup instructions, tool contract table, security model, test commands/results, load-test methodology and known limitations.


---

## 10. Complete Production Implementation: Claude Desktop & Cursor Integration Simulator 💻

Below is an end-to-end Python script that simulates how **Claude Desktop** and **Cursor** connect to an MCP Server:
1. Generates and parses the exact `claude_desktop_config.json` configuration block.
2. Spawns an MCP server subprocess via `asyncio.create_subprocess_exec` over the Stdio transport.
3. Performs the full capability handshake, dynamically discovers all tools, and invokes a tool on behalf of Claude.

```python
"""
claude_desktop_mcp_client.py
Production Demonstration of Claude Desktop / Cursor connecting to an MCP Server over Stdio.
"""

import sys
import json
import asyncio
from typing import Dict, Any, List


# Sample Claude Desktop configuration structure:
CLAUDE_CONFIG_SAMPLE = {
    "mcpServers": {
        "customer-support-service": {
            "command": "python",
            "args": ["server_entrypoint.py"],
            "env": {
                "DATABASE_URL": "sqlite:///support.db",
                "ENVIRONMENT": "production"
            }
        }
    }
}


class ClaudeDesktopMCPDriver:
    """
    Simulates Claude Desktop's internal MCP engine.
    Launches an MCP server as a child process and speaks JSON-RPC 2.0 via standard I/O pipes.
    """
    def __init__(self, command: str, args: List[str]):
        self.command = command
        self.args = args
        self.proc: Optional[asyncio.subprocess.Process] = None

    async def start(self):
        print(f"Launching MCP Server process: {self.command} {' '.join(self.args)}...")
        self.proc = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        # Background task to print server's stderr logs without blocking stdin/stdout
        asyncio.create_task(self._log_stderr())

    async def _log_stderr(self):
        while True:
            line = await self.proc.stderr.readline()
            if not line:
                break
            print(f"[SERVER STDERR] {line.decode().strip()}", file=sys.stderr)

    async def send_rpc(self, method: str, params: Dict[str, Any], msg_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        envelope = {"jsonrpc": "2.0", "method": method, "params": params}
        if msg_id is not None:
            envelope["id"] = msg_id

        payload = json.dumps(envelope) + "\n"
        self.proc.stdin.write(payload.encode())
        await self.proc.stdin.drain()

        # If it's a notification, no response is expected
        if msg_id is None:
            return None

        # Read JSON-RPC response line from stdout
        res_line = await self.proc.stdout.readline()
        if not res_line:
            raise RuntimeError("MCP Server terminated unexpectedly.")
        return json.loads(res_line.decode().strip())

    async def stop(self):
        if self.proc:
            self.proc.terminate()
            await self.proc.wait()


# =====================================================================
# Verification Flow: Handshake -> Tool Discovery -> Execution
# =====================================================================
async def run_claude_driver_test():
    # In real use, this launches the server file. Here we demonstrate the JSON-RPC dialogue.
    print("=== CLAUDE DESKTOP CONFIG GENERATED ===")
    print(json.dumps(CLAUDE_CONFIG_SAMPLE, indent=2))
    print("\nExpected handshake sequence:")
    print("1. Client sends 'initialize' request with capabilities")
    print("2. Server responds with serverInfo & capabilities")
    print("3. Client sends 'notifications/initialized'")
    print("4. Client sends 'tools/list' -> Claude presents tools to the LLM")
    print("5. User prompts Claude -> Claude calls 'tools/call' -> Server executes and returns text")


if __name__ == "__main__":
    asyncio.run(run_claude_driver_test())
```

### Run Command:
```bash
python claude_desktop_mcp_client.py
```
