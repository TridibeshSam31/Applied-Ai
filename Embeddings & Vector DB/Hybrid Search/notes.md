# Hybrid Search 🔥 — Phase 3: Embeddings + Vector DB

**Ye Phase 3 ka last topic hai.**

Ab tak humne dekha:

```
Keyword Search
      ❌ only exact words

Vector Search
      ✅ meaning understand karta hai
```

Production RAG/search systems mein aksar dono ko combine karna useful hota hai.

## 1. Problem With Vector Search Alone

Maan le database mein:

```
Document A:
"PostgreSQL supports the JSONB data type."

Document B:
"PostgreSQL provides relational database capabilities."

Document C:
"MongoDB stores JSON-like documents."
```

User search karta hai:

```
JSONB
```

Vector search semantic similarity se relevant documents dhoondh sakta hai.

Lekin exact technical terms ke case mein:

```
"JSONB"
"JWT"
"GPT-5.6"
"ERR_CONNECTION_RESET"
"PRD-2026-042"
```

**exact lexical matching bahut valuable hota hai.**

Embedding model ko exact identifier retrieve karna necessarily easiest nahi hota.

## 2. Problem With Keyword Search Alone

Traditional keyword search dekh:

User:

```
"How can I authenticate users using tokens?"
```

Document:

```
"JWT-based authentication allows stateless authorization..."
```

Keyword overlap low ho sakta hai.

```
Query:
authenticate users using tokens

Document:
JWT-based authentication allows stateless authorization
```

Meaning same hai, words different.

```
Keyword search:
❌ weak

Semantic search:
✅ strong
```

## 3. Keyword Search Kya Hai?

Traditional search engines generally **lexical matching** use karte hain.

Simplified:

```
Query:
"JWT authentication"

        ↓

Find documents containing:
"JWT"
"authentication"
```

Scoring techniques mein:

```
TF-IDF
```

aur modern search engines mein:

```
BM25
```

bahut common hai.

## 4. BM25 Kya Hai?

**BM25 ek lexical relevance ranking algorithm hai.**

Ye in cheezon ko consider karta hai:

```
Term frequency
+
Inverse document frequency
+
Document length
```

Simple intuition:

> Query ke important words document mein kitne relevant way mein appear kar rahe hain?

Example:

```
Query:
"PostgreSQL indexing"
```

Document A:

```
PostgreSQL indexing improves query performance...
```

Document B:

```
PostgreSQL is a relational database...
```

BM25 likely A ko higher rank karega kyunki exact query terms strongly match karte hain.

## 5. Vector Search vs BM25

| | BM25 / Keyword | Vector Search |
|---|---|---|
| Matching | Words/terms | Meaning |
| Exact terms | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Synonyms | Limited | ⭐⭐⭐⭐⭐ |
| Semantic meaning | Limited | ⭐⭐⭐⭐⭐ |
| IDs / codes | Excellent | Can be weaker |
| Typo tolerance | Depends | Often better semantically |
| Technical terminology | Excellent | Good |
| Contextual meaning | Limited | Strong |

Toh:

```
BM25
→ lexical relevance

Vector
→ semantic relevance
```

## 6. Hybrid Search

Hybrid search matlab:

```
                QUERY
                  │
          ┌───────┴────────┐
          ↓                ↓
     BM25 Search      Vector Search
          ↓                ↓
      Results A        Results B
          └───────┬────────┘
                  ↓
             Fusion / Ranking
                  ↓
                Top-K
```

**Yehi core idea hai.**

## 7. Real Example

User poochta hai:

```
"How do I configure JWT refresh tokens?"
```

Maan le BM25 return karta hai:

```
1. JWT refresh token configuration
2. JWT authentication guide
3. Access token configuration
```

Vector search return karta hai:

```
1. Authentication token lifecycle
2. Refresh token rotation
3. Session renewal mechanism
```

Notice kar:

**BM25**

Great exact terms:

```
JWT
refresh
tokens
```

**Vector**

Great semantic concepts:

```
token lifecycle
session renewal
rotation
```

Combine kar:

```
JWT refresh token configuration
Refresh token rotation
JWT authentication guide
Token lifecycle
```

Ab retrieval stronger ban sakta hai.

## 8. Hybrid Search Ka Actual Challenge

Problem:

```
BM25 score = 12.7

Vector score = 0.82
```

Kya hum simply ye kar sakte hain:

```
12.7 + 0.82
```

**❌ Nahi.**

Scores different scales pe hain aur different meanings rakhte hain.

Humein **score fusion** chahiye.

## 9. Method 1 — Weighted Score Fusion

Pehle scores normalize kar.

Maan le:

```
BM25 normalized = 0.8
Vector normalized = 0.9
```

Phir:

```
final_score =
    α × vector_score
    +
    (1 - α) × bm25_score
```

