# Retries + Exponential Backoff — LLM Fundamentals

Ye previous topic (API Errors & Failure Handling) ka natural continuation hai. Wahan humne establish kiya tha ki kuch failures retryable hote hain, kuch nahi. Ab sawaal ye hai — agar error retryable hai, toh **exactly kaise** retry karein bina situation aur worse kiye?

## Table of Contents

- [The Naive Retry](#the-naive-retry)
- [Basic Retry Strategy](#basic-retry-strategy)
- [Exponential Backoff](#exponential-backoff)
- [Why Exponential](#why-exponential)
- [Synchronized Retries Problem](#synchronized-retries-problem)
- [Jitter](#jitter)
- [Exponential Backoff + Jitter](#exponential-backoff--jitter)
- [Retry Count](#retry-count)
- [What Should Be Retried](#what-should-be-retried)
- [Idempotency](#idempotency)
- [Idempotent Operations](#idempotent-operations)
- [Idempotency Keys](#idempotency-keys)
- [Retry + Timeout Interaction](#retry--timeout-interaction)
- [Retry Budget](#retry-budget)
- [Retry Flow for LLM Gateway](#retry-flow-for-llm-gateway)
- [Implementation](#implementation)
- [Retry-After](#retry-after)
- [Retry vs Fallback](#retry-vs-fallback)
- [Retry + Streaming](#retry--streaming)
- [Complete Production Mental Model](#complete-production-mental-model)
- [Summary](#summary)
- [Interview Answer](#interview-answer)

## The Naive Retry

Suppose provider ne `429 Too Many Requests` return kiya. Bad implementation:

```python
while True:
    try:
        response = call_llm()
        return response
    except RateLimitError:
        continue
```

**Ye disastrous hai.** Socho 1,000 requests sabko 429 mila — sab immediately retry karengi:

```
1000 requests → 429 → 1000 immediate retries → 429 → 1000 immediate retries → 429
```

Tune ek **retry storm** create kar diya. Provider ko recover hone mein help karne ke bajaye, tera system usse aur hammer kar raha hai.

## Basic Retry Strategy

Iske bajaye:

```
Request → Failure → Is retryable?
                          │
                         YES
                          ↓
                        Wait
                          ↓
                        Retry
```

Lekin sawaal ye hai — **kitna wait karein?** Yahin se exponential backoff aata hai.

## Exponential Backoff

Har baar same amount wait karne ke bajaye:

```
1 sec → 1 sec → 1 sec → 1 sec   ❌
```

delay ko badhate jao:

```
1 sec → 2 sec → 4 sec → 8 sec   ✅
```

Conceptually:

```
delay = base × 2^attempt
```

Example (`base = 1 second`):

```
Attempt 1 → 1 sec
Attempt 2 → 2 sec
Attempt 3 → 4 sec
Attempt 4 → 8 sec
```

Usually ek maximum bhi impose karte hain:

```
max_delay = 30 sec
```

taaki delay infinitely na badhe.

## Why Exponential

Agar provider overloaded hai:

```
you → retry immediately → provider still overloaded
```

Tu usse recover hone ka time hi nahi de raha. Exponential backoff progressively request pressure kam karta hai:

```
Failure → wait 1s → Failure → wait 2s → Failure → wait 4s → Failure → wait 8s
```

## Synchronized Retries Problem

Socho 10,000 clients sab same `1s → 2s → 4s → 8s` pattern follow kar rahe hain — sab almost exact same time pe retry karenge:

```
10,000 requests → wait 1 sec → 10,000 requests → wait 2 sec → 10,000 requests
```

**Ye abhi bhi bad hai.** Isliye add karte hain: **Jitter**.

## Jitter

Jitter = retry delay mein randomness add karna.

Exact `4 seconds` ke bajaye, kuch aisa:

```
3.2 sec, 4.7 sec, 3.8 sec, 4.3 sec
```

Ab clients apne retries spread out kar dete hain.

```
Without jitter:
████████████████
same retry time

With jitter:
███   █████   ██   ████
spread out
```

Ye synchronized retry spikes reduce karta hai.

## Exponential Backoff + Jitter

Simple conceptual implementation:

```python
import random

delay = min(
    MAX_DELAY,
    BASE_DELAY * (2 ** attempt)
)

delay += random.uniform(0, 1)
```

Example:

```
Attempt 0: 1 + random(0,1)
Attempt 1: 2 + random(0,1)
Attempt 2: 4 + random(0,1)
Attempt 3: 8 + random(0,1)
```

Several established jitter formulas hain — abhi ek formula pe obsess mat karo. Important concept ye hai:

> Backoff spreads retries over time, jitter prevents clients from synchronizing.

## Retry Count

Kabhi infinite retry mat karo.

**Bad:**
```python
while True:
    retry()
```

**Good:**
```python
MAX_RETRIES = 3
```

```
Attempt 1 → failure → Attempt 2 → failure → Attempt 3 → failure → Give up
```

**Kyun?** Kyunki provider ghanto down reh sakta hai — tu apne gateway ke resources indefinitely block nahi rakhna chahta.

## What Should Be Retried

**Usually NOT retry**: `400`, `401`, `403`, `404` — kyunki request khud ko fix karne ki zaroorat hai.

**Potentially retry**: `429`, `500`, `502`, `503`, `504`, network timeout, temporary connection failure.

Lekin phir bhi:

> "Retryable" is a policy decision, not an absolute property of an HTTP status code.

Example: kisi cheez ko create karne wale operation ko retry karna side effects create kar sakta hai.

## Idempotency ⭐

Ye ek **very important backend concept** hai.

Suppose:

```python
create_payment()
```

Call kiya. Provider ne successfully process kiya. Lekin response aane se pehle network connection mar gaya. Tera client sochega "Request failed" aur retry karega:

```python
create_payment()
```

Ab shayad do payments create ho gaye. **Ye dangerous hai.**

## Idempotent Operations

Ek operation **idempotent** hai agar usse repeat karna same intended effect produce kare jitni baar bhi karo.

```
SET user.status = "active"
```

Isse repeat karne se multiple active statuses nahi banenge. Lekin:

```
CREATE payment
```

har baar naya payment create kar sakta hai. Isliye retries ko side effects consider karna hoga.

## Idempotency Keys

Jo operations support karte hain, unke liye idempotency key help karti hai.

```
request:
    operation = create_payment
    idempotency_key = "req_123"
```

First attempt:
```
req_123 → payment created
```

Retry:
```
req_123 → provider recognizes duplicate → returns original result
```

Ye duplicate operations prevent karta hai. Plain LLM text generation ke liye side effects usually different hote hain, lekin ye concept critical ban jaata hai jab tera agent tools call karna shuru karega. **Phase 2 ke liye yaad rakhna.**

## Retry + Timeout Interaction

Ye ek subtle production issue hai.

```
Request timeout = 30 seconds
Max retries = 3
```

Tu accidentally bana sakta hai:

```
30 sec + 30 sec + 30 sec = 90 sec
```

backoff consider karne se pehle hi. Tera client already give up kar chuka ho sakta hai.

Isliye sochna chahiye:

> **overall request deadline**

har retry ko unlimited fresh request treat karne ke bajaye.

```
Total deadline = 30 sec

Attempt 1 → 10 sec
Backoff   → 1 sec
Attempt 2 → 8 sec
Backoff   → 2 sec
Attempt 3 → remaining time
```

Ye zyada sensible hai.

## Retry Budget

Scale pe, retries ko ek **retry budget** ki tarah socho.

```
100 requests, 80% failing
```

Agar har failure multiple retries trigger kare:

```
100 original + 300 retries = 400 requests
```

Load multiply ho gaya. Isliye production systems retries ko aggressively limit karte hain.

## Retry Flow for LLM Gateway

```
                  Request
                     │
                     ▼
                 Gateway
                     │
                     ▼
                 Provider
                     │
              ┌──────┴──────┐
              ↓             ↓
           Success        Failure
                            │
                            ▼
                     Classify error
                            │
                  ┌─────────┴─────────┐
                  ↓                   ↓
              Retryable           Permanent
                  │                   │
                  ↓                   ↓
             Retry policy          Return
                  │
          ┌───────┴────────┐
          ↓                ↓
       Backoff           Max retries
          │                │
          ↓                ↓
        Retry            Fallback/
                         Failure
```

## Implementation

Ek simple generic retry helper:

```python
import asyncio
import random


MAX_RETRIES = 3
BASE_DELAY = 1
MAX_DELAY = 10


async def retry_with_backoff(operation):

    for attempt in range(MAX_RETRIES + 1):

        try:
            return await operation()

        except Exception as error:

            if attempt == MAX_RETRIES:
                raise

            delay = min(
                MAX_DELAY,
                BASE_DELAY * (2 ** attempt)
            )

            jitter = random.uniform(0, 1)

            total_delay = delay + jitter

            print(
                f"Attempt {attempt + 1} failed. "
                f"Retrying in {total_delay:.2f}s"
            )

            await asyncio.sleep(total_delay)
```

Flow:

```
attempt 0 → failure → 1 + jitter seconds → attempt 1 → failure
→ 2 + jitter seconds → attempt 2 → failure → 4 + jitter seconds
→ attempt 3 → give up
```

### ⚠️ Iss code mein ek deliberate flaw hai

```python
except Exception:
```

Ye sab kuch retry kar raha hai. Humne abhi seekha ki ye kyun galat hai. Chahiye kuch aisa:

```python
except RateLimitError:
    ...
except TimeoutError:
    ...
except BadRequestError:
    raise
```

ya, aur behtar, ek retry policy jo provider error ko classify kare.

### Better Version

```python
async def retry_with_backoff(operation):

    for attempt in range(MAX_RETRIES + 1):

        try:
            return await operation()

        except Exception as error:

            if not is_retryable(error):
                raise

            if attempt == MAX_RETRIES:
                raise

            delay = min(
                MAX_DELAY,
                BASE_DELAY * (2 ** attempt)
            )

            jitter = random.uniform(0, 1)

            await asyncio.sleep(delay + jitter)
```

```python
def is_retryable(error):
    return error.status_code in {
        429,
        500,
        502,
        503,
        504,
    }
```

Ye simplified learning example hai. Production implementation ko provider SDK exceptions, network exceptions, Retry-After, request deadlines, aur operation semantics account karna chahiye.

## Retry-After

Rate limits ke liye, provider bata sakta hai kitna wait karna hai.

```
429 Too Many Requests
Retry-After: 5
```

Toh apna blindly calculate kiya `2 seconds` use karne ke bajaye, uska bataya hua `5 seconds` respect karo.

```
Provider says Retry-After?
        │
       YES
        ↓
       Use it
        │
       NO
        ↓
Exponential backoff + jitter
```

Ye ek important production detail hai.

## Retry vs Fallback

Ye same nahi hain.

**Retry** — same provider/model ko dobara try karna:
```
OpenAI → 429 → wait → OpenAI
```

**Fallback** — doosra provider/model try karna:
```
OpenAI → 503 → Anthropic
```

Eventually dono implement kar sakte ho:

```
Primary → Retry → still failing → Fallback → Retry fallback → fail
```

Lekin jab tak evidence na ho zaroorat ki, architecture ko unnecessarily complicated mat banao.

## Retry + Streaming

Ye wahi jagah hai jahan previous topic connect hota hai.

Non-streaming request ke liye:
```
Request → Provider → failure → Retry
```

Straightforward. Lekin streaming ke liye:

```
Request → Provider → chunk → chunk → chunk → 💥 failure
```

Tu already partial output bhej chuka hai. Tu simply `retry()` karke blindly concatenate nahi kar sakta. Tu produce kar sakta hai:

```
Hello, your order...
Hello, your order...
```

Isliye: **Streaming retry semantics ko special handling chahiye.** (Gateway build karte waqt handle karenge.)

## Complete Production Mental Model

```
                      REQUEST
                         │
                         ▼
                     PROVIDER
                         │
                         ▼
                      ERROR
                         │
                 ┌───────┴────────┐
                 ↓                ↓
            Retryable          Permanent
                 │                │
                 ↓                ↓
         Check Retry-After       Return
                 │
                 ↓
       Exponential Backoff
                 │
                 ↓
               Jitter
                 │
                 ↓
            Retry Budget
                 │
                 ↓
            Retry Attempt
                 │
                 ↓
             Max Retries?
              /       \
            NO         YES
            ↓           ↓
          Retry       Fallback/
                       Failure
```

## Summary

- **Exponential Backoff**: `1s → 2s → 4s → 8s`
- **Jitter**: randomness taaki clients simultaneously retry na karein
- **Max retries**: infinite retry loops prevent karta hai
- **Retry classification**: har error retry nahi hoti
- **Retry-After**: provider-supplied timing available ho toh respect karo
- **Idempotency**: critical hai jab retries side effects cause kar sakte hain
- **Deadline**: retries ko request ko forever live mat rakhne do

## Interview Answer

Agar poocha jaaye:

> How would you implement retries for an LLM API?

Strong answer:

> "I'd first classify errors into retryable and non-retryable categories. For transient errors such as rate limits or temporary upstream failures, I'd use bounded retries with exponential backoff and jitter, respect Retry-After when provided, and enforce an overall deadline. I'd also consider idempotency for operations with side effects and avoid blindly retrying streaming requests after partial output has already been delivered."

Yehi level hai jo aim karna hai.