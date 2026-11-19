# Module: Agent Negotiation --- Topic 1/10

# Fundamentals of Agent Negotiation

In traditional software architectures, interactions between systems are deterministic: Client $A$ requests a resource via an API, and Server $B$ returns it if permissions allow, or rejects it if they do not. Pricing is fixed, Service Level Agreements (SLAs) are hardcoded, and task allocations follow rigid rule engines.

However, in distributed multi-agent systems, autonomous agents frequently represent distinct stakeholders (e.g., competing departments, enterprise buyers, cloud service providers, or independent users). These agents operate under **conflicting objectives**, **constrained budgets**, and **incomplete information**:

- A buyer agent wants the lowest price, highest delivery speed, and strictest SLA.
- A seller agent wants maximum profit margin, flexible delivery schedules, and minimized liability.
- Neither agent knows the other party's exact cost structure, bottom line, or private deadlines.

If both agents take a static "take-it-or-leave-it" approach, high-value mutually beneficial agreements fail to materialize. 

**Agent Negotiation** is the science and engineering of enabling autonomous software agents to reach mutually acceptable agreements over scarce resources or contracts through iterative proposals, counterproposals, and concession protocols.

---

## 1. Why Static Prompts and Direct API Calls Fail

Why can't we simply ask an LLM: *"Negotiate the best price for 100 cloud GPU instances with the seller agent"*?

When building production agentic systems without a formal negotiation framework, three critical failures emerge:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FAILURE MODES IN NAIVE AGENT PROMPTING          │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Value Leakage (Over-disclosure):                                    │
│    The LLM accidentally reveals private constraints:                   │
│    "My maximum budget is $5,000, but I'll start by offering $3,500."   │
│    -> Counterpart agent immediately holds out for $5,000.              │
│                                                                        │
│ 2. Unprincipled Concessions (Hallucinated Compromise):                 │
│    Under conversational pressure or polite phrasing, the LLM concedes  │
│    below corporate reservation prices without mathematical rationale.  │
│                                                                        │
│ 3. Infinite Haggling Loops:                                            │
│    Without protocol termination conditions or discount factors, agents │
│    ping-pong tiny incremental concessions endlessly, burning tokens.   │
└────────────────────────────────────────────────────────────────────────┘
```

Automated negotiation requires **structured protocols**, **mathematical preference modeling**, **guarded state machines**, and **strategic concession logic** that sit *outside* or strictly constrain the LLM's generative actions.

---

## 2. Core Concepts and Terminology

Every negotiation problem consists of formal mathematical components:

| Concept | Formal Notation | Definition |
| :--- | :--- | :--- |
| **Negotiators / Agents** | $A = \{a_1, a_2, \dots, a_m\}$ | The autonomous entities representing different principals. |
| **Issues / Attributes** | $I = \{i_1, i_2, \dots, i_n\}$ | The dimensions under negotiation (e.g., Price, Delivery Time, Warranty, SLA Tier). |
| **Issue Domains** | $D_j = [min_j, max_j]$ or $\{v_1, \dots\}$ | The set of possible valid values for issue $i_j$. |
| **Negotiation Space** | $\Omega = D_1 \times D_2 \times \dots \times D_n$ | The universe of all possible complete contracts/outcomes. |
| **Proposal / Offer** | $\mathbf{x} \in \Omega$ | A specific assignment of values across all issues: $\mathbf{x} = (x_1, x_2, \dots, x_n)$. |
| **Reservation Value ($RP$)**| $RP_a$ | The worst outcome agent $a$ will accept before walking away. |
| **BATNA** | Alternative Outcome | Best Alternative to a Negotiated Agreement; sets the reservation threshold. |
| **Utility Function** | $U_a(\mathbf{x}): \Omega \to [0, 1]$ | Mathematical scoring function mapping an offer $\mathbf{x}$ to agent $a$'s satisfaction. |
| **ZOPA** | Zone of Possible Agreement | The overlap between parties' acceptable reservation ranges. |

---

## 3. The Negotiation Lifecycle

A robust automated negotiation system follows five distinct, verifiable phases:

```text
  [ Phase 1: Preparation ]
             │
             ▼
  [ Phase 2: Exploration & Framing ]
             │
             ▼
