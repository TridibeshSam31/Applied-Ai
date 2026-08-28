# Applied AI

An engineering-first roadmap and implementation repository for building **production-oriented AI systems**.

This repository focuses on **Applied AI / AI Backend Engineering** — understanding how modern LLM-powered systems work internally, how they interact with tools and external systems, and how to make them reliable, observable, evaluable, and secure.

> **Understand the primitive first. Use frameworks second.**

---

## 🎯 Objective

The goal of this repository is not to learn AI by simply calling an LLM API.

The goal is to understand and build the systems around LLMs:

* How LLM APIs work
* How tool calling works internally
* How models interact with backend systems
* How semantic retrieval works
* How RAG systems are designed
* How MCP connects models with external capabilities
* How agents execute multi-step workflows
* How AI systems are evaluated
* How agent reliability is measured
* How AI-specific security failures are handled

Every major concept is paired with a practical engineering project.

---

# 🧭 Roadmap

```text
LLM Fundamentals
        ↓
Tool / Function Calling
        ↓
Embeddings
        ↓
Vector Databases
        ↓
RAG
        ↓
MCP
        ↓
Agents
        ↓
LLM Evaluations
        ↓
Agent Evaluations
        ↓
AI Security
```

---

# 📚 Topics

## 1. LLM Fundamentals / APIs 🔴

Focus on engineering-relevant LLM concepts rather than unnecessary theory.

### Topics

* Tokens
* Context windows
* Temperature / Top-p
* System / User messages
* Streaming
* Structured outputs
* API error handling
* Retries
* Rate limits
* Token & cost tracking

### Project — LLM Gateway

Build an API gateway that:

* Supports multiple models
* Streams responses
* Tracks token usage and cost
* Handles retries
* Logs requests
* Applies rate limits

```text
Client
  ↓
LLM Gateway
  ↓
Model Provider
  ↓
Streaming Response
```

---

# 2. Tool / Function Calling 🔴🔴

Tool calling is one of the core building blocks of modern AI applications.

### Topics

* Tool schemas
* JSON arguments
* Tool selection
* Execution loops
* Tool results
* Multiple tools
* Parallel tool calls
* Argument validation
* Retries
* Failure handling
* Authorization
* Observability

### Core Architecture

```text
User
 ↓
LLM
 ↓
Tool Call
 ↓
Backend
 ↓
Database / External API
 ↓
Tool Result
 ↓
LLM
 ↓
Response
```

### Project — Tool-Using Backend Agent

Implement the tool-calling loop manually before relying on an agent framework.

Example tools:

```text
search_customer()
get_invoice()
create_ticket()
update_ticket()
search_documents()
send_notification()
```

---

# 3. Embeddings 🟠

Understand how text can be represented as vectors and used for semantic retrieval.

### Topics

* Embeddings
* Vectors
* Cosine similarity
* Semantic similarity
* Embedding models
* Chunking basics

### Project — Semantic Code Search

Index your own repositories and build a semantic search system capable of finding relevant code based on meaning rather than exact keywords.

---

# 4. Vector Databases 🟠

Start with **PostgreSQL + pgvector** to understand vector storage without unnecessarily introducing another database.

### Topics

* Vector storage
* Similarity search
* Top-k retrieval
* HNSW
* IVF concepts
* Metadata filtering
* Hybrid search

### Project — Codebase Knowledge Engine

Build a searchable knowledge layer over a codebase using vector search and metadata filtering.

---

# 5. Retrieval-Augmented Generation (RAG) 🟠

Move beyond basic "PDF chatbot" implementations.

### Topics

* Document ingestion
* Chunking
* Embeddings
* Retrieval
* Reranking
* Context construction
* Grounding
* Citations
* Failure modes

### Project — Production RAG System

Use personal/project documentation or source code as the knowledge base.

```text
Documents
    ↓
Ingestion
    ↓
Chunking
    ↓
Embeddings
    ↓
Vector Store
    ↓
Retrieval
    ↓
Reranking
    ↓
Context Construction
    ↓
LLM
    ↓
Grounded Response
    ↓
Citations
```

---

# 6. Model Context Protocol (MCP) ⭐⭐⭐

MCP is a high-priority area of this roadmap.

### Topics

* MCP architecture
* Hosts
* Clients
* Servers
* Tools
* Resources
* Prompts
* Schemas
* Transport
* stdio
* HTTP
* Authentication
* Authorization
* Error handling
* Tool discovery

### Progression

```text
Backend Function
      ↓
Function Calling
      ↓
MCP Tool
      ↓
MCP Server
      ↓
AI Client / Agent
```

### Project — Production MCP Server

Expose backend capabilities through MCP.

Example:

```text
search_customer
get_invoice
create_ticket
query_database
search_codebase
```

