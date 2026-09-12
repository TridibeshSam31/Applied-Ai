# Metadata Filtering 🔥 — Phase 3: Embeddings + Vector DB

Ab tak humne seekha:

```
Query
  ↓
Embedding
  ↓
Vector similarity
  ↓
Top-K
```

Lekin production RAG mein sirf semantic similarity kaafi nahi hoti.

Socho tere vector DB mein 10 lakh chunks hain from:

```
Company A
Company B
Company C
```

User Company A ka hai.

Agar wo poochhe:

```
"What is our leave policy?"
```

Toh system ko sirf Company A ke documents search karne chahiye.

**Yahin metadata filtering aata hai.**

## 1. Metadata Kya Hai?

Chunk ke saath additional information:

```json
{
  "document_id": "doc_123",
  "chunk_id": "chunk_07",
  "section": "Leave Policy",
  "source": "employee_handbook.pdf",
  "page": 14,
  "tenant_id": "company_A",
  "version": "2026"
}
```

**Ye information vector ka semantic meaning nahi hai.**

Ye chunk ke baare mein **structured information** hai.

## 2. Vector + Metadata

Database mein ek row:

```
┌────────────┬─────────────────────┬───────────────────────┬──────────────┐
│ chunk_id   │ content             │ embedding             │ metadata     │
├────────────┼─────────────────────┼───────────────────────┼──────────────┤
│ c_001      │ Leave policy...     │ [0.12,0.45,...]       │ company_A    │
│ c_002      │ Salary policy...    │ [0.32,0.11,...]       │ company_A    │
│ c_003      │ Leave policy...     │ [0.15,0.43,...]       │ company_B    │
└────────────┴─────────────────────┴───────────────────────┴──────────────┘
```

Ab query:

```
"What is the leave policy?"
```

Semantic search shayad ye find kare:

```
c_001 → Company A leave policy
c_003 → Company B leave policy
```

Lekin agar user Company A ka hai:

```
tenant_id = company_A
```

**humein c_003 ko exclude karna hi hoga.**

## 3. Metadata Filtering

Conceptually:

```
Query
 ↓
Query embedding
 ↓
Filter metadata
 ↓
Similarity search
 ↓
Top-K
```

Example:

```sql
SELECT
    id,
    content,
    embedding <=> '[...]' AS distance
FROM document_chunks
WHERE metadata->>'tenant_id' = 'company_A'
ORDER BY embedding <=> '[...]'
LIMIT 5;
```

Ab vector search hota hai:

```
Company A documents
```

ke andar, poore corpus ke bajaye.

## 4. Ye Extremely Important Kyun Hai

Metadata filtering in cheezon ke liye use ho sakti hai:

**Multi-tenancy**

```
tenant_id = company_A
```

**Document type**

```
type = "policy"
```

**Department**

```
department = "engineering"
```

**Language**

```
language = "en"
```

**Version**

```
version = "2026"
```

**Source**

```
source = "handbook.pdf"
```

**Date**

```
created_at > ...
```

**Permissions**

```
user can access document
```

## 5. Semantic Search vs Metadata Filtering

**Ye distinction BAHUT important hai.**

**Semantic search poochta hai:**

> "Which chunks are conceptually closest to my query?"

**Metadata filtering poochta hai:**

> "Which chunks am I allowed / interested in searching?"

Toh:

```
             SEARCH
                │
       ┌────────┴────────┐
       ↓                 ↓
Metadata Filter     Vector Similarity
       │                 │
       └────────┬────────┘
                ↓
             Ranking
                ↓
              Top-K
```

## 6. Example

Maan le database contains:

```
Chunk A
tenant = A
content = "Employees get 18 casual leaves"

Chunk B
tenant = B
content = "Employees get 12 casual leaves"

Chunk C
tenant = A
content = "Employees can work remotely"

Chunk D
tenant = B
content = "Employees can work remotely"
```

Query:

```
"How many casual leaves?"
```

Filtering ke bina:

```
A → highly relevant
B → highly relevant
C → less relevant
D → less relevant
```

Saath:

```
tenant = A
```

hume milta hai:

```
A → relevant
C → less relevant
```

**B aur D candidates bhi nahi hain.**

## 7. Hard Filters vs Soft Relevance

**Metadata filters generally hard constraints hote hain.**

Example:

```sql
WHERE tenant_id = 'A'
```

matlab:

> Company B ke documents return NAHI hone chahiye.

