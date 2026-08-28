# Structured Outputs ⭐⭐⭐ — LLM Fundamentals

Ye topic Tool Calling se pehle ka **bridge** hai. Agar ye properly samajh gaya, Phase 2 ka tool-calling loop kaafi easy lagega — isliye is topic ko halke mein mat le.

**Core problem:**

> LLM naturally text generate karta hai, lekin backend ko predictable data chahiye.

## 1. The Problem

Maan le tu LLM se invoice details extract karwa raha hai.

Tu poochta hai:

```
Extract the invoice ID, amount and due date.
Return JSON.
```

Model shayad ye return kare:

```
Sure! Here is the information:

{
  "invoice_id": "INV-123",
  "amount": 50000,
  "due_date": "2026-09-20"
}
```

Human ke liye fine hai.

**Backend ke liye potentially problematic hai.**

Kyunki shayad next time wo return kare:

```json
{
  "invoice": "INV-123",
  "total": "₹50,000",
  "due": "20 September"
}
```

Ya:

```
The invoice number is INV-123 and the amount is ₹50,000...
```

**Tera backend safely ye assume nahi kar sakta ki output exactly wahi shape hoga jo tune request kiya tha.**

## 2. Structured Output Kya Solve Karta Hai?

Isse kehne ke bajaye:

> "Please return JSON."

tu ek **expected schema** define karta hai.

Example:

```
Invoice
├── invoice_id → string
├── amount → number
└── due_date → string
```

Conceptually:

```
LLM
 ↓
Structured output constraint
 ↓
Validated schema
 ↓
Your backend
```

Ab tere backend ke paas ek **predictable contract** hai — koi guesswork nahi.

## 3. JSON ≠ Structured Output

**Ye bahut important distinction hai.**

### Plain JSON Prompting

```
"Return your answer as JSON."
```

Ye sirf ek **instruction** hai.

Model still potentially produce kar sakta hai:

- invalid JSON
- wrong fields
- wrong types
- extra text
- missing fields

### Structured Outputs

Tu ek formal schema provide karta hai aur ek API mechanism use karta hai jo specifically design kiya gaya hai us structure ko enforce/validate karne ke liye.

Conceptually:

```
Schema
  ↓
LLM
  ↓
Output constrained to schema
  ↓
Validated object
```

**Ye kaafi zyada strong hai** — sirf ek polite request nahi, balki ek enforced contract.

## 4. Example Schema

Maan le:

```python
from pydantic import BaseModel


class Invoice(BaseModel):
    invoice_id: str
    amount: float
    due_date: str
```

Ye tere backend ko batata hai:

```
invoice_id → string
amount     → number
due_date   → string
```

Ab model ka output is structure mein map ho sakta hai.

## 5. Pydantic Kyun?

Tu already FastAPI use kar raha hai, isliye ye perfectly fit baithta hai.

Pydantic deta hai:

```
Input
 ↓
Validation
 ↓
Typed Python object
```

Example:

```python
invoice = Invoice(
    invoice_id="INV-123",
    amount=50000,
    due_date="2026-09-20"
)
```

Phir:

```python
invoice.invoice_id
invoice.amount
invoice.due_date
```

Iske bajaye jo manually karna padta:

```python
data["invoice_id"]
data["amount"]
data["due_date"]
```

har jagah. Typed access clean, safe, aur less error-prone hai.

## 6. Real API Example

Current OpenAI Python SDK use karke, tu ek Pydantic model define kar sakta hai aur structured response request kar sakta hai.

Conceptually:

```python
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()


class Invoice(BaseModel):
    invoice_id: str
    amount: float
    due_date: str


response = client.responses.parse(
    model="YOUR_MODEL",
    input="Invoice INV-123 has an amount of 50000 and is due on 2026-09-20.",
    text_format=Invoice,
)

invoice = response.output_parsed

print(invoice.invoice_id)
print(invoice.amount)
print(invoice.due_date)
```

**Important part:**

```python
text_format=Invoice
```

Tu API ko bata raha hai:

> Mujhe expect hai ki model output is structure ko conform kare.

Aur:

```python
response.output_parsed
```

tujhe parsed Pydantic object deta hai.

**Note:** Exact supported models/features change ho sakte hain, isliye final project implement karte waqt current API documentation use kar.

