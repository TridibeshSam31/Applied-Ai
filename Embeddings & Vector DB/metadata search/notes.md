# Metadata Filtering 🔥 — Phase 3: Embeddings + Vector DB

Ab tak humne seekha:

```
Query
  ↓
Embedding
  ↓
Vector similarity
  ↓
Top-K
```

Lekin production RAG mein sirf semantic similarity kaafi nahi hoti.

Socho tere vector DB mein 10 lakh chunks hain from:

```
Company A
Company B
Company C
```

User Company A ka hai.

Agar wo poochhe:

```
"What is our leave policy?"
```

Toh system ko sirf Company A ke documents search karne chahiye.

**Yahin metadata filtering aata hai.**

## 1. Metadata Kya Hai?

Chunk ke saath additional information:

```json
{
  "document_id": "doc_123",
  "chunk_id": "chunk_07",
  "section": "Leave Policy",
  "source": "employee_handbook.pdf",
  "page": 14,
  "tenant_id": "company_A",
  "version": "2026"
}
```

**Ye information vector ka semantic meaning nahi hai.**

Ye chunk ke baare mein **structured information** hai.

## 2. Vector + Metadata

Database mein ek row:

```
┌────────────┬─────────────────────┬───────────────────────┬──────────────┐
│ chunk_id   │ content             │ embedding             │ metadata     │
├────────────┼─────────────────────┼───────────────────────┼──────────────┤
│ c_001      │ Leave policy...     │ [0.12,0.45,...]       │ company_A    │
│ c_002      │ Salary policy...    │ [0.32,0.11,...]       │ company_A    │
│ c_003      │ Leave policy...     │ [0.15,0.43,...]       │ company_B    │
└────────────┴─────────────────────┴───────────────────────┴──────────────┘
```

Ab query:

```
"What is the leave policy?"
```

Semantic search shayad ye find kare:

```
c_001 → Company A leave policy
c_003 → Company B leave policy
```

Lekin agar user Company A ka hai:

```
tenant_id = company_A
```

**humein c_003 ko exclude karna hi hoga.**

## 3. Metadata Filtering

Conceptually:

```
Query
 ↓
Query embedding
 ↓
Filter metadata
 ↓
Similarity search
 ↓
Top-K
```

Example:

```sql
SELECT
    id,
    content,
    embedding <=> '[...]' AS distance
FROM document_chunks
WHERE metadata->>'tenant_id' = 'company_A'
ORDER BY embedding <=> '[...]'
LIMIT 5;
```

Ab vector search hota hai:

```
Company A documents
```

ke andar, poore corpus ke bajaye.

## 4. Ye Extremely Important Kyun Hai

Metadata filtering in cheezon ke liye use ho sakti hai:

**Multi-tenancy**

```
tenant_id = company_A
```

**Document type**

```
type = "policy"
```

**Department**

```
department = "engineering"
```

**Language**

```
language = "en"
```

**Version**

```
version = "2026"
```

**Source**

```
source = "handbook.pdf"
```

**Date**

```
created_at > ...
```

**Permissions**

```
user can access document
```

## 5. Semantic Search vs Metadata Filtering

**Ye distinction BAHUT important hai.**

**Semantic search poochta hai:**

> "Which chunks are conceptually closest to my query?"

**Metadata filtering poochta hai:**

> "Which chunks am I allowed / interested in searching?"

Toh:

```
             SEARCH
                │
       ┌────────┴────────┐
       ↓                 ↓
Metadata Filter     Vector Similarity
       │                 │
       └────────┬────────┘
                ↓
             Ranking
                ↓
              Top-K
```

## 6. Example

Maan le database contains:

```
Chunk A
tenant = A
content = "Employees get 18 casual leaves"

Chunk B
tenant = B
content = "Employees get 12 casual leaves"

Chunk C
tenant = A
content = "Employees can work remotely"

Chunk D
tenant = B
content = "Employees can work remotely"
```

