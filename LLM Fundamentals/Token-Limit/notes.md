# Token Usage & Cost Tracking 💰🔴🔴 — LLM Fundamentals

Ye Phase 1 ka **last theory topic** hai.

Tune ab tak seekha:

```
Tokens
Context
Messages
Temperature
Streaming
Structured Outputs
Errors
Retries
Rate Limits
```

Ab hum pehle 9 ko connect karte hain ek aisi cheez mein jo **har production AI backend ko chahiye hoti hai:**

> Is request ne kitna consume kiya, kitna cost hua, aur kitni efficiently ye chala?

## 1. Cost Tracking Kyun Matter Karti Hai

Maan le teri application karti hai:

```
100,000 LLM requests/day
```

Tu bas ye nahi bol sakta:

> "Model ka cost $X per million tokens hai."

Tujhe apna **actual usage** pata hona chahiye.

Har request ke liye, ideally track kar:

```
request_id
user_id
model
provider
input_tokens
output_tokens
total_tokens
latency
status
cost
```

Phir tu ye sawaal answer kar payega:

- Kaunsa model sabse zyada cost kar raha hai?
- Kaunsa user sabse zyada tokens consume kar raha hai?
- Hamara average cost/request kya hai?
- Kal ka bill kyun badha?
- Kaunsa endpoint huge prompts generate kar raha hai?

**Yehi AI observability hai.**

## 2. Input vs Output Pricing

LLM providers often input aur output tokens ko **separately price** karte hain.

Conceptually:

```
Input:
1,000,000 tokens
×
input price

+

Output:
500,000 tokens
×
output price
```

Toh:

```
Total cost
=
Input cost
+
Output cost
```

**Ye mat assume kar ki input aur output ki price same hai.** Often nahi hoti — output usually input se zyada expensive hota hai.

## 3. Example

Maan le, purely illustration ke liye:

```
Input price  = $2 / 1M tokens
Output price = $8 / 1M tokens
```

Teri request:

```
Input  = 10,000 tokens
Output = 2,000 tokens
```

**Input cost:**

```
10,000 / 1,000,000 × $2
= $0.02
```

**Output cost:**

```
2,000 / 1,000,000 × $8
= $0.016
```

**Total:**

```
$0.036
```

**Important:** Ye prices sirf ek example hain. Tere actual Gateway ke liye, pricing provider/model ki current pricing configuration se aani chahiye, kisi tutorial se hardcoded numbers copy karne se nahi.

## 4. Code Mein Cost Calculation

Conceptually:

```python
def calculate_cost(
    input_tokens,
    output_tokens,
    input_price_per_million,
    output_price_per_million
):
    input_cost = (
        input_tokens / 1_000_000
    ) * input_price_per_million

    output_cost = (
        output_tokens / 1_000_000
    ) * output_price_per_million

    return input_cost + output_cost
```

Example:

```python
cost = calculate_cost(
    input_tokens=10_000,
    output_tokens=2_000,
    input_price_per_million=2,
    output_price_per_million=8
)

print(cost)
```

Result:

```
0.036
```

## 5. Hum Simply Characters Kyun Nahi Count Karte?

Kyunki billing provider ke token accounting pe based hoti hai, iss pe nahi:

```
len(text)
```

Aur definitely nahi:

```
len(text) / 4
```

Tere gateway ko provider ka **reported usage** capture karna chahiye jahan available ho.

## 6. API Response Se Token Usage

Conceptually, provider response mein ye ho sakta hai:

```json
{
  "usage": {
    "input_tokens": 1532,
    "output_tokens": 421,
    "total_tokens": 1953
  }
}
```

Tera gateway extract karta hai:

```python
usage = response.usage

input_tokens = usage.input_tokens
output_tokens = usage.output_tokens
total_tokens = usage.total_tokens
```

Phir:

```
Provider
   ↓
Usage
   ↓
Gateway
   ↓
Calculate cost
   ↓
Database
```

Exact response fields provider/API ke hisaab se vary karte hain, isliye jab hum gateway build karenge tab hum inhe apne internal format mein normalize karenge.

## 7. Provider Usage Ko Normalize Kyun Kare?

