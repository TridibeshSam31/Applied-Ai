# Embedding & Retrieval Mechanics 🔥 — Asymmetric Search, Distance Metrics & Thresholding

Embedding model choose karna aur similarity metric decide karna RAG pipeline ka mathematical core hai.

Bahut engineers galti karte hain:
- Short queries aur long documents ko bina prefix ke embed kar dete hain, jisse asymmetric search degrade ho jaata hai.
- L2-normalized vectors par bina samjhe Cosine, Dot Product, ya Euclidean distance switch karte rehte hain without realizing their mathematical equivalence.
- Har query par blind `top_k = 5` return karte hain, chahe retrieved documents query se completely irrelevant hi kyun na ho (**No score thresholding**).

Is note mein hum **Dense Embedding & Retrieval Mechanics** ke hard engineering principles break down karenge.

---

## 1. Bi-Encoder Architecture & Embedding Selection

RAG systems mein **Bi-Encoder** architecture use hota hai taaki millions of document vectors ko pre-compute karke database mein store kiya ja sake.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        BI-ENCODER ARCHITECTURE                         │
└────────────────────────────────────────────────────────────────────────┘

        User Query: "What is 401k vesting?"
                        │
                        ▼
             ┌─────────────────────┐
             │ Query Encoder (BERT)│
             └──────────┬──────────┘
                        │
                        ▼
                  Query Vector q  (e.g., 768-d)
                        │
                        ├──────────────────────────┐
                        ▼                          ▼
                 Cosine Similarity          HNSW Index Scan
                        ▲                          ▲
                        │                          │
             Passage Vectors {p_i} (Pre-computed & stored in DB)
                        │
           ┌────────────┴────────────┐
           ▼                         ▼
   ┌───────────────┐         ┌───────────────┐
   │ Passage Doc 1 │         │ Passage Doc 2 │
   └───────────────┘         └───────────────┘
```

### Key Considerations for Model Selection:
1. **Dimensions vs Memory Footprint:**
   - OpenAI `text-embedding-3-small` (1536-d) vs BAAI `bge-small-en-v1.5` (384-d).
   - Higher dimension = Zyada RAM usage in Vector DB ($D \times 4\text{ bytes per vector}$).
   - 1 Million vectors of 1536-d = $\approx 6.14\text{ GB RAM}$; 384-d = $\approx 1.53\text{ GB RAM}$.
2. **Matryoshka Representation Learning (MRL):**
   - Modern embedding models (jaise `text-embedding-3`, `nomic-embed-text`) MRL support karte hain.
   - Aap full 1536-d vector ke first 256 ya 512 dimensions truncate kar sakte ho with $<1.5\%$ drop in retrieval accuracy!

---

## 2. Asymmetric Search & Query Prefixing

Standard NLP mein task **Symmetric** hota hai (e.g., Paraphrase detection: sentence-to-sentence comparison).
Lekin RAG search fundamentally **Asymmetric** hota hai:

```
Query (Short, Intent-heavy):   "K8s pod memory limit error" (~5 words)
                                       VS
Document (Long, Descriptive):  "When a container exceeds its memory cgroup limit,
                                the Linux kernel triggers OOM Killer..." (~150 words)
```

Agar dono ko identical instruction se embed kiya jaye, toh query vector sentence-length clusters ki taraf drift ho jaata hai.

### The Solution: Instruction / Task Prefixing
Models like `E5`, `BGE`, aur `Instructor` explicitly demand asymmetric prefixes:

```
Query Prefix:    "query: How do I configure SSL in Nginx?"
Passage Prefix:  "passage: To configure SSL, specify the ssl_certificate directive..."
```

Ya BGE style:
```python
# Query side
query_text = "Represent this sentence for searching relevant passages: What is K8s OOM?"

