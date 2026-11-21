# RAG Evaluation & The RAG Triad 🔥 — Production Engineering Guide

Peter Drucker ka famous quote hai: *"You cannot improve what you cannot measure."*
RAG systems ke context mein ye 100% applicable hai. 

Engineering teams aksar RAG build karti hain, 5 test queries par manual inspection karti hain aur production mein deploy kar deti hain. Phir 2 weeks baad executive complain karta hai:
> *"Bot ne client ko wrong API rate limit bata di jo documentation mein thi hi nahi!"*

Is disaster ko rokne ke liye chahiye **Quantitative RAG Evaluation Harness**. RAG pipeline ko end-to-end black box ki tarah evaluate nahi kiya ja sakta; retrieval aur generation components ko independently measure karna padta hai.

Is standard evaluation paradigm ko kehte hain: **The RAG Triad**.

---

## 1. The RAG Triad: Deconstructing the Pipeline

TruLens aur Ragas research groups dwara establish kiya gaya **RAG Triad** teen fundamental axes par system ko measure karta hai:

```
                            [ User Query ]
                             /          \
                            /            \
       1. Context Relevance/              \ 3. Answer Relevance
                          /                \
                         ▼                  ▼
              [ Retrieved Context ] ───► [ Generated Answer ]
                         2. Groundedness / Faithfulness
```

### The 3 Core Legs:

#### 1. Context Relevance (Retrieval Precision)
- **Question:** Kya retrieved chunks user query se actually relevant hain ya noise/filler pack kar diya?
- **Failure Mode:** Context mein low-relevance chunks pack hone se generator distract ho jata hai (Retrieval Pollution).
- **Target:** $> 0.85$

#### 2. Groundedness / Faithfulness (Anti-Hallucination)
- **Question:** Kya final answer ke saare factual claims strictly retrieved context se infer ho rahe hain?
- **Failure Mode:** LLM ne context ke bahar se apni pre-training memory se fabricate kiya (Hallucination).
- **Target:** $> 0.95$ (Enterprise SLA)

#### 3. Answer Relevance (Completeness & Intent Matching)
- **Question:** Kya final answer ne user ke original question ko directly aur concisely address kiya?
- **Failure Mode:** LLM ne context se accurate facts toh uthaye, par user ke original core question ko evade kar diya (Evasive Response).
- **Target:** $> 0.90$

---

## 2. Deterministic Metrics vs LLM-as-a-Judge

RAG evaluation mein do broad schools of thought hain:

```
┌─────────────────────────────────┬─────────────────────────────────┐
│ Deterministic / Classical       │ LLM-as-a-Judge (Modern SOTA)    │
├─────────────────────────────────┼─────────────────────────────────┤
│ • ROUGE-L, BLEU, METEOR         │ • Ragas, TruLens, DeepEval      │
│ • Exact string overlap          │ • Semantic entailment scoring   │
│ • Precision@K, MRR, NDCG        │ • Claim extraction & validation │
│ • Fast & Free ($0.00 compute)   │ • Correlates with Human Judgment│
│ ❌ Fails on synonyms & paraphrase│ ❌ Slower & consumes tokens     │
└─────────────────────────────────┴─────────────────────────────────┘
```

### Classical Metrics Ka Failure:
Agar user query: *"How do I restart the database container?"*
- Reference Answer: *"Execute `docker restart postgres_db`."*
- Generated Answer: *"Run the command `docker restart postgres_db` in terminal."*
ROUGE score isko penalize kar sakta hai despite semantic perfection!

Isiliye industry standard hai:
1. Retrieval stage ke liye: **Deterministic Recall@K & Context Precision**.
2. Generation & Grounding ke liye: **LLM-as-a-Judge with Chain-of-Thought scoring**.

---

## 3. Mathematical Formulation of the RAG Triad

### A. Context Precision:
Context Precision measure karta hai ki kya relevant chunks top ranks par placed hain ya nahi:

