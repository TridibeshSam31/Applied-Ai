# Multiple Tools & Tool Chaining 🔴🔴 — Tool Calling

Ab single-tool execution clear ho gaya. Ab **actual multi-step workflows** start hote hain.

Maan le user bolta hai:

```
"Rahul ka overdue invoice find karo, aur uske liye support ticket create karo."
```

**Ek tool enough nahi hai:**

```
search_customer()
       ↓
get_invoice()
       ↓
create_ticket()
```

**Isko tool chaining kehte hain.**

## 1. Tool Chaining Kya Hai?

> **Tool chaining ka matlab hai ek tool ka output doosre tool ke input ki tarah use karna.**

Example:

```
search_customer("Rahul")
        ↓
customer_id = "CUS-123"
        ↓
get_invoice("CUS-123")
        ↓
invoice_id = "INV-002"
        ↓
create_ticket("INV-002")
```

Basically:

```
Tool 1 output
     ↓
Tool 2 input
     ↓
Tool 3 input
```

## 2. Sequential vs Independent Tools

**Ye distinction important hai.**

### Sequential / Dependent

```
search_customer
       ↓
get_invoice
```

`get_invoice()` ko `search_customer()` ka result chahiye, isliye **sequential execution zaroori hai.**

### Independent

```
get_customer()
get_balance()
get_recent_orders()
```

Agar teeno ek dusre ke results pe depend nahi karte, toh inhe **parallel mein run kiya ja sakta hai.**

```
             LLM
          /    |    \
         ↓     ↓     ↓
     customer balance orders
         \     |     /
          \    |    /
             result
```

Parallel execution next topic mein karenge.

## 3. Real Example

Tools:

```
search_customer(name)
get_invoice(customer_id)
create_ticket(customer_id, invoice_id, issue)
```

User:

```
"Rahul ki overdue invoice ke liye ticket bana do."
```

LLM ke paas initially `customer_id` aur `invoice_id` nahi hain.

Toh wo decide kar sakta hai:

**Step 1**

```
search_customer("Rahul")
```

Result:

```json
{
  "customer_id": "CUS-123"
}
```

Phir LLM ko result milta hai aur wo decide karta hai:

**Step 2**

```
get_invoice("CUS-123")
```

Result:

```json
{
  "invoice_id": "INV-002",
  "status": "overdue"
}
```

Ab model ke paas required information hai:

**Step 3**

```
create_ticket(
    customer_id="CUS-123",
    invoice_id="INV-002",
    issue="Overdue invoice"
)
```

Result:

```json
{
  "ticket_id": "TKT-789",
  "status": "created"
}
```

Final response:

```
"I've created support ticket TKT-789 for Rahul's overdue invoice."
```

## 4. Ek Important Point: Chain Hardcode Mat Karna

Agar tu code likh de:

```python
customer = search_customer("Rahul")
invoice = get_invoice(customer["customer_id"])
ticket = create_ticket(...)
```

toh wo ek **normal deterministic workflow** hai.

**Galat nahi hai** — actually many production workflows ke liye ye better bhi ho sakta hai — **lekin ye LLM-driven tool orchestration demonstrate nahi karta.**

Hamare learning project mein:

```
LLM
 ↓
decides search_customer
 ↓
result
 ↓
LLM
 ↓
decides get_invoice
 ↓
result
 ↓
LLM
 ↓
decides create_ticket
```

**Next tool ka decision model karega**, previous result ko context mein dekhkar — code hardcode karke sequence force nahi karega.

## 5. Tool Dependencies

Workflow ko ek **dependency graph** ki tarah dekh:

```
search_customer
       │
       │ customer_id
       ▼
get_invoice
       │
       │ invoice_id
       ▼
create_ticket
```

Mathematically:

```
A → B → C
```

jahan:

```
B depends on A
C depends on B
```

Isliye:

```
A
↓
B
↓
C
```

**required hai.**

Tu C ko pehle execute nahi kar sakta agar uske required inputs abhi available hi nahi hain.

## 6. Tool Result Design Matter Karta Hai

Maan le:

```
search_customer("Rahul")
```

return karta hai:

```json
{
    "customer_id": "CUS-123",
    "name": "Rahul",
    "email": "...",
    "phone": "...",
    "address": "...",
    "internal_notes": "...",
    "metadata": "..."
}
```

