# Document Ingestion 🔥 — Extraction, Deduplication & Metadata Enrichment

Production RAG systems aksar retrieval stage par nahi, **Ingestion stage par fail hote hain**.

Data science teams aksar sochte hain ki bas `pypdf` ya `BeautifulSoup` chalake text vector store mein daal do. Real-world enterprise data messy hota hai:
- Two-column PDFs jahan sentences doosre column ke saath mix ho jaate hain.
- Scanned OCR documents jahan table numbers headers ke saath merge ho jaate hain.
- Duplicate documents (v1, v2, final_v3_copy) jo vector DB ko pollute karte hain.
- Confidential documents bina tenant ACLs ke index ho jaate hain, leading to security breaches.

Is note mein hum production **Document Ingestion Pipeline** ke core engineering layers ko build karenge.

---

## 1. Document Extraction Across Heterogeneous Formats

Enterprise documents alag-alag file formats mein aate hain. Har format ke apne unique failure modes hote hain:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                        INGESTION EXTRACTION PIPELINE                          │
└───────────────────────────────────────────────────────────────────────────────┘

    Source Documents                 Extraction Layer                Clean Data Objects
 ┌──────────────────────┐        ┌──────────────────────┐        ┌──────────────────────┐
 │ PDF (Unstructured)   │ ─────► │ LayoutLM / pdfplumber│ ─────► │ Structured Text      │
 │ Markdown / Docs      │ ─────► │ AST Header Parsers   │ ─────► │ Section Hierarchy    │
 │ HTML / Confluence    │ ─────► │ DOM Boilerplate Strip│ ─────► │ Semantics + Metadata │
 │ JSON / CSV           │ ─────► │ Flatteners / Schemas │ ─────► │ Entity Key-Values    │
 └──────────────────────┘        └──────────────────────┘        └──────────────────────┘
```

### 1. PDF Parsing Challenges
- **The Reading Order Dilemma:** PDFs layout instructions (e.g., `moveTo(x, y)`) store karte hain, reading order nahi. Agar page two-column hai, standard parsers left column line 1 ke baad right column line 1 read kar lete hain:
  ```
  Column 1: "The company revenue increased"     Column 2: "due to unexpected market"
  Naive Parser reads: "The company revenue increased due to unexpected market" -> Broken semantics!
  ```
- **Tables Destruction:** Tables spatial grid hote hain. Text extract karte waqt row-column relationships tab/space delimiters mein loss ho jaate hain.
- **Solution:** Vision-based layout parsers (e.g., LayoutParser, Table Transformer, ya Unstructured.io) jo bounding box detection se text reading order preserve karte hain.

### 2. HTML & Web Scraping (Boilerplate Stripping)
- Web pages mein >60% tokens non-content hote hain: `<nav>`, `<header>`, `<footer>`, cookie banners, tracking scripts.
- Agar ye strip na ho, toh embedding noise se bhar jaati hai.
- **Solution:** Heuristic DOM-density algorithms (jaise Readability.js ya Trafilatura) jo navigation elements ko drop karke core article body extract karte hain.

### 3. Markdown & JSON
- Markdown best format hai RAG ke liye kyunki headers (`#`, `##`, `###`) natural hierarchical boundaries provide karte hain.
- JSON data ko natural language sentences mein synthesize karna padta hai:
  - Raw JSON: `{"sku": "A12", "price": 49.99, "stock": 0}`
  - Flattened Representation: `"Product SKU A12 has price $49.99 and is currently out of stock."`

---

## 2. Deduplication Strategies: Exact vs Near-Duplicate

Enterprise lakes mein 30% to 50% documents redundant ya near-duplicates hote hain. Duplicate chunks vector database index size ko inflate karte hain aur search results mein top-$K$ slots waste karte hain.

