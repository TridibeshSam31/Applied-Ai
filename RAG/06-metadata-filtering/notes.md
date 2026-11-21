# Metadata Filtering 🔥 — Pre-Filtering, Post-Filtering, Filter Starvation & Multi-Tenancy

Enterprise RAG mein sirf semantic similarity kaafi nahi hoti.

Maan lo tumhare database mein 10 lakh chunks hain:
- 500,000 chunks from **Company Alpha**
- 500,000 chunks from **Company Beta**

Dono companies ka leave policy format identical hai.
Agar Company Alpha ka ek employee query karta hai: *"What is our parental leave policy?"*
Aur system Company Beta ki policy retrieve karke answer bana deta hai — ye sirf retrieval accuracy issue nahi hai; ye ek **catastrophic multi-tenant security breach** hai!

Deterministic attributes (tenant IDs, user permissions, departments, versions) ko vector search ke saath kaise seamlessly integrate kiya jata hai? Is note mein hum **Metadata Filtering architectures** ko master karenge.

---

## 1. The 3 Paradigms of Metadata Filtering

Jab hum vector similarity aur metadata predicates (`tenant_id == 'alpha' AND department == 'finance'`) ko combine karte hain, toh 3 primary execution patterns hote hain:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        THE 3 METADATA FILTERING STRATEGIES                             │
└────────────────────────────────────────────────────────────────────────────────────────┘

 1. Post-Filtering (Anti-Pattern)    2. Pre-Filtering (Filter First)    3. Single-Stage (Integrated)
 ┌───────────────────────────┐       ┌───────────────────────────┐      ┌───────────────────────────┐
 │ 1. Global ANN Vector Scan │       │ 1. Metadata Predicate     │      │ 1. Filtered Graph Walk    │
 │    Fetch top (K × M)      │       │    Filter (SQL / Bitmap)  │      │    (ACORN / HNSW Payload) │
 │           │               │       │           │               │      │           │               │
 │           ▼               │       │           ▼               │      │           ▼               │
 │ 2. Drop chunks failing    │       │ 2. Vector Search strictly │      │ Node visited only if      │
 │    metadata predicate     │       │    on surviving subset    │      │ predicate == TRUE         │
 └───────────────────────────┘       └───────────────────────────┘      └───────────────────────────┘
   ❌ Filter Starvation Risk           ✅ Zero Starvation                 ⚡ Lowest Latency + Recall
```

### 1. Post-Filtering (Over-Fetch and Prune)
- **Workflow:**
  1. Vector DB se top-$N$ nearest neighbors retrieve karo bina filter dekhe (e.g., $N = 100$).
  2. Un 100 results par Python ya DB mein metadata filter lagao: `doc.tenant == 'alpha'`.
  3. First $K$ surviving results return karo.
- **Why it is an Anti-Pattern:**
  - Agar filter highly selective hai (e.g., filter target sirf $0.1\%$ data match karta hai), toh un top-100 retrieved results mein zero matching documents ho sakte hain!
  - Is failure mode ko **Filter Starvation** kehte hain.

### 2. Pre-Filtering (Predicate First)
- **Workflow:**
  1. Metadata index (B-tree, inverted index, ya boolean bitmap) se matching document IDs ka set fetch karo: $S = \{id \mid \text{tenant} = \text{'alpha'}\}$.
  2. Us subset $S$ ke andar brute-force ya isolated index par vector similarity compute karo.
- **Limitation:**
  - Agar matching set $S$ bada hai ($100,000$ documents), toh unke vectors par brute force scan slow ho jata hai unless har tenant ka isolated sub-index ho.

### 3. Single-Stage Integrated Filtering (Iterative Graph Traversal / ACORN)
- **Workflow (Used by modern engines like Qdrant, Milvus, pgvector HNSW):**
  - Graph traversal (HNSW) ke dauran, jab algorithm neighbor nodes explore karta hai, candidate node ki distance evaluate karne se pehle uska boolean metadata payload check karta hai.
  - Sirf eligible nodes par vector distance calculate hoti hai.
  - Agar graph disconnected ho jaye, fallback bridges dynamically explore kiye jaate hain (ACORN algorithm).

---

## 2. The Filter Starvation Catastrophe: Mathematical Breakdown

Samjho Filter Starvation mathematically kyun trigger hota hai:

```
                            THE FILTER STARVATION DISASTER
                            ──────────────────────────────

 Total Chunks in DB: 1,000,000
 Chunks matching Tenant 'SecretOps': 50 (Selectivity = 50 / 1,000,000 = 0.005%)
 Target Top-K: 5
 Overfetch Factor: 20x (Retrieve Top 100 vectors globally)

                                 Global Vector Space
                     ┌─────────────────────────────────────────┐
                     │ • • • • • • • • • • • • • • • • • • • • │
                     │ • • • • • • █ (SecretOps) • • • • • • • │
                     │ • • • • • • • • • • • • • • • • • • • • │
                     └─────────────────────────────────────────┘
                                          │
                         Global ANN retrieves Top 100 nearest
                                          │
                                          ▼
                      Top 100 Candidates: ALL 100 are Public!
                                          │
                                          ▼
                         Post-Filter Discards All 100 Chunks
                                          │
                                          ▼
                       Returned Results: [] (ZERO MATCHES!)
