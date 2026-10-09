# Rover experiment workflow

The accepted sequence is image-analysis assessment, initial drive/stop checks,
then bounded exploration with continuing calibration and reconstruction captures.
The user has prepared a relatively safe area and explicitly accepts learning
while exploring. Full metric calibration is not a prerequisite for every short
native-unit move there. Initial image assessment is complete; calibration remains
partial. General autonomous search, metric pose and reconstruction remain open.
Read [handoff](handoff.txt) and [next session](rover/calibration/next-test.md).

## One task, one question

Before editing or acquiring data, record:

- Question and the decision it will inform.
- Authorized actions: edits, offline execution/tests, hardware session,
  installation or firmware changes, as applicable.
- Fixed configuration, movement/session bounds and stop conditions.
- Evidence required, fit/validation split and completion criteria.
- Output paths and known limitations.

One explicit request can authorize the complete defined task, including its
checks and cleanup. Do not ask again within that scope. A proposal or a historical
authorization does not authorize a new session. Clarify material ambiguity.

## Prepare, acquire, assess

1. Read current context and inspect the relevant implementation. Resolve stale
   documentation before treating it as a command contract.
2. Prepare code and run only authorized offline checks. Freeze acquisition
   settings and acceptance criteria before opening control TCP.
   After runtime changes, verify the offline suite and command imports first;
   the next live session validates those changes within the existing bounds.
3. Establish fresh stopped observations within the authorized session. Battery,
   camera, bias and required clearance gates must pass before movement.
4. Execute the fixed experiment through one TCP owner. Log raw commands, replies,
   failures, images, timing brackets and configuration. Never infer rest from an
   acknowledgment or treat a zero ultrasound echo as free space.
5. Attempt N100 cleanup and close TCP on completion or fault. Report cleanup
   failures; physical rest requires observation. Analyze after disconnecting.
6. Preserve failed/rejected trials. Fit on the designated subset and evaluate
   held-out trials without refitting to them. Report missing support as unknown.
   Exclude incomplete/rest-rejected evidence from fits. Require positive cleanup
   records; silence in the log does not prove a successful close.
7. Decide: advance the named milestone, repeat with a specific justified change,
   or stop at the unresolved limitation. Update handoff and journal.

A fault ends acquisition. Repair within authorized scope while disconnected;
a new hardware run must be covered by the task's session/retry bounds. Do not
relax gates, add trials or increase power to obtain a favorable result.

## Distinct milestones

| Milestone | Evidence needed |
|---|---|
| Repeatable native-unit response | Repeated command/image/IMU response, rest support and held-out checks under stated conditions. |
| Absolute heading | Independent angular reference and supported sensor scale/timing; fitting pixels to nominal gyro angle is insufficient. |
| Translation | Independent scale or supported relative geometry, timing and quantified uncertainty; accel integration alone is insufficient. |
| Motion clearance | Body/path/swept-turn clearance with stopping allowance and uncertainty for intended conditions. |
| Bounded search | Defined area, coverage and session limits, enforced observation/action gates and fault handling. |
| Reconstruction | Suitable translated views, camera geometry, reconstruction quality criteria and agreed relative/metric output. |

Progress on one milestone does not complete the others. Calibration and bounded
exploration may share a segment: refresh stopped bias, execute one short action,
observe settling and retain camera/IMU/floor/echo evidence. Reassess between
segments before selecting more motion. Independent scale/clearance checks remain
requirements for larger or metric motion; local data collection need not wait
until every calibration milestone is complete.

## Responsibilities

The main agent prepares the experiment, interprets evidence and reports the stage
decision. Deterministic controller code owns TCP, enforces implemented command
bounds and attempts stop cleanup; proposed gates must not be described as live.

Use one main agent by default. With explicit delegation, subagents may review
controller behavior or analyze saved data independently. They never acquire
control TCP or send rover commands. Their findings go through the main agent.

Rover execution is sequential: one TCP owner serializes movement and pan.
N2/N3 requests from that owner may observe an active drive, one sensor request
pending at a time. HTTP camera recording can run alongside observation and
never sends control commands. N100 takes priority; blocking N7 waits until stopped.

## Closeout

Keep handoff short: current capabilities, latest evidence, material unknowns,
accepted limits and one next experiment. Put detailed run records and superseded
claims in journal. README owns current setup/command facts; procedure owns
detailed operating gates; results owns measured findings.

Use the project rover-experiment skill for preparing/assessing experiments.
Keep shared control in src/control, experiment policy in src/agent/runtime,
analysis/tests in src/agent/analysis and src/agent/tests, and launchers in
src/tools. Old PowerShell entry paths forward to those launchers.
Firmware proposals remain separate from host changes so
the command protocol and motor response are not changed incidentally.

## Implemented source organization

| Location | Responsibility |
|---|---|
| src/control/connection.py | One TCP owner: tagged send/poll/request, heartbeat, firmware faults and stop/close. No experiment folders or calibration policy. |
| src/control/motion.py | Pulse timing and one pending IMU request; stop takes priority and the last reply drains before stopped sensing resumes. |
| src/control/timed_camera.py | HTTP-only camera worker; optional raw device timestamp plus host brackets. |
| src/control/protocol.py and rover-protocol.psm1 | Python and PowerShell fault parsing. Existing keyboard controller stays here. |
| src/agent/runtime/ | Calibration/exploration sequencing, action limits, bias/rest policy and evidence records. |
| src/agent/analysis/ and tests/ | Saved-data interpretation and offline regressions. |
| src/tools/ | Manual rover tool and four experiment/baseline/survey launchers. src/agent/*.ps1 are compatibility forwarding entries only. |

RoverConnection is the transport base of CalibrationSession, so there is one
socket rather than a second controller inside an experiment. It refuses another
movement/pan while an action is reserved, a second pending sensor read, or
transport use from another thread. This is not a cross-process lock: the ELEGOO
app/manual controller must still be closed. N100 releases command ownership
after transmission; observations establish physical settling.

The exploration entry accepts a frozen plan of 1-3 forward/left/right actions,
each PWM60/T200, with no reverse or automatic power escalation. Default remains
three forward pulses. Main-agent interpretation selects the next bounded segment
after disconnecting and reviewing evidence; the runner does not choose a route
or detect all hazards. A turn resets the echo reference because its new heading
observes a different direction. Stopped sensor validation still applies.

Source provenance includes control, agent runtime/analysis and tools. Existing
Python module entries and evidence field names are retained; optional camera
timestamp and action-plan fields are additive. Data, vendor files, backups and
the firmware candidate are preserved. See journal for completed offline checks.