## 7. Ye Tere Backend Ke Liye Extremely Important Kyun Hai

Socho tere backend mein hai:

```
POST /tickets
```

Tere LLM ko ek customer message classify karna hai:

```
"My payment failed twice."
```

Tujhe chahiye:

```json
{
  "category": "billing",
  "priority": "high",
  "requires_human": true
}
```

Phir tera backend kar sakta hai:

```
LLM
 ↓
Structured output
 ↓
Pydantic validation
 ↓
Business logic
```

Example:

```python
if result.requires_human:
    create_human_ticket()
```

**Ye kaafi zyada safe hai** arbitrary natural language ko parse karne ki koshish se.

## 8. Structured Outputs vs Function Calling

**Ye distinction next phase ke liye bahut important hai.**

### Structured Outputs

Model **structured data return** karta hai.

```
LLM
 ↓
JSON/schema
 ↓
Backend
```

Example:

```json
{
  "priority": "high"
}
```

### Function/Tool Calling

Model **request** karta hai ki tera backend ek action perform kare.

```
LLM
 ↓
Tool Call
 ↓
Backend executes function
 ↓
Tool Result
 ↓
LLM
```

Example:

```json
{
  "name": "get_invoice",
  "arguments": {
    "invoice_id": "INV-123"
  }
}
```

Toh:

```
Structured output
→ "Mujhe structured information do"

Tool calling
→ "Meri application se ek action perform karwao"
```

Doosra wala hum Phase 2 mein banayenge.

## 9. Schema Validation

Maan le tu expect karta hai:

```python
class Ticket(BaseModel):
    priority: str
    category: str
```

lekin model deta hai:

```json
{
  "priority": 123
}
```

Tera validation layer detect kar sakta hai ki ye tere intended contract se match nahi karta.

Isliye:

```
LLM output
    ↓
Validation
    ↓
Business logic
```

ye behtar hai isse:

```
LLM output
    ↓
Business logic
```

Validation layer ko skip karna risky hai.

## 10. Model Output Ko Kabhi Blindly Trust Mat Kar

**Structured output ke saath bhi, tere backend ko important business rules validate karne chahiye.**

Maan le schema kehta hai:

```python
amount: float
```

aur model deta hai:

```json
{
  "amount": 999999999
}
```

**Ye structurally valid hai.**

Lekin shayad tera business system kehta hai:

> Ek support agent ₹10,000 se zyada ka refund issue nahi kar sakta.

**Ye ek LLM schema problem nahi hai.**

Tere backend ko enforce karna hi padega:

```
LLM
 ↓
Schema validation
 ↓
Business validation
 ↓
Authorization
 ↓
Action
```

Ye distinction tool calling mein aur bhi critical ban jaati hai.

## 11. Validation Ki Teen Layers

Tere AI backend ke liye, ye soch:

```
                 LLM OUTPUT
                      │
                      ▼
             ┌────────────────┐
             │ Schema         │
             │ Validation     │
             └───────┬────────┘
                     │
                     ▼
             ┌────────────────┐
             │ Business       │
             │ Validation     │
             └───────┬────────┘
                     │
                     ▼
             ┌────────────────┐
             │ Authorization  │
             └───────┬────────┘
                     │
                     ▼
                 ACTION
```

**In teenon ko ek concept mein mat collapse kar** — teeno alag jagah pe alag cheez check karte hain, aur teeno chahiye.

## 12. Tere LLM Gateway Mein Structured Outputs

Tera eventual gateway ye accept kar sakta hai:

```json
{
  "model": "some-model",
  "messages": [
    {
      "role": "user",
      "content": "Extract the invoice details."
    }
  ],
  "response_format": {
    "type": "json_schema"
  }
}
```

Gateway ko ye karna hoga:

```
Request
 ↓
Validate schema
 ↓
Check provider support
 ↓
Send request
 ↓
Receive structured response
 ↓
Validate
 ↓
Return
```

Yehi wajah hai ki tera gateway simply ye nahi ho sakta:

```python
requests.post(provider_url)
```

Isse AI-specific semantics samajhna hi padega.

## 13. Structured Outputs Aur Retries

Kya ho agar structured output fail ho jaaye?

Teri application ko ek strategy chahiye.

