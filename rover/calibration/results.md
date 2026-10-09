# October 9 native-unit calibration results

## Continued improvements and first local observation pilot

Added timed HTTP camera recording with pre-motion IMU sampling, fresh bias
checks before every pulse, and offline rest/vision/IMU validation. One TCP owner
retains control; HTTP worker never sends rover commands. No firmware changes.

Runs in `data/20261009003013000`:

- `logs/20261009010738515`: refused movement on stationary-image gate; no N4.
- `logs/20261009010822507`: six timed-camera trials; later three stationary
  bias attempts rejected. N100 cleanup and failure evidence retained.
- `logs/20261009011141154`: 16 complete PWM60/T200 trials, alternating IMU.
  Pre-rest support 16/16, post-rest 15/16. Held-out visual/gyro median absolute
  difference 5.637 nominal degrees on four turn checks.
- `logs/20261009011637215`: local observation pilot, exactly three forward
  PWM60/T200 pulses (600 ms commanded total). Pre/post rest supported 3/3;
  raw echoes decreased from 12399 to 11918 us across the recorded steps.
  No metric positions/free-space proof. Images/IMU/sensors and observations.json
  retained. No reverse, turn or power increase in this pilot.
- `logs/20261009011850801`: eight gyro-focused PWM60/T200 turn trials. Active
  gyro gaps about 50–59 ms versus about 95 ms with alternating reads. Pre/post
  rest supported 8/8. Held-out visual/gyro median difference 0.588 nominal degrees
  on four turn checks. This small scene-specific comparison is consistency
  evidence, not absolute angular accuracy or proof of a causal accuracy gain.
- `logs/20261009012243615`: final stopped battery check 7.655 V, N100/close.

Matching analysis directories ending `-validation` hold JSON/report. Combined
new full-run/pilot integration is under `analysis/20261009011637215-integration`.
Raw unconstrained acceleration integrals still drift. A separate conditional
zero-velocity endpoint scenario is emitted only when both rest gates pass;
it is not validated distance and is not used as control odometry.

Bias-camera failures were diagnosed as inconsistent minority flow tracks while
the majority/IMU remained quiet. The rest gate now requires >=70% coherent
partial-affine support spanning >=25% image width/height; retains raw outlier
statistics and original 1 px median/3 px p95 limits on coherent tracks. Global
image movement/insufficient support still rejects recalibration. Eighteen
offline tests passed, including translated-image rejection and pilot bounds.

Default adaptive sampling now favors gyro during turns, alternating at rest.
Forward/backward still alternate gyro/accel. Full gyro-focused mode is available
for diagnostics; its sparse in-motion accel does not support displacement.
Sampling times/range readbacks, absolute scales, camera intrinsics, physical
stop distance and general room coverage remain unresolved. Forward early-stop
advantage also remains uncertain. Calibration improvement can continue during
these bounded observation pilots; unrestricted exploration is not implemented.

## Subsequent numerical integration and recurring gyro bias

The user clarified that integration means integrating gyro rate and acceleration
over time. Added `src/agent/integrate_imu.py`, computed on 48 saved trials from
the complete PWM60/PWM80 200 ms runs. Final output:
`data/20261009003013000/analysis/20261009005347000-inertial-integration-final/`.
JSON traces, CSV, report and PNG preserve raw integrals and conditional nominal
orientation/velocity/displacement estimates with timing/bias sensitivity.

Assumed nominal scales (source-selected ±250 deg/s, ±2g; no live register
verification) give group median PWM80 expiry yaw +15.328 deg left and -15.864 deg
right. Median final residual velocity increment norm over 48 trials was 0.2476
m/s under those assumptions, despite later image stability. Acceleration
integration does not establish reliable travel distance/coordinates. Timing/bias
scenario spans are sensitivity measures, not error bounds.

Added guarded stationary bias refresh before every future wheel trial: five paired
gyro/accel samples, camera/IMU stationarity gates, 10 s maximum bias age. Bias is
applied on host; firmware untouched. Live stationary-only check
`logs/20261009005954541/` accepted raw bias [-359.8, 62.6, 250.2], N1 7.857 V,
then N100/close. No wheels moved for this integration/bias task. This check
verified the stationary path; a new full wheel run with bias refresh was not run.
Thirteen numerical/bias/battery tests passed. Provisional rest thresholds do not
prove absence of all motion.