$$\text{Context Precision@K} = \frac{\sum_{k=1}^K (\text{Precision@}k \times v_k)}{\text{Total Relevant Items in Top } K}$$

Where $v_k \in \{0, 1\}$ indicates whether chunk at rank $k$ is relevant.

### B. Faithfulness (Groundedness):
Sentence-level atomic claims extract karke verification:

$$\text{Faithfulness Score} = \frac{|\text{Number of Claims Entailed by Context}|}{|\text{Total Claims in Generated Answer}|}$$

Agar generated answer mein 4 statements hain aur context sirf 3 ko support karta hai:
$$\text{Score} = \frac{3}{4} = 0.75 \quad (\text{Flagged for Hallucination!})$$

### C. Answer Relevance:
Reverse Query Generation technique:
Generated answer se synthetic questions formulate karwaye jaate hain ($Q_{\text{synth}}$), aur original user question ($Q_{\text{orig}}$) ke saath cosine similarity measure hoti hai:

$$\text{Answer Relevance} = \frac{1}{N} \sum_{i=1}^N \cos(E(Q_{\text{orig}}), E(Q_{\text{synth}, i}))$$

---

## 4. Failure Mode Taxonomy

Jab RAG metrics drop hote hain, toh debugging ke liye ye taxonomy follow karo:

```
                   RAG FAILURE ROOT CAUSE TAXONOMY
                   
  Metric Dropped                 Root Cause                       Production Fix
┌──────────────────────────────┬───────────────────────────────┬────────────────────────────────┐
│ Low Context Relevance        │ • Poor chunking boundaries    │ • Semantic chunking            │
│                              │ • Embedding model mismatch    │ • Fine-tune or use Reranker    │
│                              │ • Broad top-k without rerank  │ • Add BGE/Cohere Cross-Encoder │
├──────────────────────────────┼───────────────────────────────┼────────────────────────────────┤
│ Low Faithfulness             │ • High LLM temperature (>0.3) │ • Set temperature = 0.0        │
│ (Hallucination detected)     │ • Permissive system prompt    │ • Enforce strict XML grounding │
│                              │ • Context overflow dilution   │ • Prune context budget         │
├──────────────────────────────┼───────────────────────────────┼────────────────────────────────┤
│ Low Answer Relevance         │ • Evasive prompt instructions │ • Tune system instructions     │
│                              │ • Missing user intent context │ • Add Query Transformation     │
└──────────────────────────────┴───────────────────────────────┴────────────────────────────────┘
```

---

## 5. Complete Production Implementation: `rag_evaluation_harness.py` 💻

Below is an industrial-strength, copy-pasteable evaluation harness that:
1. Implements deterministic **Context Precision** and **Context Hit Rate**.
2. Implements **Faithfulness (Groundedness)** scoring by parsing atomic claims and checking entailment against context.
3. Implements **Answer Relevance** score using semantic embedding alignment.
4. Generates an aggregated diagnostic scorecard identifying exact failure modes.