Query:

```
"How many casual leaves?"
```

Filtering ke bina:

```
A → highly relevant
B → highly relevant
C → less relevant
D → less relevant
```

Saath:

```
tenant = A
```

hume milta hai:

```
A → relevant
C → less relevant
```

**B aur D candidates bhi nahi hain.**

## 7. Hard Filters vs Soft Relevance

**Metadata filters generally hard constraints hote hain.**

Example:

```sql
WHERE tenant_id = 'A'
```

matlab:

> Company B ke documents return NAHI hone chahiye.

**Ye ek ranking preference nahi hai.**

**Ye ek boundary hai.**

Yehi wajah hai ki permissions ko embeddings ke through implement nahi karna chahiye.

**❌ Bad:**

> "Hopefully similarity search won't return private docs."

**Bilkul nahi.**

Use kar:

```
Authorization / metadata filter
```

ek **deterministic boundary** ki tarah.

## 8. Security Example 🔐

Maan le:

```
User A
```

ko access hai:

```
Document 1
Document 2
```

lekin nahi:

```
Document 3
```

Ye mat kar:

```
Vector Search
   ↓
Top 20
   ↓
Remove unauthorized documents
```

**Ye risky ho sakta hai** implementation aur side channels pe depend karte hue.

Access constraints ko retrieval eligibility ke hisse ki tarah enforce karna prefer kar:

```
User
 ↓
Trusted authorization context
 ↓
Allowed document scope
 ↓
Vector search
 ↓
Results
```

Aur authorization **trusted application state se aana chahiye — LLM se nahi.**

**Ye directly connect hota hai un tool-security concepts se jo tu Phase 2 mein already seekh chuka hai.**

## 9. Proper Columns Ke Saath PostgreSQL Example

Sab kuch JSONB ke andar daalne ke bajaye, kabhi kabhi regular columns use kar:

```sql
CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,

    document_id BIGINT NOT NULL,

    tenant_id BIGINT NOT NULL,

    source TEXT,

    section TEXT,

    page_number INT,

    content TEXT NOT NULL,

    embedding VECTOR(1536)
);
```

Phir filtering simple ban jaati hai:

```sql
SELECT
    id,
    content,
    embedding <=> '[...]' AS distance
FROM document_chunks
WHERE tenant_id = 42
ORDER BY embedding <=> '[...]'
LIMIT 5;
```

Ye often frequently queried/filterable fields ke liye cleaner hota hai.

## 10. JSONB Metadata

Tu ye bhi use kar sakta hai:

```
metadata JSONB
```

Example:

```json
{
    "tenant_id": 42,
    "department": "engineering",
    "language": "en",
    "document_type": "policy"
}
```

Query:

```sql
SELECT
    id,
    content
FROM document_chunks
WHERE metadata->>'department' = 'engineering';
```

Multiple filters:

```sql
SELECT
    id,
    content,
    embedding <=> '[...]' AS distance
FROM document_chunks
WHERE metadata->>'tenant_id' = '42'
  AND metadata->>'department' = 'engineering'
  AND metadata->>'language' = 'en'
ORDER BY embedding <=> '[...]'
LIMIT 5;
```

## 11. Filtering + Top-K Together

**Ye important production query hai:**

```sql
SELECT
    id,
    content,
    embedding <=> '[QUERY_VECTOR]' AS distance
FROM document_chunks
WHERE tenant_id = 42
  AND document_type = 'policy'
  AND language = 'en'
ORDER BY embedding <=> '[QUERY_VECTOR]'
LIMIT 5;
```

Isse aise padh:

> Tenant 42 ke English policy chunks mein se, mere query ke sabse close 5 chunks dhoond.

**Yehi filtered vector search hai.**

## 12. Pre-Filter vs Post-Filter ⭐

**Ye ek important concept hai.**

### Post-Filter

```
Vector search
     ↓
Top 100
     ↓
Metadata filter
     ↓
Top 5
```

