# Exploration calibration procedure

Scope: N1–N8 and N100, stationary observations first, then individually gated
short wheel pulses. This procedure does not authorize exploration or firmware
changes. Record native sensor units; no metric scale is established.

## Session and prerequisites

Use one TCP controller, rover Wi-Fi, Cam switch and closed ELEGOO app. Record
firmware/source hashes, surface, battery estimate, session name and timestamp.
Save commands/replies with UTC times under `data/<session>/logs/`; JPEGs and
request/receipt times under `captures/`; assessments under `analysis/`.
Acknowledgments establish protocol response, not physical motion or rest.

Before wheels move, establish clearance for the entire body, intended path and
stopping uncertainty. Forward ultrasound alone does not establish that clearance.
Reverse requires a verified corridor and pose; turns require swept-body clearance.
If this cannot be established, stop at stationary calibration and record the gate.
Flat floor/no drops is a user assumption, not verified cliff protection.

User-defined battery stop: N1 voltage below 7.0 V sends N100 and ends the session.
Invalid/missing voltage also ends the session. The runner checks N1 before/after
each bounded pulse; it does not poll battery inside the 100/200 ms pulse.
Voltage conversion remains uncalibrated. Exactly 7.0 V is not below the threshold.
`-BatteryOnly` performs a stopped N1 check and cleanup without pan/wheel commands.

Gyro bias is now refreshed while stopped before every movement trial. N100 and
0.7 s wait precede five paired gyro/accelerometer reads bracketed by two images.
The estimate requires >=20 valid image tracks, median motion <=1 px, 95th
percentile <=3 px, gyro standard deviation <=50 raw counts per axis and accel
standard deviation <=300 raw counts per axis. These provisional gates support
stationarity; they do not prove physical rest. Unknown/unstable evidence or a
bias older than 10 s refuses movement. Bias is logged per trial and applied on
the host; firmware calibration is unchanged. `-GyroCalibrationOnly` exercises
this path with no wheel/pan commands.

Bias checks now use a robust partial-affine image-motion model: >=70% coherent
tracks spanning >=25% of image width/height. Raw motion statistics stay logged;
the 1 px median/3 px p95 limits apply to coherent tracks. Up to three stationary
checks may be attempted without loosening thresholds or sending wheel commands.

`-TimedCamera` records camera frames through a separate HTTP-only worker while
the sole TCP owner records IMU. Sampling starts 1 s before N4 and continues 1.6 s
after N100; at least two pre-motion frames are required. Camera faults stop/refuse
motion; the worker never owns control TCP. Camera and sensor request/receipt
brackets share host monotonic time, not exposure/acquisition timestamps.

Default `-ImuPlan adaptive` prioritizes gyro through a turn and 300 ms after host
stop, alternating gyro/accel during rest. Forward/backward retain alternating
reads. Explicit `alternate`/`gyro-focus` remain available for comparison.
`-TurnOnly -Repeats 2` limits a focused comparison to eight turn trials.
`src/agent/validate_motion.py` compares first-repeat fits against later turns and
checks pre/post rest evidence. Conditional zero-velocity endpoint corrections
are diagnostics and are never used as validated distance or control odometry.

The local exploration entry `src/agent/run_exploration.ps1` performs exactly
three PWM60/T200 forward pulses in the user-assumed safe area, recording camera,
IMU and stopped sensors. It refuses additional pulses, turns, duration/power
changes and >20% shortening of successive raw echoes. This echo-change trigger
is provisional supporting evidence, not calibrated collision avoidance. No
metric position or verified-free-space map is emitted; battery/gyro-bias gates
remain active. Room search and coverage are not implemented.

Numerical time integration of saved samples:

```powershell
.venv\Scripts\python.exe src/agent/integrate_imu.py data/<session>/logs/<run> --output data/<session>/analysis/<new-output>
```

The integrator removes gyro bias and composes orientation increments. It rotates
accelerometer readings into the initial sensor frame, subtracts the stationary
reference, then integrates once for velocity increment and twice for displacement.
It compares request/midpoint/receipt timing and local/run-baseline offsets. Nominal
gyro/accel conversions follow source-configured ranges; installed scales and
acquisition timestamps remain unverified. Only overlapping observed support is
used. Initial velocity at that window is unknown, so zero-initial-velocity
displacement is a diagnostic assumption, not measured travel.

For the current calibration the user explicitly permits assuming a safe area,
covering short forward/backward and left/right trials. Record this as an
assumption; it does not validate autonomous exploration clearance.

Implemented entry point (one Python TCP owner through PowerShell):

```powershell
pwsh -NoProfile -File ./src/agent/run_calibration.ps1 -SessionTimestamp 20261009003013000 -ChatName 'Exploration calibration' -SafeAreaAssumed
pwsh -NoProfile -File ./src/agent/run_calibration.ps1 -SessionTimestamp 20261009003013000 -ChatName 'Exploration calibration' -SafeAreaAssumed -DurationMs 200 -DriveOnly
.venv\Scripts\python.exe src/agent/assess_calibration.py data/<session>/logs/<run>
```

