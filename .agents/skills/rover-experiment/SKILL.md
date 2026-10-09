---
name: rover-experiment
description: Prepare and assess bounded ELEGOO rover experiments in the hyohakusha project, using its single controller and recorded camera/IMU evidence.
---

Use the repository root containing AGENTS.md and handoff.txt. Read the current
[handoff](../../../handoff.txt) and [next experiment](../../../rover/calibration/next-test.md).
Use [procedure](../../../rover/calibration/procedure.md) for detailed gates;
do not load the historical journal unless a specific evidence question needs it.

Resolve the authorized experiment scope before invoking hardware. A skill,
saved command or old authorization does not authorize movement. Keep one TCP
owner; HTTP camera recording is separate and never sends control commands.

Choose the existing entry point. Canonical PowerShell launchers are in src/tools;
the old src/agent paths forward parameters for compatibility. Shared transport,
motion and HTTP-only recording live in src/control; experiment policy stays in
src/agent/runtime.
Python modules run from the project root with .venv\Scripts\python.exe -m:

- src.agent.runtime.calibration_session for bounded calibration.
- src.agent.runtime.bounded_exploration for frozen local 1-3-action segments.
- src.agent.analysis.validate_motion for saved motion evidence.
- src.agent.analysis.integrate_imu for conditional inertial diagnostics.

Before acquisition, freeze the question, configuration, trial/retry bounds and
completion criteria. Do not replace a focused experiment with the larger default
calibration sequence. Record all mode flags and source identity. Retain raw
evidence on failed trials and inspect cleanup outcome before considering a retry.

The user permits calibration while exploring the prepared relatively safe area.
After fresh stopped/drive/stop checks, use short segments to collect calibration
and reconstruction evidence together. Do not require complete metric calibration
before every local move under the accepted assumption. Exploration defaults to
three forward pulses; -Actions 'forward,left,forward' freezes an optional mixed
segment (1-3 actions, PWM60/T200, no reverse). Keep an overall session cap in
addition to the runner's segment cap. The main agent selects the next segment
after stopped/disconnected review; the runner has no automatic route selection
or validated cliff/obstacle detector. Turns require swept-body clearance and
start a new raw-echo reference. Never send pan/blocking N7 during a drive.

After disconnecting, use the printed run paths. Failed/rest-rejected trials
remain in reports but cannot fit the visual/gyro conversion. Host timestamps
bound network transactions; they are not device execution or exposure times.
Optional camera_timestamp headers are unverified device metadata, not host time.
Full-gyro Z integration and historical accel-overlap Euler yaw are different
diagnostics. Neither establishes an independent angular scale or metric pose.

Close out with the specific stage decision, remaining unknowns and evidence
paths. Put current conclusions in handoff and detailed records in journal.
When delegation is explicitly authorized, give independent reviewers offline
code/data questions; keep hardware control with the main agent.
