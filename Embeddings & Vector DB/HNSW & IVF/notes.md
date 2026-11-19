# HNSW & IVF 🔥 — Phase 3: Embeddings + Vector DB

Ab ye important **vector DB engineering** topic hai.

Ab tak hum kar rahe the:

```
Query Vector
     ↓
Compare with vectors
     ↓
Rank
     ↓
Top-K
```

Problem:

```
10M vectors
      ↓
compare query with 10M vectors
      ↓
EXPENSIVE
```

Isliye **Approximate Nearest Neighbor (ANN)** indexes use karte hain.

Do major approaches:

```
ANN
├── HNSW
└── IVF
```

## 1. ANN Kya Solve Karta Hai?

**Exact search:**

```
Query
 ↓
ALL 10M vectors
 ↓
calculate distance
 ↓
sort
 ↓
Top-K
```

**ANN:**

```
Query
 ↓
INDEX
 ↓
Only promising candidates
 ↓
Top-K
```

Trade-off:

```
Exact Search
→ maximum accuracy
→ potentially expensive

ANN
→ much faster
→ may miss some true nearest neighbors
```

Yahan important metric:

```
Recall@K
```

Agar actual top-5:

```
A B C D E
```

aur ANN return karta hai:

```
A B C X Y
```

phir:

```
Recall@5 = 3/5 = 60%
```

Good ANN systems ye achieve karne ki koshish karte hain:

```
high speed
+
high recall
```

## 2. HNSW — Hierarchical Navigable Small World

Full form:

```
Hierarchical Navigable Small World
```

Iska basic idea:

> Vectors ko ek graph mein organize karo, taaki query ko har vector check na karna pade.

Iske bajaye:

```
Query
 ↓
Graph
 ↓
nearby/promising nodes
 ↓
better nodes
 ↓
Top-K
```

## 3. Graph Intuition

Socho vectors ko cities ki tarah.

```
A ---- B ---- C
|      |      |
D ---- E ---- F
       |
       G
```

Har node:

```
Node = vector
Edge = connection to another vector
```

Similar vectors ko generally graph mein nearby connections milte hain.

Maan le query vector Q hai:

```
Q
 ↓
A
 ↓
B
 ↓
E
 ↓
F
```

Algorithm intelligently graph navigate karta hai, sab kuch check karne ke bajaye.

## 4. "Small World" Kyun?

Small-world graph ka intuition:

> **Most nodes tak relatively few hops mein pahunch sakte ho.**

Real-life example:

```
You
 ↓
Friend
 ↓
Friend of friend
 ↓
Target person
```

Iske bajaye ki tu check kare:

```
8 billion people
```

tu ek small number of connections traverse karta hai.

HNSW vector search mein similar intuition apply karta hai.

## 5. HNSW Mein Layers Hote Hain ⭐

HNSW ka most important concept:

> **Multiple graph layers.**

Conceptually:

**Layer 2:**

```
          A ----------- F
          |             |
          |             |
          D ----------- H
```

**Layer 1:**

```
      A ---- B ---- C ---- F
      |     /      |      |
      D --- E ----- G ---- H
```

**Layer 0:**

```
A--B--C--D--E--F--G--H--I--J--K...
```

**Upper layers**

```
few nodes
large jumps
```

**Lower layers**

```
many nodes
fine-grained navigation
```

Toh search:

```
Top layer
    ↓
coarse navigation
    ↓
lower layer
    ↓
more precise navigation
    ↓
Layer 0
    ↓
nearest neighbors
```

**Yehi core HNSW intuition hai.**

## 6. Search Example

Maan le query:

```
Q = "authentication with JWT"
```

Vector space:

```
                  JWT
                   ●
                  / \
                 /   \
               ●       ●
           OAuth       Auth
             |
             ●
          Database
```

HNSW necessarily Q ko har point ke saath compare nahi karta.

Ye graph ke through navigate karta hai:

```
Entry Point
     ↓
Candidate
     ↓
Better candidate
     ↓
Better candidate
     ↓
Nearest region
     ↓
Top-K
```

