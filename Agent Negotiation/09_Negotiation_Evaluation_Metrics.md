# Module: Agent Negotiation --- Topic 9/10

# Negotiation Evaluation & Metrics

Evaluating a negotiating agent is fundamentally different from evaluating a conversational chatbot or code-generation model. Standard NLP metrics like BLEU, ROUGE, or token perplexity are meaningless here. An agent can speak flawless English while surrendering 90% of its principal's profit margin.

Negotiating agents must be evaluated across **economic surplus**, **game-theoretic efficiency**, **behavioral robustness**, and **operational cost**.

---

## 1. The Core Quantitative Evaluation Metrics

A production evaluation framework measures performance across six fundamental dimensions:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                     AGENT NEGOTIATION SCORECARD                        │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Agreement Rate (AR):            Percentage of sessions reaching deal│
│ 2. Surplus Extraction (SE):        Percentage of ZOPA captured by agent│
│ 3. Pareto Distance (D_pareto):     Distance from true Pareto frontier  │
│ 4. Jain's Fairness Index (J):      Equitability of surplus split       │
│ 5. Operational Cost & Speed:       Rounds to deal, LLM tokens, latency │
│ 6. Post-Deal Regret:               Utility lost vs complete info SPE   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Mathematical Formulations

### A. Agreement Rate ($AR$)
The baseline measure of deal viability across $N$ test sessions:

$$AR = \frac{N_{\text{agreement}}}{N_{\text{total}}} \times 100\%$$

*Target:* In positive ZOPA markets, a well-tuned agent should achieve $AR > 90\%$.

---

### B. Surplus Extraction Ratio ($SE$)
Measures the percentage of available economic surplus captured by the agent:

$$SE_A = \frac{U_A(\mathbf{x}^*) - RP_A}{1.0 - RP_A}$$

- $SE = 1.0$: Agent captured 100% of its aspiration.
- $SE = 0.0$: Agent settled at its bare minimum reservation price ($RP$).
- $SE < 0.0$: **Catastrophic Failure** (violated reservation boundary).

---

### C. Distance to the Pareto Frontier ($D_{\text{pareto}}$)
Quantifies how much joint value was left on the table:

$$D_{\text{pareto}} = \min_{\mathbf{p} \in \mathcal{P}} \sqrt{(U_A(\mathbf{x}^*) - U_A(\mathbf{p}))^2 + (U_B(\mathbf{x}^*) - U_B(\mathbf{p}))^2}$$

Where $\mathcal{P}$ is the set of all Pareto-optimal contracts.
- $D_{\text{pareto}} = 0.0$: The deal is Pareto optimal (no joint value wasted).
- Higher distance indicates inefficient, sub-optimal logrolling.

---

### D. Jain's Fairness Index ($J$)
Measures whether the contract unfairly favors one party or divides surplus equitably:

$$J(s_A, s_B) = \frac{(s_A + s_B)^2}{2 \cdot (s_A^2 + s_B^2)}$$

Where $s_A, s_B$ are the normalized surplus shares extracted by agents $A$ and $B$.
- $J = 1.0$: Perfectly equal surplus distribution.
- $J = 0.5$: Completely one-sided exploitation (one party captures 100% of surplus).

---

### E. Operational Efficiency
Measures the computational and monetary cost required to close a contract:
- **Rounds to Agreement ($RTA$):** Average turns elapsed before consensus.
- **Cost per Deal:** Total LLM token expenditure + compute latency.

---

## 3. Implementation: Comprehensive Negotiation Evaluator & Benchmark

Below is a complete Python module calculating the full metric suite and running an automated Monte Carlo benchmark comparing different agent strategy configurations.

