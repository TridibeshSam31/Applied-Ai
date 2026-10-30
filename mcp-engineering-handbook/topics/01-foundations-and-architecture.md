# 01 — MCP Foundations and Architecture

## 1. The integration problem

An AI application often needs information or actions outside the model's context: databases, files, issue trackers, calendars, internal APIs or deployment systems.

Without a shared integration contract, every host builds custom adapters. Each adapter invents its own discovery, argument format, authentication assumptions and error behaviour. The result is duplicated engineering and integrations that are difficult to reuse.

**Model Context Protocol (MCP)** defines a common protocol through which an AI application can discover and use capabilities exposed by external servers. It standardises the interaction boundary. It does not make model reasoning correct, guarantee that tools are safe, or replace your business logic.

A useful mental model:
- MCP is the integration protocol.
- An MCP server is the adapter and policy boundary around a capability.
- The host is the user-facing AI application.
- The client is the protocol component that connects the host to a server.

## 2. What MCP is and is not

| MCP is | MCP is not |
|---|---|
| A protocol for exchanging context and invoking capabilities | An LLM |
| A standardised client-server interaction model | A database |
| A way to expose tools, resources and prompts | An agent framework |
| Transport-independent at the conceptual protocol layer | A guarantee of secure execution |
| An integration boundary | A replacement for REST or domain services |

MCP is sometimes compared to USB: a common interface reduces the need for every consumer and device to invent a unique integration. The analogy is useful, but MCP is a software protocol with explicit messages, lifecycle and capabilities.

## 3. The three participants

### Host
The host is the AI application the user interacts with. It commonly manages the conversation/model, decides which servers to connect to, creates MCP clients, presents server capabilities to the model, applies host-level policy and handles user consent.

### Client
An MCP client is the protocol component inside the host that maintains a connection to one server. It performs initialization, capability negotiation, sends requests, receives responses and handles notifications and transport/session details.

A host connecting to three servers will commonly manage three client connections.

### Server
An MCP server exposes capabilities. It can list and execute tools, expose resources, provide prompt templates, validate inputs, authenticate callers, authorize operations and call internal services or databases. A server does not need to contain an LLM.

```text
                 AI HOST
       conversation / model / UI
          |         |         |
       Client A  Client B  Client C
          |         |         |
       Server A  Server B  Server C
        GitHub     Files    Internal API
```

Do not use host and client interchangeably. The host is the application; the client is its protocol connection component.

## 4. Example request flow

User: “Find open incidents assigned to me.”

1. The host receives the request.
2. The model or host determines that an incident-search capability may help.
3. The client has discovered the server's tools (or refreshes discovery).
4. The client sends a `tools/call` request with a tool name and arguments.
5. The server validates arguments and checks the authenticated caller's permissions.
6. The server queries the incident system.
7. The server returns a protocol result.
8. The host makes the result available to the model and presents the answer.

The model does not magically receive database access. The server implementation determines what operation occurs and what data is returned.

## 5. MCP versus function calling

Function calling is generally a model/API feature: the model emits structured arguments and the application interprets and executes them. MCP standardises a broader integration layer: discovery, lifecycle, transports and multiple capability types.

They can work together:

```text
User → Host → Model chooses capability
                  |
              MCP Client
                  |
              MCP Server
                  |
          Internal REST API
```

The model may select a tool, but the host/client/server handle protocol and execution.

## 6. MCP versus REST

REST describes resource-oriented HTTP APIs. MCP defines a protocol for AI applications to discover and use capabilities. An MCP server can call a REST API internally.

| Concern | REST | MCP |
|---|---|---|
| Typical consumer | Any HTTP client | MCP-capable host/client |
| Interface | Routes and HTTP methods | Protocol methods and capabilities |
| Discovery | OpenAPI/docs/custom | Protocol list methods |
| Common purpose | Service integration | AI context and capability integration |

MCP does not make REST obsolete. A sensible architecture often keeps a stable domain API and adds an MCP adapter at the boundary.

## 7. Keep domain logic separate

Avoid putting all business logic inside MCP decorators. Prefer:

```text
MCP Tool Handler
      |
Validation + trusted identity
      |
Application Service
      |
Repository / Domain API
      |
Database or external system
```

This lets REST endpoints, background jobs, tests and MCP tools reuse the same domain behaviour.

## 8. Practical exercise

Design an MCP integration for a university project tracker. Identify:
- host, client and server;
- three tools, two resources and one prompt;
- which operations are read-only and which mutate data;
- where authentication and authorization happen.

Draw a sequence diagram for “create a task assigned to me”. Include validation, authorization, persistence and the result.

## 9. Interview questions
1. What problem does MCP solve?
2. Explain host, client and server.
3. Can one host connect to multiple servers?
4. Does an MCP server need an LLM?
5. How is MCP different from REST?
6. How is MCP different from function calling?
7. Where should business logic live?
8. Does MCP itself guarantee safe tool execution?

**Strong answer to 8:** No. MCP standardises interaction. Host and server still need authentication, authorization, validation, consent, least privilege, audit logging and safe output handling.
