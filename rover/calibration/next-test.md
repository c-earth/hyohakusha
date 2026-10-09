# Next round: exploration first, analysis in parallel

This is a proposed runbook, not live authorization. The next round collects useful
new views while calibration continues. Reconstruction and camera intrinsics are
background questions, not prerequisites for every supported local pulse. See
[WORKFLOW.md](../../WORKFLOW.md) for decision diagrams, hierarchy and worker contracts.

## Freeze the round brief before connection

Read AGENTS.md, the coordinator skill and current task checkpoint first.
Record the objective and explicit live scope, prepared-area/body/path/swept-turn
clearance assumptions, maximum attempted pulses and segments, deadline, and retry
allowance. Current exploration is 1-3 forward/left/right PWM60/T200 actions per
segment, no reverse or escalation. The coordinator manages the overall cap; the
runner enforces segment limits only. Choose actual round limits before executing;
this document supplies no automatic total allowance.

October 9's 43 trials support native response and later rest, including early N100.
Independent expiry and physical stopping clearance remain unverified. Latest saved
battery/pose are historical; obtain fresh evidence after reconnect/setup changes.
The prior seven-pulse/no-retry proposal is superseded, not a current permission.

## Start and continue

1. Re-establish rover Wi-Fi/CAM, close other controllers, verify prepared-area
   assumptions and camera view. One main TCP owner; workers remain offline.
2. Within the authorized round, run one stopped preflight. Valid N1 >=7.0 V,
   camera and bias/rest support are required. Do not infer current servo feedback
   from old camera.json or command history.
3. Freeze one first action when current response/view is uncertain; select it from
   fresh evidence. Then use 1-3 actions per supported segment within remaining caps.
4. After disconnect, validate saved rest/completeness/cleanup and inspect sensors
   and latest images. Dispatch completed paths to background workers and immediately
   select the next supported segment. Each runner already has its baseline and
   per-trial bias; do not duplicate preflight/baseline before each successful segment.
5. Reserve the frozen plan in selected round state before the separate live launcher;
   import the resulting run with its reservation ID after review. Ledger checks do
   not grant permission or automatically bind the hardware launcher.
6. Collect worker requests when the route fits; keep the rest as backlog. Stop on
   material faults, unsupported clearance or overall completion/caps/deadline.

Templates; replace placeholders and explicitly choose Actions:

```powershell
pwsh -NoProfile -File ./src/tools/run_calibration.ps1 -SessionTimestamp <session> -ChatName '<name>' -SafeAreaAssumed -GyroCalibrationOnly
pwsh -NoProfile -File ./src/tools/run_exploration.ps1 -SessionTimestamp <session> -ChatName '<name>' -SafeAreaAssumed -Actions '<chosen-actions>'
.venv\Scripts\python.exe -B -m src.agent.analysis.validate_motion data/<session>/logs/<run> --output data/<session>/analysis/<new-output>-validation
pwsh -NoProfile -File ./src/tools/review_segment.ps1 -Session data/<session> -Run <run> -Output data/<session>/analysis/<new-output>-review
pwsh -NoProfile -File ./src/tools/session_brief.ps1 -Session data/<session> -LastRun <run> -Output data/<session>/analysis/<new-output>-brief
```

Use review_segment instead of a separate validation invocation on the immediate
decision path: it runs validation and inventory together. Validation exit 0 means
a report was saved; inspect acquisition_complete,
cleanup_recorded, event_errors and per-trial pre/post rest support. The summary
is an inventory, not a clearance/rest classifier. Preserve failed/partial trials.

## Recovery and completion

Current host echo trigger is >90% shortening at comparable unchanged heading;
exactly 90% is allowed and turns reset the reference. Zero/invalid echo faults.
Approximate range uses echo_us*0.0001715 m, not a verified body/path clearance.
A very short absolute echo or observed approach merits reassessment even when the
percentage gate passes. Floor ADC has no validated cliff detector.

If the round includes echo retries, allow up to three separately logged echo-only
recoveries with fresh stopped evidence, clean cleanup and a specific recovery reason.
Never replay an entire partially moved segment. Other battery/IMU/camera/connection
faults end acquisition and require diagnosis. Do not loosen gates/increase power.

Complete when the defined coverage/data objective, cap or deadline is reached;
report actual attempted/completed pulses, observations, unknowns and cleanup.
Supported local collection does not establish metric pose, independent expiry,
physical stopping distance, autonomous coverage or a Euclidean room model.

The focused reference below is optional; it is not a prerequisite to exploration.
## Optional focused turn comparison

Proposed experiment, not permission to run. The reorganized controller has
offline regression coverage; its changed scheduling/recording needs live verification.
This test evaluates repeatability of the existing scene-dependent method;
absolute heading, translation and stopping clearance remain separate milestones.

The October 9 build is installed and flash-verified; it has not passed live
protocol/stop checks. Record which build is installed. Complete separately scoped
initial stopped/bounded protocol checks before this eight-turn
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

Before this optional comparison, inspect the source/flags and latest
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
