# 06 — FastAPI Integration, Authentication and Identity

FastAPI and MCP solve different problems. FastAPI is a web framework for HTTP APIs. MCP is a protocol for AI hosts and clients to discover and invoke capabilities. They can coexist in one application.

## 1. Two interfaces, one application layer

```text
                   Application Services
                    /              \
             FastAPI route       MCP tool
                  |                 |
             HTTP contract      MCP contract
                    \              /
                    Domain / Repository
                              |
                           Database
```

Keep protocol surfaces separate while sharing application services. Do not assume mounting an MCP transport automatically converts every FastAPI route into an MCP tool.

## 2. Authentication versus authorization

**Authentication:** Who is making the request? Examples include a validated OAuth access token, signed JWT or service identity.

**Authorization:** What may this principal do? Examples include reading incidents in one tenant, creating tickets in permitted projects or approving refunds with a specific role.

A valid token does not mean unrestricted access.

## 3. Trusted identity propagation

Secure flow:
1. Transport receives the request.
2. Authentication layer validates credentials.
3. Application creates a trusted principal/context.
4. Tool handler obtains that context through the SDK's supported mechanism.
5. Application service authorizes the operation and object.
6. Repository queries are scoped to tenant and permissions.

Never accept a model-supplied `user_id`, `role` or `tenant_id` as proof of identity.

Dangerous design:

```python
@mcp.tool()
def get_customer(customer_id: str, user_id: str):
    # Dangerous: the caller can choose the identity being checked.
    return repository.get_customer(customer_id, user_id)
```

Better conceptually:

```python
@mcp.tool()
async def get_customer(customer_id: str, context=trusted_request_context):
    principal = context.authenticated_principal
    authorize_customer_read(principal, customer_id)
    return await customer_service.get_visible_customer(
        principal=principal,
        customer_id=customer_id,
    )
```

The exact context injection API is SDK/version-specific. The requirement is not: identity must come from a trusted authentication layer.

## 4. JWT validation checklist

If using JWT access tokens, validate:
- signature using trusted key material;
- allowed signing algorithm;
- issuer (`iss`);
- audience (`aud`);
- expiration (`exp`);
- not-before (`nbf`) when present;
- token type and intended use;
- scopes/claims required by the application.

Do not merely base64-decode a JWT and trust its payload. Decoding is not validation.

Plan for key rotation, clock skew, revocation strategy and appropriate token lifetime.

## 5. OAuth and delegated access

For remote deployments, OAuth-based authorization may be appropriate. The exact flow depends on the current MCP authorization specification, client capabilities and deployment model.

Understand:
- resource server: protects the API/resource;
- authorization server: issues tokens;
- client: obtains tokens;
- audience/resource: identifies where a token may be used;
- scope: limits what the token authorizes.

Do not copy a generic OAuth flow blindly. Follow current MCP authorization guidance and the host's supported flow. Never pass a token intended for one service to an unrelated downstream service.

## 6. FastAPI integration pattern

A FastAPI route can call a shared application service:

```python
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/incidents")
async def list_incidents(principal=Depends(require_principal)):
    return await incident_service.list_visible_to(principal)
```

An MCP tool should call the same service but obtain its principal from the MCP transport's trusted auth/context mechanism. Do not reuse FastAPI's `Depends` object directly inside a tool handler unless the SDK explicitly supports that integration.

## 7. Multi-tenant isolation

Risky query:

```sql
SELECT * FROM incidents WHERE id = :incident_id;
```

Safer pattern:

```sql
SELECT *
FROM incidents
WHERE id = :incident_id
  AND tenant_id = :authenticated_tenant_id;
```

For complex systems, enforce tenant scoping in repositories or database policies as well as service-level authorization. Defence in depth helps prevent a forgotten filter from leaking data.

## 8. Practical tasks
1. Add a FastAPI endpoint and MCP tool sharing one incident service.
2. Implement a principal with `subject`, `tenant_id` and scopes.
3. Test expired token, wrong audience and missing scope.
4. Add a cross-tenant access test.
5. Prove a model cannot change identity by passing a different `user_id`.
6. Document token acquisition, validation, scope and rotation.

## 9. Interview questions
- Authentication versus authorization?
- Why is a user ID argument not trustworthy identity?
- How do FastAPI and MCP fit together?
- Which JWT claims should be validated?
- What is an OAuth scope?
- How do you prevent cross-tenant leakage?
- Why check token audience?
