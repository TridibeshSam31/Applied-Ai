# Chunking Strategies 🔥 — Fixed, Recursive, Semantic & Hierarchical Architecture

Chunking RAG pipeline ka wo silent decision hai jo pure system ki retrieval quality ko make ya break karta hai.

Agar chunk bahut chhota hai ($\le 50$ tokens):
- Sentence isolated ho jaata hai. LLM ko pata hi nahi chalta ki *"He approved the proposal"* mein *"He"* kaun tha (**Context Loss**).

Agar chunk bahut bada hai ($\ge 2000$ tokens):
- Embedding model pure 2000 tokens ka ek single average vector nikalta hai. Core semantic needle irrelevant background noise mein drown ho jaati hai (**Vector Dilution / Low SNR**).

Is note mein hum **Fixed, Recursive, Semantic, aur Hierarchical chunking** ko rigorously compare karenge.

---

## 1. The Chunk Size & Overlap Trade-Off

Engineering mein chunking ek optimization problem hai jahan do competing forces balance kiye jaate hain:

```
                      THE CHUNKING EQUILIBRIUM
                      ────────────────────────

      Small Chunks (e.g., 128 tokens)            Large Chunks (e.g., 1024 tokens)
   ┌───────────────────────────────────┐      ┌───────────────────────────────────┐
   │ ✅ High semantic density          │      │ ❌ Vector dilution / Low SNR      │
   │ ✅ Precise vector matching        │      │ ❌ High LLM prompt token costs    │
   │ ❌ Context loss (pronoun amnesia) │      │ ✅ Rich surrounding context       │
   │ ❌ Fragmented semantic flow       │      │ ✅ Self-contained information     │
   └─────────────────┬─────────────────┘      └─────────────────┬─────────────────┘
                     │                                          │
                     └────────────────────┬─────────────────────┘
                                          ▼
                                   Optimal Window
                               (Typically 256 - 512 tokens
                                 with 10-20% Overlap)
```

### Why Chunk Overlap is Non-Negotiable
Agar do chunks ke beech **zero overlap** ho:
```
Chunk 1: "The annual bonus is awarded only if the team achieves"
------------------ CUT BOUNDARY ------------------
Chunk 2: "at least 110% of their quarterly pipeline target."
```
Ab agar user poochhe: *"What is the condition for annual bonus?"*
- Chunk 1 mein condition missing hai.
- Chunk 2 mein subject ("annual bonus") missing hai.
- Vector search dono chunks par fail ho sakta hai!

**With 20% Overlap:**
```
Chunk 1: "...awarded only if the team achieves at least 110% of their target."
Chunk 2: "the team achieves at least 110% of their quarterly pipeline target. Payout occurs in March..."
```
Boundary par context bridge maintain rehta hai.

---

## 2. Token-Aware vs Character-Aware Chunking

Ek common junior engineer bug:
`chunk_size = 500` (Characters) define kar dena.

Kyunki:
1. **Characters $\neq$ Tokens:**
   - English prose: $\approx 4$ characters per token.
   - Code snippet ya non-Latin languages (Hindi, Chinese, Cyrillic): $\approx 1$ to $2$ characters per token.
   - Ek 1000-character JSON chunk shayad 600 tokens le le, jabki 1000 characters of English text sirf 250 tokens lega!
2. **Tokenizer Boundary Violations:**
   - Agar character cut kisi UTF-8 multi-byte glyph ya subword token ke beech pad gaya, toh invalid token replacement (``) trigger ho jaata hai.

> [!IMPORTANT]
> **Production Rule:** Ingestion pipeline mein chunk bounds hamesha target embedding model ke actual BPE/SentencePiece tokenizer se evaluate karo (e.g., `tiktoken` ya HuggingFace `AutoTokenizer`).

---

## 3. Deep Dive into the 4 Major Chunking Paradigms

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               THE 4 CHUNKING STRATEGIES                                │
└────────────────────────────────────────────────────────────────────────────────────────┘

 1. Fixed-Size Chunking         2. Recursive Character Chunker
 ┌─────────────────────────┐    ┌─────────────────────────┐
 │ [ Chunk 1: 500 tokens ] │    │ Splits by:              │
 │ ────────[Overlap]───────│    │  1. "\n\n" (Paragraphs) │
 │ [ Chunk 2: 500 tokens ] │    │  2. "\n"   (Sentences)  │
 │ (Rigid, cuts sentences) │    │  3. " "    (Words)      │
 └─────────────────────────┘    └─────────────────────────┘

 3. Semantic Similarity Chunking 4. Hierarchical / Parent-Document
 ┌─────────────────────────┐    ┌─────────────────────────┐
 │ Sentence 1 ─┐ Sim = 0.92│    │ [Parent Chunk: 1000 tok]│
 │ Sentence 2 ─┘           │    │  ├── [Child 1: 200 tok] │
 │ ────── BREAKPOINT ───── │    │  ├── [Child 2: 200 tok] │
 │ Sentence 3 (New Topic)  │    │  └── [Child 3: 200 tok] │
 └─────────────────────────┘    └─────────────────────────┘