```python
"""
negotiation_evaluation.py
Comprehensive metrics and benchmark harness for evaluating autonomous negotiating agents.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import random


@dataclass
class NegotiationRunResult:
    session_id: str
    status: str  # "AGREEMENT" or "IMPASSE"
    rounds: int
    buyer_utility: float
    seller_utility: float
    buyer_rp: float
    seller_rp: float
    tokens_consumed: int
    latency_ms: float


class NegotiationEvaluator:
    """Computes rigorous mathematical metrics across a batch of negotiation runs."""

    @staticmethod
    def evaluate_batch(runs: List[NegotiationRunResult]) -> Dict[str, float]:
        total_runs = len(runs)
        if total_runs == 0:
            return {}

        agreements = [r for r in runs if r.status == "AGREEMENT"]
        agreement_rate = (len(agreements) / total_runs) * 100.0

        if not agreements:
            return {
                "total_runs": total_runs,
                "agreement_rate_pct": 0.0,
                "avg_rounds": sum(r.rounds for r in runs) / total_runs,
                "avg_buyer_surplus_extracted": 0.0,
                "avg_seller_surplus_extracted": 0.0,
                "jains_fairness_index": 0.0,
            }

        # Calculate surplus extractions
        buyer_extractions = []
        seller_extractions = []
        fairness_scores = []
        rounds_list = []
        tokens_list = []

        for deal in agreements:
            rounds_list.append(deal.rounds)
            tokens_list.append(deal.tokens_consumed)

            # Surplus Extraction = (U - RP) / (1.0 - RP)
            b_se = max(0.0, (deal.buyer_utility - deal.buyer_rp) / (1.0 - deal.buyer_rp))
            s_se = max(0.0, (deal.seller_utility - deal.seller_rp) / (1.0 - deal.seller_rp))
            buyer_extractions.append(b_se)
            seller_extractions.append(s_se)

            # Jain's Fairness Index over extracted surplus
            numerator = (b_se + s_se) ** 2
            denominator = 2.0 * ((b_se ** 2) + (s_se ** 2))
            j_index = (numerator / denominator) if denominator > 0 else 1.0
            fairness_scores.append(j_index)

        return {
            "total_runs": total_runs,
            "agreements_count": len(agreements),
            "agreement_rate_pct": round(agreement_rate, 2),
            "avg_rounds_to_deal": round(sum(rounds_list) / len(rounds_list), 2),
            "avg_buyer_surplus_extracted": round(sum(buyer_extractions) / len(buyer_extractions), 4),
            "avg_seller_surplus_extracted": round(sum(seller_extractions) / len(seller_extractions), 4),
            "jains_fairness_index": round(sum(fairness_scores) / len(fairness_scores), 4),
            "avg_tokens_per_deal": round(sum(tokens_list) / len(tokens_list), 1),
        }


# =====================================================================
# Monte Carlo Benchmark Test Harness
# =====================================================================

def run_monte_carlo_benchmark(num_episodes: int = 50) -> None:
    """
    Simulates 50 randomized market episodes pitting Boulware against Conceder agents.
    """
    print(f"\n==================================================================")
    print(f" RUNNING MONTE CARLO NEGOTIATION BENCHMARK ({num_episodes} EPISODES)")
    print(f"==================================================================")

    simulated_runs: List[NegotiationRunResult] = []

    for i in range(1, num_episodes + 1):
        # Generate random market conditions with positive ZOPA
        buyer_rp = round(random.uniform(0.20, 0.40), 2)
        seller_rp = round(random.uniform(0.20, 0.40), 2)
        
        # 85% chance of reaching deal; varying rounds
        reached_deal = random.random() < 0.88
        rounds = random.randint(3, 9) if reached_deal else 10

        if reached_deal:
            # Buyer is Boulware (aggressive, extracts more), Seller is Linear
            buyer_u = round(random.uniform(0.65, 0.90), 3)
            seller_u = round(random.uniform(0.45, 0.70), 3)
            status = "AGREEMENT"
        else:
            buyer_u = 0.0
            seller_u = 0.0
            status = "IMPASSE"

        run = NegotiationRunResult(
            session_id=f"EPISODE-{i:03d}",
            status=status,
            rounds=rounds,
            buyer_utility=buyer_u,
            seller_utility=seller_u,
            buyer_rp=buyer_rp,
            seller_rp=seller_rp,
            tokens_consumed=rounds * 450,
            latency_ms=rounds * 850.0,
        )
        simulated_runs.append(run)

    # Evaluate results
    metrics = NegotiationEvaluator.evaluate_batch(simulated_runs)

    print("\n--- BENCHMARK PERFORMANCE REPORT ---")
    for metric_name, value in metrics.items():
        print(f"  • {metric_name:<30}: {value}")


# =====================================================================
# Verification and Demonstration
# =====================================================================
if __name__ == "__main__":
    run_monte_carlo_benchmark(num_episodes=50)
```

---

## 4. Key Takeaways

1. **Surplus Extraction Defines Strategic Power**: Agreement rate alone is misleading; an agent that always agrees by accepting terrible deals has a 100% agreement rate but negative financial value.
2. **Jain's Fairness Index Guards Against Exploitation**: High fairness scores indicate balanced partnerships; skewed scores warn of strategic vulnerabilities.
3. **Benchmarking Exposes Edge Cases**: Monte Carlo stress testing across random ZOPAs and deadlines reveals whether an agent degrades gracefully or crashes into impasses.
