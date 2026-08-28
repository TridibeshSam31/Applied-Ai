# Rate Limits & Concurrency — LLM Fundamentals

Ab hum LLM Gateway ke **most important backend problems** mein se ek pe hain.

Pehle ek distinction samajh lo:

> **Rate limiting** controls how much traffic you allow.
> **Concurrency** controls how many operations are happening at the same time.

Dono related hain, lekin same nahi hain.

## Table of Contents

- [Why Do We Need Rate Limiting](#why-do-we-need-rate-limiting)
- [Rate Limit vs Quota](#rate-limit-vs-quota)
- [RPM and TPM](#rpm-and-tpm)
- [Why Token-Based Limiting Matters](#why-token-based-limiting-matters)
- [Basic Rate Limiter](#basic-rate-limiter)
- [Token Bucket](#token-bucket)
- [Why Token Bucket Is Useful](#why-token-bucket-is-useful)
- [Sliding Window](#sliding-window)
- [Fixed Window](#fixed-window)
- [Distributed Rate Limiting](#distributed-rate-limiting)
- [Redis Solves This Problem](#redis-solves-this-problem)
- [Concurrency](#concurrency)
- [Rate Limit ≠ Concurrency Limit](#rate-limit--concurrency-limit)
- [Why Concurrency Matters for LLMs](#why-concurrency-matters-for-llms)
- [Semaphore](#semaphore)
- [Concurrency + Streaming](#concurrency--streaming)
- [Backpressure](#backpressure)
- [Queue vs Reject](#queue-vs-reject)
- [Rate Limiting Per User](#rate-limiting-per-user)
- [Rate Limiting + Provider Limits](#rate-limiting--provider-limits)
- [Token-Based Rate Limiting](#token-based-rate-limiting)
- [A Realistic Gateway Flow](#a-realistic-gateway-flow)
- [Code: Simple Token Bucket](#code-simple-token-bucket)
- [Code: Concurrency](#code-concurrency)
- [The Interview Distinction](#the-interview-distinction)
- [The Biggest Mistakes](#the-biggest-mistakes)
- [Final Mental Model](#final-mental-model)

## Why Do We Need Rate Limiting

Suppose tera API `POST /v1/chat` public hai. Ek user script chala deta hai:

```
request → request → request → ... → 100,000 requests
```

Bina protection ke:

```
                    Gateway
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
      LLM             LLM             LLM
        ↓              ↓              ↓
      $$$             $$$             $$$
```

**Problems:**
- provider rate limit hit
- huge bill
- server overload
- legitimate users affected
- provider account potentially throttled

Isliye gateway ko ek policy chahiye:

```
User → Rate Limiter → Allowed?
                        ├── YES → LLM
                        └── NO  → 429
```

## Rate Limit vs Quota

Ye thode different hain.

**Rate limit** — controls karta hai requests/tokens kitni jaldi consume ho sakte hain.
```
100 requests / minute
```

**Quota** — controls karta hai total kitna usage allowed hai bade time period mein.
```
1 million tokens / day
```

```
Rate limit → speed
Quota      → total allowance
```

## RPM and TPM

LLM APIs sirf requests nahi, aur bhi kuch care karti hain.

**RPM** — Requests Per Minute. `100 RPM` matlab roughly `100 requests/minute`.

**TPM** — Tokens Per Minute. `100,000 TPM` matlab allowed token throughput bhi constrained hai.

Ye isliye important hai:

```
Request A → 100 tokens
Request B → 50,000 tokens
```

Provider ke perspective se ye equivalent nahi hain. Isliye AI gateway ko dono control karne pad sakte hain: **requests + tokens**.

## Why Token-Based Limiting Matters

Suppose limit hai `100 requests/minute`.

**User A**: `100 requests × 100 tokens = 10,000 tokens`

**User B**: `100 requests × 20,000 tokens = 2,000,000 tokens`

Same number of requests. **Completely different resource consumption.** Isliye AI systems ke liye sirf request-based rate limiting kaafi nahi hoti.

## Basic Rate Limiter

Suppose chahiye: `10 requests / minute / user`

```
User 123 → 10 requests → allowed
11th request → 429
```

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests"
  }
}
```

## Token Bucket ⭐

Sabse useful rate-limiting algorithms mein se ek.

Socho har user ka ek bucket hai:

```
        ┌───────────────┐
        │ ● ● ● ● ● ● ● │
        │   TOKENS       │
        └───────────────┘
```

Bucket capacity: `10 tokens`. Refill rate: `2 tokens/sec`. Har request ek ya zyada tokens consume karti hai.

```
Request → Take token from bucket → Available?
                                     ┌──────┴──────┐
                                     YES           NO
                                     ↓              ↓
                                    Allow          429
```

## Why Token Bucket Is Useful

Ye controlled bursts allow karta hai.

Suppose `capacity = 10`, `refill = 2/sec`. User immediately `10 requests` kar sakta hai kyunki bucket mein already 10 tokens hain.

```
11th request → rejected
```

2 seconds wait karne ke baad, approximately `4 new tokens` available ho jaate hain (exact implementation pe depend karta hai). Toh milta hai:

```
burst capacity + sustained rate
```

Ye simplistic approach se zyada useful hai:
```python
if requests_this_minute > 10:
    reject
```

## Sliding Window

Ek aur approach:

```
Current time
      │
      ▼
┌─────────────────────────┐
│ last 60 seconds         │
│                         │
│ req req req req req     │
└─────────────────────────┘
```

Current time window ke andar requests count karo. Agar `count >= limit` toh `429` return karo. Samajhna easy hai, lekin boundary behavior aur storage ke around different variants aur tradeoffs hain.

## Fixed Window

Simplest approach:

```
12:00 → 12:01
Allow: 100 requests
At 12:01: counter resets
```

**Problem:** User boundary exploit kar sakta hai:

```
12:00:59 → 100 requests
12:01:00 → 100 requests
```

Potentially `200 requests` bahut kam time mein. Isliye token bucket/sliding-window approaches requirements ke hisaab se preferable ho sakte hain.

## Distributed Rate Limiting ⭐

Ab system-design preparation ke liye important part.

Suppose gateway ke paas:

```
              Load Balancer
                    │
          ┌─────────┼─────────┐
          ↓         ↓         ↓
       Server 1  Server 2  Server 3
```

Agar Server 1 apna khud ka counter rakhta hai:

```
Server 1 → 10 requests
Server 2 → 10 requests
Server 3 → 10 requests
```

User effectively `30 requests` pa sakta hai `10 requests` ki jagah. **Tera rate limiter globally consistent nahi hai.**

## Redis Solves This Problem

Rate-limit state centralize kar sakte ho:

```
             Gateway
          /     |      \
         ↓      ↓       ↓
      Server1 Server2 Server3
         \      |       /
          \     |      /
              Redis
```

Sab servers same state check karte hain: `user:123:rate_limit`. Redis counters/bucket state store karta hai. Ab sab servers same rate-limit state share karte hain. **Isliye Redis tere eventual LLM Gateway mein perfectly fit hota hai.**

## Concurrency

Ab doosra concept.

Suppose gateway ke paas `100 requests/sec` hai, lekin har LLM request `5 seconds` leti hai. Toh multiple requests simultaneously "in flight" ho sakti hain.

**Concurrency** = kitne operations currently active hain same time pe.

```
Request 1 ──────────────────
Request 2 ─────────────
Request 3 ───────────────────
Request 4 ───────
```

Ek point pe `4 requests` simultaneously active hain. **Yehi concurrency hai.**

## Rate Limit ≠ Concurrency Limit

Suppose:
```
Rate limit = 100 requests/sec
Concurrency limit = 10
```

Tu `100 requests` receive kar sakta hai, lekin sirf `10 active LLM requests` ek time pe allow kar sakta hai. Baaki wait karengi ya reject ho jaayengi.

```
Rate limit       → How frequently requests can enter
Concurrency limit → How many requests can be active
```

## Why Concurrency Matters for LLMs

LLM calls expensive aur long-lived ho sakti hain, especially streaming:

```
Request → connection stays open → tokens → tokens → tokens → done
```

Socho `5,000 simultaneous streams` — bahut sara connections, memory, provider concurrency, sockets, CPU/event-loop activity, downstream capacity. Isliye gateway ko concurrency limit chahiye ho sakti hai.

## Semaphore

Python mein simple concurrency control mechanism: `asyncio.Semaphore`.

```python
import asyncio

semaphore = asyncio.Semaphore(10)
```

```python
async def call_llm():
    async with semaphore:
        return await provider_call()
```

Matlab: maximum `10 calls` ek saath. Agar 11th aata hai, design ke hisaab se wait karega.

## Concurrency + Streaming

Streaming ke liye careful raho. Agar tu:

```python
async with semaphore:
    async for chunk in stream:
        yield chunk
```

karta hai, semaphore poori stream ke liye occupied rehta hai. Ye usually theek hai agar limit active provider streams represent karti hai. Lekin socho `10 concurrent streams` jo har ek `2 minutes` chalti hain — un slots ko 2 minutes ke liye occupy kar diya. Isliye **concurrency limits ko apne actual workload ke around design karna hoga.**

## Backpressure ⭐

Ek useful system-design concept.

Suppose gateway `100 concurrent requests` process kar sakta hai lekin achanak `10,000` aa jaayein. Overload ko downstream propagate hone se rokna hoga — **yehi backpressure hai.**

```
10,000 requests
       ↓
   Gateway
       ↓
   Queue/limit
       ↓
100 active
       ↓
Provider
```

Iske bajaye:
```
10,000 → Provider → 💥
```

Backpressure system ke through flow ko control karta hai.

## Queue vs Reject

Jab concurrency full ho jaaye:

```
Request 101 → limit reached
```

Do options hain:

**Option A — Queue**
```
Request → Queue → wait → LLM
```
Useful jab waiting acceptable ho.

**Option B — Reject**
```
Request → 429 / 503
```
Useful jab low latency matter karti ho aur waiting pointless ho.

Interactive AI API ke liye, blindly unlimited queue banana dangerous hai — `10,000 waiting requests` bana sakte ho, aur ab memory/latency problem ban jaata hai.

## Rate Limiting Per User

Zaroori nahi sirf ek global limit ho. Multiple levels ho sakte hain:

```
Global:     10,000 RPM
Per user:      100 RPM
Per API key:   500 RPM
Per model:   1,000 RPM
```

Potentially:
```
free user    → 20 RPM
premium user → 200 RPM
```

Ye tere API product design ka hissa ban jaata hai.

## Rate Limiting + Provider Limits

Gateway ke do layers of limits hote hain:

```
             Your Gateway
                  │
            Your rate limit
                  │
                  ▼
             LLM Provider
                  │
            Provider limit
                  │
                  ▼
                 LLM
```

Suppose provider `1,000 RPM` support karta hai, lekin tera gateway `10,000 RPM` allow karta hai — **bad design.** Tu constantly provider limits hit karega. Gateway ko provider capacity samajhni chahiye aur usi ke hisaab se apni policies rakhni chahiye.

## Token-Based Rate Limiting

AI systems ke liye, advanced gateway token consumption estimate/track kar sakta hai:

```
Request → Estimate input tokens → Check token budget → Allow/reject → LLM
```

Response ke baad:

```
Actual usage → Update accounting
```

Ye directly first topic se connect hota hai:

```
Tokens → Rate limiting → Cost tracking
```

## A Realistic Gateway Flow

Ab jo humne seekha hai combine karte hain:

```
                    Client
                      │
                      ▼
                ┌───────────┐
                │  FastAPI  │
                └─────┬─────┘
                      │
                      ▼
                 Authentication
                      │
                      ▼
                  Rate Limit
                      │
                      ▼
               Concurrency Limit
                      │
                      ▼
                 Model Router
                      │
                      ▼
                  LLM Provider
                      │
                ┌─────┴─────┐
                ↓           ↓
             Success      Failure
                │           │
                │        Retry policy
                │           │
                └─────┬─────┘
                      ↓
                   Stream
                      ↓
                    Client
```

Iske saath saath:

```
Redis      → Rate-limit state
PostgreSQL → Request/token/cost logs
```

Ab tu actually ek AI infrastructure service design kar raha hai.

## Code: Simple Token Bucket

Ek learning implementation:

```python
import time


class TokenBucket:

    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.monotonic()

    def allow(self):

        now = time.monotonic()
        elapsed = now - self.last_refill

        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )

        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True

        return False
```

Usage:

```python
bucket = TokenBucket(
    capacity=5,
    refill_rate=1
)

if bucket.allow():
    print("Request allowed")
else:
    print("Rate limit exceeded")
```

Matlab: `Bucket capacity = 5 requests`, `Refill rate = 1 request/sec`.

⚠️ Ye multiple processes/servers ke liye production-safe nahi hai. Actual Gateway ke liye Redis/shared state use karenge.

## Code: Concurrency

Simple example:

```python
import asyncio

semaphore = asyncio.Semaphore(3)


async def call_llm(request_id):

    async with semaphore:

        print(f"{request_id} started")

        await asyncio.sleep(3)

        print(f"{request_id} finished")


async def main():

    tasks = [
        call_llm(i)
        for i in range(10)
    ]

    await asyncio.gather(*tasks)


asyncio.run(main())
```

10 tasks create karne ke bawajood:

```
10 requests → Semaphore = 3 → Only 3 active at once
```

## The Interview Distinction

Agar interviewer poochhe:

> What's the difference between rate limiting and concurrency limiting?

Answer:

> "Rate limiting controls how frequently requests are admitted over time, while concurrency limiting controls how many operations can be in flight simultaneously. For LLM systems I'd often use both because requests can be long-lived and expensive, especially when streaming."

Strong answer.

## The Biggest Mistakes

- ❌ **Only rate-limit requests** — AI requests different amounts of tokens consume karte hain.
- ❌ **Store counters in local memory** — jab horizontally scale karo toh break ho jaata hai.
- ❌ **Unlimited queue** — overload ko memory/latency problem mein badal sakta hai.
- ❌ **Ignore streaming** — long-lived streams concurrency slots ko lambe time ke liye occupy kar sakti hain.
- ❌ **Let your gateway hit provider limits constantly** — gateway ko upstream provider protect karna chahiye, sirf problem forward nahi karni chahiye.

## Final Mental Model

```
              INCOMING TRAFFIC
                     │
                     ▼
              ┌─────────────┐
              │ Rate Limit  │
              └──────┬──────┘
                     │
                  allowed
                     │
                     ▼
              ┌─────────────┐
              │ Concurrency │
              │   Limit     │
              └──────┬──────┘
                     │
                 capacity
                     │
                     ▼
                LLM Provider
                     │
                     ▼
                   Result
```

Aur yaad rakho:

> **Rate limiting controls traffic over time. Concurrency limiting controls work happening right now.**
