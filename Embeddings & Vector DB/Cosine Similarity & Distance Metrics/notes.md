# Cosine Similarity & Distance Metrics 📐 — Phase 3: Embeddings + Vector DB

Ab actual maths pe aate hain. **Ye topic vector search ka core hai.**

Humare paas:

```
Query
  ↓
Embedding
  ↓
Query Vector

Documents
  ↓
Embeddings
  ↓
Document Vectors
```

Ab question:

> Query vector aur document vector kitne similar hain?

## 1. Cosine Similarity

Cosine similarity do vectors ke beech **angle** compare karta hai.

Formula:

$$ \text{cosine similarity}(A,B) = \frac{A\cdot B} {\|A\|\|B\|} $$

Panic mat kar 😂. Isko pieces mein samajhte hain.

## 2. Dot Product

Maan le:

```
A = [1, 2]
B = [3, 4]
```

Dot product:

$$ A\cdot B = (1×3)+(2×4) $$
```
= 3 + 8
= 11
```

Python:

```python
import numpy as np

A = np.array([1, 2])
B = np.array([3, 4])

dot = np.dot(A, B)

print(dot)
# 11
```

## 3. Vector Magnitude

Magnitude basically vector ki **length** hai.

Formula:

$$ \|A\| = \sqrt{A_1^2 + A_2^2 + ...} $$

For:

```
A = [1, 2]
```
$$ \|A\| = \sqrt{1^2+2^2} $$
```
= √5
≈ 2.236
```

Python:

```python
magnitude = np.linalg.norm(A)

print(magnitude)
```

## 4. Full Cosine Calculation

For:

```
A = [1, 2]
B = [3, 4]
```

Hamare paas hai:

```
A · B = 11
```

Magnitude:

```
|A| ≈ 2.236
|B| = 5
```

Isliye:

$$ \frac{11}{2.236×5} $$

≈

```
0.984
```

Toh vectors ek bahut similar direction mein point kar rahe hain.

## 5. Intuition — Angle

Socho:

```
             B
            ↗
           /
          /
         /
        ↗
       A
```

Small angle:

```
→ high cosine similarity
```

Agar vectors exactly same direction mein point karte hain:

```
A ─────────→
B ─────────→
```

Angle:

```
0°
```

Cosine:

```
cos(0°) = 1
```

Toh:

```
Similarity = 1
```

## 6. Opposite Direction

```
A ─────────→

←───────── B
```

Angle:

```
180°
```
$$ cos(180°)=-1 $$

Toh:

```
Similarity = -1
```

## 7. Perpendicular Vectors

```
        B
        ↑
        │
        │
        │
────────┼──────→ A
```

Angle:

```
90°
```
$$ cos(90°)=0 $$

Toh:

```
Similarity ≈ 0
```

## 8. Basic Range

Standard cosine similarity ke liye:

```
-1 ───────── 0 ───────── +1
```

Matlab roughly:

```
-1 → opposite direction
 0 → perpendicular
+1 → same direction
```

**Note:** Kai modern text embeddings ke saath, practical scores ek narrower positive range mein occupy ho sakte hain, model aur data pe depend karte hue. Ye assume mat kar ki 0.5, 0.7, ya 0.9 ka koi universal meaning hai models ke across.

## 9. Direction Kyun?

Ye key intuition hai.

Consider kar:

```
A = [1, 1]
B = [10, 10]
```

B kaafi bada hai.

Lekin direction identical hai:

```
A ↗
B ↗
```

Isliye:

```
cosine_similarity(A, B) = 1
```

Calculate kar:

$$ \frac{1×10+1×10} {\sqrt{2}\sqrt{200}} $$
```
= 1
```

Toh cosine similarity essentially ye kehta hai:

> "Mujhe orientation ki fikar zyada hai raw magnitude se."

## 10. Euclidean Distance

Ek aur option hai **Euclidean distance.**

Formula:

$$ d(A,B)=\sqrt{\sum_i(A_i-B_i)^2} $$

For:

```
A = [1, 2]
B = [3, 4]
```
```
distance =
√((1-3)² + (2-4)²)

= √(4 + 4)

= √8
≈ 2.828
```

Python:

```python
distance = np.linalg.norm(A - B)

print(distance)
```

Yahan:

> **Smaller distance = more similar**, agar tu Euclidean distance ko similarity notion ki tarah use kar raha hai.

## 11. Cosine vs Euclidean

| | Cosine | Euclidean |
|---|---|---|
| Measures | Direction/angle | Straight-line distance |
| Better score | Usually higher | Usually lower |
| Range | -1 to 1 | 0 to ∞ |
| Magnitude matters? | Less directly | Yes |
| Common for embeddings | Very common | Also used |

Lekin ye yaad mat kar:

> "Cosine good, Euclidean bad."

**Ye galat hai.**

Correct choice embedding model aur indexing/retrieval setup pe depend karta hai.

## 12. Dot Product

Teesra important metric:

$$ A\cdot B $$

For:

```
A = [1,2]
B = [3,4]
```

hum already calculate kar chuke hain:

```
11
```

**Dot product bhi vector databases mein commonly use hota hai.**

Lekin cosine similarity ke unlike, raw dot product vector magnitude se affected hota hai.

Example:

```
A = [1,1]
B = [10,10]
```

Dot product:

```
20
```

jabki:

```
A = [1,1]
C = [1,1]
```

Dot product:

```
2
```

Same direction, lekin different magnitude → different dot-product scores.

## 13. Cosine Aur Dot Product Ka Relationship

Agar vectors normalized hain:

```
||A|| = 1
||B|| = 1
```

phir:

$$ \frac{A\cdot B}{1×1} $$

ban jaata hai:

$$ A\cdot B $$

