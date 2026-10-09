# Project Description

This workspace is an ELEGOO Smart Robot Car V4.0 project. Its goal is to connect an AI agent to the rover for manual control, then bounded exploration and 3D reconstruction of the interior visible to the camera.

Read the introduction and [Hardware](README.md#hardware) section of README for capabilities, hardware, and verification status.

Read `README.md` for project usage and structure, and relevant `info.txt` files and source for task-specific details. Keep README for user-facing setup and facts; keep this file for agent working instructions.

# Response Behavior

- Give concise, direct answers without unnecessary background, repetition, or restating the request.
- For yes/no questions, begin with `Yes`, `No`, or `Unknown`, as supported by the available evidence, followed only by necessary explanation.

# Evidence and Reporting

- Distinguish verified findings, assumptions, and proposals.
- Verify factual claims that determine whether a recommendation is applicable.
- Distinguish documented capabilities from capabilities verified in the user's environment. Do not present an unverified capability as an available solution.
- When evidence is insufficient, state what is unknown and avoid filling the gap with assumptions.
- Describe only checks actually performed and conclusions those checks support. When reporting implementation results, state how they were verified. State relevant limitations.
- When correcting an unsupported claim, withdraw it explicitly rather than replacing it with another inference.
- Briefly summarize file changes in the final response and link to relevant files.

# Explicit Action Authorization

- Before any state-changing action or execution of code or executables, identify an explicit user request authorizing that action and its scope. This requirement covers file creation, modification, deletion, movement, and copying; implementation; configuration changes; dependency installation; tests; and simulations.
- Explicit authorization must communicate an intent to have a defined action performed within a defined scope.
- Requests for explanation, analysis, review, or proposals authorize that informational work only. Do not infer authorization for state changes or execution from discussion, criticism, preferences, behavioral guidance, or expressions of frustration.
- Keep authorization limited to the requested action and scope. Permission for one category of action does not automatically extend to another. Editing, execution, testing, installation, and simulation require their own explicit authorization, which may be given together in one request.
- Do not treat your own plan, announcement, or recommendation as user approval.
- Authorization remains valid while completing the requested work within its established scope; do not repeatedly ask for it during that work. Once the requested work is complete, further actions require new explicit authorization unless the user explicitly granted continuing authorization. Separate system permission requirements still apply.

# Clarification

- Follow editing instructions exactly. Before editing, verify that the requested target and stated condition match the actual file. If they do not match, explain the mismatch and ask for clarification; wait for an explicit answer before editing. Do not reinterpret the request as a different change, even if that change seems useful or consistent with an inferred intent.
- When ambiguity affects intent, scope, correctness, instrument behavior, or an irreversible decision, ask and wait for an explicit answer before acting.
- Once implementation is explicitly authorized, use reasonable judgment for minor, reversible choices within that scope and disclose material implementation choices.

# Project Context

- Read relevant instruction or guidance files before working.
- Treat project-specific instructions as the primary source for understanding the project's structure, conventions, terminology, and workflows.
- Focused read-only inspection of relevant project files is allowed when needed to answer accurately, verify implementation claims, or complete an explicitly authorized task. Commands limited to that inspection are exempt from separate execution authorization. This exception excludes project code, tests, simulations, and all Python execution; those require explicit authorization.
- Do not assume conventions from other projects apply to this project.
- Reading or inspecting files or directories outside the project workspace, or in another project, requires explicit user authorization. Avoid unrelated project folders. When cross-project context is necessary, explain why and identify the specific files or directories needed before requesting access.

# Coding Standards

- Use classes with clear responsibilities and encapsulation for stateful components such as sessions, controllers and recorders. Small pure numerical or formatting functions may remain functions; do not add wrapper classes solely to satisfy a style rule.
- Place all imports at the beginning of the file, after any module docstring and before other code, unless doing so conflicts with a required behavior or another applicable instruction.
- Separate Python imports into three blocks, in this order, with a blank line between blocks: Python standard library packages, installed third-party packages, and project-specific functions/classes or modules.
- Place docstrings only at the top of a file as a module docstring, or as the first statement in a function, method, or class body immediately after its definition signature.
- Docstrings must explain purpose and behavior, meaningful inputs/outputs, units, assumptions and constraints. Document relevant attributes on stateful classes. Avoid boilerplate about absent inputs or outputs and repeating information already clear from the signature.

# Python Environment

- Use `.venv\Scripts\python.exe` for authorized project Python execution and `.venv\Scripts\python.exe -m pip` for authorized dependency operations.
- Retrieve interpreter details from `.venv/pyvenv.cfg` when relevant.
- Keep `tools/esptool` separate from the project environment; do not inject its Python 3.12-specific native packages into `.venv`.

# Project Retrieval

- Read [handoff.txt](handoff.txt) for the current project state, completed work, accepted decisions, and the staged roadmap through AI control, exploration, and final 3D reconstruction. Its proposed steps are not authorization to execute them.
- Keep `handoff.txt` concise and current. Read [journal.md](journal.md) when historical evidence or completed-task details are needed; archived findings and authorizations may be superseded and do not authorize new work. The accepted sequence is image-analysis assessment, initial drive/stop checks, then bounded exploration with continuing calibration and reconstruction captures. The user permits calibration while exploring the prepared relatively safe area; do not require completed metric calibration before every short native-unit move there. Functional movement checks do not complete calibration.
- Read [WORKFLOW.md](WORKFLOW.md) for the proposed decision process, agent hierarchy, runtime loop, and development sequence. Treat proposed components as unimplemented until verified.
- For exploration coordination, read [.agents/skills/rover-coordinator/SKILL.md](.agents/skills/rover-coordinator/SKILL.md) and current [task state](rover/state/task-state.json), then the selected round-state file. Native specialist definitions live in `.codex/agents/`; file validation is not proof of client discovery or actual profile-backed spawning.
- Read [Project structure](README.md#project-structure) for file locations and [Development tools and references](README.md#development-tools-and-references) for tool configuration.
- Read [Firmware and backups](README.md#firmware-and-backups) before work involving firmware artifacts.
- Read [Connection setup](README.md#connection-setup), [Command-line tools](README.md#command-line-tools), and [Keyboard driving](README.md#keyboard-driving) before rover operations.
- Read [Calibration and capture data](README.md#calibration-and-capture-data) when interpreting observations or working with captures.

# Agent Operations

- As authorized tasks are completed, update `handoff.txt` with the actual changes, checks performed, results, remaining work, and next applicable stage. The user grants continuing authorization for these progress updates within completed task scope; this does not authorize additional implementation or execution. Mark roadmap stages complete only when their completion criteria are met, and distinguish partial progress from completion. Keep accepted decisions and relevant limitations accurate rather than carrying forward stale claims.
- Put detailed completed-task records in `journal.md`; keep crucial current results, accepted decisions, unresolved limitations and next steps in `handoff.txt`. Preserve historical evidence when relocating it, and clearly distinguish it from current state.
- Keep changes within the authorized scope; do not add unrelated cleanup or refactoring.
- Keep one owner of the rover TCP control connection. Do not operate concurrent controllers.
- Rover actions are sequential: serialize movement and pan through that owner. IMU requests may observe an active drive, with one pending sensor request; HTTP camera recording never sends control commands. N100 takes priority over further actions.
- Distinguish command acknowledgments from observed physical results.
- Use one main agent by default. Spawn subagents only when the user explicitly requests delegation or parallel agent work.
- During an authorized exploration round, the main agent prioritizes new useful views and data collection. Keep heavy mapping/reconstruction analysis offline and concurrent when delegation is authorized; it does not block another supported segment. Full metric calibration is not a prerequisite for short native-unit collection in the established prepared area.
- Give workers completed-run cutoffs, narrow questions and unique derived output paths. Workers never connect to the rover or change acquisition gates. Reuse workers rather than respawning for every segment. Worker capture requests enter a coordinator-owned backlog and are collected when the route fits; significant supported findings may change the immediate decision.
- The coordinator tracks overall attempted-pulse/segment caps, deadline and retry allowance; the runner enforces only its per-segment bounds. Count attempted sends conservatively and never replay an entire failed segment that may already have moved.
- Use `src/tools/workflow_state.ps1` to persist frozen reservations, run associations, workers and requested-view backlog. Reserve the full plan before dispatch and import its resulting run with the reservation ID. Unlinked imported motion consumes additional budget; unknown accounting blocks further reservations. The live launcher does not read this ledger, so main must match the reserved plan and authorization explicitly. State never grants live permission.
- After disconnecting, use src/tools/review_segment.ps1 for saved completion/rest/cleanup/battery evidence and src/tools/session_brief.ps1 for a session inventory. Reporting success is not evidence support or movement permission. Inspect decision predicates, sensor trends, latest images and required clearance before choosing another segment.
- At round start obtain fresh stopped evidence. Existing segments already collect a baseline and per-trial bias; avoid duplicate standalone baseline/preflight acquisition before each successful segment. Retain all implemented gates and stop between pulses.
- For echo-only recovery included in the round scope, allow up to three logged retries after inspecting attempted motion and positive cleanup, with fresh stopped evidence and a specific recovery reason. Other battery/IMU/camera/connection faults end acquisition and require diagnosis. Do not bypass a fault by turning or relaxing gates. Ask for physical help when significant faults or required clearance remain unresolved.
- Restore context after resume/compaction by reading maintained project instructions, handoff and selected state. Codex-generated memories are supplemental; they never establish current pose, sensor values, cleanup, budget or authorization. Do not hand-edit Codex internal chat/memory stores or change user memory settings incidentally. No lifecycle hook is installed; the user requested its removal.
- When designing Codex workflows, verify native agent, skill, hook and configuration formats against current official OpenAI documentation. Use product-native mechanisms where applicable. Distinguish written definitions, offline validation, discovery and observed runtime behavior; never present generic prompt-driven workers as verified native-profile agents.

# Experiment Discipline

- Use [.agents/skills/rover-experiment/SKILL.md](.agents/skills/rover-experiment/SKILL.md) for experiment preparation and assessment. It routes to maintained procedures and does not authorize operations.
- Keep shared TCP/protocol/motion/camera code in src/control, experiment policy and sequencing in src/agent/runtime, analysis in src/agent/analysis and tests in src/agent/tests. Canonical PowerShell launchers live in src/tools; retain old src/agent launcher paths as forwarding entries. Invoke Python entry modules with `.venv\Scripts\python.exe -m src.agent.<package>.<module>` from the project root.
- Preserve data, backups and vendor files during source cleanup. Historical records may contain old source paths; update current instructions without rewriting historical evidence.
- Firmware source edits, builds and uploads are separate scopes. Consult legacy code for evidence without restoring onboard autonomous modes or changing direct PWM behavior incidentally.
- Before acquisition, define one question, the decision it informs, fixed settings, authorized action categories, session/retry bounds, evidence requirements and completion criteria. One explicit request may cover editing, offline checks and a bounded live session together; do not repeatedly ask within that defined scope.
- Read rover/calibration/next-test.md before preparing the next live test. It is a proposal and command reference, not authorization.
- Freeze acquisition settings before connecting. End acquisition on a fault; retain rejected/failed trials. Identify a specific justified change before retrying. Do not loosen gates or increase power to obtain favorable results.
- Analyze after disconnecting. Keep fitting and held-out evidence separate. Visual conversion fitted to nominal gyro angles demonstrates consistency, not independent absolute heading accuracy.
- Treat repeatable native-unit response, absolute heading, translation, stopping clearance, bounded search and reconstruction as separate milestones.
- For calibration during exploration, freeze each segment's 1-3 actions and the overall session/segment bound. Collect bias, camera/IMU, stopped floor/echo/battery and settling evidence around each pulse. Analyze and choose the next segment while stopped/disconnected. The prepared area's relative safety is a user assumption, not an implemented cliff/obstacle detector; preserve uncertainty and stop on faults or unsupported clearance.
- Keep handoff to current evidence, limits and one next experiment. Archive superseded detail in journal; never retain stale claims as current state.
- README owns current setup/command facts; procedure owns detailed gates; results owns measured findings. Resolve discrepancies against source and recorded evidence, and label anything still unknown.