```

System crash ho jata hai: Database mein relevant document present tha, lekin global vector search ne use top-100 mein nahi laya, isliye post-filter ne empty list return kar di!

---

## 3. Multi-Tenant Data Isolation: Software vs Storage vs Logical

Enterprise SaaS applications mein multi-tenancy enforce karne ke teen primary patterns hote hain:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MULTI-TENANCY ISOLATION PATTERNS                          │
└────────────────────────────────────────────────────────────────────────────────────────┘

 Pattern 1: Hard Physical Isolation       Pattern 2: Collection-Level Isolation
 ┌───────────────────────────────────┐    ┌───────────────────────────────────┐
 │ Separate Vector DB / Instance     │    │ Separate Table / Collection per   │
 │ per Customer                      │    │ Tenant (e.g. `col_tenant_123`)    │
 │ • Max Security                    │    │ • Clean isolation                 │
 │ • Highest Cost & Ops Overhead     │    │ • Connection / Resource limits    │
 └───────────────────────────────────┘    └───────────────────────────────────┘

 Pattern 3: Logical Partitioning (Payload Filter with Row-Level Security)
 ┌───────────────────────────────────────────────────────────────────┐
 │ Single Shared HNSW Index with enforced `tenant_id` metadata tag    │
 │ • Most cost-effective, high vector sharing efficiency             │
 │ • Requires iron-clad query middleware to prevent filter bypass    │
 └───────────────────────────────────────────────────────────────────┘
```

### The Infallible Rule of RAG Authorization
> [!CAUTION]
> **Never rely on the LLM or embeddings for security or access control!**
> "Only answer if the user has role: HR" in the prompt is a critical vulnerability susceptible to prompt injection.
> Access control must be **deterministic, backend-enforced, and mathematically guaranteed** at the storage layer before vectors reach the prompt.

---

## 4. Senior Interview Questions & Answers 🧠

#### Q1. Vector databases mein Filter Starvation kya hota hai aur iska primary solution kya hai?
> **Answer:** Filter Starvation tab hota hai jab post-filtering architecture use ki jaati hai: system globally top-$K$ ya top-$(K \times M)$ nearest vectors retrieve karta hai, lekin high filter selectivity (e.g., $<1\%$ of data matches the predicate) ki wajah se retrieved candidates mein se saare chunks filter predicate fail kar dete hain, resulting in 0 returned results. Solution pre-filtering (filtering before vector search) ya single-stage integrated graph traversal (HNSW search constrained by payload filter bitmaps) use karna hai.

#### Q2. Inverted index metadata filtering vs B-Tree indexing: Vector DBs dono ko kaise use karte hain?
> **Answer:** B-Tree indexing scalar range queries (e.g., `timestamp >= 1700000000` ya `price < 50`) ke liye optimal hoti hai. Inverted index categorical multi-value tags (e.g., `tags CONTAINS 'k8s'`, `allowed_groups = ['eng', 'ops']`) ke liye fast postings list intersection facilitate karta hai. Advanced vector DBs jaise Qdrant ya pgvector payload indices ko Roaring Bitmaps mein compile karte hain, jisse ANN traversal ke dauran $O(1)$ bitwise eligibility checks possible ho jate hain.

