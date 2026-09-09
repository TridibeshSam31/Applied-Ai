# Chunking Basics 🧩 — Phase 3: Embeddings + Vector DB

Chunking RAG ke liye sabse important concepts mein se ek hai, kyunki:

> **bad chunking → bad retrieval → bad answers**

## 1. Chunking Ki Zarurat Kyun Hai?

Maan le tere paas ek 100-page document hai.

**Tu simply poore document ke liye ek embedding nahi bana sakta aur good retrieval expect nahi kar sakta.**

Example:

```
Company Policy
 ├── Leave Policy
 ├── Work From Home
 ├── Salary
 ├── Promotion
 ├── Security
 └── Reimbursement
```

User poochta hai:

```
"How many casual leaves can I take?"
```

Agar poore 100-page document ka ek hi embedding hai, to vector document ke overall meaning ko represent karta hai.

Ye precisely represent **nahi** karta:

```
"Employees get X casual leaves..."
```

Iske bajaye:

```
100-page document
       ↓
    1 vector
       ↓
very broad representation
```

Humein chahiye:

```
100-page document
       ↓
   split into chunks
       ↓
 ┌─────┬─────┬─────┬─────┐
 C1    C2    C3    C4   ...
       ↓
 embedding for each chunk
       ↓
vector database
```

Phir:

```
Query
 "How many casual leaves?"
        ↓
     embedding
        ↓
Vector Search
        ↓
Relevant chunk
        ↓
LLM
```

**Yehi RAG ki foundation hai.**

## 2. Chunk Exactly Kya Hai?

**Ek chunk ek bade document ka chhota piece hota hai.**

Example:

Original document:

```
Employees are entitled to 18 casual leaves per year.
Casual leaves cannot be carried forward.
Employees should apply for leave through the HR portal.
...
```

Ye ban sakta hai:

```
Chunk 1:
Employees are entitled to 18 casual leaves per year.
Casual leaves cannot be carried forward.

Chunk 2:
Employees should apply for leave through the HR portal.
...
```

**Har chunk ko apna embedding milta hai.**

## 3. Fundamental Trade-Off

**Ye BAHUT important hai.**

### Chunks Bahut Chhote

Example:

```
Chunk:
"18 casual leaves"
```

Tu important context lose kar sakta hai.

Shayad actual sentence tha:

```
"Employees are entitled to 18 casual leaves per year, subject to manager approval."
```

Agar tu badly split karta hai:

```
Chunk 1:
Employees are entitled to

Chunk 2:
18 casual leaves per year

Chunk 3:
subject to manager approval
```

Retrieval sirf ye find kar sakta hai:

```
18 casual leaves per year
```

aur qualification lose kar sakta hai.

### Chunks Bahut Bade

Maan le:

```
Chunk = 10,000 tokens
```

Isme hai:

```
Leave
Salary
Promotion
Security
Travel
Reimbursement
...
```

Query:

```
"What is the leave policy?"
```

Ab embedding kai different topics represent karta hai.

**Retrieval less precise ban jaata hai.**

Aur:

```
Large chunks
   ↓
more tokens sent to LLM
   ↓
higher cost
   ↓
more context
   ↓
potentially worse signal/noise
```

Toh:

```
Too small ←────── Sweet Spot ──────→ Too large
context loss                         dilution
```

**Koi universal perfect chunk size nahi hoti.**

Tu isse apne actual data ke against benchmark karta hai.

## 4. Fixed-Size Chunking

Sabse simple strategy.

Example:

```
chunk_size = 500 characters
overlap = 100 characters
```

Document:

```
ABCDEFGHIJKLMNOPQRSTUVWXYZ...
```

approximately ban jaata hai:

```
Chunk 1:
[0 ---------------- 500]

Chunk 2:
[400 --------------- 900]

Chunk 3:
[800 -------------- 1300]
```

Notice kar:

```
100 characters
       ↑
    overlap
```

## 5. Overlap Kyun?

Consider kar:

```
Chunk 1
-------------------------
The employee must submit
the leave request through
the HR portal before taking
any planned leave.
-------------------------

Chunk 2
-------------------------
any planned leave. Requests
made after the leave begins
may be rejected.
-------------------------
```

**Overlap boundaries ke around information preserve karta hai.**

Overlap ke bina:

```
Chunk 1 → "before taking any planned leave"
Chunk 2 → "Requests made after..."
```

Overlap ke saath:

```
Chunk 1 → ...planned leave.
Chunk 2 → planned leave. Requests made...
```

Toh overlap boundary information loss reduce karta hai.

Ek commonly discussed starting point roughly 10–20% ho sakta hai, lekin isse ek rule ki tarah treat mat kar. **Isse retrieval quality, document type, aur cost ke basis pe tune kar.**

