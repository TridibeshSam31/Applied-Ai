# 09 — Production MCP Design, Testing and Deployment

A demo proves a tool can run. Production engineering proves it behaves safely and predictably under real workloads, failures and adversarial inputs.

## 1. Reference architecture

```text
                 AI Host
                    |
                MCP Client
                    |
              TLS / Gateway
                    |
             MCP Server Layer
        authn | validation | rate limits
                    |
             Application Services
             /       |        \
       Repository  Policy   External APIs
           |                   |
        Database          SaaS systems
```

Keep the MCP layer thin. It adapts protocol inputs to application services and converts results into protocol outputs.

## 2. Design bounded capabilities

Prefer explicit operations:
- `search_tickets`;
- `get_ticket`;
- `add_ticket_comment`;
- `assign_ticket`.

Avoid a generic tool that can do anything. A `run_sql(query)` tool creates a huge attack surface and makes it difficult to prove what the caller can do.

## 3. Reliability controls

Consider connection pooling, downstream timeouts, bounded concurrency, per-principal rate limits, circuit breakers, retry budgets, idempotency, graceful shutdown, health/readiness checks and backpressure.

Do not add every resilience pattern mechanically. Add it where a workload or dependency needs it and test the failure it addresses.

## 4. Data and tenant design

For multi-tenant services:
- derive tenant identity from authenticated context;
- scope every tenant-owned query;
- add constraints and indexes;
- test cross-tenant access;
- avoid leaking whether another tenant's record exists;
- define retention and deletion policies.

For tickets, candidate indexes might include `(tenant_id, status, updated_at)` and `(tenant_id, assignee_id, status)`, depending on query patterns. Use `EXPLAIN ANALYZE` and realistic data before choosing indexes.

## 5. Testing pyramid

**Unit tests:** domain logic, validation and policy decisions.

**Contract tests:** tool names, descriptions, input schema, output structure and error conventions.

**Integration tests:** start the server and use a real SDK client to initialize, list capabilities and call tools.

**Security tests:** identity, scopes, tenant boundaries, malicious inputs, oversized payloads and approval gates.

**Load tests:** latency and error rate at realistic concurrency. Observe database pool saturation, event-loop blocking, memory growth and downstream throttling.

**End-to-end tests:** exercise the host/client/server workflow using the intended client environment where possible.

## 6. Load testing method

1. Define workload: tool mix, payload sizes, read/write ratio and concurrency.
2. Define success criteria: p95 latency, error rate, throughput and resource ceilings.
3. Establish a low-concurrency baseline.
4. Increase concurrency gradually.
5. Observe where latency rises sharply.
6. Inspect CPU, memory, event loop, connection pool and dependency metrics.
7. Repeat after a change and compare.

Do not report only requests per second. A service returning errors quickly can have high throughput but poor reliability.

## 7. Deployment

For remote deployment:
- containerise the server;
- run as non-root;
- pin dependencies;
- scan dependencies and images;
- inject secrets at runtime;
- use TLS;
- configure resource limits;
- add health/readiness checks;
- use structured logs and metrics;
- maintain a rollback plan.

For local stdio tools, provide a deterministic launch command, document environment requirements, keep stdout protocol-clean and avoid machine-specific paths.

## 8. Operational runbook

Document how to start/stop, verify readiness, find logs/metrics, rotate credentials, disable a compromised tool, roll back, investigate latency and respond to suspected data leakage.

## 9. Production readiness checklist
- [ ] Explicit tool contracts and schemas.
- [ ] Authentication and per-operation authorization.
- [ ] Tenant isolation tested.
- [ ] No secrets in logs or source control.
- [ ] Timeouts on external dependencies.
- [ ] Bounded and safe retries.
- [ ] Idempotency strategy for mutations.
- [ ] Cancellation and shutdown handled.
- [ ] Structured logs, metrics and correlation IDs.
- [ ] Unit, contract, integration and security tests pass.
- [ ] Load test has documented workload and results.
- [ ] Deployment and rollback documented.
- [ ] Tool descriptions reviewed.

## 10. Practical tasks
1. Implement read-only tools first.
2. Add authentication and tenant scope.
3. Add a state-changing operation with idempotency.
4. Add contract and security tests.
5. Run a load test.
6. Write a runbook.
7. Record limitations honestly.

## 11. Interview questions
- What changes when moving local MCP to remote?
- How would you load-test an MCP server?
- Why are p95/p99 more useful than average alone?
- How do you prevent one tenant exhausting shared resources?
- What is backpressure?
- What belongs in a runbook?
- How would you disable a compromised tool?
