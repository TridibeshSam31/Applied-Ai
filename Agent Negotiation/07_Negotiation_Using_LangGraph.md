# Module: Agent Negotiation --- Topic 7/10

# Negotiation Using LangGraph

While linear chains or simple ReAct loops work for one-off tool calling, autonomous negotiation is inherently **cyclic**, **stateful**, and **multi-actor**. Two or more agents must converse in iterative rounds, inspect evolving proposals, evaluate conditional thresholds, and terminate when consensus or a deadline is reached.

**LangGraph** is the industry standard framework for this architecture. It provides:
1. **Explicit Cyclic Graph Execution:** Natural modeling of iterative offer-counteroffer loops.
2. **Deterministic State Schemas:** Strongly-typed state tracked across every negotiation turn.
3. **Conditional Routing:** Edge logic that dynamically routes execution based on proposal evaluations.
4. **Checkpointing & Time Travel:** Inherent persistence allowing long-running negotiations to pause for Human-in-the-Loop (HITL) manager sign-off and resume seamlessly.

---

## 1. Graph Architecture for Bilateral Negotiation

The bilateral negotiation graph models the alternating bargaining process as a cyclical state machine:

```text
                     ┌───────────────────────┐
                     │         START         │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │      Buyer Node       │ ◄─────────────────────────┐
                     │ (Evaluate / Propose)  │                           │
                     └───────────┬───────────┘                           │
                                 │                                       │
                                 ▼                                       │
                     ┌───────────────────────┐                           │
                     │ Buyer Route Decision  │                           │
                     └───┬───────────────┬───┘                           │
                 Accept  │               │ Counteroffer                  │
                         ▼               ▼                               │
                   ┌──────────┐    ┌───────────────────────┐             │
                   │   END    │    │      Seller Node      │             │
                   │(Agreement│    │ (Evaluate / Counter)  │             │
                   └──────────┘    └───────────┬───────────┘             │
                         ▲                     │                         │
                         │                     ▼                         │
                         │         ┌───────────────────────┐             │
                         │         │ Seller Route Decision │             │
                         │         └───┬───────────────┬───┘             │
                         │     Accept  │               │ Counteroffer    │
                         └─────────────┘               └─────────────────┘
                                                       (Advances Round;
                                                       checks deadline)
```

---

## 2. State Schema Design

A well-designed LangGraph state schema isolates the public negotiation transcript from private agent profiles, while maintaining a single source of truth for graph execution.

```python
from typing import Annotated, Any, Dict, List, Literal, Optional
from typing_extensions import TypedDict
import operator


class NegotiationState(TypedDict):
    # Session metadata
    session_id: str
    round_number: int
    max_rounds: int
    status: Literal["IN_PROGRESS", "AGREEMENT", "IMPASSE"]
    
    # Public dialogue history (accumulated via operator.add)
    history: Annotated[List[Dict[str, Any]], operator.add]
    
    # Active proposal under consideration
    current_proposal: Optional[Dict[str, float]]
    active_agent: str
    
    # Private agent parameters (In a microservice deployment, these reside in private stores)
    buyer_budget: float
    seller_cost_floor: float
    final_contract: Optional[Dict[str, float]]
```

---

## 3. Node Logic and Decision Primitives

Each node represents an agent taking a turn:
1. **Reads** the current public proposal from state.
2. **Evaluates** the utility against its internal reservation price and current aspiration level.
3. **Decides**:
   - If acceptable $\to$ Sets performative to `ACCEPT`.
   - If unacceptable but rounds remain $\to$ Computes concession and sets performative to `COUNTER`.
   - If round limit reached or reservation violated $\to$ Sets performative to `IMPASSE`.

---

## 4. Conditional Edge Routing

LangGraph conditional edges inspect the output performative of the active node:

```python
def route_after_buyer(state: NegotiationState) -> Literal["seller_node", "end_node"]:
    if state["status"] in ("AGREEMENT", "IMPASSE"):
        return "end_node"
    return "seller_node"

def route_after_seller(state: NegotiationState) -> Literal["buyer_node", "end_node"]:
    if state["status"] in ("AGREEMENT", "IMPASSE"):
        return "end_node"
    return "buyer_node"
```