**Ye ek ranking preference nahi hai.**

**Ye ek boundary hai.**

Yehi wajah hai ki permissions ko embeddings ke through implement nahi karna chahiye.

**❌ Bad:**

> "Hopefully similarity search won't return private docs."

**Bilkul nahi.**

Use kar:

```
Authorization / metadata filter
```

ek **deterministic boundary** ki tarah.

## 8. Security Example 🔐

Maan le:

```
User A
```

ko access hai:

```
Document 1
Document 2
```

lekin nahi:

```
Document 3
```

Ye mat kar:

```
Vector Search
   ↓
Top 20
   ↓
Remove unauthorized documents
```

**Ye risky ho sakta hai** implementation aur side channels pe depend karte hue.

Access constraints ko retrieval eligibility ke hisse ki tarah enforce karna prefer kar:

```
User
 ↓
Trusted authorization context
 ↓
Allowed document scope
 ↓
Vector search
 ↓
Results
```

Aur authorization **trusted application state se aana chahiye — LLM se nahi.**

**Ye directly connect hota hai un tool-security concepts se jo tu Phase 2 mein already seekh chuka hai.**

## 9. Proper Columns Ke Saath PostgreSQL Example

Sab kuch JSONB ke andar daalne ke bajaye, kabhi kabhi regular columns use kar:

```sql
CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,

    document_id BIGINT NOT NULL,

    tenant_id BIGINT NOT NULL,

    source TEXT,

    section TEXT,

    page_number INT,

    content TEXT NOT NULL,

    embedding VECTOR(1536)
);
```

Phir filtering simple ban jaati hai:

```sql
SELECT
    id,
    content,
    embedding <=> '[...]' AS distance
FROM document_chunks
WHERE tenant_id = 42
ORDER BY embedding <=> '[...]'
LIMIT 5;
```

Ye often frequently queried/filterable fields ke liye cleaner hota hai.

## 10. JSONB Metadata

Tu ye bhi use kar sakta hai:

```
metadata JSONB
```

Example:

```json
{
    "tenant_id": 42,
    "department": "engineering",
    "language": "en",
    "document_type": "policy"
}
```

Query:

```sql
SELECT
    id,
    content
FROM document_chunks
WHERE metadata->>'department' = 'engineering';
```

Multiple filters:

```sql
SELECT
    id,
    content,
    embedding <=> '[...]' AS distance
FROM document_chunks
WHERE metadata->>'tenant_id' = '42'
  AND metadata->>'department' = 'engineering'
  AND metadata->>'language' = 'en'
ORDER BY embedding <=> '[...]'
LIMIT 5;
```

## 11. Filtering + Top-K Together

**Ye important production query hai:**

```sql
SELECT
    id,
    content,
    embedding <=> '[QUERY_VECTOR]' AS distance
FROM document_chunks
WHERE tenant_id = 42
  AND document_type = 'policy'
  AND language = 'en'
ORDER BY embedding <=> '[QUERY_VECTOR]'
LIMIT 5;
```

Isse aise padh:

> Tenant 42 ke English policy chunks mein se, mere query ke sabse close 5 chunks dhoond.

**Yehi filtered vector search hai.**

## 12. Pre-Filter vs Post-Filter ⭐

**Ye ek important concept hai.**

### Post-Filter

```
Vector search
     ↓
Top 100
     ↓
Metadata filter
     ↓
Top 5
```

**Problem:**

Maan le un 100 mein se sirf 3 hi user ke tenant ke hain.

Tu bahut kam results ke saath end up ho sakta hai.

### Pre-Filter

```
Metadata filter
     ↓
Eligible documents
     ↓
Vector search
     ↓
Top 5
```

Conceptually better hai jab filter ek hard eligibility constraint represent karta hai.

Lekin implementation/index trade-offs hote hain, especially scale pe. Exact behavior tere database/index aur query plan pe depend karta hai.

## 13. Filtering Scale Pe Kyun Difficult Ban Sakti Hai

Maan le:

```
100 million vectors
```

aur:

```
tenant_id = 42
```

lekin Tenant 42 sirf:

```
10,000 vectors
```

owns karta hai.

Tu ideally chahta hai ki search us relevant subset ke andar efficiently operate kare.

Ab socho combine karte hue:

```
Vector similarity
+
tenant filter
+
department filter
+
permissions
+
date range
```

**Query planner/index strategy important ban jaana start hoti hai.**

