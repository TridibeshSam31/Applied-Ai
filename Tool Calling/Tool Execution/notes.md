# Tool Execution Loop ⭐⭐⭐ — Tool Calling

**Ye Phase 2 ka sabse important topic hai.**
Agar ye properly samajh gaya, toh agent frameworks ke andar actually kya ho raha hai wo clear ho jaayega — ye topic halka mat le.

Abhi tak flow tha:

```
User
 ↓
LLM
 ↓
Tool Call
```

Ab hum **complete loop** banayenge:

```
User
 ↓
LLM
 ↓
Tool Call
 ↓
Validate
 ↓
Execute
 ↓
Tool Result
 ↓
LLM
 ↓
Tool Call again?
 ├── YES → execute again
 └── NO  → final answer
```

## 1. Loop Ki Zarurat Kyun Hai?

Maan le user bolta hai:

```
"Find Rahul's overdue invoice."
```

LLM ke paas necessarily ek step mein kaafi information nahi hoti.

Wo ye kar sakta hai:

**Step 1:**

```
search_customer(name="Rahul")
```

Backend return karta hai:

```json
{
  "customer_id": "CUS-123",
  "name": "Rahul"
}
```

Ab LLM result dekhta hai aur sochta hai:

```
I now know the customer ID.
I should get the invoice.
```

Toh wo call karta hai:

```
get_invoice(customer_id="CUS-123")
```

Backend return karta hai:

```json
{
  "invoice_id": "INV-002",
  "status": "overdue",
  "amount": 50000
}
```

Ab LLM ke paas kaafi information hai:

```
"Rahul has an overdue invoice of ₹50,000."
```

**Yehi wajah hai ki humein chahiye:**

```
LLM → Tool → LLM → Tool → LLM
```

## 2. The Core Algorithm

Ye poora concept hai:

```python
while True:

    response = call_llm(messages, tools)

    if no_tool_calls(response):
        return response

    for tool_call in response.tool_calls:

        validate(tool_call)

        result = execute(tool_call)

        add_result_to_messages(result)
```

**Ye foundation hai.**

Is loop ki importance ko underestimate mat kar — poora Phase 2 isi ke around ghumta hai.

## 3. Chal Isse Break Down Karte Hain

### Step 1 — User Request Bhej

```python
messages = [
    {
        "role": "user",
        "content": "What's the status of INV-002?"
    }
]
```

Aur tools provide kar:

```python
tools = [...]
```

Phir:

```python
response = call_llm(messages, tools)
```

## 4. LLM Ek Tool Call Return Karta Hai

Iske bajaye:

```
"INV-002 is overdue."
```

wo shayad conceptually kuch aisa return kare:

```
tool_call:
    name = "get_invoice"

    arguments = {
        "invoice_id": "INV-002"
    }
```

**Important:**

> LLM ne kuch bhi execute nahi kiya hai.

Usne bas request ki hai:

```
"Please execute get_invoice with these arguments."
```

## 5. Tool Dhoond

Hamare paas hamara registry hai:

```python
TOOLS = {
    "get_invoice": {
        "handler": get_invoice,
        "schema": GetInvoiceArgs
    },
    "search_customer": {
        "handler": search_customer,
        "schema": SearchCustomerArgs
    }
}
```

Ab:

```python
tool = TOOLS.get(tool_call.name)
```

Agar:

```
tool_call.name = "get_invoice"
```

hume milta hai:

```
TOOLS["get_invoice"]
```

## 6. Unknown Tool

**Kabhi ye assume mat kar ki model hamesha ek valid tool deta hai.**

Maan le wo return karta hai:

```
delete_database
```

lekin tere paas wo tool nahi hai.

Phir:

```python
if tool is None:
    raise ValueError("Unknown tool")
```

**Kabhi bhi dynamically arbitrary model-generated function names execute mat kar.**

## 7. Arguments Validate Kar

Maan le tool schema hai:

