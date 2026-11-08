# Agent Communication & Message Passing

## 1. Why Do Agents Need Communication?

In the previous topic, we explored five multi-agent architectures:

-   Sequential
-   Supervisor
-   Network
-   Hierarchical
-   Handoff

Now consider an important question:

**How do agents communicate with one another?**

Imagine an AI software development system with three agents:

-   Research Agent
-   Developer Agent
-   Testing Agent

The Research Agent discovers requirements. The Developer Agent needs
those requirements to generate code. The Testing Agent needs the
generated code to test it.

``` text
Research Agent
Discovers requirements
       |
       | Message
       v
Developer Agent
Receives requirements and generates code
       |
       | Message
       v
Testing Agent
Receives code and tests it
```

Without communication, the agents remain independent and cannot
coordinate to complete the overall task.

## 2. What Is Agent Communication?

Agent communication is the process through which agents exchange
information, instructions, task requests, results, and feedback.

A message can generally contain:

1.  Sender identity
2.  Receiver identity
3.  Message content
4.  Task information
5.  Execution status
6.  Additional metadata

### Example: Structured message

The Research Agent sends a message to the Developer Agent:

``` json
{
  "sender": "research_agent",
  "receiver": "developer_agent",
  "message_type": "task_assignment",
  "content": {
    "task": "Build a student management REST API",
    "requirements": [
      "Create student",
      "Get student",
      "Update student",
      "Delete student"
    ]
  }
}
```

This is a structured message rather than unstructured text. Structured
communication makes it easier for agents to process information
consistently.

## 3. Types of Agent Communication

### A. Direct Communication

One agent directly sends information to another agent.

``` text
Agent A  ───── Message ─────>  Agent B
```

Example:

``` python
def research_agent():
    return {
        "topic": "REST API",
        "requirements": [
            "Create endpoint",
            "Read endpoint"
        ]
    }


def developer_agent(message):
    print("Received:", message)
    return "API code generated"


research_result = research_agent()

developer_result = developer_agent(
    research_result
)

print(developer_result)
```

The Research Agent's output is passed directly to the Developer Agent.

**Use case:** Simple sequential workflows.

### B. Communication Through a Supervisor

Agents do not directly send messages to one another. The Supervisor
coordinates communication and routes relevant information.

``` text
Research Agent
      |
      v
  Supervisor
      |
      v
Developer Agent
      |
      v
  Supervisor
      |
      v
 Testing Agent
```

**Use case:** Supervisor-based architectures.

### C. Communication Through Shared State

Agents access and update a common state object.

Example initial state:

``` python
state = {
    "requirements": None,
    "generated_code": None,
    "test_results": None
}
```

Research Agent:

``` python
def research_agent(state):
    state["requirements"] = [
        "Create student",
        "Get student"
    ]

    return state
```

Developer Agent:

``` python
def developer_agent(state):
    requirements = state["requirements"]

    state["generated_code"] = (
        f"Generated code for {requirements}"
    )

    return state
```

Testing Agent:

``` python
def testing_agent(state):
    code = state["generated_code"]

    state["test_results"] = "Tests passed"

    return state
```

Execution:

``` python
state = research_agent(state)
state = developer_agent(state)
state = testing_agent(state)

print(state)
```

The agents exchange information by reading and updating a shared data
structure.

**Use cases:** LangGraph workflows, shared execution context, and
stateful systems.

## 4. Message Passing vs Shared State

This distinction is important.

  -----------------------------------------------------------------------
  Message Passing                     Shared State
  ----------------------------------- -----------------------------------
  An agent sends information          An agent updates common state

  Sender and receiver can be explicit Multiple agents can access the
                                      state

  Messages represent individual       State represents current workflow
  exchanges                           data

  Communication history can be        Latest shared values are accessible
  maintained                          
  -----------------------------------------------------------------------

Message-passing example:

``` python
developer_agent.send(
    message="Requirements are ready"
)
```

Shared-state example:

``` python
state["requirements"] = requirements
```

**Important:** These approaches are not mutually exclusive. A system can
use both messages and shared state.

## 5. Synchronous vs Asynchronous Communication

This connects multi-agent communication to backend engineering.

### Synchronous communication

Agent A calls Agent B and waits until Agent B returns a result.

``` python
result = developer_agent(requirements)
print(result)
```

Execution is blocked until the function returns.

### Asynchronous communication

A task can be awaited or run concurrently with other tasks.

Python example:

``` python
import asyncio


async def research_agent():
    await asyncio.sleep(2)
    return "Research completed"


async def developer_agent():
    await asyncio.sleep(3)
    return "Development completed"


async def main():
    results = await asyncio.gather(
        research_agent(),
        developer_agent()
    )

    print(results)


asyncio.run(main())
```

Possible output:

``` text
['Research completed', 'Development completed']
```

Both tasks execute concurrently.

