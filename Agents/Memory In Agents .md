# Module 5: Memory in AI Agents

> **Core agent architecture**

So far, we've taught an agent how to reason, use tools, and create
plans.

But what happens when an agent forgets everything after completing a
task or ending a conversation?

Imagine you're building a personal AI assistant.

You tell it: - You're a third-year IT engineering student. - You're
interested in backend engineering and Applied AI. - You prefer Python
for AI projects. - You're preparing for internships.

Tomorrow, you ask:

> Find some projects I should build next.

A memory-enabled agent can use relevant information from previous
interactions instead of asking you everything again.

That's the purpose of memory.

------------------------------------------------------------------------

## 1. What Is Memory in AI Agents?

**Memory** is the mechanism through which an agent stores, retrieves,
and uses information from previous interactions or experiences.

It helps an agent maintain context and make informed decisions over
time.

### Important Distinction

An LLM does not automatically remember every previous conversation.

The application or agent framework must provide the relevant information
again, usually through: - Conversation history. - Stored state. - A
retrieval mechanism.

------------------------------------------------------------------------

## 2. Types of Memory

There are several ways to classify agent memory. A useful engineering
classification is based on how long information is retained and what it
represents.

### A. Short-term Memory

Short-term memory stores information needed during the current task or
conversation.

**Example:**

You ask:

> Find three backend internships in Delhi.

The agent remembers: - Preferred role: Backend intern. - Location:
Delhi. - Experience level: Student.

It uses this information during the ongoing interaction.

**Common implementations:** - Conversation history. - In-memory state. -
Workflow state. - Context passed to the LLM.

Example state:

``` json
{
  "role": "Backend Intern",
  "location": "Delhi",
  "level": "Student"
}
```

Information remains available while the relevant state is retained.

### B. Long-term Memory

Long-term memory stores useful information across multiple conversations
or sessions.

**Example:**

An agent remembers that a user: - Prefers Python. - Has experience with
FastAPI. - Is interested in AI backend engineering. - Has already
applied to Company X.

This information can be retrieved in a future session.

**Common implementations:** - PostgreSQL. - Redis with appropriate
persistence. - Vector databases. - Document stores.

**Important:** A database does not automatically become an intelligent
memory system. You need policies for what to store, retrieve, update,
and forget.

### C. Episodic Memory

Episodic memory stores information about specific past events or
experiences.

Example:

``` json
{
  "event": "Applied to Backend Intern role",
  "company": "Example Technologies",
  "date": "2026-10-31",
  "outcome": "Application submitted"
}
```

It allows an agent to reason about what happened previously.

**Useful for:** - Application tracking. - Customer support history. -
Learning from previous task outcomes. - Remembering completed workflows.

### D. Semantic Memory

Semantic memory stores facts, concepts, and general knowledge.

Example:

``` json
{
  "skill": "Python",
  "proficiency": "Intermediate",
  "evidence": "Built FastAPI backend projects"
}
```

Unlike episodic memory, it doesn't necessarily record a particular
event. It represents information the agent considers useful and
reusable.

**Useful for:** - User profiles. - Preferences. - Product knowledge. -
Domain-specific information.

### E. Procedural Memory

Procedural memory stores information about how to perform a task.

Example:

``` text
To process a refund:
1. Verify customer identity.
2. Fetch the order.
3. Check refund eligibility.
4. Request approval if required.
5. Process the refund.
6. Record the transaction.
```

It represents reusable procedures rather than personal facts or
individual events.

------------------------------------------------------------------------

## 3. Understand the Difference

  Memory type   Stores                   Example
  ------------- ------------------------ -----------------------------
  Short-term    Current context          Current conversation
  Long-term     Persistent information   User profile
  Episodic      Past experiences         Previous job application
  Semantic      Facts and knowledge      User knows Python
  Procedural    How to do something      Refund processing procedure

These categories can overlap. For example, episodic and semantic
memories can both be stored in PostgreSQL.

------------------------------------------------------------------------

## 4. How Does an AI Agent Actually Remember?

Let's understand the architecture.

### Agent Memory Architecture

