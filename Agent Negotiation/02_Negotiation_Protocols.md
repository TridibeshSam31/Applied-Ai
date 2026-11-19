# Module: Agent Negotiation --- Topic 2/10

# Negotiation Protocols

A **Negotiation Protocol** defines the formal rules of engagement governing multi-agent interactions. While an agent's *strategy* dictates *what* it chooses to offer or accept, the *protocol* dictates *who* can speak, *when* they can speak, *what message types* are legally permissible, and *how* the negotiation terminates.

Without a strictly enforced protocol, multi-agent systems suffer from race conditions, deadlocks, infinite messaging loops, and unresolvable disputes.

---

## 1. Formal Communication Primitives (FIPA-ACL Standard)

Standardized protocols rely on well-defined communicative acts. The Foundation for Intelligent Physical Agents (FIPA) Agent Communication Language (ACL) defines the core communicative performatives used in autonomous negotiation:

```text
┌─────────────────┐       Call For Proposal (CFP)       ┌─────────────────┐
│                 │ ──────────────────────────────────► │                 │
│                 │          Propose(Offer)             │                 │
│                 │ ◄────────────────────────────────── │                 │
│    Manager /    │        Accept-Proposal(Deal)        │   Participant / │
│   Buyer Agent   │ ──────────────────────────────────► │   Seller Agent  │
│                 │        Reject-Proposal(Reason)      │                 │
│                 │ ──────────────────────────────────► │                 │
│                 │               Inform                │                 │
│                 │ ◄────────────────────────────────── │                 │
└─────────────────┘                                     └─────────────────┘
```

| Performative | Sender | Receiver | Semantic Meaning |
| :--- | :--- | :--- | :--- |
| **CFP (Call For Proposal)** | Manager / Buyer | Candidates | Invites bids under specific issue constraints and deadlines. |
| **PROPOSE** | Participant | Manager | Submits a formal, binding offer with explicit issue values. |
| **ACCEPT-PROPOSAL** | Either | Counterpart | Formally accepts the active proposal; creates a binding agreement. |
| **REJECT-PROPOSAL** | Either | Counterpart | Rejects the active proposal with optional explanatory feedback. |
| **TERMINATE / CANCEL**| Either | Counterpart | Aborts the negotiation session without agreement (impasse). |

---

## 2. Taxonomy of Negotiation Protocols

Negotiation protocols are categorized across two primary architectural axes: **Participant Cardinality** and **Temporal Ordering**.

```text
                                Negotiation Protocols
                                          │
            ┌─────────────────────────────┴─────────────────────────────┐
            ▼                                                           ▼
   Bilateral Protocols                                       Multilateral Protocols
    (Exactly 2 Agents)                                       (3 or More Agents)
   ┌─────────────────────────────────┐                       ┌─────────────────────────────────┐
   │ • Alternating Offers Protocol   │                       │ • One-to-Many:                  │
   │   (Rubinstein Bargaining)       │                       │   Contract Net Protocol (CNP)   │
   │ • Take-it-or-leave-it           │                       │   English / Dutch / Vickrey     │
   │   (Ultimatum Game)              │                       │ • Many-to-Many:                 │
   │                                 │                       │   Continuous Double Auction     │
   └─────────────────────────────────┘                       └─────────────────────────────────┘
```

### A. Bilateral: Alternating Offers (Rubinstein Protocol)
The most common protocol for enterprise contracting:
1. Agent $A$ proposes offer $\mathbf{x}_1$ at round $t=1$.
2. Agent $B$ can either:
   - **Accept** $\mathbf{x}_1$ $\to$ Agreement reached.
   - **Walk away** $\to$ Impasse.
   - **Counterpropose** $\mathbf{x}_2$ at round $t=2$.
3. The process alternates sequentially until an agreement is reached or the maximum round / timeout is exceeded.

