# Module: Agent Negotiation --- Topic 6/10

# Multi-Agent Negotiation Architecture

In production environments, negotiating agents do not exist in an isolated Jupyter notebook or a single monolithic script. They run as independent, distributed services representing distinct legal or business entities.

Building a production-grade negotiation architecture requires solving three core distributed systems challenges:
1. **Privacy Isolation:** Ensuring private budgets, cost structures, and utility models can never be leaked to counterparts.
2. **Deterministic Orchestration:** Preventing turn-jumping, message reordering, and race conditions.
3. **Auditable Non-Repudiation:** Creating an immutable, tamper-evident record of all proposals and binding agreements.

---

## 1. System Topology: Peer-to-Peer vs. Mediated Coordinator

There are two primary architectural topologies for multi-agent negotiation:

```text
       Topology A: Peer-to-Peer (P2P)                  Topology B: Mediated Coordinator
                                                            (Enterprise Production Standard)

   ┌──────────────┐          ┌──────────────┐                 ┌──────────────┐
   │ Buyer Agent  │ ◄──────► │ Seller Agent │                 │ Buyer Agent  │
   └──────────────┘          └──────────────┘                 └──────┬───────┘
          • High risk of race conditions                             │ Private session
          • Complex synchronization                                  ▼
          • No neutral audit arbiter                       ┌───────────────────┐
                                                           │    COORDINATOR    │
                                                           │ • Turn Enforcer   │
                                                           │ • Invariant Guard │
                                                           │ • Audit Ledger    │
                                                           └─────────┬─────────┘
                                                                     ▲
                                                                     │ Private session
                                                              ┌──────┴───────┐
                                                              │ Seller Agent │
                                                              └──────────────┘
```

In enterprise B2B systems, the **Mediated Coordinator Topology** is preferred:
- The coordinator acts as the neutral gatekeeper.
- It validates message schemas, strictly manages alternating turns, rejects illegal actions, and timestamps every event into a persistent ledger.
- Neither agent talks directly to the other's internal memory or private state.

---

## 2. Component Architecture of a Negotiating Agent

Each participating agent service is composed of modular internal layers:

```text
┌────────────────────────────────────────────────────────┐
│                   NEGOTIATING AGENT                    │
├────────────────────────────────────────────────────────┤
│ 1. Communication Gateway (HTTP / WebSockets / gRPC)   │
│    Serializes and deserializes structured Pydantic     │
│    messages; verifies cryptographic signatures.        │
├────────────────────────────────────────────────────────┤
│ 2. Strategic Decision Engine                           │
│    • Concession Curve Generator (Boulware/Linear)      │
│    • Opponent Preference Model                         │
│    • LLM Tactical Reasoner (Context-guarded)           │
├────────────────────────────────────────────────────────┤
│ 3. Private Domain Store                                │
│    • Multi-Attribute Utility Function (MAUT)           │
│    • Private Reservation Price (RP) & BATNA            │
│    • Enterprise Inventory / Budget Constraints         │
├────────────────────────────────────────────────────────┤
│ 4. Deterministic Guardrail Interceptor                 │
│    Hard software assertions preventing any action      │
│    below reservation threshold or out-of-protocol.     │
└────────────────────────────────────────────────────────┘
```

---

## 3. Communication Contract: Typed Message Schemas

All messages exchanged through the coordinator must adhere to strict, validated schemas to prevent malformed data and injection attacks.

```text
Message Structure:
┌────────────────────────────────────────────────────────┐
│ header:                                                │
│   message_id: "msg_9f81a7b..."                         │
│   session_id: "sess_corp_2026"                         │
│   sender_id:  "buyer_agent_alpha"                      │
│   round_idx:  3                                        │
│   timestamp:  "2026-11-19T14:30:00Z"                   │
│   signature:  "sha256_hash_signature"                  │
├────────────────────────────────────────────────────────┤
│ performative: "COUNTEROFFER"                           │
├────────────────────────────────────────────────────────┤
│ proposal:                                              │
│   price: 185.00                                        │
│   delivery_days: 10                                    │
│   sla_tier: "Gold"                                     │
├────────────────────────────────────────────────────────┤
│ public_notes: "Accepted your delivery timeline, but    │
│                adjusted price to maintain margins."    │
└────────────────────────────────────────────────────────┘
```

---

## 4. State Management and Privacy Isolation

A critical engineering failure in naive multi-agent implementations is **Shared State Bleed**: placing both agents in the same runtime memory object where Agent $A$ can accidentally inspect Agent $B$'s attributes.

