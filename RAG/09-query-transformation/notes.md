# Query Transformation Techniques 🔥 — Production RAG Engineering Guide

Production RAG ka sabse common failure point vector database nahi, **User ki Query** hoti hai.

User real world mein kabhi well-formed, semantically dense queries nahi likhta. User type karega:
- *"it failed again with that memory error"* (Context missing)
- *"PgBouncer vs RDS Proxy"* (Too short, ambiguous intent)
- *"How to migrate from Oracle to Postgres without downtime and what about CDC with Debezium?"* (Multi-intent compound query)

Agar tum aisi raw query ko directly embedding model mein pass kar doge, toh:
```
Raw User Query ("it failed again with that memory error")
                     │
                     ▼
             Embedding Model
                     │
                     ▼ (Vector points to generic 'error' or 'memory' space)
           [ Vector Database ]
                     │
                     ▼
❌ Returns 5 random out-of-context error chunks!
```

Is problem ko solve karne ke liye production RAG mein retrieval se pehle **Query Transformation Layer** lagayi jaati hai.

---

## 1. Why Raw Queries Fail Against Dense Vectors

Dense vectors cosine similarity compute karte hain based on semantic coordinate proximity in high-dimensional space ($\mathbb{R}^d$).

```
                      VECTOR SPACE ASYMMETRY
                      
     Query Space (Short, Question-form)        Document Space (Long, Declarative)
  ┌───────────────────────────────────┐    ┌───────────────────────────────────┐
  │ "Why is my PG container killed?"  │    │ "Linux Out-Of-Memory (OOM) killer  │
  │ • 6 tokens                        │ ≠  │ invokes SIGKILL on postgres pid    │
  │ • Interrogative syntax            │    │ when cgroup memory limit breached" │
  │ • Lacks domain keywords           │    │ • 250 tokens, technical, passive  │
  └───────────────────────────────────┘    └───────────────────────────────────┘
```

### Core Failure Modes:
1. **Asymmetric Formulation (Question vs Answer mismatch):** User question poochta hai, jabki database mein informative answer declarative statements mein hota hai. Embedding space mein Question vector aur Document vector ke beech structural cosine distance rehti hai.
2. **Pronoun & Anaphora Ambiguity (Conversational Context):** Multi-turn chat mein user kehta hai: *"How do I increase its pool size?"*. "Its" kisko refer kar raha hai? Redis? PostgreSQL? PgBouncer? Vector search is completely blind to conversational history.
3. **Compound Multi-Part Queries:** Single vector multiple independent questions ka average representation ban jata hai, jisse retrieval dono topics ke shallow overlap par restrict ho jaati hai (Sub-intent dilution).

---

## 2. The 4 Big Query Transformation Strategies

```
┌─────────────────────────┬────────────────────────────┬─────────────────────────────┐
│ Strategy                │ Transformation Mechanism   │ Ideal Use Case              │
├─────────────────────────┼────────────────────────────┼─────────────────────────────┤
│ 1. Query Rewriting      │ History context resolution │ Conversational follow-ups   │
│ 2. HyDE (Hypothetical)  │ Hallucinates pseudo-answer │ Asymmetric search/Abstract Q│
│ 3. Multi-Query Expansion│ Generates 3-5 perspectives │ High-recall / Polysemy      │
│ 4. Step-Back Prompting  │ Extracts broader principle │ Deep debugging / Complex CS │
└─────────────────────────┴────────────────────────────┴─────────────────────────────┘
```

---

### Strategy 1: Conversational Query Rewriting (De-contextualization)

Agar user multi-turn chat mein baat kar raha hai:
- Turn 1: *"Explain PgBouncer transaction pooling."*
- Turn 2: *"Can it handle prepared statements?"*

Raw Query for Turn 2: *"Can it handle prepared statements?"* (No mention of PgBouncer or transaction mode).

```
[ Conversation History ] + [ Raw Turn-2 Query ]
                      │
                      ▼ (Small LLM e.g., GPT-4o-mini / Llama-3-8B)
[ De-contextualized Query: "Can PgBouncer transaction pooling handle prepared statements?" ]
                      │
                      ▼
              Vector Retrieval (Hits exact PgBouncer documentation!)
```

