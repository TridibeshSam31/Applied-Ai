# Module: Agent Negotiation --- Topic 3/10

# Offer, Counteroffer & Concession Strategies

In an automated negotiation, the decision-making core is the **Concession Strategy**. Given the history of past exchanges, the current round $t$, and the remaining time before deadline $T_{max}$, the agent must determine:
1. **Should I accept the counterpart's latest offer?**
2. **If not, what exact concession should I make in my counteroffer?**
3. **Or should I break off negotiations and walk away?**

A strategy that concedes too rapidly surrenders valuable surplus to the counterpart. A strategy that is too rigid risks costly impasses where mutually profitable agreements were fully achievable.

---

## 1. The Strategic Action Space

At round $t$, an agent evaluates the counterpart's latest proposal $\mathbf{x}^B_t$ against its own internal target utility $A_A(t)$ (its current **aspiration level**):

```text
                                Counterpart Offer x_t^B
                                           │
                                           ▼
                               Calculate Utility U_A(x_t^B)
                                           │
                   ┌───────────────────────┴───────────────────────┐
                   ▼                                               ▼
         U_A(x_t^B) >= A_A(t)                            U_A(x_t^B) < A_A(t)
                   │                                               │
                   ▼                                               ▼
              [ ACCEPT ]                              t >= T_max or U_A < RP?
                                                      ┌────────────┴────────────┐
                                                      ▼                         ▼
                                                    [ YES ]                   [ NO ]
                                                      │                         │
                                                      ▼                         ▼
                                                [ WALK AWAY ]           Generate Counteroffer
                                                                         matching target A_A(t+1)
```

### Acceptance Criterion (Faratin Rule)
An agent accepts offer $\mathbf{x}^B_t$ if:

$$U_A(\mathbf{x}^B_t) \ge A_A(t+1) \quad \text{or} \quad U_A(\mathbf{x}^B_t) \ge U_A(\mathbf{x}^A_{t+1})$$

*Intuition:* If what the counterpart is offering right now is equal to or better than what I plan to offer in the very next round, accept immediately to avoid discount penalties and risk of breakdown.

---

## 2. Anchoring Strategies: Opening Offers and First-Mover Advantage

The opening offer sets the psychological and numerical baseline for the entire negotiation.

```text
Aggressive Anchor                     Realistic Anchor                    Insulting Anchor
(Captures high surplus)              (Safe, fast consensus)              (Triggers immediate impasse)
┌─────────────────────────┐          ┌─────────────────────────┐         ┌─────────────────────────┐
│ Offer: $120             │          │ Offer: $180             │         │ Offer: $20              │
│ Target: $200            │          │ Target: $200            │         │ Cost to seller: $150    │
│ Counterpart counters:   │          │ Counterpart counters:   │         │ Result: Counterpart     │
│ $260 -> Settle at $190  │          │ $220 -> Settle at $200  │         │ terminates immediately  │
└─────────────────────────┘          └─────────────────────────┘         └─────────────────────────┘
```

### Strategic Rules for Anchoring
1. **First-Mover Surplus Capture**: In the absence of complete information, making the first offer anchors the counterpart's expectation.
2. **The Credibility Boundary**: An anchor must be defensible within the known domain. If an agent offers an absurdly low price below the counterpart's known operational costs, rational agents will interpret this as bad-faith behavior and terminate immediately.
3. **Counter-Anchoring**: When the counterpart opens with an aggressive anchor, never split the difference. Re-anchor immediately at your own target or demand an alternative package.

---

## 3. Mathematical Concession Curves (Time-Dependent Tactics)

The seminal formulation developed by Faratin, Sierra, and Jennings (1998) parameterizes an agent's concession curve over normalized time:

$$\alpha(t) = k + (1 - k) \left( \frac{\min(t, T_{max})}{T_{max}} \right)^{\frac{1}{\beta}}$$

Given an initial aspiration $U_{max}$ (typically $1.0$) and a reservation threshold $RP$, the agent's target utility $A(t)$ at round $t$ is:

$$A(t) = U_{max} - \alpha(t) \cdot (U_{max} - RP)$$

The shape parameter **$\beta$** controls the agent's negotiating "personality":

```text
Aspiration A(t)
1.0 ┬──────────────────────────────────────────
    │ ╲                   Boulware (beta = 0.2)
    │  ╲───┈┈┈┈┈┈┈┈┈┈┈                     (Holds firm until deadline)
    │      ╲
    │       ╲             Linear (beta = 1.0)
    │        ╲                             (Constant steady concession)
    │         ╲
    │          ╲          Conceder (beta = 3.0)
RP  │           ╲                          (Concedes immediately)
0.0 ┴────────────┴─────────────────────────────
    0           t                             T_max
```

