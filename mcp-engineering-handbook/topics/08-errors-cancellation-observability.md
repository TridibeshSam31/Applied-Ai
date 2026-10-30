# 08 — Errors, Cancellation, Progress and Observability

Reliable MCP systems need predictable failure behaviour. A tool that works only when every dependency is healthy is not production-ready.

## 1. Separate failure layers

1. **Transport failure:** connection lost, process exited, HTTP timeout.
2. **Protocol failure:** malformed JSON-RPC, unknown method, invalid parameters.
3. **Tool execution failure:** tool was dispatched but the requested operation failed.
4. **Domain failure:** order not found, invalid state transition, permission denied.
5. **Dependency failure:** database unavailable, third-party API rate-limited.
6. **Internal defect:** unexpected exception or bug.

Different failures need different handling. Do not retry a permission denial as if it were a temporary network outage.

## 2. Protocol error versus tool result error

A JSON-RPC error means the protocol request could not be processed as requested, for example because the method is unknown or parameters are invalid.

A tool may return a normal tool-result envelope indicating execution failed (the protocol defines an `isError` convention for tool results). This is useful when the call was understood and dispatched but the operation failed.

Examples:
- unknown tool name: request/protocol handling error;
- known `create_ticket` tool, but project is archived: tool/domain execution failure.

Use the SDK's documented exception and result mechanisms. Never leak stack traces to the model or user.

## 3. Error response design

A useful application error contains a stable category/code, safe message, retryability hint, correlation ID and optional non-sensitive details.

```json
{
  "code": "PROJECT_ARCHIVED",
  "message": "The selected project is archived.",
  "retryable": false,
  "correlation_id": "req_abc123"
}
```

Do not return database connection strings, stack traces, tokens or raw internal exception messages.

## 4. Retry policy

Retries are appropriate only when the failure is plausibly transient and repeating the operation is safe.

Potential retry candidates:
- temporary network errors;
- rate limits, respecting `Retry-After`;
- selected 5xx responses;
- transient database connection failures.

Usually do not retry:
- invalid input;
- authentication failure;
- authorization denial;
- permanent not-found;
- business-rule violation.

Use exponential backoff with jitter and a maximum attempt/time budget. Unbounded retries amplify outages.

## 5. Idempotency

A retry can duplicate a state-changing operation. Suppose `create_payment` succeeds but the response is lost. A retry may create a second payment.

Use an idempotency key tied to the logical operation. The server stores the key and outcome. Repeating the same key returns the prior outcome rather than executing the mutation again.

Define:
- key scope (user, tenant, operation);
- expiry;
- persistence;
- conflict behaviour;
- behaviour when the same key is reused with different arguments.

Naturally idempotent operations can be safer to retry, but verify their semantics.

## 6. Cancellation

Long-running work should stop consuming resources after cancellation/disconnection where cancellation is supported end-to-end.

A cancellation-aware operation should observe cancellation signals, stop downstream work where possible, close streams, release locks and avoid partial state. Use transactions or compensating actions for mutations.

Cancellation is not rollback by magic. If an external payment has already been issued, cancelling the client's wait does not reverse it.

## 7. Progress

Progress updates can help a host communicate that work is ongoing. They should be meaningful, bounded, rate-limited, safe to expose and correlated with the operation. Do not invent percentages without a basis.

## 8. Logging and tracing

Useful structured fields:
- timestamp, severity, service and environment;
- server and tool name;
- request/correlation ID;
- privacy-safe subject and tenant identifiers;
- duration and outcome/error category;
- downstream dependency name.

Never log access tokens, API keys, passwords or full sensitive records. A trace should connect:

`host request → MCP method → tool handler → application service → database/API`

## 9. Metrics

Track:
- tool calls by tool and outcome;
- latency percentiles (p50/p95/p99);
- error rate by category;
- active sessions/connections;
- downstream latency;
- timeout and cancellation counts;
- rate-limit events;
- queue depth and resource saturation.

Avoid high-cardinality labels such as raw user IDs, request IDs or arbitrary tool arguments.

## 10. Practical tasks
1. Force a downstream timeout and return a safe error.
2. Add bounded exponential backoff for a transient read.
3. Add an idempotency key to a mutation.
4. Simulate a lost response after successful mutation.
5. Add cancellation to a long-running task.
6. Emit structured logs with correlation IDs.
7. Build a dashboard for tool latency and failure rate.

## 11. Interview questions
- Transport error versus tool error?
- When should a client retry?
- Why is retrying create dangerous?
- What is idempotency?
- Does cancellation roll back side effects?
- What should be logged?
- Which metrics would you alert on?
