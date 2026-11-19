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


---

## 12. Complete Production Implementation: Error Handling, Cancellation & Observability 💻

Below is an end-to-end Python implementation demonstrating production observability and error resilience:
1. **Idempotency Keys & Safe Retries:** Caches completed tool executions by `Idempotency-Key` to prevent double-charging or duplicated actions during network retries.
2. **Active Request Cancellation:** Handles `notifications/cancelled` by cancelling the running `asyncio.Task` and releasing upstream resources cleanly.
3. **Structured Observability:** Emits structured latency, tool error metrics, and OpenTelemetry-style trace spans for every tool call.

```python
"""
mcp_errors_cancellation_observability.py
Production Implementation of MCP Cancellation, Idempotency, and Structured Observability.
"""

import time
import json
import asyncio
from typing import Dict, Any, Optional


class MCPObservableServer:
    def __init__(self):
        # In-flight task tracker: request_id -> asyncio.Task
        self.active_tasks: Dict[str, asyncio.Task] = {}
        # Idempotency cache: idempotency_key -> cached_result
        self.idempotency_cache: Dict[str, Any] = {}
        # Simple metrics counter
        self.metrics = {"total_calls": 0, "errors": 0, "cancelled": 0}

    async def cancel_task(self, request_id: str):
        """Cancels an in-flight tool execution when receiving notifications/cancelled."""
        task = self.active_tasks.get(request_id)
        if task and not task.done():
            print(f">>> [Cancellation Engine] Cancelling active request ID: {request_id}")
            task.cancel()
            self.metrics["cancelled"] += 1

    async def execute_tool_with_observability(
        self,
        request_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a tool with timing, idempotency protection, and cancellation tracking.
        """
        self.metrics["total_calls"] += 1
        start_time = time.perf_counter()

        # Idempotency check: Return cached output if already executed!
        if idempotency_key and idempotency_key in self.idempotency_cache:
            print(f">>> [Idempotency Hit] Replaying previous response for key: {idempotency_key}")
            return self.idempotency_cache[idempotency_key]

        # Wrap tool execution in an asyncio task for cancellation support
        coro = self._run_tool_logic(tool_name, arguments)
        task = asyncio.create_task(coro)
        self.active_tasks[request_id] = task

        try:
            result = await task
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            response = {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "isError": False
            }

            if idempotency_key:
                self.idempotency_cache[idempotency_key] = response

            # Emit structured log
            print(f">>> [Observability Span] Tool='{tool_name}' | Status=SUCCESS | Latency={latency_ms:.2f}ms")
            return response

        except asyncio.CancelledError:
            print(f">>> [Observability Span] Tool='{tool_name}' | Status=CANCELLED by client.")
            raise

        except Exception as exc:
            self.metrics["errors"] += 1
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            print(f">>> [Observability Span] Tool='{tool_name}' | Status=ERROR | Error='{exc}' | Latency={latency_ms:.2f}ms")
            # Return application-level tool error (isError: true) rather than crashing protocol
            return {
                "content": [{"type": "text", "text": f"Tool execution failed: {str(exc)}"}],
                "isError": True
            }

        finally:
            self.active_tasks.pop(request_id, None)

    async def _run_tool_logic(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "long_running_export":
            # Simulate heavy task
            await asyncio.sleep(2.0)
            return {"exported_rows": 150000, "file_path": "/exports/data.csv"}
        elif name == "charge_credit_card":
            amount = args.get("amount", 0)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
            return {"charge_id": "ch_9812", "status": "paid", "amount": amount}
        raise ValueError(f"Unknown tool: {name}")


# =====================================================================
# Verification Runner
# =====================================================================
async def run_observability_demo():
    server = MCPObservableServer()

    print("\n--- Test 1: Idempotency Protection on Payment Calls ---")
    res1 = await server.execute_tool_with_observability(
        request_id="req-1",
        tool_name="charge_credit_card",
        arguments={"amount": 1000},
        idempotency_key="idemp-key-abc-123"
    )
    print("Call 1 Response:", res1)

    # Re-sending with the same key must return instantly without executing again
    res2 = await server.execute_tool_with_observability(
        request_id="req-2",
        tool_name="charge_credit_card",
        arguments={"amount": 1000},
        idempotency_key="idemp-key-abc-123"
    )
    print("Call 2 Response (from cache):", res2)

    print("\n--- Test 2: Active Task Cancellation ---")
    # Launch heavy export task in background
    long_task = asyncio.create_task(
        server.execute_tool_with_observability(
            request_id="req-heavy-99",
            tool_name="long_running_export",
            arguments={}
        )
    )

    await asyncio.sleep(0.3)
    # User closes browser / cancels request
    await server.cancel_task("req-heavy-99")

    try:
        await long_task
    except asyncio.CancelledError:
        print("Confirmed: Task was cleanly cancelled!")

    print(f"\nFinal Metrics Summary: {server.metrics}")


if __name__ == "__main__":
    asyncio.run(run_observability_demo())
```

### Run Command:
```bash
python mcp_errors_cancellation_observability.py
```