### B. Multilateral: One-to-Many (Contract Net Protocol - CNP)
Designed for distributed task allocation and vendor procurement:
1. **Manager** broadcasts a `CFP` describing task specs and SLA criteria to $N$ contractors.
2. **Contractors** evaluate their capacity and submit `PROPOSE` bids or refuse.
3. **Manager** compares bids using a multi-attribute utility function and sends `ACCEPT-PROPOSAL` to the winning contractor and `REJECT-PROPOSAL` to the others.
4. **Winner** confirms execution via `INFORM`.

### C. Multilateral: Many-to-Many (Continuous Double Auction)
Used in high-frequency compute spot markets, energy trading, and automated exchanges:
- Multiple buyers place bids (maximum price they will pay).
- Multiple sellers place asks (minimum price they will accept).
- An order book matches intersecting bids and asks using clearing rules (e.g., $p_{clearing} = \frac{bid + ask}{2}$).

---

## 3. Temporal Dimensions and The Rubinstein Bargaining Model

Time is not neutral in negotiation. Delays consume LLM API tokens, tie up computational resources, and introduce opportunity costs.

In 1982, economist Ariel Rubinstein formalized the **Alternating Offers Bargaining Game with Discount Factors**. 

If agents have discount factors $\delta_A, \delta_B \in (0, 1)$, a payoff received at round $t$ is discounted by $\delta^t$:

$$U_A(\mathbf{x}, t) = \delta_A^t \cdot U_A(\mathbf{x})$$

```text
Utility Over Time with Discount Factor (delta = 0.90)
Round 0: 1.000 ════════════════════════════════════════
Round 1: 0.900 ══════════════════════════════════
Round 2: 0.810 ════════════════════════════
Round 3: 0.729 ═══════════════════════
Round 4: 0.656 ══════════════════
Round 5: 0.590 ═══════════════
```

### Game-Theoretic Theorem
In infinite-horizon alternating bargaining with perfect information, there exists a unique **Subgame Perfect Nash Equilibrium (SPE)**:
- Agreement is reached **immediately at round 0**.
- Agent $A$ (the first mover) proposes a split where Agent $B$ receives exactly what Agent $B$ could guarantee by rejecting and making a counterproposal in round 1.
- The equilibrium payoff share $s_A^*$ allocated to Agent $A$ is:

$$s_A^* = \frac{1 - \delta_B}{1 - \delta_A \delta_B}$$

**Engineering Implication:** In automated agent systems, the agent that is more patient (higher $\delta$) commands higher bargaining power. An agent under severe latency or deadline constraints ($\delta \to 0$) is forced to concede rapidly.

---

## 4. Protocol Invariants and Anti-Abuse Engineering

When running distributed agents across separate processes or network boundaries, protocols must defend against:

1. **Turn Jumping**: An agent spamming multiple counteroffers out of turn to manipulate the state machine.
2. **Post-Deadline Exploitation**: Accepting an offer after its expiration timestamp has elapsed.
3. **Ghost Proposals**: Referencing non-existent proposal IDs during acceptance.
4. **Retroactive Modification**: Mutating an offer's terms after it has been transmitted.

---

## 5. Implementation: Bilateral and Multilateral Protocols

Below is an enterprise-ready implementation containing both:
1. **The Rubinstein Alternating Offers Protocol** with temporal discounting.
2. **The Contract Net Protocol (CNP) Orchestrator** for competitive multi-vendor bidding.

