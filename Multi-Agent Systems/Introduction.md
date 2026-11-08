# Topic 1: Introduction to Multi-Agent Systems

## 1. First Understand the Problem

Imagine building an AI-powered travel planning application.

A user asks:

> Plan a 5-day trip to Japan within ₹1 lakh.

A single agent may need to research destinations, find hotels, calculate
transportation costs, plan daily activities, check the budget, and
generate an itinerary.

A single agent can handle these tasks, but as the task becomes more
complex, its instructions, tool usage, and reasoning can become harder
to manage.

We can divide responsibilities among specialized agents:

``` text
User Request: Plan a 5-day Japan trip under ₹1 lakh
                         |
                         v
                 Orchestrator Agent
               Understands and delegates
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
     Research Agent  Hotel Agent   Budget Agent
          |              |              |
          +--------------+--------------+
                         |
                  Itinerary Agent
                         |
                         v
                  Orchestrator
             Combines and validates outputs
                         |
                         v
                  Final Travel Plan
```

This is a basic example of a **Multi-Agent System (MAS)**.

## 2. What Is a Multi-Agent System?

A Multi-Agent System is a system in which multiple autonomous agents
interact or coordinate to achieve individual or shared objectives.

Each agent can have: - Its own instructions. - Its own tools. - Its own
responsibilities. - Its own context or memory. - Its own decision-making
process.

Agents coordinate through communication and task delegation.

**Important:** An agent does not necessarily need a separate LLM or
server. Multiple agents can share the same model, infrastructure, and
database while maintaining different roles and contexts.

## 3. Single Agent vs Multi-Agent

  -----------------------------------------------------------------------
  Single Agent                        Multi-Agent
  ----------------------------------- -----------------------------------
  One agent handles the task          Multiple agents share
                                      responsibilities

  One primary instruction set         Different role-specific
                                      instructions

  Simpler coordination                Requires coordination

  Easier to debug                     More complex debugging

  Lower orchestration overhead        Higher orchestration overhead

  Good for focused tasks              Useful for complex tasks requiring
                                      specialization
  -----------------------------------------------------------------------

### Important engineering insight

Multi-Agent is not automatically better.

Suppose a customer support agent only needs to: 1. Check order status.
2. Create a support ticket.

A single agent with two tools is probably sufficient. Introducing five
agents would increase latency, cost, and failure points without
providing meaningful benefits.

**Use multiple agents when decomposition provides a real advantage.**

## 4. Core Characteristics of Multi-Agent Systems

### A. Autonomy

Each agent can make decisions within its assigned responsibilities.

Example: A research agent independently decides which sources to
investigate.

### B. Specialization

Each agent focuses on a particular domain.

Examples: - Research Agent → Information retrieval. - Budget Agent →
Financial calculations. - Reviewer Agent → Quality verification.

### C. Communication

Agents exchange information through messages, structured outputs, shared
state, or other communication mechanisms.

### D. Coordination

Agents organize their activities to avoid conflicting or duplicated
work.

### E. Cooperation

Agents work towards a shared objective.

These properties help distinguish a properly designed MAS from a
collection of unrelated LLM calls.

## 5. Understand the Code: Build a Simple Multi-Agent Workflow

We'll build a tiny multi-agent-style workflow without LangGraph first.
The goal is to understand the underlying architecture before introducing
a framework.

We'll use Python functions to simulate specialized agents. Initially,
this implementation is deterministic; later, the functions can be
replaced with actual LLM-powered agents.

### Step 1 --- Create specialized agents

``` python
def research_agent(destination):
    return {
        "destination": destination,
        "places": ["Tokyo", "Kyoto", "Osaka"]
    }


def budget_agent(budget):
    return {
        "total_budget": budget,
        "hotel_budget": budget * 0.30,
        "food_budget": budget * 0.25,
        "travel_budget": budget * 0.30,
        "other_budget": budget * 0.15
    }


def itinerary_agent(places):
    return {
        "day_1": places[0],
        "day_2": places[1],
        "day_3": places[2],
        "day_4": "Local exploration",
        "day_5": "Departure"
    }
```

Each function has a specific responsibility: - `research_agent()`
returns destination information. - `budget_agent()` divides the supplied
budget into categories. - `itinerary_agent()` creates a basic five-day
itinerary from the supplied places.

### Step 2 --- Build the orchestrator

``` python
def orchestrator(destination, budget):
    research = research_agent(destination)

    budget_details = budget_agent(budget)

    itinerary = itinerary_agent(
        research["places"]
    )

    return {
        "research": research,
        "budget": budget_details,
        "itinerary": itinerary
    }


result = orchestrator(
    destination="Japan",
    budget=100000
)

print(result)
```

### What happened?

``` text
             Orchestrator
                  |
       +----------+----------+
       |          |          |
       v          v          v
   Research     Budget    Itinerary
    Agent       Agent       Agent
       |          |          |
       +----------+----------+
                  |
                  v
            Combined Result
```

The orchestrator calls specialized components and combines their
outputs.

**Important distinction:** This is currently a deterministic
multi-component workflow, not a fully autonomous LLM-based MAS. The
functions do not reason independently, use LLMs to select actions, or
dynamically delegate tasks. The orchestrator follows a predefined
sequence.

Using multiple functions does not automatically mean that we have built
autonomous AI agents.

## 6. Important Terminology

  Term                  Meaning
  --------------------- ----------------------------------------------
  Agent                 Autonomous decision-making component
  Orchestrator          Coordinates agents and tasks
  Delegation            Assigning work to another agent
  Specialized Agent     Agent with a focused responsibility
  Shared State          Information accessible across workflow steps
  Agent Communication   Exchange of information between agents
  Coordination          Managing dependencies and interactions

These terms will appear repeatedly in LangGraph and multi-agent
architecture discussions.

## 7. When Should You Use Multi-Agent Systems?

### Good use cases

-   Complex research involving different domains.
-   Software development agents with coding, testing, and reviewing
    roles.
-   Financial research involving analysis and risk evaluation.
-   Customer support involving multiple specialized workflows.
-   Procurement negotiation involving buyer, supplier, and arbitrator
    agents.

### Poor use cases

-   Simple CRUD operations.
-   A basic chatbot.
-   One API call followed by a response.
-   A task that one agent can reliably handle using a few tools.

## 8. Quick Revision

-   A Multi-Agent System uses multiple agents that interact or
    coordinate to achieve objectives.
-   Agents can have separate roles, instructions, tools, context, and
    decision-making processes.
-   Agents do not necessarily require separate LLMs or servers.
-   An orchestrator coordinates tasks and combines agent outputs.
-   Specialization, autonomy, communication, coordination, and
    cooperation are core characteristics.
-   Multi-agent architecture adds coordination overhead, latency, cost,
    and debugging complexity.
-   Multiple functions or LLM calls do not automatically make a system
    an autonomous MAS.

**Core takeaway:** Use multiple agents when clear specialization and
coordination improve the solution. Do not add agents merely to make the
architecture look more advanced.