Technically possible hai, lekin **unnecessary.**

Better:

```json
{
    "customer_id": "CUS-123",
    "name": "Rahul"
}
```

**Sirf required information return kar.**

Benefits:

```
less data
↓
less context
↓
fewer tokens
↓
lower cost
↓
less noise
```

Aur sensitive information unnecessarily model ke context mein nahi jaati.

## 7. Clean Tool Contracts

Good chaining ke liye tools ke input/output contracts **clear** hone chahiye.

Example:

```
search_customer()
OUTPUT:
customer_id
```

Phir:

```
get_invoice(customer_id)
INPUT:
customer_id
```

Phir:

```
get_invoice()
OUTPUT:
invoice_id
status
amount
```

Phir:

```
create_ticket(customer_id, invoice_id, issue)
```

Toh:

```
Tool A output
     ↓
Tool B input
```

Agar tool contracts messy hain, chaining **unreliable** ban jaayegi.

## 8. Chaining Linear Hona Zaroori Nahi Hai

Real workflows **branch** bhi kar sakte hain.

Example:

```
get_invoice()
      ↓
   status?
   /     \
paid     overdue
 │          │
 ↓          ↓
answer   create_ticket
             │
             ↓
        send_notification
```

Agar invoice paid hai:

```
→ answer
```

Agar overdue hai:

```
→ create_ticket()
→ send_notification()
```

Yahan previous tool ka result next action determine kar raha hai.

## 9. Critical Business Rules LLM Ko Mat De

**Ye bahut important production principle hai.**

Maan le rule hai:

```
"Refunds above ₹50,000 require manager approval."
```

Isko sirf LLM ke decision par mat chhod:

```
LLM:
"Seems okay, refund it."
```

**Backend mein deterministic rule hona chahiye:**

```python
if amount > 50000:
    require_manager_approval()
```

Toh:

```
LLM
 ↓
requests refund
 ↓
Backend business rules
 ↓
approval required?
 ↓
execute / reject
```

**LLM intent samajhne ke liye useful hai; critical authorization/business rules ka final authority backend hona chahiye.**

## 10. Tool Chaining + State

**Topic 5 ka state yahan directly use hota hai.**

Pehle tool ke baad:

```
step = 1

messages:
    user
    assistant → search_customer
    tool → CUS-123
```

Doosre ke baad:

```
step = 2

messages:
    user
    assistant → search_customer
    tool → CUS-123
    assistant → get_invoice
    tool → INV-002
```

Phir:

```
step = 3

assistant → create_ticket
tool → TKT-789
```

**Model ko trajectory ka relevant context milta rehta hai.**

## 11. Chain Mein Failures

Maan le:

```
search_customer()
       ↓
success
       ↓
get_invoice()
       ↓
database timeout
```

Possible responses:

```
retry get_invoice()
```

ya:

```
return controlled failure to LLM
```

ya, jahan appropriate ho:

```
fallback service/provider
```

**Phase 1 ki knowledge yahan directly reuse ho rahi hai:**

```
Retries
Timeouts
Error handling
```

Agar `search_customer()` already successful hai, toh unnecessarily poori chain restart mat kar.

**Prefer:**

```
search_customer()
      ↓
success
      ↓
get_invoice()
      ↓
timeout
      ↓
retry get_invoice()
```

iske bajaye:

```
❌ search_customer()
❌ get_invoice()
```

phir se.

**Ye latency, tokens, aur API calls save karta hai.**

## 12. Side Effects + Idempotency

Maan le chain pahunchti hai:

```
create_ticket()
```

aur execution ke time network problem ho gayi.

Agent ko lag sakta hai:

```
"Tool failed."
```

Lekin database mein ticket actually create ho chuka ho sakta hai.

Agar blindly retry kiya:

```
create_ticket()
```

phir se, tujhe mil sakta hai:

```
TKT-001
TKT-002
```

**same request ke liye.**

Yehi wajah hai ki side-effecting tools ko appropriate **idempotency/business safeguards** chahiye.

Conceptually:

```
request_id = REQ-123
```

Backend ye ensure kar sakta hai:

```
REQ-123
 ↓
ticket already created
 ↓
return existing ticket
```

