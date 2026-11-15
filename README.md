# Applied AI

An engineering-first roadmap and implementation repository for building **production-grade AI systems**.

This repository covers **Applied AI and AI Backend Engineering**: how LLM-powered systems work internally, how they interact with tools and external systems, and how to make them reliable, observable, measurable, and secure.

> **Understand the primitive first. Use frameworks second.**

---

## Table of Contents

1. [Objective](#objective)
2. [Roadmap](#roadmap)
3. [Curriculum and Status](#curriculum-and-status)
4. [Projects](#projects)
5. [Flagship Capstone: Coding Agent Platform and RL Environment](#flagship-capstone-coding-agent-platform-and-rl-environment)
6. [Repository Structure](#repository-structure)
7. [Methodology](#methodology)
8. [Technology Direction](#technology-direction)
9. [Author](#author)

---

## Objective

The goal is not to learn AI by calling an LLM API. The goal is to understand and build the systems around LLMs:

- How LLM APIs behave, fail, and are metered
- How tool calling works internally and how it is secured
- How semantic retrieval and RAG systems are designed
- How MCP exposes backend capabilities to models
- How single agents and multi-agent systems plan, remember, and recover from failure
- How agents are evaluated, and how environments with verifiable rewards are built
- How AI-specific security failures arise and are mitigated

Every major area is paired with a practical engineering project.

---

## Roadmap

```text
LLM Fundamentals
      ↓
Tool / Function Calling
      ↓
Embeddings  →  Vector Databases
      ↓
RAG
      ↓
MCP
      ↓
Agents
      ↓
Multi-Agent Systems
      ↓
Evaluations and RL Environments
      ↓
AI Security
      ↓
Capstone: Coding Agent Platform + Coding RL Environment
```

---

## Curriculum and Status

Status legend: **Complete** (notes written), **In progress**, **Planned**.

| # | Area | Scope | Status |
|---|------|-------|--------|
| 1 | [LLM Fundamentals](./LLM%20Fundamentals) | Tokens, context window, token limits, role-based messages, temperature vs top-p, streaming, structured outputs, error reading, retries, rate limits | Complete |
| 2 | [Tool Calling](./Tool%20Calling) | Fundamentals, schemas, selection, execution, chaining, parallel calls, security, observability | Complete |
| 3 | [Embeddings and Vector DB](./Embeddings%20%26%20Vector%20DB) | Embedding fundamentals and models, dimensions, similarity metrics, chunking, pgvector, similarity search, metadata filtering, HNSW and IVF, hybrid search | Complete |
| 4 | [RAG](./RAG) | Ingestion, chunking, retrieval, reranking, context construction, query transformation, hybrid RAG, evaluation, production architecture | In progress (topic list drafted) |
| 5 | [MCP Engineering Handbook](./mcp-engineering-handbook) | Architecture, primitives, JSON-RPC lifecycle, transports, Python SDK, FastAPI authentication, authorization and threats, observability, production design, Claude integration | Complete |
| 6 | [Agents](./Agents) | Foundations, ReAct, tool architecture, planning and decomposition, memory, state management, single-agent architecture, error handling, Alembic migrations | Complete |
| 7 | [Multi-Agent Systems](./Multi-Agent%20Systems) | Architectures, communication, orchestration and delegation, shared memory, parallel vs sequential execution, conflict resolution and failure handling | Complete |
| 8 | Evaluations and RL Environments | Eval datasets, deterministic verifiers, LLM-as-a-judge, trajectory evaluation, reward design, reward hacking, benchmark construction | Planned |
| 9 | [AI Security](./Ai%20Security) | Prompt injection, indirect injection, tool poisoning, RAG poisoning, data exfiltration, excessive agency, system prompt leakage, malicious tool output | Complete (notes) |

The detailed learning order is maintained in [`topics.txt`](./topics.txt).

---

## Projects

Each area has an associated implementation project. Notes come first; implementations follow.

| Area | Project | Description | Status |
|------|---------|-------------|--------|
| LLM Fundamentals | **LLM Gateway** | Multi-model API gateway with streaming, token and cost tracking, retries, request logging, and rate limiting | Planned |
| Tool Calling | **Tool-Using Backend Agent** | Hand-written tool-calling loop over a realistic backend (customers, invoices, tickets), without an agent framework | Planned |
| Embeddings | **Semantic Code Search** | Meaning-based search over personal repositories | Planned |
| Vector DB | **Codebase Knowledge Engine** | pgvector-backed knowledge layer with metadata filtering and hybrid search | Planned |
| RAG | **Production RAG System** | Grounded, cited answers over project documentation and source code, with reranking and failure-mode handling | Planned |
| MCP | **Customer Support MCP Server** | Authenticated, tenant-isolated MCP server with idempotent mutations, audit logging, and contract and security tests ([spec](./mcp-engineering-handbook/project/README.md)) | Specification complete |
| Agents | **Enterprise Task Agent** | Multi-step workflow agent (find unpaid invoice, check eligibility, create ticket, notify customer) with full trajectory storage | Planned |
| Evals | **LLM Eval Harness** | Dataset, model, evaluator, score, and report pipeline that makes prompt and model changes measurable | Planned |
| Security | **Agent Security Playground** | Controlled reproductions of common AI security failures with defensive mechanisms | Planned |
| Capstone | **Coding Agent Platform + Coding RL Environment** | See below | Planned |

---

## Flagship Capstone: Coding Agent Platform and RL Environment

The capstone combines the earlier areas into one system: a coding agent that runs both as a local CLI and as a cloud service, evaluated inside a reproducible environment with verifiable rewards.

### Components

| Component | Description |
|-----------|-------------|
| **Agent core** | Agent loop, planning, tool set (read, edit, search, shell), context management, permission tiers, retry and recovery logic |
| **CLI agent** | Terminal interface in the style of Claude Code: streaming output, local tool execution, approval prompts for risky actions, session persistence |
| **Cloud agent** | Job queue, one isolated sandbox per task, repository clone, agent execution, pull request creation, live progress streaming, cancellation and cost limits |
| **Sandbox layer** | Container isolation, resource limits, timeouts, network policy, secrets handling, parallel episode execution |
| **Coding RL environment** | Task specification, reproducible sandbox per episode, deterministic verifier (hidden tests) producing a reward, Gym-style `reset` / `step` interface, full trajectory logging |
| **Eval suite** | 50 to 100 hand-verified tasks, validated against flaky tests and reward hacking, reporting pass rate, cost, latency, step count, and failure categories across models and agent variants |
| **Observability** | Per-run traces covering tool calls, tokens, cost, latency, and decisions |

### Architecture

```text
            ┌────────────────────────────┐
            │      Task Specification     │
            │ (repo snapshot, issue, tools)│
            └──────────────┬─────────────┘
                           ↓
 ┌───────────┐     ┌───────────────┐     ┌────────────────┐
 │ CLI Agent │ ──→ │  Agent Core   │ ←── │  Cloud Agent   │
 └───────────┘     │ plan · act ·  │     │ queue · PR · UI│
                   │ recover       │     └────────────────┘
                   └───────┬───────┘
                           ↓
                ┌─────────────────────┐
                │  Isolated Sandbox   │
                │ (container per run) │
                └──────────┬──────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │ Verifier (hidden tests) → Reward      │
        │ Trajectory log → Eval report          │
        └──────────────────────────────────────┘
```

### Success criteria

- The CLI agent resolves a failing test in a real repository end to end, with approvals and logging
- The environment is reproducible: the same task and the same solution produce the same reward
- Verifiers reject incorrect solutions and resist reward hacking
- A published pass-rate table compares at least two models and several agent configurations, with categorized failures
- Security posture is documented: permission tiers, sandbox escape tests, and prompt-injection defenses drawn from the AI Security notes

### Build order

1. Agent core and CLI
2. Sandbox layer
3. Task format, verifier, and Gym-style environment
4. Eval suite and reporting
5. Cloud mode (queue, sandbox-per-task, PR creation, streaming UI)

---

## Repository Structure

```text
Applied-Ai/
├── LLM Fundamentals/            # Tokens, context, sampling, streaming, structured outputs, errors, retries, rate limits
├── Tool Calling/                # Schemas, selection, execution, chaining, parallel calls, security, observability
├── Embeddings & Vector DB/      # Embeddings, similarity metrics, chunking, pgvector, HNSW/IVF, hybrid search
├── RAG/                         # Topic list for the RAG module
├── mcp-engineering-handbook/    # 10-topic MCP handbook, references, and capstone specification
├── Agents/                      # Foundations, ReAct, planning, memory, state, errors, tool architecture
├── Multi-Agent Systems/         # Architectures, communication, orchestration, shared memory, failure handling
├── Ai Security/                 # Eight AI-specific security topics
├── topics.txt                   # Full learning roadmap
└── README.md
```

Each topic folder contains written notes (`notes.md`), with runnable code where relevant.

---

## Methodology

Every topic follows the same progression:

```text
Learn → Understand the primitive → Implement from scratch → Build a backend system
      → Add reliability → Add observability → Evaluate → Secure → Deploy
```

The aim is to avoid disconnected demos. Each project should show the engineering required to turn an AI capability into a dependable backend system.

---

## Technology Direction

| Layer | Tools |
|-------|-------|
| Language and services | Python, FastAPI |
| Data | PostgreSQL, pgvector, Redis |
| Queues and execution | Message queues, Docker sandboxes |
| Models and protocols | LLM provider APIs, MCP |
| Orchestration | LangGraph (after understanding the underlying execution model) |
| Delivery | Docker, cloud deployment |

Tools are chosen to serve the architecture, not the other way around.

---

## Author

**Tridibesh Samantroy**
B.Tech Information Technology, Bharati Vidyapeeth's College of Engineering, New Delhi

Focus areas: backend engineering, distributed systems, applied AI, and AI backend engineering.

[GitHub](https://github.com/TridibeshSam31)
