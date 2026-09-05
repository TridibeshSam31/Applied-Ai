# Semantic Similarity 🧠📐 — Phase 3: Embeddings + Vector DB

Ab tak:

```
Text
 ↓
Embedding Model
 ↓
Vector
```

Ab actual question:

> **Do vectors kaise pata lagayenge ki unke texts semantically similar hain?**

**Isi ko semantic similarity kehte hain.**

## 1. Semantic Similarity Kya Hai?

Semantic similarity ka matlab:

> Do pieces of data ke meaning kitne similar hain.

Example:

```
A = "I love programming"
B = "I enjoy writing code"
C = "The weather is very hot"
```

Human intuitively samajhta hai:

```
A ↔ B   HIGH similarity
A ↔ C   LOW similarity
```

**Embedding system bhi roughly ye relationship capture karne ki koshish karta hai.**

## 2. Vector Space Mein Imagine Karo

Maan le embeddings ko 2D mein visualize kar sakein:

```
                    Programming
                         ↑
                         │
             A ●         │
               ╲         │
                ╲        │
                 ● B     │
                         │
                         │
                         │
                         │
                         ● C
                         │
─────────────────────────┼────────→
```

Jahan:

```
A = "I love programming"
B = "I enjoy writing code"
C = "The weather is hot"
```

A aur B paas hain.

C door hai.

Toh:

```
distance(A, B) → small
distance(A, C) → large
```

Ya similarity use karke:

```
similarity(A, B) → high
similarity(A, C) → low
```

## 3. Semantic ≠ Lexical Similarity

**Ye distinction interview mein important hai.**

### Lexical Similarity

Exact words compare kar:

```
"I love programming"
"I love programming"
```

Very high.

Lekin:

```
"I love programming"
"I enjoy writing software"
```

Words different hain.

Keyword matching struggle kar sakta hai.

### Semantic Similarity

Meaning compare karta hai:

```
"I love programming"
        ↕
"I enjoy writing software"
```

High similarity.

## 4. Example: Search

Database:

```
D1 = "How to reset your password"
D2 = "How to change your email address"
D3 = "How to deploy a Python API"
```

Query:

```
"I forgot my login password"
```

Semantic similarity ideally:

```
Query ↔ D1 = HIGH
Query ↔ D2 = LOW
Query ↔ D3 = VERY LOW
```

Toh vector search return karta hai:

```
D1
```

**Yehi basic idea hai semantic search ke peeche.**

## 5. Hum Isse Calculate Kaise Karte Hain?

Ab mathematics aayegi.

Common similarity/distance measures:

### 1. Cosine Similarity ⭐

```
angle between vectors
```

### 2. Euclidean Distance

```
straight-line distance
```

### 3. Dot Product

```
vector multiplication
```

Aaj semantic similarity ka concept samajh le.

Next Topic 4 mein cosine similarity ko mathematically + code ke saath properly karenge.

## 6. Simple Vector Example

Maan le:

```
A = [1, 0]
B = [0.9, 0.1]
C = [-1, 0]
```

Visual:

```
              B
             ↗
            /
A ───────────────→

←─────────────── C
```

A aur B same general direction mein hain.

A aur C opposite directions mein hain.

Isliye:

```
similarity(A, B) → high
similarity(A, C) → low/negative
```

**Cosine similarity particularly useful hai kyunki ye direction pe focus karta hai, sirf magnitude pe nahi.**

## 7. Direction vs Magnitude

Maan le:

```
A = [1, 1]
B = [10, 10]
```

Direction same hai:

```
A → ↗
B → ↗
```

Magnitude different hai.

Cosine similarity:

```
≈ 1
```

kyunki direction same hai.

**Ye embeddings ke liye useful ho sakta hai jahan vector space mein orientation semantic information carry karta hai** — magnitude irrelevant ho sakta hai, direction hi wo cheez hai jo meaning encode karti hai.

## 8. Sirf Euclidean Distance Kyun Nahi?

Euclidean distance:

```
distance(A, B)
```

magnitude aur direction dono pe depend karta hai.

Embeddings ke liye, kabhi kabhi direction raw magnitude se zyada informative hoti hai.

**Yehi wajah hai ki cosine similarity ek bahut common choice hai.**

Lekin important:

> Cosine universally "the best" metric nahi hai. Appropriate metric embedding model aur retrieval setup pe depend karta hai.

## 9. Similarity Score

Maan le hum calculate karte hain:

```
Query ↔ Document 1 = 0.92
Query ↔ Document 2 = 0.71
Query ↔ Document 3 = 0.18
```

Hum rank kar sakte hain:

```
1. Document 1 → 0.92
2. Document 2 → 0.71
3. Document 3 → 0.18
```

Phir top-k retrieve kar:

```
Top 2
 ↓
Document 1
Document 2
```

**Yehi wo cheez hai jo hum eventually pgvector ke saath implement karenge.**

## 10. Similarity Ka Matlab "Truth" Nahi Hai

**Bahut important.**

Maan le:

```
Query:
"How do I get a refund?"
```

Retrieved document:

```
"Refunds are available within 30 days."
```

**High semantic similarity ka matlab hai:**

> Ye document probably relevant hai.

**Iska matlab NAHI hai:**

> Ye document necessarily correct hai.

**Semantic search retrieval hai, fact verification nahi.**

Yehi wajah hai ki baad mein RAG ko chahiye:

```
retrieval
+
grounding
+
evaluation
```

## 11. Similarity Threshold

Maan le results hain:

```
D1 → 0.91
D2 → 0.83
D3 → 0.21
D4 → 0.17
```

Tu use kar sakta hai:

```
threshold = 0.75
```

Phir:

```
D1 ✅
D2 ✅
D3 ❌
D4 ❌
```

Lekin blindly ye assume mat kar:

```
0.75 = always relevant
```

Similarity scores model- aur setup-dependent hote hain.

**Ek threshold ideally tere actual dataset pe evaluation ke through determine hona chahiye.**

Ye Phase 7 Evals mein important ban jaata hai.

## 12. Ranking

Maan le 1,000 documents exist karte hain.

Query:

```
"What is the company's leave policy?"
```

Hum ye nahi chahte:

```
1,000 documents
```

LLM ko bheje jaayein.

Iske bajaye:

```
1,000 documents
       ↓
Generate/query vector
       ↓
Similarity search
       ↓
Rank
       ↓
Top 5
       ↓
LLM
```

**Ye efficient RAG ki foundation hai.**

## 13. Semantic Similarity Pipeline

Ye architecture apne dimaag mein rakh:

```
                 QUERY
                   │
                   ▼
             Embedding Model
                   │
                   ▼
             Query Vector
                   │
                   ▼
        ┌─────────────────────┐
        │ Compare with stored │
        │ document vectors    │
        └──────────┬──────────┘
                   │
                   ▼
              Similarity
                   │
                   ▼
                 Rank
                   │
                   ▼
                Top-K
```

## 14. Python: Basic Similarity Experiment

Vector DB use karne se pehle, chal isse manually karte hain.

```python
import numpy as np


def cosine_similarity(a, b):
    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


a = np.array([1, 0])
b = np.array([0.9, 0.1])
c = np.array([-1, 0])

print(cosine_similarity(a, b))
print(cosine_similarity(a, c))
```

Tujhe approximately milega:

```
0.994
-1.0
```

Toh:

```
A ↔ B → almost identical direction
A ↔ C → opposite direction
```

**Numbers yaad mat kar. Geometry samajh.**

## 15. Real Embeddings

Ab socho:

```python
query_vector = embed(
    "I forgot my password"
)

document_vectors = [
    embed("How to reset your password"),
    embed("How to deploy a Python API"),
    embed("Today's weather forecast")
]
```

Phir:

```python
scores = [
    cosine_similarity(query_vector, doc)
    for doc in document_vectors
]
```

Potential result:

```
[
    0.89,
    0.21,
    0.08
]
```

Descending sort kar:

```
Password document → 0.89
Python API        → 0.21
Weather           → 0.08
```

**Yehi semantic retrieval hai.**

## 16. Ek Major Limitation

Semantic similarity magic nahi hai.

Consider kar:

```
A:
"Java is a programming language."

B:
"Java is an island in Indonesia."
```

Dono mein same word hai:

```
Java
```

**Ek good contextual embedding model inke meanings ko surrounding context ke basis pe distinguish karna chahiye.**

Lekin retrieval quality phir bhi fail ho sakti hai in wajahon se:

```
ambiguous language
poor chunking
domain-specific terminology
bad embedding model
insufficient context
multilingual issues
```

Yehi wajah hai ki baad mein hum study karenge:

```
Embedding model
+
Chunking
+
Metadata
+
Hybrid search
+
Reranking
```

## 17. Semantic Similarity vs Semantic Search

Inhe confuse mat kar.

### Semantic Similarity

Sawaal:

```
"How similar are A and B?"

A ↔ B → score
```

### Semantic Search

Sawaal:

```
"Which documents are most similar to this query?"

Query
 ↓
Compare against many vectors
 ↓
Rank
 ↓
Top-K
```

Toh:

```
Semantic Similarity
        ↓
building block
        ↓
Semantic Search
        ↓
RAG
```

## 18. Interview Questions

**Q: What is semantic similarity?**

> Ye measure karta hai ki do pieces of data meaning mein kitne closely related hain, often unke embedding vectors compare karke.

**Q: How does semantic search differ from keyword search?**

> Keyword search primarily lexical terms match karta hai, jabki semantic search vector representations use karta hai meaning ke basis pe content retrieve karne ke liye.

**Q: Why are embeddings useful for search?**

> Ye queries aur documents ko, jinke words different ho sakte hain lekin meaning similar, ek comparable vector space mein represent karne dete hain aur similarity se rank karne dete hain.

**Q: Is a high similarity score proof that a document is correct?**

> Nahi. Ye semantic relevance indicate karta hai, factual correctness nahi.