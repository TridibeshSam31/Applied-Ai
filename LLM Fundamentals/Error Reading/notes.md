# API Errors & Failure Handling 🔴🔴 — LLM Fundamentals

Ab hum **actual backend engineering** mein enter kar rahe hain. Ye topic halka mat le — production mein sabse zyada bugs isi area mein aate hain.

LLM API ko aise mat soch:

```
request → LLM → response
```

Production mein reality kuch aisi hai:

```
request
   ↓
LLM Provider
   ↓
┌───────────────┐
│ success       │
│ timeout       │
│ 429           │
│ 4xx           │
│ 5xx           │
│ network error │
│ invalid output│
└───────────────┘
```

Tere gateway ko har failure ko **intelligently** handle karna padega — sab kuch ek jaisa treat nahi karna.

## 1. First Principle

Ek strong backend engineer ka mindset:

> **Failure is normal.**

Especially external APIs ke saath. OpenAI/Anthropic/Gemini/etc. tere control mein nahi hain.

Teri system ko ye assume karna hi chahiye:

- Provider can fail
- Network can fail
- Client can disconnect
- Model can timeout
- Rate limit can happen
- Response can be invalid

Ye sab "edge cases" nahi hain — production mein ye **normal cases** hain.

## 2. HTTP Status Codes

Basic categories:

```
2xx → Success
4xx → Client/request problem
5xx → Server/provider problem
```

Ek LLM Gateway ke liye, kuch codes particularly important hain — inko detail mein samajhte hain.

## 3. 400 — Bad Request

Request khud invalid hai.

Example:

```json
{
  "model": "does-not-exist",
  "messages": []
}
```

ya invalid parameters.

Mental model:

```
Client
 ↓
❌ Invalid request
 ↓
400
```

**Kya tujhe retry karna chahiye?**

Usually: **NO.**

Kyunki exact same invalid request dobara bhejne se wo fix nahi hoti.

```
400
 ↓
retry ❌
 ↓
400
 ↓
retry ❌
 ↓
400
```

**Ye pointless hai** — jab tak tu request khud fix nahi karta, wahi error baar-baar aayegi.

## 4. 401 — Unauthorized

Usually authentication/API-key ka problem.

```
Client
 ↓
Provider
 ↓
❌ invalid credentials
 ↓
401
```

Yahan bhi: **Blindly retry mat kar.**

Tujhe credentials/configuration fix karni hai.

## 5. 403 — Forbidden

Request samajh mein aayi, lekin caller ko wo perform karne ki permission nahi hai.

Example:

```
API key
 ↓
Provider
 ↓
Model/resource not permitted
 ↓
403
```

Usually: **Retry mat kar.**

## 6. 404 — Not Found

Iska matlab ho sakta hai requested resource/model/endpoint exist nahi karta.

Example:

```
model = "xyz"
        ↓
provider
        ↓
404
```

Usually: **Same request retry mat kar.**

## 7. 429 — Too Many Requests ⭐⭐⭐

**Ye extremely important hai.**

```
Your Gateway
      ↓
Provider
      ↓
429 Too Many Requests
```

Matlab tu kisi rate/usage limit se takra gaya hai.

Isme ye cheezein involve ho sakti hain:

- requests per minute
- tokens per minute
- concurrency
- quota

Exact limits provider/model/account pe depend karte hain.

**Kya tujhe retry karna chahiye?**

**Potentially yes.**

Lekin:

```
429
 ↓
immediate retry
 ↓
429
 ↓
immediate retry
 ↓
429
```

**Ye terrible hai** — immediate retry se rate limit aur bhi worse ho sakta hai.

Correct approach agle topic mein seekhega: **Exponential Backoff + Jitter.**

## 8. 500 — Internal Server Error

Provider ko internal problem hua.

```
Client
 ↓
Gateway
 ↓
Provider
 ↓
💥
 ↓
500
```

**Potentially retryable.**

Lekin tujhe automatically nahi pata ki har 500 ko indefinitely retry karna chahiye ya nahi.

Use kar:

```
limited retries
+
backoff
+
timeouts
```

## 9. 502 / 503 / 504

Ye especially relevant hain jab tu ek gateway build kar raha ho.

### 502 — Bad Gateway

Often matlab hai koi upstream server/proxy ne invalid response return kiya.

