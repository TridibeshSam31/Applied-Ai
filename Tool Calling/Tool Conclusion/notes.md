# Tool Results & Conversation State 🔴🔴 — Tool Calling

Ab hum ek bahut important **missing piece** fix karenge.

Pichhle topic mein flow tha:

```
User
 ↓
LLM
 ↓
Tool Call
 ↓
Execute
 ↓
Tool Result
 ↓
LLM
```

Lekin LLM ko tool result dena **exactly kaise hai?**
Aur previous tool call ko conversation mein preserve **kyun karna hai?**

Yahi aaj ka topic hai.

## 1. Conversation State Kya Hai?

LLM ko har request par generally context dena padta hai.

Example:

```
User:
Find Rahul's invoice.

A:
I need to search for Rahul.

Tool:
CUS-123

A:
Now I'll find the invoice.

Tool:
INV-002, overdue

A:
Rahul has an overdue invoice.
```

Ye poora interaction ek **conversation/state history** ka part hai.

Conceptually:

```python
state = [
    user message,
    assistant tool call,
    tool result,
    assistant tool call,
    tool result,
    assistant final answer
]
```

## 2. Hum Sirf Latest Tool Result Kyun Nahi Bhej Sakte?

Maan le LLM ko sirf ye bhej diya:

```json
{
  "customer_id": "CUS-123"
}
```

Model ko pata hi nahi:

- Ye result kis tool ka hai?
- Kis request ke liye tha?
- Maine tool kyun call kiya tha?
- User ne kya poocha tha?

**Context lost.**

Isliye hum poori interaction preserve karte hain:

```
User request
     ↓
Assistant's tool call
     ↓
Tool result
     ↓
LLM
```

## 3. Tool Call Aur Tool Result Paired Hote Hain

**Ye extremely important hai.**

Socho:

```
A:
call get_invoice(INV-002)
```

Phir:

```
Tool:
status = overdue
```

LLM ko ye samajhna hoga:

> Ye result **isi** tool call ka hai.

Isi wajah se modern tool-calling APIs generally tool calls/results ke liye identifiers provide karti hain.

Conceptually:

```json
{
  "tool_call_id": "call_123",
  "name": "get_invoice",
  "arguments": {
    "invoice_id": "INV-002"
  }
}
```

Tool result:

```json
{
  "tool_call_id": "call_123",
  "result": {
    "status": "overdue"
  }
}
```

ID inhe connect karta hai:

```
call_123
   │
   ├── Tool Call
   │
   └── Tool Result
```

## 4. Conversation State Ka Example

Chal isse conceptually represent karte hain:

```python
messages = [
    {
        "role": "user",
        "content": "What's the status of INV-002?"
    },

    {
        "role": "assistant",
        "tool_call": {
            "id": "call_123",
            "name": "get_invoice",
            "arguments": {
                "invoice_id": "INV-002"
            }
        }
    },

    {
        "role": "tool",
        "tool_call_id": "call_123",
        "content": {
            "status": "overdue",
            "amount": 50000
        }
    }
]
```

Phir ye state wapas LLM ko bhej de.

Model ab dekhta hai:

```
User asked about INV-002
        ↓
I requested get_invoice(INV-002)
        ↓
Tool says overdue, ₹50,000
```

Isliye wo correctly answer kar sakta hai.

## 5. Multi-Step Example

Yahan pe state **really important** ban jaata hai.

User:

```
"Find Rahul's invoice."
```

### Initial State

```
User:
Find Rahul's invoice.
```

LLM:

```
search_customer("Rahul")
```

State ban jaata hai:

```
User
 ↓
Assistant → search_customer("Rahul")
```

Tool return karta hai:

```json
{
  "customer_id": "CUS-123"
}
```

State:

```
User
 ↓
Assistant → search_customer("Rahul")
 ↓
Tool → CUS-123
```

Ab LLM ko complete state milti hai.

Wo decide karta hai:

```
get_invoice("CUS-123")
```

State:

```
User
 ↓
Assistant → search_customer()
 ↓
Tool → CUS-123
 ↓
Assistant → get_invoice()
```

Phir:

```
Tool → INV-002, overdue
```

Finally:

```
Assistant → "Rahul has an overdue invoice."
```

## 6. State Multi-Step Reasoning Enable Karti Hai

**State ke bina:**

```
Tool 1
 ↓
forget
 ↓
Tool 2
```

**State ke saath:**

```
Tool 1
 ↓
result
 ↓
remember
 ↓
LLM
 ↓
Tool 2
```

Toh:

> **Tool calling model ko actions deta hai; conversation state usse un actions ke beech continuity deta hai.**

## 7. State Ko Memory Se Confuse Mat Kar

