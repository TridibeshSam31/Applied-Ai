# Retrieval Pipeline 🔥 — The 4 Stages, Latency Budgets & Dual Search Mechanics

Production RAG system banana ek simple API call nahi hai. Jab ek enterprise application mein 100,000 concurrent users queries daalte hain, toh agar architecture optimised nahi hai, latency easily 3-5 seconds touch kar jaati hai.

Is note mein hum **Retrieval Pipeline** ke mechanics ko stage-by-stage dissect karenge, production latency budget formulate karenge, aur **Dense vs Sparse** retrieval ke internal working principles samjhenge.

---

## 1. The 4 Fundamental Stages of RAG

Har modern RAG system chaar sequential phases mein operate karta hai:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                               THE 4 STAGES OF PRODUCTION RAG                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘

     Stage 1                  Stage 2                  Stage 3                 Stage 4
 ┌──────────────┐         ┌──────────────┐         ┌──────────────┐        ┌──────────────┐
 │    QUERY     │ ──────► │  RETRIEVAL   │ ──────► │ AUGMENTATION │ ─────► │  GENERATION  │
 └──────────────┘         └──────────────┘         └──────────────┘        └──────────────┘
  • Sanitization           • Dense Embed            • Context Pack          • Token Stream
  • Rewriting / HyDE       • Sparse Tokenizer       • De-duplication        • First Token (TTFT)
  • ACL / Filter Prep      • ANN Vector Scan        • Reranking             • Citation Anchor
  • Intent Routing         • Hybrid Fusion          • Prompt Synthesis      • Guardrail Check
```

### Stage 1: Query Processing & Orchestration
- **User input directly search engine mein fekna anti-pattern hai.**
- **Operations:**
  1. **Sanitization:** Prompt injection markers (`Ignore all previous instructions...`) strip karna.
  2. **Query Expansion / HyDE:** Short ya vague query ko expand karna ya hypothetical document generate karna.
  3. **Security Context Injection:** Logged-in user ke claims (`tenant_id`, `department_id`, `clearance_level`) extract karna for deterministic DB filtering.

### Stage 2: Retrieval (Candidate Search)
- External storage index se relevant top-$K$ candidate chunks fetch karna.
- **Components:**
  - Dense bi-encoder embedding computation.
  - Inverted index / BM25 lexical scan.
  - Approximate Nearest Neighbor (ANN) graph traversal (HNSW / IVF-PQ).
  - Score normalization aur reciprocal rank fusion (RRF).

### Stage 3: Augmentation (Context Engineering)
- Chunks ko directly LLM prompt mein append nahi kiya jaata.
- **Operations:**
  - **De-duplication:** Overlapping chunks ko merge karna to save context space.
  - **Cross-Encoder Reranking:** Top-50 candidates ko heavy compute cross-encoder se re-score karke top-3 or top-5 mein compress karna.
  - **Lost-in-the-Middle Mitigation:** Highest relevance score waale chunks ko prompt ke top aur bottom edges par strategically place karna.
  - **Prompt Templating:** System instructions, grounding boundaries, aur dynamic context tags (`<context>...</context>`) assemble karna.

### Stage 4: Generation (Synthesis & Guardrails)
- Grounded prompt ko LLM inference engine (vLLM, TensorRT-LLM, OpenAI/Anthropic/Gemini API) par dispatch karna.
- **Operations:**
  - Streaming generation for lowest perceived latency.
  - Time-to-First-Token (TTFT) optimization.
  - Real-time hallucination check aur grounded attribution verification.

---

## 2. Production Latency Budget Breakdown

Agar tere RAG endpoint ka SLA **< 1.0 second (P99)** hai, toh latency budget ka ek-ek millisecond strictly accounted for hona chahiye:

```
                       P99 LATENCY BUDGET ALLOCATION (Total: ~850ms)
                       ──────────────────────────────────────────────

 [Gateway / TLS / Auth]           50ms   ███▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
 [Query Rewriting / HyDE (Optional)] 80ms  █████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
 [Embedding Computation]          20ms   █▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
 [Vector DB Search (HNSW)]        15ms   █▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
 [BM25 Sparse Search]             10ms   █▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
 [Cross-Encoder Reranking]        45ms   ███▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
 [Context Construction]            5ms   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
 [LLM Time to First Token (TTFT)] 350ms  █████████████████████▒▒▒▒▒▒▒▒▒▒
 [LLM Generation (150 tokens)]    275ms  █████████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒
```

### Detailed Component Latency Table

| Stage | Operation | Typical P50 | Hard P99 SLA | Bottleneck Cause | Optimization Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ingress** | API Gateway, JWT verification, payload check | 15ms | 50ms | Auth service network hop | Edge proxy caching, local JWT decoding |
| **Embed** | Bi-Encoder forward pass (e.g., BGE-small / text-embed-3) | 12ms | 30ms | GPU kernel launch, tokenization | ONNX Runtime, TensorRT, Batching |
| **Retrieve** | Hybrid search (HNSW index + Inverted BM25 index) | 10ms | 25ms | Disk I/O, lock contention | In-memory graphs, IVF index, sharded partitions |
| **Rerank** | Cross-Encoder re-scoring (Top-50 $\to$ Top-5) | 30ms | 60ms | $O(N \times L)$ cross-attention | Prune $N$ to 20, FlashAttention-2, quantization |
| **Augment** | Context packing, template rendering | 2ms | 5ms | String allocations | Zero-copy templating |
| **LLM TTFT** | Pre-fill attention phase over retrieved prompt | 180ms | 400ms | KV cache pre-fill, concurrency queuing | Prompt caching, speculative decoding |
| **LLM Stream** | Inter-token generation ($150 \text{ tokens} \times 15\text{ms}$) | 150ms | 300ms | Memory bandwidth during decoding | FP8 kv-cache, vLLM continuous batching |

---

## 3. Dense vs Sparse Retrieval: Deep Comparison

Enterprise RAG mein sirf vector search use karna ek classic failure pattern hai. Chalo dono ke internal mechanics compare karte hain:

```
                           DENSE vs SPARSE PARADIGM
                           ────────────────────────

               DENSE RETRIEVAL                         SPARSE RETRIEVAL
             (Semantic Bi-Encoder)                     (Lexical BM25 / SPLADE)
        ┌─────────────────────────────┐           ┌─────────────────────────────┐
        │ Text: "Heart attack symptoms"│          │ Text: "Heart attack symptoms"│
        │             │               │           │             │               │
        │             ▼               │           │             ▼               │
        │ [0.12, -0.45, ..., 0.88]    │           │ {"heart": 3.4, "attack": 2.8│
        │ Fixed Dimension (e.g. 768)  │           │  "symptoms": 1.9}           │
        │ Continuous real values      │           │ High-dimensional (30,000+)  │
        │ All dimensions non-zero     │           │ >99.9% zeros (Sparse)       │
        └──────────────┬──────────────┘           └──────────────┬──────────────┘
                       │                                         │
                       ▼                                         ▼
            Vector Space Neighborhood                  Inverted Index Lookup
         (Captures: "Myocardial Infarction",          (Matches exact IDs, names,
          "cardiac arrest", "chest pain")              error codes: "ERR_404")