``` text
                  User Input
                      |
                      v
               Memory Retrieval
             Find relevant information
                      |
                      v
                Context Assembly
       User input + retrieved memory + instructions
                      |
                      v
                 LLM / Agent
              Reason and act
                      |
                      v
                 Memory Update
           Extract and store useful information
                      |
                      v
               Persistent Storage
          PostgreSQL / Redis / Vector DB
```

There are two major operations:

-   **Read path:** Retrieve relevant information before the agent acts.
-   **Write path:** Store useful new information after an interaction or
    task.

This is often called a **memory read/write pipeline**.

------------------------------------------------------------------------

## 5. Context Window vs. Memory

This is a very common interview question.

**They are NOT the same thing.**

-   **Context window:** The amount of information an LLM can process in
    a single request.
-   **Memory:** The mechanism used to preserve and retrieve information
    across interactions or tasks.

### Example

Imagine: - Your conversation contains 100,000 tokens. - Your model can
process only 20,000 tokens in its current context window.

You cannot simply pass everything to the model.

Instead, an agent can:

1.  Store conversation history.
2.  Summarize older conversations.
3.  Retrieve relevant information.
4.  Put that information into the current context.
5.  Generate a response.

Memory helps manage information beyond the current context window.

------------------------------------------------------------------------

## 6. How Does Vector Memory Work?

Now we reach an important technical concept.

Suppose you store these three memories:

1.  "I am interested in backend engineering."
2.  "I have experience building REST APIs using FastAPI."
3.  "I enjoy playing cricket."

A user asks:

> What technical projects should I build to improve my internship
> chances?

A traditional database query might search for an exact word such as
`internship`.

But semantic retrieval can identify that memories 1 and 2 are relevant,
even if the query uses different wording.

This is where **embeddings** come in.

### Step 1: Convert Text into Embeddings

An embedding model converts text into a numerical vector.

``` python
text = "I enjoy backend engineering"

embedding = embedding_model.encode(text)

print(embedding)
```

Illustrative output:

``` python
[0.12, -0.45, 0.81, 0.23, ...]
```

This vector represents semantic information about the text.

### Step 2: Store Embeddings

A vector database stores: - The embedding. - Original text or a
reference to it. - Metadata. - User or session identifiers.

### Step 3: Retrieve Relevant Memories

When the user asks a question:

1.  Convert the question into an embedding.
2.  Search for similar vectors.
3.  Retrieve the closest matches.
4.  Pass relevant memories to the LLM.

### Semantic Memory Retrieval

``` text
User Query
"Suggest projects for backend internships"
             |
             v
       Embedding Model
          Text → Vector
             |
             v
     Vector Similarity Search
   Find semantically relevant memories
             |
             v
      Retrieved Memories
 Backend experience · FastAPI · REST APIs
             |
             v
      LLM Generates a
      Contextual Response
```

### What Is Cosine Similarity?

A common way to measure how similar two embedding vectors are is cosine
similarity.

\[ `\text{Similarity}`{=tex}(A,B)= `\frac{A\cdot B}{\|A\|\|B\|}`{=tex}
\]

A higher value generally means the vectors point in a more similar
direction.

**Remember:** Semantic similarity does not guarantee factual relevance.
Retrieval results still need filtering and validation.

------------------------------------------------------------------------

## 7. Where Does RAG Fit In?

Retrieval-Augmented Generation (RAG) and agent memory are related, but
they are not identical.

  -----------------------------------------------------------------------
  RAG                                 Agent Memory
  ----------------------------------- -----------------------------------
  Retrieves external knowledge        Retrieves past information and
                                      experiences

  Often uses documents                Can use conversations, events,
                                      facts, and procedures

  Grounds LLM responses               Maintains continuity and context

  Usually read-focused                Often has read and write operations
  -----------------------------------------------------------------------

An agent can use RAG as part of its memory architecture.

**Example:** - RAG retrieves company documentation. - Episodic memory
retrieves previous customer interactions. - Semantic memory retrieves
customer preferences.

The agent combines these sources to make a decision.