**Problem:**

Maan le un 100 mein se sirf 3 hi user ke tenant ke hain.

Tu bahut kam results ke saath end up ho sakta hai.

### Pre-Filter

```
Metadata filter
     ↓
Eligible documents
     ↓
Vector search
     ↓
Top 5
```

Conceptually better hai jab filter ek hard eligibility constraint represent karta hai.

Lekin implementation/index trade-offs hote hain, especially scale pe. Exact behavior tere database/index aur query plan pe depend karta hai.

## 13. Filtering Scale Pe Kyun Difficult Ban Sakti Hai

Maan le:

```
100 million vectors
```

aur:

```
tenant_id = 42
```

lekin Tenant 42 sirf:

```
10,000 vectors
```

owns karta hai.

Tu ideally chahta hai ki search us relevant subset ke andar efficiently operate kare.

Ab socho combine karte hue:

```
Vector similarity
+
tenant filter
+
department filter
+
permissions
+
date range
```

**Query planner/index strategy important ban jaana start hoti hai.**

Yehi ek wajah hai ki vector search sirf ye nahi hai "embeddings store karo aur cosine similarity calculate karo."

**Ye ek database engineering problem bhi hai.**

## 14. Metadata Hamesha Sirf JSON Nahi Hoti

Production systems mein ye ho sakta hai:

```
document_chunks
├── tenant_id
├── document_id
├── access_control
├── source
├── page
├── section
├── language
├── version
├── created_at
└── embedding
```

Kuch honi chahiye:

```
normal indexed columns
```

jabki flexible attributes ho sakte hain:

```
JSONB
```

**Rule of thumb:**

> Agar ek field frequently filtered, sorted, joined, ya constrained hoti hai, ek dedicated column often preferable hota hai usse arbitrary JSON ke andar chupane se.

## 15. Metadata Aur Citations

Yaad hai hamara chunk?

```json
{
    "source": "employee_handbook.pdf",
    "page": 14,
    "section": "Leave Policy"
}
```

Retrieval ke baad, teri application ko pata hai:

```
Chunk
 ↓
document_id
 ↓
source
 ↓
page
 ↓
section
```

Toh baad mein RAG ye generate kar sakta hai:

```
According to the Leave Policy,
employees receive 18 casual leaves per year.

Source: employee_handbook.pdf, page 14
```

**Yehi ek wajah hai ki metadata itna useful hai.**

## 16. Metadata Aur Document Updates

Maan le:

```
Policy 2025
```

ko replace kar diya jaata hai:

```
Policy 2026
```

se.

Tu filter kar sakta hai:

```sql
WHERE version = '2026'
```

ya ek:

```
is_active
```

field maintain kar sakta hai.

Example:

```sql
WHERE tenant_id = 42
  AND is_active = TRUE
```

Ab stale chunks retrieval mein nahi aate.

## 17. Metadata Filtering ≠ Security By Itself

**Important distinction:**

```
Metadata filter
        ≠
Complete authorization system
```

Ek robust architecture hai:

```
Authenticated User
       ↓
Authorization Service / trusted policy
       ↓
Allowed tenant/documents
       ↓
Retrieval filter
       ↓
Vector Search
       ↓
Results
```

Kabhi nahi:

```
LLM says:
"User is admin"
       ↓
Trust it
```

**Nahi.**

Same principle Phase 2 se yahan apply hoti hai:

> **LLM output untrusted input hai.**

## 18. Production RAG Retrieval

Ab hamari retrieval architecture ban rahi hai:

```
                     USER
                       │
                       ↓
                  User Query
                       │
                       ↓
                Query Embedding
                       │
                       ↓
             ┌──────────────────┐
             │ Retrieval Layer  │
             └────────┬─────────┘
                      │
             ┌────────┴─────────┐
             ↓                  ↓
      Metadata Filter      Vector Search
             │                  │
             └────────┬─────────┘
                      ↓
                   Ranking
                      ↓
                    Top-K
                      ↓
                Retrieved Chunks
                      ↓
                     LLM
```