```python
"""
rag_evaluation_harness.py
Production-grade RAG Evaluation Suite implementing the RAG Triad:
1. Context Precision & Relevance (Retrieval Quality)
2. Faithfulness / Groundedness (Hallucination Detection)
3. Answer Relevance (Query Intent Satisfaction)
Includes diagnostic threshold alert system and complete self-verification runner.
"""

import math
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import numpy as np


@dataclass
class EvaluationSample:
    query: str
    retrieved_contexts: List[str]
    generated_answer: str
    ground_truth_answer: Optional[str] = None


@dataclass
class RAGScorecard:
    context_precision: float
    context_recall: float
    faithfulness: float
    answer_relevance: float
    triad_composite_score: float
    verdict: str
    unsupported_claims: List[str] = field(default_factory=list)


class ProductionRAGEvaluator:
    """
    Evaluates RAG generation and retrieval quality.
    Simulates high-precision claim extraction and semantic entailment judges.
    """
    def __init__(self, embedding_dim: int = 128):
        self.dim = embedding_dim

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _embed(self, text: str) -> np.ndarray:
        """
        Bag-of-Tokens normalized hashing projection.
        Simulates dense semantic space with consistent lexical/concept alignment.
        """
        tokens = self._tokenize(text)
        vec = np.zeros(self.dim, dtype=np.float32)
        if not tokens:
            return vec
        for t in tokens:
            h = abs(hash(t)) % self.dim
            vec[h] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 1e-6 else vec

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        dot = np.dot(a, b)
        return float(np.clip(dot, -1.0, 1.0))

    # =================================================================
    # 1. Context Precision & Relevance
    # =================================================================
    def evaluate_context_relevance(self, query: str, contexts: List[str]) -> Tuple[float, float]:
        """
        Calculates Context Precision@K and Mean Relevance.
        Measures the signal-to-noise ratio in retrieved context blocks.
        """
        if not contexts:
            return 0.0, 0.0

        q_vec = self._embed(query)
        relevant_flags = []

        for ctx in contexts:
            c_vec = self._embed(ctx)
            sim = self._cosine_similarity(q_vec, c_vec)
            # Relevance threshold calibrated on semantic overlap
            is_relevant = sim > 0.12
            relevant_flags.append(is_relevant)

        # Calculate Context Precision@K
        precisions = []
        cumulative_relevant = 0
        for k, is_rel in enumerate(relevant_flags, 1):
            if is_rel:
                cumulative_relevant += 1
                precisions.append(cumulative_relevant / k)

        context_precision = sum(precisions) / len(precisions) if precisions else 0.0
        context_hit_rate = 1.0 if any(relevant_flags) else 0.0

        return round(context_precision, 4), round(context_hit_rate, 4)

    # =================================================================
    # 2. Faithfulness / Groundedness (Hallucination Detector)
    # =================================================================
    def evaluate_faithfulness(self, generated_answer: str, contexts: List[str]) -> Tuple[float, List[str]]:
        """
        Extracts factual statements from generated answer and verifies entailment
        against the retrieved context corpus.
        """
        combined_context = " ".join(contexts).lower()
        
        # Deconstruct answer into atomic claims (sentence splitting)
        raw_sentences = [s.strip() for s in re.split(r"[.!?]\s+", generated_answer) if len(s.strip()) > 5]
        if not raw_sentences:
            return 1.0, []

        entailed_count = 0
        unsupported_claims = []
        stop_words = {"should", "generally", "also", "with", "from", "that", "this", "have", "been"}

        for claim in raw_sentences:
            claim_tokens = [t for t in self._tokenize(claim) if len(t) > 3 and t not in stop_words]
            if not claim_tokens:
                entailed_count += 1
                continue

            # Check support in context using exact or stem/prefix match
            supported_terms = sum(1 for t in claim_tokens if (t in combined_context or t[:4] in combined_context))
            entailment_ratio = supported_terms / len(claim_tokens)

            # Claim is grounded if >= 65% of core entities/predicates exist in context
            if entailment_ratio >= 0.65:
                entailed_count += 1
            else:
                unsupported_claims.append(claim)

        faithfulness_score = entailed_count / len(raw_sentences)
        return round(faithfulness_score, 4), unsupported_claims

    # =================================================================
    # 3. Answer Relevance (Intent Satisfaction)
    # =================================================================
    def evaluate_answer_relevance(self, query: str, generated_answer: str) -> float:
        """
        Computes semantic alignment between user query and generated response.
        Penalizes evasive answers or off-topic responses.
        """
        q_vec = self._embed(query)
        a_vec = self._embed(generated_answer)
        
        raw_sim = self._cosine_similarity(q_vec, a_vec)
        
        # Length multiplier if answer is too terse (< 4 words)
        words = len(generated_answer.split())
        length_multiplier = min(1.0, words / 4.0)
        
        relevance_score = max(0.0, raw_sim * length_multiplier)
        return round(float(relevance_score), 4)

    # =================================================================
    # 4. Master Evaluation Pipeline
    # =================================================================
    def evaluate_sample(self, sample: EvaluationSample) -> RAGScorecard:
        ctx_precision, _ = self.evaluate_context_relevance(sample.query, sample.retrieved_contexts)
        faithfulness, unsupported = self.evaluate_faithfulness(sample.generated_answer, sample.retrieved_contexts)
        ans_relevance = self.evaluate_answer_relevance(sample.query, sample.generated_answer)

        # Composite Harmonic Mean (Triad Score)
        epsilon = 1e-6
        composite = 3.0 / (
            (1.0 / (ctx_precision + epsilon)) +
            (1.0 / (faithfulness + epsilon)) +
            (1.0 / (ans_relevance + epsilon))
        )

        verdict = "PASS"
        if faithfulness < 0.85:
            verdict = "FAIL (Hallucination Detected)"
        elif ctx_precision < 0.30:
            verdict = "WARNING (Noisy Context)"
        elif ans_relevance < 0.15:
            verdict = "FAIL (Low Answer Relevance)"

        return RAGScorecard(
            context_precision=ctx_precision,
            context_recall=1.0 if ctx_precision > 0 else 0.0,
            faithfulness=faithfulness,
            answer_relevance=ans_relevance,
            triad_composite_score=round(composite, 4),
            verdict=verdict,
            unsupported_claims=unsupported
        )


# =====================================================================
# 5. Verification & Demonstration Runner
# =====================================================================
if __name__ == "__main__":
    evaluator = ProductionRAGEvaluator()

    # Case A: High-Quality Grounded RAG Output
    sample_pass = EvaluationSample(
        query="What is the recommended shared_buffers setting in PostgreSQL?",
        retrieved_contexts=[
            "For Linux systems running dedicated PostgreSQL instances, shared_buffers should be set to 25% of total system RAM.",
            "Setting shared_buffers higher than 40% often degrades performance due to double buffering with the Linux page cache."
        ],
        generated_answer="PostgreSQL shared_buffers on Linux should generally be set to 25% of total system RAM. Setting it higher than 40% degrades performance."
    )

    # Case B: Hallucinating Output (Contains fabricated claim)
    sample_hallucination = EvaluationSample(
        query="What is the recommended shared_buffers setting in PostgreSQL?",
        retrieved_contexts=[
            "For Linux systems running dedicated PostgreSQL instances, shared_buffers should be set to 25% of total system RAM."
        ],
        generated_answer="PostgreSQL shared_buffers should be set to 25% of RAM. You should also run Redis on port 6379 to accelerate writes."
    )

    print("=" * 80)
    print("RAG TRIAD EVALUATION REPORT")
    print("=" * 80)

    score_pass = evaluator.evaluate_sample(sample_pass)
    print("\n--- SAMPLE 1: GROUNDED RESPONSE ---")
    print(f"Context Precision:  {score_pass.context_precision}")
    print(f"Faithfulness Score: {score_pass.faithfulness}")
    print(f"Answer Relevance:   {score_pass.answer_relevance}")
    print(f"Composite Triad:    {score_pass.triad_composite_score}")
    print(f"Verdict:            {score_pass.verdict}")

    score_hallucinated = evaluator.evaluate_sample(sample_hallucination)
    print("\n--- SAMPLE 2: HALLUCINATED CLAIMS DETECTED ---")
    print(f"Context Precision:  {score_hallucinated.context_precision}")
    print(f"Faithfulness Score: {score_hallucinated.faithfulness}")
    print(f"Answer Relevance:   {score_hallucinated.answer_relevance}")
    print(f"Composite Triad:    {score_hallucinated.triad_composite_score}")
    print(f"Verdict:            {score_hallucinated.verdict}")
    print(f"Unsupported Claims: {score_hallucinated.unsupported_claims}")

    # Assertions
    assert score_pass.faithfulness == 1.0, "Pass sample must have 100% faithfulness!"
    assert score_hallucinated.faithfulness < 1.0, "Hallucinated claim must lower faithfulness score!"
    assert len(score_hallucinated.unsupported_claims) > 0, "Harness must flag unsupported claim!"
    print("\nALL RAG TRIAD EVALUATION CHECKS PASSED SUCCESSFULLY!")
```