Tera gateway multiple providers support karta hai:

```
             Gateway
           /    |     \
          ↓     ↓      ↓
       OpenAI Claude Gemini
```

Wo usage information ko differently expose kar sakte hain.

Teri application ko iski fikar nahi karni chahiye.

Ek internal structure bana:

```python
class Usage:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
```

Phir:

```
OpenAI response
      ↓
     normalize
      ↓
Usage object


Anthropic response
      ↓
     normalize
      ↓
Usage object


Gemini response
      ↓
     normalize
      ↓
Usage object
```

**Ye ek abstraction layer rakhne ka major reason hai** — application code ko provider-specific format ki fikar nahi karni padegi.

## 8. Cost Tracking Architecture

Tera Gateway:

```
                       Client
                         │
                         ▼
                  ┌─────────────┐
                  │   Gateway   │
                  └──────┬──────┘
                         │
                         ▼
                     Provider
                         │
                         ▼
                      Response
                         │
                         ▼
                    Usage Data
                         │
                ┌────────┴────────┐
                ▼                 ▼
             Cost Calc         Metrics
                │                 │
                ▼                 ▼
            PostgreSQL       Monitoring
```

## 9. Tujhe Kya Store Karna Chahiye?

Tere Gateway ke liye, main kuch aisa store karunga:

```
requests
──────────────────────────────
id
request_id
user_id
provider
model
input_tokens
output_tokens
total_tokens
cost
latency_ms
ttft_ms
status
error_code
created_at
```

Potentially ye bhi:

```
streaming
retry_count
endpoint
```

depending on tujhe kya chahiye.

## 10. PostgreSQL Kyun?

Kyunki tere Gateway ko already structured, queryable data chahiye.

Example:

```sql
SELECT
    SUM(cost)
FROM requests
WHERE created_at >= CURRENT_DATE;
```

Ab tujhe pata hai aaj ka AI spend kya hai.

Ya:

```sql
SELECT
    model,
    SUM(cost)
FROM requests
GROUP BY model;
```

Ab:

```
Model A → $10
Model B → $42
Model C → $7
```

**Tu actually is data ke basis pe engineering decisions le sakta hai.**

## 11. Per-User Cost

Maan le:

```
User A → 10,000 tokens
User B → 2,000,000 tokens
User C → 50,000 tokens
```

Tu calculate kar sakta hai:

```
cost/user
```

Ye enable karta hai:

- usage limits
- billing
- abuse detection
- analytics
- customer-level quotas

## 12. Cost Tracking vs Token Tracking

Ye related hain lekin identical nahi.

### Token Tracking

Answer karta hai:

> Humne kitne tokens use kiye?

```
input
output
total
```

### Cost Tracking

Answer karta hai:

> Us usage ne kitne paise represent kiye?

```
input tokens
× input price

+

output tokens
× output price
```

**Dono rakh.** Ek doosre ko replace nahi karta.

## 13. Token Usage + Rate Limiting

Ab Topic 9 ko connect karte hain.

Maan le:

```
User quota = 1M tokens/day
```

Tera gateway maintain kar sakta hai:

```
User
 ↓
Token usage
 ↓
Daily quota
 ↓
Allowed?
```

Example:

```
User used:
950,000 tokens

New request:
100,000 tokens

Expected:
1,050,000
```

Tera gateway apni quota policy ke hisaab se us request ko reject ya handle kar sakta hai.

Ye RPM se alag hai:

```
RPM → request frequency
TPM → token throughput
Quota → total allowance
```

## 14. Cost Estimation vs Actual Cost

**Ye distinction important hai.**

### Before Request

Tu estimate kar sakta hai:

```
estimated input tokens
```

Useful for:

- quota checks
- preventing huge requests
- budgeting

### After Request

Tujhe milta hai:

```
actual input tokens
actual output tokens
```

Useful for:

- billing
- analytics
- accurate cost tracking

Toh:

```
Before
 ↓
Estimate
 ↓
Request

After
 ↓
Actual usage
 ↓
Final cost
```

## 15. Streaming Usage Ko Complicate Karti Hai

Yaad hai streaming?