Session: `data/20261009003013000`, Exploration calibration. Safe area was
explicitly assumed by the user. The run ends stopped and disconnected.

Three complete runs covered N1–N8/N100, repeated stationary N5/N6 steps and
72 fully captured drive trials: PWM 60 / 100 ms, PWM 60 / 200 ms and PWM 80 /
200 ms. Each drive condition had three trials per direction per stop mode.
The first run had no in-motion IMU sampling; the latter two alternated gyro and
accelerometer reads. These are different timing conditions, not a pure duration
comparison. Preserve the raw command/response records when comparing them.

An additional 200 ms run stopped during its sixth wheel trial after a 250 ms
gyro-response timeout. Five complete trial records and the failed sixth trial's
raw traffic are retained. The reply arrived about 265 ms after request during
cleanup. TCP_NODELAY, fewer redundant heartbeats and a 750 ms response timeout
were then applied; stop deadlines remain independent of sensor replies.

## Observed response

| PWM / firmware duration | Forward median image motion px | Backward px | Left px | Right px |
|---|---:|---:|---:|---:|
| 60 / 100 ms | 2.780 | 1.715 | 3.013 | 39.594 |
| 60 / 200 ms | 5.301 | 4.504 | 85.061 | 93.726 |
| 80 / 200 ms | 8.182 | 4.423 | 148.106 | 149.711 |

Values above are expiry trials followed by explicit N100. Image displacement
depends on scene depth/orientation and is not travel distance or yaw.

At PWM 80, early N100 at 100 ms reduced median left/right image motion to
54.557/47.745 px. Forward early-stop motion was 8.091 px versus 8.182 px for
expiry: a reliable translation stopping advantage is not established.
Late-frame median motion was 0.333–0.434 px across those direction/stop groups.

Gyro Z response was positive for left and negative for right in the 200 ms
trials. At PWM 80, group median gyro return times were 247–413 ms after host
N100 send. These use a raw-count noise band and receipt timestamps; they are
not physical stopping latency or proof that translation ended. Acceleration
residuals and gyro count-second integrals are saved as supporting motion clues.
No coordinate estimate is established by integrating them.

Repeated N5 5-command-degree changes produced approximately 31–38 px image
motion. N6 ±5 produced approximately 34–40 px. N6 ±1 produced only 0.36–0.51 px
motion, comparable to stationary image variation; one-command-degree physical
response was not resolved. Actual physical servo angles remain unknown.

## Evidence

- `analysis/20261009003509244/`: complete PWM 60 / 100 ms and pan assessment.
- `analysis/20261009003805349/`: partial run and timeout evidence.
- `analysis/20261009003930548/`: complete PWM 60 / 200 ms assessment.
- `analysis/20261009004129863/`: complete PWM 80 / 200 ms assessment.
- Matching `logs/` and `captures/` directories preserve JSONL, trial JSON and
  JPEG/host timestamp manifests. Each assessment has report.md/measurements.json.
- `logs/20261009004436364/`: final N1 check, 7.857 V, followed by N100 cleanup.

## Operating limits

User-defined low-battery rule is now enforced: N1 <7.0 V stops immediately and
ends the runner. Missing/invalid voltage is a fault. Exactly 7.0 V is permitted.
Battery is checked before/after every short pulse; voltage accuracy is unverified.
Three offline tests verified cutoff, exact boundary and nonfinite-value handling;
the final above-threshold check ran on hardware. A physical low-battery event was
not induced.

Calibration remains partial for exploration: metric scale, calibrated yaw,
physical stop distance, held-out predictive motion tests and a fused pose/
uncertainty/clearance controller remain unestablished. PWM 80 response is measured
for these isolated 200 ms trials; longer/higher-power exploration is not validated.
The next stage is motion/pose validation within this measured envelope, with
fresh battery/IMU/scene evidence and recorded uncertainty.