Ye related hain lekin different hain.

### Conversation State

Usually current execution/conversation ke liye zaruri information matlab hai.

```
User request
+
tool calls
+
tool results
```

### Long-Term Memory

Information jo conversations/tasks ke across retained hoti hai.

Example:

```
User prefers dark mode.
```

Ye months tak persist ho sakta hai.

**Hamare current Phase 2 system ke liye, hum mainly execution state deal kar rahe hain, long-term memory nahi.**

## 8. State Object

Random variables har jagah pass karne ke bajaye, tu ek **execution state** create kar sakta hai:

```python
state = {
    "messages": [],
    "step": 0,
    "tool_calls": [],
    "results": []
}
```

Phir:

```
state
 ├── messages
 ├── step
 ├── tool_calls
 └── results
```

Baad mein, jab hum agents study karenge, ye kaafi zyada sophisticated ban jaata hai.

## 9. Step Kyun Matter Karta Hai

Maan le:

```python
state["step"] = 3
```

Tu track kar sakta hai:

```
Step 1 → search_customer
Step 2 → get_invoice
Step 3 → create_ticket
```

Ye madad karta hai:

- max-step limits
- debugging
- observability
- agent evaluation
- cost tracking

## 10. Tool Result Structured Hona Chahiye

**Bad:**

```python
result = "something went wrong"
```

**Better:**

```json
{
  "success": false,
  "error": {
    "code": "INVOICE_NOT_FOUND",
    "message": "Invoice does not exist."
  }
}
```

**Success:**

```json
{
  "success": true,
  "data": {
    "invoice_id": "INV-002",
    "status": "overdue",
    "amount": 50000
  }
}
```

Ab model result ke baare mein zyada reliably reason kar sakta hai.

## 11. Unnecessary Data Expose Mat Kar

Maan le teri database return karti hai:

```json
{
  "id": "CUS-123",
  "name": "Rahul",
  "email": "...",
  "password_hash": "...",
  "internal_notes": "...",
  "credit_card": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

**Tujhe pura database object LLM mein dump nahi karna chahiye.**

Iske bajaye:

```json
{
  "customer_id": "CUS-123",
  "name": "Rahul"
}
```

**Sirf wo return kar jo model ko chahiye.**

Ye deta hai:

```
less context
↓
fewer tokens
↓
lower cost
↓
less sensitive data exposure
↓
less noise
```

Production systems ke liye ye bahut important hai — sensitive data exposure yahan security concern bhi hai, sirf efficiency nahi.

## 12. Tool Result ≠ Final Answer

Maan le tool return karta hai:

```json
{
  "status": "overdue",
  "amount": 50000
}
```

Tool ko normally ye generate nahi karna chahiye:

```
"Your invoice is overdue and you need to pay ₹50,000 immediately."
```

**Uska kaam data return karna hai.**

LLM us data ko user-facing response mein badalta hai.

```
Tool
 ↓
structured data
 ↓
LLM
 ↓
natural language
```

Ye separation useful hai — responsibility clear rehti hai, tool logic simple rehta hai.

## 13. Tool Result Errors

Maan le:

```
get_invoice()
```

fail hota hai.

Tu ye return kar sakta hai:

```json
{
  "success": false,
  "error": {
    "code": "DATABASE_TIMEOUT"
  }
}
```

Phir LLM decide kar sakta hai:

```
retry?
```

ya:

```
tell user it couldn't retrieve the data
```

**Lekin model ko ye decide mat karne de ki operation indefinitely retry hona chahiye ya nahi.** Retry policy tere backend ki hai — model sirf suggest kar sakta hai, decide nahi.

## 14. State + Retries

Maan le:

```
Step 1
get_invoice()
 ↓
timeout
```

Backend retry karta hai:

```
Attempt 2
get_invoice()
 ↓
success
```

Tu chahega ki state/observability ye preserve kare:

```
Step 1
 ├── Attempt 1 → timeout
 └── Attempt 2 → success
```

Notice kar:

```
step ≠ attempt
```

Ek step logical action hai:

```
get_invoice
```

Ek attempt individual execution hai:

```
attempt 1
attempt 2
```

**Ye distinction jab hum observability build karenge tab useful ban jaayega.**

## 15. Ek Response Mein Multiple Tool Calls

Ek model multiple independent tools request kar sakta hai:

```
get_customer()
get_balance()
get_recent_orders()
```

Tujhe milega:

```
assistant
 ├── call_1 → get_customer
 ├── call_2 → get_balance
 └── call_3 → get_recent_orders
```

Tera backend inhe execute karta hai.

Phir state ko sab corresponding results chahiye:

```
assistant
 ├── call_1
 ├── call_2
 └── call_3