### 503 — Service Unavailable

Provider/service temporarily unavailable hai.

### 504 — Gateway Timeout

Upstream service expected time ke andar respond nahi kar paayi.

Ye often **potentially transient** hote hain.

Toh:

```
502/503/504
      ↓
possibly retry
```

appropriate limits ke saath.

## 10. Ek Retry Classification Banao

Ye mat likh:

```python
if error:
    retry()
```

**Ye bad hai.**

Iske bajaye:

```
                 ERROR
                   │
          ┌────────┴────────┐
          ↓                 ↓
      Retryable          Permanent
          │                 │
          ↓                 ↓
      Retry             Return error
```

Example table:

| Error | Usually retry? |
|---|---|
| 400 | ❌ |
| 401 | ❌ |
| 403 | ❌ |
| 404 | ❌ |
| 429 | 🟡 Yes, carefully |
| 500 | 🟡 Potentially |
| 502 | 🟡 Potentially |
| 503 | 🟡 Potentially |
| 504 | 🟡 Potentially |
| Network timeout | 🟡 Potentially |

**"Potentially" important hai.** Tera retry policy operation, provider, timeout, aur error details pe depend karta hai — koi blanket rule nahi hai.

## 11. Timeouts ⭐⭐⭐

Socho:

```
Gateway
   ↓
Provider
   ↓
.............
.............
.............
```

Kya ho agar provider le raha hai:

```
10 seconds?
60 seconds?
5 minutes?
```

Tu connections indefinitely open nahi rakh sakta.

**Tere gateway ko ek timeout chahiye.**

Conceptually:

```
Request
 ↓
Provider
 ↓
wait
 ↓
timeout reached
 ↓
cancel/fail
```

Example:

```python
import httpx

async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(...)
```

Exact timeout values teri workload aur provider behavior ke basis pe choose honi chahiye, blindly copy mat kar.

## 12. Connection Errors

Network fail ho sakta hai isse pehle ki tujhe koi HTTP response mile bhi.

Example:

```
Gateway
   │
   │─────── X ─────── Provider
```

Possible causes:

- DNS failure
- connection reset
- network interruption
- TLS issue
- provider connectivity problem

Tera code distinguish karna chahiye:

```
HTTP error
```

vs:

```
Network/transport error
```

kyunki doosre case mein koi HTTP status code hi nahi hota.

## 13. Invalid Model Output

Yahan Topic 6 wapas aata hai.

Maan le tu expect karta hai:

```json
{
  "priority": "high"
}
```

lekin parsing fail ho jaati hai.

```
LLM
 ↓
response
 ↓
Pydantic
 ↓
❌ validation failure
```

**Ye same nahi hai:**

```
HTTP 500
```

**Ye ek application-level failure hai.**

Teri system ko decide karna hoga:

- retry
- fallback
- return structured error

## 14. Error Handling Layers

Tere Gateway mein multiple layers honi chahiye.

```
                   Request
                      │
                      ▼
              Request Validation
                      │
                      ▼
                Rate Limiting
                      │
                      ▼
                Provider Call
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
       Success     HTTP Error   Network Error
          │           │           │
          ↓           ↓           ↓
      Response    Classify      Classify
                      │
                 ┌────┴────┐
                 ↓         ↓
              Retry     Return
```

Phir ek successful response ke baad:

```
Provider response
       ↓
Parse
       ↓
Validate
       ↓
Business checks
       ↓
Return
```

## 15. Provider Internals Ko Blindly Expose Mat Kar

Maan le OpenAI kuch detailed internal error return karta hai.

Tera client ko necessarily raw provider response nahi milna chahiye.

**Bad:**

```
Provider's entire internal error
        ↓
Client
```

**Better:**

```json
{
  "error": {
    "code": "upstream_rate_limit",
    "message": "The model provider rate limit was exceeded.",
    "request_id": "req_123"
  }
}
```

Tere gateway ko ek **stable error contract** establish karna chahiye.

Ye gateway build karne ke actual reasons mein se ek hai.

## 16. Request IDs ⭐⭐⭐

Har request ko ek identifier milna chahiye.

Example:

```
req_01JXYZ...
```

Flow:

```
Client
  ↓
Gateway
  ↓
request_id = req_123
  ↓
Provider
  ↓
Error
```

Logs:

```
req_123
model=...
status=429
latency=...
```

Ab jab user kahe:

> "My request failed."

tu dhoond sakta hai:

```
req_123
```

aur investigate kar sakta hai.

**Yehi observability hai.**

## 17. Error Logging

Ye mat kar sirf:

```python
print("error")
```

**Structured information log kar:**

```json
{
  "request_id": "req_123",
  "model": "model-x",
  "provider": "provider-a",
  "status": 429,
  "error_type": "rate_limit",
  "retryable": true,
  "attempt": 2
}
```

Baad mein tu probably structured logging use karega, `print` ke bajaye.

## 18. Streaming Failures Ko Aur Bhi Mushkil Banati Hai

Yaad hai Topic 5?

**Normal:**

```
Request
 ↓
Provider
 ↓
Error
```

**Streaming:**

```
Request
 ↓
Provider
 ↓
chunk
 ↓
chunk
 ↓
chunk
 ↓
💥 failure
```

Client ko already partial data mil chuka hai.

Isliye tu error ko treat nahi kar sakta jaise kuch hua hi nahi.

Tere gateway ko samajhna hoga:

```
partial response
+
stream termination
+
client cancellation
+
upstream failure
```

## 19. Fallback Models

Maan le:

```
Primary model
      ↓
503
```

Tera gateway potentially ye kar sakta hai:

```
Primary
  ↓
failure
  ↓
Fallback
  ↓
response
```

Example:

```
GPT-X
  ↓
unavailable
  ↓
Claude-X
  ↓
response
```

Lekin **har error pe blindly fallback mat kar.**

Agar request hai:

```
400 invalid request
```

model switch karne se ye probably fix nahi hoga.

Fallback certain transient/provider-specific failures ke liye zyada appropriate hai — structural request problems ke liye nahi.

## 20. Error Handling Architecture

Tera eventual Gateway:

```
                         Client
                           │
                           ▼
                    ┌────────────┐
                    │  Gateway   │
                    └─────┬──────┘
                          │
                     Validate
                          │
                     Rate Limit
                          │
                     Model Router
                          │
                          ▼
                    ┌────────────┐
                    │  Provider  │
                    └─────┬──────┘
                          │
               ┌──────────┼──────────┐
               ↓          ↓          ↓
            Success      429       5xx
               │          │          │
               │          └────┬─────┘
               │               ↓
               │           Retry policy
               │               │
               │          ┌────┴────┐
               │          ↓         ↓
               │        Retry     Fallback
               │
               ▼
           Validate
               │
               ▼
             Client
```

## 21. Sabse Bada Mistake

Ye mat likh:

```python
try:
    response = call_llm()
except Exception:
    retry()
```

**Ye terrible hai.**

Kyun?

Kyunki tu treat kar raha hai:

```
400
401
403
429
500
timeout
invalid output
programming bug
```

sabko **same cheez ki tarah**.

**Ye same nahi hain.**

Ek acchi system failures ko **classify** karti hai.

## 22. Tera Code Eventually Kaisa Dikhna Chahiye

Conceptually:

```python
async def call_provider(request):

    try:
        response = await provider.generate(request)

        return response

    except RateLimitError as e:
        raise RetryableError("rate_limit") from e

    except TimeoutError as e:
        raise RetryableError("timeout") from e

    except AuthenticationError as e:
        raise PermanentError("authentication") from e

    except BadRequestError as e:
        raise PermanentError("bad_request") from e
```

Phir ek separate layer handle karti hai:

```python
async def execute_with_retry(request):
    ...
```

**Provider-specific errors ko retry logic ke saath mix mat kar.**

Ye ek important architectural separation hai — dono ka apna responsibility hai.

## 23. Jo Mujhe Chahiye Tu Yaad Rakhe

```
             LLM REQUEST
                  │
                  ▼
             PROVIDER
                  │
          ┌───────┴────────┐
          ↓                ↓
       Success           Failure
                           │
                 ┌─────────┼─────────┐
                 ↓         ↓         ↓
              4xx       429/5xx    Network
                 │         │         │
                 ↓         ↓         ↓
              Usually    Retry?    Retry?
              no retry   carefully carefully
```

**Key principle:**

> **Don't retry errors blindly. Classify the failure first.**
>
> Errors ko blindly retry mat kar. Pehle failure ko classify kar.