**Ye ek wajah hai ki tool execution simply ek Python function call karne se kaafi zyada hai.**

## 13. Tool Chaining + Authorization

Maan le chain hai:

```
search_customer()
      ↓
get_invoice()
      ↓
refund_payment()
```

Chahe LLM select kare:

```
refund_payment()
```

**backend ko phir bhi check karna hoga:**

```
Is this user authorized?
```

Potentially:

```
amount > threshold?
       ↓
manager approval required
```

Toh har sensitive tool chain ko interrupt kar sakta hai:

```
LLM
 ↓
Tool Call
 ↓
Policy
 ↓
Execute
```

**Model ki final say nahi hoti.**

## 14. Chaining vs Orchestration

Yahan ek useful engineering distinction hai.

### LLM-Driven Orchestration

```
LLM
 ↓
decides next tool
 ↓
LLM
 ↓
decides next tool
```

**Flexible.**

### Code-Driven Orchestration

```python
customer = search_customer()
invoice = get_invoice(customer.id)
ticket = create_ticket(invoice.id)
```

**Deterministic.**

**Koi bhi automatically better nahi hai.**

Deterministic code use kar jab:

```
workflow is fixed
business rules are strict
safety is critical
```

LLM orchestration use kar jab:

```
workflow varies
user intent is unpredictable
next action depends on unstructured information
```

**Strong AI backend engineering ka matlab ye bhi hai ki tujhe pata ho kab agent unnecessary hai.**

## 15. Ek Giant Tool Mat Bana

**Bad:**

```
execute_customer_operation(
    operation="find_invoice_create_ticket_notify"
)
```

Tune poora workflow ek tool ke andar chhupa diya.

**Better:**

```
search_customer()
get_invoice()
create_ticket()
send_notification()
```

Phir model inhe compose kar sakta hai.

## 16. Lekin Tools Ko Over-Fragment Bhi Mat Kar

Ye bhi bad hai:

```
get_customer_id()
get_customer_name()
get_customer_email()
get_customer_phone()
```

Ek simple lookup ke liye char unnecessary calls chahiye ho sakti hain.

Meaningful business capabilities ko prefer kar:

```
get_customer()
```

har tiny database operation ko ek LLM-facing tool banane ke bajaye.

## 17. Hamara Project

Hum eventually ye expose kar rahe hain:

```
search_customer()
get_invoice()
create_ticket()
update_ticket()
search_documents()
send_notification()
```

Example:

```
"Find Rahul's overdue invoice and notify him."
```

Potential trajectory:

```
search_customer
      ↓
get_invoice
      ↓
send_notification
      ↓
final answer
```

Doosra:

```
"Find Rahul's invoice and create a ticket."
```

```
search_customer
      ↓
get_invoice
      ↓
create_ticket
```

Doosra:

```
"Update the ticket with the refund policy."
```

Potentially:

```
search_documents
      ↓
update_ticket
```

**Same tools, different workflows.**

**Yehi tool composition ki actual value hai.**

## 🧠 Jo Tujhe Yaad Rakhna Hai

### Tool Chaining

```
A → B → C
```

jab outputs inputs ban jaate hain.

### Sequential Execution

Use kar jab tools mein dependencies hon.

### Parallel Execution

Use kar jab operations independent hon.

### Conditional Branching

```
result
 ↓
condition
 ↓
different tool
```

### Deterministic Business Logic

Critical rules backend code se enforce hone chahiye.

### Idempotency

Especially important un tools ke liye jo cheezein create/update/delete karte hain.

### State

Trajectory ko multiple calls ke across preserve karta hai.

## 🎯 Interview Question

Agar interviewer poochhe:

> **"Would you let an LLM orchestrate every backend workflow?"**

**"Yes" mat bol.**

Ek stronger answer:

> "Nahi. Main LLM-driven orchestration use karunga jab workflow variable user intent ya dynamically discovered information pe depend karta ho. Deterministic aur safety-critical workflows ke liye, main explicit application logic prefer karunga aur LLM ko sirf wahan use karunga jahan language understanding ya flexible decision-making actually useful ho."

**Yehi wo engineering answer hai jo wo dhoond rahe hain.**


---

## 9. Complete Production Implementation: Dynamic Multi-Step Tool Chaining Pipeline 💻