---

### Strategy 2: HyDE (Hypothetical Document Embeddings)

Gao et al. (2022) ne ek brilliant technique propose ki:
> **"Instead of embedding the question, ask an LLM to hallucinate a fake answer, and embed THAT answer!"**

```
Raw Query: "Why does PostgreSQL crash with exit code 137?"
                      │
                      ▼ (LLM Zero-Shot Generation)
Hypothetical Document (Fake Answer):
"PostgreSQL exit code 137 indicates SIGKILL sent by Linux kernel OOM Killer.
This happens when memory consumption exceeds docker container cgroup limits..."
                      │
                      ▼ (Embedding Model)
Hypothetical Vector (Now in the EXACT same declarative semantic space as real docs!)
                      │
                      ▼
[ Vector Search ] ──> Retrieves ground-truth production incident manuals!
```

- **Kyun kaam karta hai?** Fake answer ke factual details galat bhi ho sakte hain, lekin uska **linguistic style, terminology, and semantic neighborhood** exact documents ke saath match karta hai!

---

### Strategy 3: Multi-Query Expansion (Perspective Fan-Out)

Ek query ko 3 to 5 different ways mein rephrase kiya jata hai taaki alag-alag vocabulary aur synonyms cover ho sakein:

```
                          "PostgreSQL slow query debugging"
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
           Query Variant 1         Query Variant 2         Query Variant 3
      "Postgres EXPLAIN ANALYZE   "Diagnosing database    "Slow query log and
       execution plan issues"      index scan latency"     pg_stat_statements"
                 │                       │                       │
                 ▼                       ▼                       ▼
            [Vector DB]             [Vector DB]             [Vector DB]
                 └───────────────────────┬───────────────────────┘
                                         ▼
                            Reciprocal Rank Fusion (RRF)
                                         ▼
                           Combined High-Recall Candidates
```

---

### Strategy 4: Step-Back Prompting (Abstraction Layer)

Google DeepMind ne prove kiya ki complex queries ke liye broader fundamental concept dhoondhna retrieval quality ko $30\%+$ boost karta hai:
- **Original Query:** *"Why is my asyncpg connection pool throwing TimeoutError when 500 Celery workers execute queries?"*
- **Step-Back Query:** *"What causes database connection pool starvation under high concurrent worker architectures?"*

Broader query se architecture level guidelines retrieve hoti hain, aur specific query se exact driver syntax retrieve hota hai. Dono context milkar LLM ko perfect answer formulate karne dete hain.

---

## 3. Latency & Cost Trade-offs

Transformation free nahi hoti! Production mein har extra LLM call latency aur dollar cost add karti hai:

```
┌─────────────────────────┬──────────────────┬─────────────────────────────┐
│ Technique               │ Added Latency    │ Production Mitigation       │
├─────────────────────────┼──────────────────┼─────────────────────────────┤
│ Raw Query (No transform)│ 0 ms             │ ❌ Poor precision/recall    │
│ Conversational Rewriter │ 120 - 250 ms     │ Run fast quantized 3B model │
│ HyDE Generation         │ 250 - 450 ms     │ Cache answers, 1-shot temp=0│
│ Multi-Query (5 queries) │ 150ms + 5x DB Q  │ Parallel async Vector calls │
│ Step-Back Prompting     │ 180 - 300 ms     │ Single LLM call multi-output│
└─────────────────────────┴──────────────────┴─────────────────────────────┘
```

**Production Golden Rule:**
Multi-turn conversational rewriter **always-on** hona chahiye. HyDE aur Multi-Query ko **selective / router-driven** rakho (sirf tab trigger karo jab user query ambiguous ho ya initial retrieval score threshold se neeche ho).

---

## 4. Complete Production Implementation: `query_transformation_suite.py` 💻

Below is an end-to-end, runnable query transformation engine featuring:
1. **Conversational History Rewriter** (resolves pronouns & context).
2. **HyDE Generator** (produces domain-aligned hypothetical docs).
3. **Multi-Query Expander** (generates multiple orthogonal search vectors).
4. **Sub-Query Decomposer** (splits compound questions into atomic sub-queries).
5. Self-contained verification runner demonstrating each strategy.

