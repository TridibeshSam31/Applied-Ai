# Similarity Search & Top-K 🔎 — Phase 3: Embeddings + Vector DB

Ab hum **actual retrieval algorithm** samjhenge.

Ab tak:

```
Document
 ↓
Chunk
 ↓
Embedding
 ↓
Vector DB
```

Ab user query aati hai:

```
"How do I authenticate a user?"
```

Question:

> Database mein 1 lakh chunks hain — relevant chunks kaise nikaalenge?

## 1. Core Idea

Query ko bhi embedding mein convert karo:

```
User Query
   ↓
Embedding Model
   ↓
Query Vector
```

Maan le simplified vectors:

```
Query      → [0.90, 0.80, 0.70]

Chunk A    → [0.91, 0.81, 0.71]
Chunk B    → [0.10, 0.20, 0.30]
Chunk C    → [0.88, 0.79, 0.69]
Chunk D    → [0.30, 0.20, 0.10]
```

Ab query vector ko har chunk ke vector ke saath compare karo.

```
Query
  │
  ├── Chunk A → similarity
  ├── Chunk B → similarity
  ├── Chunk C → similarity
  └── Chunk D → similarity
```

Phir rank karo.

```
A → highest
C → second
B → third
D → fourth
```

Agar:

```
K = 2
```

phir:

```
Top-K = [A, C]
```

## 2. Top-K Ka Matlab

**K = kitne results chahiye.**

```
LIMIT 5
```

matlab:

```
K = 5
```

Toh:

```
Top-3 → 3 most relevant chunks
Top-5 → 5 most relevant chunks
Top-10 → 10 most relevant chunks
```

RAG mein common flow:

```
Query
 ↓
Retrieve Top-K
 ↓
Context
 ↓
LLM
```

## 3. Similarity Calculate Kaise Hoti Hai?

Humne Topic 4 mein cosine similarity padha tha:

$$ cos(A,B)=\frac{A\cdot B}{||A||||B||} $$

Example:

```
A = [1, 0]
B = [1, 0]
```

Phir:

```
cosine similarity = 1
```

Same direction.

**Example 2**

```
A = [1, 0]
B = [0, 1]
```

Phir:

```
similarity = 0
```

Perpendicular.

**Example 3**

```
A = [1, 0]
B = [-1, 0]
```

Phir:

```
similarity = -1
```

Opposite direction.

## 4. Python Mein Actual Top-K

Small dataset ke liye NumPy se samajh:

```python
import numpy as np


def cosine_similarity(a, b):
    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


query = np.array([0.9, 0.8, 0.7])

documents = {
    "A": np.array([0.91, 0.81, 0.71]),
    "B": np.array([0.10, 0.20, 0.30]),
    "C": np.array([0.88, 0.79, 0.69]),
    "D": np.array([0.30, 0.20, 0.10]),
}

results = []

for doc_id, vector in documents.items():

    score = cosine_similarity(query, vector)

    results.append((doc_id, score))


results.sort(
    key=lambda x: x[1],
    reverse=True
)

top_k = results[:2]

print(top_k)
```

Conceptually output:

```
[
    ('A', 0.999...),
    ('C', 0.999...)
]
```

## 5. Algorithm Ko Line-by-Line Samajh

### Step 1

```python
query = [...]
```

Query ka embedding.

### Step 2

```python
for doc_id, vector in documents.items():
```

Har stored chunk ko consider karo.

### Step 3

```python
score = cosine_similarity(query, vector)
```

Query aur chunk ke beech similarity.

### Step 4

```python
results.append((doc_id, score))
```

Score save karo.

### Step 5

```python
results.sort(
    key=lambda x: x[1],
    reverse=True
)
```

Highest similarity first.

### Step 6

```python
top_k = results[:2]
```

Top 2 results.

**Yehi poora basic retrieval algorithm hai.**

## 6. Lekin Production Mein Python Loop Nahi Karenge

Maan le:

```
10 million vectors
```

Agar Python mein:

```python
for vector in 10_000_000:
    calculate_similarity()
```

**❌ Terrible approach.**

Iske bajaye:

```
Python
  ↓
PostgreSQL + pgvector
  ↓
Vector search
```

Example:

```sql
SELECT
    id,
    content,
    embedding <=> '[0.9,0.8,0.7]' AS distance
FROM document_chunks
ORDER BY embedding <=> '[0.9,0.8,0.7]'
LIMIT 5;
```

**Database retrieval handle karta hai.**

## 7. Exact Nearest Neighbor Search

Vector index ke bina, conceptually:

```
Query
 ↓
Compare with Vector 1
 ↓
Compare with Vector 2
 ↓
Compare with Vector 3
 ↓
...
 ↓
Compare with Vector N
 ↓
Sort
 ↓
Top-K
```

Agar N vectors hain aur har vector ke D dimensions hain:

roughly:

```
O(N × D)
```

work ek brute-force scan ke liye.

Example:

```
N = 1,000,000
D = 1536
```

**Ye ek LOT of vector operations hai.**

## 8. Top-K Kyun Enough Nahi Hai

Koi bol sakta hai:

> "Bas LIMIT 5 laga do."

Problem ye hai ki:

```sql
ORDER BY distance
LIMIT 5
```

**phir bhi determine karna padta hai ki kaunse vectors sabse closest hain.**

`LIMIT 5` magically search ko cheap nahi bana deta.

Conceptually database ko phir bhi nearest vectors dhoondhne ka ek efficient tarika chahiye.

Yehi wajah hai ki humein chahiye:

```
Vector Index
     ↓
HNSW
IVF
```

