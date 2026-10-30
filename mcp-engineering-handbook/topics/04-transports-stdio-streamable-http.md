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