```
Request
 ↓
chunk
 ↓
chunk
 ↓
chunk
 ↓
chunk
 ↓
final usage
```

Tujhe complete output usage tab tak nahi pata hoga jab tak stream finish na ho ya provider usage metadata supply na kare.

Isliye tere gateway ko ye handle karna hoga:

```
stream starts
      ↓
chunks delivered
      ↓
stream finishes
      ↓
usage finalized
      ↓
cost calculated
      ↓
DB record updated
```

Agar stream beech mein fail ho jaaye, tujhe wo case bhi account karna hoga.

## 16. Retries Cost Ko Complicate Karti Hain

Maan le:

```
Attempt 1
 ↓
provider timeout
 ↓
Retry
 ↓
Attempt 2
 ↓
success
```

Kya tune Attempt 1 pe resources consume kiye?

**Potentially yes.**

Isliye tera accounting simply record nahi karna chahiye:

```
successful attempt only
```

Tujhe track karna pad sakta hai:

```
request
 ├── attempt 1
 └── attempt 2
```

Phir usage/cost ko appropriately aggregate kar.

Yehi wajah hai ki hamara Gateway eventually request-level aur attempt-level observability rakhega.

## 17. Example Database Model

Ek clean approach:

```
requests
   │
   ├── request_id
   ├── user_id
   ├── model
   ├── final_status
   ├── total_cost
   └── created_at
          │
          │
          ▼
       attempts
          │
          ├── attempt_number
          ├── provider
          ├── input_tokens
          ├── output_tokens
          ├── cost
          ├── latency_ms
          ├── status
          └── error
```

Ye ek giant table mein sab kuch daalne se zyada useful hai, jab retries/fallbacks involve hone lagte hain.

**Lekin humari first implementation ke liye, schema simple hi rakh.** Isse overengineer mat kar.

## 18. Cost Anomalies

Ab socho tera normal request cost karta hai:

```
$0.003
```

lekin suddenly:

```
$0.50
```

Teri system ye detect kar sakni chahiye:

```
cost spike
   ↓
investigate
```

Potential causes:

- huge prompt
- huge RAG context
- agent loop
- repeated tool calls
- retry storm
- wrong model
- prompt regression

Yahan pe:

```
tokens
+
cost
+
latency
+
logs
```

saath mein extremely powerful ban jaate hain.

## 19. AI Observability

Tere Gateway ke liye, main teen major dimensions ke baare mein sochunga:

**Cost**
```
tokens
$
```

**Performance**
```
TTFT
latency
tokens/sec
```

**Reliability**
```
success rate
429 rate
5xx rate
retry rate
timeout rate
```

Saath mein:

```
             AI OBSERVABILITY
                    │
       ┌────────────┼────────────┐
       ↓            ↓            ↓
     COST       PERFORMANCE   RELIABILITY
       │            │            │
     tokens       TTFT         errors
     dollars      latency      retries
                  throughput    timeouts
```

**Yehi exact cheez hai jo ek AI backend project ko ek basic chatbot se differentiate karti hai.**

## 20. Tera Final Phase 1 Architecture

Ab humne itna seekh liya hai ki pehla version design kar sakein:

```
                         CLIENT
                           │
                           ▼
                    ┌─────────────┐
                    │   FastAPI   │
                    │   Gateway   │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    ↓             ↓
              Authentication   Validation
                    │
                    ▼
               Rate Limiter
                    │
                    ▼
             Concurrency Limit
                    │
                    ▼
              Model Router
                    │
          ┌─────────┼─────────┐
          ↓         ↓         ↓
       Provider  Provider  Provider
          │         │         │
          └─────────┼─────────┘
                    │
              Retry / Backoff
                    │
                    ▼
                 Response
                    │
             ┌──────┴──────┐
             ↓             ↓
         Streaming      Usage
             │             │
             ↓             ↓
           Client       Cost Calc
                           │
                           ▼
                       PostgreSQL
                           │
                           ▼
                    Observability
```

Ye poora Phase 1 ka theory foundation hai, ek architecture ke roop mein jo actually build karne layak hai — cost, performance, aur reliability, teeno as first-class citizens.