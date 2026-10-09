---
name: rover-coordinator
description: Coordinate a bounded hyohakusha exploration round with offline mapping and image workers, opportunistic capture requests, and saved-evidence review. Use for next-round preparation or an explicitly authorized live round.
---

This skill is installed in the repository skill catalog. Discovery in an already-open
chat may require refreshing its available skills; the file can also be read directly. Read [WORKFLOW.md](../../../WORKFLOW.md) for the
decision diagrams and worker contracts, [handoff](../../../handoff.txt) for current
evidence, and [next-test](../../../rover/calibration/next-test.md) for the proposed live brief.
Use the existing [experiment skill](../rover-experiment/SKILL.md)
for detailed experiment preparation/assessment. Instructions do not authorize
hardware, tests, dependencies or edits.

Keep the main agent focused on useful new views. Once a live round is authorized,
freeze its objective, area assumptions, attempted-pulse/segment caps, deadline,
retry allowance and fixed native command bounds. Track overall limits explicitly;
the existing runner enforces only its 1–3-action PWM60/T200 segment.

Use fresh stopped evidence at round start and review each segment after disconnect.
Do not duplicate its built-in baseline/bias checks. Use session_brief for inventory
and review_segment (which runs validate_motion) for saved rest/completeness/cleanup;
read report fields rather
than interpreting an exit code as permission to move. Inspect latest camera views
and required clearance before freezing the next action plan.

When delegation is authorized, reuse offline map, image/reconstruction and evidence
workers. Give completed run cutoffs, narrow questions and separate output paths.
No worker owns TCP or sends commands. Heavy analysis never blocks another supported
segment. Requests enter a coordinator backlog and are collected opportunistically;
only significant supported findings change immediate movement decisions.

Keep maps as observable landmark/view graphs unless metric localization is actually
supported. Camera points upward; unseen floor and swept-body clearance remain unknown.
Approximate ultrasound distance is evidence about a reflecting target, not verified
free space. Missing intrinsics do not block collecting useful overlapping views in
the established prepared area.

On faults, stop/close, preserve evidence and diagnose within scope. For an authorized
echo-only recovery, inspect cleanup and attempted movement, then use at most three
logged retries with fresh stopped evidence and a specific recovery reason. Never
replay already attempted actions, turn merely to bypass a fault, relax gates or
increase power. Ask for help when a material fault or required clearance remains
unresolved after available bounded recovery.

At closeout, report attempted/completed pulses, useful observations, faults/unknowns,
cleanup and evidence paths. Update current handoff and detailed journal. Do not mark
metric navigation, physical stopping calibration or reconstruction complete from
native response or projective diagnostics.

Use native project profiles when delegation is authorized:
[rover_map](../../../.codex/agents/rover_map.toml),
[rover_images](../../../.codex/agents/rover_images.toml),
[rover_evidence](../../../.codex/agents/rover_evidence.toml).
These are standalone Codex agent definitions, not ad hoc role prompt documents.
Profile creation does not prove this running client has loaded them. If native role
selection is unavailable in the current tool surface, report that limitation rather
than silently presenting generic spawned workers as profile-backed workers.

Read current durable state in rover/state/task-state.json when present. Use the
workflow_state offline tool to record mission scope, attempted-send accounting,
processed runs, worker assignments and opportunistic requests. State/history are
project evidence, not fresh hardware observations or permission. Budget feasibility
is advisory until the coordinator freezes and executes an authorized segment.

No lifecycle hook is installed: the user requested its removal. Restore context by
reading AGENTS.md, current handoff and durable state. Generated Codex memories are
supplementary; never use them as current sensor state, mission budget or permission.