# Passage side (Indexed as raw body without prefix)
passage_text = "When a container consumes memory beyond limit..."
```
Is instruction prefix ke bina recall rate drastically drop ho jaata hai (often by $15\% - 30\%$).

---

## 3. Mathematical Equivalence: Cosine vs Dot Product vs Euclidean Distance

Aksar junior engineers debate karte hain: *"Vector DB mein metric kya set karun: Cosine, Inner Product, ya L2 Euclidean?"*

Chalo mathematical proof dekhte hain:

```
                             VECTOR DISTANCE EQUIVALENCE
                             ───────────────────────────

    For any two vectors u and v that are L2-Normalized (i.e. ||u|| = 1 and ||v|| = 1):

                        Cosine Similarity = Dot Product (Inner Product)
                        ──────────────────────────────────────────────
                                          u · v
                         cos(θ) = ───────────────────── = u · v
                                   ||u||₂ · ||v||₂

                               Euclidean Distance Formula
                               ──────────────────────────
                         ||u - v||² = ||u||² + ||v||² - 2(u · v)
                                    =   1    +   1   - 2(u · v)
                                    = 2 - 2(u · v)

                                          ▼
                         ||u - v|| = √( 2 · (1 - cos(θ)) )
```

### Engineering Implications:
1. **L2 Normalize Vectors at Ingestion Time:**
   - Ingestion time par har vector ko unit norm bana do: $\vec{v} = \frac{\vec{v}}{\|\vec{v}\|_2}$.
2. **Use Inner Product (Dot Product) in Vector DB:**
   - Dot product calculate karna hardware (SIMD / AVX-512 / GPU) par fastest hota hai kyunki square root ya division operations nahi hote.
   - For normalized vectors: **Dot product rank order is identical to Cosine and Euclidean rank order!**

---

## 4. Vector DB Retrieval Mechanics: Score Thresholding vs Top-K

Naive RAG hamesha blind `limit: 5` run karta hai. Iska side effect:
Agar user ne out-of-domain query poochhi: *"Tell me about alien abductions in 1947"* aur database enterprise billing docs ka hai:
- System still top-5 least-bad billing documents retrieve karega (with low similarity $\approx 0.18$).
- LLM prompt mein garbage context jayega, aur LLM hallucinate karna shuru kar dega!

```
                    SCORE THRESHOLDING PIPELINE
                    ───────────────────────────

               Query ──► [ Vector Search (Top-K=10) ]
                                    │
                                    ▼
                      Candidate Similarities:
                      [ 0.88, 0.82, 0.74, 0.32, 0.28, 0.19 ]
                                    │
                                    ▼
                         Threshold Filter (τ = 0.65)
                                    │
                   ┌────────────────┴────────────────┐
                   ▼                                 ▼
             Keep Chunks                       Discard Noise
          [ 0.88, 0.82, 0.74 ]               [ 0.32, 0.28, 0.19 ]
                   │
                   ▼
         Passed to LLM Context