## 6. Character vs Token Chunking

Do different cheezein hain jinhe log often confuse karte hain.

### Character-Based

```python
text[0:1000]
```

matlab:

```
1000 characters
```

### Token-Based

```
500 tokens
```

matlab 500 tokenizer units.

**Ye equivalent nahi hain.**

LLM systems ke liye, token-based chunking generally more predictable hai kyunki model context limits aur costs tokens mein measure hote hain.

## 7. Simple Character Chunker

Learning ke liye:

```python
def chunk_text(text, chunk_size=500, overlap=100):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]
        chunks.append(chunk)

        start = end - overlap

    return chunks
```

Example:

```python
text = "A" * 1200

chunks = chunk_text(
    text,
    chunk_size=500,
    overlap=100
)

for i, chunk in enumerate(chunks):
    print(i, len(chunk))
```

Conceptually:

```
1200 characters

Chunk 0 → 0–499
Chunk 1 → 400–899
Chunk 2 → 800–1199
```

## 8. Ek Important Bug Samajh

Is implementation ko valid parameters chahiye.

Agar:

```
overlap >= chunk_size
```

phir:

```python
start = end - overlap
```

forward move karne mein fail ho sakta hai — infinite loop ban sakta hai.

Toh production code ko validate karna chahiye:

```python
def chunk_text(text, chunk_size=500, overlap=100):

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be >= 0 and < chunk_size"
        )

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size
        chunks.append(text[start:end])

        start = end - overlap

    return chunks
```

**Is tarah ka edge-case thinking hi working code ko engineering code se alag karta hai.**

## 9. Sentence-Based Chunking

Blindly har 500 characters pe cut karne ke bajaye:

```
Sentence 1.
Sentence 2.
Sentence 3.
Sentence 4.
```

Hum sentences preserve karne ki koshish karte hain.

Example:

```
Chunk 1:
Sentence 1.
Sentence 2.
Sentence 3.

Chunk 2:
Sentence 4.
Sentence 5.
Sentence 6.
```

Ye generally isse better hai:

```
Sentence 1. Sentence 2. Sen
tence 3. Sentence 4...
```

kyunki semantic units saath rehte hain.

## 10. Paragraph-Based Chunking

Kai documents ke liye aur bhi better:

```
Heading

Paragraph 1...

Paragraph 2...

Paragraph 3...
```

Paragraphs ko saath rakhne ki koshish kar.

Example:

```
Chunk 1
---------
Heading: Leave Policy

Paragraph 1
Paragraph 2
---------

Chunk 2
---------
Heading: Work From Home

Paragraph 1
Paragraph 2
---------
```

## 11. Structure-Aware Chunking ⭐

**Yahan real systems zyada interesting ban jaate hain.**

Sirf ye mat poochh:

```
"How many characters?"
```

Ye poochh:

```
"What is the natural semantic/structural unit of this document?"
```

Example, ek technical document:

```
# Authentication

## JWT

Explanation...

## Refresh Tokens

Explanation...

# Authorization

## RBAC

Explanation...
```

Ek good chunker preserve kar sakta hai:

```
Heading
  ↓
Subheading
  ↓
Content
```

randomly usse cutting through karne ke bajaye.

## 12. Code Ko Special Treatment Chahiye

Maan le tu apna Semantic Code Search system bana raha hai.

Ye mat kar:

```
characters 0–500
characters 500–1000
```

Tujhe accidentally mil sakta hai:

```python
def authenticate_user(
```

ek chunk mein aur:

```python
    username,
    password
):
    ...
```

doosre mein.

**Bad.**

Code ke liye, natural boundaries ho sakte hain:

```
File
 ↓
Class
 ↓
Function
 ↓
Method
```

Example:

```
Chunk:
File: auth.py
Class: AuthService
Function: authenticate_user()

<entire function>
```

Ye embedding ko kaafi zyada behtar semantic context deta hai.

## 13. Metadata Extremely Important Hai

Har chunk sirf ye nahi hona chahiye:

```
"text"
```

Tujhe metadata store karna chahiye.

Example:

```json
{
    "chunk_id": "doc123_chunk_07",
    "doc_id": "doc123",
    "text": "Employees are entitled...",
    "section": "Leave Policy",
    "page": 14,
    "source": "employee_handbook.pdf",
    "version": "2026.1",
    "position": 7
}
```

Baad mein tu isse use karega:

```
Filtering
Citations
Access control
Debugging
Re-ranking
Document updates
```

Multi-tenant systems ke liye, tujhe ye bhi chahiye ho sakta hai:

```
tenant_id
permissions
```