The runner permits PWM 60/80 and only 100/200 ms positive expiry. Each
duration has three repetitions per direction and stop mode (24 trials). Full
runs also repeat N5/N6 pan sequences three times. No automatic power escalation
or exploration is implemented. Use -Speed 80 for the explicitly selected higher
power comparison after inspecting PWM 60 results. Sensors, command/reply UTC and monotonic times,
JPEGs and trial metadata are saved. Sensor request/reply time brackets are not
acquisition timestamps. Current gyro/accel sampling alternates asynchronous
N2/N3 reads, with one pending request and independent host stop deadline.
N2/N3 change the global firmware reply tag, so expiry acknowledgments may be
retagged; do not interpret them as independently correlated N4 acknowledgments.
Serial/network latency and sampling effects remain part of these trial conditions.

## Command coverage

Each JSON example needs a unique short H tag except N100. Send heartbeat messages
`{Heartbeat}` while connected. Validate replies and stop on timeout/malformed data.

| Command | Request example | Calibration and acceptance evidence |
|---|---|---|
| N100 stop | `{"N":100}` | Start/end every stage. Record send/reply and image/IMU settling separately; no reply proves physical rest. |
| N1 battery | `{"N":1,"H":"b1"}` | At least 12 stationary readings and before/after pulses; report range in estimated V. Conversion accuracy needs independent voltage reference. |
| N2 gyro | `{"N":2,"H":"g1"}` | At least 12 stationary XYZ samples; bias, spread and drift in raw counts. Later record turn sign/response and settling. No calibrated angle claim. |
| N3 acceleration | `{"N":3,"H":"a1"}` | Stationary XYZ mean/spread and gravity vector; compare pre/post movement for tilt/change. Mounting and scale remain unknown without independent evidence. |
| N7 ultrasound | `{"N":7,"D1":2,"T":30000,"H":"u1"}` | Repeated echo duration in us, timeout rate and spread. Zero means unknown. Validate 0–30000. Known reference distances are required for metric validation. |
| N8 floor | `{"N":8,"D1":0,"H":"f1"}` | Repeat D1=0/1/2 for left/middle/right raw ADC baselines and spread. No cliff-protection claim. |
| N5 absolute pan | `{"N":5,"D1":1,"D2":100,"H":"p1"}` | Stop first. Command 100 reference; 95/100/105/100 repeated three times with >=650 ms settling and JPEGs. Measure pixel direction and return residual. Command degrees are not measured physical degrees. |
| N6 incremental pan | `{"N":6,"D1":1,"H":"i1"}` | From N5=100, +1/-1 and +5/-5 repeated three times, JPEG after each settled step; restore N5=100. Measure repeatability and image response; clamping/state are not position feedback. |
| N4 timed drive | `{"N":4,"D1":3,"D2":60,"T":100,"H":"m1"}` | D1: left=1/right=2/forward=3/backward=4. Positive finite duration only; PWM is not velocity. Gate every trial independently. |

N5 acknowledgment can precede servo execution. N4 acknowledgment occurs on timed
expiry in current source. Keep N5/N6 and blocking N7 reads out of active drive:
mode changes and synchronous waits can interfere with expiry. Do not run a
separate Sensors controller alongside a Move controller.

## Ordered stages

1. Stationary baseline: 12 sensor batches plus camera captures. Existing entry:
   `pwsh -NoProfile -File ./src/agent/collect_baseline.ps1 -SessionTimestamp <17-digit timestamp> -ChatName <name> -Samples 12`.
   Decode JPEGs, assess temporal image stability and sensor noise; report faults.
2. Stationary pan: N100, N5/N6 sequences above, repeat captures, restore 100,
   N100. Determine observable forward direction/return repeatability. Ultrasound
   pointing relative to camera pan is unverified; do not interpret these readings
   as an ultrasound sweep without establishing the mounting relationship.
3. Clearance gate: inspect fresh forward and side views and account for hidden
   near-floor/body space. Unknown clearance blocks wheel trials. Do not invent a
   numeric safe threshold from raw echo values or apparent image openness.
4. Drive response: initially PWM 60, T=100 ms, one direction at a time, explicit
   N100 after the finite pulse. Collect before/after sensor batches and images.
   Repeat three times only while the gate remains satisfied. Increase to 200 ms
   only after repeatable motion/rest and sufficient clearance. Test all four
   directions; reverse/turn remain blocked until their distinct gates pass.
5. Stopping: compare expiry with N100 sent halfway through the same bounded
   pulse. Use timestamped continuous IMU/image observations from a single owner
   to estimate settling latency and residual motion. Before/after stills alone
   cannot measure latency or stopping distance. Do not test Wi-Fi loss while
   moving before independent clearance and recovery are established.
6. Assessment: report median/spread of pixel motion, gyro response, bias drift,
   echo change and settling for each PWM/duration/direction. Preserve failures
   and unobserved trials. Fit models only to observed conditions; held-out repeats
   must support predictions before those models gate exploration.

## Completion and exploration gate

Complete only when repeated results cover each command, all four drive directions,
finite expiry/early stop, observable settling, camera return and fault handling.
Report unsupported stages as incomplete. Native-unit calibration does not provide
centimeters, calibrated yaw, obstacle size or physical stopping distance.

Before exploration define area/session bounds, coverage criteria and stop
conditions, and implement a controller that enforces fresh observations, bounded
positive-duration commands, one-owner logging and best-effort N100 cleanup.
Stop on sensor/camera/communication fault, unexpected movement, tilt/floor change,
obstacle entry, uncertain clearance or exceeded bounds. No autonomous runner or
clearance gate is established by this document.