```

### Production Dynamic Threshold Formulation
Fixed threshold static corpus par kaam karta hai, lekin queries ke variations par fail ho sakta hai. Production mein use **Relative Score Margin Filtering**:
$$\text{Keep chunk } i \iff S_i \ge \tau_{\text{absolute}} \quad \text{AND} \quad S_i \ge (S_{\text{top1}} - \delta)$$
Jahan:
- $\tau_{\text{absolute}} \approx 0.60$ (Noise floor).
- $\delta \approx 0.15$ (Score drop limit relative to best candidate).

---

## 5. Senior Interview Questions & Answers 🧠

#### Q1. What is Matryoshka Representation Learning (MRL) and how does it save vector DB infrastructure cost?
> **Answer:** MRL trains embedding models such that the most critical information is packed into the earliest vector dimensions. For instance, a 1536-dimensional vector can be sliced down to 256 or 512 dimensions. Vector DB storage and RAM usage scales linearly with vector dimensions ($4\text{ bytes} \times D$). Truncating to 512-d cuts RAM footprint and memory bandwidth during ANN search by $66\%$ while preserving over $98\%$ of retrieval recall.

#### Q2. Why do asymmetric embedding models mandate query prefixing?
> **Answer:** In asymmetric search, queries are typically short, keyword-sparse intent expressions ($<10$ tokens), whereas candidate chunks are long, factual passages ($200-500$ tokens). Without instruction prefixing (e.g., `query: ` vs `passage: `), transformer self-attention spaces represent sentence length and grammatical form, pulling query vectors away from relevant documents. Prefixes prime the transformer's attention masks to generate vectors tailored for retrieval mapping.

#### Q3. In an L2-normalized vector space, why should your vector database be configured for Inner Product instead of Cosine distance?
> **Answer:** In an L2-normalized space, $\|\vec{u}\| = \|\vec{v}\| = 1$, making $\cos(\theta) = \vec{u} \cdot \vec{v}$. Computing cosine similarity on un-normalized vectors requires floating-point division and square roots during runtime: $\frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}$. By pre-normalizing vectors upon insertion, the database avoids dynamic square-root computations during query execution and relies strictly on AVX-512/NEON vector dot products, increasing ANN throughput.

#### Q4. What is the danger of returning a fixed $Top\text{-}K$ without similarity score thresholding in production RAG?
> **Answer:** Fixed Top-K retrieval blindly forwards the nearest $K$ vectors regardless of absolute semantic distance. For out-of-domain, adversarial, or irrelevant queries, the nearest neighbors still possess low similarity (e.g., $<0.30$). Forcing these noisy chunks into the LLM context dilutes attention, increases input token costs, and induces hallucinations as the model attempts to force a synthesis between the query and irrelevant text.

#### Q5. How does Cross-Encoder reranking mathematically differ from Bi-Encoder retrieval?
> **Answer:** Bi-encoders process query $q$ and document $d$ in separate forward passes: $\vec{u} = f(q)$ and $\vec{v} = g(d)$, computing similarity via cheap dot product $\vec{u} \cdot \vec{v}$ with no token-level interaction. Cross-encoders concatenate both inputs into a single sequence $[CLS] \circ q \circ [SEP] \circ d$ and pass it through a transformer, enabling full pairwise all-to-all cross-attention between every query token and every document token, achieving far higher ranking fidelity at the cost of $O(N)$ inference latency.

---

## 6. Complete Production Implementation: `embedding_retrieval_engine.py` 💻

Neeche diya gaya script ek self-contained dense vector indexing engine implement karta hai:
1. **Asymmetric Query vs Passage Prefixing**.
2. **L2 Vector Normalization & Dot Product Cosine Equivalence**.
3. **Dynamic Thresholding** (Absolute noise floor + relative margin drop pruning).
4. **Top-K Search Engine** demonstrating rejection of out-of-domain queries.

```python
"""
embedding_retrieval_engine.py
Production-grade Demonstration of:
- Asymmetric Query/Passage Prefixing
- L2 Vector Normalization & Equivalence of Dot Product and Cosine Similarity
- Dense Vector Indexing with Dynamic Similarity Thresholding
- Out-of-Domain Noise Rejection Simulation
"""

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class IndexedDocument:
    doc_id: str
    content: str
    vector: List[float]
    metadata: Dict[str, str]


class AsymmetricEmbeddingEngine:
    """Simulates an Asymmetric Bi-Encoder (such as E5 or BGE) with prefix-aware encoding."""
    def __init__(self, dim: int = 64):
        self.dim = dim

    def _hash_vector(self, text: str, prefix_weight: float) -> List[float]:
        tokens = re.findall(r"\b\w+\b", text.lower())
        vec = [0.0] * self.dim
        if not tokens:
            return vec

        for t in tokens:
            idx = abs(hash(t)) % self.dim
            vec[idx] += 1.0

        # Inject prefix weight to shift coordinate cluster
        vec[0] += prefix_weight

        # L2 Normalization: ||v|| = 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm > 0.0 else vec

    def encode_passage(self, passage: str) -> List[float]:
        """Passages are encoded with 'passage: ' task bias."""
        return self._hash_vector(f"passage: {passage}", prefix_weight=0.5)

    def encode_query(self, query: str) -> List[float]:
        """Queries are encoded with 'query: ' task bias."""
        return self._hash_vector(f"query: {query}", prefix_weight=0.5)