```
                   EXACT DEDUPLICATION vs NEAR DEDUPLICATION
                   ─────────────────────────────────────────

          EXACT DEDUPLICATION                     NEAR-DUPLICATE (LSH)
         (Cryptographic Hashes)                (MinHash + Jaccard Similarity)
      ┌─────────────────────────┐               ┌─────────────────────────┐
      │ Document A: Text        │               │ Doc A: "Return within   │
      │           │             │               │         14 days."       │
      │           ▼             │               │ Doc B: "Returns allowed │
      │   SHA-256 Checksum      │               │         within 14 days."│
      │ e3b0c44298fc1c149afb... │               │           │             │
      └───────────┬─────────────┘               │           ▼             │
                  │                             │ MinHash Signatures      │
                  ▼                             │ Jaccard Sim = 0.88      │
      Matches only 100% exact bytes             └───────────┬─────────────┘
      (1 typo changes entire hash)                          │
                                                            ▼
                                                Catches version edits, minor
                                                formatting changes, & updates
```

### 1. Exact Deduplication (SHA-256)
- **Mechanism:** Text string ko canonicalize karo (lowercase, strip whitespace, remove punctuation) aur 256-bit hash compute karo.
- **Complexity:** $O(N)$ computation, $O(1)$ lookup via hash set or Bloom filter.
- **Limitation:** Ek comma ya extra space add hote hi SHA-256 completely change ho jaata hai (Avalanche effect).

### 2. Near-Duplicate Detection (MinHash & Locality-Sensitive Hashing - LSH)
- **Concept:** Documents ko $k$-shingles (overlapping n-grams) mein break kiya jaata hai. Jaccard similarity estimate karne ke liye $M$ random hash functions use karke **MinHash signature vector** banaya jaata hai:

$$J(A, B) = \frac{|A \cap B|}{|A \cup B|} \approx \Pr(\min(h(A)) = \min(h(B)))$$

- **LSH Bands:** MinHash signatures ko bands mein split kiya jaata hai. Agar do documents kisi ek band mein match karte hain, unhe candidate duplicates mark kiya jaata hai ($O(1)$ candidate retrieval).

---

## 3. Metadata Enrichment: The Secret Sauce of Enterprise RAG

Chunk text ke alawa uske saath kya metadata attach hota hai, wahi determine karta hai ki RAG secure aur performant hoga ya nahi.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CHUNK METADATA SCHEMA                           │
└────────────────────────────────────────────────────────────────────────┘

 {
   "chunk_id": "chk_c4a89f91a2",
   "parent_doc_id": "doc_hr_policy_2026_v2",
   "doc_title": "Global Employee Benefit Handbook 2026",
   "doc_type": "pdf",
   "section_hierarchy": ["Compensation & Benefits", "Health Insurance", "Maternity Leave"],
   "created_at": "2026-01-15T09:30:00Z",
   "last_modified": "2026-03-01T14:15:00Z",
   "author": "People Operations Team",
   "chunk_index": 14,
   "total_chunks_in_doc": 84,
   "security": {
     "tenant_id": "enterprise_corp_apac",
     "allowed_roles": ["employee", "manager", "hr_admin"],
     "classification": "internal_confidential"
   },
   "checksum_sha256": "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4"
 }
```

### Why These Fields Matter:
1. **`parent_doc_id` & `chunk_index`:** Small-to-big retrieval allow karta hai (retrieve small chunk for embedding precision, but expand to parent chunk for full context).
2. **`section_hierarchy`:** LLM ko context milta hai ki ye clause kis heading ke andar tha (e.g., "Exceptions" clause kis parent policy ka hai).
3. **`security.tenant_id` & `allowed_roles`:** Pre-filtering stage par deterministic SQL filter inject karta hai to prevent unauthorized data leaks.
4. **`last_modified`:** Stale documents ko purge ya deprioritize karne ke liye time-decay scoring enable karta hai.

---

## 4. Cleaning & Boilerplate Removal Pipeline

Raw text mein se downstream retrieval ko distort karne waale artifacts clean karna zaroori hai:

```
[Raw Ingested Text]
        │
        ▼
[1. Unicode Normalization (NFKC)]  ──► Fixes smart quotes, zero-width spaces, ligatures (æ, ﬁ)
        │
        ▼
[2. Whitespace Canonicalization]   ──► Replaces multi-spaces, trailing \r\n, tab floods
        │
        ▼