```

### Mathematical Formulation of BM25 (Sparse)
BM25 score ek document $D$ aur query $Q$ ke liye calculate hota hai:

$$\text{Score}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

- $f(q_i, D)$: Document $D$ mein token $q_i$ ki frequency.
- $|D|$ aur $\text{avgdl}$: Current doc length aur corpus ki average document length.
- $k_1$ (typically $1.2 - 2.0$): Term frequency saturation parameter.
- $b$ (typically $0.75$): Document length penalization parameter.

### Dense vs Sparse Comparison Matrix

| Property | Dense Retrieval (e.g. BGE, E5, OpenAI) | Sparse Retrieval (BM25, TF-IDF) |
| :--- | :--- | :--- |
| **Representation** | Low-dimensional dense vector ($D \in [384, 1536]$) | High-dimensional sparse bag-of-words ($V \in [30000, 100000]$) |
| **Query Strengths** | Semantic similarity, synonyms, multilingual, fuzzy intent | Exact keyword match, SKU codes, function names, IDs |
| **Failure Mode** | Hallucinates semantic closeness on rare technical terms | Fails when query uses different vocabulary than document |
| **Index Structure** | HNSW, IVF-Flat, ScaNN graph | Inverted Index (Postings list, Skip lists) |
| **Cold Start** | Requires pre-trained transformer model | Zero training required; computes directly on text corpus |

---

## 4. Hybrid Search Fusion: Reciprocal Rank Fusion (RRF)

Don't choose between Dense and Sparse — **use both via Hybrid Fusion**!
Don't mix raw scores directly (Cosine similarity $[0, 1]$ cannot be cleanly summed with unbounded BM25 scores $[0, \infty)$).

Use **Reciprocal Rank Fusion (RRF)**:

$$\text{RRF\_Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

Where:
- $M$: Ranking methods set $\{\text{Dense}, \text{Sparse}\}$
- $r_m(d)$: Document $d$ ki rank under search method $m$ (1-indexed)
- $k$: Smoothing constant (default constant $k = 60$)

---

## 5. Senior Interview Questions & Answers 🧠

#### Q1. RAG pipeline mein Time-to-First-Token (TTFT) kya hota hai aur isko optimize kaise karein?
> **Answer:** TTFT wo time duration hai jo user query send karne se lekar LLM ke pehle generated token ke stream hone tak lagti hai. Isme network hop + embedding generation + vector search + reranking + LLM pre-fill stage (context token evaluation) include hoti hai. Isse optimize karne ke liye: Prompt Caching use karein (static system prompts dobara compute na ho), top-$K$ chunks ko prune karein to lower pre-fill load, aur faster bi-encoders (jaise ONNX-quantized models) employ karein.

#### Q2. Dense vector search exact keyword queries (jaise serial numbers ya bug IDs) par kyun fail hoti hai?
> **Answer:** Dense embeddings continuous latent space mein semantic conceptual distance capture karte hain. Rare tokens (e.g., `CVE-2024-38077` ya `UUID-9f8a`) pre-training data mein infrequent hote hain aur unke embeddings standard technical vocabulary ke paas cluster ho jaate hain. Resultantly, bi-encoder unhe arbitrary semantic neighbors ke saath confuse kar deta hai, jabki sparse inverted index exact character match guarantee karta hai.

#### Q3. Cross-Encoder reranking ko top-1000 candidate retrieval ke liye seedha kyun nahi use karte?
> **Answer:** Cross-encoders query aur candidate document ko ek saath single sequence $[CLS] \circ Query \circ [SEP] \circ Doc$ bana kar all-to-all cross-attention run karte hain ($O(N \cdot L^2)$ complexity). 1000 candidates par cross-attention run karna hundreds of milliseconds ya seconds le lega. Isliye bi-encoders se fast $O(1)$ ANN search se Top-50 candidates filter kiye jaate hain, aur heavy cross-encoder sirf unhi Top-50 par execute hota hai.

#### Q4. Why is Reciprocal Rank Fusion (RRF) preferred over linear score combination in Hybrid RAG?
> **Answer:** Linear score combination ($S = \alpha S_{\text{dense}} + (1-\alpha) S_{\text{sparse}}$) scale mismatch se suffer karti hai kyunki cosine similarity $[0, 1]$ ya $[-1, 1]$ bounded hoti hai jabki BM25 scores unbounded positive real numbers hote hain jo corpus statistics par fluctuate karte hain. RRF raw scores ko discard karke pure ordinal ranks par operate karta hai, making it scale-invariant, robust, and hyperparameter-free.

#### Q5. What is Query Expansion / HyDE, and what latency trade-off does it introduce?
> **Answer:** HyDE (Hypothetical Document Embeddings) zero-shot LLM prompt se pehle ek hypothetical answer chunk generate karwata hai, fir us hypothetical answer ka embedding vector search ke liye use karta hai (hypothetical passage-to-passage search creates better vector symmetry). Trade-off: Isse pipeline mein ek extra LLM call add hoti hai, jo TTFT mein $+150\text{ms}$ to $+300\text{ms}$ latency penalty introduce karti hai.

---

## 6. Complete Production Implementation: `retrieval_pipeline_simulator.py` 💻

Neeche diya gaya script ek production retrieval pipeline simulator hai:
1. Simulates stage-by-stage latencies (Ingress, Embedding, Dense ANN, Sparse BM25, Reranker, Context Construction, LLM TTFT).
2. Performs Hybrid search (Dense Cosine + Sparse BM25) with Reciprocal Rank Fusion (RRF).
3. Demonstrates prompt injection assembly and outputs structured pipeline profiling metrics.

```python
"""
retrieval_pipeline_simulator.py
Production-grade demonstration of:
- The 4-Stage RAG Pipeline: Query -> Retrieval -> Augmentation -> Generation
- Latency profiling across all sub-stages with microsecond precision
- Hybrid Retrieval (Dense Vector + Sparse Lexical BM25)
- Reciprocal Rank Fusion (RRF) for rank-invariant score aggregation
"""