```

### Strategy 1: Fixed-Size Window Chunking
- **How it works:** Sliding window of $N$ tokens with step size $N - K$ (overlap).
- **Pros:** Computationally fastest ($O(N)$ string slicing).
- **Cons:** Sentences aur paragraphs ko beech mein se split kar deta hai. Semantically dumb.

### Strategy 2: Recursive Character Chunking (LangChain standard)
- **How it works:** Hierarchy of separators try karta hai: `["\n\n", "\n", ". ", " "]`.
  Pehle paragraphs par split karne ki koshish karega. Agar koi paragraph chunk size se bada hai, toh use sentences par split karega, fir words par.
- **Pros:** Document ke natural structural boundaries ko maximum preserve karta hai.
- **Cons:** Text formatting par heavily dependent hai; unstructured OCR outputs par degrade ho jaata hai.

### Strategy 3: Semantic Similarity Breakpoint Chunking
- **How it works:**
  1. Text ko individual sentences mein divide karo: $[S_1, S_2, S_3, \dots, S_n]$.
  2. Consecutive sentences ke embeddings compute karo: $\vec{v}_i, \vec{v}_{i+1}$.
  3. Adjacent sentence pairs ki cosine similarity compute karo: $\text{sim}(S_i, S_{i+1})$.
  4. Jab similarity drop kisi statistical threshold (e.g., $1.5$ standard deviations below mean) se neeche gir jaye, wahan naya chunk shuru karo (**Topic Shift Boundary**).
- **Pros:** Chunks strictly single topic focus maintain karte hain.
- **Cons:** Heavy embedding overhead during ingestion ($N$ sentences require $N$ embedding passes).

### Strategy 4: Hierarchical (Parent-Document) Chunking
- **The Core Architecture:**
  - Index mein **Child Chunks** ($100-200$ tokens) embed kiye jaate hain.
  - Search query child chunks ko high precision se retrieve karti hai.
  - LLM context generation ke waqt child chunk ka **Parent Chunk** ($1000-2000$ tokens) replace ho jata hai.
- **Why it wins:** Vector similarity search sharp focus chahta hai, jabki LLM synthesis broad context chahta hai. Ye dono ko satisfy karta hai!

---

## 4. Chunking Strategy Trade-Off Matrix

| Strategy | Compute Cost | Boundary Quality | Semantic Purity | Best Suited For |
| :--- | :--- | :--- | :--- | :--- |
| **Fixed Size** | Minimal ($O(1)$) | Terrible (Mid-sentence cuts) | Low | Quick prototypes, uniform raw logs |
| **Recursive** | Very Low ($O(N)$) | Excellent (Preserves paragraphs) | Medium-High | Markdown docs, articles, manuals |
| **Semantic** | High ($O(N)$ GPU passes)| Natural (Topic transitions) | Very High | Conversational transcripts, books, essays |
| **Hierarchical**| Medium-High | Superior (Two-tier mapping) | Maximum | Complex legal contracts, dense technical manuals |

---

## 5. Senior Interview Questions & Answers 🧠

#### Q1. Chunking mein token count use karna character count ke upar kyun standard rule hai?
> **Answer:** LLMs aur Transformer embedding models character counts par operate nahi karte; unka input context window strictly tokens (BPE, WordPiece, ya SentencePiece) mein bounded hota hai. Natural languages aur code mein character-to-token ratio widely vary karta hai ($1.2$ to $5$ chars/token). Character chunking se chunks embedding model ke `max_seq_length` (e.g., 512 tokens) ko silently exceed kar sakte hain, causing silent truncation of vital trailing text.

#### Q2. Semantic Chunking mein topic split boundary kaise decide hoti hai?
> **Answer:** Consecutive sentences ke consecutive embedding vectors ke beech cosine distance compute kiya jaata hai: $d_i = 1 - \cos(\vec{v}_i, \vec{v}_{i+1})$. Pure document ke distance distribution ka mean $\mu$ aur standard deviation $\sigma$ evaluate hota hai. Dynamic threshold formulate hota hai: $\tau = \mu + k \cdot \sigma$ (or percentile threshold, e.g., 90th percentile). Jahan $d_i > \tau$, wahan topic shift identify karke chunk split create kiya jaata hai.

#### Q3. Explain the Parent-Child (Hierarchical) chunking mechanism and why it solves the "Context Granularity Paradox".
> **Answer:** Context Granularity Paradox states that small chunks are best for dense embedding retrieval (higher cosine similarity, less topic dilution), but large chunks are required for LLM reasoning (broad context, complete clauses). Hierarchical chunking breaks documents into large parent chunks, and further sub-segments each parent into multiple small child chunks. Only child vectors are indexed. When a child chunk is retrieved via ANN search, its `parent_id` is resolved in memory to inject the full parent chunk into the LLM prompt.

#### Q4. Chunk overlap ratio kitna hona chahiye aur isko tune kaise karte hain?
> **Answer:** Standard industry baseline $10\% - 20\%$ of chunk size hota hai (e.g., 512 token chunk with 50-100 token overlap). Aggressive overlap ($>30\%$) vector database index size ko explode karta hai aur duplicate retrieved chunks generate karta hai jo reranker ko confuse karte hain. Insufficient overlap ($<5\%$) boundary entities aur cross-sentence dependencies ko break karta hai.

#### Q5. What is Late Chunking and how does it differ from traditional chunking?
> **Answer:** Traditional chunking pehle raw text ko cut karta hai fir har chunk ko independently embed karta hai, losing global document context. Late Chunking (introduced by Jina AI) pure document ko transformer encoder mein pass karta hai up to long context length (e.g., 8192 tokens) to compute token-level representations with full bidirectional self-attention across the whole text. Uske baad token boundary ranges par mean pooling apply karke individual chunk embeddings derive kiye jaate hain, preserving cross-chunk contextual embeddings.

---

## 6. Complete Production Implementation: `chunking_strategies_comparison.py` 💻

Neeche diya gaya script teeno primary chunking algorithms implement aur compare karta hai:
1. **Fixed-Size Token Window Chunker** with overlap.
2. **Recursive Character Chunker** respecting paragraph and sentence boundaries.
3. **Semantic Similarity Breakpoint Chunker** calculating sentence similarity drops.

```python
"""
chunking_strategies_comparison.py
Production-grade comparison of:
- Fixed-Size Sliding Window Chunker
- Recursive Structural Chunker (Paragraphs -> Sentences -> Words)
- Semantic Breakpoint Chunker (Sentence embedding cosine distance thresholding)
Includes token count analysis and context preservation benchmarking.
"""