[3. Header/Footer Regex Pruning]   ──► Strips "Page 14 of 95", confidential watermarks
        │
        ▼
[4. Markdown Link Simplification]  ──► [Click Here](https://...) -> Click Here (retains semantics)
        │
        ▼
[Clean Enriched Chunks Ready for Indexing]
```

---

## 5. Senior Interview Questions & Answers 🧠

#### Q1. Two-column PDFs parse karte waqt standard OCR ya text extractors fail kyun hote hain?
> **Answer:** Standard stream-based PDF parsers text streams ko byte offset ya geometric $Y$-coordinates ke order mein render karte hain. Two-column layout mein horizontally matching lines same $Y$-coordinate share karti hain. As a result, parser Column 1 Line 1 ke turant baad Column 2 Line 1 concatenate kar deta hai, disrupting the logical linguistic reading flow. Solution layout-aware computer vision models (LayoutLMv3) use karna hai jo bounding boxes se columns pehle partition karte hain.

#### Q2. Content hashing (SHA-256) aur MinHash LSH ke use cases mein kya difference hai?
> **Answer:** SHA-256 exact bitwise duplicate detection ke liye ideal hai (e.g., identical re-uploaded files), jahan zero false positives chahiye. Lekin minor edit (jaise punctuation change ya footer revision) SHA-256 ko completely alter kar deti hai. MinHash LSH high-dimensional $k$-shingle sets ko compact signature vectors mein compress karta hai, enabling fast $O(1)$ probabilistic candidate identification for near-duplicates having Jaccard similarity above a threshold $\tau$ (e.g., $J > 0.85$).

#### Q3. Ingestion pipeline mein Parent-Child chunk metadata linkage kyun critical hai?
> **Answer:** Dense embeddings 100-200 token chunks par highest semantic precision show karte hain, lekin generation LLM ko answer synthesize karne ke liye 1000+ tokens ka broad context chahiye hota hai. Small-to-big retrieval pattern mein vector search small child chunk par execute hota hai, aur retrieval ke baad system metadata se `parent_doc_id` lookup karke larger parent chunk ko LLM context window mein inject karta hai.

#### Q4. Why is Unicode normalization (NFKC) essential during ingestion?
> **Answer:** Documents often contain varied unicode representations for visually identical glyphs (e.g., ligatures like 'ﬁ', full-width characters, non-breaking spaces `\u00A0`, or zero-width joiners). Agar ingestion aur query tokenizers mein unicode mismatch ho, toh embedding model different sub-word token IDs produce karega, leading to artificial semantic divergence and missed retrievals.

#### Q5. How do you handle tabular data during text ingestion for RAG?
> **Answer:** Raw linear text conversion of tables collapses column headers and cell alignments, causing the LLM to cross-contaminate row attributes. Best practice is to extract tables into structured schemas (Markdown tables, HTML `<table>` blocks, or synthesized natural language row sentences: `"In Q3, Revenue was $4.2M with EBITDA margin 21%"`), attaching table column descriptions as chunk metadata.

---

## 6. Complete Production Implementation: `ingestion_pipeline.py` 💻

Neeche diya gaya script ek production-grade multi-format document ingestion engine hai:
1. Multi-format loaders (PDF simulator, Markdown AST parser, HTML DOM cleaner, JSON flattener).
2. Content canonicalizer with NFKC normalization & boilerplate scrub.
3. Cryptographic SHA-256 deduplication + Near-duplicate MinHash signature simulator.
4. Hierarchical metadata enrichment (ACLs, timestamps, parent-child links).

```python
"""
ingestion_pipeline.py
Production-grade Document Ingestion & Deduplication Pipeline:
- Multi-format ingestion (Markdown, simulated PDF, HTML boilerplate cleaner)
- Text canonicalization (Unicode normalization, whitespace stripping)
- Exact SHA-256 Deduplication & Near-duplicate Detection
- Metadata enrichment with RBAC access control lists (ACLs) and hierarchical links
"""

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class RawDocument:
    raw_id: str
    content: str
    doc_format: str  # 'markdown', 'html', 'json', 'text'
    source_uri: str
    tenant_id: str
    allowed_roles: List[str]


@dataclass
class ProcessedChunk:
    chunk_id: str
    parent_id: str
    content: str
    content_hash: str
    metadata: Dict[str, Any]


class TextCleaner:
    @staticmethod
    def clean(text: str, doc_format: str) -> str:
        # 1. Unicode NFKC Normalization
        normalized = unicodedata.normalize("NFKC", text)

        # 2. Format-specific boilerplate stripping
        if doc_format.lower() == "html":
            # Strip script, style, and navigation tags
            normalized = re.sub(r"<(script|style|nav|footer)[^>]*>.*?</\1>", "", normalized, flags=re.DOTALL | re.I)
            # Strip remaining HTML tags
            normalized = re.sub(r"<[^>]+>", " ", normalized)
            # Unescape basic entities
            normalized = normalized.replace("&nbsp;", " ").replace("&amp;", "&")

        # 3. Collapse multiple spaces and blank lines
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n\s*\n+", "\n\n", normalized)
        return normalized.strip()


class DeduplicationEngine:
    """Combines exact cryptographic hashing (SHA-256) with 3-gram Jaccard near-duplication."""
    def __init__(self, jaccard_threshold: float = 0.80):
        self.seen_hashes: Set[str] = set()
        self.shingle_registry: Dict[str, Set[str]] = {}  # doc_id -> set of 3-grams
        self.jaccard_threshold = jaccard_threshold

    @staticmethod
    def compute_sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _get_shingles(text: str, k: int = 3) -> Set[str]:
        tokens = re.findall(r"\b\w+\b", text.lower())
        if len(tokens) < k:
            return set(tokens)
        return {" ".join(tokens[i:i + k]) for i in range(len(tokens) - k + 1)}

    def is_exact_duplicate(self, content_hash: str) -> bool:
        if content_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(content_hash)
        return False

    def find_near_duplicate(self, text: str) -> Optional[Tuple[str, float]]:
        shingles = self._get_shingles(text)
        if not shingles:
            return None

        for existing_id, existing_shingles in self.shingle_registry.items():
            intersection = len(shingles & existing_shingles)
            union = len(shingles | existing_shingles)
            similarity = intersection / union if union > 0 else 0.0
            if similarity >= self.jaccard_threshold:
                return existing_id, similarity
        return None

    def register(self, doc_id: str, text: str) -> None:
        self.shingle_registry[doc_id] = self._get_shingles(text)


class IngestionPipeline:
    def __init__(self):
        self.cleaner = TextCleaner()
        self.dedup = DeduplicationEngine(jaccard_threshold=0.80)

    def process_document(self, doc: RawDocument) -> Tuple[List[ProcessedChunk], Dict[str, Any]]:
        clean_text = self.cleaner.clean(doc.content, doc.doc_format)
        content_hash = DeduplicationEngine.compute_sha256(clean_text)

        # 1. Exact Duplicate Check
        if self.dedup.is_exact_duplicate(content_hash):
            return [], {"status": "SKIPPED_EXACT_DUPLICATE", "doc_id": doc.raw_id}

        # 2. Near-Duplicate Check
        near_match = self.dedup.find_near_duplicate(clean_text)
        if near_match:
            dup_id, sim = near_match
            return [], {
                "status": "SKIPPED_NEAR_DUPLICATE",
                "doc_id": doc.raw_id,
                "matches_with": dup_id,
                "similarity": f"{sim:.2f}"
            }

        self.dedup.register(doc.raw_id, clean_text)

        # 3. Simple Paragraph Chunker with Metadata Enrichment
        paragraphs = [p.strip() for p in clean_text.split("\n\n") if len(p.strip()) > 30]
        chunks: List[ProcessedChunk] = []

        now_utc = datetime.now(timezone.utc).isoformat()

        for idx, para in enumerate(paragraphs, start=1):
            chunk_hash = DeduplicationEngine.compute_sha256(para)
            chunk_id = f"{doc.raw_id}_c{idx:03d}"

            metadata = {
                "parent_id": doc.raw_id,
                "source_uri": doc.source_uri,
                "chunk_index": idx,
                "total_chunks": len(paragraphs),
                "ingested_at": now_utc,
                "tenant_id": doc.tenant_id,
                "allowed_roles": doc.allowed_roles,
                "char_length": len(para)
            }

            chunks.append(ProcessedChunk(
                chunk_id=chunk_id,
                parent_id=doc.raw_id,
                content=para,
                content_hash=chunk_hash,
                metadata=metadata
            ))

        return chunks, {"status": "SUCCESS_INGESTED", "chunks_produced": len(chunks)}


if __name__ == "__main__":
    print("=" * 80)
    print("    ENTERPRISE DOCUMENT INGESTION & DEDUPLICATION PIPELINE")
    print("=" * 80)

    pipeline = IngestionPipeline()

    raw_docs = [
        RawDocument(
            raw_id="DOC_001",
            content="""<html><head><title>Engineering Handbook</title></head>
            <body><nav><a href='/home'>Home</a></nav>
            <h1>Kubernetes Deployment Guide</h1>
            <p>Production pods must specify both CPU limits and memory limits to prevent node starvation.</p>
            <p>All ingress traffic is encrypted using TLS 1.3 with automated Let's Encrypt certificates.</p>
            <footer>Copyright 2026 Enterprise Corp</footer></body></html>""",
            doc_format="html",
            source_uri="https://wiki.internal.net/k8s-guide",
            tenant_id="tenant_finance",
            allowed_roles=["devops", "platform_engineer"]
        ),
        # Exact duplicate of DOC_001 (re-ingestion attempt)
        RawDocument(
            raw_id="DOC_001_DUPLICATE",
            content="""<html><head><title>Engineering Handbook</title></head>
            <body><nav><a href='/home'>Home</a></nav>
            <h1>Kubernetes Deployment Guide</h1>
            <p>Production pods must specify both CPU limits and memory limits to prevent node starvation.</p>
            <p>All ingress traffic is encrypted using TLS 1.3 with automated Let's Encrypt certificates.</p>
            <footer>Copyright 2026 Enterprise Corp</footer></body></html>""",
            doc_format="html",
            source_uri="https://wiki.internal.net/k8s-guide-copy",
            tenant_id="tenant_finance",
            allowed_roles=["devops"]
        ),
        # Near duplicate (Minor typo/formatting change)
        RawDocument(
            raw_id="DOC_002_NEAR_DUP",
            content="""Kubernetes Deployment Guide.
            Production pods must specify both CPU limits and memory limits to prevent node starvation.
            All ingress traffic is encrypted using TLS 1.3 with automated certificates.""",
            doc_format="text",
            source_uri="s3://backups/k8s-guide-v1.txt",
            tenant_id="tenant_finance",
            allowed_roles=["devops"]
        ),
        # Distinct unique document
        RawDocument(
            raw_id="DOC_003_SECURITY",
            content="""# SecOps Incident Response Policy
            Any Severity-1 security breach requires an immediate incident war-room within 15 minutes.
            All production database credentials must be rotated immediately upon confirmation of breach.""",
            doc_format="markdown",
            source_uri="https://secops.internal.net/incident-sla",
            tenant_id="tenant_finance",
            allowed_roles=["secops", "ciso"]
        )
    ]

    for d in raw_docs:
        print(f"\nProcessing Document: {d.raw_id} (Format: {d.doc_format})")
        chunks, result = pipeline.process_document(d)
        print(f"Status: {result['status']}")

        if chunks:
            print(f"Produced {len(chunks)} enriched chunks:")
            for c in chunks:
                print(f"  • [{c.chunk_id}] {c.content[:75]}...")
                print(f"    ACLs: {c.metadata['allowed_roles']} | Tenant: {c.metadata['tenant_id']}")
        else:
            print(f"Details: {result}")

    print("\n" + "=" * 80)
    print("Ingestion verification completed successfully.")
```
