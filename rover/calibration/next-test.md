# Next live session: calibrate while exploring

Offline preparation is complete for bounded local collection. The user has a
relatively safe prepared area and wants calibration to continue during
exploration. Read WORKFLOW.md for the decision loop. The runtime selects no
route itself; the main agent interprets evidence and freezes each segment.
This is a runbook, not an already-authorized hardware session.

## After charging

1. Confirm the installed firmware. The October 9 candidate is built but has
   not been uploaded. If deploying it, scope upload/readback and stopped/bounded
   protocol/stop verification first. Keep the saved October 8 build available.
2. Establish Wi-Fi/Cam switch, close other controllers, then run one stopped
   battery/gyro/camera preflight. N1 must be valid and at least 7.0 V; bias and
   image-rest gates must pass. Fresh observations are required after charging.
   Recheck the camera's view/pan after any power cycle; saved camera.json and
   historical command 100 are not current position feedback.
3. Start exploration with **one forward PWM60/T200 action**, once its path and
   stopping allowance fit the prepared area. It records fresh stopped bias,
   raw sensors, continuous camera/IMU, N100 and settling evidence.
4. Disconnect and assess the saved run. If supported, select the next segment
   of 1-3 forward/left/right actions from the stopped views and response. A turn
   needs swept-body clearance. Capture translated overlapping views as useful
   reconstruction input; retain them without claiming metric pose.
5. Continue calibration during those segments: direction/sign, response spread,
   gyro drift, image overlap, raw floor/echo changes and settling. Use the
   focused turn comparison below only when that specific question warrants it.
   Do not make all eight turn trials a prerequisite for each local segment.

Proposed first-session cap: one preflight plus three exploration segments total,
first segment one action and the next two at most three each: **seven pulses,
PWM60/T200, at most 1,400 ms total commanded duration**. The runner enforces its
per-segment plan; the main agent tracks the overall session cap. No reverse,
power increase, automatic retry or unplanned movement. A fault/refusal ends the
session and retains partial evidence. These bounds remain a proposal until the
live session is authorized; charge completion alone does not execute it.

## Commands for that bounded session

Use the same 17-digit New York session-start timestamp and chat name. Replace
placeholders; commands here are references. Run from PowerShell 7 at project root.

```powershell
pwsh -NoProfile -File ./src/tools/run_calibration.ps1 -SessionTimestamp <session-start> -ChatName '<chat-name>' -SafeAreaAssumed -GyroCalibrationOnly
pwsh -NoProfile -File ./src/tools/run_exploration.ps1 -SessionTimestamp <session-start> -ChatName '<chat-name>' -SafeAreaAssumed -Actions 'forward'
```

After reviewing that segment, a chosen later segment can use the same entry with
`-Actions 'forward,left,forward'`, or another supported 1-3-action plan. This is
an example, not a preselected route through the room. Every action is sequential;
only IMU readings and HTTP-only camera observations overlap wheel motion.
Each segment still records its 12-batch baseline; do not launch collect_baseline
separately as a duplicate prerequisite. Old src/agent launcher paths still work.

After each disconnect, inspect printed Logs/Captures paths and run:

```powershell
.venv\Scripts\python.exe -B -m src.agent.analysis.validate_motion data/<session-start>/logs/<run> --output data/<session-start>/analysis/<analysis-start>-validation
```

Review trial completion, pre/post rest support, gyro gaps, command/stop timing,
battery and positive cleanup records; inspect before/after/timed frames before
choosing more motion. Retain unsupported trials. Mixed exploration segments may
not have enough matched turn trials for a fitted/held-out angle comparison; that
result is unknown rather than a reason to invent angle/position estimates.

Software readiness does not establish automatic obstacle avoidance, cliff
stopping, physical stopping distance, absolute heading or room coverage. The
prepared area is a user assumption. Floor values are logged, not classified as
edges. Echo shortening is a stopped change gate, with a fresh reference after
turns. If relevant clearance or evidence is unsupported, stop and assess.

## Optional focused turn comparison

Proposed experiment, not permission to run. The reorganized controller has
offline regression coverage; its changed scheduling/recording needs live verification.
This test evaluates repeatability of the existing scene-dependent method;
absolute heading, translation and stopping clearance remain separate milestones.