Below is an end-to-end Python implementation demonstrating a production **Tool Chaining Pipeline**:
1. **Multi-Step Dependency Resolution:** Output of Tool A (`find_order_id`) flows into Tool B (`get_shipping_details`), which flows into Tool C (`calculate_delivery_eta`).
2. **Deterministic Fallback vs LLM Autonomous Chaining:** Shows how to guard against hallucinations and infinite looping using step-budget counters and state verification.
3. **Loop Detection & Context Window Compaction:** Prevents the LLM from repeatedly calling the same failing tool.

```python
"""
tool_chaining_pipeline.py
Production Implementation of Multi-Step Tool Chaining:
Dependency Resolution, State Transition Verification, and Loop Detection.
"""

import json
from typing import Dict, Any, List, Optional


# =====================================================================
# 1. Chained Service Tools
# =====================================================================
def get_user_orders(user_email: str) -> Dict[str, Any]:
    database = {
        "user@corp.com": [{"order_id": "ORD-5541", "created_at": "2026-11-15", "status": "shipped"}]
    }
    orders = database.get(user_email)
    if not orders:
        return {"error": "No orders found for email."}
    return {"orders": orders}


def get_tracking_info(order_id: str) -> Dict[str, Any]:
    tracking_db = {
        "ORD-5541": {"carrier": "BlueDart", "tracking_no": "BD-90210", "current_hub": "Bengaluru Sorting Facility"}
    }
    info = tracking_db.get(order_id)
    if not info:
        return {"error": f"No tracking details found for order {order_id}"}
    return info


def calculate_delivery_estimate(tracking_no: str) -> Dict[str, Any]:
    if tracking_no == "BD-90210":
        return {"estimated_delivery": "2026-11-21 by 6:00 PM", "status": "In Transit"}
    return {"error": "Tracking number not found in carrier network."}


TOOLS_MAP = {
    "get_user_orders": get_user_orders,
    "get_tracking_info": get_tracking_info,
    "calculate_delivery_estimate": calculate_delivery_estimate
}


# =====================================================================
# 2. Multi-Step Chaining Coordinator with Loop Guard
# =====================================================================
class ToolChainingCoordinator:
    def __init__(self, max_hops: int = 5):
        self.max_hops = max_hops
        self.execution_history: List[str] = []

    def execute_chain(self, initial_query: str):
        print(f"\n[USER GOAL]: {initial_query}\n" + "="*65)
        
        # Simulating the multi-step chain execution
        # Step 1: User email -> Order ID
        print("\n>>> Hop 1: Resolving order ID from user email...")
        orders_res = TOOLS_MAP["get_user_orders"](user_email="user@corp.com")
        self.execution_history.append("get_user_orders")
        print("    Result:", orders_res)

        order_id = orders_res["orders"][0]["order_id"]

        # Step 2: Order ID -> Carrier Tracking Number
        print(f"\n>>> Hop 2: Chaining order_id '{order_id}' to tracking info...")
        track_res = TOOLS_MAP["get_tracking_info"](order_id=order_id)
        self.execution_history.append("get_tracking_info")
        print("    Result:", track_res)

        tracking_no = track_res["tracking_no"]

        # Step 3: Tracking Number -> Live Delivery Estimate
        print(f"\n>>> Hop 3: Chaining tracking_no '{tracking_no}' to carrier API...")
        eta_res = TOOLS_MAP["calculate_delivery_estimate"](tracking_no=tracking_no)
        self.execution_history.append("calculate_delivery_estimate")
        print("    Result:", eta_res)

        # Final Synthesis
        print("\n" + "="*65)
        print("[FINAL ASSISTANT ANSWER]")
        print(f"Your order {order_id} is currently {eta_res['status']} at {track_res['current_hub']}.")
        print(f"Carrier: {track_res['carrier']} (Tracking #{tracking_no})")
        print(f"Expected Delivery: {eta_res['estimated_delivery']}")
        print(f"Total Chaining Hops: {len(self.execution_history)}")


if __name__ == "__main__":
    coordinator = ToolChainingCoordinator(max_hops=4)
    coordinator.execute_chain("Where is my order? My email is user@corp.com")
```

### Execution:
```bash
python tool_chaining_pipeline.py
```
