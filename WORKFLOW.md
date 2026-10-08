# Agentic workflow

This document records the proposed development and rover-operation workflow.
The runtime observation/planning loop and autonomous exploration are proposals,
not implemented capabilities. See [README](README.md) for current capabilities
and [AGENTS](AGENTS.md) for agent instructions and authorization rules.

## Decision process

```mermaid
flowchart TD
    A([User request]) --> B[Read relevant project context]
    B --> C{Intent and scope clear?}
    C -- No --> D[Ask for clarification and wait]
    D --> B
    C -- Yes --> E[Identify requested actions and authorization]
    E --> F{Informational work only?}
    F -- Yes --> G[Inspect relevant files and explain findings]
    G --> R[Report evidence and relevant unknowns]
    F -- No --> H{Next action explicitly authorized?}
    H -- No --> I[Describe concrete action and request authorization]
    I --> H
    H -- Yes --> J{Action involves the rover?}

    J -- No --> K[Perform the authorized edit or offline operation]
    K --> L{Verification execution authorized?}
    L -- No --> M[Read back edits and report verification limits]
    M --> R
    L -- Yes --> N[Run relevant authorized checks]
    N --> O{Checks pass?}
    O -- No --> P{Repair within authorized scope?}
    P -- Yes --> K
    P -- No --> R
    O -- Yes --> Q{More requested work?}
    Q -- Yes --> E
    Q -- No --> R

    J -- Yes --> S[Establish connection and observations within authorized scope]
    S --> T{Evidence sufficient and action within bounds?}
    T -- No --> U[Stop session and report issue]
    T -- Yes --> V[Execute bounded operation through the controller]
    V --> W[Record commands and observed results]
    W --> X{Requested session complete?}
    X -- No --> E
    X -- Yes --> Y[Complete authorized standby and disconnect]
    Y --> R
    U --> R
    R --> Z([Done])
```

Editing, execution, testing, installation, simulation, and hardware operations
must be covered by explicit authorization. Authorization may cover several
actions or an entire defined session together; it need not be requested again
for each step within that scope. Observation, recording, and session stop actions
must also be included in the authorized hardware session.

## Agent hierarchy

```mermaid
flowchart TD
    USER[User: goals, scope, and authorization] --> MAIN[Main agent: plan, coordinate, and assess evidence]

    MAIN --> DEV[Development role: code and documentation]
    MAIN --> OBS[Observation role: images, sensors, and state estimation]
    MAIN --> PLAN[Planning role: choose a bounded action]
    MAIN --> REVIEW[Review role: assess outcomes and completion]

    OBS --> PLAN
    PLAN --> CTRL[Deterministic controller: validate limits, heartbeat, and stop]
    CTRL --> ROVER[Rover: UNO and ESP32-S3]
    ROVER --> DATA[Session evidence: commands, images, and sensor readings]
    DATA --> OBS
    DATA --> REVIEW
    REVIEW --> MAIN

    MAIN -. Only with explicit delegation request .-> SUB[Optional subagents: independent software or analysis work]
```

These roles describe responsibilities and can run within one main agent.
Subagents are optional and require an explicit user request. One controller
owns the rover TCP connection; concurrent agents do not independently drive it.

## Proposed runtime loop

```mermaid
flowchart LR
    OBS[Observe] --> EST[Estimate state and uncertainty]
    EST --> PLAN[Select bounded action]
    PLAN --> CHECK{Controller accepts action?}
    CHECK -- Yes --> ACT[Execute and record]
    ACT --> OBS
    CHECK -- No --> STOP[Stop and report reason]
```

The AI selects actions within an authorized session. Deterministic code enforces
command bounds and handles connection loss and stopping. Command acknowledgments
are recorded separately from observations of physical results.

## Proposed development sequence

1. Shared rover interface for commands, sensors, captures, and session logging.
2. Reliable manual sessions with coordinated observations and timing metadata.
3. Reconstruction from saved captures.
4. Bounded supervised exploration trials.
5. Autonomous exploration after state estimation and physical stopping behavior
   have been verified for the intended operating conditions.

Each stage requires its own defined implementation and verification scope.