import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass
class Document:
    doc_id: str
    title: str
    body: str


@dataclass
class StageMetrics:
    stage_name: str
    latency_ms: float
    metadata: Dict[str, str] = field(default_factory=dict)


class ToyTokenizer:
    @staticmethod
    def tokenize(text: str) -> List[str]:
        return re.findall(r"\b[a-z0-9_\-]+\b", text.lower())


class SparseBM25Index:
    """Production BM25 Lexical Search Engine Simulator."""
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs: Dict[str, Document] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_len: float = 0.0
        self.inverted_index: Dict[str, Dict[str, int]] = {}  # term -> {doc_id: tf}
        self.idf: Dict[str, float] = {}

    def fit(self, docs: List[Document]) -> None:
        self.docs = {d.doc_id: d for d in docs}
        total_len = 0
        df: Dict[str, int] = Counter()

        for d in docs:
            tokens = ToyTokenizer.tokenize(d.body)
            t_len = len(tokens)
            self.doc_lengths[d.doc_id] = t_len
            total_len += t_len

            term_counts = Counter(tokens)
            for term, count in term_counts.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = {}
                self.inverted_index[term][d.doc_id] = count
                df[term] += 1

        n_docs = len(docs)
        self.avg_doc_len = total_len / max(1, n_docs)

        # Compute Robertson-Spärck Jones IDF
        for term, freq in df.items():
            self.idf[term] = math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        q_tokens = ToyTokenizer.tokenize(query)
        scores: Dict[str, float] = Counter()

        for term in q_tokens:
            if term not in self.inverted_index:
                continue
            term_idf = self.idf[term]
            postings = self.inverted_index[term]

            for doc_id, tf in postings.items():
                d_len = self.doc_lengths[doc_id]
                denom = tf + self.k1 * (1.0 - self.b + self.b * (d_len / self.avg_doc_len))
                num = tf * (self.k1 + 1.0)
                scores[doc_id] += term_idf * (num / denom)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