| Strategy | Parameter Value | Behavior & Dynamics |
| :--- | :--- | :--- |
| **Boulware (Hardheaded)** | $\beta < 1$ (e.g., $0.2$) | Concedes almost nothing during initial rounds. Maintains maximum pressure. Only makes concessions as the deadline $T_{max}$ approaches. |
| **Linear** | $\beta = 1.0$ | Decreases aspiration at a constant, predictable rate: $A(t) = U_{max} - \frac{t}{T_{max}}(U_{max} - RP)$. |
| **Conceder (Accommodating)** | $\beta > 1$ (e.g., $3.0$) | Concedes rapidly in early rounds to reach an agreement as fast as possible; minimizes the risk of impasse at the expense of surplus. |

---

## 4. Behavior-Dependent Tactics (Tit-for-Tat)

While time-dependent tactics only look at the clock, **behavior-dependent tactics** react to the counterpart's concessions.

### Absolute Tit-for-Tat (Reciprocal Concession)
The agent measures the concession made by the counterpart between rounds $t-2$ and $t-1$, and matches that exact concession:

$$C_B(t-1) = U_A(\mathbf{x}^B_{t-1}) - U_A(\mathbf{x}^B_{t-2})$$

$$A_A(t) = A_A(t-1) - \gamma \cdot C_B(t-1)$$

Where $\gamma > 0$ is the reciprocity multiplier:
- If $\gamma = 1.0$: Exact reciprocity.
- If the counterpart refuses to concede ($C_B = 0$), the agent freezes its offers ($A_A(t) = A_A(t-1)$).

---

## 5. Multi-Issue Trade-offs and Logrolling

In multi-issue contracts (e.g., Price + Delivery Days + Warranty), an agent should not concede equally on all issues.

**Logrolling** is the practice of conceding on an issue of low internal importance in exchange for a concession on an issue of high internal importance:

```text
Issue Importance:
Buyer:  Price (High weight = 0.7), Delivery Days (Low weight = 0.3)
Seller: Price (Medium weight = 0.4), Delivery Days (High weight = 0.6 - fast shipping is costly)

Logrolling Deal:
Buyer agrees to slower delivery (20 days instead of 5 days)  --> Costs buyer little utility
In exchange, Seller agrees to low price ($120 instead of $200) --> Saves buyer massive utility
=> Joint Pareto surplus increases! Both agents win!
```

---

## 6. Implementation: Concession Engine and Simulation

Below is a complete Python implementation of time-dependent concession curves ($\beta$-parameterized), Tit-for-Tat strategies, and a simulation engine pitting different strategies against one another.

