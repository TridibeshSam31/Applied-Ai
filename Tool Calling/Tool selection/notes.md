# Tool Selection & Routing 🔴🔴 — Tool Calling

Ab tak:

```
Topic 1 → Tool kya hai
Topic 2 → Tool ka schema kya hai
```

Ab actual **intelligence part:**

> LLM ko kaise decide karna hai ki available tools mein se kaunsa use kare?

## 1. Simple Example

Humare paas 3 tools hain:

```
search_customer()
get_invoice()
create_ticket()
```

User bolta hai:

```
"Rahul ka invoice dhundho."
```

LLM ko decide karna hai:

```
search_customer()
```

User:

```
"INV-002 ka status kya hai?"
```

LLM:

```
get_invoice()
```

User:

```
"Rahul ke liye payment issue ka ticket bana do."
```

LLM:

```
create_ticket()
```

Toh:

```
User request
     ↓
     LLM
     ↓
Which tool?
     ↓
Tool selection
```

## 2. Model Ko Tools Kaise Pata Chalte Hain?

Hum API request mein tools provide karte hain:

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
                    "type": "string"
                }
            },
            "required": ["invoice_id"]
        }
    }
]
```

Model ko effectively ye information milti hai:

```
Available tool:

get_invoice
→ Retrieve invoice
→ requires invoice_id
```

Phir:

```
User:
What's the status of INV-002?

          ↓

LLM:
I should use get_invoice.
```

## 3. Tool Description BAHUT Important Hai

Ye do tools consider kar:

```
search()
search()
```

**Terrible.**

Model ke paas ambiguity hogi — kaunsa `search()`?

Iske bajaye:

```
search_customer()
→ Search customers by name or email.

search_documents()
→ Search internal company documentation.
```

Ab:

```
"Find Rahul"
       ↓
search_customer()

"Find our refund policy"
       ↓
search_documents()
```

**Rule:**

> **Tool names aur descriptions tere routing interface ka hissa hain.**

Poor descriptions → poor tool selection. Ye koi cosmetic detail nahi hai, ye directly model ki decision-making ko affect karta hai.

## 4. Tools Ko Zyada Broad Mat Bana

**Bad:**

```
manage_customer()
```

Ye karta kya hai?

```
search?
update?
delete?
refund?
```

Model ke liye ambiguous.

**Better:**

```
search_customer()
get_customer()
update_customer()
```

Ab har tool ka ek focused responsibility hai.

**Ye basically Single Responsibility Principle hai jo LLM tools pe apply ho raha hai.**

## 5. Tools Ko Unnecessarily Granular Bhi Mat Bana

Opposite problem:

```
get_customer_name()
get_customer_email()
get_customer_phone()
get_customer_address()
get_customer_id()
```

Ab ek simple customer lookup ke liye chahiye:

```
5 tool calls
```

**Ye inefficient hai.**

Better:

```
get_customer()
```

jo return kare:

```json
{
  "id": "CUS-123",
  "name": "Rahul",
  "email": "rahul@example.com",
  "phone": "...",
  "address": "..."
}
```

**Goal:**

> Tools ko useful business capabilities represent karne chahiye, har tiny line of code nahi.

## 6. Tool Selection Deterministic Business Logic Nahi Hai

**Ye ek important distinction hai.**

Tere backend mein ho sakta hai:

```python
if request == "invoice":
    get_invoice()
```

Lekin **LLM tool selection probabilistic/model-driven hai.**

Tu provide karta hai:

```
tools
+
descriptions
+
schemas
```

aur model determine karta hai ki wo kya call karna chahta hai.

Yehi wajah hai ki evaluation baad mein important ban jaata hai.

## 7. Tool Choice Modes

Depending on API/provider, tere paas control ho sakta hai ki tools call ho sakte hain ya nahi.

Conceptually kuch modes hote hain jaise:

```
auto
none
required
specific tool
```

### Auto

Model decide karta hai:

> Kya mujhe ek tool call karna chahiye?

Example:

```
User:
What's 2 + 2?