```python
class GetInvoiceArgs(BaseModel):
    invoice_id: str
```

Model deta hai:

```json
{
    "invoice_id": "INV-002"
}
```

Validate kar:

```python
args = GetInvoiceArgs.model_validate(
    tool_call.arguments
)
```

Ab hume pata hai ki arguments hamare schema ko conform karte hain.

## 8. Execute Kar

Ab:

```python
result = tool["handler"](
    **args.model_dump()
)
```

Ye effectively karta hai:

```python
get_invoice(
    invoice_id="INV-002"
)
```

**Backend execution ka owner hai.**

## 9. Result Wapas LLM Ko Bhej

**Ye wo step hai jo beginners often miss karte hain.**

Tu simply ye nahi kar sakta:

```
LLM
 ↓
Tool
 ↓
Result
```

aur ruk jaaye.

**LLM ko result dekhna chahiye.**

Conceptually:

```python
messages.append(
    {
        "role": "tool",
        "content": json.dumps(result)
    }
)
```

Exact message representation depend karta hai us provider API pe jo tu use kar raha hai.

Phir:

```python
response = call_llm(messages, tools)
```

dobara.

## 10. Yehi Loop Hai

Toh:

```
                  ┌─────────────┐
                  │     LLM     │
                  └──────┬──────┘
                         │
                   Tool call?
                    /         \
                  NO           YES
                  │             │
                  ▼             ▼
               Answer      Validate
                                │
                                ▼
                             Execute
                                │
                                ▼
                           Tool Result
                                │
                                ▼
                               LLM
                                │
                                └─────────┐
                                          │
                                          └── repeat
```

**Ye basically agent loop ka primitive hai.**

## 11. Real Code — Simplified Version

Chal khud likhte hain.

```python
import json
from pydantic import BaseModel


class GetInvoiceArgs(BaseModel):
    invoice_id: str


def get_invoice(invoice_id: str):
    invoices = {
        "INV-001": {
            "status": "paid",
            "amount": 10000
        },
        "INV-002": {
            "status": "overdue",
            "amount": 50000
        }
    }

    return invoices.get(invoice_id)


TOOLS = {
    "get_invoice": {
        "handler": get_invoice,
        "schema": GetInvoiceArgs
    }
}
```

Ab execution:

```python
def execute_tool(tool_call):

    tool = TOOLS.get(tool_call["name"])

    if tool is None:
        raise ValueError(
            f"Unknown tool: {tool_call['name']}"
        )

    args = tool["schema"].model_validate(
        tool_call["arguments"]
    )

    result = tool["handler"](
        **args.model_dump()
    )

    return result
```

Phir:

```python
tool_call = {
    "name": "get_invoice",
    "arguments": {
        "invoice_id": "INV-002"
    }
}

result = execute_tool(tool_call)

print(result)
```

Output:

```
{'status': 'overdue', 'amount': 50000}
```

## 12. Ab Actual Loop

Conceptually:

```python
def run_agent(messages):

    while True:

        response = call_llm(
            messages=messages,
            tools=tools
        )

        if not response.tool_calls:
            return response

        for tool_call in response.tool_calls:

            result = execute_tool(tool_call)

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result)
                }
            )
```

Ye wo skeleton hai jise hum eventually ek real implementation mein badlenge.

## 13. Ek Important Correction

Real provider APIs mein, tujhe usually **assistant ka tool-call message/item conversation ka hissa preserve karna padta hai**, uske corresponding tool result ke saath.

Ye simply itna nahi hai:

```python
messages.append(tool_result)
```

Model ko correct sequence dekhni chahiye:

```
User
 ↓
Assistant → tool call
 ↓
Tool → result
 ↓
Assistant → final answer
```

Warna provider request reject kar sakta hai, ya model tool call aur uske result ke beech ka relationship lose kar sakta hai.

Exact representation APIs ke beech different hoti hai.

## 14. Multi-Step Example

Chal isse aur interesting banate hain.

