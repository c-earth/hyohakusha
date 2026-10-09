# ELEGOO rover project

AI-assisted control of an ELEGOO Smart Robot Car V4.0, with a longer-term goal
of bounded exploration and reconstruction of the interior visible to its camera.
Manual tools, bounded calibration and 1-3-action exploration segments with
calibration evidence are implemented. General autonomous room search, metric pose and 3D reconstruction
are not implemented.

Start with [handoff](handoff.txt) for current state and
[next live test](rover/calibration/next-test.md) for a focused proposed session.
Operating gates are in [calibration procedure](rover/calibration/procedure.md);
historical evidence is in [results](rover/calibration/results.md) and [journal](journal.md).
Examples below are usage references, not authorization to operate.

The current host passes 53 offline Python tests, PowerShell reply/launcher checks
and command import checks. The [charged-session plan](rover/calibration/next-test.md)
starts with fresh stopped evidence and one short action, then interleaves
calibration with bounded exploration in the prepared area. Hardware verification
of the refactored host and installed October 9 firmware remains outstanding.

## Hardware

- Arduino UNO, TB6612FNG motor driver and MPU6050 IMU.
- ESP32-S3-WROOM-1 camera with 8 MB flash and 8 MB PSRAM.
- Forward camera/ultrasound, downward floor/light sensors and camera pan servo.
- No motor encoders or servo position feedback have been established.

Camera access, sensor replies, pan/return, short movement response and later
image/IMU settling have been observed. Absolute sensor accuracy, calibrated
heading, metric translation, physical stopping distance and camera intrinsics
remain unverified. Battery cutoff is N1 <7.0 V; invalid/missing readings fault.

## Connection setup

Use PowerShell 7 from the project root. Connect to rover Wi-Fi, set the
Upload-Cam switch to Cam and close the ELEGOO app. One controller owns TCP.
Default address: 192.168.4.1; scripts accept an Address override.

