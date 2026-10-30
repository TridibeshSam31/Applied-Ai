# Capstone — Customer Support MCP Server

Build a realistic MCP server that exposes a small, secure support-ticket workflow. The scope is intentionally limited so one developer can finish a strong version without building an entire help-desk platform.

## 1. Product brief

A support team wants an AI host to:
- search tickets visible to the authenticated user;
- retrieve a ticket;
- add an internal note;
- assign a ticket to an agent;
- read the support policy.

The server must prevent cross-tenant access. Mutations must be auditable and safe against accidental duplicate execution.

## 2. Scope

**In scope:** Python MCP server using the official SDK; PostgreSQL or SQLite for development; tools, one resource and one prompt; authenticated principal; tenant/object authorization; structured logs and correlation IDs; unit, contract, integration and security tests; optional Docker development environment.

**Out of scope initially:** full chat UI, payment processing, arbitrary SQL/shell execution, autonomous deletion and production OAuth provider implementation before the core authorization model works.

## 3. Tool contract

| Tool | Inputs | Behaviour | Risk |
|---|---|---|---|
| `search_tickets` | status?, assignee?, limit | Search caller's tenant | Sensitive read |
| `get_ticket` | ticket_id | Return one visible ticket | Sensitive read |
| `add_internal_note` | ticket_id, body, idempotency_key | Add internal note | State change |
| `assign_ticket` | ticket_id, assignee_id, idempotency_key | Assign if permitted | State change |

Use strict schemas, bounded strings and maximum result counts. Never accept `tenant_id` or `authenticated_user_id` as a model-controlled argument.

## 4. Resource and prompt

**Resource:** `support://policies/ticket-handling`  
Expose the current ticket-handling policy as read-only context. Define MIME type and freshness expectations.

**Prompt:** `draft_ticket_summary`  
Ask for a structured summary: issue, customer impact, current status, missing information and recommended next action. Do not let the prompt perform mutations; actions belong in tools.

## 5. Data model

Minimal relational starting point:

```sql
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    assignee_id TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE ticket_notes (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets(id),
    tenant_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    idempotency_key TEXT NOT NULL,
    UNIQUE (tenant_id, author_id, idempotency_key)
);

CREATE TABLE audit_events (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    target_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
```

Review foreign-key consistency, indexes, retention and whether the idempotency uniqueness scope matches the business operation. A dedicated idempotency table may be better for complex workflows.

## 6. Architecture

```text
AI Host
  |
MCP Client
  |
MCP transport
  |
MCP Server
  |-- authenticate request
  |-- validate tool arguments
  |-- derive trusted principal
  |-- authorize action and object
  |
TicketService
  |
TicketRepository
  |
Database
```

Keep handlers thin. Put business rules in `TicketService`; database access belongs in `TicketRepository`.

## 7. Authorization rules

Example policy:
- support agent can read tickets in their tenant;
- agent can add notes to tickets in their tenant;
- only users with `tickets:assign` can assign;
- a caller cannot read or mutate another tenant's ticket;
- tenant identity comes from authenticated context, never tool arguments.

A security design without cross-tenant tests is incomplete.

## 8. Idempotency behaviour

For `add_internal_note`:
1. Caller supplies a key for the logical action.
2. Server scopes the key to tenant and authenticated actor.
3. Server checks whether the key already has an outcome.
4. If present, return the previous outcome.
5. Otherwise create note and audit event in one transaction.
6. Persist key/outcome atomically.

If the same key is reused with materially different arguments, reject it. Do not silently return an unrelated outcome.

## 9. Implementation milestones

### Milestone 1 — Domain
- [ ] Define ticket and principal models.
- [ ] Implement repository and service.
- [ ] Add validation and unit tests.
- [ ] Seed two tenants with separate tickets.

### Milestone 2 — MCP interface
- [ ] Register `search_tickets`.
- [ ] Register `get_ticket`.
- [ ] Register policy resource.
- [ ] Register summary prompt.
- [ ] Verify discovery and calls with an MCP client.

### Milestone 3 — Identity and security
- [ ] Add trusted authentication context.
- [ ] Enforce tenant scoping.
- [ ] Add permission check for assignment.
- [ ] Add cross-tenant denial tests.
- [ ] Review descriptions and schemas.

### Milestone 4 — Mutations and reliability
- [ ] Add internal note.
- [ ] Add assignment.
- [ ] Implement idempotency.
- [ ] Add transaction boundaries.
- [ ] Add safe error mapping.

### Milestone 5 — Operations
- [ ] Add structured logs.
- [ ] Add correlation IDs.
- [ ] Add timeouts and bounded concurrency.
- [ ] Add graceful shutdown.
- [ ] Add Docker configuration if useful.

### Milestone 6 — Verification
- [ ] Unit tests.
- [ ] Contract tests.
- [ ] Integration tests.
- [ ] Security tests.
- [ ] Load test and written results.
- [ ] Setup and architecture documentation.

## 10. Acceptance criteria

The project is complete when:
- a client initializes and discovers expected capabilities;
- read tools return only records visible to the principal;
- cross-tenant access is denied;
- assignment requires the correct permission;
- duplicate note calls with the same key do not create duplicate notes;
- failures return safe, understandable errors;
- logs trace a request without exposing secrets;
- tests cover critical happy and unhappy paths;
- README explains setup, configuration, security and limitations.

## 11. Suggested repository layout

```text
customer-support-mcp/
├── README.md
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── src/support_mcp/
│   ├── server.py
│   ├── auth.py
│   ├── context.py
│   ├── schemas.py
│   ├── services/
│   ├── repositories/
│   └── observability.py
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   └── security/
└── docs/
    ├── architecture.md
    └── threat-model.md
```

## 12. Portfolio demo

Show capability discovery, successful ticket search, ticket retrieval, denied cross-tenant request, permitted note creation, duplicate idempotent request returning the original outcome, audit event and correlation ID, and test/load-test evidence.

Never fabricate benchmark numbers. Record hardware, workload, duration, concurrency, p95 latency and error rate.