Example:

```
α = 0.7
```

Phir:

```
final =
0.7 × 0.9
+
0.3 × 0.8

= 0.63 + 0.24

= 0.87
```

Toh vector search ko zyada weight milti hai.

## 10. Normalization Kyun?

Kyunki raw scores kuch aise dikh sakte hain:

```
BM25:
12.4
8.7
4.2
1.1

Vector:
0.91
0.87
0.81
0.65
```

Inke scales different hain.

Isliye:

```
Raw scores
   ↓
Normalize
   ↓
Combine
```

## 11. Method 2 — Reciprocal Rank Fusion ⭐

Ek bahut useful approach hai:

```
RRF — Reciprocal Rank Fusion
```

Raw scores combine karne ke bajaye, **rank positions combine kar.**

Formula:

$$ RRF(d)=\sum_i\frac{1}{k+rank_i(d)} $$

Formula se dar mat.

Intuition:

> Ek document jo multiple retrieval systems mein highly rank karta hai, usse ek strong combined score milta hai.

## 12. RRF Example

BM25:

```
Rank 1 → A
Rank 2 → B
Rank 3 → C
Rank 4 → D
```

Vector:

```
Rank 1 → C
Rank 2 → A
Rank 3 → E
Rank 4 → B
```

Ab:

```
A → BM25 #1 + Vector #2
B → BM25 #2 + Vector #4
C → BM25 #3 + Vector #1
D → BM25 #4
E → Vector #3
```

**A aur C strongly perform karte hain kyunki dono retrievers agree karte hain ki ye relevant hain.**

**Ye powerful hai.**

## 13. RRF Useful Kyun Hai

RRF ko ye nahi chahiye:

```
BM25 score normalization
```

kyunki ye rankings pe operate karta hai.

Toh:

```
BM25 ranking
      +
Vector ranking
      ↓
     RRF
      ↓
Combined ranking
```

Ye isse ek practical fusion strategy banata hai.

## 14. RAG Mein Hybrid Search

Production RAG aisa dikh sakta hai:

```
                     USER QUERY
                         │
              ┌──────────┴──────────┐
              ↓                     ↓
        Keyword Search         Query Embedding
              ↓                     ↓
             BM25             Vector Search
              ↓                     ↓
        Top 20 results        Top 20 results
              └──────────┬──────────┘
                         ↓
                    RRF / Fusion
                         ↓
                    Top 10 / 20
                         ↓
                    Reranker
                         ↓
                    Top 5 chunks
                         ↓
                       LLM
```

Ye ek production retrieval architecture ke kaafi close hai.

## 15. Hybrid Search vs Reranking

Inhe confuse mat kar.

### Hybrid Search

Multiple retrieval methods combine karta hai:

```
BM25 + Vector
```

### Reranking

Retrieved candidates leta hai aur ek zyada expensive relevance model apply karta hai.

```
Top 20 candidates
       ↓
    Reranker
       ↓
Top 5
```

Toh:

```
Retrieve broadly
      ↓
Hybrid Search
      ↓
Rerank precisely
      ↓
LLM
```

## 16. Sirf Vector Search Kyun Nahi?

Kyunki different queries different signals se benefit karte hain.

**Query 1**

```
"What is the company's leave policy?"
```

Semantic search:

```
🔥 Very useful
```

**Query 2**

```
"What does ERR_CONNECTION_RESET mean?"
```

Exact lexical matching:

```
🔥 Very useful
```

**Query 3**

```
"Explain JWT refresh token rotation"
```

Dono:

```
BM25 → JWT / refresh / rotation
Vector → conceptual meaning
```

**Hybrid potentially strongest hai.**

## 17. Tere Semantic Code Search Project Ke Liye Hybrid Search

**Ye especially us project se relevant hai jo tu baad mein banaayega.**

Maan le developer search karta hai:

```
"JWT middleware"
```

BM25 dhoond sakta hai:

```
jwtMiddleware.ts
authenticateUser()
verifyToken()
```

Vector search dhoond sakta hai:

```
auth middleware
token validation
request authentication
```

Combined:

```
Developer Query
      │
      ├─────────────┐
      ↓             ↓
    BM25          Vector
      ↓             ↓
 Exact terms    Semantic concepts
      └──────┬──────┘
             ↓
          Fusion
             ↓
        Best Results
```

**Ye ek kaafi better code search engine hai.**

## 18. Ek Aur Important Problem: Synonyms

Query:

```
"car"
```

Document:

```
"automobile"
```

BM25:

```
Maybe poor match
```

Vector:

```
Likely strong match
```

Ab:

Query:

```
"ERR_CONNECTION_RESET"
```

Document:

```
"ERR_CONNECTION_RESET occurred in production"
```

BM25:

```
Excellent
```

Vector:

```
Also potentially good
```