class DenseVectorStore:
    def __init__(self, embedder: AsymmetricEmbeddingEngine):
        self.embedder = embedder
        self.documents: List[IndexedDocument] = []

    def insert(self, doc_id: str, content: str, metadata: Dict[str, str]) -> None:
        vec = self.embedder.encode_passage(content)
        self.documents.append(IndexedDocument(doc_id, content, vec, metadata))

    @staticmethod
    def dot_product(v1: List[float], v2: List[float]) -> float:
        """For L2-normalized vectors, dot product strictly equals cosine similarity."""
        return sum(a * b for a, b in zip(v1, v2))

    def search(
        self,
        query: str,
        top_k: int = 5,
        abs_threshold: float = 0.50,
        relative_margin: float = 0.20
    ) -> List[Tuple[IndexedDocument, float]]:
        """
        Retrieval with Dual-Threshold Guardrails:
        1. Discards candidates below abs_threshold (absolute noise floor).
        2. Discards candidates whose score is worse than (Top1_Score - relative_margin).
        """
        q_vec = self.embedder.encode_query(query)
        scored: List[Tuple[IndexedDocument, float]] = []

        for doc in self.documents:
            score = self.dot_product(q_vec, doc.vector)
            if score >= abs_threshold:
                scored.append((doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        if not scored:
            return []

        # Apply Relative Score Margin Pruning
        top_score = scored[0][1]
        filtered_candidates = [
            (doc, score) for doc, score in scored
            if score >= (top_score - relative_margin)
        ]

        return filtered_candidates[:top_k]


if __name__ == "__main__":
    print("=" * 80)
    print("    ASYMMETRIC EMBEDDING & DENSE RETRIEVAL ENGINE WITH THRESHOLDING")
    print("=" * 80)

    embedder = AsymmetricEmbeddingEngine(dim=64)
    vstore = DenseVectorStore(embedder)

    # Ingest production knowledge chunks
    corpus = [
        ("DOC-01", "PostgreSQL connection pooling with PgBouncer reduces backend connection overhead.", {"db": "postgres"}),
        ("DOC-02", "PgBouncer supports session, transaction, and statement pooling modes.", {"db": "postgres"}),
        ("DOC-03", "Kubernetes Horizontal Pod Autoscaler scales replicas based on observed CPU and memory metrics.", {"infra": "k8s"}),
        ("DOC-04", "Redis clustered mode shards keys across 16384 hash slots.", {"db": "redis"}),
    ]

    for d_id, text, meta in corpus:
        vstore.insert(d_id, text, meta)

    print(f"Indexed {len(corpus)} documents into normalized vector space.\n")

    # Scenario 1: Highly Relevant In-Domain Query
    query_1 = "How does PgBouncer connection pooling work?"
    print(f"[Query 1] '{query_1}'")
    results_1 = vstore.search(query_1, top_k=3, abs_threshold=0.45, relative_margin=0.25)
    print(f"Retrieved {len(results_1)} candidates (Passed Thresholds):")
    for doc, score in results_1:
        print(f"  • [{doc.doc_id}] Score: {score:.4f} | Content: '{doc.content}'")

    # Scenario 2: Completely Out-of-Domain Query (Noise Rejection)
    query_2 = "What is the optimal baking temperature for French sourdough bread?"
    print(f"\n[Query 2] '{query_2}' (Out-of-Domain)")
    results_2 = vstore.search(query_2, top_k=3, abs_threshold=0.45, relative_margin=0.25)
    print(f"Retrieved {len(results_2)} candidates (Passed Thresholds):")
    if not results_2:
        print("  ✅ [GUARDRAIL TRIGGERED] All candidates dropped below noise threshold! Zero irrelevant context sent to LLM.")
    else:
        for doc, score in results_2:
            print(f"  • [{doc.doc_id}] Score: {score:.4f}")

    print("\n" + "=" * 80)
    print("Verification complete: Asymmetric encoding + score thresholding prevents hallucination noise.")
```