## 7. HNSW Parameters 🔥

Jab tu ek HNSW index create karta hai, tu ye dekhega:

```sql
WITH (
    m = 16,
    ef_construction = 64
)
```

Aur search ke dauran:

```
ef_search
```

Tujhe teeno samajhne honge.

## 8. M

M roughly control karta hai:

> Ek node kitni graph connections maintain kar sakta hai.

Example:

```
M = 4
```

Node approximately maintain kar sakta hai:

```
      B
      |
A --- Node --- C
      |
      D
```

**Higher M:**

```
more connections
     ↓
richer graph
     ↓
potentially better recall
     ↓
more memory
```

**Lower M:**

```
fewer connections
     ↓
smaller index
     ↓
less memory
     ↓
potentially lower recall
```

Toh:

```
M ↑
→ memory ↑
→ index size ↑
→ potential recall ↑
```

**Free win nahi hai.**

## 9. ef_construction

Ye control karta hai ki HNSW index build karte waqt kitni effort use hoti hai.

Soch:

```
ef_construction = how hard we search while building the graph
```

**Higher:**

```
ef_construction ↑
        ↓
better graph construction
        ↓
potentially better recall
        ↓
slower index building
        ↓
more build-time work
```

**Lower:**

```
faster construction
but potentially weaker graph
```

## 10. ef_search

Ye query time ke liye hai.

Soch:

```
ef_search = how many candidates the search explores
```

**Higher:**

```
ef_search ↑
     ↓
more candidates explored
     ↓
better chance of finding true neighbors
     ↓
higher recall
     ↓
more query computation
     ↓
higher latency
```

**Lower:**

```
faster
but potentially lower recall
```

## 11. Teeno Parameters Saath Mein

Ye yaad rakh:

```
M
↓
Graph connectivity

ef_construction
↓
How carefully graph is built

ef_search
↓
How extensively graph is searched
```

**Interview answer:**

> M graph connectivity control karta hai, ef_construction index construction ke dauran effort control karta hai, aur ef_search query time pe search breadth control karta hai.

## 12. pgvector HNSW

Example:

```sql
CREATE INDEX document_chunks_embedding_hnsw
ON document_chunks
USING hnsw (embedding vector_cosine_ops);
```

Custom parameters:

```sql
CREATE INDEX document_chunks_embedding_hnsw
ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (
    m = 16,
    ef_construction = 64
);
```

Phir query:

```sql
SELECT
    id,
    content,
    embedding <=> '[QUERY_VECTOR]' AS distance
FROM document_chunks
ORDER BY embedding <=> '[QUERY_VECTOR]'
LIMIT 5;
```

Database HNSW index use kar sakta hai.

## 13. ef_search Set Karna

Conceptually:

```sql
SET hnsw.ef_search = 100;
```

Phir:

```sql
SELECT ...
ORDER BY embedding <=> '[QUERY_VECTOR]'
LIMIT 5;
```

Higher `ef_search` generally matlab zyada search effort.

Tu ye soch sakta hai:

```
ef_search = 20
→ faster

ef_search = 100
→ more candidates

ef_search = 500
→ more expensive but potentially higher recall
```

Exact best value teri workload pe depend karta hai.

## 14. HNSW Ka Sabse Bada Advantage

HNSW usually ek excellent:

```
speed ↔ recall
```

trade-off deta hai.

Aur ek major practical benefit:

> **Isse IVF jaisa separate training/clustering step nahi chahiye.**

Ye isse kai dynamic workloads ke liye attractive banata hai.

## 15. Ab IVF

**IVF = Inverted File Index.**

Different idea.

Graph create karne ke bajaye:

```
HNSW
→ graph
```

**IVF vector space ko clusters/lists mein divide karta hai.**

Socho:

```
             Vector Space

       ● ● ● ●
       Cluster A


                    ● ● ●
                    Cluster B


   ● ● ●
   Cluster C


                         ● ● ● ●
                         Cluster D
```