#### Q3. Explain how pgvector with PostgreSQL Row-Level Security (RLS) guarantees multi-tenant safety.
> **Answer:** PostgreSQL mein RLS security policies SQL engine level par enforce hoti hain: `CREATE POLICY tenant_isolation ON document_chunks USING (tenant_id = current_setting('app.current_tenant_id'))`. Jab query execute hoti hai, PostgreSQL query optimizer vector distance operator (`<=>`) ko RLS WHERE predicate ke saath compose karta hai. Database connection context ke bahar ka koi bhi chunk vector distance calculate hone se pehle hi filter ho jata hai, eliminating data leaks.

#### Q4. What is the ACORN algorithm in filtered vector search?
> **Answer:** ACORN (Approximate Closest Oriented Neighbor) ek specialized graph indexing algorithm hai jo filtered HNSW search ke dauran graph connectivity preservation problem ko solve karta hai. Standard HNSW mein un-matching nodes ko skip karne par graph traverse path break ho sakta hai. ACORN extra long-range edges construct karta hai between nodes sharing metadata predicates, guaranteeing high recall even under aggressive ($>99\%$) filter selectivity.

#### Q5. Can a prompt-based system prompt replace database metadata filtering for role-based access?
> **Answer:** Absolutely not. Prompt-based instructions (e.g., *"Ignore salary data if user is not manager"*) are non-deterministic and universally vulnerable to adversarial jailbreaking, indirect prompt injections, and context leakage. Security and authorization boundaries must always be enforced non-parametrically at the database retrieval layer via deterministic boolean filters.

---

## 5. Complete Production Implementation: `metadata_filtered_rag.py` 💻

Neeche diya gaya script ek production metadata-filtered retrieval engine implement karta hai:
1. Simulates multi-tenant records with strict `tenant_id`, `department`, and `access_level`.
2. **Post-Filtering Demonstration:** Highlights the Filter Starvation catastrophe when filtering a restricted department.
3. **Pre-Filtering Implementation:** Uses predicate masks first, guaranteeing $100\%$ target recall without starvation.
4. **RBAC Token Verification:** Injects user session claims to isolate sensitive enterprise data.

