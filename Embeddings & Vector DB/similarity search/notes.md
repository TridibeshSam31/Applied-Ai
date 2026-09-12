# pgvector 🚀 — Phase 3: Embeddings + Vector DB

Ab theory ko **actual PostgreSQL implementation** se connect karte hain.

Tumhe ye samajhna hai:

> PostgreSQL ko vector database ki tarah kaise use karte hain?

## 1. pgvector Kya Hai?

**pgvector PostgreSQL ka extension hai** jo PostgreSQL ko:

```
vector store karne
vector similarity calculate karne
nearest-neighbor search karne
vector indexes banane
```

ki capability deta hai.

Architecture:

```
PostgreSQL
   │
   ├── users
   ├── documents
   ├── permissions
   └── document_chunks
          │
          └── embedding VECTOR(...)
                         ↑
                      pgvector
```

## 2. Extension Enable Karna

PostgreSQL database mein:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Check:

```sql
SELECT * FROM pg_extension
WHERE extname = 'vector';
```

Agar row aa gayi:

```
vector
```

phir pgvector enabled hai.

## 3. Table Create Karna

Maan le hum document chunks store kar rahe hain.

```sql
CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,

    document_id BIGINT NOT NULL,

    content TEXT NOT NULL,

    embedding VECTOR(3),

    metadata JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);
```

Yahan:

```
embedding VECTOR(3)
```

sirf learning ke liye 3 dimensions hain.

Real model ho sakta hai:

```
VECTOR(1536)
```

ya:

```
VECTOR(3072)
```

embedding model pe depend karte hue.

## 4. Ek Vector Insert Karte Hain

```sql
INSERT INTO document_chunks
(document_id, content, embedding, metadata)
VALUES
(
    1,
    'Python is used for backend development.',
    '[0.10, 0.20, 0.30]',
    '{"section": "backend"}'
);
```

Second:

```sql
INSERT INTO document_chunks
(document_id, content, embedding, metadata)
VALUES
(
    1,
    'FastAPI is a Python framework for building APIs.',
    '[0.11, 0.21, 0.31]',
    '{"section": "backend"}'
);
```

Third:

```sql
INSERT INTO document_chunks
(document_id, content, embedding, metadata)
VALUES
(
    2,
    'PostgreSQL is a relational database.',
    '[0.80, 0.70, 0.60]',
    '{"section": "database"}'
);
```

Ab:

```
id | content                  | embedding
---|--------------------------|----------------
1  | Python backend...        | [0.10,0.20,0.30]
2  | FastAPI Python...        | [0.11,0.21,0.31]
3  | PostgreSQL database...   | [0.80,0.70,0.60]
```

## 5. Ab Actual Vector Search 🔥

Maan le user query ka embedding hai:

```
[0.12, 0.22, 0.32]
```

Hume chahiye:

> "Is query ke closest chunks kaunse hain?"

pgvector mein cosine distance ke liye:

```sql
SELECT
    id,
    content,
    embedding <=> '[0.12, 0.22, 0.32]' AS distance
FROM document_chunks
ORDER BY embedding <=> '[0.12, 0.22, 0.32]'
LIMIT 3;
```

### `<=>` Kya Hai?

pgvector mein:

```
<=> = cosine distance
```

**Lower distance = more similar.**

Example:

```
Chunk 1 → 0.001
Chunk 2 → 0.004
Chunk 3 → 0.72
```

Phir:

```
Chunk 1
   ↓
most similar
```

## 6. Similarity vs Distance — VERY IMPORTANT

Pehle humne cosine similarity padha tha:

```
cosine similarity
higher = better
```

Lekin query mein:

```sql
ORDER BY embedding <=> query
```

hum use kar rahe hain:

```
cosine distance
lower = better
```

Relationship:

```
cosine distance = 1 - cosine similarity
```

Conceptually:

```
Similarity      Distance
   1.0    ↔       0.0    BEST
   0.8    ↔       0.2
   0.3    ↔       0.7
```

**Isliye ordering ko dhyan se samajhna** — similarity aur distance ka direction opposite hai, ye galti se mix ho sakti hai agar dhyan na diya jaaye.

## 7. Different Distance Operators

pgvector different distance concepts support karta hai.

### Cosine Distance

```
embedding <=> query_vector
```

### Euclidean / L2 Distance

```
embedding <-> query_vector
```

### Negative Inner Product

```
embedding <#> query_vector
```

**Important:**

```
<=> → cosine distance
<-> → L2 distance
<#> → negative inner product
```

Kaunsa choose karna hai ye embedding model aur retrieval setup pe depend karta hai.

## 8. Top-K Retrieval

RAG mein generally humein chahiye:

```
Top 5 relevant chunks
```

Toh:

```sql
SELECT
    id,
    content,
    embedding <=> '[0.12,0.22,0.32]' AS distance
FROM document_chunks
ORDER BY embedding <=> '[0.12,0.22,0.32]'
LIMIT 5;
```

Ye hai:

```
Query
  ↓
Query embedding
  ↓
pgvector
  ↓
similarity/distance
  ↓
sort
  ↓
LIMIT 5
  ↓
Top-5 chunks
```

**Ye basically vector retrieval ka core hai.**

## 9. Real RAG Query

Maan le user poochta hai:

```
"How do I build APIs using Python?"
```

Application:

```
User Query
    ↓
Embedding Model
    ↓
[0.12, 0.22, 0.32, ...]
    ↓
PostgreSQL + pgvector
    ↓
Top-K chunks
```