## 14. Chunk ID vs Document ID

Inhe confuse mat kar.

```
Document
   ↓
doc_123
   │
   ├── chunk_0
   ├── chunk_1
   ├── chunk_2
   └── chunk_3
```

Toh:

```
doc_id = doc_123
chunk_id = doc_123_chunk_2
```

**Document tujhe batata hai ki wo kahan se aaya.**

**Chunk tujhe batata hai ki kaunsa piece.**

## 15. Parent-Child Chunking

Ek aur useful concept.

Maan le:

```
Parent:
"Leave Policy"
```

isme hai:

```
Child 1 → Casual Leave
Child 2 → Sick Leave
Child 3 → Earned Leave
Child 4 → Carry Forward
```

Tu precision ke liye ek chhota child chunk retrieve kar sakta hai lekin phir LLM ko ek bada parent context provide kar sakta hai.

Conceptually:

```
             Document
                │
          Parent Section
                │
      ┌─────────┼─────────┐
      ↓         ↓         ↓
   Child 1   Child 2   Child 3
```

Ye is trade-off ko solve karne mein madad karta hai:

```
small chunk → precise retrieval
large context → better understanding
```

## 16. Chunking RAG Ko Directly Affect Karta Hai

Yaad hai poora pipeline?

```
Document
   ↓
Parsing
   ↓
Chunking
   ↓
Embedding
   ↓
Vector DB
   ↓
Query embedding
   ↓
Similarity Search
   ↓
Top-K chunks
   ↓
Context construction
   ↓
LLM
   ↓
Answer
```

Isliye:

```
Bad chunking
     ↓
Bad embeddings
     ↓
Bad retrieval
     ↓
Bad context
     ↓
Bad answer
```

**Yehi wajah hai ki RAG quality sirf ek better LLM choose karne ke baare mein nahi hai.**

## 17. Chunk Size Kaise Choose Kare?

Ye yaad mat kar:

```
"Always use 500 tokens."
```

**Ye bad engineering hai.**

Iske bajaye test kar:

```
Chunk size
256
512
768
1024
```

aur shayad different overlaps.

Phir retrieval measure kar:

```
Recall@K
MRR
Precision@K
Answer correctness
Latency
Token cost
```

Example:

| Chunk | Recall@5 | p95 latency | Cost |
|---|---|---|---|
| 256 | 82% | 100ms | Low |
| 512 | 89% | 115ms | Medium |
| 768 | 91% | 130ms | Medium |
| 1024 | 90% | 150ms | High |

Tu probably 768 investigate karega, blindly sabse bada chunk choose karne ke bajaye.

## 18. Interview-Level Answer

**Interviewer:**

> "Why do we chunk documents before embedding?"

**Good answer:**

> "Kyunki ek poore large document ko embed karna ek broad representation produce karta hai aur retrieval ko less precise banata hai. Chunking chhote semantically meaningful units create karti hai, jisse hum document ke relevant portion ko retrieve kar sakein. Chunk size aur overlap context preservation, retrieval precision, latency, aur token cost ke beech trade-offs hain, isliye inhe ek representative evaluation dataset ke against tune kiya jaana chahiye."

**Ye ek strong answer hai.**

## 19. Common Mistakes ❌

### Mistake 1

> Bade chunks hamesha better hote hain.

❌ **Nahi.**

### Mistake 2

> Chhote chunks hamesha better hote hain.

❌ **Nahi.**

### Mistake 3

> 20% overlap mandatory hai.

❌ **Nahi.** Ye sirf ek possible starting point hai.

### Mistake 4

> Chunking sirf har N characters pe text split karna hai.

❌ Production systems ko document structure consider karna chahiye.

### Mistake 5

> Chunking matter nahi karti agar embedding model acha hai.

❌ Retrieval quality heavily chunk quality pe depend karti hai.

### Mistake 6

> Metadata optional hai.

❌ Production RAG mein, metadata filtering, citations, permissions aur debugging ke liye extremely useful ban jaata hai.

## 20. Wo Mental Model Jo Tujhe Yaad Rakhna Chahiye

```
              DOCUMENT
                  │
          ┌───────┴───────┐
          │   CHUNKING    │
          └───────┬───────┘
                  │
       ┌──────────┼──────────┐
       ↓          ↓          ↓
     Chunk 1    Chunk 2    Chunk 3
       │          │          │
       ↓          ↓          ↓
   Embedding  Embedding  Embedding
       │          │          │
       └──────────┼──────────┘
                  ↓
             VECTOR DB
```

**Core principle:**

> **Chunk for retrieval, not merely for storage.**
>
> Chunking retrieval ke liye kar, sirf storage ke liye nahi.

Yehi key idea hai.