Firmware source now has a compiled October 9 candidate; the rover still has the
October 8 build. The candidate has not passed live protocol/stop checks. Record
which build is installed. If deploying the candidate, complete separately scoped
upload/readback and initial stopped/bounded protocol checks before this eight-turn
experiment. Host fault handling accepts existing successful reply formats.

### Scope to authorize

One stopped gyro/battery preflight, followed only if accepted by one focused
turn run: PWM60, T200, two repeats, left/right, expiry/half-duration N100,
timed camera and adaptive IMU. Eight pulses maximum, 1,600 ms total requested
firmware durations; half-duration-stop trials request N100 earlier.
No pan, forward/reverse, power increase or automatic retry session.
Include stopped observations, evidence writing, N100 cleanup/disconnect and
offline validation in the authorization. Specify safe-area assumptions and
clearance for the full swept body; the runner does not verify swept clearance.

Freeze these settings before connecting. The default full calibration run is
larger and includes pan/all directions; do not substitute it for this recipe.

### Prepare and preflight

Read handoff, procedure and the relevant runner source. Confirm rover Wi-Fi,
Cam switch, closed ELEGOO app and no other TCP controller. Use a fresh 17-digit
New York chat-start timestamp and the current chat name. Placeholders below
must be replaced; these are command templates, not runnable defaults.

For this first session after refactoring, inspect the source/flags and latest
offline test result before connecting. Runtime changes now refuse a scheduled
start more than 50 ms late, require at least two pre-motion camera frames with
the latest received within 500 ms, and recheck bias age at dispatch. Treat a
refusal as evidence to investigate; do not enlarge limits during acquisition.

Within the authorized session:

```powershell
pwsh -NoProfile -File ./src/tools/run_calibration.ps1 -SessionTimestamp <session-start> -ChatName '<chat-name>' -SafeAreaAssumed -GyroCalibrationOnly
```

This reads fresh battery, attempts stopped bias/image checks and attempts N100
cleanup/close. It sends no wheel or pan commands. A failed preflight ends this
test; retain its evidence. Do not bypass its gates.

### Acquire once

After accepted preflight and required clearance:

```powershell
pwsh -NoProfile -File ./src/tools/run_calibration.ps1 -SessionTimestamp <session-start> -ChatName '<chat-name>' -SafeAreaAssumed -DriveOnly -TurnOnly -TimedCamera -Repeats 2 -Speed 60 -DurationMs 200 -ImuPlan adaptive
```

DriveOnly skips pan, not the 12-batch stopped baseline. The runner refreshes
bias per trial, checks battery before/after pulses and requires pre-motion
camera support. Sampling favors gyro during turns. Up to three stopped bias
attempts are internal to a trial; they do not authorize another acquisition run.
Sensor/camera/communication faults end the run and attempt stop cleanup.

Record printed Logs/Captures paths, rejected attempts and cleanup outcome.
Never treat N100 acknowledgment as proof of physical rest.

### Assess after disconnect

Use the actual printed run directory and a fresh analysis-start timestamp:

```powershell
.venv\Scripts\python.exe -m src.agent.analysis.validate_motion data/<session-start>/logs/<run> --output data/<session-start>/analysis/<analysis-start>-validation
```

The validator excludes incomplete/rest-rejected trials, fits eligible repeat 0
and checks eligible later turns. The visual
conversion is fitted to nominal gyro angles: this is held-out consistency,
not independent absolute angular validation.

Heading now uses full-gyro sensor-Z integration. Historical 3D Euler yaw used
the shorter accel-overlap window. Record this method change; use the new report
as a baseline rather than claiming an improvement against the old median.

Completion evidence:

- Eight recorded trials, or an explicitly incomplete fault/refusal record.
- Usable timed frames and IMU brackets; pre/post rest support for every trial.
- Four held-out turn comparisons, reported per trial and as median/spread.
- Active gyro sample gaps and actual N4 send/host N100 timing inspected.
- Raw failures retained; battery and cleanup outcomes included.
- Positive socket-close/stop-attempt record; missing cleanup evidence is unknown.

No numeric angular pass threshold is established. The historical 0.588 nominal
degree median on four checks is a reference, not a target or acceptance bound.
Timing and disagreement must be reported even when rest gates pass. No metric
pose, power increase or exploration readiness follows from completing this test.

Decision: if evidence is incomplete, name the missing support and the specific
change needed before another run. If complete, record repeatability and remaining
scale/timing limitations, then choose an independent heading/translation
validation experiment. Update handoff and journal.