┌────────────────────────────────────────────────────────┐
│  [ Phase 3: Interaction & Bidding Loop ]               │
│                                                        │
│   Agent A generates proposal x_t                       │
│        │                                               │
│        ▼                                               │
│   Agent B evaluates U_B(x_t)                           │
│        │                                               │
│   ┌────┴─────────────────────────────┐                 │
│   ▼                                  ▼                 │
│ Accept? ──Yes──┐             Generate Counteroffer     │
│   │ No         │                     │                 │
│   ▼            │                     ▼                 │
│ Concede or     │             Agent B proposes x_{t+1}  │
│ Walk Away?     │                     │                 │
│   │            │                     ▼                 │
│   └────────────┼──────────► Update Round / Check Time  │
│                │                                       │
└────────────────┼───────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
[ Phase 4: Agreement ]  [ Phase 4: Impasse (No Deal) ]
        │
        ▼
[ Phase 5: Verification & Contract Settlement ]
```

### Phase 1: Preparation (Private Configuration)
Before exchanging any messages, the agent initializes its private state:
- Loads the principal's requirements, weights, and priorities across all issues.
- Calculates its **Reservation Price ($RP$)** from its **BATNA**.
- Determines its opening anchor and maximum allowable concession slope.

### Phase 2: Exploration & Framing
Agents register with a coordinator or establish a peer-to-peer session:
- Confirm mutual compatibility (e.g., verifying that both speak the same protocol schema).
- Exchange issue scopes without disclosing private values (e.g., "We will negotiate Price, Delivery Days, and SLA Tier").

### Phase 3: Deliberation & Bidding Loop
The iterative offer-counteroffer phase:
- Agents take turns offering concrete proposals $\mathbf{x} \in \Omega$.
- An agent accepts if the counterpart's proposal yields utility exceeding its reservation value and current aspiration level.
- Otherwise, the agent generates a counteroffer or signals an impasse if time or concession limits are exhausted.

### Phase 4: Resolution (Agreement vs. Impasse)
- **Agreement**: An offer is mutually accepted. The final state snapshot is frozen.
- **Impasse / Breakdown**: The round deadline expires, or negative ZOPA makes consensus mathematically impossible. Both agents default to their respective BATNAs.

### Phase 5: Verification & Settlement
- The agreed contract payload is cryptographically validated and persisted.
- Business systems execute downstream workflows (e.g., creating purchase orders, provisioning API keys, or executing smart contracts).

---

## 4. The Principal-Agent Problem in AI

An autonomous negotiating agent acts on behalf of a human user or enterprise principal. This introduces the classical **Principal-Agent Problem**:

```text
┌───────────────────────┐                    ┌───────────────────────┐
│       PRINCIPAL       │                    │    NEGOTIATING AGENT  │
│  (Human / Enterprise) │                    │      (AI System)      │
├───────────────────────┤                    ├───────────────────────┤
│ • Broad business goals│  Delegation &      │ • Executes bidding    │
│ • Private risk bounds │ ─────────────────► │ • Selects concessions │
│ • Fiduciary liability │  Boundaries        │ • Operates fast at scale│
└───────────────────────┘                    └───────────────────────┘
            ▲                                            │
            │          Outcome & Audit Log               │
            └────────────────────────────────────────────┘
```

To maintain alignment and safety, every production negotiating agent must adhere to **Three Invariants of Autonomous Agency**:

1. **Strict Invariant of Bounded Loss**: The agent must possess deterministic software guardrails preventing it from ever committing to an offer below its pre-configured reservation price ($U(\mathbf{x}) < RP$), regardless of LLM reasoning or prompt persuasion.
2. **Value Confidentiality**: The agent must maintain strict separation between private state (budget, internal costs, BATNA) and public communication payloads. Private constraints must never be exposed to external counterparts.
3. **Auditability and Replayability**: Every proposal, counteroffer, concession step, and timestamp must be recorded in an immutable ledger for legal and operational compliance.

---

## 5. Information Structures: Complete vs. Incomplete Knowledge

Negotiation strategies depend fundamentally on what is known to each participant:

```text
                               Negotiation Information
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
        Complete Information                            Incomplete Information
   (Symmetric / Toy Scenarios)                       (Asymmetric / Real World)
  • Both know all utility functions                 • Private utility functions
  • Both know exact BATNAs                          • Hidden reservation prices
  • Trivial game-theoretic solution                 • Uncertainty, bluffing, learning