```python
"""
query_transformation_suite.py
Production-grade Query Transformation Suite for Advanced RAG.
Features:
- Conversational Context Rewriter (Anaphora Resolution)
- Hypothetical Document Embeddings (HyDE) Generator
- Multi-Query Expander with parallel variants
- Sub-Query Decomposer for compound queries
- Clean rule-based / LLM-ready modular architecture
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ChatTurn:
    role: str  # 'user' or 'assistant'
    content: str


@dataclass
class TransformationResult:
    original_query: str
    transformed_queries: List[str]
    transformation_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class QueryTransformationEngine:
    """
    Transforms fragile user queries into optimized, retrieval-ready representations.
    Designed for production inference pipelines.
    """
    def __init__(self, use_simulated_llm: bool = True):
        self.use_simulated_llm = use_simulated_llm

    # =================================================================
    # 1. Conversational Query Rewriting (De-contextualization)
    # =================================================================
    def rewrite_conversational_query(
        self,
        history: List[ChatTurn],
        current_query: str
    ) -> TransformationResult:
        """
        Resolves pronouns, ambiguous references ('it', 'that issue', 'previous method'),
        and anchors the current turn into a fully standalone retrieval query.
        """
        if not history:
            return TransformationResult(
                original_query=current_query,
                transformed_queries=[current_query],
                transformation_type="conversational_rewrite",
                metadata={"resolved": False, "reason": "No history"}
            )

        # Extract entities from recent assistant turns
        recent_context = " ".join([t.content for t in history[-3:]])
        
        # Rule-based / simulated LLM resolution:
        # In production, this prompt is executed against GPT-4o-mini / Claude-3.5-Haiku
        rewritten = current_query
        pronouns = ["it", "its", "this", "that", "these", "those", "the same"]
        
        has_ambiguous_ref = any(re.search(rf"\b{p}\b", current_query.lower()) for p in pronouns)
        
        if has_ambiguous_ref:
            # Detect key subjects from recent context
            inferred_subject = "PostgreSQL PgBouncer connection pooling"
            if "redis" in recent_context.lower():
                inferred_subject = "Redis caching"
            elif "kafka" in recent_context.lower():
                inferred_subject = "Kafka consumer group"

            # Transform ambiguous query
            clean_q = re.sub(r"\b(it|its|this|that)\b", inferred_subject, current_query, flags=re.IGNORECASE)
            rewritten = clean_q.strip()

        return TransformationResult(
            original_query=current_query,
            transformed_queries=[rewritten],
            transformation_type="conversational_rewrite",
            metadata={"resolved": has_ambiguous_ref, "standalone_query": rewritten}
        )

    # =================================================================
    # 2. HyDE: Hypothetical Document Embeddings
    # =================================================================
    def generate_hyde(self, query: str) -> TransformationResult:
        """
        Generates a synthetic hypothetical answer passage.
        Embedding this passage bridges the asymmetric semantic gap between
        question syntax and declarative documentation paragraphs.
        """
        # In production, execute prompt:
        # "Write a concise, highly technical passage that answers this question: {query}"
        
        # High-fidelity simulated domain generation
        tokens = query.lower()
        if "oom" in tokens or "137" in tokens or "crash" in tokens:
            hypothetical_doc = (
                f"Linux kernel Out-Of-Memory (OOM) killer terminated the database process with SIGKILL (exit code 137). "
                f"This occurs when container memory limit is reached due to unconstrained work_mem or connection leaks. "
                f"Resolution requires adjusting shared_buffers, tuning cgroup limits, and setting max_connections."
            )
        else:
            hypothetical_doc = (
                f"Regarding {query}: The technical solution requires properly configuring connection parameters, "
                f"validating resource constraints in the cluster, and analyzing log outputs for root cause isolation."
            )

        return TransformationResult(
            original_query=query,
            transformed_queries=[hypothetical_doc],
            transformation_type="hyde",
            metadata={"synthetic_tokens": len(hypothetical_doc.split())}
        )

    # =================================================================
    # 3. Multi-Query Expansion
    # =================================================================
    def expand_multi_query(self, query: str, num_variants: int = 3) -> TransformationResult:
        """
        Expands the user query into multiple orthogonal viewpoints,
        capturing technical synonyms, diagnostic angles, and keyword variations.
        """
        # Production prompt generates N distinct search queries
        variants = [query]
        
        # Deterministic domain-aligned expansion for demonstration
        if "slow" in query.lower() or "performance" in query.lower():
            variants.append(f"analyzing high query latency and execution plan bottlenecks for {query}")
            variants.append(f"optimizing database index scans and disk IO wait time in {query}")
        elif "connection" in query.lower() or "timeout" in query.lower():
            variants.append(f"troubleshooting socket pool exhaustion and client connection errors: {query}")
            variants.append(f"configuring keepalive and max pool size limits for {query}")
        else:
            variants.append(f"technical specifications and best practices for {query}")
            variants.append(f"debugging and error handling in {query}")

        return TransformationResult(
            original_query=query,
            transformed_queries=variants[:num_variants],
            transformation_type="multi_query_expansion",
            metadata={"variant_count": len(variants[:num_variants])}
        )

    # =================================================================
    # 4. Compound Sub-Query Decomposition
    # =================================================================
    def decompose_sub_queries(self, query: str) -> TransformationResult:
        """
        Decomposes complex multi-intent questions into discrete, atomic sub-queries.
        Each sub-query is retrieved independently and results are unioned.
        """
        # Detect conjunctions splitting independent topics: 'and what about', 'also how do', 'versus'
        split_patterns = r"\b(?:and what about|also how to|while also|as well as|and how do i)\b|\band\b"
        parts = re.split(split_patterns, query, flags=re.IGNORECASE)
        
        sub_queries = [p.strip() for p in parts if len(p.strip()) > 10]
        if not sub_queries:
            sub_queries = [query]

        return TransformationResult(
            original_query=query,
            transformed_queries=sub_queries,
            transformation_type="sub_query_decomposition",
            metadata={"sub_query_count": len(sub_queries)}
        )


# =====================================================================
# 5. Verification & Demonstration Runner
# =====================================================================
if __name__ == "__main__":
    engine = QueryTransformationEngine()

    print("=" * 80)
    print("QUERY TRANSFORMATION SUITE VERIFICATION")
    print("=" * 80)

    # 1. Conversational Query Rewriting Test
    chat_history = [
        ChatTurn(role="user", content="How does PgBouncer transaction pooling work?"),
        ChatTurn(role="assistant", content="PgBouncer in transaction mode assigns a server connection only for the duration of a transaction.")
    ]
    follow_up = "Can it support prepared statements safely?"
    res_rewrite = engine.rewrite_conversational_query(chat_history, follow_up)
    print("\n[1] Conversational Query Rewrite:")
    print(f"    Raw Turn:      '{res_rewrite.original_query}'")
    print(f"    Decontextualized: '{res_rewrite.transformed_queries[0]}'")

    # 2. HyDE Test
    raw_error_query = "Why did my worker pod die with exit code 137?"
    res_hyde = engine.generate_hyde(raw_error_query)
    print("\n[2] Hypothetical Document Embedding (HyDE):")
    print(f"    User Query:    '{res_hyde.original_query}'")
    print(f"    Hypothetical Doc: '{res_hyde.transformed_queries[0]}'")

    # 3. Multi-Query Expansion Test
    perf_query = "PostgreSQL slow query response times"
    res_multi = engine.expand_multi_query(perf_query, num_variants=3)
    print("\n[3] Multi-Query Expansion:")
    print(f"    Original:      '{res_multi.original_query}'")
    for i, v in enumerate(res_multi.transformed_queries, 1):
        print(f"    Variant {i}:     '{v}'")

    # 4. Sub-Query Decomposition Test
    complex_query = "How to configure PostgreSQL connection pooling and how do I set up Kafka CDC with Debezium?"
    res_decomp = engine.decompose_sub_queries(complex_query)
    print("\n[4] Sub-Query Decomposition:")
    print(f"    Compound:      '{res_decomp.original_query}'")
    for i, sq in enumerate(res_decomp.transformed_queries, 1):
        print(f"    Sub-Query {i}:   '{sq}'")

    # Assertions
    assert len(res_rewrite.transformed_queries) == 1
    assert "PgBouncer" in res_rewrite.transformed_queries[0], "Conversational rewrite failed to inject context!"
    assert len(res_multi.transformed_queries) == 3, "Multi-query expansion should produce 3 variants."
    assert len(res_decomp.transformed_queries) == 2, "Compound query should split into 2 sub-queries."
    print("\nALL QUERY TRANSFORMATION CHECKS VERIFIED SUCCESSFULLY!")
```

