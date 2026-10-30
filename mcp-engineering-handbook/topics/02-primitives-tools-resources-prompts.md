# 02 — MCP Primitives: Tools, Resources and Prompts

MCP servers can expose different kinds of capabilities. The three concepts to distinguish are **tools**, **resources** and **prompts**.

## 1. Tools: operations a client can invoke

A tool represents an operation, such as searching tickets, creating an issue, calculating a quote or querying an order. A tool has a name, description and input schema. Implementations may also provide output schema or structured content.

A tool is not merely a Python function. Its description and schema are part of the interface consumed by clients and potentially used by a model to decide when and how to call it.

### Design a useful tool contract

A good contract states:
- what the operation does and does not do;
- required and optional arguments;
- valid values and constraints;
- whether it reads or mutates state;
- expected result;
- possible failures.

Bad: `do_stuff(data)`.

Better: `search_open_incidents(status?, limit=10)` where `status` is a documented enum and `limit` is bounded between 1 and 50.

### JSON Schema example

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "minLength": 2,
      "maxLength": 120
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 25,
      "default": 10
    }
  },
  "required": ["query"],
  "additionalProperties": false
}
```

A schema helps clients construct valid calls, but server-side validation remains mandatory. Model-generated arguments are untrusted input.

### Result design
Return concise, useful content. Prefer stable machine-readable fields where deterministic processing matters. Include units and timestamps. Avoid secrets, raw stack traces and unnecessary internal details. A tool execution failure can be represented through the tool-result error convention (including `isError` where applicable); this differs from a JSON-RPC protocol error.

## 2. Resources: addressable context

A resource represents data or context identified by a URI. Examples:
- `file:///workspace/README.md`
- `docs://policies/refunds`
- `incident://INC-1042`

Clients can list resources and read a resource by URI. Resource templates describe parameterised URI patterns.

A static resource identifies a concrete item, for example `docs://policies/refunds`. A template might describe `customer://{customer_id}/profile`.

A resource should have a stable URI, clear name/description, MIME type when meaningful, access policy and documented freshness expectations.

### Resource freshness
Do not assume that a resource is live merely because it can be read. State whether it is immutable, periodically refreshed, cached or read from a live backend. Where supported, use resource update notifications and list-changed notifications appropriately.

## 3. Prompts: reusable interaction templates

A prompt is a reusable template exposed by a server. It can accept arguments and return messages a host can use in a conversation.

Examples:
- summarise a support ticket in a standard format;
- review a pull request against team conventions;
- generate a release checklist;
- explain a policy to a specified audience.

A prompt does not perform the external action itself. Keep the action in a tool. Never use a prompt to smuggle hidden instructions or override host safety policy.

## 4. Choosing the correct primitive

| Requirement | Primitive | Reason |
|---|---|---|
| Search orders | Tool | Executes a query/action |
| Read a policy document | Resource | Exposes addressable data |
| Create a ticket | Tool | Mutates external state |
| Standard incident-summary format | Prompt | Reusable interaction template |
| Read a customer record | Resource or tool | Depends on URI/addressability and access semantics |

A common mistake is exposing everything as a tool. If the consumer needs a stable document, a resource may express the intent more clearly.

## 5. Naming and description guidelines
- Use action-oriented tool names: `search_orders`, `create_ticket`.
- Avoid ambiguous names such as `query`, `execute`, `process`.
- State important constraints and side effects.
- Never describe a mutating tool as read-only.
- Do not rely on the model to infer required arguments from implementation code.

## 6. Illustrative Python tool

Check exact imports and APIs against your pinned SDK version.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("support-tools")

@mcp.tool()
def calculate_refund(order_total: float, refund_percent: float) -> dict:
    """Calculate a proposed refund. Does not issue a payment."""
    if order_total < 0:
        raise ValueError("order_total must be non-negative")
    if not 0 <= refund_percent <= 100:
        raise ValueError("refund_percent must be between 0 and 100")

    amount = round(order_total * refund_percent / 100, 2)
    return {
        "order_total": order_total,
        "refund_percent": refund_percent,
        "proposed_refund": amount,
        "currency": "INR",
        "issued": False,
    }
```

The description explicitly says it calculates a proposal and does not issue a payment. That is an important contract boundary.

## 7. Security implications
- A read-only tool can still disclose sensitive data.
- A resource URI must not become an insecure direct object reference.
- Prompt content may be stale or untrusted.
- Tool descriptions influence model behaviour and should be reviewed.
- The server must authorize every read and write.

## 8. Practical tasks
1. Design tools for search, reserve and cancel in a library system.
2. Design resources for the public borrowing policy and a user's reservation record.
3. Design a prompt for explaining late fees.
4. Write schemas with bounds, required fields and `additionalProperties: false`.
5. Classify each capability as public-read, sensitive-read or state-changing.
6. Explain why a `user_id` argument cannot establish caller identity.

## 9. Interview questions
- Difference between tool and resource?
- When would you use a prompt?
- What is a resource template?
- Why is a tool description part of the security surface?
- Does JSON Schema remove server-side validation?
- How should destructive operations be exposed?
