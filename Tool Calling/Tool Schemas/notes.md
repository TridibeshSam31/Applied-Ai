# Tool Schemas & JSON Arguments 🔴🔴 — Tool Calling

Previous topic mein humne manually ye banaya tha:

```python
tool_call = {
    "name": "get_invoice",
    "arguments": {
        "invoice_id": "INV-002"
    }
}
```

Ab question hai:

> LLM ko kaise pata chalega ki `get_invoice` exist karta hai aur usko `invoice_id` chahiye?

**Answer: Tool schema.**

## 1. Tool Schema Kya Hota Hai?

Tool schema basically LLM ko tool ka **contract** batata hai.

Example:

```json
{
  "name": "get_invoice",
  "description": "Retrieve an invoice using its ID.",
  "parameters": {
    "type": "object",
    "properties": {
      "invoice_id": {
        "type": "string",
        "description": "The invoice ID"
      }
    },
    "required": ["invoice_id"]
  }
}
```

LLM ko ab pata hai:

```
Tool:
    get_invoice

Input:
    invoice_id

Type:
    string

Required:
    yes
```

## 2. Schema Kyun Matter Karta Hai?

Maan le tu model ko sirf itna bolta hai:

```
There is a function called get_invoice.
```

Model reliably ye nahi jaanta:

- What arguments?
- What types?
- Which arguments required?
- What does it return?

**Schema isse explicit banata hai.**

```
                Tool
                 │
       ┌─────────┼─────────┐
       ↓         ↓         ↓
     Name    Description  Parameters
                           │
                    ┌──────┴──────┐
                    ↓             ↓
                  Type         Required
```

## 3. JSON Arguments

Model ka tool call generally **structured arguments** contain karega.

Example:

```json
{
  "name": "get_invoice",
  "arguments": {
    "invoice_id": "INV-002"
  }
}
```

Tera backend extract karta hai:

```python
name = tool_call["name"]

arguments = tool_call["arguments"]
```

Phir:

```python
tool = TOOLS[name]

result = tool(**arguments)
```

Jo ban jaata hai:

```python
get_invoice(invoice_id="INV-002")
```

## 4. Multiple Arguments

Maan le:

```python
def search_customer(name: str, email: str | None = None):
    ...
```

Schema:

```json
{
  "name": "search_customer",
  "description": "Search for a customer.",
  "parameters": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string"
      },
      "email": {
        "type": "string"
      }
    },
    "required": ["name"]
  }
}
```

Model ye generate kar sakta hai:

```json
{
  "name": "search_customer",
  "arguments": {
    "name": "Rahul",
    "email": "rahul@example.com"
  }
}
```

Tera backend:

```python
result = search_customer(
    name="Rahul",
    email="rahul@example.com"
)
```

## 5. Types Matter Karte Hain

Maan le:

```python
def get_invoice(invoice_id: str):
    ...
```

Tujhe chahiye:

```json
{
  "invoice_id": "INV-123"
}
```

ye nahi:

```json
{
  "invoice_id": 123
}
```

Schema:

```json
"invoice_id": {
    "type": "string"
}
```

ye expectation communicate karta hai.

**Lekin ye mat assume kar ki akela schema hi kaafi security hai.** Tere backend ko execution se pehle bhi arguments validate karne chahiye.

## 6. Enum Values

Maan le tere paas hai:

```python
def create_ticket(priority: str):
    ...
```

Valid priorities:

```
low
medium
high
```

Sirf model ko ye mat bata:

```
priority is a string
```

Allowed values **define** kar:

```json
{
  "priority": {
    "type": "string",
    "enum": ["low", "medium", "high"]
  }
}
```

Ab intended contract ye hai:

```
priority
    ↓
low
medium
high
```

iske bajaye:

```
priority
    ↓
literally any string
```

## 7. Required vs Optional

Maan le:

```python
def search_customer(
    name: str,
    email: str | None = None
):
    ...
```

Toh:

```
name  → required
email → optional
```

Schema:

```json
"required": ["name"]
```

**Important:**

> Har property ko automatically `required` mein mat daal de.