Phir:

```
Chunk 17:
FastAPI is a Python framework...

Chunk 92:
FastAPI supports...

Chunk 41:
Python backend APIs...
```

Ye chunks LLM ke liye context ban jaate hain.

## 10. pgvector + Metadata

**Yahan pe PostgreSQL really useful ban jaata hai.**

Maan le:

```
document_chunks
```

mein different companies ke documents hain.

Tu ye nahi chahta:

```
Company A user
      ↓
search Company A + Company B + Company C
```

Iske bajaye:

```sql
SELECT
    id,
    content,
    embedding <=> '[0.12,0.22,0.32]' AS distance
FROM document_chunks
WHERE metadata->>'tenant_id' = 'company_123'
ORDER BY embedding <=> '[0.12,0.22,0.32]'
LIMIT 5;
```

Ab:

```
metadata filter
       +
vector similarity
```

**Ye production RAG mein extremely important ban jaata hai** — bina iske, data leak ho sakta hai companies ke across.

## 11. Python → pgvector

Typical application architecture:

```
                FastAPI
                   │
          ┌────────┴────────┐
          │                 │
          ↓                 ↓
   Embedding API       PostgreSQL
          │                 │
          ↓                 ↓
     query vector      pgvector
                              │
                              ↓
                         Top-K chunks
```

Python:

```python
query = "How do I build APIs using Python?"

embedding = embedding_model.embed(query)
```

Maan le:

```python
embedding = [0.12, 0.22, 0.32]
```

Phir database query:

```python
cursor.execute(
    """
    SELECT
        id,
        content,
        embedding <=> %s AS distance
    FROM document_chunks
    ORDER BY embedding <=> %s
    LIMIT 5
    """,
    (embedding, embedding)
)
```

Exact parameter adaptation tere PostgreSQL driver/pgvector integration pe depend karta hai, lekin conceptually yehi application flow hai.

## 12. Ab BIG Problem: Scale

Socho:

```
100 chunks
```

No problem.

```
10,000 chunks
```

Still manageable.

Lekin:

```
10 million chunks
```

Agar PostgreSQL karta hai:

```
query
 ↓
compare against every vector
 ↓
calculate distance 10M times
 ↓
sort
```

**ye exact nearest-neighbor search hai aur expensive ban sakta hai.**

Humein indexes chahiye.

```
Millions of vectors
       ↓
Vector Index
       ↓
Fast approximate search
```

Aur yahin pe:

```
HNSW + IVF
```

aate hain.

## 13. Exact vs Approximate Search

### Exact

```
Query
 ↓
Compare with ALL vectors
 ↓
Calculate exact distance
 ↓
Sort
 ↓
Top-K
```

**Advantage:**

```
Very accurate
```

**Disadvantage:**

```
Expensive at scale
```

### Approximate

```
Query
 ↓
Vector Index
 ↓
Search promising region
 ↓
Top-K candidates
```

**Advantage:**

```
Much faster
```

**Trade-off:**

```
May sacrifice some recall
```

Ye classic:

```
                    SPEED
                      ↕
                 TRADE-OFF
                      ↕
                   RECALL
```

## 14. HNSW Index Example

Baad mein hum HNSW deeply study karenge, lekin syntax dekh le:

```sql
CREATE INDEX document_chunks_embedding_idx
ON document_chunks
USING hnsw (embedding vector_cosine_ops);
```

Ab PostgreSQL cosine-distance searches ke liye ek HNSW index use kar sakta hai.

## 15. IVF Index Example

Ek aur approach:

```sql
CREATE INDEX document_chunks_embedding_idx
ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

`lists` ki abhi fikar mat kar.

Hum properly samjhenge:

```
HNSW
vs
IVF
```

Topic 12 mein.

## 16. Ek Complete Mini Example

### Step 1

```sql
CREATE EXTENSION vector;
```

### Step 2

```sql
CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(3)
);
```

### Step 3

```sql
INSERT INTO documents (content, embedding)
VALUES
(
    'Python is a programming language.',
    '[0.1, 0.2, 0.3]'
),
(
    'FastAPI is used to build Python APIs.',
    '[0.11, 0.21, 0.31]'
),
(
    'PostgreSQL is a relational database.',
    '[0.8, 0.7, 0.6]'
);
```

### Step 4 — Query

```sql
SELECT
    content,
    embedding <=> '[0.12,0.22,0.32]' AS distance
FROM documents
ORDER BY embedding <=> '[0.12,0.22,0.32]'
LIMIT 2;
```

Result conceptually:

```
FastAPI is used to build Python APIs.     0.001
Python is a programming language.         0.002
```

Toh ye do chunks retrieve hote hain.

## 🧠 Poori Cheez Ek Picture Mein

```
              DOCUMENT
                  ↓
               CHUNKS
                  ↓
           EMBEDDING MODEL
                  ↓
             [0.1, 0.2,...]
                  ↓
        ┌───────────────────┐
        │ PostgreSQL        │
        │                   │
        │ + pgvector        │
        │                   │
        │ content           │
        │ metadata          │
        │ embedding         │
        └─────────┬─────────┘
                  │
             VECTOR SEARCH
                  ↑
                  │
            QUERY EMBEDDING
                  ↑
                  │
              USER QUERY
```

### The Key Distinction:

```
pgvector
   ↓
makes PostgreSQL capable of storing/searching vectors

HNSW / IVF
   ↓
make large-scale vector search faster
```

**Yehi conceptual boundary hai jo tujhe yaad rakhni hai.**