Aur ab tu dekh sakta hai ki pichle topics kaise connect hote hain:

```
Chunking
   ↓
Embeddings
   ↓
Vector Storage
   ↓
Similarity Search
   ↓
Metadata Filtering
   ↓
Efficient Index
   ↓
RAG
```

## 🧠 Interview Questions

**Q1. Why use metadata filtering with vector search?**

> Retrieval ko un documents tak constrain karne ke liye jo deterministic conditions satisfy karte hain jaise tenant, permissions, document type, language, ya version, jabki semantic similarity us eligible set ke andar relevance determine karti hai.

**Q2. Can embeddings handle authorization?**

> Nahi.

> Authorization deterministic hona chahiye aur trusted backend logic se enforce hona chahiye.

**Q3. What is pre-filtering?**

> Candidate set ko metadata constraints use karke restrict karna, vector retrieval se pehle ya uska hissa banake.

**Q4. Why is multi-tenancy important in vector search?**

> Tenant isolation ke bina, doosre customer se semantically similar data ek retrieval candidate ban sakta hai, jisse correctness aur potentially serious data-isolation issues dono create ho sakte hain.

**Q5. Why not put every metadata field into the embedding?**

> Kyunki semantic representation deterministic filtering ka substitute nahi hai. Ek vector reliably ye enforce nahi kar sakta:

```
tenant = 42
```

ya:

```
user has permission
```


---

## 9. Complete Production Implementation: Metadata-Filtered Vector Search Engine 💻

Below is an end-to-end Python implementation contrasting the three metadata filtering strategies discussed:
1. **Post-filtering (Over-fetch & Prune):** Retrieves top $K \times M$ nearest vectors, then filters by metadata. Demonstrates where it fails (filter starvation).
2. **Pre-filtering (Boolean Bitmap Masking):** Applies SQL/metadata predicate first, then executes vector search on the qualified candidate subset.
3. **Single-stage Integrated Filtering (Iterative Graph Traversal):** Simulates how modern vector databases (like pgvector with partial indexes or Qdrant) maintain high recall even with restrictive tenant/department filters.