```text
ANTI-PATTERN (Shared State Bleed):
class NegotiationRoom:
    buyer_budget = 1000      # ACCESSIBLE TO ALL AGENTS!
    seller_cost = 600        # ZERO PRIVACY!

PRODUCTION PATTERN (Decoupled Actors):
BuyerProcess:  Owns private memory {budget: 1000}. Exposes only public bids.
SellerProcess: Owns private memory {cost: 600}.   Exposes only public asks.
Coordinator:   Owns session state {round, public_history}. Has no access to private RP.
```

---

## 5. Implementation: Modular Multi-Agent Architecture

Below is a complete Python implementation demonstrating the decoupled architecture with a Coordinator, independent Buyer and Seller agents, strict message validation, and private state insulation.

```python
"""
multi_agent_architecture.py
Decoupled multi-agent negotiation system with Coordinator, Buyer, and Seller agents.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import hashlib
import json
import uuid


class Performative(str, Enum):
    PROPOSE = "PROPOSE"
    COUNTER = "COUNTER"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    TERMINATE = "TERMINATE"


@dataclass(frozen=True)
class ContractProposal:
    price: float
    delivery_days: int
    sla_uptime: float


@dataclass(frozen=True)
class NegotiationMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str = ""
    sender_id: str = ""
    round_idx: int = 0
    performative: Performative = Performative.PROPOSE
    proposal: Optional[ContractProposal] = None
    public_rationale: str = ""

    def compute_hash(self) -> str:
        """Generates a tamper-evident digest of the message content."""
        content = f"{self.session_id}:{self.sender_id}:{self.round_idx}:{self.performative.value}:{self.proposal}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


# =====================================================================
# Base Agent Class (Decoupled Actor)
# =====================================================================

class BaseNegotiator:
    """Abstract base class for independent negotiating agents."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id

    def receive_message(self, message: NegotiationMessage) -> NegotiationMessage:
        raise NotImplementedError


# =====================================================================
# Specialized Buyer Agent
# =====================================================================

class BuyerAgent(BaseNegotiator):
    def __init__(self, agent_id: str, max_budget: float, target_price: float) -> None:
        super().__init__(agent_id)
        # Private state
        self._max_budget = max_budget
        self._target_price = target_price
        self._concession_step = (max_budget - target_price) / 5.0
        self._current_bid = target_price

    def receive_message(self, incoming: NegotiationMessage) -> NegotiationMessage:
        session_id = incoming.session_id
        current_round = incoming.round_idx

        # If incoming is an offer from seller
        if incoming.proposal:
            offered_price = incoming.proposal.price

            # Acceptance rule: Is offered price within our acceptable target/budget?
            if offered_price <= self._current_bid:
                return NegotiationMessage(
                    session_id=session_id,
                    sender_id=self.agent_id,
                    round_idx=current_round,
                    performative=Performative.ACCEPT,
                    proposal=incoming.proposal,
                    public_rationale="Terms accepted. Offer satisfies our financial parameters.",
                )

        # Otherwise, calculate counteroffer
        self._current_bid = min(self._max_budget, self._current_bid + self._concession_step)

        # Check if even max budget cannot meet seller's price
        if incoming.proposal and incoming.proposal.price > self._max_budget and self._current_bid >= self._max_budget:
            # Cannot reach agreement
            return NegotiationMessage(
                session_id=session_id,
                sender_id=self.agent_id,
                round_idx=current_round,
                performative=Performative.TERMINATE,
                public_rationale="Reached maximum budget constraint. Terminating negotiation.",
            )

        counter_proposal = ContractProposal(
            price=round(self._current_bid, 2),
            delivery_days=7,
            sla_uptime=99.9,
        )

        return NegotiationMessage(
            session_id=session_id,
            sender_id=self.agent_id,
            round_idx=current_round,
            performative=Performative.COUNTER,
            proposal=counter_proposal,
            public_rationale=f"Counteroffering with adjusted price ${self._current_bid:.2f}.",
        )


# =====================================================================
# Specialized Seller Agent
# =====================================================================

class SellerAgent(BaseNegotiator):
    def __init__(self, agent_id: str, cost_floor: float, opening_price: float) -> None:
        super().__init__(agent_id)
        # Private state
        self._cost_floor = cost_floor
        self._opening_price = opening_price
        self._concession_step = (opening_price - cost_floor) / 6.0
        self._current_ask = opening_price

    def receive_message(self, incoming: NegotiationMessage) -> NegotiationMessage:
        session_id = incoming.session_id
        current_round = incoming.round_idx

        if incoming.proposal:
            buyer_price = incoming.proposal.price

            # Acceptance rule: Is buyer price >= our current ask?
            if buyer_price >= self._current_ask:
                return NegotiationMessage(
                    session_id=session_id,
                    sender_id=self.agent_id,
                    round_idx=current_round,
                    performative=Performative.ACCEPT,
                    proposal=incoming.proposal,
                    public_rationale="Offer meets our profitability and operational threshold.",
                )

        # Calculate counteroffer
        self._current_ask = max(self._cost_floor, self._current_ask - self._concession_step)

        counter_proposal = ContractProposal(
            price=round(self._current_ask, 2),
            delivery_days=10,
            sla_uptime=99.5,
        )

        return NegotiationMessage(
            session_id=session_id,
            sender_id=self.agent_id,
            round_idx=current_round,
            performative=Performative.COUNTER,
            proposal=counter_proposal,
            public_rationale=f"Conceding price down to ${self._current_ask:.2f}.",
        )


# =====================================================================
# Neutral Coordinator (Mediator)
# =====================================================================

class NegotiationCoordinator:
    """
    Manages session routing, turn order, ledger immutability, and termination.
    """

    def __init__(self, session_id: str, buyer: BuyerAgent, seller: SellerAgent, max_rounds: int = 10) -> None:
        self.session_id = session_id
        self.agents: Dict[str, BaseNegotiator] = {buyer.agent_id: buyer, seller.agent_id: seller}
        self.turn_order = [buyer.agent_id, seller.agent_id]
        self.max_rounds = max_rounds
        self.ledger: List[NegotiationMessage] = []
        self.is_completed = False
        self.final_agreement: Optional[ContractProposal] = None

    def run_negotiation(self) -> Dict[str, any]:
        """Executes the negotiation loop until resolution or deadline."""
        print(f"=== Starting Negotiation Session [{self.session_id}] ===")
        current_round = 1
        active_msg = NegotiationMessage(
            session_id=self.session_id,
            sender_id="SYSTEM",
            round_idx=1,
            performative=Performative.PROPOSE,
            proposal=None,
        )

        while current_round <= self.max_rounds and not self.is_completed:
            for agent_id in self.turn_order:
                agent = self.agents[agent_id]
                response_msg = agent.receive_message(active_msg)

                # Store in tamper-evident ledger
                msg_hash = response_msg.compute_hash()
                self.ledger.append(response_msg)
                print(
                    f"[Round {current_round:02d} | {agent_id}] {response_msg.performative.value} "
                    f"-> Proposal: {response_msg.proposal} (Digest: {msg_hash})"
                )

                if response_msg.performative == Performative.ACCEPT:
                    self.is_completed = True
                    self.final_agreement = response_msg.proposal
                    print(f"\n>>> AGREEMENT REACHED in Round {current_round}!")
                    print(f">>> Final Binding Contract: {self.final_agreement}")
                    return {"status": "AGREEMENT", "rounds": current_round, "contract": self.final_agreement}

                elif response_msg.performative == Performative.TERMINATE:
                    self.is_completed = True
                    print(f"\n>>> IMPASSE in Round {current_round}: Agent {agent_id} walked away.")
                    return {"status": "IMPASSE", "rounds": current_round}

                active_msg = response_msg

            current_round += 1

        print(f"\n>>> IMPASSE: Reached maximum round limit ({self.max_rounds}).")
        return {"status": "TIMEOUT", "rounds": self.max_rounds}


# =====================================================================
# Verification and Demonstration
# =====================================================================
if __name__ == "__main__":
    buyer = BuyerAgent(agent_id="Acme_Corp", max_budget=240.0, target_price=160.0)
    seller = SellerAgent(agent_id="Cloud_Supplies_Ltd", cost_floor=180.0, opening_price=280.0)

    coordinator = NegotiationCoordinator(
        session_id="SESS-B2B-CLOUD",
        buyer=buyer,
        seller=seller,
        max_rounds=8,
    )

    result = coordinator.run_negotiation()
    print(f"\nExecution Summary: {result['status']} after {result['rounds']} rounds.")
    print(f"Total Audit Trail Entries: {len(coordinator.ledger)}")
```

---

## 6. Key Takeaways

1. **Mediated Architecture Protects System Invariants**: A centralized Coordinator prevents race conditions, enforces turn taking, and provides non-repudiable audit logs.
2. **Decoupled Actors Ensure True Privacy**: Buyer and seller agents must execute with strictly isolated memory spaces. Internal reservation thresholds must never be exposed to the coordinator or counterpart.
3. **Cryptographic Digests Guarantee Non-Repudiation**: Hashing every message payload creates an auditable record of bids, offers, and binding acceptances.