## 9. Exact vs Approximate Search 🔥

### Exact Nearest Neighbor

```
Query
 ↓
Check ALL vectors
 ↓
Find actual nearest neighbors
```

**Advantage:**

```
Highest recall / exact result
```

**Disadvantage:**

```
Can become expensive at large scale
```

### Approximate Nearest Neighbor — ANN

Sab kuch check karne ke bajaye:

```
Query
 ↓
Index
 ↓
Search likely candidates
 ↓
Top-K
```

**Tu thodi exactness sacrifice karta hai much better speed ke liye.**

Ye hai:

```
        ANN
         │
    ┌────┴────┐
    ↓         ↓
 Faster     Approximate
 Search     Neighbors
```

## 10. Recall Important Ban Jaata Hai

Maan le actual nearest neighbors hain:

```
A
B
C
D
E
```

Tera ANN search return karta hai:

```
A
B
C
X
Y
```

Tune dhoonda:

```
3 / 5
```

Toh:

```
Recall@5 = 3/5 = 60%
```

High-quality retrieval systems in metrics ki fikar karte hain:

```
Recall@K
Precision@K
MRR
NDCG
```

Abhi ke liye, **Recall@K** important hai.

## 11. RAG Mein Retrieval Recall Kyun Matter Karta Hai

Maan le correct answer exist karta hai:

```
Chunk 932
```

mein.

Lekin tera retriever isse return nahi karta.

Phir:

```
Retriever
    ↓
wrong chunks
    ↓
LLM
    ↓
wrong context
    ↓
wrong answer
```

**Chahe tera LLM extremely powerful ho.**

Toh:

> **Ek generation model reliably us information se answer nahi kar sakta jo retrieval layer provide karne mein fail hui.**

Yehi wajah hai ki RAG evaluation sirf ye nahi hai:

> "Did the LLM sound good?"

Tujhe retrieval ko separately evaluate karna hoga.

## 12. Top-K Selection Ka Ek Trade-off Hai

Maan le:

```
K = 2
```

Tujhe milte hain:

```
2 chunks
```

Very focused context.

Lekin shayad answer ko chunk 3 se information chahiye ho.

Agar:

```
K = 50
```

tu bahut saari information retrieve karta hai.

Lekin ab:

```
50 chunks
 ↓
huge context
 ↓
more tokens
 ↓
higher cost
 ↓
more noise
```

Toh:

```
Small K
 ↓
precision
 ↓
less context

Large K
 ↓
recall
 ↓
more noise/cost
```

Phir se, isse benchmark kar.

## 13. Retrieval Pipeline

Ye mental model hai jo main chahta hoon tu lock kar le:

```
                  USER QUERY
                       │
                       ↓
                Embedding Model
                       │
                       ↓
                 Query Vector
                       │
                       ↓
              ┌────────────────┐
              │ Vector Search  │
              └───────┬────────┘
                      │
              Similarity/Distance
                      │
                      ↓
                   Ranking
                      │
                      ↓
                    Top-K
                      │
                      ↓
              Retrieved Chunks
                      │
                      ↓
                  RAG Context
                      │
                      ↓
                     LLM
```

## 14. Bahut Important Distinction

### Embedding

Answer karta hai:

> "How do I represent this text as a vector?"

### Similarity

Answer karta hai:

> "How close are these two vectors?"

### Search

Answer karta hai:

> "Which stored vectors are closest to my query vector?"

### Top-K

Answer karta hai:

> "How many of the best results should I return?"

### Vector Index

Answer karta hai:

> "How can I make this search efficient at scale?"

**In concepts ko separate rakh.**

## 15. Real pgvector Example

Maan le:

```sql
CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536)
);
```

Query:

```sql
SELECT
    id,
    content,
    embedding <=> '[...]' AS distance
FROM document_chunks
ORDER BY embedding <=> '[...]'
LIMIT 5;
```

Iska matlab hai:

```
embedding
    ↓
compare with query vector
    ↓
cosine distance
    ↓
smallest distance first
    ↓
5 results
```

## 16. Ek Subtle Production Issue

Maan le similarity scores hain:

```
0.91
0.89
0.88
0.42
0.39
```

Kya tujhe blindly top 5 lena chahiye?

Shayad nahi.

Agar:

```
K = 5
```

tujhe phir bhi milenge:

```
0.42
0.39
```

chahe wo probably weak matches hon.

Yehi wajah hai ki baad mein tu combine kar sakta hai:

```
Top-K
+
similarity threshold
+
reranking
```

Example:

```
Retrieve Top-20
       ↓
Filter/rerank
       ↓
Top-5 high-quality chunks
```

Isse hum properly RAG mein encounter karenge.

## 🧠 Interview Questions

**Q1. What is Top-K retrieval?**

> K highest-ranked documents/chunks retrieve karna ek similarity ya distance metric ke according.

**Q2. Why not retrieve the entire database?**

> Isse huge context, latency aur cost introduce hoti hai, aur irrelevant information add hoti hai.

**Q3. Why is ANN used?**

> Exact nearest-neighbor search expensive ban jaati hai jaise jaise vector count badhta hai, isliye ANN indexes recall ka ek chhota sa amount trade karte hain significantly better search efficiency ke liye.

**Q4. What is Recall@K?**

> Relevant items ka wo fraction jo successfully top K results ke andar retrieve hua.

**Q5. Is higher cosine similarity always better?**

> Same compatible embedding/search setup ke andar, higher cosine similarity greater geometric similarity matlab rakhta hai, lekin absolute score semantic correctness ka universal measure nahi hai.