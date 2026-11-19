# Module: Agent Negotiation --- Topic 4/10

# Utility Functions & Preference Modeling

An autonomous agent cannot negotiate intelligently without a mathematically rigorous way to evaluate any given proposal. While a human says *"I want high quality, fast shipping, and low price,"* an agent requires a formal **Utility Function** $U(\mathbf{x}) \in [0, 1]$ to compare multi-dimensional trade-offs.

If an agent's utility function is improperly calibrated, the agent will make irrational trades—such as saving $5 on shipping at the cost of a 3-week delivery delay that violates core business commitments.

---

## 1. Multi-Attribute Utility Theory (MAUT)

In real-world contracts, an offer $\mathbf{x}$ consists of $m$ distinct issues: $\mathbf{x} = (x_1, x_2, \dots, x_m)$. Under **Multi-Attribute Utility Theory (MAUT)**, overall satisfaction is modeled as a weighted linear combination of individual issue evaluation functions:

$$U(\mathbf{x}) = \sum_{j=1}^{m} w_j \cdot u_j(x_j)$$

Subject to the normalization constraints:

$$\sum_{j=1}^{m} w_j = 1 \quad \text{and} \quad w_j \ge 0 \quad \forall j$$

Where:
- $w_j$ is the **importance weight** of issue $j$.
- $u_j(x_j) \in [0, 1]$ is the **component utility function** scoring the specific value of issue $j$.

```text
                  Multi-Attribute Utility Composition
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
Price Weight: 0.50          Delivery Weight: 0.30        SLA Weight: 0.20
u_price($180) = 0.80        u_delivery(5d) = 0.90        u_sla(99.9%) = 0.70
      │                            │                            │
      └────────────────────────────┼────────────────────────────┘
                                   ▼
             U(x) = (0.50 * 0.80) + (0.30 * 0.90) + (0.20 * 0.70)
                  = 0.40 + 0.27 + 0.14 = 0.81 (Total Utility)
```

---

## 2. Component Utility Functions $u_j(x_j)$

Issues behave differently depending on their economic characteristics:

### A. Linear Benefits and Costs
Used for straightforward numeric issues:
- **Cost Issue (Lower is Better - e.g., Price for Buyer):**
  $$u_j(x) = \frac{x_{max} - x}{x_{max} - x_{min}}$$
- **Benefit Issue (Higher is Better - e.g., SLA, Warranty):**
  $$u_j(x) = \frac{x - x_{min}}{x_{max} - x_{min}}$$

### B. Non-Linear Diminishing Marginal Utility (Risk Aversion)
In many real systems, moving from 99.0% to 99.9% uptime is valuable, but moving from 99.99% to 99.999% yields diminishing marginal business value relative to its cost. We model this using exponential curves:

$$u_j(x) = \frac{1 - e^{-\lambda \frac{x - x_{min}}{x_{max} - x_{min}}}}{1 - e^{-\lambda}}$$

- $\lambda > 0$: **Risk-averse / Concave** (diminishing returns).
- $\lambda < 0$: **Risk-seeking / Convex** (accelerating returns).

### C. Discrete Categorical & Threshold Utilities
Used for qualitative contract terms (e.g., Payment Terms: `Net-15`, `Net-30`, `Net-60`):
$$u_{payment}(x) = \begin{cases} 1.0 & \text{if } x = \text{"Net-15"} \\ 0.6 & \text{if } x = \text{"Net-30"} \\ 0.0 & \text{if } x = \text{"Net-60"} \end{cases}$$

---

## 3. Multi-Objective Optimization in Deal Spaces

In a bilateral negotiation, both agents have distinct utility functions $U_A(\mathbf{x})$ and $U_B(\mathbf{x})$. The outcome space can be mapped onto a 2D utility plane:

```text
Utility of Agent B (Seller)
1.0 ┬      Pareto Frontier (Non-dominated deals)
    │     ╭────────────────╮
    │    ╭╯    * Deal 1    ╰╮
    │   ╭╯ (NBS: Nash point) ╰╮
    │  ╭╯                      ╰╮
    │  │     • Suboptimal Deal  │
    │  │                        │
    │  │  d (Disagreement Point)│
0.0 ┴──┴────────────────────────┴──────── 1.0
    0.0                               Utility of Agent A (Buyer)
```

### A. Pareto Optimality and the Pareto Frontier
- **Pareto Dominance:** A deal $\mathbf{x}$ dominates $\mathbf{y}$ if both agents prefer $\mathbf{x}$ or are indifferent, and at least one strictly prefers it:
  $$U_A(\mathbf{x}) \ge U_A(\mathbf{y}) \quad \text{and} \quad U_B(\mathbf{x}) \ge U_B(\mathbf{y}) \quad (\text{with at least one strict } >)$$
- **Pareto Frontier:** The set of all deals where no party can be made better off without making the other party worse off. Any deal *inside* the frontier leaves economic value on the table.

### B. The Nash Bargaining Solution (NBS)
John Nash proved in 1950 that under four foundational axioms of fairness (Pareto efficiency, symmetry, invariance to affine transformations, and independence of irrelevant alternatives), the unique optimal agreement point $\mathbf{x}^*$ maximizes the **product of the parties' utility gains** over their disagreement/BATNA points $(d_A, d_B)$:

$$\mathbf{x}^* = \arg\max_{\mathbf{x} \in \Omega} \Big( U_A(\mathbf{x}) - d_A \Big) \cdot \Big( U_B(\mathbf{x}) - d_B \Big)$$

---

## 4. Opponent Preference Modeling (Learning Weights from Concessions)

In incomplete-information negotiations, you do not know the counterpart's weights $\mathbf{w}_B$. However, an agent can infer them during negotiation using the **Principle of Differential Concession**:

> **Rule of Inference:** An agent concedes first and largest on issues that it values the least. Issues on which an agent refuses to concede are its highest-priority weights.

If between rounds $t-1$ and $t$, the counterpart concedes heavily on *Delivery Days* but holds firm on *Price*, our agent infers:
$$w_{B, \text{delivery}} \ll w_{B, \text{price}}$$

This enables our agent to exploit **logrolling**: grant concessions on the counterpart's high-weight issues in exchange for favorable terms on our own high-weight issues.

---

## 5. Implementation: Complete Utility & Preference Modeling Engine

Below is an enterprise-grade Python module providing:
1. Multi-attribute utility computation (linear, exponential, categorical).
2. Pareto dominance analysis and Nash Bargaining Solution finder.
3. An online Bayesian-inspired opponent weight estimator.