→ No tool
```

Lekin:

```
User:
What's my invoice status?

→ get_invoice()
```

### None

Us request ke liye tool calling allow mat kar.

```
tools disabled
```

Useful hai jab tujhe explicitly text-only response chahiye.

### Required

Model ko forcefully ek tool call karwa.

Useful hai jab teri application ko ek external data lookup chahiye hi.

Conceptually:

```
User:
Give me my current balance.

         ↓

Tool call required
         ↓
get_balance()
```

### Specific Tool

Tu model ko ek particular tool tak constrain kar sakta hai.

Example:

```
Only use get_invoice.
```

Ye useful ho sakta hai jab teri application ne already determine kar liya hai ki kaunsa operation relevant hai.

**Note:** Exact parameter names aur capabilities provider ke hisaab se vary karte hain, isliye inhe API concepts ki tarah treat kar, kisi ek provider ka syntax blindly copy mat kar.

## 8. Tool Selection Kyun Fail Ho Sakti Hai

Maan le hamare paas hai:

```
search_customer()
search_documents()
```

User:

```
"Find information about Rahul."
```

**Ambiguous.**

Iska matlab ho sakta hai:

```
customer Rahul
```

ya:

```
documents mentioning Rahul
```

Model incorrectly choose kar sakta hai.

Possible solutions:

### Better Descriptions

```
search_customer()
→ Search customer records by customer identity.

search_documents()
→ Search internal documents and knowledge bases.
```

### Better User Clarification

```
Do you mean Rahul's customer record or documents about Rahul?
```

### Application-Level Routing

Kabhi kabhi tujhe har request ko sab tools expose nahi karne chahiye.

## 9. Tool Availability Dynamic Ho Sakti Hai

**Ye ek bahut useful production concept hai.**

Maan le user hai:

```
normal_support_agent
```

LLM ko ye mat de:

```
delete_account()
refund_payment()
change_subscription()
admin_database_query()
```

Iske bajaye sirf allowed tools expose kar:

```
search_customer()
get_invoice()
create_ticket()
```

Architecture:

```
User
 ↓
Authentication
 ↓
Permissions
 ↓
Allowed tools
 ↓
LLM
```

Ye nahi:

```
User
 ↓
LLM
 ↓
LLM chooses anything
```

**Ye dono hai — routing bhi aur security bhi.**

## 10. Tool Routing Layer

Eventually hum kuch aisa banayenge:

```
                    Request
                       │
                       ▼
                 Authentication
                       │
                       ▼
                 User permissions
                       │
                       ▼
                  Tool Registry
                       │
              ┌────────┴────────┐
              ↓                 ↓
       Allowed tools       Blocked tools
              │
              ▼
             LLM
              │
              ▼
        Tool selection
```

**Model ko sirf wo tools milte hain jo usse actually use karne ki permission hai.**

## 11. Example: Customer Support

Available tools:

```
search_customer()
get_invoice()
create_ticket()
send_notification()
```

User:

```
"My payment failed. Find my account and create a support ticket."
```

Possible trajectory:

```
LLM
 ↓
search_customer()
 ↓
Tool result
 ↓
LLM
 ↓
create_ticket()
 ↓
Tool result
 ↓
LLM
 ↓
Final response
```

Ek cheez notice kar:

**Model sirf ek tool select nahi kar raha.**

Ye ek **sequence of decisions** le sakta hai.

Yehi wajah hai ki tool selection eventually ek agent loop ban jaata hai.

## 12. Tool Selection ≠ Tool Execution

**Inhe separate rakh.**

### Selection

```
LLM:
"I want get_invoice."
```

### Execution

```
Backend:
"Okay, I'll actually execute get_invoice()."
```

Architecture:

```
        LLM
         │
         │ selection
         ▼
     Tool Call
         │
         │ execution
         ▼
      Backend
         │
         ▼
       Tool