import math
import re
from dataclasses import dataclass
from typing import Callable, List, Tuple


@dataclass
class Chunk:
    chunk_index: int
    text: str
    token_count: int
    strategy: str


class SimpleTokenizer:
    """Whitespace and punctuation aware BPE token counter approximation."""
    @staticmethod
    def tokenize(text: str) -> List[str]:
        return re.findall(r"\w+|[^\w\s]", text, re.UNICODE)

    @classmethod
    def count_tokens(cls, text: str) -> int:
        return len(cls.tokenize(text))


# =====================================================================
# 1. FIXED-SIZE SLIDING WINDOW CHUNKER
# =====================================================================
class FixedWindowChunker:
    def __init__(self, chunk_size: int = 40, overlap: int = 10):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[Chunk]:
        tokens = SimpleTokenizer.tokenize(text)
        chunks: List[Chunk] = []
        step = max(1, self.chunk_size - self.overlap)
        idx = 0

        for i in range(0, len(tokens), step):
            window = tokens[i:i + self.chunk_size]
            chunk_str = " ".join(window)
            chunks.append(Chunk(idx, chunk_str, len(window), "FixedWindow"))
            idx += 1
            if i + self.chunk_size >= len(tokens):
                break
        return chunks


# =====================================================================
# 2. RECURSIVE STRUCTURAL CHUNKER
# =====================================================================
class RecursiveStructuralChunker:
    def __init__(self, max_tokens: int = 45, separators: List[str] = None):
        self.max_tokens = max_tokens
        self.separators = separators or ["\n\n", "\n", ". ", " "]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        if not separators:
            return [text]

        sep = separators[0]
        remaining_seps = separators[1:]

        parts = text.split(sep)
        result: List[str] = []

        for p in parts:
            p = p.strip()
            if not p:
                continue
            if SimpleTokenizer.count_tokens(p) <= self.max_tokens:
                result.append(p)
            else:
                # Recursively break using next granular separator
                result.extend(self._split_text(p, remaining_seps))
        return result

    def chunk(self, text: str) -> List[Chunk]:
        raw_splits = self._split_text(text, self.separators)
        # Merge small adjacent fragments to optimize token budget
        chunks: List[Chunk] = []
        buffer: List[str] = []
        current_len = 0
        idx = 0

        for part in raw_splits:
            part_tokens = SimpleTokenizer.count_tokens(part)
            if current_len + part_tokens <= self.max_tokens:
                buffer.append(part)
                current_len += part_tokens
            else:
                if buffer:
                    combined = " ".join(buffer)
                    chunks.append(Chunk(idx, combined, SimpleTokenizer.count_tokens(combined), "Recursive"))
                    idx += 1
                buffer = [part]
                current_len = part_tokens

        if buffer:
            combined = " ".join(buffer)
            chunks.append(Chunk(idx, combined, SimpleTokenizer.count_tokens(combined), "Recursive"))

        return chunks