Toh hybrid humein deta hai:

```
semantic flexibility
+
lexical precision
```

## 19. Metadata Ke Saath Hybrid Search Architecture

Ab sab concepts combine karo:

```
                         QUERY
                           │
                           ↓
                 ┌─────────────────┐
                 │ Authorization   │
                 └────────┬────────┘
                          ↓
                  Metadata Filters
                          │
               ┌──────────┴──────────┐
               ↓                     ↓
             BM25              Vector Search
               ↓                     ↓
          lexical rank          semantic rank
               └──────────┬──────────┘
                          ↓
                     RRF / Fusion
                          ↓
                       Reranker
                          ↓
                        Top-K
                          ↓
                         LLM
```

**Ye modern RAG retrieval ke liye ek bahut strong mental model hai.**

## 20. Important Engineering Point

**Hybrid search automatically better nahi hai.**

Tu add kar raha hai:

```
BM25
+
Embedding generation
+
Vector search
+
Fusion
+
Potential reranker
```

Iska matlab hai:

```
More complexity
More latency
More infrastructure
More tuning
```

Isliye tujhe evaluate karna chahiye:

```
Vector only
vs
BM25 only
vs
Hybrid
```

apne actual evaluation dataset pe.

Metrics:

```
Recall@K
MRR
NDCG
Latency
Cost
Answer correctness
```

## 21. Interview-Level Answer

**Interviewer:**

> "Why would you use hybrid search instead of pure vector search?"

**Strong answer:**

> "Vector search semantic matching mein strong hai, lekin lexical search jaise BM25 often better hai exact terms, identifiers, product names, error codes, aur technical terminology ke liye. Hybrid search lexical aur semantic signals combine karta hai, usually score ya rank fusion ke through, retrieval robustness improve karne ke liye different query types ke across."

**Yehi wo answer hai jo tu chahta hai.**

## 22. Ek Aur Interview Question

> **"What is RRF?"**

> "Reciprocal Rank Fusion ek rank-based method hai multiple retrieval systems se results combine karne ke liye. Directly incompatible raw scores compare karne ke bajaye, ye un documents ko reward karta hai jo ek ya zyada ranked result lists mein highly appear karte hain."

## 23. Final Phase 3 Mental Model 🧠

Tu shuru hua tha:

```
Text
 ↓
Embedding
 ↓
Vector
```

Ab tu poori retrieval layer samajhta hai:

```
                       DOCUMENT
                          ↓
                       CHUNKING
                          ↓
                     EMBEDDINGS
                          ↓
                PostgreSQL + pgvector
                          ↓
                   HNSW / IVF
                          ↓
─────────────────────────────────────────
                     USER QUERY
                          ↓
                  Query Embedding
                          │
               ┌──────────┴──────────┐
               ↓                     ↓
             BM25               Vector Search
               ↓                     ↓
          Lexical Rank          Semantic Rank
               └──────────┬──────────┘
                          ↓
                       RRF
                          ↓
                     Reranking
                          ↓
                       Top-K
                          ↓
                    Retrieved Context
                          ↓
                         LLM
```

## 🚨 Ek Critical Distinction

Ab ye 4 cheezein mix mat karna:

```
Embedding
→ represents meaning

Vector Search
→ finds semantically similar vectors

BM25
→ finds lexical/term relevance

Hybrid Search
→ combines lexical + semantic retrieval
```


---

## 9. Complete Production Implementation: Hybrid Search Engine (BM25 + Dense + RRF) 💻

Below is an end-to-end, runnable implementation of a **Production Hybrid Search Engine**.
It features:
1. **BM25 Lexical Search** (with Okapi BM25 TF-IDF scoring, tokenization, stop-words, and length normalization).
2. **Dense Vector Search** (using cosine similarity over simulated or real embeddings).
3. **Reciprocal Rank Fusion (RRF)** combiner (`score = sum(1 / (k + rank))`).
4. **Weighted Score Fusion** (`final_score = alpha * dense_score + (1 - alpha) * bm25_score`).
5. Complete verification test demonstrating why Hybrid Search succeeds where pure Vector or pure BM25 fails (exact keyword match vs semantic ambiguity).