---

## 5. Complete Runnable Implementation: LangGraph Negotiation Engine

Below is a complete, self-contained implementation constructing and compiling a cyclic negotiation graph with LangGraph.

*(Note: The implementation demonstrates the pure graph mechanics and state reducer transitions without requiring external API keys).*

```python
"""
langgraph_negotiation.py
Cyclic multi-agent negotiation engine implemented with LangGraph.
"""

from __future__ import annotations
from typing import Annotated, Any, Dict, List, Literal, Optional
from typing_extensions import TypedDict
import operator

# Core LangGraph primitives
from langgraph.graph import StateGraph, END


# =====================================================================
# 1. State Schema
# =====================================================================

class ContractState(TypedDict):
    session_id: str
    round_idx: int
    max_rounds: int
    status: Literal["IN_PROGRESS", "AGREEMENT", "IMPASSE"]
    
    # Public history uses operator.add reducer to append turns
    history: Annotated[List[Dict[str, Any]], operator.add]
    
    active_proposal: Optional[Dict[str, float]]
    final_agreement: Optional[Dict[str, float]]
    
    # Private constraints
    buyer_max_budget: float
    buyer_target: float
    seller_min_cost: float
    seller_target: float


# =====================================================================
# 2. Node Implementations
# =====================================================================

def buyer_node(state: ContractState) -> Dict[str, Any]:
    """Buyer evaluates seller's proposal or initiates opening offer."""
    round_idx = state["round_idx"] + 1
    active_offer = state["active_proposal"]
    max_budget = state["buyer_max_budget"]
    target = state["buyer_target"]

    # 1. If seller made an offer, evaluate it
    if active_offer:
        seller_price = active_offer["price"]
        # Acceptance condition: price <= buyer's current concession limit
        buyer_current_limit = target + (max_budget - target) * (round_idx / state["max_rounds"])
        
        if seller_price <= buyer_current_limit:
            return {
                "round_idx": round_idx,
                "status": "AGREEMENT",
                "final_agreement": active_offer,
                "history": [{
                    "round": round_idx,
                    "agent": "Buyer",
                    "action": "ACCEPT",
                    "proposal": active_offer,
                    "note": f"Accepted price ${seller_price:.2f} within limit ${buyer_current_limit:.2f}",
                }],
            }

    # 2. Check if deadline reached
    if round_idx > state["max_rounds"]:
        return {
            "round_idx": round_idx,
            "status": "IMPASSE",
            "history": [{"round": round_idx, "agent": "Buyer", "action": "IMPASSE", "note": "Max rounds reached."}],
        }

    # 3. Generate counteroffer (conceding linearly toward max budget)
    concession_factor = min(1.0, round_idx / float(state["max_rounds"]))
    counter_price = target + (max_budget - target) * (concession_factor * 0.7)
    counter_proposal = {
        "price": round(counter_price, 2),
        "delivery_days": 10.0,
        "sla_uptime": 99.9,
    }

    return {
        "round_idx": round_idx,
        "active_proposal": counter_proposal,
        "status": "IN_PROGRESS",
        "history": [{
            "round": round_idx,
            "agent": "Buyer",
            "action": "PROPOSE",
            "proposal": counter_proposal,
            "note": f"Offering ${counter_price:.2f}",
        }],
    }


def seller_node(state: ContractState) -> Dict[str, Any]:
    """Seller evaluates buyer's counteroffer and responds."""
    round_idx = state["round_idx"]
    active_offer = state["active_proposal"]
    min_cost = state["seller_min_cost"]
    target = state["seller_target"]

    # 1. Evaluate buyer's active offer
    buyer_price = active_offer["price"]
    # Seller's acceptable price decreases linearly over time toward cost floor
    concession_factor = min(1.0, round_idx / float(state["max_rounds"]))
    seller_current_floor = target - (target - min_cost) * (concession_factor * 0.8)

    if buyer_price >= seller_current_floor:
        return {
            "status": "AGREEMENT",
            "final_agreement": active_offer,
            "history": [{
                "round": round_idx,
                "agent": "Seller",
                "action": "ACCEPT",
                "proposal": active_offer,
                "note": f"Accepted price ${buyer_price:.2f} above floor ${seller_current_floor:.2f}",
            }],
        }

    # 2. Check deadline
    if round_idx >= state["max_rounds"]:
        return {
            "status": "IMPASSE",
            "history": [{"round": round_idx, "agent": "Seller", "action": "IMPASSE", "note": "Deadline reached."}],
        }

    # 3. Generate counteroffer
    counter_price = max(min_cost, target - (target - min_cost) * (concession_factor * 0.6))
    counter_proposal = {
        "price": round(counter_price, 2),
        "delivery_days": 14.0,
        "sla_uptime": 99.5,
    }

    return {
        "active_proposal": counter_proposal,
        "status": "IN_PROGRESS",
        "history": [{
            "round": round_idx,
            "agent": "Seller",
            "action": "COUNTER",
            "proposal": counter_proposal,
            "note": f"Counteroffering ${counter_price:.2f}",
        }],
    }


# =====================================================================
# 3. Conditional Edge Routers
# =====================================================================

def route_buyer_output(state: ContractState) -> str:
    if state["status"] in ("AGREEMENT", "IMPASSE"):
        return "end_node"
    return "seller_node"


def route_seller_output(state: ContractState) -> str:
    if state["status"] in ("AGREEMENT", "IMPASSE"):
        return "end_node"
    return "buyer_node"


# =====================================================================
# 4. Assemble and Compile the Graph
# =====================================================================

def build_negotiation_graph() -> StateGraph:
    workflow = StateGraph(ContractState)

    # Add agent nodes
    workflow.add_node("buyer_node", buyer_node)
    workflow.add_node("seller_node", seller_node)

    # Set entry point
    workflow.set_entry_point("buyer_node")

    # Add conditional edges
    workflow.add_conditional_edges(
        "buyer_node",
        route_buyer_output,
        {
            "seller_node": "seller_node",
            "end_node": END,
        },
    )

    workflow.add_conditional_edges(
        "seller_node",
        route_seller_output,
        {
            "buyer_node": "buyer_node",
            "end_node": END,
        },
    )

    return workflow.compile()


# =====================================================================
# Verification and Demonstration
# =====================================================================
if __name__ == "__main__":
    app = build_negotiation_graph()

    # Initial state configuration
    initial_state: ContractState = {
        "session_id": "LANGGRAPH-B2B-NEGOTIATION-001",
        "round_idx": 0,
        "max_rounds": 6,
        "status": "IN_PROGRESS",
        "history": [],
        "active_proposal": None,
        "final_agreement": None,
        # Private limits
        "buyer_max_budget": 280.0,
        "buyer_target": 180.0,
        "seller_min_cost": 220.0,
        "seller_target": 350.0,
    }

    print("=== Executing LangGraph Negotiation Engine ===")
    final_output = app.invoke(initial_state)

    print(f"\nFinal Session Status: {final_output['status']}")
    print(f"Total Turns Elapsed: {len(final_output['history'])}")
    print("\n--- Negotiation Dialogue Trace ---")
    for event in final_output["history"]:
        proposal_str = f"| Offer: {event.get('proposal')}" if event.get("proposal") else ""
        print(f"[Round {event['round']}] {event['agent']} -> {event['action']} {proposal_str} ({event['note']})")

    if final_output["status"] == "AGREEMENT":
        print(f"\n>>> FINAL BINDING CONTRACT REACHED: {final_output['final_agreement']}")
    else:
        print("\n>>> NEGOTIATION TERMINATED IN IMPASSE.")
```

---

## 6. Key Takeaways

1. **Cycles as First-Class Citizens**: LangGraph natively supports cyclic state transitions, making it the ideal framework for iterative negotiation loops.
2. **Conditional Edges Control Termination**: Dynamic routers eliminate infinite loops by checking agreement states, reservation constraints, and round deadlines on every hop.
3. **State Reducers Enable Auditability**: Using `operator.add` on the public history field ensures every action is automatically preserved in the trajectory log.