Conceptually:

```
LLM
 ↓
Structured output
 ↓
Validation
 ↓
FAILED
 ↓
Retry / fallback
```

Lekin blindly forever retry mat kar.

Use kar:

```
max_retries
+
backoff
+
error classification
```

Ye hum formally Topic 8: Retries mein cover karenge.

## 14. Structured Outputs Aur Streaming

Ek aur nuance hai yahan.

Plain text stream karna straightforward hai:

```
chunk
chunk
chunk
chunk
```

**Structured output zyada complicated ho sakta hai** kyunki final structure sirf tabhi valid banega jab kaafi output aa chuka ho.

Example:

```
{
  "invoice_id": "INV-
```

Ye abhi complete valid JSON object nahi hai.

Isliye ye mat assume kar:

> "Streaming + structured output = bas har chunk print kar de."

Tujhe provider ke structured-output streaming semantics samajhne padenge.

Abhi ke liye, bas ye yaad rakh:

> **Final structured object ko schema satisfy karna chahiye; intermediate stream chunks individually valid JSON nahi bhi ban sakte.**

## 15. Example: Ticket Classification

Chal ek useful schema design karte hain.

```python
from enum import Enum
from pydantic import BaseModel


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Ticket(BaseModel):
    category: str
    priority: Priority
    requires_human: bool
```

Ab:

```
User:
"My payment has failed three times and I need help immediately."
```

Expected structured result:

```json
{
  "category": "billing",
  "priority": "high",
  "requires_human": true
}
```

Teri application safely is result ko consume kar sakti hai.

## 16. Schemas Tool Calling Ke Liye Kyun Matter Karte Hain

**Ye Phase 2 ka bridge hai.**

Maan le tere paas hai:

```python
def get_invoice(invoice_id: str):
    ...
```

Model ko ye generate karna hoga:

```json
{
  "invoice_id": "INV-123"
}
```

Ek tool schema define karta hai:

- tool name
- description
- parameters
- parameter types
- required fields

Toh jald hi tere paas ye hoga:

```
Structured Outputs
       ↓
Understand schemas
       ↓
Tool schemas
       ↓
Function Calling
```

Isi wajah se hum ye topic abhi kar rahe hain — foundation set ho raha hai.

## 17. Common Mistakes

### ❌ "Main bas model ko JSON return karne bolunga."

Production-grade nahi hai.

Jahan support ho wahan schema-based structured output use kar.

### ❌ "Valid JSON matlab valid application data."

**Nahi.**

Ye:

```json
{
  "amount": -500000
}
```

valid JSON ho sakta hai lekin invalid business data.

### ❌ "Schema validation matlab action safe hai."

**Nahi.**

Schema validation structure/type check karta hai.

Authorization permission check karta hai.

Business validation ye check karta hai ki operation allowed hai ya nahi.

### ❌ "Structured output hallucinations eliminate kar deta hai."

**Nahi.**

Ye format reliability improve karta hai.

Model still factually wrong data produce kar sakta hai jo perfectly tere schema se match kare.

Example:

```json
{
  "invoice_id": "INV-999"
}
```

structurally perfect ho sakta hai lekin completely fabricated.

Yehi wajah hai ki humein baad mein grounding + evals chahiye.

## 18. Interview Answer

Agar poocha jaaye:

> **Why use structured outputs instead of asking an LLM to return JSON?**

Bol:

> "Prompting for JSON model ko sirf ek instruction deta hai. Structured outputs ek schema-based contract provide karte hain jo API ko model ke response ko ek expected structure ke against constrain ya validate karne dete hain. Isse downstream parsing zyada reliable ban jaati hai, halaanki business validation aur authorization phir bhi zaroori hain."

Ye wo answer hai jo main ek AI backend engineer se expect karunga.

## 🧠 Final Mental Model

```
                    USER
                      │
                      ▼
                     LLM
                      │
                      ▼
              Structured Output
                      │
                      ▼
                 Schema Check
                      │
              ┌───────┴────────┐
              │                │
           Valid             Invalid
              │                │
              ▼                ▼
      Business Logic       Retry/Fallback
              │
              ▼
        Authorization
              │
              ▼
            Action
```

**Core principle:**

> **LLMs generate; schemas structure; validation verifies; backend logic decides.**