Endpoints: HTTP /status and /capture, MJPEG
[stream](http://192.168.4.1:81/stream), TCP port 100. The downloaded camera source
specifies Wi-Fi channel 9; its identity with installed firmware is unproven.
The keyboard panel embeds a JPEG snapshot/live preview using HTTP /capture.

## Command-line tools

Current UNO firmware was uploaded October 9, 2026, with flash read-back
verification. Historical journal examples may use superseded IDs.

| Command | Contract |
|---|---|
| N1 | Estimated battery V, three fractional digits; conversion accuracy unverified. |
| N2 | Signed raw gyro XYZ counts; no host bias subtraction in firmware reply. |
| N3 | Signed raw accelerometer XYZ counts, including gravity. |
| N4 | Timed drive; T in milliseconds, T=0 bypasses expiry. |
| N5 | Absolute servo command; pan D1=1, target D2 in command degrees. |
| N6 | Signed pan increment D1; clamped command state, no angle feedback. |
| N7 | Ultrasound; D1=2 returns raw echo microseconds, T is timeout microseconds. Zero means unknown. |
| N8 | Fresh floor ADC; D1=0/1/2 selects left/middle/right. |
| N100 | Stop/standby; acknowledgment does not prove physical rest. |

Onboard autonomous modes, button/IR control and automatic battery monitoring
were removed from the installed UNO application. It retains startup
servo positioning and LED initialization. Forward/backward use
requested PWM without the previous gyro correction. The installed October 9 build
removes the unused startup gyro-offset calculation.

The candidate reports faults as `{H_error_reason}` or `{error_reason}` without
a tag. Reasons are `imu_not_ready`, `imu_read`, `drive_busy`, `drive_direction`,
`bad_json` and `frame_too_long`. Motor output stops before the error reply.
Python acquisition and PowerShell controllers now reject these replies; valid
installed-firmware replies remain supported. A failed IMU read latches readiness
false, so N2/N3/N4 refuse subsequent requests until successful initialization at
board restart. N5/N6/N7 during a drive stop it and reject the blocking request.
N100 retains `{ok}`; the candidate stops output before acknowledging it.

```powershell
./src/tools/rover.ps1 -Action Sensors
./src/tools/rover.ps1 -Action Stop
./src/tools/rover.ps1 -Action Record -Seconds 10 -FramesPerSecond 2 -SessionTimestamp <17-digit-session-start> -ChatName '<chat-name>'
```

Sensors reads battery, IMU, raw ultrasound and floor ADC. Ultrasound timeout
defaults to 30,000 us; host range is 1-1,000,000 us. Record downloads JPEGs with
host UTC request/receipt times, not exposure times.

The manual Move action requires EnableMovement and accepts PWM 1-100:
```powershell
./src/tools/rover.ps1 -Action Move -Direction Forward -DurationMs 200 -Speed 60 -EnableMovement
```

DurationMs is an unrestricted integer/default 200; T=0 bypasses firmware expiry.
The tool polls for completion/faults for up to DurationMs+100 ms, then sends N100
and closes TCP. Extreme values can fail host integer conversion. Stop cleanup is
also attempted after faults. It does not enforce calibration gates; use the
bounded calibration entry for experiments.

PanTest performs 90/100/90; FinePanTest performs 100/101/100. Both require
SessionTimestamp and ChatName. PanStep uses PanStepDegrees (default 1).
N6 request example: `{"N":6,"D1":1,"H":"pan"}`.
Command 100 was provisionally identified by the user as forward; increasing
commands pan left. camera.json is historical command state, not feedback.

## Keyboard driving

```powershell
pwsh -NoProfile -STA -File ./src/control/keyboard-rover.ps1
```

Starts disconnected and disabled. Connect, then enable driving with clear floor.
Hold WASD/arrows; release to stop. Space/Escape, focus loss, closing, or multiple
directions stop and disable driving. Default PWM60 (range 20-100); N4/T250 is
renewed every 100 ms. No automatic obstacle avoidance. SelfTest is an offline
execution option and requires task authorization.

Buttons and shortcuts provide the manual observation/pan interfaces:

| Control | Action |
|---|---|
| Check sensors / F5 | Battery, raw gyro/accelerometer XYZ, ultrasound echo us and left/middle/right floor ADC. |
| Snapshot / F6 | Display a JPEG in the window; no file saved. |
| Live JPEG preview checkbox | Repeated asynchronous /capture requests, with 500 ms between completed requests; actual frame rate depends on camera/network. |
| Pan - / F8, Pan + / F9 | Signed command increment, step 1-20 degrees (default 1). Increasing commands pan left. |
| Pan target / F10 | Absolute command target 10-170 degrees (default 100); no position feedback. |

Sensor/pan requests send Stop and disable driving, use the same TCP owner, and
allow one pending reply. Re-enable driving after completion. Space/Escape cancels
queued requests and sends Stop; any already-sent request drains or times out.
Faults, missing replies, or invalid/below-7.0 V battery replies disconnect with
best-effort Stop. Battery checks are manual, not continuous battery monitoring.
Readings and images show host times and may become stale; raw values do not
establish sensor accuracy, clearance or physical rest. Ultrasound zero is unknown.
Camera uses HTTP only and can operate while TCP is disconnected. Preview errors
disable live refresh and mark the displayed image as potentially stale.
The additions passed offline syntax and keyboard/queue SelfTest checks; window
layout, camera refresh and live sensor/pan operation remain unverified on hardware.

Observed individual trials support timed expiry, early N100 and stopping after
TCP close/heartbeat timeout. Physical stop distance, abrupt Wi-Fi-loss behavior
and reliability across conditions remain unverified.

## Calibration and capture data

[Next test](rover/calibration/next-test.md) provides the proposed focused recipe.
run_calibration.ps1 delegates one Python TCP owner. Bounds are PWM60/80 and
T100/200; stationary-only, turn-only, timed-camera and repeat options are exposed.
src/tools/run_exploration.ps1 defaults to three PWM60/T200 forward pulses.
`-Actions 'forward,left,forward'` freezes a segment of up to three forward/left/right
actions under the same limits. Bias/rest checks and camera/IMU evidence accompany
every action, so calibration can continue while exploring the prepared area.
Its >20% echo-shortening trigger applies while heading is unchanged; a turn
starts a new echo reference. It is not verified collision avoidance.

Python modules run from the project root with `-m`; canonical PowerShell launchers
under src/tools set that directory and restore it afterward. Existing src/agent
launcher paths forward their parameters and remain usable:

```powershell
.venv\Scripts\python.exe -m src.agent.analysis.validate_motion data/<session>/logs/<run> --output data/<session>/analysis/<new-output>
.venv\Scripts\python.exe -m src.agent.analysis.integrate_imu data/<session>/logs/<run> --output data/<session>/analysis/<new-output>
```

The runtime refuses starts more than 50 ms late and pre-motion camera evidence
older than 500 ms, and rechecks the 10 s bias limit at dispatch. These provisional
host limits are offline-tested, not yet live-verified. Failed trials retain
status/error, partial telemetry and camera evidence. Command send and socket
receipt brackets exclude subsequent log-write time.

Validation retains unsupported trials with exclusion reasons. Only complete,
rest-supported trials enter the visual/gyro comparison. Its current heading
diagnostic integrates the full gyro Z record; historical reports used Euler yaw
over accel overlap, so their medians are not directly comparable. Cleanup is
reported as unknown when a positive socket-close record is absent.

One controller serializes movement/pan actions. N2/N3 readings from that owner
and HTTP-only camera recording may observe the active motion; N100 has priority.
Keep N5/N6 and blocking N7 out of active drive. Host timing brackets are not
sensor acquisition times. Gyro/image consistency does not establish absolute
angle, and acceleration integration is not validated odometry.
The shared transport refuses overlapping actions, a second pending sensor and
access from another thread. The sampler drains its final IMU reply before the
next stopped read. This does not replace closing other controller applications.
Captures retain an optional `camera_timestamp` from HTTP `X-Timestamp`.
Its device clock/exposure meaning is unverified; analysis still uses host brackets.

Use New York session-start timestamps in yyyyMMddHHmmssfff format and reuse
the same SessionTimestamp/ChatName within a chat. Metadata conflicts are rejected.
Captures retain their filenames and purpose info.txt; do not rename old data.
Calibration logs include JSONL and trials.json; captures include frames.json and
timed trial subfolders. Manual Record uses frames.csv. Analysis belongs beside
captures/logs in the same session.

## Project structure

| Path | Purpose |
|---|---|
| data/<session>/captures, logs, analysis | Raw observations, command evidence and derived diagnostics. |
| src/control/ | Shared TCP owner, protocol, pulse scheduler and HTTP-only recorder; keyboard controller. |
| src/agent/*.ps1 | Compatibility forwarding entries to src/tools. |
| src/agent/runtime/ | Calibration/exploration decisions, gyro-bias gates and experiment records. |
| src/agent/analysis/ | Saved-data assessment, inertial mathematics and report commands. |
| src/agent/tests/ | Offline regressions using fake transports and synthetic data. |
| .agents/skills/rover-experiment/ | Project skill routing experiment preparation and assessment. |
| src/tools/ | Manual rover tool and calibration, exploration, baseline and survey launchers. |
| src/control/keyboard-rover.ps1 | Keyboard controller. |
| src/control/rover-protocol.psm1 | Shared PowerShell firmware-fault handling. |
| rover/calibration/ | Procedure, next experiment, results and provisional camera state. |
| rover/firmware/src, build | Current source and firmware artifacts. |
| rover/backups/20261007183240988/ | Preserved original sources/readbacks. |
| rover/vendor/ | Retained vendor manuals, examples, libraries and models. |
| tools/arduino, tools/esptool | Separate firmware tool installations. |

Unused empty source reservations were removed. Mapping/reconstruction remain
roadmap work; their absence is explicit in handoff.

## Firmware and backups

October 9 UNO upload/read-back on COM3 verified 19,762 application flash bytes
with accepted ATmega328P signature 1E 95 0F. Runtime behavior remains unverified.
The saved October 8 build contains 20,416 application flash bytes.
Its saved build/uno/flash.hex and eeprom.hex are retained; EEPROM output contains
no EEPROM data. The October 9 build is compiled separately and now installed:

| UNO build | Flash / 32,256 bytes | Global RAM / 2,048 bytes |
|---|---:|---:|
| Saved October 8 | 20,416 | 794 |
| Installed October 9 | 19,762 | 664 |

Candidate: `rover/firmware/build/uno-candidate-20261009/uno.ino.hex`.
It isolates N4's completion tag and timer, services expiry around serial/sensor
work, validates IMU identity/configuration/read status, and bounds each Wire wait
to 10,000 us. N5 now acknowledges after its driver returns. Direct PWM, command
IDs, sensor units, servo limits, N4/T=0 and 9600-baud UART remain unchanged.
The timeout and cooperative expiry checks do not prove physical stop latency.

Offline checks passed: UNO build, ten production-timer compile-time assertions,
41 Python tests, twelve PowerShell reply checks, keyboard SelfTest and parsing of
four changed PowerShell sources. Hardware I2C fault injection, UART ordering and
physical stopping have not been exercised on this candidate. Build/check details
are in journal and candidate verification.json. Upload passed; live checks remain
separate work.

Original UNO backups contain full 32 KB flash and 1 KB EEPROM readbacks; fuse
and lock backup is absent. Camera was not flashed. Active/backup ESP32 flash.bin
are full 8 MB readbacks; downloaded S3 source is not proven identical.
Preserve vendor/backup artifacts. The redundant euler.md was removed after its
bias-corrected gyro integration informed analysis/inertial.py. The original
legacy function remains in the backup; onboard yaw correction was not restored.

The [legacy review](rover/firmware/legacy-review.txt) covers application modes,
drivers, IMU/library interfaces, networking, camera handlers and web UI. It
records useful calibration/efficiency leads and source defects separately from
available host features. In particular, use raw N7 D1=2: current D1=1 compares
microseconds against 20 and is not a calibrated obstacle-distance flag.

Vendor camera settings: ESP32S3 Dev Module, USB CDC On Boot, 8 MB flash,
8M with SPIFFS (3 MB APP/1.5 MB SPIFFS), OPI PSRAM. See firmware/info.txt.
Ports/connectivity must be re-established before any authorized upload/live check.

## Development tools and references

Project Python: .venv\Scripts\python.exe; pyvenv.cfg records Python 3.13.13 and
base D:\local\python\python_3_13_13\python.exe. OpenCV, NumPy, Pillow, SciPy,
scikit-image and Matplotlib were installed/import-checked previously.
Additional installation and execution require explicit task scope.

Arduino CLI: tools/arduino/arduino-cli/arduino-cli.exe, configuration
tools/arduino/arduino-cli.yaml (checkout-specific absolute paths).
Recorded installation: AVR core 1.8.8, Servo 1.3.0, FastLED 3.2.10.
Esptool 5.4.0 under tools/esptool requires its compatible Python runtime;
keep its Python 3.12-specific native packages outside .venv.

Authorized offline regression command:

```powershell
.venv\Scripts\python.exe -B -m unittest discover -s src/agent/tests -t . -v
pwsh -NoProfile -File ./src/agent/tests/test_firmware_replies.ps1
pwsh -NoProfile -File ./src/agent/tests/test_launchers.ps1
```

The repository skill uses the documented
[local skill layout](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills).
The repository skill is available in this chat. Its bundled validator was not
run successfully during creation because PyYAML was absent.

[Official ELEGOO reference](https://github.com/elegooofficial/ELEGOO-Smart-Robot-Car-Kit-V4.0).