---

## 6. Senior Interview Questions & Answers

### Q1: The RAG Triad ke 3 pillars kya hain aur unme se har ek kiske beech relationship validate karta hai?
**Answer:** The RAG Triad teen primary relationships evaluate karta hai:
1. **Context Relevance:** Validates Query $\rightarrow$ Context (kya retriever ne strictly relevant chunks fetch kiye ya irrelevant noise?).
2. **Groundedness / Faithfulness:** Validates Context $\rightarrow$ Answer (kya generated answer ke saare factual claims retrieved context se entail ho rahe hain ya model hallucinate kar raha hai?).
3. **Answer Relevance:** Validates Query $\rightarrow$ Answer (kya generated response user ke core intent aur question ko directly answer karta hai ya evade kar raha hai?).

### Q2: LLM-as-a-Judge evaluation mein "Self-Consistency / Position Bias" ko kaise mitigate karein?
**Answer:** LLM judges three major biases exhibit karte hain: (a) Egocentric bias (apne hi generated text ko high score dena), (b) Position bias (pehla option hamesha better lagna), aur (c) Verbosity bias (lambe answers ko higher score dena). Mitigation strategies:
1. **Chain-of-Thought (CoT) First:** Judge ko final score output karne se pehle atomic claims extract karne aur step-by-step reasoning likhne par force karo.
2. **Permutation Testing:** Pairwise comparisons mein options ka order swap karke do baar evaluate karo.
3. **Strict Structured Rubric:** Numerical 1-5 scale ki jagah explicit boolean criteria use karo (e.g., `is_claim_supported: bool`).