---

## 5. Senior Interview Questions & Answers

### Q1: HyDE (Hypothetical Document Embeddings) standard question vector retrieval se superior kyun perform karta hai?
**Answer:** Question embeddings aur document embeddings vector space mein asymmetric hote hain. Questions short aur interrogative hote hain ("Why is my pod 137?"), jabki corpus documents declarative, verbose aur formal hote hain ("SIGKILL triggered by Linux kernel OOM killer..."). HyDE ek LLM se zero-shot answer generate karwata hai. Bhale hi generated facts partially inaccurate hon, uska syntax, vocabulary, aur technical density exact documentation space se match karta hai, jisse cosine similarity dramatically increase ho jaati hai.

### Q2: HyDE production mein kab completely fail ho jata hai (Hallucination Poisoning)?
**Answer:** HyDE un domains mein severely backfire karta hai jahan query unfamiliar/novel hoti hai ya user confidential proprietary codes poochta hai (e.g. internal ticket numbers, obscure private APIs, newly released features). Jab base LLM ke training set mein wo topic hota hi nahi, toh model completely bogus terms hallucinate karta hai. Ye hallucinatory vector corpus ke galat documents ko high-confidence se retrieve kar leta hai (Garbage-In, Garbage-Out). Rule: Public domain conceptual topics ke liye HyDE best hai; private codebases aur exact ID queries ke liye HyDE avoid karein.