The server should be usable from an MCP-compatible client such as Claude / Claude Code.

---

# 7. Agents ⭐⭐⭐

Agents are studied after understanding the primitives underneath them.

### Topics

* Agent loops
* State
* Observations
* Actions
* Memory
* Planning
* Multi-step execution
* Tool selection
* Retries
* Failure recovery
* Stopping conditions

Frameworks such as **LangGraph** are useful, but the underlying execution model should be understood first.

### Project — Enterprise Task Agent

Example workflow:

```text
Find unpaid invoice
        ↓
Check eligibility
        ↓
Create support ticket
        ↓
Notify customer
```

The complete trajectory should be stored so that the agent's decisions and failures can later be evaluated.

---

# 8. LLM Evaluations ⭐⭐⭐

A system that works on one demo is not necessarily a reliable AI system.

### Topics

* Evaluation datasets
* Golden datasets
* Deterministic evaluation
* Expected outcomes
* Rubrics
* LLM-as-a-judge
* Correctness
* Relevance
* Groundedness
* Hallucination
* Regression testing
* Cost
* Latency

### Project — LLM Eval Harness

```text
Dataset
   ↓
Model
   ↓
Output
   ↓
Evaluator
   ↓
Score
   ↓
Report
```

The evaluation system should make model and prompt changes measurable rather than subjective.

---

# 9. Agent Evaluations ⭐⭐⭐

Agent evaluation is different from evaluating a single LLM response.

The entire trajectory matters.

### Topics

* Trajectory evaluation
* Tool-call correctness
* Argument correctness
* Task completion
* State-based evaluation
* Failure classification
* Benchmark design
* Agent reliability

### Project — Agent Benchmark Platform

```text
Task
 ↓
Agent
 ↓
Trajectory
 ↓
┌─────────────────┐
│ Tool Evaluation │
│ State Evaluation│
│ Final Evaluation│
│ Cost            │
│ Latency         │
└─────────────────┘
 ↓
Overall Score
```

---

# 10. AI Security 🟠

Focus on security problems specific to LLM-powered systems and agents.

### Topics

* Prompt injection
* Indirect prompt injection
* Tool poisoning
* Excessive agency
* Data exfiltration
* RAG poisoning
* System prompt leakage
* Malicious tool output

### Project — Agent Security Playground

Build controlled examples of common AI security failures and implement defensive mechanisms around them.

---

# 🏗️ Project Philosophy

Every topic follows the same progression:

```text
Learn
  ↓
Understand the primitive
  ↓
Implement from scratch
  ↓
Build a backend system
  ↓
Add reliability
  ↓
Add observability
  ↓
Evaluate
  ↓
Secure
  ↓
Deploy
```

The objective is to avoid building disconnected AI demos.

Instead, projects should progressively demonstrate the engineering required to turn AI capabilities into reliable backend systems.

---

# 🛠️ Technology Direction

The stack will evolve as the projects become more complex.

Current direction:

* **Python**
* **FastAPI**
* **PostgreSQL**
* **pgvector**
* **Redis / Message Queues**
* **LLM APIs**
* **MCP**
* **LangGraph**
* **Docker**
* **Cloud deployment**

Tools and frameworks are not the goal.

**Understanding the architecture is the goal.**

---

# 📂 Repository Structure

```text
Applied-Ai/
│
├── LLM Fundamentals/
│   └── ...
│
├── topics.txt
│
└── README.md
```

As the roadmap progresses, this repository will contain:

```text
Notes
Experiments
Implementations
Backend Services
AI Systems
Evaluation Suites
Security Experiments
Projects
```

---

# 🚀 Progress

This repository is actively being developed.

The roadmap will evolve from fundamentals and experiments into increasingly production-oriented implementations.

### Current Focus

* [x] Define Applied AI roadmap
* [ ] LLM Fundamentals
* [ ] LLM Gateway
* [ ] Tool / Function Calling
* [ ] Semantic Code Search
* [ ] Vector Database
* [ ] Production RAG
* [ ] MCP
* [ ] Agents
* [ ] LLM Evals
* [ ] Agent Evals
* [ ] AI Security

---

# 🎯 End Goal

Build the ability to design and implement AI systems that are:

```text
Useful
  +
Reliable
  +
Observable
  +
Evaluable
  +
Secure
  +
Scalable
```

The end goal is **not** to become someone who can simply call an LLM API.

The goal is to become an engineer who can take an AI capability and build the **backend infrastructure, tools, retrieval systems, agents, evaluations, and safeguards around it**.

---

## 👤 Author

**Tridibesh Samantroy**

Engineering student focused on:

* Backend Engineering
* Distributed Systems
* Applied AI
* AI Backend Engineering

Learning by building systems, understanding their internals, and iterating toward production quality.