Har cluster ka ek centroid hota hai.

## 16. Centroid Kya Hai?

Maan le:

```
Cluster A:
A1
A2
A3
A4
```

Hum ek representative point calculate karte hain:

```
       Centroid
          ●
       /  |  \
     A1  A2  A3
          |
          A4
```

**Centroid = approximately us cluster ka center.**

## 17. IVF Search

Query:

```
Q
```

aati hai.

Har vector search karne ke bajaye:

```
Q
 ↓
Find closest clusters
 ↓
Search vectors only inside those clusters
 ↓
Top-K
```

Example:

```
4 clusters

A     B     C     D

          Q
          ↓
Closest cluster = C
```

Search:

```
C only
```

iske bajaye:

```
A + B + C + D
```

## 18. lists

IVF mein, tu ye dekhega:

```sql
WITH (lists = 100)
```

`lists` roughly matlab:

> Vectors kitne clusters/lists mein partition kiye jaate hain.

Example:

```
lists = 4
```

matlab:

```
Cluster 1
Cluster 2
Cluster 3
Cluster 4
```

**Higher lists:**

```
more clusters
     ↓
smaller clusters
     ↓
potentially less work per searched cluster
```

Lekin ek catch hai.

**Bahut zyada lists dataset size aur query settings pe depend karte hue search/training behavior ko less effective bana sakti hain.**

Toh phir se:

> **Benchmark kar, magic value yaad mat kar.**

## 19. probes

Query time pe, IVF ko decide karna padta hai:

> Mujhe kitne clusters search karne chahiye?

Ye control hota hai:

```
probes
```

se.

Example:

```
probes = 1
```

Sirf closest cluster search kar.

```
probes = 5
```

5 closest clusters search kar.

```
probes ↑
    ↓
more clusters searched
    ↓
higher recall
    ↓
more computation
```

Toh:

```
lists
→ number of clusters

probes
→ number of clusters searched per query
```

## 20. HNSW vs IVF

Ab compare karte hain:

| | HNSW | IVF |
|---|---|---|
| Basic structure | Graph | Clusters |
| Main idea | Navigate graph | Search selected clusters |
| Build complexity | Graph construction | Clustering/training |
| Query tuning | ef_search | probes |
| Build tuning | M, ef_construction | lists |
| Memory | Generally higher | Can be lower |
| Dynamic updates | Generally convenient | Can have more considerations |
| Main trade-off | Connectivity/search breadth | Clustering/search breadth |

**Table ko "HNSW always wins" ki tarah interpret mat kar. Workload matter karta hai.**

## 21. Visual Difference

**HNSW**

```
          A -------- B
         / \        / \
        C---D------E---F
         \          /
          G--------H

        GRAPH NAVIGATION
```

**IVF**

```
     ┌──────────────┐
     │ Cluster A    │
     │ ● ● ● ●      │
     └──────────────┘

     ┌──────────────┐
     │ Cluster B    │
     │ ● ● ●        │
     └──────────────┘

     ┌──────────────┐
     │ Cluster C    │
     │ ● ● ● ●      │
     └──────────────┘

            ↓

       Search nearest
          clusters
```

## 22. Tu HNSW Kab Choose Karega?

Generally attractive hai jab:

```
Need strong recall
+
low-latency search
+
frequent updates
+
you don't want clustering complexity
```

Kai modern RAG workloads ke liye, HNSW ek strong starting point hai.

## 23. IVF Kab Sense Banata Hai?

IVF attractive ho sakta hai jab:

```
Very large vector datasets
+
memory efficiency matters
+
clustering-based retrieval fits workload
+
you can tune lists/probes
```

Interview mein correct answer ye nahi hai:

> "HNSW is always better."

Iske bajaye:

> "Main HNSW aur IVF ko representative data pe benchmark karunga, recall, p95 latency, memory/index size, aur update behavior measure karte hue."

**Yehi engineering answer hai.**

## 24. Ek BAHUT Important Distinction

Ye mix mat kar:

```
Embedding model
```

ke saath:

```
Vector index
```

**Embedding model:**

```
text → vector
```

**HNSW/IVF:**

```
vectors → efficient retrieval structure
```

Toh:

```
Text
 ↓
Embedding Model
 ↓
Vector
 ↓
Vector Index
 ↓
Fast Search
```

## 25. Full Production Flow

Ab hamara Phase 3 pipeline aisa dikhta hai:

```
                  DOCUMENT
                     ↓
                  CHUNKING
                     ↓
               EMBEDDING MODEL
                     ↓
                  VECTORS
                     ↓
          PostgreSQL + pgvector
                     ↓
               HNSW / IVF
                     ↓
────────────────────────────────
                     ↑
                  QUERY
                     ↓
              Query Embedding
                     ↓
             Metadata Filters
                     ↓
             ANN Vector Search
                     ↓
                  Ranking
                     ↓
                   Top-K
```

**Tu ab basically RAG ke neeche ka retrieval engine dekh raha hai.**

## 🧠 Interview Questions

**1. Why is HNSW faster than brute-force search?**

> Kyunki ye vectors ke ek graph ko navigate karta hai aur search ko promising regions pe focus karta hai, query ko har vector ke saath compare karne ke bajaye.

**2. What does ef_search control?**

> Search-time exploration breadth. Higher values generally recall improve karti hain, more computation/latency ki cost pe.

**3. What does M control?**

> Approximate graph connectivity — per node maintain ki gayi connections ki number, jo memory, construction, aur recall ko affect karti hai.

**4. What does IVF do?**

> Vectors ko clusters/lists mein partition karta hai aur poore dataset ke bajaye sirf selected clusters search karta hai.

**5. What is nprobe/probes?**

> Ek query ke liye examine kiye gaye IVF clusters/lists ki number.

**6. HNSW or IVF?**

> Workload pe depend karta hai. Recall, p95 latency, memory, index size, build time, aur update behavior benchmark kar.


---

## 9. Complete Production Implementation: HNSW & IVF Simulation & Recall Benchmark 💻

Below is an end-to-end Python implementation that demonstrates:
1. **Brute Force (Exact k-NN)** as the ground truth.
2. **Inverted File Index (IVF)** implementation with k-means centroids, inverted lists, and configurable `nprobe`.
3. **Hierarchical Navigable Small World (HNSW)** simulation using skip-list greedy routing across graph layers.
4. **Empirical Recall@k and Latency Benchmark** comparing Brute Force vs IVF vs HNSW.