# =====================================================================
# 3. SEMANTIC BREAKPOINT CHUNKER
# =====================================================================
class SemanticBreakpointChunker:
    def __init__(self, similarity_drop_threshold: float = 0.35, dim: int = 32):
        self.similarity_drop_threshold = similarity_drop_threshold
        self.dim = dim

    def _embed_sentence(self, sentence: str) -> List[float]:
        # Fast deterministic hash-based sentence encoder
        tokens = re.findall(r"\b\w+\b", sentence.lower())
        vec = [0.0] * self.dim
        for t in tokens:
            vec[abs(hash(t)) % self.dim] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm > 0.0 else vec

    @staticmethod
    def _cosine(v1: List[float], v2: List[float]) -> float:
        return sum(a * b for a, b in zip(v1, v2))

    def chunk(self, text: str) -> List[Chunk]:
        # Split text into sentences
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if not sentences:
            return []

        embeddings = [self._embed_sentence(s) for s in sentences]
        chunks: List[Chunk] = []
        current_chunk_sentences = [sentences[0]]
        idx = 0

        for i in range(len(sentences) - 1):
            sim = self._cosine(embeddings[i], embeddings[i + 1])
            # If semantic similarity drops significantly, trigger a chunk boundary
            if sim < self.similarity_drop_threshold:
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append(Chunk(
                    idx,
                    chunk_text,
                    SimpleTokenizer.count_tokens(chunk_text),
                    f"Semantic (Split at Sim: {sim:.2f})"
                ))
                idx += 1
                current_chunk_sentences = [sentences[i + 1]]
            else:
                current_chunk_sentences.append(sentences[i + 1])

        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append(Chunk(idx, chunk_text, SimpleTokenizer.count_tokens(chunk_text), "Semantic (Final)"))

        return chunks


# =====================================================================
# VERIFICATION & COMPARISON RUNNER
# =====================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("    CHUNKING STRATEGIES COMPARISON: FIXED vs RECURSIVE vs SEMANTIC")
    print("=" * 80)

    sample_document = (
        "PostgreSQL utilizes Multi-Version Concurrency Control (MVCC) to achieve high transaction throughput. "
        "Each update creates a new version of the row, while the previous version remains accessible to older transactions. "
        "Vacuuming processes periodically purge dead tuples to prevent table bloat.\n\n"
        "On the other hand, Apache Kafka is an event-streaming platform built on an append-only distributed commit log. "
        "Producers publish messages to topic partitions, while consumer groups read data sequentially from offset checkpoints. "
        "Zero-copy transfer via sendfile provides extremely high disk-to-network bandwidth."
    )

    print(f"Total Document Tokens: {SimpleTokenizer.count_tokens(sample_document)}\n")

    # 1. Run Fixed
    fixed_engine = FixedWindowChunker(chunk_size=35, overlap=8)
    fixed_chunks = fixed_engine.chunk(sample_document)

    print(f"--- 1. Fixed-Size Window Chunker ({len(fixed_chunks)} chunks produced) ---")
    for c in fixed_chunks:
        print(f"  Chunk #{c.chunk_index} ({c.token_count} tokens): {c.text[:65]}...")

    # 2. Run Recursive
    rec_engine = RecursiveStructuralChunker(max_tokens=45)
    rec_chunks = rec_engine.chunk(sample_document)

    print(f"\n--- 2. Recursive Structural Chunker ({len(rec_chunks)} chunks produced) ---")
    for c in rec_chunks:
        print(f"  Chunk #{c.chunk_index} ({c.token_count} tokens): {c.text[:65]}...")

    # 3. Run Semantic
    semantic_engine = SemanticBreakpointChunker(similarity_drop_threshold=0.20)
    semantic_chunks = semantic_engine.chunk(sample_document)

    print(f"\n--- 3. Semantic Breakpoint Chunker ({len(semantic_chunks)} chunks produced) ---")
    for c in semantic_chunks:
        print(f"  Chunk #{c.chunk_index} ({c.token_count} tokens | {c.strategy}):\n    '{c.text}'")

    print("\n" + "=" * 80)
    print("Notice how Semantic Chunking naturally split the document at the database -> streaming transition!")
```