**Important:** Async programming does not automatically create a
Multi-Agent System. This example only runs concurrent tasks. Real agents
also need independent decision-making, tools, communication, and
coordination.

## 6. Communication Protocols

In complex systems, agents need a common message format and rules for
communication.

  Protocol / Approach   Purpose
  --------------------- ----------------------------------
  JSON messages         Structured information exchange
  HTTP / REST           Service-to-service communication
  WebSockets            Persistent two-way communication
  Message queues        Asynchronous message delivery
  Shared state          Common workflow information
  A2A                   Agent-to-agent interoperability

### A2A Protocol

Agent2Agent (A2A) is a protocol that provides standard mechanisms for
independently developed agents to communicate and collaborate.

Example:

-   Company A has a Research Agent.
-   Company B has a Data Analysis Agent.

They may use different frameworks and infrastructure but can interact
through A2A.

### A2A vs MCP

Do not confuse these two:

-   **MCP:** Helps an AI application connect to tools and external
    context.
-   **A2A:** Helps independent agents communicate and collaborate with
    one another.

## 7. Build a Practical Message-Passing System

Let's define a message structure using Pydantic.

### Step 1 --- Define the message schema

``` python
from pydantic import BaseModel, Field
from typing import Any
from uuid import uuid4


class AgentMessage(BaseModel):
    message_id: str = Field(
        default_factory=lambda: str(uuid4())
    )
    sender: str
    receiver: str
    message_type: str
    content: dict[str, Any]
```

The `message_id` is generated separately for every message.

### Step 2 --- Create the Research Agent

``` python
def research_agent():
    return AgentMessage(
        sender="research_agent",
        receiver="developer_agent",
        message_type="task_assignment",
        content={
            "task": "Build Student REST API",
            "requirements": [
                "Create student",
                "Get student",
                "Update student"
            ]
        }
    )
```

### Step 3 --- Create the Developer Agent

``` python
def developer_agent(message: AgentMessage):
    if message.receiver != "developer_agent":
        raise ValueError("Wrong receiver")

    requirements = message.content["requirements"]

    print("Received requirements:", requirements)

    return AgentMessage(
        sender="developer_agent",
        receiver="testing_agent",
        message_type="code_ready",
        content={
            "code": "Student API implementation",
            "requirements": requirements
        }
    )
```

### Step 4 --- Execute the communication

``` python
research_message = research_agent()

developer_message = developer_agent(
    research_message
)

print(developer_message.model_dump())
```

One agent generates a structured message, and another agent receives and
processes it.

**Note:** This is a message-passing simulation, not production messaging
infrastructure. Real systems must also handle message validation,
authentication, delivery guarantees, timeouts, and correlation IDs.

## 8. Advanced Concepts

  Concept                      Meaning
  ---------------------------- ----------------------------------------
  Message Queue                Temporarily stores messages
  Event-driven communication   Activates agents based on events
  Correlation ID               Identifies related messages
  Message Routing              Sends a message to the correct agent
  Acknowledgement (ACK)        Confirms message processing
  Dead Letter Queue            Stores repeatedly failed messages
  Message Ordering             Maintains the correct message sequence

For example, if Agent B is unavailable, a message queue can temporarily
store a message and deliver it later.

This is an important part of distributed systems engineering.

## 9. Connection with Our Customer Support Agent

Original single-agent project:

``` text
User
  |
  v
Single Agent
  |
  +---- get_order_status()
  |
  +---- create_support_ticket()
  |
  v
Backend
```

A possible future multi-agent design:

``` text
             Customer
                 |
                 v
          Supervisor Agent
                 |
                 v
            Triage Agent
                 |
        +--------+--------+
        |        |        |
        v        v        v
      Order   Billing   Ticket
      Agent    Agent    Agent
        |        |        |
        +--------+--------+
                 |
                 v
          Final Response
```

Messages between agents may transfer:

-   Customer requests
-   Order information
-   Task status
-   Execution results

**Security boundary:** Customer identity and authorization must remain
under backend control. An agent message must not be treated as proof
that a user is authorized to access a resource.

## 10. Quick Revision

-   Agent communication is the exchange of information, instructions,
    requests, results, and feedback between agents.
-   Messages can contain sender, receiver, message type, content,
    status, and metadata.
-   Direct communication passes output from one agent to another.
-   A supervisor can coordinate and route information between agents.
-   Shared state allows multiple agents to read and update common
    workflow data.
-   Message passing and shared state can be used together.
-   Synchronous calls wait for a result; asynchronous execution can
    allow concurrent work.
-   Async programming alone does not create a Multi-Agent System.
-   MCP connects AI applications with tools and external context; A2A
    supports communication between independent agents.
-   Production messaging requires validation, authentication, delivery
    handling, timeouts, and traceability.

**Core takeaway:** Multi-agent systems need a reliable way to exchange
structured information. The communication mechanism should match the
architecture, execution model, and reliability requirements.