tool
 ├── result_1
 ├── result_2
 └── result_3
```

Phir updated state wapas model ko bhej.

**Parallel execution hum properly Topic 7 mein implement karenge.**

## 16. State Mutation

Socho:

```
User:
Update my address to Kolkata.
```

Tool:

```
update_address(...)
```

return karta hai:

```json
{
  "success": true
}
```

Ab external system mein state change ho chuka hai.

**Ye important hai.**

Teri conversation state shayad kahe:

```
Tool:
address updated
```

Lekin actual source of truth hai:

```
Database
```

Isliye confuse mat kar:

```
LLM context
```

with:

```
application state
```

**Ye alag hain.**

## 17. Teen Prakaar Ki State

Hamari architecture ke liye, in cheezon ke baare mein soch:

### 1. Conversation State

```
messages
tool calls
tool results
```

### 2. Execution State

```
current step
attempts
timeouts
status
```

### 3. Application State

```
PostgreSQL
Redis
external APIs
```

Architecture:

```
                 Agent
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
 Conversation   Execution   Application
   State         State        State
        │          │           │
        ↓          ↓           ↓
     messages     steps      database
     results      retries    Redis
```

**Ye distinction Phase 6 Agents mein bahut important ban jaati hai.**

## 18. State Ka Matlab "Sab Kuch Forever Store Karo" Nahi Hai

Ye mat kar:

```
conversation = 50,000 messages
```

aur har baar poori cheez model ko bhej de.

**Context windows ki limits hoti hain.**

Aur tokens paise cost karte hain.

Eventually tujhe chahiye hoga:

```
old messages
 ↓
summarization
 ↓
relevant state
 ↓
LLM
```

Ye wapas Phase 1 se connect hota hai: **context windows aur tokens.**

## 19. Tool Loop Ab Aisa Dikhta Hai

Hamari improved architecture:

```
                         USER
                           │
                           ▼
                    ┌────────────┐
                    │    State   │
                    └─────┬──────┘
                          │
                          ▼
                         LLM
                          │
                     Tool Call
                          │
                          ▼
                   Validate Args
                          │
                          ▼
                    Authorization
                          │
                          ▼
                    Execute Tool
                          │
                          ▼
                    Tool Result
                          │
                          ▼
                    Update State
                          │
                          ▼
                         LLM
                          │
                   Tool call again?
                    /           \
                  YES            NO
                   │              │
                   └──────┐       ▼
                          │    Final answer
                          │
                          └──→ loop
```

## 20. Actual State Implementation

Hamare learning project ke liye:

```python
state = {
    "messages": [
        {
            "role": "user",
            "content": "Find Rahul's invoice"
        }
    ],
    "step": 0
}
```

Jab LLM ek tool call return karta hai:

```python
state["messages"].append(
    assistant_tool_call
)
```

Execution ke baad:

```python
state["messages"].append(
    tool_result
)
```

Phir:

```python
state["step"] += 1
```

aur LLM ko dobara call kar.

## 21. Important Production Rule

**Kabhi conversation state ko authorization state ki tarah trust mat kar.**

Maan le previous model output kehta hai:

```
"User is an admin."
```

**Iska matlab ye nahi hai ki user actually admin hai.**

Authorization tere trusted backend se aana chahiye:

```
JWT/session
 ↓
User identity
 ↓
Database/permission service
 ↓
Authorization decision
```

ye nahi:

```
LLM says user is admin
```

**Ye bahut zyada matter karega jab hum security tak pahunchenge.**

## 22. Ab Tujhe Ye Samajhna Chahiye

Tujhe ye explain kar paana chahiye:

### Tool Call IDs Kyun?

Associate karne ke liye:

```
tool request ↔ tool result
```

### Assistant Tool Calls Preserve Kyun Kare?

Kyunki LLM ko us history/context ki zarurat hai jo usne request kiya tha.

### Tool Results Preserve Kyun Kare?

Kyunki wo agle model decision ke liye zaruri information provide karte hain.

### Structured Results Kyun?

Kyunki ye application logic aur LLM dono ke liye reason karna easier hai.

### State Ko Database State Se Alag Kyun Rakhe?

Kyunki:

```
LLM context ≠ source of truth
```

## 🧠 Golden Mental Model

Ye yaad rakh:

```
             CONVERSATION STATE

User
 ↓
Assistant → Tool Call #1
 ↓
Tool → Result #1
 ↓
Assistant → Tool Call #2
 ↓
Tool → Result #2
 ↓
Assistant → Final Answer
```

State wo cheez hai jo LLM ko ye samajhne deta hai:

> **"Ab tak kya hua, aur mujhe next kya karna chahiye?"**