```python
"""
utility_and_preferences.py
MAUT utility functions, Pareto frontier evaluation, and opponent weight learning.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple
import math


class IssueType(str, Enum):
    LINEAR_BENEFIT = "LINEAR_BENEFIT"  # Higher is better
    LINEAR_COST = "LINEAR_COST"        # Lower is better
    EXPONENTIAL = "EXPONENTIAL"        # Diminishing returns
    CATEGORICAL = "CATEGORICAL"        # Discrete values


@dataclass
class IssueModel:
    name: str
    issue_type: IssueType
    weight: float
    min_val: float = 0.0
    max_val: float = 1.0
    lambda_param: float = 1.0  # For exponential risk aversion
    categorical_scores: Dict[str, float] = field(default_factory=dict)

    def evaluate(self, val: any) -> float:
        """Evaluates issue value to a normalized score in [0.0, 1.0]."""
        if self.issue_type == IssueType.LINEAR_BENEFIT:
            clamped = max(self.min_val, min(self.max_val, float(val)))
            return (clamped - self.min_val) / (self.max_val - self.min_val)

        elif self.issue_type == IssueType.LINEAR_COST:
            clamped = max(self.min_val, min(self.max_val, float(val)))
            return (self.max_val - clamped) / (self.max_val - self.min_val)

        elif self.issue_type == IssueType.EXPONENTIAL:
            clamped = max(self.min_val, min(self.max_val, float(val)))
            normalized_x = (clamped - self.min_val) / (self.max_val - self.min_val)
            numerator = 1.0 - math.exp(-self.lambda_param * normalized_x)
            denominator = 1.0 - math.exp(-self.lambda_param)
            return numerator / denominator if denominator != 0 else normalized_x

        elif self.issue_type == IssueType.CATEGORICAL:
            return self.categorical_scores.get(str(val), 0.0)

        return 0.0


class MultiAttributeUtilityFunction:
    """
    Computes global multi-attribute utility: U(x) = sum(w_i * u_i(x_i)).
    Enforces normalized weights sum == 1.0.
    """

    def __init__(self, issues: List[IssueModel], reservation_value: float = 0.3) -> None:
        self.issues = {issue.name: issue for issue in issues}
        self.reservation_value = reservation_value
        self._normalize_weights()

    def _normalize_weights(self) -> None:
        total = sum(issue.weight for issue in self.issues.values())
        if total <= 0:
            raise ValueError("Total weight must be positive.")
        for issue in self.issues.values():
            issue.weight = issue.weight / total

    def evaluate(self, proposal: Dict[str, any]) -> float:
        """Calculates total weighted utility score."""
        total_utility = 0.0
        for name, issue in self.issues.items():
            if name not in proposal:
                raise KeyError(f"Proposal missing issue: {name}")
            val = proposal[name]
            component_score = issue.evaluate(val)
            total_utility += issue.weight * component_score
        return round(total_utility, 5)

    def is_acceptable(self, proposal: Dict[str, any]) -> bool:
        """Checks if proposal meets the minimum reservation threshold."""
        return self.evaluate(proposal) >= self.reservation_value


# =====================================================================
# Pareto Frontier and Nash Bargaining Solution (NBS) Calculator
# =====================================================================

def find_pareto_and_nash(
    candidate_deals: List[Dict[str, any]],
    utility_a: MultiAttributeUtilityFunction,
    utility_b: MultiAttributeUtilityFunction,
    batna_a: float = 0.0,
    batna_b: float = 0.0,
) -> Tuple[List[Dict[str, any]], Dict[str, any]]:
    """
    Identifies all Pareto-efficient contracts and the Nash Bargaining Solution.
    """
    scored = []
    for deal in candidate_deals:
        ua = utility_a.evaluate(deal)
        ub = utility_b.evaluate(deal)
        scored.append({"deal": deal, "ua": ua, "ub": ub})

    # 1. Filter Pareto Frontier
    pareto_frontier = []
    for item_i in scored:
        is_dominated = False
        for item_j in scored:
            # item_j dominates item_i if it is >= on both and > on at least one
            if (
                item_j["ua"] >= item_i["ua"]
                and item_j["ub"] >= item_i["ub"]
                and (item_j["ua"] > item_i["ua"] or item_j["ub"] > item_i["ub"])
            ):
                is_dominated = True
                break
        if not is_dominated:
            pareto_frontier.append(item_i)

    # 2. Find Nash Bargaining Solution (Maximize (ua - da) * (ub - db))
    best_nash_product = float("-inf")
    best_deal = None
    for item in pareto_frontier:
        surplus_a = max(0.0, item["ua"] - batna_a)
        surplus_b = max(0.0, item["ub"] - batna_b)
        nash_product = surplus_a * surplus_b
        if nash_product > best_nash_product:
            best_nash_product = nash_product
            best_deal = item

    return pareto_frontier, best_deal


# =====================================================================
# Opponent Preference Learner (Heuristic Weight Estimation)
# =====================================================================

class OpponentWeightEstimator:
    """
    Estimates opponent issue weights by tracking their concession deltas over time.
    Issues with low concession rate are inferred to have high importance.
    """

    def __init__(self, issue_names: List[str]) -> None:
        self.issue_names = issue_names
        self.history: List[Dict[str, float]] = []

    def record_bid(self, bid: Dict[str, float]) -> None:
        self.history.append(bid)

    def estimate_weights(self) -> Dict[str, float]:
        """Calculates normalized inferred weights based on observed resistance."""
        if len(self.history) < 2:
            # Uniform prior
            eq = 1.0 / len(self.issue_names)
            return {name: eq for name in self.issue_names}

        # Calculate total concession delta for each issue
        first_bid = self.history[0]
        latest_bid = self.history[-1]
        concessions = {}

        for name in self.issue_names:
            delta = abs(latest_bid.get(name, 0.0) - first_bid.get(name, 0.0))
            concessions[name] = delta

        total_concession = sum(concessions.values())
        if total_concession == 0:
            eq = 1.0 / len(self.issue_names)
            return {name: eq for name in self.issue_names}

        # Invert: smaller concession implies higher weight
        raw_weights = {}
        for name, delta in concessions.items():
            # Inversion formula: (1 - delta/total)
            raw_weights[name] = 1.0 - (delta / total_concession)

        weight_sum = sum(raw_weights.values())
        return {name: round(w / weight_sum, 4) for name, w in raw_weights.items()}


# =====================================================================
# Verification and Demonstration
# =====================================================================
if __name__ == "__main__":
    # Buyer's Utility Model
    buyer_issues = [
        IssueModel("price", IssueType.LINEAR_COST, weight=0.6, min_val=100.0, max_val=400.0),
        IssueModel("delivery_days", IssueType.LINEAR_COST, weight=0.2, min_val=1.0, max_val=20.0),
        IssueModel("sla_percent", IssueType.EXPONENTIAL, weight=0.2, min_val=99.0, max_val=99.99, lambda_param=2.5),
    ]
    buyer_util = MultiAttributeUtilityFunction(buyer_issues, reservation_value=0.35)

    # Seller's Utility Model
    seller_issues = [
        IssueModel("price", IssueType.LINEAR_BENEFIT, weight=0.4, min_val=100.0, max_val=400.0),
        IssueModel("delivery_days", IssueType.LINEAR_BENEFIT, weight=0.4, min_val=1.0, max_val=20.0), # Seller prefers later delivery
        IssueModel("sla_percent", IssueType.LINEAR_COST, weight=0.2, min_val=99.0, max_val=99.99),     # Lower SLA is easier
    ]
    seller_util = MultiAttributeUtilityFunction(seller_issues, reservation_value=0.30)

    # Candidate deals
    candidates = [
        {"price": 150.0, "delivery_days": 18.0, "sla_percent": 99.5},
        {"price": 200.0, "delivery_days": 10.0, "sla_percent": 99.9},
        {"price": 280.0, "delivery_days": 5.0,  "sla_percent": 99.99},
        {"price": 350.0, "delivery_days": 2.0,  "sla_percent": 99.99},
        {"price": 120.0, "delivery_days": 2.0,  "sla_percent": 99.99}, # Unrealistic / highly asymmetric
    ]

    frontier, nbs = find_pareto_and_nash(candidates, buyer_util, seller_util, batna_a=0.35, batna_b=0.30)

    print("--- Pareto Frontier Deals ---")
    for f in frontier:
        print(f"Deal: {f['deal']} -> U_Buyer: {f['ua']}, U_Seller: {f['ub']}")

    print("\n--- Nash Bargaining Solution (NBS) ---")
    print(f"Optimal Deal: {nbs['deal']}")
    print(f"Payoffs: U_Buyer={nbs['ua']}, U_Seller={nbs['ub']}")
```

---

## 6. Key Takeaways

1. **MAUT Prevents Irrational Trade-offs**: Multi-attribute modeling ensures that multi-issue concessions reflect true economic priorities rather than arbitrary heuristics.
2. **Target the Pareto Frontier**: Suboptimal contracts leave joint surplus unharvested. Logrolling enables both agents to simultaneously increase their payoffs.
3. **The Nash Bargaining Solution Maximizes Fair Surplus**: The product $(U_A - d_A)(U_B - d_B)$ is the mathematically optimal benchmark for fair consensus.