```python
"""
concession_strategies.py
Mathematical concession curves, behavioral Tit-for-Tat, and strategy simulation.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import math


class StrategyType(str, Enum):
    BOULWARE = "BOULWARE"
    LINEAR = "LINEAR"
    CONCEDER = "CONCEDER"
    TIT_FOR_TAT = "TIT_FOR_TAT"


class ConcessionEngine:
    """
    Computes mathematical target aspiration levels based on time, deadlines,
    and counterpart behavior.
    """

    def __init__(
        self,
        strategy_type: StrategyType,
        reservation_price: float,
        initial_aspiration: float = 1.0,
        max_rounds: int = 20,
        beta: float = 1.0,
        k: float = 0.05,
    ) -> None:
        self.strategy_type = strategy_type
        self.reservation_price = reservation_price
        self.initial_aspiration = initial_aspiration
        self.max_rounds = max_rounds
        self.beta = beta
        self.k = k

        # Adjust beta based on preset strategy names if not custom
        if strategy_type == StrategyType.BOULWARE:
            self.beta = 0.2
        elif strategy_type == StrategyType.LINEAR:
            self.beta = 1.0
        elif strategy_type == StrategyType.CONCEDER:
            self.beta = 3.5

    def compute_aspiration(
        self,
        current_round: int,
        counterpart_concession: float = 0.0,
        previous_aspiration: Optional[float] = None,
    ) -> float:
        """
        Calculates the target utility level A(t) for the upcoming turn.
        Enforces that A(t) never drops below reservation_price.
        """
        if self.strategy_type == StrategyType.TIT_FOR_TAT:
            prev = previous_aspiration if previous_aspiration is not None else self.initial_aspiration
            # Match counterpart concession
            target = prev - max(0.0, counterpart_concession)
            return max(self.reservation_price, min(self.initial_aspiration, target))

        # Time-dependent formula (Faratin et al.)
        t = min(current_round, self.max_rounds)
        normalized_time = t / float(self.max_rounds)
        alpha = self.k + (1.0 - self.k) * math.pow(normalized_time, 1.0 / self.beta)
        alpha = min(1.0, max(0.0, alpha))

        target = self.initial_aspiration - alpha * (self.initial_aspiration - self.reservation_price)
        return max(self.reservation_price, target)


# =====================================================================
# Strategy Simulation Harness
# =====================================================================

@dataclass
class AgentState:
    agent_id: str
    engine: ConcessionEngine
    current_aspiration: float
    history_offers: List[float]


def simulate_bilateral_haggling(
    buyer_strategy: StrategyType,
    seller_strategy: StrategyType,
    buyer_rp: float = 0.3,   # Buyer requires utility >= 0.3
    seller_rp: float = 0.3,  # Seller requires utility >= 0.3
    max_rounds: int = 15,
) -> Dict[str, any]:
    """
    Simulates a bilateral single-issue price negotiation where:
    - Deal price domain is [$100, $500].
    - Buyer utility: (500 - price) / 400
    - Seller utility: (price - 100) / 400
    """
    buyer_engine = ConcessionEngine(buyer_strategy, reservation_price=buyer_rp, max_rounds=max_rounds)
    seller_engine = ConcessionEngine(seller_strategy, reservation_price=seller_rp, max_rounds=max_rounds)

    buyer = AgentState("Buyer", buyer_engine, 1.0, [])
    seller = AgentState("Seller", seller_engine, 1.0, [])

    print(f"\n=======================================================")
    print(f" SIMULATING: {buyer_strategy.value} (Buyer) vs {seller_strategy.value} (Seller)")
    print(f"=======================================================")

    for round_idx in range(1, max_rounds + 1):
        # 1. Buyer computes aspiration and offers price
        buyer.current_aspiration = buyer.engine.compute_aspiration(round_idx)
        # Buyer price: U_b = (500 - p) / 400 => p = 500 - (U_b * 400)
        buyer_price_offer = 500.0 - (buyer.current_aspiration * 400.0)
        buyer.history_offers.append(buyer_price_offer)

        # Check if Buyer accepts Seller's previous offer
        if seller.history_offers:
            seller_last_price = seller.history_offers[-1]
            seller_last_utility_to_buyer = (500.0 - seller_last_price) / 400.0
            if seller_last_utility_to_buyer >= buyer.current_aspiration:
                print(f"[Round {round_idx}] BUYER ACCEPTS Seller's previous offer of ${seller_last_price:.2f}!")
                return {
                    "outcome": "AGREEMENT",
                    "round": round_idx,
                    "agreed_price": seller_last_price,
                    "buyer_utility": seller_last_utility_to_buyer,
                    "seller_utility": (seller_last_price - 100.0) / 400.0,
                }

        # 2. Seller computes aspiration and counters
        seller.current_aspiration = seller.engine.compute_aspiration(round_idx)
        # Seller price: U_s = (p - 100) / 400 => p = 100 + (U_s * 400)
        seller_price_counter = 100.0 + (seller.current_aspiration * 400.0)
        seller.history_offers.append(seller_price_counter)

        # Check if Seller accepts Buyer's current offer
        buyer_utility_to_seller = (buyer_price_offer - 100.0) / 400.0
        if buyer_utility_to_seller >= seller.current_aspiration:
            print(f"[Round {round_idx}] SELLER ACCEPTS Buyer's offer of ${buyer_price_offer:.2f}!")
            return {
                "outcome": "AGREEMENT",
                "round": round_idx,
                "agreed_price": buyer_price_offer,
                "buyer_utility": buyer.current_aspiration,
                "seller_utility": buyer_utility_to_seller,
            }

        print(
            f"Round {round_idx:02d}: Buyer offers ${buyer_price_offer:.2f} (Asp: {buyer.current_aspiration:.2f}) | "
            f"Seller asks ${seller_price_counter:.2f} (Asp: {seller.current_aspiration:.2f})"
        )

    print(f"Negotiation terminated at deadline ({max_rounds} rounds). IMPASSE.")
    return {"outcome": "IMPASSE", "round": max_rounds}


# =====================================================================
# Verification and Demonstration
# =====================================================================
if __name__ == "__main__":
    # Test 1: Boulware (Stubborn) vs Conceder (Accommodating)
    res1 = simulate_bilateral_haggling(StrategyType.BOULWARE, StrategyType.CONCEDER)
    print(f"Result 1: {res1}\n")

    # Test 2: Boulware vs Boulware (Both stubborn -> High risk of impasse or late agreement)
    res2 = simulate_bilateral_haggling(StrategyType.BOULWARE, StrategyType.BOULWARE)
    print(f"Result 2: {res2}\n")

    # Test 3: Linear vs Linear (Steady meeting in the middle)
    res3 = simulate_bilateral_haggling(StrategyType.LINEAR, StrategyType.LINEAR)
    print(f"Result 3: {res3}\n")
```

---

## 7. Key Takeaways

1. **Boulware Traps Conceders**: When a stubborn agent (Boulware) faces an accommodating agent (Conceder), the Boulware agent extracts almost the entire economic surplus.
2. **Mutual Stubbornness Triggers Impasse**: When both agents deploy aggressive Boulware strategies, neither concedes in time, leading to frequent breakdowns unless deadlines are extended.
3. **Acceptance Rule Prevents Value Waste**: Always accept if the counterpart's active offer is equal to or higher than what you plan to offer next turn.