```python
"""
metadata_filtered_rag.py
Production-grade Demonstration of:
- Pre-Filtering vs Post-Filtering in Vector Stores
- Real-time simulation of the 'Filter Starvation' catastrophe
- Multi-Tenant Isolation and Role-Based Access Control (RBAC)
- Deterministic Authorization Enforcement before Context Augmentation
"""

import math
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DocumentRecord:
    doc_id: str
    tenant_id: str
    department: str
    access_level: int  # 1: Public, 2: Internal, 3: Confidential
    content: str
    embedding: List[float]


class MetadataVectorStore:
    def __init__(self, dim: int = 32):
        self.dim = dim
        self.records: List[DocumentRecord] = []

    def insert(self, record: DocumentRecord) -> None:
        self.records.append(record)

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        return dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

    def matches_predicate(self, record: DocumentRecord, tenant_id: str, dept: str, max_clearance: int) -> bool:
        if record.tenant_id != tenant_id:
            return False
        if record.department != dept:
            return False
        if record.access_level > max_clearance:
            return False
        return True

    # -------------------------------------------------------------
    # 1. Post-Filtering (Anti-Pattern: Vulnerable to Starvation)
    # -------------------------------------------------------------
    def post_filtered_search(
        self,
        query_vec: List[float],
        tenant_id: str,
        dept: str,
        max_clearance: int,
        top_k: int = 5,
        overfetch_factor: int = 10
    ) -> Tuple[List[Tuple[DocumentRecord, float]], int]:
        """
        Step 1: Fetch top (K * overfetch_factor) purely by vector distance.
        Step 2: Discard candidates failing the metadata predicate.
        """
        candidate_count = top_k * overfetch_factor
        # Sort all records globally by vector similarity
        all_scored = [(rec, self.cosine_similarity(query_vec, rec.embedding)) for rec in self.records]
        all_scored.sort(key=lambda x: x[1], reverse=True)
        top_global = all_scored[:candidate_count]

        # Filter
        surviving: List[Tuple[DocumentRecord, float]] = []
        for rec, score in top_global:
            if self.matches_predicate(rec, tenant_id, dept, max_clearance):
                surviving.append((rec, score))
                if len(surviving) == top_k:
                    break

        return surviving, len(top_global)

    # -------------------------------------------------------------
    # 2. Pre-Filtering (Safe: Predicate applied before Vector Search)
    # -------------------------------------------------------------
    def pre_filtered_search(
        self,
        query_vec: List[float],
        tenant_id: str,
        dept: str,
        max_clearance: int,
        top_k: int = 5
    ) -> Tuple[List[Tuple[DocumentRecord, float]], int]:
        """
        Step 1: Identify subset satisfying deterministic security claims.
        Step 2: Perform vector ranking exclusively on qualified candidates.
        """
        eligible_records = [
            rec for rec in self.records
            if self.matches_predicate(rec, tenant_id, dept, max_clearance)
        ]

        if not eligible_records:
            return [], 0

        scored = [(rec, self.cosine_similarity(query_vec, rec.embedding)) for rec in eligible_records]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k], len(eligible_records)


if __name__ == "__main__":
    print("=" * 80)
    print("    METADATA FILTERING & MULTI-TENANT ISOLATION SIMULATOR")
    print("=" * 80)

    store = MetadataVectorStore(dim=16)

    # Populate synthetic dataset:
    # 9,980 general public engineering documents for tenant_alpha
    # 20 highly confidential payroll documents for tenant_alpha (Department: Payroll)
    random.seed(42)

    def random_vec(dim=16, bias=0.0):
        v = [random.gauss(0, 1) + bias for _ in range(dim)]
        norm = math.sqrt(sum(x * x for x in v))
        return [x / norm for x in v]

    print("Generating 5,000 multi-tenant records across departments...")
    for i in range(5000):
        if i < 15:
            # Restricted Payroll records
            store.insert(DocumentRecord(
                doc_id=f"PAYROLL_{i:03d}",
                tenant_id="tenant_alpha",
                department="payroll",
                access_level=3,  # Confidential
                content=f"Confidential executive compensation ledger record #{i}",
                embedding=random_vec(16, bias=0.2)
            ))
        else:
            # Public Engineering records
            store.insert(DocumentRecord(
                doc_id=f"ENG_{i:04d}",
                tenant_id="tenant_alpha" if i % 2 == 0 else "tenant_beta",
                department="engineering",
                access_level=1,  # Public
                content=f"General engineering log item #{i}",
                embedding=random_vec(16, bias=0.5)
            ))

    query_vector = random_vec(16, bias=0.2)
    target_k = 5

    print("\n[Scenario]: User queries restricted 'payroll' records with Confidential clearance.")
    print(f"Goal: Retrieve Top {target_k} chunks matching tenant='tenant_alpha', dept='payroll', clearance=3\n")

    # 1. Run Post-Filtering (Overfetch factor = 10 -> checks top 50 globally)
    t0 = time.perf_counter()
    post_results, evaluated_post = store.post_filtered_search(
        query_vector,
        tenant_id="tenant_alpha",
        dept="payroll",
        max_clearance=3,
        top_k=target_k,
        overfetch_factor=10
    )
    t_post = (time.perf_counter() - t0) * 1000

    print("--- 1. POST-FILTERING (Overfetch: 10x = 50 candidates) ---")
    print(f"Global candidates evaluated : {evaluated_post}")
    print(f"Matching results returned   : {len(post_results)} / {target_k}")
    print(f"Filter Starvation Occurred  : {'🚨 YES! (0 results returned despite matching docs existing!)' if len(post_results) == 0 else 'No'}")
    print(f"Latency                     : {t_post:.3f} ms\n")

    # 2. Run Pre-Filtering (Predicate first)
    t0 = time.perf_counter()
    pre_results, evaluated_pre = store.pre_filtered_search(
        query_vector,
        tenant_id="tenant_alpha",
        dept="payroll",
        max_clearance=3,
        top_k=target_k
    )
    t_pre = (time.perf_counter() - t0) * 1000

    print("--- 2. PRE-FILTERING (Predicate First via Bitmask/Index) ---")
    print(f"Eligible candidate subset   : {evaluated_pre}")
    print(f"Matching results returned   : {len(pre_results)} / {target_k} (Complete Recall Guaranteed)")
    print(f"Latency                     : {t_pre:.3f} ms")
    for rank, (doc, score) in enumerate(pre_results, start=1):
        print(f"  #{rank}: [{doc.doc_id}] Score: {score:.4f} | Dept: {doc.department} | Level: {doc.access_level}")

    print("\n" + "=" * 80)
    print("Conclusion: Pre-filtering or single-stage integrated graph filtering is mandatory for secure enterprise RAG.")
```
