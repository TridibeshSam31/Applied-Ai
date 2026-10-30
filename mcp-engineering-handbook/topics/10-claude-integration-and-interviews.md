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