class DenseSemanticIndex:
    """Production Dense Vector Index Simulator."""
    def __init__(self, dim: int = 64):
        self.dim = dim
        self.docs: Dict[str, Document] = {}
        self.embeddings: Dict[str, List[float]] = {}

    def _embed(self, text: str) -> List[float]:
        # Hash projection with synthetic semantic clustering
        tokens = ToyTokenizer.tokenize(text)
        vec = [0.0] * self.dim
        for t in tokens:
            idx = abs(hash(t)) % self.dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm > 0.0 else vec

    def fit(self, docs: List[Document]) -> None:
        for d in docs:
            self.docs[d.doc_id] = d
            self.embeddings[d.doc_id] = self._embed(d.body)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        q_vec = self._embed(query)
        scores: List[Tuple[str, float]] = []

        for doc_id, vec in self.embeddings.items():
            # Cosine similarity on unit vectors is dot product
            dot = sum(a * b for a, b in zip(q_vec, vec))
            scores.append((doc_id, dot))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class ProductionRAGPipeline:
    def __init__(self, docs: List[Document]):
        self.docs_map = {d.doc_id: d for d in docs}
        self.sparse_engine = SparseBM25Index()
        self.sparse_engine.fit(docs)

        self.dense_engine = DenseSemanticIndex(dim=64)
        self.dense_engine.fit(docs)

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Tuple[str, float]],
        sparse_results: List[Tuple[str, float]],
        rrf_k: int = 60
    ) -> List[Tuple[str, float]]:
        """Combines multiple ranked lists using Reciprocal Rank Fusion."""
        rrf_scores: Dict[str, float] = Counter()

        for rank, (doc_id, _) in enumerate(dense_results, start=1):
            rrf_scores[doc_id] += 1.0 / (rrf_k + rank)

        for rank, (doc_id, _) in enumerate(sparse_results, start=1):
            rrf_scores[doc_id] += 1.0 / (rrf_k + rank)

        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked

    def run_query(self, query: str, top_k: int = 3) -> Tuple[str, List[StageMetrics]]:
        metrics: List[StageMetrics] = []

        # --- STAGE 1: QUERY PROCESSING & SANITIZATION ---
        t0 = time.perf_counter()
        clean_query = query.strip()
        # Simulated prompt injection scrub
        clean_query = re.sub(r"(ignore\s+previous|system\s+override)", "", clean_query, flags=re.I)
        t_query = (time.perf_counter() - t0) * 1000
        metrics.append(StageMetrics("1. Query Sanitization", t_query, {"query_length": str(len(clean_query))}))

        # --- STAGE 2: HYBRID RETRIEVAL (DENSE + SPARSE) ---
        t0 = time.perf_counter()
        dense_candidates = self.dense_engine.search(clean_query, top_k=5)
        sparse_candidates = self.sparse_engine.search(clean_query, top_k=5)
        fused_candidates = self._reciprocal_rank_fusion(dense_candidates, sparse_candidates, rrf_k=60)
        t_retrieval = (time.perf_counter() - t0) * 1000
        metrics.append(StageMetrics(
            "2. Hybrid Retrieval (Dense+BM25+RRF)",
            t_retrieval,
            {"candidates_evaluated": "10", "fused_top": str(len(fused_candidates))}
        ))

        # --- STAGE 3: AUGMENTATION (CONTEXT ASSEMBLY) ---
        t0 = time.perf_counter()
        top_selected = fused_candidates[:top_k]
        context_blocks = []
        for rank, (doc_id, rrf_score) in enumerate(top_selected, start=1):
            doc = self.docs_map[doc_id]
            context_blocks.append(
                f"[Chunk {rank} | ID: {doc_id} | RRF Score: {rrf_score:.4f}]\n"
                f"Title: {doc.title}\nContent: {doc.body}"
            )
        augmented_prompt = (
            "SYSTEM: Answer the query using ONLY the provided verified context.\n"
            "<context>\n" + "\n\n".join(context_blocks) + "\n</context>\n\n"
            f"USER QUERY: {clean_query}\nASSISTANT: "
        )
        t_augment = (time.perf_counter() - t0) * 1000
        metrics.append(StageMetrics("3. Augmentation & Context Engineering", t_augment, {"prompt_tokens": str(len(augmented_prompt.split()))}))

        # --- STAGE 4: GENERATION (SYNTHESIS & TTFT SIMULATION) ---
        t0 = time.perf_counter()
        # Simulated time-to-first-token & generation
        best_doc = self.docs_map[top_selected[0][0]]
        synthetic_llm_response = (
            f"Based on [{best_doc.doc_id}] ({best_doc.title}): {best_doc.body[:140]}..."
        )
        t_gen = (time.perf_counter() - t0) * 1000 + 45.0  # +45ms simulated neural decode
        metrics.append(StageMetrics("4. LLM Generation (Pre-fill + TTFT)", t_gen, {"status": "SUCCESS_STREAMING"}))

        return synthetic_llm_response, metrics


if __name__ == "__main__":
    print("=" * 80)
    print("    PRODUCTION RETRIEVAL PIPELINE SIMULATOR & LATENCY PROFILER")
    print("=" * 80)

    corpus = [
        Document("DOC-K8S-01", "Kubernetes Pod CrashLoopBackOff", "Pod fails with exit code 137 due to OOMKilled memory limit exceeded."),
        Document("DOC-K8S-02", "Kubernetes Ingress Controller", "Nginx ingress controller returns HTTP 504 Gateway Timeout when upstream service is dead."),
        Document("DOC-SEC-99", "OAuth2 Token Expiration Policy", "JWT access tokens expire after 900 seconds. Refresh tokens expire in 30 days."),
        Document("DOC-AWS-42", "AWS DynamoDB Provisioned Throughput", "Exceeding provisioned RCU/WCU causes ProvisionedThroughputExceededException throttling."),
        Document("DOC-BUG-137", "Memory Leak Diagnostic Playbook", "Investigating error code 137: Inspect cgroups memory.max and heap allocation graphs.")
    ]

    pipeline = ProductionRAGPipeline(corpus)
    sample_query = "Why did my pod get error code 137?"

    print(f"\nIncoming Request: '{sample_query}'\n")
    response, latency_report = pipeline.run_query(sample_query, top_k=2)

    total_latency = sum(m.latency_ms for m in latency_report)

    print("STAGE-BY-STAGE LATENCY PROFILING:")
    print("-" * 75)
    for m in latency_report:
        pct = (m.latency_ms / total_latency) * 100.0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"{m.stage_name:<40} | {m.latency_ms:>6.2f} ms | {pct:>5.1f}% | {bar}")

    print("-" * 75)
    print(f"{'TOTAL PIPELINE LATENCY':<40} | {total_latency:>6.2f} ms | 100.0%\n")

    print(f"Synthesized Grounded Response:\n{response}")
    print("=" * 80)
```