Isliye:

> **Normalized vectors ke liye, cosine similarity aur dot product same ranking produce karte hain.**

**Ye ek important engineering optimization hai.**

## 14. Actual Semantic Search Example

Maan le:

```
Query:
"I forgot my password"
```

Embedding:

```
Q
```

Documents:

```
D1 = "How to reset your password"
D2 = "How to deploy FastAPI"
D3 = "Weather forecast"
```

Vectors:

```
Q  → [....]
D1 → [....]
D2 → [....]
D3 → [....]
```

Calculate kar:

```
cos(Q,D1) = 0.91
cos(Q,D2) = 0.19
cos(Q,D3) = 0.07
```

Rank:

```
D1 → 0.91  ⭐
D2 → 0.19
D3 → 0.07
```

Return kar:

```
D1
```

**Ye semantic retrieval ka mathematical core hai.**

## 15. Manual Implementation

Ek baar khud likh:

```python
import numpy as np


def cosine_similarity(a, b):
    dot_product = np.dot(a, b)

    magnitude_a = np.linalg.norm(a)
    magnitude_b = np.linalg.norm(b)

    return dot_product / (
        magnitude_a * magnitude_b
    )


a = np.array([1, 2])
b = np.array([3, 4])

score = cosine_similarity(a, b)

print(score)
```

## 16. Zero-Vector Protection Add Kar

Production code ko blindly divide nahi karna chahiye.

Agar:

```
A = [0,0]
```

phir:

```
||A|| = 0
```

aur hum zero se divide kar denge.

Better:

```python
def cosine_similarity(a, b):

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        raise ValueError(
            "Cosine similarity undefined for zero vector"
        )

    return np.dot(a, b) / (norm_a * norm_b)
```

Small detail, lekin good engineering — ye chhoti checks hi production code ko tutne se bachati hain.

## 17. Ek Query Ko Kai Documents Ke Against Compare Karna

Real search kuch aisa hota hai:

```python
query = np.array([1, 2])

documents = {
    "doc1": np.array([1, 1]),
    "doc2": np.array([2, 2]),
    "doc3": np.array([-1, 0])
}

scores = []

for doc_id, vector in documents.items():

    score = cosine_similarity(query, vector)

    scores.append((doc_id, score))

scores.sort(
    key=lambda x: x[1],
    reverse=True
)

print(scores)
```

Conceptually:

```
doc2 → highest
doc1 → next
doc3 → lowest
```

**Ye already ek primitive semantic search engine hai.**

## 18. Top-K

Maan le hamare paas hai:

```
100,000 documents
```

Scores:

```
doc_1 → 0.21
doc_2 → 0.91
doc_3 → 0.54
...
doc_99999 → 0.83
```

Similarity se sort kar:

```
0.95
0.93
0.91
0.89
0.87
...
```

Phir:

```
Top-K = 5
```

sirf ye return karta hai:

```
5 most relevant documents
```

**Ye fundamental operation hai jo hum eventually pgvector se efficiently perform karwaayenge.**

## 19. Vector Databases Ki Zarurat Kyun Hai

Tu shayad soche:

> "Bhai, Python loop se sab vectors compare kar lenge."

Iske liye:

```
100 documents
```

Sure.

Iske liye:

```
100 million vectors
```

**Har query ke liye naive exact scan practical nahi hai.**

Tujhe chahiye:

```
efficient storage
+
vector indexes
+
nearest-neighbor search
+
metadata filtering
```

Yehi wajah hai ki hum move karte hain:

```
NumPy
```

se:

```
Vector Database
```

Aur specifically, **pgvector**, kyunki tu already PostgreSQL ke saath comfortable hai.

## 20. Exact vs Approximate Search

Do broad approaches:

### Exact / Brute-Force

```
Query
 ↓
Compare against EVERY vector
 ↓
Find exact nearest neighbors
```

Accurate, lekin scale pe expensive.

### Approximate Nearest Neighbor (ANN)

```
Query
 ↓
Vector index
 ↓
Search promising region
 ↓
Top-K candidates
```

Scale pe **much faster**, possible accuracy/recall trade-off ke saath.

Baad mein:

```
HNSW
IVF
```

important index concepts hain.

## 21. Ek Important Correction

Ye mat bol:

> "Cosine similarity tells whether two sentences mean exactly the same thing."

Iske bajaye ye bol:

> "Cosine similarity unke embedding representations ke beech similarity measure karta hai."

**Embedding model determine karta hai ki meaning kaise represent hota hai.**

Toh retrieval quality depend karti hai:

```
Embedding model
        +
Data
        +
Chunking
        +
Similarity metric
        +
Index
```

**Sirf cosine similarity pe nahi.**

## 🔥 Interview Questions

**Q1. Why is cosine similarity popular for embeddings?**

> Kyunki ye vectors ki **orientation** compare karta hai aur vector magnitude se less directly affected hota hai, jo often semantic representations ke liye useful hota hai.

**Q2. Cosine similarity vs Euclidean distance?**

> Cosine vector direction compare karta hai, jabki Euclidean geometric distance measure karta hai. Kaunsa appropriate hai ye embedding model aur retrieval setup pe depend karta hai.

**Q3. What happens if vectors are normalized?**

> Cosine similarity unke dot product ke equivalent ban jaata hai.

**Q4. Why do we need vector indexes?**

> Query ko har stored vector ke against compare karna large scale pe expensive ban jaata hai, isliye approximate nearest-neighbor indexes search cost ko significantly reduce kar sakte hain.

**Q5. Does 0.9 cosine similarity always mean "90% similar"?**

> Nahi. Score ek universal percentage nahi hai. Iski interpretation embedding model, dataset, aur retrieval task pe depend karti hai.