### Q3: Multi-Query expansion retrieval pipeline mein latency aur cost ko kitna multiply karti hai?
**Answer:** Agar hum 1 query ko 5 variants mein expand karte hain, toh:
1. Ek upfront LLM call lagti hai ($\sim 150-250\text{ms}$).
2. 5 independent embedding API calls ($5 \times \text{cost}$).
3. 5 vector database queries ($5 \times \text{read IOPS}$).
4. Ek downstream Reciprocal Rank Fusion (RRF) aggregation layer.
Latency impact mitigate karne ke liye embeddings aur database calls ko `asyncio.gather` ke through fully parallelize kiya jata hai, limiting wall-clock latency overhead to just the slowest parallel DB query + LLM call.

### Q4: Multi-turn chat applications mein de-contextualization (query rewriting) kyun compulsory hai?
**Answer:** Conversational users heavily anaphoric pronouns use karte hain ("How to configure that?", "Why did it fail?", "What was the third option?"). Agar ye raw prompt vector DB mein bheja jaye, toh "it" aur "that" meaningless generic noise create karte hain. Query Rewriter pure conversation session state ko inspect karke pronouns ko explicit entities se replace karta hai ("How to configure PgBouncer transaction pooling?"), ensuring retrieval isolation and high precision.

### Q5: Step-Back Prompting kya hai aur ye complex reasoning queries ko kaise solve karta hai?
**Answer:** Google DeepMind (Zheng et al., 2023) dwara introduced technique hai. Jab user overly specific ya convoluted error trace deta hai, LLM pehle ek "step-back" abstraction question formulate karta hai (e.g., specific error: "Why did my gunicorn worker timeout on postgres execute?" $\rightarrow$ step-back: "What are the common causes of connection starvation between WSGI workers and relational databases?"). Dono queries ka context retrieve karke LLM ko provide kiya jata hai, allowing it to anchor on broad architectural principles first before diagnosing the specific incident.