Tools:

```
search_customer()
get_invoice()
```

User:

```
"Find Rahul's invoice."
```

### Iteration 1

LLM:

```
search_customer(name="Rahul")
```

Backend:

```json
{
    "customer_id": "CUS-123",
    "name": "Rahul"
}
```

### Iteration 2

LLM ko wo result milta hai.

LLM:

```
get_invoice(customer_id="CUS-123")
```

Backend:

```json
{
    "invoice_id": "INV-002",
    "status": "overdue",
    "amount": 50000
}
```

### Iteration 3

Ab LLM ke paas kaafi information hai:

**No tool call.**

Return karta hai:

```
Rahul has an overdue invoice of ₹50,000.
```

## 15. Notice Kar Kya Hua

Humne khud nahi likha:

```
search_customer()
get_invoice()
```

**Model ne khud sequence decide kiya, mile hue information ke basis pe.**

**Yehi agentic behavior ki shuruaat hai.**

## 16. Agar Model Ek Aur Tool Call Kare Toh?

Isi wajah se hum use karte hain:

```python
while True:
```

iske bajaye:

```python
response = call_llm()
execute_one_tool()
return
```

Kyunki ho sakta hai:

```
0 tools
1 tool
2 tools
10 tools
...
```

Loop tab tak continue hota hai jab tak:

```
LLM → no more tool calls
```

## 17. Lekin Infinite Loops Possible Hain ⚠️

Socho ek broken model/tool interaction:

```
LLM
 ↓
tool A
 ↓
LLM
 ↓
tool A
 ↓
LLM
 ↓
tool A
 ↓
...
```

Tera:

```python
while True:
```

forever run kar sakta hai.

**Production mein kabhi bhi ek unrestricted agent loop allow mat kar.**

## 18. Ek Maximum Number of Steps Add Kar

Iske bajaye:

```python
MAX_STEPS = 10

for step in range(MAX_STEPS):

    response = call_llm(...)

    if not response.tool_calls:
        return response

    ...
```

Phir:

```
Step 1
Step 2
Step 3
...
Step 10
 ↓
Stop
```

Agar agent ne task complete nahi kiya:

```
Agent stopped:
maximum steps exceeded
```

**Isse stopping condition kehte hain.**

Isme hum bahut zyada deep Phase 6 Agents mein jaayenge.

## 19. Max Steps Kyun Matter Karta Hai

Har tool call consume kar sakta hai:

```
tokens
money
time
database resources
API calls
```

Maan le:

```
10 steps
×
2,000 tokens
```

Ye already potentially significant hai.

Ek accidental loop ye kar sakta hai:

```
$0.01
```

ko badal ke:

```
$10
```

ya worse.

Isliye:

```
max_steps
+
timeouts
+
budgets
```

important hain.

## 20. Tool Execution Isolated Hona Chahiye

Sab kuch ek massive function ke andar mat daal.

Better:

```
Agent Loop
    │
    ├── LLM call
    │
    ├── Tool Router
    │
    ├── Validator
    │
    ├── Authorization
    │
    ├── Executor
    │
    └── State Manager
```

Ye system ko test aur observe karna easier banata hai.

## 21. Tool Result Controlled Hona Chahiye

Maan le:

```
get_invoice()
```

ek huge database object return karta hai:

```
100 fields
```

Blindly sab kuch model ko mat bhej.

Iske bajaye sirf jo chahiye wo return kar:

```json
{
    "invoice_id": "INV-002",
    "status": "overdue",
    "amount": 50000
}
```

Kyun?

```
less context
↓
fewer tokens
↓
lower cost
↓
less noise
↓
better reasoning
```

Ye important hai jab tera agent badhta hai.

## 22. Tool Result Errors

Maan le:

```
get_invoice()
```

fail hota hai:

```
Database timeout
```

Poori process ko blindly crash mat kar.

Tu ek controlled tool result return kar sakta hai:

```json
{
    "success": false,
    "error": "invoice_lookup_failed"
}
```

Phir model decide kar sakta hai kya karna hai.

Shayad:

```
retry
```

ya:

```
tell user it couldn't retrieve the invoice
```

Exact policy tere backend ki hai.

## 23. Errors Ke Saath Tool Loop

Conceptually:

```
LLM
 ↓
Tool Call
 ↓
Validation
 ↓
Authorization
 ↓
Execute
 ↓
 ┌──────────────┐
 │              │
Success       Failure
 │              │
 ↓              ↓
Result      Error Result
 │              │
 └───────┬──────┘
         ↓
        LLM
```

Ye isse kaafi behtar hai:

```
tool failure
 ↓
application crashes
```

## 24. Tool Loop + Authorization

Kabhi ye mat kar:

```python
result = execute_tool(tool_call)
```

permissions consider kiye bina.

Eventually:

```python
validate_arguments()

authorize(
    user=user,
    tool=tool,
    arguments=args
)

execute_tool()
```

Toh:

```
LLM request
     ↓
Schema validation
     ↓
Authorization
     ↓
Business rules
     ↓
Execution
```

Ye Topic 8/9 ban jaayega.

## 25. Tool Loop + Observability

Har iteration mein kuch aisa hona chahiye:

```json
{
    "request_id": "req_123",
    "step": 2,
    "tool": "get_invoice",
    "latency_ms": 142,
    "status": "success"
}
```

Phir tu reconstruct kar sakta hai:

```
Request
 │
 ├── Step 1
 │    └── search_customer
 │
 ├── Step 2
 │    └── get_invoice
 │
 └── Final response
```

**Isse trajectory kehte hain.**

Baad mein, Agent Evals in trajectories ko evaluate karenge.

## 26. Ye Basically Agents Ki Foundation Hai

Yaad hai Phase 6?

```
Agents
```

Core mechanism largely ye hai:

```
Observe
 ↓
Reason/decide
 ↓
Act
 ↓
Observe result
 ↓
Reason/decide
 ↓
Act
 ↓
...
```

Hamara tool loop:

```
LLM
 ↓
Tool
 ↓
Result
 ↓
LLM
```

wo primitive hai jo hum abhi seekh rahe hain.

**Isse abhi ek full production agent mat bol.**

Hum pehle underlying mechanism seekh rahe hain.

## 27. Full Architecture

Is point pe, tera mental model ye hona chahiye:

```
                         USER
                           │
                           ▼
                          LLM
                           │
                           ▼
                     Tool Call
                           │
                           ▼
                  ┌─────────────────┐
                  │   Tool Router   │
                  └────────┬────────┘
                           │
                     Known tool?
                      /          \
                    NO            YES
                    │              │
                  Error        Validate args
                                   │
                                   ▼
                              Authorization
                                   │
                                   ▼
                              Execute tool
                                   │
                           ┌───────┴───────┐
                           ↓               ↓
                        Success         Failure
                           │               │
                           └───────┬───────┘
                                   ↓
                              Tool Result
                                   │
                                   ▼
                                  LLM
                                   │
                         Tool call again?
                           /          \
                         YES           NO
                          │             │
                          └─────┐       ▼
                                │    Final answer
                                │
                                └──→ loop
```

## 28. 5 Cheezein Jo Tujhe Yaad Rakhni Hain

### 1. LLM Tools Execute Nahi Karta

```
LLM → requests
Backend → executes
```

### 2. Tool Result Wapas LLM Ko Jaata Hai

```
Tool → Result → LLM
```

### 3. Loop Final Response Tak Continue Hota Hai

```
LLM → Tool → LLM → Tool → LLM → Answer
```

### 4. Loop Ko Limit Kar

```
max_steps
timeout
budget
```

### 5. Execution Se Pehle Validate + Authorize Kar

```
Tool call
 ↓
Validation
 ↓
Authorization
 ↓
Execution
```