```

In real-world enterprise agent negotiations, systems operate under **Incomplete Asymmetric Information**:
- Agent $A$ knows its own utility function $U_A(\mathbf{x})$ and reservation price $RP_A$.
- Agent $A$ does **not** know $U_B(\mathbf{x})$ or $RP_B$.
- Agent $A$ can only infer Agent $B$'s preferences through the observed history of bids and concessions.

---

## 6. Implementation: The Negotiation Lifecycle State Machine

Below is a complete, production-grade Python implementation of the core negotiation lifecycle state machine, featuring strict invariant validation, turn management, and trajectory tracking.

```python
"""
fundamentals_negotiation.py
Core state machine and entities for autonomous multi-issue agent negotiation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class NegotiationStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    IN_PROGRESS = "IN_PROGRESS"
    AGREEMENT = "AGREEMENT"
    IMPASSE = "IMPASSE"
    TERMINATED = "TERMINATED"


class ActionType(str, Enum):
    OFFER = "OFFER"
    COUNTEROFFER = "COUNTEROFFER"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    WALK_AWAY = "WALK_AWAY"


@dataclass(frozen=True)
class IssueSpec:
    """Defines the domain boundaries and type for an issue under negotiation."""
    name: str
    min_value: float
    max_value: float
    is_higher_better: bool  # True for seller price; False for buyer price


@dataclass(frozen=True)
class Proposal:
    """An offer containing specific values for all negotiated issues."""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    round_number: int = 0
    issue_values: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def validate(self, issue_specs: Dict[str, IssueSpec]) -> None:
        """Validates that all issues are present and within valid domains."""
        for issue_name, spec in issue_specs.items():
            if issue_name not in self.issue_values:
                raise ValueError(f"Missing required issue: {issue_name}")
            val = self.issue_values[issue_name]
            if not (spec.min_value <= val <= spec.max_value):
                raise ValueError(
                    f"Issue '{issue_name}' value {val} out of bounds "
                    f"[{spec.min_value}, {spec.max_value}]"
                )


@dataclass
class NegotiationEvent:
    """Immutable audit record of an action taken in a negotiation session."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    round_number: int = 0
    actor_id: str = ""
    action: ActionType = ActionType.OFFER
    proposal: Optional[Proposal] = None
    rationale: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class NegotiationSession:
    """
    Manages the lifecycle, turns, invariants, and trajectory of an
    autonomous negotiation between two agents.
    """

    def __init__(
        self,
        session_id: str,
        participant_ids: List[str],
        issue_specs: Dict[str, IssueSpec],
        max_rounds: int = 20,
    ) -> None:
        if len(participant_ids) != 2:
            raise ValueError("Bilateral session requires exactly 2 participants.")
        self.session_id = session_id
        self.participant_ids = participant_ids
        self.issue_specs = issue_specs
        self.max_rounds = max_rounds

        self.status: NegotiationStatus = NegotiationStatus.INITIALIZED
        self.current_round: int = 0
        self.current_turn_index: int = 0
        self.trajectory: List[NegotiationEvent] = []
        self.active_proposal: Optional[Proposal] = None
        self.final_contract: Optional[Proposal] = None

    @property
    def current_agent_id(self) -> str:
        return self.participant_ids[self.current_turn_index]

    def start(self) -> None:
        """Transitions session from INITIALIZED to IN_PROGRESS."""
        if self.status != NegotiationStatus.INITIALIZED:
            raise RuntimeError(f"Cannot start session in status: {self.status}")
        self.status = NegotiationStatus.IN_PROGRESS
        self.current_round = 1
        self.current_turn_index = 0

    def submit_action(
        self,
        agent_id: str,
        action: ActionType,
        proposal: Optional[Proposal] = None,
        rationale: str = "",
    ) -> NegotiationEvent:
        """Executes an action, enforcing turn validity, invariants, and state transitions."""
        if self.status != NegotiationStatus.IN_PROGRESS:
            raise RuntimeError(f"Session is not active (current: {self.status})")

        if agent_id != self.current_agent_id:
            raise PermissionError(
                f"Turn violation: expected {self.current_agent_id}, received {agent_id}"
            )

        if action in (ActionType.OFFER, ActionType.COUNTEROFFER):
            if not proposal:
                raise ValueError("An OFFER or COUNTEROFFER action requires a valid proposal.")
            proposal.validate(self.issue_specs)
            self.active_proposal = proposal

        elif action == ActionType.ACCEPT:
            if not self.active_proposal:
                raise ValueError("Cannot ACCEPT: No active proposal exists to accept.")
            self.status = NegotiationStatus.AGREEMENT
            self.final_contract = self.active_proposal

        elif action == ActionType.WALK_AWAY:
            self.status = NegotiationStatus.IMPASSE

        # Record trajectory event
        event = NegotiationEvent(
            session_id=self.session_id,
            round_number=self.current_round,
            actor_id=agent_id,
            action=action,
            proposal=proposal or self.active_proposal,
            rationale=rationale,
        )
        self.trajectory.append(event)

        # Check deadline termination
        if self.status == NegotiationStatus.IN_PROGRESS:
            self._advance_turn()

        return event

    def _advance_turn(self) -> None:
        """Swaps turn and increments round counter when both agents have acted."""
        self.current_turn_index = 1 - self.current_turn_index
        # If we return to agent 0, a full round has elapsed
        if self.current_turn_index == 0:
            self.current_round += 1
            if self.current_round > self.max_rounds:
                self.status = NegotiationStatus.IMPASSE