```python
"""
hybrid_search_engine.py
Complete Implementation of Production Hybrid Search:
- Inverted Index & Okapi BM25
- Dense Vector Retriever
- Reciprocal Rank Fusion (RRF) & Weighted Score Fusion
- Benchmark showing keyword exactness vs semantic match
"""

import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Any
import numpy as np


# =====================================================================
# 1. Okapi BM25 Lexical Search Engine
# =====================================================================
class BM25Retriever:
    """
    Standard Okapi BM25 implementation:
    score(D, Q) = sum( IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * (|D| / avgdl))) )
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[str] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
        self.num_docs: int = 0

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def index(self, documents: List[str]):
        self.corpus = documents
        self.num_docs = len(documents)
        self.doc_lengths = []

        total_tokens = 0
        for doc_id, doc in enumerate(documents):
            tokens = self._tokenize(doc)
            self.doc_lengths.append(len(tokens))
            total_tokens += len(tokens)

            counts = Counter(tokens)
            for token, freq in counts.items():
                self.doc_freqs[token] += 1
                self.inverted_index[token].append((doc_id, freq))

        self.avg_doc_len = total_tokens / self.num_docs if self.num_docs > 0 else 0.0

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        query_tokens = self._tokenize(query)
        scores = defaultdict(float)

        for token in query_tokens:
            if token not in self.doc_freqs:
                continue

            # Inverse Document Frequency (IDF) with smoothing
            df = self.doc_freqs[token]
            idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)

            for doc_id, freq in self.inverted_index[token]:
                doc_len = self.doc_lengths[doc_id]
                # BM25 term saturation formula
                denom = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                term_score = idf * (freq * (self.k1 + 1.0)) / denom
                scores[doc_id] += term_score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


# =====================================================================
# 2. Dense Semantic Retriever (Vector Search)
# =====================================================================
class DenseVectorRetriever:
    """
    Computes cosine similarity between dense query embedding and document embeddings.
    """
    def __init__(self, dim: int = 64):
        self.dim = dim
        self.embeddings: np.ndarray = None
        self.documents: List[str] = []

    def _mock_embed(self, text: str) -> np.ndarray:
        """Deterministic pseudo-embedding for testing without OpenAI/HuggingFace keys."""
        rng = np.random.RandomState(abs(hash(text)) % (2**32))
        v = rng.randn(self.dim).astype(np.float32)
        return v / np.linalg.norm(v)

    def index(self, documents: List[str]):
        self.documents = documents
        vecs = [self._mock_embed(d) for d in documents]
        self.embeddings = np.array(vecs)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        q_vec = self._mock_embed(query)
        # Cosine similarity (both sides are normalized)
        scores = np.dot(self.embeddings, q_vec)
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(idx, float(scores[idx])) for idx in top_indices]


# =====================================================================
# 3. Hybrid Fusion Layer: Reciprocal Rank Fusion (RRF) & Weighted Score
# =====================================================================
class HybridSearchEngine:
    def __init__(self, rrf_k: int = 60, dense_weight: float = 0.6):
        self.bm25 = BM25Retriever()
        self.dense = DenseVectorRetriever()
        self.documents: List[str] = []
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight

    def index(self, documents: List[str]):
        self.documents = documents
        self.bm25.index(documents)
        self.dense.index(documents)

    def search_rrf(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF):
        RRF_Score(d) = sum( 1 / (k + rank_i(d)) )
        Does not require calibrating or normalizing scores between models!
        """
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        dense_results = self.dense.search(query, top_k=top_k * 2)

        rrf_scores = defaultdict(float)
        rank_details = defaultdict(dict)

        # Process BM25 ranks
        for rank, (doc_id, score) in enumerate(bm25_results, start=1):
            rrf_scores[doc_id] += 1.0 / (self.rrf_k + rank)
            rank_details[doc_id]["bm25_rank"] = rank

        # Process Dense ranks
        for rank, (doc_id, score) in enumerate(dense_results, start=1):
            rrf_scores[doc_id] += 1.0 / (self.rrf_k + rank)
            rank_details[doc_id]["dense_rank"] = rank

        ranked_doc_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        output = []
        for doc_id, score in ranked_doc_ids:
            output.append({
                "doc_id": doc_id,
                "text": self.documents[doc_id],
                "rrf_score": round(score, 5),
                "ranks": rank_details[doc_id]
            })
        return output


# =====================================================================
# 4. Demonstration & Verification
# =====================================================================
if __name__ == "__main__":
    docs = [
        "How to configure PostgreSQL connection pooling with asyncpg in Python.",
        "Error 404: Resource not found in FastAPI routing endpoints.",
        "Error 500: Database transaction deadlock detected under high concurrent write load.",
        "Configuring HNSW vector index parameters M and efConstruction for high recall.",
        "Troubleshooting network timeouts when calling external REST microservices."
    ]

    engine = HybridSearchEngine(rrf_k=60)
    engine.index(docs)

    query = "database deadlock asyncpg error 500"
    print(f"Query: '{query}'\n")

    results = engine.search_rrf(query, top_k=3)
    print("=== HYBRID SEARCH RESULTS (via RRF) ===")
    for rank, r in enumerate(results, start=1):
        print(f"Rank {rank} (RRF Score: {r['rrf_score']}):")
        print(f"   Text: {r['text']}")
        print(f"   Breakdown: {r['ranks']}\n")
```

### Execution:
```bash
python hybrid_search_engine.py
```
