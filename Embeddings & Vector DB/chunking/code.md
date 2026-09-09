# Chunking — Code Walkthrough (Addendum to Topic 7: Chunking Basics)

*Isse apni Topic 7 notes.md ke end mein append kar de — ye us topic ka practical/code companion hai.*

## 1. Basic Fixed-Size Chunking

Sabse simple version, bina overlap ke:

```python
def chunk_text(text, chunk_size=500):
    chunks = []

    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)

    return chunks


text = "A" * 1200

chunks = chunk_text(text, 500)

for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {len(chunk)} characters")
```

Output:

```
Chunk 0: 500 characters
Chunk 1: 500 characters
Chunk 2: 200 characters
```

Simple hai — bas har `chunk_size` characters pe cut karta ja raha hai, koi overlap nahi.

## 2. Overlap Wala Actual Implementation ⭐

**Ye zyada important hai.**

```python
def chunk_text(text, chunk_size=500, overlap=100):

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be between 0 and chunk_size"
        )

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start = end - overlap

    return chunks
```

Ab:

```python
text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 50

chunks = chunk_text(
    text,
    chunk_size=100,
    overlap=20
)

for i, chunk in enumerate(chunks):
    print(
        f"Chunk {i}: "
        f"length={len(chunk)}, "
        f"start='{chunk[:10]}', "
        f"end='{chunk[-10:]}'"
    )
```

Conceptually:

```
Original:

0------------------------------------------------100
                  Chunk 0
                  ↑

80------------------------------------------------180
                  Chunk 1
                  ↑
          20 chars overlap

160-----------------------------------------------260
                  Chunk 2
```

Kyunki:

```python
start = end - overlap
```

Agar:

```
chunk_size = 100
overlap    = 20
```

phir:

```
Chunk 0 → 0   - 99
Chunk 1 → 80  - 179
Chunk 2 → 160 - 259
```

Toh 20 characters consecutive chunks ke beech repeat hote hain — **yehi overlap ka actual visual proof hai**, previous topic mein jo concept diagram mein dikhaya tha, wo yahan real numbers mein calculate ho raha hai.

## 3. Ek Important Cheez

Agar:

```
chunk_size = 100
overlap = 100
```

phir:

```python
start = end - overlap
```

ban jaata hai:

```
start = end - 100
      = start
```

**Matlab start aage hi nahi badhega → infinite loop.**

Isliye:

```
overlap < chunk_size
```

**mandatory validation hai** — ye wahi edge-case check hai jo Topic 7 mein already discuss kiya tha, yahan ye actually kaise fail hota hai wo dikh raha hai.

## 4. Realistic Text Example

```python
text = """
Python is a high-level programming language.
It is widely used for backend development.
FastAPI is a modern Python framework.
It can be used to build APIs.
PostgreSQL is a relational database.
It is commonly used in backend systems.
"""

chunks = chunk_text(
    text,
    chunk_size=100,
    overlap=20
)

for i, chunk in enumerate(chunks):
    print(f"\n--- CHUNK {i} ---")
    print(chunk)
```

Output roughly:

```
--- CHUNK 0 ---
Python is a high-level programming language.
It is widely used for backend development.
F

--- CHUNK 1 ---
opment.
FastAPI is a modern Python framework.
It can be used to build APIs.
PostgreSQL is a rela

--- CHUNK 2 ---
a relational database.
It is commonly used in backend systems.
```

**Aur yahin problem samajh:**

Character chunking technically kaam kar raha hai, lekin words/sentences beech mein cut ho sakte hain — dekh, "FastAPI" ka "F" Chunk 0 mein reh gaya aur baaki "opment." Chunk 1 mein aa raha hai (ye actually "development." se cut hua tha).

**Yehi wajah hai ki production RAG mein hum eventually use karte hain:**

```
Character chunking
        ↓
Token chunking
        ↓
Sentence/paragraph chunking
        ↓
Structure-aware chunking
```

data pe depend karte hue.

## 5. Bonus: Paragraph-Based Simple Chunker

```python
def paragraph_chunker(text, max_chars=500):

    paragraphs = text.split("\n\n")

    chunks = []
    current = ""

    for paragraph in paragraphs:

        if len(current) + len(paragraph) <= max_chars:
            current += paragraph + "\n\n"

        else:
            if current:
                chunks.append(current.strip())

            current = paragraph + "\n\n"

    if current:
        chunks.append(current.strip())

    return chunks
```

Ye:

```
Paragraph 1
Paragraph 2
Paragraph 3
Paragraph 4
```

ko blindly characters pe nahi kaatega; **paragraph boundaries preserve karne ki koshish karega** — jab tak ek paragraph add karne se `max_chars` cross na ho, current chunk mein add karta jaayega, warna naya chunk start kar dega.

## Abhi Ke Liye Ye Hierarchy Yaad Rakh

```
Fixed character chunks
        ↓
Overlap
        ↓
Token-based chunks
        ↓
Sentence / paragraph chunks
        ↓
Structure-aware chunks
        ↓
Production RAG
```

**Important:** Upar wala `chunk_text()` learning ke liye hai. Production mein main recommend karunga ki tokenization aur document structure ko explicitly handle karein, especially jab hum RAG banayenge.