```python
"""
hnsw_ivf_benchmark.py
End-to-End Implementation of Approximate Nearest Neighbor (ANN) Algorithms:
- Exact Brute-Force (Flat Scan) Ground Truth
- IVF (Inverted File Index) with Voronoi Partitions & nprobe
- HNSW (Hierarchical Navigable Small World) multi-layer graph search
- Recall@K and Latency evaluation
"""

import time
import math
import heapq
import numpy as np
from typing import List, Dict, Tuple, Set


# =====================================================================
# 1. Exact Brute-Force Ground Truth (Flat Scan)
# =====================================================================
def brute_force_knn(query: np.ndarray, corpus: np.ndarray, k: int = 10) -> List[int]:
    """
    Computes exact Euclidean distance against all N vectors: O(N * D).
    Returns indices of top-k nearest neighbors.
    """
    dists = np.linalg.norm(corpus - query, axis=1)
    return np.argsort(dists)[:k].tolist()


# =====================================================================
# 2. IVF (Inverted File Index) Implementation
# =====================================================================
class SimpleIVFIndex:
    """
    Partitions the vector space into C Voronoi cells using k-means centroids.
    At query time, searches only the closest 'nprobe' clusters.
    """
    def __init__(self, n_clusters: int = 32, nprobe: int = 4):
        self.n_clusters = n_clusters
        self.nprobe = nprobe
        self.centroids: np.ndarray = None
        self.inverted_lists: Dict[int, List[int]] = {}
        self.corpus: np.ndarray = None

    def fit_and_build(self, corpus: np.ndarray, max_iter: int = 10):
        self.corpus = corpus
        n_samples, d = corpus.shape
        
        # Simple K-Means initialization (random selection)
        indices = np.random.choice(n_samples, self.n_clusters, replace=False)
        self.centroids = corpus[indices].copy()
        
        # Lloyd's K-Means clustering
        for _ in range(max_iter):
            # Assign points to nearest centroid
            dists = np.linalg.norm(corpus[:, np.newaxis, :] - self.centroids[np.newaxis, :, :], axis=2)
            assignments = np.argmin(dists, axis=1)
            
            # Update centroids
            for c in range(self.n_clusters):
                cluster_pts = corpus[assignments == c]
                if len(cluster_pts) > 0:
                    self.centroids[c] = cluster_pts.mean(axis=0)

        # Build Inverted Lists
        self.inverted_lists = {c: [] for c in range(self.n_clusters)}
        dists = np.linalg.norm(corpus[:, np.newaxis, :] - self.centroids[np.newaxis, :, :], axis=2)
        assignments = np.argmin(dists, axis=1)
        for idx, c in enumerate(assignments):
            self.inverted_lists[c].append(idx)

    def search(self, query: np.ndarray, k: int = 10) -> List[int]:
        # Step 1: Find 'nprobe' closest centroids
        centroid_dists = np.linalg.norm(self.centroids - query, axis=1)
        nearest_clusters = np.argsort(centroid_dists)[:self.nprobe]

        # Step 2: Search vectors inside only those clusters
        candidate_indices = []
        for c in nearest_clusters:
            candidate_indices.extend(self.inverted_lists[c])

        if not candidate_indices:
            return []

        candidates = self.corpus[candidate_indices]
        dists = np.linalg.norm(candidates - query, axis=1)
        top_local = np.argsort(dists)[:k]
        return [candidate_indices[i] for i in top_local]


# =====================================================================
# 3. Simple HNSW Multi-Layer Graph Simulation
# =====================================================================
class SimpleHNSWIndex:
    """
    Hierarchical Navigable Small World graph.
    Vectors exist across multiple layers with exponentially decaying probability.
    Greedy search descends from top layer to bottom layer.
    """
    def __init__(self, m: int = 8, ef_search: int = 16, ml: float = 1.0 / math.log(2)):
        self.m = m                     # Max connections per node
        self.ef_search = ef_search     # Size of dynamic candidate list during search
        self.ml = ml                   # Multiplier for layer assignment
        self.layers: List[Dict[int, Set[int]]] = []  # layer -> {node_id: set(neighbors)}
        self.entry_point: int = None
        self.max_layer: int = -1
        self.corpus: np.ndarray = None

    def _random_level(self) -> int:
        r = np.random.uniform(0, 1)
        return int(-math.log(r) * self.ml)

    def build(self, corpus: np.ndarray):
        self.corpus = corpus
        n_samples = len(corpus)

        for i in range(n_samples):
            level = self._random_level()
            while len(self.layers) <= level:
                self.layers.append({})

            # Connect node to existing nodes at each assigned level
            for l in range(level + 1):
                self.layers[l][i] = set()
                existing_nodes = list(self.layers[l].keys())
                if len(existing_nodes) > 1:
                    # Pick up to M closest neighbors
                    other_nodes = [node for node in existing_nodes if node != i]
                    if other_nodes:
                        vecs = self.corpus[other_nodes]
                        dists = np.linalg.norm(vecs - self.corpus[i], axis=1)
                        closest = np.argsort(dists)[:self.m]
                        for idx in closest:
                            neighbor = other_nodes[idx]
                            self.layers[l][i].add(neighbor)
                            self.layers[l][neighbor].add(i)

            if self.entry_point is None or level > self.max_layer:
                self.entry_point = i
                self.max_layer = level

    def search(self, query: np.ndarray, k: int = 10) -> List[int]:
        if self.entry_point is None:
            return []

        curr_obj = self.entry_point
        curr_dist = float(np.linalg.norm(self.corpus[curr_obj] - query))

        # Top layers: Greedy search down to layer 0
        for l in range(self.max_layer, 0, -1):
            changed = True
            while changed:
                changed = False
                for neighbor in self.layers[l].get(curr_obj, set()):
                    d = float(np.linalg.norm(self.corpus[neighbor] - query))
                    if d < curr_dist:
                        curr_dist = d
                        curr_obj = neighbor
                        changed = True

        # Layer 0: Search with priority queue (ef_search)
        candidates = [(curr_dist, curr_obj)]
        visited = {curr_obj}
        w = [(curr_dist, curr_obj)]

        while candidates:
            c_dist, c_id = heapq.heappop(candidates)
            if c_dist > w[-1][0] and len(w) >= self.ef_search:
                break

            for neighbor in self.layers[0].get(c_id, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    n_dist = float(np.linalg.norm(self.corpus[neighbor] - query))
                    if n_dist < w[-1][0] or len(w) < self.ef_search:
                        heapq.heappush(candidates, (n_dist, neighbor))
                        w.append((n_dist, neighbor))
                        w.sort(key=lambda x: x[0])
                        if len(w) > self.ef_search:
                            w.pop()

        return [item[1] for item in w[:k]]


# =====================================================================
# 4. Evaluation & Benchmark Runner (Recall@K and Speedup)
# =====================================================================
def run_ann_benchmark():
    np.random.seed(42)
    n_corpus = 5_000
    d = 128
    n_queries = 50
    k = 10

    print(f"Generating synthetic dataset: {n_corpus} vectors, {d} dimensions...")
    corpus = np.random.randn(n_corpus, d).astype(np.float32)
    queries = np.random.randn(n_queries, d).astype(np.float32)

    # 1. Ground truth via Brute Force
    print("Computing Ground Truth (Exact Flat Scan)...")
    t0 = time.perf_counter()
    ground_truth = [brute_force_knn(q, corpus, k=k) for q in queries]
    bf_time = (time.perf_counter() - t0) * 1000

    # 2. IVF Index
    print("Building and querying IVF index (clusters=32, nprobe=4)...")
    ivf = SimpleIVFIndex(n_clusters=32, nprobe=4)
    ivf.fit_and_build(corpus)

    t0 = time.perf_counter()
    ivf_results = [ivf.search(q, k=k) for q in queries]
    ivf_time = (time.perf_counter() - t0) * 1000

    # 3. HNSW Index
    print("Building and querying HNSW index...")
    hnsw = SimpleHNSWIndex(m=8, ef_search=16)
    hnsw.build(corpus)

    t0 = time.perf_counter()
    hnsw_results = [hnsw.search(q, k=k) for q in queries]
    hnsw_time = (time.perf_counter() - t0) * 1000

    # Compute Recall@K
    def calculate_recall(pred_list, true_list):
        recalls = []
        for p, t in zip(pred_list, true_list):
            intersection = len(set(p).intersection(set(t)))
            recalls.append(intersection / len(t))
        return np.mean(recalls) * 100.0

    ivf_recall = calculate_recall(ivf_results, ground_truth)
    hnsw_recall = calculate_recall(hnsw_results, ground_truth)

    print("\n=======================================================")
    print(f"BENCHMARK RESULTS (Top-{k} on {n_queries} queries):")
    print("=======================================================")
    print(f"Brute Force (Exact) : Recall = 100.0% | Latency = {bf_time:.2f} ms")
    print(f"IVF (nprobe=4)      : Recall = {ivf_recall:5.1f}% | Latency = {ivf_time:.2f} ms (Speedup: {bf_time/ivf_time:.1f}x)")
    print(f"HNSW (ef=16)        : Recall = {hnsw_recall:5.1f}% | Latency = {hnsw_time:.2f} ms (Speedup: {bf_time/hnsw_time:.1f}x)")


if __name__ == "__main__":
    run_ann_benchmark()
```

### Execution:
```bash
python hnsw_ivf_benchmark.py
```