### Q3: Synthetic test dataset generation (Ragas framework style) kaise kaam karta hai?
**Answer:** Manual evaluation datasets banana expensive aur slow hota hai. Frameworks jaise Ragas raw documentation chunks ko analyze karke synthetic test pairs generate karte hain:
1. Chunk se key entities aur concepts identify kiye jaate hain.
2. LLM prompts se diverse query types formulate karwate hain: specific queries, comparative queries, ambiguous queries, aur reasoning-heavy questions.
3. Ground truth answers context se synthesize hote hain.
Ye production data distribution ke bina bhi cold-start RAG evaluation pipeline enable karta hai.

### Q4: Faithfulness score 1.0 hai lekin user satisfaction 0 hai — iska kya cause ho sakta hai?
**Answer:** Ye classic **Retrieval Failure / Evasive Response** mode hai. Agar retriever ne user question ke irrelevant documents fetch kiye, aur system prompt ne strictly instruction di: *"If not found, say I don't know"*, toh LLM faithfully answer karega: *"I do not possess information to answer this."* Is case mein:
- Faithfulness $= 1.0$ (Zero hallucination ✅).
- Context Relevance $= 0.1$ (Bad retrieval ❌).
- Answer Relevance $= 0.1$ (User intent unsatisfied ❌).
RAG Triad ka importance yahi hai: koi bhi single metric overall system health diagnose nahi kar sakti.

### Q5: Production telemetry mein RAG evaluation pipeline continuous kaise run karein without incurring 2x LLM costs?
**Answer:** Production mein 100% live traffic par full LLM-as-a-Judge chalana financially unsustainable hota hai. Standard practice:
1. **Sampling:** Sirf 1-5% random queries ko async evaluation queue (Kafka / Celery) mein push karo.
2. **Negative Signal Triggering:** Agar user thumbs-down deta hai, text copy karta hai, ya follow-up mein "that's wrong" bolta hai, toh us turn ko 100% priority ke saath evaluation pipeline mein send karo.
3. **Deterministic Fast Filters:** Regex, token overlap, and cosine embedding filters pehle run karo; heavyweight LLM judge sirf anomalous borderline samples par invoke karo.