Tera schema actual function contract represent karna chahiye — jo function mein optional hai, schema mein bhi optional hi rehna chahiye.

## 8. Nested Arguments

Real tools mein zyada complex inputs ho sakte hain.

Example:

```python
def create_ticket(customer_id, issue, metadata):
    ...
```

Schema kuch aisa dikh sakta hai:

```json
{
  "name": "create_ticket",
  "parameters": {
    "type": "object",
    "properties": {
      "customer_id": {
        "type": "string"
      },
      "issue": {
        "type": "string"
      },
      "metadata": {
        "type": "object",
        "properties": {
          "source": {
            "type": "string"
          },
          "priority": {
            "type": "string"
          }
        }
      }
    },
    "required": [
      "customer_id",
      "issue"
    ]
  }
}
```

Ab tera schema nested structure bhi represent karta hai.

## 9. Pydantic Isse Easier Banata Hai

Since hum Python + FastAPI use kar rahe hain, Pydantic extremely useful hai.

```python
from pydantic import BaseModel


class GetInvoiceArgs(BaseModel):
    invoice_id: str
```

Phir:

```python
args = GetInvoiceArgs(
    invoice_id="INV-002"
)
```

Ab Pydantic structure validate karta hai.

Example:

```python
args = GetInvoiceArgs(
    invoice_id=123
)
```

Teri Pydantic configuration/version pe depend karte hue, coercion ya validation behavior matter kar sakta hai, isliye strict tool contracts ke liye tujhe explicitly appropriate validation types/configuration choose karni chahiye, ye assume karne ke bajaye ki har type mismatch hamesha reject ho jaayega.

## 10. Better Tool Architecture

Iske bajaye ki hamare paas ho:

```python
TOOLS = {
    "get_invoice": get_invoice
}
```

Hum metadata bhi store karna start kar sakte hain.

Example:

```python
TOOLS = {
    "get_invoice": {
        "handler": get_invoice,
        "description": "Retrieve an invoice using its ID.",
        "schema": GetInvoiceArgs
    }
}
```

Ab ek registry entry mein ye sab hota hai:

```
get_invoice
 ├── handler
 ├── description
 └── schema
```

Ye baad mein extremely useful ban jaata hai.

## 11. Actual OpenAI Tool Definition

Ab isse API se connect karte hain.

Conceptually:

```python
tools = [
    {
        "type": "function",
        "name": "get_invoice",
        "description": "Retrieve an invoice using its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": "The invoice ID"
                }
            },
            "required": ["invoice_id"],
            "additionalProperties": False
        },
        "strict": True
    }
]
```

Phir:

```python
response = client.responses.create(
    model="YOUR_MODEL",
    input="What is the status of invoice INV-002?",
    tools=tools
)
```

Model decide kar sakta hai ki usse chahiye:

```
get_invoice
```

with:

```json
{
  "invoice_id": "INV-002"
}
```

Exact API fields API families/providers ke across vary kar sakte hain, isliye jab tu actual project implement kare, current provider SDK schema follow kar.

## 12. `strict` Kya Kar Raha Hai

Jab support ho, strict structured tool schemas expected argument shape ko kaafi zyada constrained bana dete hain.

Soch:

**Strong schema enforcement ke bina:**

```
LLM
 ↓
"hopefully correct JSON"
 ↓
Backend
```

**Ek strict schema ke saath:**

```
LLM
 ↓
schema-constrained arguments
 ↓
Backend validation
 ↓
execution
```

Lekin yaad rakh:

> **Schema correctness ≠ authorization.**

Ek perfectly valid:

```json
{
  "invoice_id": "INV-999"
}
```

phir bhi ek unauthorized request ho sakti hai.

## 13. Raw Model Arguments Ko Kabhi Directly Execute Mat Kar

**Bad:**

```python
tool(**tool_call["arguments"])
```

bina validation ke.

**Better:**

```
Tool Call
    ↓
Parse JSON
    ↓
Validate schema
    ↓
Authorization
    ↓
Business validation
    ↓
Execute
```

Toh eventually:

```python
args = GetInvoiceArgs.model_validate(
    tool_call["arguments"]
)

check_authorization(user, args)

result = get_invoice(
    invoice_id=args.invoice_id
)
```

**Ye kaafi zyada safe hai.**

## 14. Unknown Arguments

Maan le model generate karta hai:

```json
{
  "invoice_id": "INV-002",
  "delete_database": true
}
```

Tera schema ko unexpected fields ko reject karna chahiye jahan appropriate ho.

Isi wajah se tu often ye dekhega:

```
"additionalProperties": false
```

strict JSON schemas mein.

Conceptually:

```
Expected:
invoice_id

Received:
invoice_id
delete_database
      ↓
REJECT
```

**Ye ek useful defensive layer hai** — LLM output se accidental ya malicious extra fields backend tak nahi pahunchte.

## 15. Schema Descriptions Matter Karte Hain

Descriptions ko underestimate mat kar.

**Bad:**

```json
{
  "name": "search",
  "description": "Search"
}
```

**Better:**

```json
{
  "name": "search_customer",
  "description": "Search customers by exact email or customer name."
}
```

Kyun?

Model tool ki **semantic description** use karta hai ye decide karte waqt ki kaunsa tool call kare.

Poor descriptions → ambiguous tool selection.

Ye hum Topic 3 mein cover karenge.

## 16. Tool Schema Ek API Contract Hai

Isse aise soch:

**Normal API**

```
Client
 ↓
POST /invoice
 ↓
OpenAPI/schema
 ↓
Backend
```

**Tool calling:**

```
LLM
 ↓
Tool schema
 ↓
Tool call
 ↓
Backend
```

Toh tool schemas effectively ek **LLM-facing API contract** hain.

Backend engineer ke naate, inke baare mein sochne ka ye ek bahut useful tarika hai.

## 17. Schema vs Implementation

Model ko ye jaanne ki zarurat nahi:

```python
def get_invoice():
    query PostgreSQL
    ...
```

Usse sirf ye chahiye:

```
get_invoice
 ↓
what it does
 ↓
what arguments it accepts
```

Isliye:

```
          LLM
           │
     Tool Interface
           │
           ▼
      get_invoice()
           │
           ▼
       PostgreSQL
```

Tu completely database implementation change kar sakta hai without tool contract change kiye.

**Yehi abstraction hai.**

## 18. Hamare Project Ke Saath Example

Hum eventually ye expose karne wale hain:

```
search_customer
get_invoice
create_ticket
update_ticket
search_documents
send_notification
```

Har ek ko schema chahiye.

Example:

```python
class GetInvoiceArgs(BaseModel):
    invoice_id: str


class SearchCustomerArgs(BaseModel):
    name: str


class CreateTicketArgs(BaseModel):
    customer_id: str
    issue: str
    priority: str
```

Phir:

```
Tool Registry
│
├── search_customer
│   └── SearchCustomerArgs
│
├── get_invoice
│   └── GetInvoiceArgs
│
└── create_ticket
    └── CreateTicketArgs
```

## 19. Full Flow

Ab Topic 1 + Topic 2 ko combine karte hain:

```
                         User
                           │
                           ▼
                          LLM
                           │
                 Tool definitions
                           │
                           ▼
                    Tool selection
                           │
                           ▼
                   Tool + Arguments
                           │
                           ▼
                    Parse arguments
                           │
                           ▼
                   Schema validation
                           │
                           ▼
                     Authorization
                           │
                           ▼
                    Execute function
```

**Yehi wo foundation hai jispe hum build karne wale hain.**

## 20. Critical Distinction

Tujhe ab in teeno cheezon ko alag-alag samajhna chahiye:

### Tool Schema

> Ye tool kaunse arguments accept karta hai?

### Validation

> Supplied arguments structurally valid hain kya?

### Authorization

> Kya is user ko ye operation perform karne ki permission hai?

**Inhe merge mat kar.**

```
Schema
  ↓
Structure

Validation
  ↓
Correct input

Authorization
  ↓
Permission
```

Teeno alag jagah pe alag cheez check karte hain — ek dusre ka substitute nahi hain.