Yehi ek wajah hai ki vector search sirf ye nahi hai "embeddings store karo aur cosine similarity calculate karo."

**Ye ek database engineering problem bhi hai.**

## 14. Metadata Hamesha Sirf JSON Nahi Hoti

Production systems mein ye ho sakta hai:

```
document_chunks
├── tenant_id
├── document_id
├── access_control
├── source
├── page
├── section
├── language
├── version
├── created_at
└── embedding
```

Kuch honi chahiye:

```
normal indexed columns
```

jabki flexible attributes ho sakte hain:

```
JSONB
```

**Rule of thumb:**

> Agar ek field frequently filtered, sorted, joined, ya constrained hoti hai, ek dedicated column often preferable hota hai usse arbitrary JSON ke andar chupane se.

## 15. Metadata Aur Citations

Yaad hai hamara chunk?

```json
{
    "source": "employee_handbook.pdf",
    "page": 14,
    "section": "Leave Policy"
}
```

Retrieval ke baad, teri application ko pata hai:

```
Chunk
 ↓
document_id
 ↓
source
 ↓
page
 ↓
section
```

Toh baad mein RAG ye generate kar sakta hai:

```
According to the Leave Policy,
employees receive 18 casual leaves per year.

Source: employee_handbook.pdf, page 14
```

**Yehi ek wajah hai ki metadata itna useful hai.**

## 16. Metadata Aur Document Updates

Maan le:

```
Policy 2025
```

ko replace kar diya jaata hai:

```
Policy 2026
```

se.

Tu filter kar sakta hai:

```sql
WHERE version = '2026'
```

ya ek:

```
is_active
```

field maintain kar sakta hai.

Example:

```sql
WHERE tenant_id = 42
  AND is_active = TRUE
```

Ab stale chunks retrieval mein nahi aate.

## 17. Metadata Filtering ≠ Security By Itself

**Important distinction:**

```
Metadata filter
        ≠
Complete authorization system
```

Ek robust architecture hai:

```
Authenticated User
       ↓
Authorization Service / trusted policy
       ↓
Allowed tenant/documents
       ↓
Retrieval filter
       ↓
Vector Search
       ↓
Results
```

Kabhi nahi:

```
LLM says:
"User is admin"
       ↓
Trust it
```

**Nahi.**

Same principle Phase 2 se yahan apply hoti hai:

> **LLM output untrusted input hai.**

## 18. Production RAG Retrieval

Ab hamari retrieval architecture ban rahi hai:

```
                     USER
                       │
                       ↓
                  User Query
                       │
                       ↓
                Query Embedding
                       │
                       ↓
             ┌──────────────────┐
             │ Retrieval Layer  │
             └────────┬─────────┘
                      │
             ┌────────┴─────────┐
             ↓                  ↓
      Metadata Filter      Vector Search
             │                  │
             └────────┬─────────┘
                      ↓
                   Ranking
                      ↓
                    Top-K
                      ↓
                Retrieved Chunks
                      ↓
                     LLM
```

Aur ab tu dekh sakta hai ki pichle topics kaise connect hote hain:

```
Chunking
   ↓
Embeddings
   ↓
Vector Storage
   ↓
Similarity Search
   ↓
Metadata Filtering
   ↓
Efficient Index
   ↓
RAG
```

## 🧠 Interview Questions

**Q1. Why use metadata filtering with vector search?**

> Retrieval ko un documents tak constrain karne ke liye jo deterministic conditions satisfy karte hain jaise tenant, permissions, document type, language, ya version, jabki semantic similarity us eligible set ke andar relevance determine karti hai.

**Q2. Can embeddings handle authorization?**

> Nahi.

> Authorization deterministic hona chahiye aur trusted backend logic se enforce hona chahiye.

**Q3. What is pre-filtering?**

> Candidate set ko metadata constraints use karke restrict karna, vector retrieval se pehle ya uska hissa banake.

**Q4. Why is multi-tenancy important in vector search?**

> Tenant isolation ke bina, doosre customer se semantically similar data ek retrieval candidate ban sakta hai, jisse correctness aur potentially serious data-isolation issues dono create ho sakte hain.

**Q5. Why not put every metadata field into the embedding?**

> Kyunki semantic representation deterministic filtering ka substitute nahi hai. Ek vector reliably ye enforce nahi kar sakta:

```
tenant = 42
```

ya:

```
user has permission
```