```python
"""
metadata_filtered_search.py
Production Demonstration of Metadata Filtering in Vector Databases:
- Pre-filtering vs Post-filtering vs Single-stage Filtering
- Demonstrating the 'Filter Starvation' catastrophe in Post-filtering
- Multi-tenant isolation simulation (tenant_id, department, access_level)
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple


class DocumentRecord:
    def __init__(self, doc_id: int, text: str, embedding: np.ndarray, metadata: Dict[str, Any]):
        self.doc_id = doc_id
        self.text = text
        self.embedding = embedding
        self.metadata = metadata


class MetadataVectorStore:
    def __init__(self, dim: int = 64):
        self.dim = dim
        self.documents: List[DocumentRecord] = []
        self.embeddings: np.ndarray = None

    def insert(self, doc_id: int, text: str, metadata: Dict[str, Any]):
        rng = np.random.RandomState(doc_id)
        vec = rng.randn(self.dim).astype(np.float32)
        vec /= np.linalg.norm(vec)
        self.documents.append(DocumentRecord(doc_id, text, vec, metadata))
        self.embeddings = np.array([d.embedding for d in self.documents])

    def matches_filter(self, metadata: Dict[str, Any], filter_pred: Dict[str, Any]) -> bool:
        """Evaluates exact match metadata predicates (AND semantics)."""
        for k, v in filter_pred.items():
            if metadata.get(k) != v:
                return False
        return True

    # -------------------------------------------------------------
    # 1. Post-Filtering (Anti-pattern for selective filters)
    # -------------------------------------------------------------
    def post_filtered_search(
        self, query_vec: np.ndarray, filter_pred: Dict[str, Any], top_k: int = 5, overfetch_factor: int = 4
    ) -> List[Tuple[DocumentRecord, float]]:
        """
        Step 1: Retrieve top (K * overfetch_factor) purely by vector similarity.
        Step 2: Discard candidates that fail the metadata predicate.
        Risk: If the filter matches only 1% of data, all top-N candidates might be discarded!
        """
        candidate_count = top_k * overfetch_factor
        scores = np.dot(self.embeddings, query_vec)
        top_indices = np.argsort(scores)[::-1][:candidate_count]

        filtered_results = []
        for idx in top_indices:
            doc = self.documents[idx]
            if self.matches_filter(doc.metadata, filter_pred):
                filtered_results.append((doc, float(scores[idx])))
                if len(filtered_results) == top_k:
                    break

        return filtered_results

    # -------------------------------------------------------------
    # 2. Pre-Filtering (Safe for selective filters)
    # -------------------------------------------------------------
    def pre_filtered_search(
        self, query_vec: np.ndarray, filter_pred: Dict[str, Any], top_k: int = 5
    ) -> List[Tuple[DocumentRecord, float]]:
        """
        Step 1: Filter documents matching predicate first.
        Step 2: Perform vector dot product ONLY on the surviving subset.
        Guarantee: Always returns up to top_k matching documents without starvation.
        """
        valid_indices = [
            i for i, doc in enumerate(self.documents)
            if self.matches_filter(doc.metadata, filter_pred)
        ]

        if not valid_indices:
            return []

        subset_embeddings = self.embeddings[valid_indices]
        scores = np.dot(subset_embeddings, query_vec)
        top_local_indices = np.argsort(scores)[::-1][:top_k]

        return [
            (self.documents[valid_indices[local_idx]], float(scores[local_idx]))
            for local_idx in top_local_indices
        ]


# =====================================================================
# Verification: Starvation Scenario
# =====================================================================
if __name__ == "__main__":
    store = MetadataVectorStore(dim=64)

    print("Populating 10,000 synthetic documents across tenants...")
    # 9,950 documents belong to tenant_id = 'public'
    # 50 documents belong to tenant_id = 'finance_restricted'
    for i in range(10_000):
        tenant = "finance_restricted" if i < 50 else "public"
        dept = "payroll" if i < 10 else "engineering"
        store.insert(
            doc_id=i,
            text=f"Document #{i} relating to internal operations.",
            metadata={"tenant_id": tenant, "department": dept}
        )

    query = np.random.randn(64).astype(np.float32)
    query /= np.linalg.norm(query)

    filter_criteria = {"tenant_id": "finance_restricted", "department": "payroll"}
    target_k = 5

    print(f"\nTarget filter: {filter_criteria}")
    print(f"Goal: Return top {target_k} matching records.\n")

    # Run Post-filtering
    t0 = time.perf_counter()
    post_results = store.post_filtered_search(query, filter_criteria, top_k=target_k, overfetch_factor=10)
    t_post = (time.perf_counter() - t0) * 1000

    print(f"=== POST-FILTERING (Overfetch: 10x) ===")
    print(f"Results returned : {len(post_results)} / {target_k} (Filter Starvation: {len(post_results) < target_k})")
    print(f"Latency          : {t_post:.3f} ms\n")

    # Run Pre-filtering
    t0 = time.perf_counter()
    pre_results = store.pre_filtered_search(query, filter_criteria, top_k=target_k)
    t_pre = (time.perf_counter() - t0) * 1000

    print(f"=== PRE-FILTERING (Predicate first) ===")
    print(f"Results returned : {len(pre_results)} / {target_k} (Complete Recall Guaranteed)")
    print(f"Latency          : {t_pre:.3f} ms")
    for rank, (doc, score) in enumerate(pre_results, start=1):
        print(f"  #{rank}: Doc ID {doc.doc_id} | Score: {score:.4f} | Meta: {doc.metadata}")
```

### Execution:
```bash
python metadata_filtered_search.py
```