```

**Model ko teri database ka direct access kabhi nahi hota.**

## 13. Agar Model Galat Tool Choose Kare Toh?

Example:

```
User:
What's the status of INV-002?
```

Model choose karta hai:

```
search_customer()
```

**Ye incorrect hai.**

Possible causes:

- poor description
- ambiguous tool names
- too many tools
- model limitations
- confusing schemas

Tu improve kar sakta hai:

```
tool descriptions
+
schemas
+
prompting
+
tool availability
+
evaluation
```

**Immediately kisi framework ko problem pe mat phenk de** — pehle basics fix kar.

## 14. Application Logic Ke Saath Tool Routing

Kabhi kabhi application ko kuch aisa pata hota hai jo LLM ko nahi pata.

Example:

```
User's request is already classified as billing.
```

Phir tera backend expose kar sakta hai:

```
billing tools only
```

iske bajaye:

```
50 tools
```

**Ye model ka search space reduce karta hai.**

Soch:

```
50 tools
 ↓
harder routing
 ↓
more ambiguity
```

versus:

```
5 relevant tools
 ↓
simpler routing
 ↓
better reliability
```

## 15. Bahut Zyada Tools Ek Real Problem Hai

Socho LLM ko dena:

```
200 tools
```

Ab isse ek huge tool catalog ke upar reason karna padega.

Potential problems:

- more context/token usage
- ambiguous selection
- slower requests
- higher chance of wrong tool
- larger tool definitions

Isliye production agents ko often **tool discovery/routing strategies** chahiye hoti hain, har possible tool ko har request mein dump karne ke bajaye.

Ye especially relevant ban jaayega jab hum MCP tak pahunchenge.

## 16. Tool Descriptions Ko Behavior Describe Karna Chahiye

**Bad:**

```
"Gets data."
```

**Good:**

```
"Retrieve an invoice by its unique invoice ID.
Use this when the user asks about the status,
amount, or due date of a specific invoice."
```

Doosri description model ko **routing information** deti hai.

Lekin massive novels bhi mat likh.

Teri tool description honi chahiye:

- specific
- clear
- non-ambiguous

## 17. Tool Selection Aur Security

Maan le:

```
delete_customer()
```

exist karta hai.

User bolta hai:

```
"Delete all customers."
```

Chahe model select kare:

```
delete_customer()
```

**tere backend ko phir bhi poochhna chahiye:**

```
Is this user authorized?
```

Toh:

```
Tool Selection
      ↓
Validation
      ↓
Authorization
      ↓
Execution
```

**Model ki final say nahi hoti.**

## 18. Actual API Flow

Conceptually:

```python
response = client.responses.create(
    model="YOUR_MODEL",
    input="What's the status of INV-002?",
    tools=tools
)
```

Response mein ek tool call ho sakta hai, jo conceptually aisa dikhega:

```
name:
get_invoice

arguments:
{
    "invoice_id": "INV-002"
}
```

Tera code phir ye karta hai:

```python
tool_name = tool_call.name

tool = TOOLS.get(tool_name)

if not tool:
    raise ValueError("Unknown tool")

args = tool["schema"].model_validate(
    tool_call.arguments
)

result = tool["handler"](
    **args.model_dump()
)
```

Ye bridge hai:

```
Topic 2
schema
```

se:

```
Topic 4
execution loop
```

## 19. Important Architecture

Ab tak:

```
                    USER
                      │
                      ▼
                     LLM
                      │
               Available tools
                      │
                      ▼
                TOOL SELECTION
                      │
                      ▼
                 Tool Call
                      │
                      ▼
             ┌────────────────┐
             │    Backend     │
             ├────────────────┤
             │ Schema         │
             │ Validation     │
             │ Authorization  │
             └───────┬────────┘
                     │
                     ▼
                 Execution
```

## 20. The Golden Rule

Ye yaad rakh:

> **Model ek tool recommend/select kar sakta hai. Tera backend usse execute karne ka authority rakhta hai.**

Aur ek aur:

> **Good tool design tool selection improve karta hai.**

Tool quality sirf implementation ke baare mein nahi hai.

Ye bhi hai:

```
Name
+
Description
+
Schema
+
Scope
+
Permissions
```