```python
"""
negotiation_protocols.py
Protocols for Bilateral (Rubinstein) and Multilateral (Contract Net Protocol) negotiation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional
import uuid


class Performative(str, Enum):
    CFP = "CFP"
    PROPOSE = "PROPOSE"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    TERMINATE = "TERMINATE"


@dataclass(frozen=True)
class Message:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    performative: Performative = Performative.PROPOSE
    sender: str = ""
    receiver: str = ""
    round_idx: int = 0
    payload: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# =====================================================================
# 1. Bilateral Protocol: Rubinstein Alternating Offers with Discounting
# =====================================================================

class BilateralAlternatingProtocol:
    """
    Enforces strict turn-taking, temporal discounting, and valid state transitions
    between two bargaining agents.
    """

    def __init__(
        self,
        agent_a: str,
        agent_b: str,
        delta_a: float = 0.95,
        delta_b: float = 0.90,
        max_rounds: int = 10,
    ) -> None:
        self.participants = [agent_a, agent_b]
        self.deltas = {agent_a: delta_a, agent_b: delta_b}
        self.max_rounds = max_rounds
        self.current_round = 0
        self.turn_idx = 0
        self.active_proposal: Optional[Message] = None
        self.is_finished = False
        self.agreed_deal: Optional[Dict[str, float]] = None

    @property
    def current_actor(self) -> str:
        return self.participants[self.turn_idx]

    def process_message(self, msg: Message) -> None:
        if self.is_finished:
            raise RuntimeError("Cannot process messages: Protocol has already terminated.")

        if msg.sender != self.current_actor:
            raise PermissionError(
                f"Protocol violation: Turn belongs to {self.current_actor}, but received message from {msg.sender}"
            )

        if msg.performative == Performative.PROPOSE:
            self.active_proposal = msg
            self._advance_turn()

        elif msg.performative == Performative.ACCEPT:
            if not self.active_proposal:
                raise ValueError("Illegal ACCEPT: No active proposal exists to accept.")
            self.is_finished = True
            self.agreed_deal = self.active_proposal.payload

        elif msg.performative == Performative.TERMINATE:
            self.is_finished = True
            self.agreed_deal = None

    def calculate_discounted_payoff(self, agent_id: str, raw_utility: float) -> float:
        """Applies the temporal discount factor: Utility * (delta ^ round)."""
        delta = self.deltas[agent_id]
        return raw_utility * (delta ** self.current_round)

    def _advance_turn(self) -> None:
        self.turn_idx = 1 - self.turn_idx
        if self.turn_idx == 0:
            self.current_round += 1
            if self.current_round >= self.max_rounds:
                self.is_finished = True  # Deadline expired -> Impasse


# =====================================================================
# 2. Multilateral Protocol: Contract Net Protocol (CNP) Orchestrator
# =====================================================================

@dataclass
class TaskRequirement:
    task_id: str
    min_ram_gb: float
    max_price: float
    deadline_hours: float


class ContractNetOrchestrator:
    """
    Orchestrates one-to-many procurement matching a manager agent against
    multiple bidding contractor agents.
    """

    def __init__(self, manager_id: str) -> None:
        self.manager_id = manager_id

    def execute_procurement(
        self,
        task: TaskRequirement,
        contractor_ids: List[str],
        bidding_functions: Dict[str, Callable[[TaskRequirement], Optional[Dict[str, float]]]],
        scoring_function: Callable[[Dict[str, float]], float],
    ) -> Optional[tuple[str, Dict[str, float]]]:
        """
        Executes a complete CNP round:
        1. Broadcast CFP
        2. Collect Proposals
        3. Evaluate & Award Contract
        """
        print(f"[{self.manager_id}] Broadcasting CFP for Task {task.task_id} to {len(contractor_ids)} contractors.")

        # Step 1 & 2: Collect proposals
        proposals: Dict[str, Dict[str, float]] = {}
        for contractor_id in contractor_ids:
            bid_func = bidding_functions.get(contractor_id)
            if not bid_func:
                continue
            bid = bid_func(task)
            if bid is not None:
                # Basic validation: cannot exceed max_price
                if bid.get("price", float("inf")) <= task.max_price:
                    proposals[contractor_id] = bid
                    print(f"  -> Contractor {contractor_id} submitted valid proposal: {bid}")
                else:
                    print(f"  -> Contractor {contractor_id} bid exceeds max price. Discarded.")

        if not proposals:
            print(f"[{self.manager_id}] Procurement failed: No valid proposals received.")
            return None

        # Step 3: Evaluate and Select Best Bid
        best_contractor: Optional[str] = None
        best_score = float("-inf")
        best_bid: Optional[Dict[str, float]] = None

        for contractor_id, bid in proposals.items():
            score = scoring_function(bid)
            if score > best_score:
                best_score = score
                best_contractor = contractor_id
                best_bid = bid

        print(f"[{self.manager_id}] Contract awarded to {best_contractor} (Score: {best_score:.4f})")
        return best_contractor, best_bid


# =====================================================================
# Verification and Demonstration
# =====================================================================
if __name__ == "__main__":
    print("--- 1. Testing Bilateral Alternating Protocol ---")
    proto = BilateralAlternatingProtocol("buyer_agent", "seller_agent", delta_a=0.95, delta_b=0.90)

    # Round 0: Buyer proposes
    msg1 = Message(
        performative=Performative.PROPOSE,
        sender="buyer_agent",
        receiver="seller_agent",
        round_idx=0,
        payload={"price": 100.0, "latency_ms": 50.0},
    )
    proto.process_message(msg1)
    print(f"After turn 1: Next actor is {proto.current_actor}, round={proto.current_round}")

    # Round 0: Seller counters
    msg2 = Message(
        performative=Performative.PROPOSE,
        sender="seller_agent",
        receiver="buyer_agent",
        round_idx=0,
        payload={"price": 140.0, "latency_ms": 60.0},
    )
    proto.process_message(msg2)
    print(f"After turn 2: Next actor is {proto.current_actor}, round={proto.current_round}")

    # Round 1: Buyer accepts
    msg3 = Message(
        performative=Performative.ACCEPT,
        sender="buyer_agent",
        receiver="seller_agent",
        round_idx=1,
    )
    proto.process_message(msg3)
    print(f"Deal status: is_finished={proto.is_finished}, Agreed deal: {proto.agreed_deal}")
    buyer_discounted = proto.calculate_discounted_payoff("buyer_agent", raw_utility=0.85)
    print(f"Buyer raw utility 0.85 at round 1 -> Discounted utility: {buyer_discounted:.4f}\n")

    print("--- 2. Testing Multilateral Contract Net Protocol (CNP) ---")
    orchestrator = ContractNetOrchestrator(manager_id="cloud_scheduler")
    task_req = TaskRequirement(task_id="JOB-GPU-88", min_ram_gb=64, max_price=500.0, deadline_hours=4.0)

    # Mock bidding functions for 3 contractors
    bids = {
        "aws_node": lambda t: {"price": 420.0, "delivery_hours": 1.0, "sla": 99.99},
        "gcp_node": lambda t: {"price": 380.0, "delivery_hours": 2.5, "sla": 99.95},
        "onprem_node": lambda t: {"price": 250.0, "delivery_hours": 3.8, "sla": 99.50},
    }

    # Scoring: higher SLA and lower price give higher score
    def evaluate_bid(b: Dict[str, float]) -> float:
        return (500.0 - b["price"]) * 0.6 + (b["sla"] - 99.0) * 100.0 * 0.4

    winner, winning_bid = orchestrator.execute_procurement(
        task=task_req,
        contractor_ids=list(bids.keys()),
        bidding_functions=bids,
        scoring_function=evaluate_bid,
    )
    print(f"Winner: {winner} with terms: {winning_bid}")
```

---

## 6. Key Takeaways

1. **Protocol Separates Rules from Tactics**: An agent's AI logic decides *what* offer to generate, but the protocol strictly decides *valid turn-taking*, *message schemas*, and *termination conditions*.
2. **Rubinstein Discounting Penalizes Delay**: In real-time multi-agent negotiation, patience is power, but latency has an exponential cost ($\delta^t$).
3. **CNP Enables Competitive One-to-Many Markets**: When allocating tasks or procuring resources across multiple providers, the Contract Net Protocol provides a clean, parallel bidding structure with clear award criteria.
