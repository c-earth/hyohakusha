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

- All code written must follow proper object-oriented design, with clear class responsibilities and encapsulation.
- Place all imports at the beginning of the file, after any module docstring and before other code, unless doing so conflicts with a required behavior or another applicable instruction.
- Separate Python imports into three blocks, in this order, with a blank line between blocks: Python standard library packages, installed third-party packages, and project-specific functions/classes or modules.
- Place docstrings only at the top of a file as a module docstring, or as the first statement in a function, method, or class body immediately after its definition signature.
- Every docstring must clearly describe the purpose and behavior of the documented code, relevant variables or attributes, inputs or parameters, and outputs or return values. Include types, meanings, units, defaults, and constraints where applicable, and explicitly state when there are no inputs or outputs.

# Python Environment

- Use `.venv\Scripts\python.exe` for authorized project Python execution and `.venv\Scripts\python.exe -m pip` for authorized dependency operations.
- Retrieve interpreter details from `.venv/pyvenv.cfg` when relevant.
- Keep `tools/esptool` separate from the project environment; do not inject its Python 3.12-specific native packages into `.venv`.

# Project Retrieval

- Read [handoff.txt](handoff.txt) for the current project state, completed work, accepted decisions, and the staged roadmap through AI control, exploration, and final 3D reconstruction. Its proposed steps are not authorization to execute them.
- Keep `handoff.txt` concise and current. Read [journal.md](journal.md) when historical evidence or completed-task details are needed; archived findings and authorizations may be superseded and do not authorize new work. The current accepted sequence is image-analysis tool assessment, drive calibration, then bounded search while collecting reconstruction data; functional movement checks are not drive calibration.
- Read [WORKFLOW.md](WORKFLOW.md) for the proposed decision process, agent hierarchy, runtime loop, and development sequence. Treat proposed components as unimplemented until verified.
- Read [Project structure](README.md#project-structure) for file locations and [Development tools and references](README.md#development-tools-and-references) for tool configuration.
- Read [Firmware and backups](README.md#firmware-and-backups) before work involving firmware artifacts.
- Read [Connection setup](README.md#connection-setup), [Command-line tools](README.md#command-line-tools), and [Keyboard driving](README.md#keyboard-driving) before rover operations.
- Read [Calibration and capture data](README.md#calibration-and-capture-data) when interpreting observations or working with captures.

# Agent Operations

- As authorized tasks are completed, update `handoff.txt` with the actual changes, checks performed, results, remaining work, and next applicable stage. The user grants continuing authorization for these progress updates within completed task scope; this does not authorize additional implementation or execution. Mark roadmap stages complete only when their completion criteria are met, and distinguish partial progress from completion. Keep accepted decisions and relevant limitations accurate rather than carrying forward stale claims.
- Put detailed completed-task records in `journal.md`; keep crucial current results, accepted decisions, unresolved limitations and next steps in `handoff.txt`. Preserve historical evidence when relocating it, and clearly distinguish it from current state.
- Keep changes within the authorized scope; do not add unrelated cleanup or refactoring.
- Keep one owner of the rover TCP control connection. Do not operate concurrent controllers.
- Distinguish command acknowledgments from observed physical results.
- Use one main agent by default. Spawn subagents only when the user explicitly requests delegation or parallel agent work.