------------------------------------------------------------------------

## 8. Which Databases Should You Use?

  Technology                   Best suited for
  ---------------------------- --------------------------------------------
  PostgreSQL                   Structured facts, user profiles, history
  Redis                        Fast temporary state and caching
  pgvector                     Vector similarity search inside PostgreSQL
  Dedicated vector databases   Large-scale semantic retrieval
  Object storage               Large documents and files

**Recommendation from the lesson:** Don't introduce five databases into
one project just because they are available.

PostgreSQL + pgvector is a reasonable starting point for many agent
applications.

------------------------------------------------------------------------

## 9. Production Challenges in Agent Memory

An engineer must handle these problems:

1.  **Memory pollution:** Storing irrelevant information.
2.  **Incorrect memories:** Saving hallucinated facts.
3.  **Stale information:** Using outdated preferences or details.
4.  **Privacy:** Storing sensitive information unnecessarily.
5.  **Retrieval errors:** Returning irrelevant memories.
6.  **Context overload:** Sending too much retrieved information to the
    LLM.
7.  **Multi-user isolation:** Accidentally retrieving one user's
    memories for another user.

### Useful Engineering Techniques

-   Memory relevance scoring.
-   Metadata filtering.
-   Time-based expiration.
-   Memory update and deletion policies.
-   User-level access control.
-   Retrieval evaluation.
-   Summarization and deduplication.

------------------------------------------------------------------------

## 10. Interview Questions

Make sure you can explain these:

### Q1. What's the difference between short-term and long-term memory?

Short-term memory retains information needed for the current task or
conversation. Long-term memory preserves useful information across
sessions and retrieves it when needed.

### Q2. What's the difference between episodic and semantic memory?

Episodic memory stores specific past events or experiences. Semantic
memory stores reusable facts, concepts, and knowledge.

### Q3. Is a context window the same as memory?

No. A context window is the amount of information a model can process in
one request. Memory is the mechanism for storing and retrieving
information across interactions or tasks.

### Q4. What are embeddings?

Embeddings are numerical vector representations of data, such as text.
They allow systems to compare semantic similarity between pieces of
information.

### Q5. How does vector similarity search work?

The system converts a query into an embedding, compares it with stored
vectors using a similarity metric, retrieves the closest matches, and
provides relevant results to the model.

### Q6. What's the difference between RAG and agent memory?

RAG retrieves external knowledge to ground responses. Agent memory
maintains information from past interactions, events, facts, and
procedures. An agent can use RAG as part of its memory architecture.

### Q7. Why shouldn't an agent store every conversation?

Storing everything can introduce irrelevant or incorrect information,
increase storage and retrieval costs, create privacy risks, and overload
the model's context. Memory should be selected based on usefulness and
retention policies.

### Q8. How would you prevent one user's memory from leaking into another user's session?

Enforce user-level access control in the storage and retrieval layers.
Scope every memory query by the authenticated user's identity, validate
ownership on reads and writes, and test cross-user isolation.

------------------------------------------------------------------------

## 11. Quick Revision

  Term                Remember
  ------------------- ---------------------------------------------------
  Short-term memory   Current task or conversation context
  Long-term memory    Information retained across sessions
  Episodic memory     Specific past events and experiences
  Semantic memory     Facts and reusable knowledge
  Procedural memory   How to perform a task
  Context window      Information a model can process in one request
  Embedding           Numerical vector representation
  Vector search       Retrieves semantically similar information
  Cosine similarity   Measures the angle-based similarity of vectors
  RAG                 Retrieves external knowledge to ground generation
  Memory read path    Retrieve relevant information
  Memory write path   Store useful new information

**Core architecture to remember:**

``` text
User Input
    |
    v
Retrieve Relevant Memory
    |
    v
Assemble Current Context
    |
    v
LLM / Agent Performs Task
    |
    v
Extract Useful New Information
    |
    v
Validate and Store Memory
```

**Interview one-liner:** Agent memory is an application-managed
mechanism for storing, retrieving, and updating useful information so an
agent can maintain context and continuity across tasks and
conversations.