# =====================================================================
# Verification and Demonstration
# =====================================================================
if __name__ == "__main__":
    # Define contract issues
    specs = {
        "price_per_unit": IssueSpec(
            name="price_per_unit", min_value=100.0, max_value=500.0, is_higher_better=True
        ),
        "delivery_days": IssueSpec(
            name="delivery_days", min_value=3.0, max_value=30.0, is_higher_better=False
        ),
        "sla_uptime_percent": IssueSpec(
            name="sla_uptime_percent", min_value=99.0, max_value=99.99, is_higher_better=True
        ),
    }

    session = NegotiationSession(
        session_id="SESSION-CORP-2026",
        participant_ids=["buyer_agent_1", "seller_agent_2"],
        issue_specs=specs,
        max_rounds=5,
    )
    session.start()

    # Turn 1: Buyer opens
    p1 = Proposal(
        sender_id="buyer_agent_1",
        round_number=1,
        issue_values={"price_per_unit": 180.0, "delivery_days": 7.0, "sla_uptime_percent": 99.9},
    )
    session.submit_action("buyer_agent_1", ActionType.OFFER, p1, rationale="Opening aggressive anchor")

    # Turn 2: Seller counters
    p2 = Proposal(
        sender_id="seller_agent_2",
        round_number=1,
        issue_values={"price_per_unit": 320.0, "delivery_days": 14.0, "sla_uptime_percent": 99.5},
    )
    session.submit_action("seller_agent_2", ActionType.COUNTEROFFER, p2, rationale="Counter with standard margins")

    # Turn 3: Buyer makes compromise counteroffer
    p3 = Proposal(
        sender_id="buyer_agent_1",
        round_number=2,
        issue_values={"price_per_unit": 240.0, "delivery_days": 10.0, "sla_uptime_percent": 99.9},
    )
    session.submit_action("buyer_agent_1", ActionType.COUNTEROFFER, p3, rationale="Conceding price for SLA")

    # Turn 4: Seller accepts
    session.submit_action("seller_agent_2", ActionType.ACCEPT, rationale="Meets minimum profitability threshold")

    print(f"Negotiation Status: {session.status.value}")
    print(f"Total Events Logged: {len(session.trajectory)}")
    print(f"Agreed Contract: {session.final_contract.issue_values}")
```

---

## 7. Key Takeaways and Architectural Patterns

1. **Protocol Decouples from Reasoner**: The negotiation protocol and state machine must enforce valid turns, bounds, and termination independently of the LLM or heuristic strategy.
2. **Deterministic Guardrails are Mandatory**: Never trust an unconstrained LLM prompt to safeguard enterprise budgets. Invariants must be enforced at the API and state machine boundaries.
3. **Structured Audit Logs are Non-Negotiable**: In enterprise B2B environments, the complete trajectory of proposals, counterproposals, and acceptances must be fully serializable for regulatory compliance and dispute resolution.
