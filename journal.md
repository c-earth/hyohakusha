# Project journal

Historical record relocated from handoff.txt on October 8, 2026.
Read handoff.txt for current state and AGENTS.md for working instructions.
Entries below preserve the prior record verbatim, including superseded findings,
old command IDs, proposed roadmaps and historical authorizations. They do not
establish current capabilities or grant authorization for new work.

## Archived handoff and completed work

ELEGOO rover project handoff

OCTOBER 8, 2026: PROJECT ROVER COMMAND PREFIX RULE
- User explicitly requested adding the necessary prefix to project RULES. Created .codex/rules/rover.rules allowing the exact prefix pwsh -NoProfile -File ./src/tools/rover.ps1, following existing project-local prefix_rule syntax. Arguments after the script path are covered; arbitrary PowerShell code and in-memory variants are not covered.
- Explicit task authorization remains required under AGENTS.md. Read back the rule; no rover command, parser test or rule-reload check performed. Whether the current session loads this new rule is unverified. Existing .codex/ is untracked; no commit or push requested.

OCTOBER 8, 2026: REMOVE HOST MOVEMENT DURATION RANGE
- User explicitly requested removing the timed limit in rover.ps1. Removed ValidateRange(50,500) from DurationMs; integer type and default 200 ms remain. Updated README to describe the unrestricted integer parameter and existing T=0 firmware expiry bypass / host N100 behavior.
- Verified the target before editing and reviewed the patch. No script execution, tests or rover commands performed. Negative/extreme integer durations are not validated and can fail the existing host wait; firmware timing behavior was not changed. Drive calibration followed by bounded search with reconstruction data collection is the user's revised direction; earlier functional checks are not drive calibration.
Prepared: October 8, 2026, America/New_York
Workspace: D:\projects\hyohakusha

PURPOSE OF THIS HANDOFF

Resume the project with its current instructions, files, and user decisions.
This is a session snapshot, not standing authorization to perform the proposed
next steps. Read AGENTS.md first. Read README.md for project facts and usage,
and WORKFLOW.md for the proposed decision flow and agent hierarchy.

The current request authorizes rereading the whole handoff, review with three
subagents, and updating this file with evidence and ordered next steps. The user
also granted continuing authorization to update this handoff as authorized tasks
are completed. No roadmap implementation, test, dependency installation,
simulation, or hardware session is authorized merely by its inclusion here.

PROJECT GOAL AND CURRENT STAGE

Connect an AI agent to an ELEGOO Smart Robot Car V4.0 for manual control, then
bounded exploration of an accessible surface and 3D reconstruction of the
interior visible to the camera.

Existing implementation: two PowerShell scripts for keyboard driving, sensor
readings, JPEG recording, timed movement, standby, and camera pan tests.
Future proposals: shared rover interface, coordinated session logging,
observation/state estimation, reconstruction, planning, and autonomous motion.
The proposed controller and agent roles in WORKFLOW.md are not an implemented
runtime architecture. The Python environment exists, but no project Python
control or reconstruction application has been created in the work recorded here.

Accepted architecture in the current conversation: retain PowerShell for rover
control; use a separate vision/reconstruction component. Its language, processing
method, and live communication boundary remain undecided. A Python migration of
rover control is not planned. No shared interface has been implemented.

IMPORTANT USER INSTRUCTIONS

AGENTS.md contains the user's response, evidence, authorization, clarification,
context, and coding requirements. Read the actual file rather than relying on
this summary. In particular:

- Be concise and direct. For yes/no questions, start Yes, No, or Unknown.
- Separate verified findings, assumptions, and proposals. Withdraw unsupported
  claims explicitly. Do not invent capabilities, checks, or user preferences.
- Informational requests authorize inspection/explanation only. File changes,
  code execution, tests, installations, and simulations need explicit scope.
- Focused read-only project inspection is allowed. All Python execution needs
  explicit authorization, even if used for inspection.
- Reading outside the project workspace requires explicit authorization.
- Do not treat your own plan as approval. Do not ask again within an already
  authorized scope. Ask and wait when material scope or intent is ambiguous.
- Use proper object-oriented code, import ordering, and descriptive docstrings
  as specified in AGENTS.md.
- Use one main agent. Subagents require the user's explicit delegation request.
- Keep a single owner of the rover TCP connection.

The user wants AGENTS.md to contain instructions useful to the agent, not
setup history, repetitive reminders, personal preference guesses, or lengthy
project facts already retrievable from README. Do not expand it back into a
handoff or troubleshooting history without a request.

CURRENT ROOT AND FILE ROLES

.venv/       Project Python virtual environment.
data/        Existing camera capture sessions.
rover/       Firmware, backups, calibration, and retained vendor package.
src/         Project PowerShell scripts grouped by purpose.
tools/       Local Arduino toolchain and separate esptool package installation.
AGENTS.md    Standing agent instructions and retrieval pointers.
README.md    User-facing project description, structure, usage, and provenance.
WORKFLOW.md  Proposed workflow, Mermaid diagrams, and development sequence.
handoff.txt  This session snapshot, newly created at the user's request.

The previous handoff was explicitly removed in the previous chat. The present
file is newly authorized; it does not restore the old file's unsupported claims.

COMPLETED IN THE PREVIOUS CHAT (HISTORICAL)

1. Organized src:
   src/control/keyboard-rover.ps1
   src/tools/rover.ps1
   Updated the recording path calculation after moving rover.ps1 so captures
   still go to the project root's data/captures. Updated README commands.

2. Reviewed file placement across the pre-venv inventory: 4,935 files, including
   hidden files, 318 retained vendor files, and 4,527 installed tool files.
   This was a placement/dependency review, not a line-by-line correctness audit
   of every third-party implementation. Do not report that old count as current;
   creating .venv and documentation changed the inventory afterward.

3. Fixed active UNO .vscode/arduino.json:
   board = arduino:avr:uno
   sketch = uno.ino
   Removed stale COM13 and AVRISP mkII entries. No replacement port hardcoded.

4. Removed vendor temporary Word lock file:
   rover/vendor/ELEGOO Smart Robot Car Kit V4.0 2023.02.01/
   03 Tutorial & Code/02 SmartRobotCarV4.0_Move/~$nquerorCar_Move.docx
   It was a lock/owner file, not a tutorial document.

5. Fixed six vendor .vscode/arduino.json sketch references, changing only the
   sketch filename to the .ino file actually present:
   - WROVER camera example: ESP32_CameraServer_AP_20210107.ino ->
     ESP32_CameraServer_AP_20220120.ino
   - Obstacle DRV8835 Demo2 and TB6612 Demo2:
     ConquerorCar.ino -> Demo2.ino
   - Follow DRV8835 Demo1 and TB6612 Demo1:
     ConquerorCar.ino -> Demo1.ino
   - DIY/App SmartRobotCarV4.0_V1_20220303:
     SmartRobotCarV4.0_V1_20201229.ino -> SmartRobotCarV4.0_V1_20220303.ino
   No source code was missing; editor configurations had outdated names.

6. Rewrote README to match current script locations, confirmed S3 hardware,
   calibration path, firmware/source/readback distinctions, capture behavior,
   tools, and retained vendor package. Removed obsolete archive references.

7. Created Python .venv using the latest installed interpreter found, 3.13.13.
   The user meant newest on this computer, not newest public release.
   A downloaded 3.14.8 installer was never installed. Removed its tools/python
   directory after the user explicitly requested cleanup.

8. Created AGENTS.md with the user's supplied rules, then removed redundant
   README facts and unnecessary session history at the user's direction.

9. Created WORKFLOW.md with decision process, hierarchy, runtime loop, and
   proposed implementation stages. Added a retrieval reference in AGENTS.md.

10. Extended this handoff through stages 0-10 and final project completion
    criteria. Updated AGENTS.md to retrieve this handoff and maintain it as
    authorized tasks finish. Verified the saved retrieval and maintenance
    instructions by read-only text inspection. No roadmap stage has been
    completed by these documentation changes.

ACCEPTED AS-IS: DO NOT REOPEN AS CLEANUP PROBLEMS

- Active UNO source retains SmartRobotCarV4.0_V1_20230201.hex and addLibrary ZIPs.
  The user explicitly said this is not a problem. Identical copies were found
  in rover/backups/20261007183240988/src/uno, including addLibrary.
- Active UNO .vscode/c_cpp_properties.json retains old third-party installation
  paths. The user explicitly said this is not a problem. It was not changed.
- Existing capture filenames vary. The user did NOT establish a preferred
  frame000000.jpg format. An earlier handoff's preference claim was withdrawn.
- Firmware readback/source provenance, differing backup times, and unimplemented
  future features are facts, not cleanup problems the user asked to fix.
- Keep the retained ELEGOO vendor package. Do not delete it as obsolete just
  because it contains other board variants or older WROVER examples.

PYTHON ENVIRONMENT

.venv/pyvenv.cfg currently records:
  version: 3.13.13
  base executable: D:\local\python\python_3_13_13\python.exe
  include-system-site-packages: false

Use .venv\Scripts\python.exe for authorized project Python work and
.venv\Scripts\python.exe -m pip for authorized dependency operations.
Optional PowerShell activation: .\.venv\Scripts\Activate.ps1

Earlier checks found local Python 3.9.25, local 3.13.13, and the bundled runtime
3.12.14. This is historical evidence, not a current exhaustive system inventory.

The initial venv creation failed in ensurepip because the sandbox blocked
temporary-file access. Explicitly approved execution outside the sandbox
completed pip setup. Python 3.13.13, distinct venv/base prefixes, and pip 26.0.1
were then verified. Reverification is not automatically authorized.

tools/esptool remains separate, installed for the bundled Python 3.12 runtime.
It includes cp312 native extensions. Do not inject it into Python 3.13's
PYTHONPATH. No migration or reinstall into .venv has been requested.

ROVER AND FIRMWARE CONTEXT

Confirmed hardware: ELEGOO V4.0, Arduino UNO, TB6612FNG, MPU6050, and
ESP32-S3-WROOM-1 camera board with 8 MB flash and 8 MB PSRAM.
Do not revive the earlier WROVER hardware assumption.

Default network address 192.168.4.1; HTTP /status and /capture; MJPEG stream
http://192.168.4.1:81/stream; TCP control port 100. The camera source uses
Wi-Fi channel 9. Current Wi-Fi connectivity and serial port assignments are
unknown. Historical COM3/COM5 assignments do not establish current ports.

UNO source was patched and uploaded on October 7, 2026 for 1-degree N5 servo
commands. Built-in modes retain their original servo interface.
Active build/uno/flash.hex: compiled app, 31,068 data bytes.
Active build/uno/eeprom.hex: compiler output, no EEPROM data.
Backup build/uno/flash.hex: 32,768-byte original memory readback.
Backup build/uno/eeprom.hex: 1,024-byte original memory readback.
Fuse/lock settings were not backed up.

Camera firmware was never written or erased by this project. Active and backup
build/esp32/flash.bin are identical full 8 MB readbacks from offset 0, containing
bootloader, partition table, application, and stored data. Downloaded S3 source
is not proven to match installed firmware. See firmware/info.txt and README.

Camera pan calibration: provisional command 100 degrees straight ahead,
increasing commands turn left. Historical command values are not current-state
feedback. Scripts do not load camera.json automatically.
No motor encoders or servo angle feedback have been established.

EXISTING SCRIPT BEHAVIOR

keyboard-rover.ps1:
- PowerShell 7 Windows Forms; starts disconnected and disarmed.
- WASD/arrows; conflicting directions stop.
- PWM 20-100, default 60.
- Timed N2 T250 ms, renewed every 100 ms.
- Key release, Space/Escape, focus loss, and close initiate stopping.
- Heartbeat freshness handling; no automatic obstacle avoidance.
- SelfTest returns before GUI/network setup.

rover.ps1:
- Actions Sensors, Record, Move, Stop, PanTest, FinePanTest.
- Move requires EnableMovement, PWM 1-100, duration 50-500 ms.
- Sensors reads ultrasound and three floor values using TCP responses.
- Record uses HTTP capture and frame-000000.jpg-style filenames plus frames.csv.
- PanTest 90 -> 100 -> 90; FinePanTest 100 -> 101 -> 100.
- Pan tests capture center/pan/return JPEGs and attempt servo restoration.
- Opening/closing a control connection can affect standby behavior.

Read source before modifying behavior. Do not run these scripts to inspect them
unless execution is authorized. Pan tests are physical servo operations.

VERIFICATION ALREADY PERFORMED

During the previous chat, before the standing authorization rules were added:
- Both moved PowerShell scripts passed parser syntax checks.
- Keyboard SelfTest passed, including from another working directory.
- Capture path was checked against the project-root data/captures location.
  An extracted-function test initially failed because its synthetic scriptblock
  had no PSScriptRoot; a subsequent check substituted the real script directory
  and confirmed path resolution. No live recording was used for this check.
- Existing recording CSV entries referenced files present in their session.
- Active/backup sketch names matched their folder names.
- Local firmware header relationships were checked; external SDK headers were
  distinguished from local source files. ESP32 SDK is not installed in the
  local Arduino package tree; camera compilation was not verified.
- UNO HEX files parsed successfully and data sizes above were read.
- Active and backup ESP32 readbacks had identical SHA-256 hashes.
- Esptool package manifest files and relocated launcher entries existed;
  esptool version execution reported 5.4.0.
- Six edited vendor sketch references and active UNO sketch reference resolved.
- README's documented project paths were checked for existence.
- New AGENTS and WORKFLOW files were read back. Mermaid rendering was not tested.
- Venv Python and pip were verified after authorized pip setup.

No rover network, wheel, servo, flash-write, or erase operations were performed
in that previous chat. Historical physical verification must not be presented
as a new test or proof of current connectivity.

CURRENT CONVERSATION: PERMISSIONS AND READ-ONLY REVIEW

- The user reported the rover was off. An explicitly authorized HTTP /status
  request to 192.168.4.1:80 failed inside the sandbox with a socket access-
  permissions error. The escalation approval was canceled; the outside-sandbox
  request was not established as executed. This does not verify live connectivity.
- The user wants approval for rover-control commands outside the sandbox to
  persist for this project only. AGENTS.md is not a sandbox permission mechanism;
  the earlier suggestion to solve this through AGENTS.md was withdrawn.
- A project-local .codex/rules/rover.rules command-prefix allow rule was proposed.
  No .codex directory was present in the inspected project root. No persistent
  rule/configuration was created or verified. A remembered global user rule must
  not be assumed project-only. Rules match command prefixes, not the semantic
  category "all rover-related commands". A shared stable entry point is proposed
  to make future rover actions use a narrow repeatable invocation.
- The proposed src/control/RoverClient.psm1 is a possible shared module location,
  not an implemented module or approved final file specification.
- Three explicitly requested subagents reviewed firmware/sensors, host control,
  and calibration/reconstruction prerequisites. They performed read-only project
  inspection; only the main agent edited this handoff. No project code, firmware
  builds, offline tests, simulations, sensor measurements, or hardware operations
  were run for this review.

SOURCE FINDINGS: NOT PHYSICAL MEASUREMENTS

Firmware findings below refer to the inspected active UNO source and local AVR
core. Camera findings refer to downloaded source, which remains unproven against
the installed camera firmware. Do not call every quantization or design choice a
calibration defect; distinguish code defects from accuracy requiring measurement.

- DeviceDriverSet_xxx0.cpp:277-299 casts pulseIn's duration to unsigned int before
  dividing by 58. On the UNO AVR target this narrows to 16 bits before conversion.
  It truncates whole centimeters (not rounds up), clips computed values above
  150 to 150, and gives no separate validity/saturation status. No-echo returns 0;
  0 must not be interpreted as a verified zero-distance obstacle or free space.
  Long pulse durations can wrap before division; no physical occurrence was
  demonstrated. Host code cannot recover raw precision/status already discarded.
- pulseIn has no explicit timeout in that driver. The installed AVR core header
  tools/arduino/arduino-data/packages/arduino/hardware/avr/1.8.8/cores/arduino/
  Arduino.h defines a default of 1,000,000 microseconds. Ultrasound queries run
  synchronously in serial command handling, before timed-motion processing in
  uno.ino. Blocking acquisition can therefore delay subsequent command/expiry
  handling; actual motor overrun duration has not been measured.
- ApplicationFunctionSet_xxx0.cpp:1198 onward: N2 expiry is loop-polled and T=0
  bypasses its expiry condition. Firmware does not enforce the host's 50-500 ms
  duration bounds. Review command validation and zero/missing/out-of-range fields
  before treating host limits as a firmware guarantee.
- N22 floor-query handling ends by setting CMD_Programming_mode (:1613), without
  stopping motors there. N5 pan also changes functional mode (:1857). N2 expiry
  runs only while CMD_CarControl_TimeLimit is active, so a query/pan can disable
  that expiry path while previously set motor output may remain. This is a
  critical source-level integration hazard; do not combine sensing/pan and motion
  until expiry is independent of those mode changes or a verified restriction
  prevents the hazard. No physical runaway/overrun was demonstrated.
- N2's tagged acknowledgment is emitted after expiry invokes stopping, not on
  receipt. N100 emits {ok} while parsing, before later motor-stop processing.
  Neither reply establishes an observed physical stop; log their meanings
  separately rather than treating every _ok/ok as command completion.
- Straight-line motor control applies gyro correction to requested PWM and clamps
  each output to 10-180 in timed/untimed command modes. A host request of PWM 60
  is therefore not necessarily a per-wheel output cap of 60. Decide whether bounds
  refer to requested PWM, actual motor output, or measured motion.
- Floor values are raw ADC readings updated in the loop; N22 serializes cached
  values without acquisition timestamps. Leave-ground detection uses fixed
  thresholds. These are not measured distance or validated edge detection.
- Voltage conversion uses ADC * 0.0375 plus 8% compensation. Its accuracy is
  unverified; compare with a reference meter before relying on voltage decisions.
  The low-voltage counter is not cleared on above-threshold readings, despite
  its continuity comment (ApplicationFunctionSet_xxx0.cpp:328-345).
- MPU6050 source provides gyro bias/yaw integration for motor correction. This
  does not establish usable host IMU telemetry or calibrated localization.
  MPU6050_getdata.cpp:34 has an uninitialized init retry counter; the caller does
  not act on the reported init error. Calibration adds samples to existing gzo
  without clearing it and uses integer division for the bias mean (:56-64).
  Yaw integration uses floating point, but drops per-sample increments below
  0.05 degrees (:75-79), making the deadband depend on sampling interval.
  Calibration does not reset integration timing/angle; no IMU telemetry query
  was found in the inspected command switch. These are source findings, not
  measurements of current drift or a claim that all IMU arithmetic is integer.
- UNO serial framing accumulates a String until a closing brace, without an
  explicit receive-length cap or partial-frame expiry. Review malformed frames,
  resynchronization, command validation and stop priority together.
- Camera reference source forwards commands, sends heartbeats, and sends standby
  on disconnect. That source behavior is not verified protection on the installed
  camera. Stop effectiveness and latency require observed physical checks.

Host findings from src/control/keyboard-rover.ps1 and src/tools/rover.ps1:
- TCP, writes, parsing and lifecycle logic are duplicated. No cross-process
  control ownership lock or coordinated command/sensor/capture log is implemented.
- CLI Read-Rover discards other-tag responses, recreates its buffer per call, has
  no receive-length cap, and checks its deadline outside the DataAvailable loop.
  Persistent incoming data can postpone that check. Keyboard code limits input
  per tick and partial-frame length but interprets only heartbeat replies.
- Move asks the operator to verify sensors; it does not perform that verification,
  wait for a movement acknowledgment, or measure physical motion/stopping.
- CLI cleanup disposes TCP. Pan restoration failure can bypass the explicit
  standby send; cleanup must attempt stopping independently of restoration.
- Neither script loads camera.json. PanTest starts at 90, although provisional
  forward alignment is 100. The pan tests are relative test sequences, not a
  calibrated world-angle measurement.
- Capture request/receipt timestamps are not exposure times. Pan captures lack
  the recording timestamp manifest and its JPEG signature check. A historical
  commanded pan angle is not measured present position.

Saved-data inspection found four sessions and twelve JPEGs: one initial frame,
five recording frames, and two three-image pan/return tests. Only the recording
has frames.csv. No images were processed or visually assessed in this review.
The inspected metadata establishes no translated camera poses, metric reference,
intrinsic/distortion calibration, or sensor/wheel/IMU calibration results. Do not
assume these images suffice for reconstruction or rename accepted filenames.

WHAT TO DO NEXT: PROPOSED, NOT AUTHORIZED

Next engineering milestone: resolve the firmware/protocol correctness and timing
contract, decide essential corrections, and define their verification scope.
The previous "shared interface first" recommendation was premature. Source review
has begun, but corrections, builds, flashing and physical verification have not.
Do not unconditionally flash the camera merely because its reference source was
reviewed. Finish the prerequisite gates below before freezing the shared interface
or trusting measurements for autonomous decisions.

Start the next chat as follows:
1. Read AGENTS.md, then relevant README and WORKFLOW sections.
2. Establish the user's next requested action. If they ask to continue without
   a defined scope, propose one concrete next action, file scope and reason.
3. Explicitly distinguish permission to edit from permission to run offline
   checks, install dependencies, use mocks/simulations, or contact the rover.
4. Only inspect relevant files until those actions are authorized.

Shared-interface scope after the firmware/protocol decision:
- Define one object-oriented interface for connection/session lifecycle,
  command encoding, brace-delimited response parsing, sensor retrieval, HTTP
  capture, and standby.
- Keep rover control in PowerShell (accepted). Proposed module location:
  src/control/RoverClient.psm1. Agree integration and public entry-point scope;
  separate vision/reconstruction technology is still open.
- Keep the current working PowerShell entry points until their replacement or
  integration is specifically requested. Do not remove or refactor them broadly.
- Define a session record format that keeps requested commands, acknowledgments,
  observations, request/receipt timestamps, and failure reasons separate.
- Keep raw capture files usable and preserve current timestamp semantics.
- Handle connection/read timeouts, malformed/partial responses, and cleanup
  within the requested scope. Use bounded framing, request correlation and
  monotonic deadlines; enforce one process owning TCP control. Attempt standby
  independently of pan restoration or other cleanup failures.
- Preserve raw replies plus explicit validity, clipping and unknown-state flags.
  Load provisional camera alignment without representing it as measured pose.
  Associate logs with firmware, camera settings and calibration identifiers.
- Put command bounds in deterministic control code. Do not add continuous or
  autonomous motion as an incidental feature.
- Choose minimal dependencies only after need is established; installation is
  a separate authorized action. Do not reuse Python 3.12 native wheels in .venv.
- Discuss whether offline parser/encoding/error-path checks are authorized.
  Mocks and simulations are not implicitly authorized by permission to edit.

Suggested acceptance criteria for the explicitly authorized shared interface:
- Clear class responsibilities and documented inputs, outputs, units, bounds.
- Existing command semantics represented without unrequested firmware changes.
- Partial and malformed responses handled predictably where implemented.
- Session evidence distinguishes acknowledgments from physical measurements.
- File paths resolve from the intended project layout.
- No networking or motion occurs on import or ordinary offline verification.
- Any authorized checks are reported accurately, including untested hardware.

ROADMAP THROUGH THE PROJECT GOAL

These stages extend through AI-controlled exploration and a usable interior
reconstruction. They are a proposed sequence, not authorization to execute.
Each stage must be scoped with the user and evaluated against actual evidence.
Dependencies may require revisiting earlier stages; do not skip an unmet gate.

STAGE 0: DEFINE THE FINAL OUTCOME AND OPERATING AREA

Agree with the user on:
- The accessible surface and its boundaries, including prohibited areas.
- What counts as sufficient exploration coverage and when to stop exploring.
- What interior surfaces the reconstruction must represent; restrict claims to
  surfaces visible to the camera and reachable viewpoints.
- Whether the deliverable needs metric dimensions or only relative geometry.
- Required geometric accuracy, visual quality, tolerable gaps, and export format.
- The intended level of supervision and the authorized operating duration.

Inspect the existing source, calibration, and saved data to identify the evidence
already available. Do not infer numeric accuracy or coverage targets.
Completion gate: a defined target area, deliverable, and measurable criteria
accepted by the user. These choices remain open at the time of this handoff.

PREREQUISITE 0A: ESTABLISH PROJECT-SCOPED SANDBOX ACCESS

Choose a stable explicit command invocation for each rover entry point. Propose
the exact narrow prefix and project-local allow rule for review; configure only
when authorized. A module by itself is not an executable entry point. Do not
allow an unrestricted shell/interpreter merely to cover arbitrary future scripts.
Keep routine unrelated commands under the existing sandbox approval policy.

Completion gate: persistent rule location and matching invocation are verified
in this project, repeat execution no longer prompts for matching commands, and
unrelated invocations remain outside the grant. Rule checks/execution need their
own authorization. Rover-off permission checks cannot prove live TCP/HTTP access;
verify actual HTTP and control connectivity later with the rover on. Approval
readiness does not prove sensor correctness, stopping or movement authorization.

PREREQUISITE 0B: REVIEW AND CORRECT FIRMWARE/PROTOCOL FOUNDATIONS

1. Complete a focused source audit of sensor data types/conversion, no-echo and
   saturation semantics, acquisition blocking, IMU bias/timing, motor correction,
   serial framing/validation, timed expiry, standby and link-loss behavior.
2. Define what the host may rely on: units, raw/converted values, validity,
   acquisition age, command bounds, acknowledgment meaning and stop guarantees.
   Decide protocol compatibility/versioning before changing replies. Old scripts
   must not silently interpret an incompatible new reading.
3. Propose essential UNO corrections in the relevant driver/application files:
   preserve pulse width before conversion; represent invalid/clipped data; bound
   sensor acquisition and receive buffers; validate timed commands; make motor
   expiry independent of query/pan mode changes; define applied PWM bounds and
   stop priority; remove or bound operations that can starve stopping. Numeric
   precision alone does not prove sensor accuracy. Exact schema/time budgets
   remain design decisions.
4. Separate code corrections from physical calibration: coefficient accuracy,
   floor thresholds and motion response need measurements; do not invent them.
   Decide whether IMU corrections/telemetry are actually required for the pilot.
5. If authorized, edit, build and perform scoped offline checks. Preserve original
   backups; verify board/build settings, flash size margin and recovery procedure.
   Upload only within a separately defined hardware scope, record what was
   uploaded, and retain the earlier 1-degree pan behavior where requested.
6. Treat ESP32 changes as a separate decision. Establish build prerequisites and
   installed-firmware behavior/provenance before replacing the unproven camera
   source. No camera update is justified solely by source mismatch uncertainty.

Completion gate: required fixes and compatibility contract are explicit; any
chosen edits/builds are verified under their authorized scope. Physical validity
and stopping gates remain open until stage 2. A documented host workaround may
be used only where it handles uncertainty conservatively; it cannot recover raw
data or eliminate blocking already occurring on the rover.

STAGE 1: BUILD THE SHARED POWERSHELL ROVER INTERFACE

Use the shared-interface scope above: object-oriented command/capture/sensor
interface, single control-session ownership, deterministic action validation,
and session logging against prerequisite 0B's contract. Language is PowerShell;
integration scope and final files still require a concrete proposal. Preserve
existing entry points. Implement enough evidence logging before calibration
sessions to make the measurements reproducible. Keep firmware changes separate.

Completion gate: the requested interface and offline behavior are verified using
authorized checks, and its limitations are documented. It must not silently
initiate networking or motion during imports or offline checks.

STAGE 2: VERIFY LIVE CONTROL AND CALIBRATE SENSORS/MOTION

Within an explicitly authorized hardware session:
- Verify present camera, sensor, and control connectivity.
- Measure response latency and observation age under the actual setup.
- Exercise short wheel commands, servo commands, standby, and session closure
  within agreed bounds. Record requested commands and observed outcomes.
- Verify physical stop behavior and loss-of-control handling using a test
  procedure agreed with the user; do not treat firmware acknowledgments as proof.
- Establish which observations can detect obstacles, edges, or loss of tracking
  in the intended operating area, and which hazards remain unobserved.
- Start with stationary observation checks; only then perform bounded movement.
  Check no-echo/clipped readings, sensor-query latency, delayed or malformed
  responses, and their interaction with expiry/stop using an agreed procedure.
  Specifically verify expiry/stop while ultrasound, floor and pan commands are
  processed, after source-level hazards have been addressed. Do not use an
  uncorrected mixed-command drive as an incidental calibration experiment.
- Calibrate ultrasound against known distances and relevant targets/orientations;
  record error, repeatability, invalid cases and useful range. Verify whether its
  beam turns with camera pan before treating every range as straight ahead.
- Characterize floor ADC ranges/polarity under intended floors and lighting;
  verify any edge/leave-ground interpretation rather than assuming it is reliable.
- If battery or IMU data will be used, verify reference voltage, stationary bias,
  timing, drift, mounting axes and host telemetry availability as applicable.
- Characterize movement deadband, forward/backward asymmetry, turn response,
  coasting/braking, and dependence on floor/battery. Record requested PWM versus
  actual outcomes; timed PWM remains insufficient evidence for reliable odometry.

Completion gate: manual operations needed for the project produce usable records,
and measured results support the agreed operating envelope. Unsupported actions
remain unavailable to the autonomous planner.
Relevant sensor/motion calibration results, invalidity handling and measured
stopping limits must support that envelope; command acknowledgments do not.

STAGE 3: ESTABLISH CAMERA CALIBRATION AND DATA QUALITY

Determine what calibration the selected reconstruction method requires.
If authorized, acquire suitable calibration imagery and estimate camera
intrinsics and lens distortion. Establish image resolution, camera settings,
mounting stability, and usable pan behavior. Use measured quantities only when
the project actually needs them and there is an authorized way to obtain them.
Recheck provisional 100-degree forward alignment after reset or mounting changes.
Characterize permitted pan range, repeatability, backlash and settling; establish
camera-to-rover geometry/physical pan angle only when required. Keep commanded
angles distinct from measured pose and label absent position feedback explicitly.

Define a capture plan with overlapping viewpoints and translational motion.
Treat pan-only imagery as insufficient evidence for general depth recovery.
Assess blur, exposure variation, texture, occlusion, and frame consistency.
Record the calibration/settings used with each dataset.

Completion gate: a dataset and calibration appropriate to the selected method,
with known timing and image-quality limitations. If metric scale is required,
identify and verify an authorized scale reference or measurement source.
The pilot method and calibration requirements can be selected together; do not
wait until processing to discover the capture lacks the required geometry.

STAGE 4: PROVE OFFLINE RECONSTRUCTION ON A SMALL DATASET

Select a reconstruction approach after examining the actual data and the user's
deliverable criteria. Before installation or execution, obtain authorization
for dependencies and experiments. Existing captures may be useful for inspection
but should not be assumed sufficient for a full interior model.

For an authorized pilot dataset:
- Estimate camera poses and sparse geometry where supported.
- Produce denser geometry, mesh, and texture only as required by the deliverable.
- Compare results with input images and available reference measurements.
- Record gaps, outliers, uncertain regions, scale ambiguity, and processing cost.
- Preserve source images and distinguish raw data from derived artifacts.

Completion gate: an inspectable pilot reconstruction meets the agreed small-area
criteria. If it fails, correct capture/calibration or method selection before
building exploration around it. Do not promise metric accuracy without evidence.

STAGE 5: IMPLEMENT OBSERVATION AND STATE ESTIMATION

Build the runtime observation role around the available camera and sensors.
Choose pose estimation/localization and mapping methods supported by the pilot
results. Account for the absence of established motor encoders and servo feedback;
timed PWM commands alone do not measure traveled distance or camera pose.

Represent observation timestamps, pose confidence/uncertainty, obstacle evidence,
exploration coverage, and tracking loss explicitly. Decide how the system handles
drift and revisiting locations, and whether additional hardware is necessary.
Hardware additions remain proposals requiring the user's decision.

Completion gate: authorized validation demonstrates that state estimates are
usable within the chosen area, and stale observations or lost localization are
detectable. If evidence is inadequate, the next stage stays supervised or blocked
pending a defined improvement rather than assuming reliable localization.

STAGE 6: IMPLEMENT BOUNDED ACTION PLANNING AND CONTROL

Connect observation, planning, review, and the deterministic controller.
The planner selects bounded actions; the controller checks operating bounds,
command duration/PWM limits, observation freshness, and permitted action types.
Use explicit stop conditions for task completion, user interruption, connection
loss, insufficient evidence, and localization failure.

Plan movement and viewpoints for accessible-surface coverage and useful camera
overlap. Distinguish navigation coverage from visual coverage of the interior;
visiting a floor region does not establish that every interior surface was seen.
Define how the agent requests help when it cannot choose a supported action.

Completion gate: authorized offline checks and supervised short trials verify
planner/controller integration, bounded behavior, and failure handling within
the approved envelope. Simulation is an optional authorized activity, not proof
that physical rover behavior is correct.

STAGE 7: RUN SUPERVISED END-TO-END EXPLORATION TRIALS

Start in a small user-approved area with a defined duration and stop procedure.
Run observe -> estimate -> plan -> validate -> act -> review loops. Record every
action, acknowledgment, sensor result, capture, and termination reason.
Review progress against agreed coverage and reconstruction criteria.

Progressively expand trials only when authorized and supported by prior results.
Check recovery from tracking loss, insufficient texture, blocked routes, repeated
views, and connection interruptions where those tests are explicitly requested.
Do not expand the operating area automatically after a successful trial.

Completion gate: repeated authorized trials produce stable behavior and datasets
that support reconstruction. Remaining failure modes are documented and addressed
or accepted by the user before independent exploration.

STAGE 8: EXPLORE THE AGREED AREA AT THE APPROVED AUTONOMY LEVEL

Execute a defined session covering the target accessible surface and camera
viewpoints needed for the model. Keep operating boundaries and duration fixed
to the authorized scope. Monitor evidence quality and completeness during the
session; stop or request help when supported progress is no longer possible.

Finish using the authorized standby/disconnection procedure and preserve the
complete dataset. Record unreachable regions, unseen surfaces, and why the
session ended. Do not label an incomplete run complete solely because time ran out.

Completion gate: coverage criteria are met, or the user explicitly accepts a
documented reduced scope. Captured evidence is sufficient for the final processing
stage according to the proven method.

STAGE 9: BUILD AND VALIDATE THE FINAL INTERIOR RECONSTRUCTION

Process the final dataset with the validated pipeline. Apply pose refinement,
geometry cleanup, meshing, texturing, and scale alignment as required by the
agreed output. Keep raw captures and processing parameters available.

Validate against the stage-0 criteria:
- Visual correspondence to the camera imagery.
- Geometric consistency and reference measurements where available.
- Coverage of the agreed visible interior surfaces.
- Explicit representation or documentation of holes and uncertain regions.
- Correct scale claims and successful opening of the requested export format.

If criteria fail, identify whether additional viewpoints, calibration changes,
or processing changes are needed. Obtain authorization for those actions rather
than silently repeating a hardware session or accepting a lower-quality result.

Completion gate: the final model meets the agreed quality and coverage targets,
or deviations are explicitly accepted by the user.

STAGE 10: DELIVER THE COMPLETE SYSTEM AND PROJECT RESULT

Provide the working AI-control/exploration entry point, reproducible processing
procedure, final 3D artifact in the agreed format, session records, and concise
instructions for using them. Update README and workflow status when authorized
so implemented features are distinguishable from future proposals.

Report exactly what was verified, the operating conditions tested, and remaining
limits. Provide an authorized end-to-end demonstration if requested. Do not
delete intermediate evidence or backups as an incidental delivery cleanup.

THE PROJECT GOAL IS COMPLETE WHEN:
- The AI agent can operate the rover at the agreed autonomy/supervision level.
- It can explore the agreed accessible surface within defined operating bounds.
- Its captured data produces an inspectable 3D reconstruction of the agreed
  camera-visible interior surfaces meeting the accepted quality criteria.
- The user receives the model and usable, reproducible system with limitations
  accurately documented.

This roadmap does not assert that every stage is feasible with current hardware.
Feasibility and any required changes must be established through the staged
evidence gates rather than assumed at the outset.

DOCUMENTATION NOTES FOR THE NEXT CHAT

README was rewritten before .venv, AGENTS.md, and WORKFLOW.md were added. Its
root structure listing does not currently list those additions, and it has no
project .venv setup section. If the user requests documentation synchronization,
update those parts; no such additional edit is authorized by creating this
handoff. Do not call otherwise accepted files new cleanup problems.

Only handoff.txt was edited for this review. README and WORKFLOW were not changed;
WORKFLOW's interface-first summary is now less detailed than this revised order.
Use this handoff's prerequisite gates and latest accepted PowerShell decision
when resuming; synchronize other documentation only within an authorized scope.
No roadmap gate is marked complete by this documentation update. Immediate next
work is the concrete firmware/protocol correction proposal (prerequisite 0B),
with project-only permission configuration tracked independently as 0A.

AGENTS.md points to WORKFLOW.md and this handoff, and requires progress updates
here as authorized tasks finish. Keep it focused on agent instructions.
Detailed project facts belong in README or relevant info/config files; transient
session context belongs here. The latest user corrections take precedence over
any older snapshot or inferred preference.

OCTOBER 8, 2026: GIT INITIALIZATION AND ACCEPTED SEQUENCING
- User authorized git init in the existing hyohakusha project directory.
- git init succeeded, creating D:/projects/hyohakusha/.git/. No commit, remote, or .gitignore was created.
- User accepted non-overlapping drive -> stop -> sense/pan -> drive sequencing as the initial approach to the mode-change hazard. This restriction is not implemented or tested; it does not fix the underlying firmware defect.


- User authorized ignoring folders that can grow. Added .gitignore for .venv, Python caches, data, installed tools, vendor packages, hardware backups, firmware build output, and future root build/dist/logs/outputs/node_modules folders. Source, documentation, and calibration remain eligible for tracking. Git check-ignore confirmed the six existing bulk folder rules; git status showed only eligible project paths. No files deleted and no commit created.


- User authorized an initial commit and push to public GitHub repository c-earth/hyohakusha. Initial snapshot includes eligible project files under the established .gitignore. GitHub CLI is unavailable and the browser requires user sign-in; remote creation/push are pending. Commit author uses c-earth with existing configured email c_earth@mit.edu. No firmware/controller changes or hardware operations performed.


- Completed GitHub publication: created public https://github.com/c-earth/hyohakusha, configured origin, and pushed initial commit e13226e on main. Git reported successful new-branch publication and upstream tracking of origin/main. The earlier sign-in/remote/push pending note is resolved. Initial commit contains 39 files; ignored bulk folders remain local. This completion record is being committed separately to keep the published initial commit unchanged.

OCTOBER 8, 2026: EXACT EDITING INSTRUCTIONS
- User authorized updating the instruction file after clarifying that a requested
  edit whose stated condition does not match the file requires clarification.
- Added a rule under AGENTS.md Clarification: verify the requested target and
  condition, explain mismatches, and wait for an explicit answer before editing;
  do not reinterpret the request as a different change based on inferred intent.
- Verified the saved rule and this record by read-only inspection. No project
  code, tests, or hardware operations were run. No roadmap stage changed.


OCTOBER 8, 2026: RAW ULTRASOUND SOURCE CHANGE
- User authorized implementation of the discussed ultrasound plan: remove /58 and the 150 cm cap, use a host-supplied pulseIn timeout, report raw pulseIn output, leave existing thresholds/logic unchanged, and rename variables only when their names signify distance.
- Driver now accepts timeoutUs and writes the unsigned long pulseIn result directly. N21 requires integer T from 1 to 1,000,000 microseconds; invalid or missing T replies {H_error_timeout}. D1=2 reports raw microseconds, with zero indicating timeout.
- Raw storage and numeric formatting preserve the 32-bit result. Distance-signifying variables renamed; neutral ULTRASONIC_Get and tempda names retained. Unused millimeter member renamed UltrasoundPulse_unused without changing its type or adding behavior.
- Built-in obstacle/follow calls explicitly retain the prior 1,000,000 us timeout. Their numeric thresholds and branching remain unchanged and now consume raw microseconds. N21 D1=1 similarly retains its threshold of 20.
- Host Sensors action now sends T using UltrasoundTimeoutUs (default 30,000, permitted 1-1,000,000) and labels output ultrasound_us. README documents the source contract and deployment status.
- Verified by read-only source/caller inspection and git diff --check (no whitespace errors; existing AGENTS.md line-ending warning). No compiler, project script, test, upload, or hardware session executed. Source change is not deployment: installed UNO firmware still uses its prior contract; host labels are intended for the modified firmware after upload.
- No roadmap gate completed. Next sensor-review work remains floor sensors after user direction; build/offline execution and upload require their own authorization.

OCTOBER 8, 2026: REMOVE UNUSED ULTRASOUND MEMBER
- User explicitly requested removal of UltrasoundPulse_unused. Confirmed its only source occurrence was its declaration, then removed that declaration from ApplicationFunctionSet_xxx0.h.
- Read-only search after editing confirmed no occurrences remain; scoped diff inspection confirmed the deletion. No build, tests, or hardware operations performed.
- User asked why N21 handling cannot resemble the old direct call. Simplifying timeout validation placement remains discussion only; no command-handler change authorized or made in this step.

OCTOBER 8, 2026: HOST OWNS ULTRASOUND TIMEOUT VALIDATION
- User directed that the host handle timeout validation. Removed the N21 firmware validation/error block; the switch now directly calls CMD_UltrasoundModuleStatus_xxx0(doc["D1"], doc["T"]). No validation was moved into the handler.
- Updated README to reflect direct forwarding. This supersedes the earlier firmware 1-1,000,000 validation/error contract; that range remains in the existing PowerShell host parameter only.
- Verified the saved switch and README by read-only inspection and scoped git diff --check. No build, project execution, tests, or hardware operations performed.

OCTOBER 8, 2026: ULTRASOUND COMMIT AND PUSH
- User authorized commit and push. Commit e890746 contains the ultrasound changes, host request update, documentation, and pending exact-editing instruction change in AGENTS.md. Untracked .codex/ excluded.
- Push succeeded to origin/codex/sequential-rover-control with upstream tracking configured. No merge to main or firmware deployment performed. This publication record is committed separately.

OCTOBER 8, 2026: REMOVE AVOIDANCE AND FOLLOWING MODES
- User explicitly requested removal of obstacle-avoidance and following modes. Removed both application implementations/declarations, loop calls, enum entries, motor correction and LED cases, button and IR selection cases, and N101 D1=2/3 selection branches from active UNO source.
- Set Rocker_mode explicitly to 4 to preserve the numeric values of remaining enum entries. Other mode identifiers and command selectors were not renumbered. Removed button/IR cases fall through existing defaults; no new stop/error behavior added. N101 D1=2/3 no longer changes mode but retains the existing {ok} reply.
- Raw ultrasound driver and N21 host measurement/status paths remain. This supersedes earlier records that obstacle/follow modes remain in the modified source. Button counter cycle and IR decoding remain unchanged.
- Updated README with removal and source/deployment distinction. Verified full application diff, declarations and loop diff, remaining-reference search (no removed mode/function names remain in active UNO source), and scoped whitespace check. No build, tests, upload, commit, push, or hardware operations performed for this removal. Installed firmware has not changed.

OCTOBER 8, 2026: AVOIDANCE/FOLLOW REMOVAL PUBLICATION
- User authorized one commit and one push of the five changed files for this removal. This record is included in that same commit; no separate publication-record commit is planned. Publication result will be reported in chat after execution.

OCTOBER 8, 2026: REMOVE LINE TRACKING AND LEAVE-GROUND DETECTION
- User authorized removing line tracking and leave-ground detection, then confirmed removal after discussion of their IMU dependencies. Removed tracking mode/function/declaration/loop call, mode LED and direct-motor branches, button/IR selection and threshold adjustment, tracking statuses/thresholds, leave-ground function/flag/declarations, and N23/N101 handlers from active UNO source.
- Removed floor-triggered standby gyro calibration and the floor-triggered heading-reference reset condition. Standby stopping, startup gyro calibration, straight-driving gyro correction, and direction-change heading-reference resets remain. Other mode numeric values remain preserved by Rocker_mode=4.
- Kept raw floor drivers, loop-cached TrackingData_L/M/R, and N22 raw replies and programming-mode transition. No request-time reading conversion was implemented; the host-command-driven loop is an accepted future plan to implement one sensor at a time.
- Updated README. Verified application diff, searches showing no removed mode/flag/threshold/function/N23/N101 references in active UNO source, retained startup calibration/N22/raw cache paths, header/loop diffs and whitespace checks. No build, tests, upload, commit, push, or hardware operations performed. Installed firmware remains unchanged.

OCTOBER 8, 2026: N22 PRESERVES CURRENT MODE
- User explicitly requested removal of the programming-mode trigger after N22. Verified the assignment at the end of CMD_TraceModuleStatus_xxx0 and removed only that assignment. Cached raw readings and reply behavior remain unchanged.
- README now states N22 leaves the current mode unchanged. This supersedes earlier records that its programming-mode transition remains.
- Verified saved N22 handler and scoped whitespace check by read-only inspection. No build, tests, upload, commit, push, or hardware operations performed.

OCTOBER 8, 2026: REQUEST-TIME FLOOR SENSOR READS
- User explicitly authorized implementation of direct N22 readings and removal of the floor cache. N22 now calls the selected ITR20001 raw-read method before formatting its reply: D1=0 left, 1 middle, 2 right. Reply format and current-mode preservation remain unchanged.
- Removed the per-loop floor acquisition block and TrackingData_L/M/R members. Sensor initialization and raw driver methods remain; voltage update still runs through SensorDataUpdate and is outside this change.
- Updated README. Verified saved N22 branches, all active raw-read call sites, absence of TrackingData members, and scoped whitespace checks through read-only inspection. No build, tests, upload, commit, push, or hardware operations performed. Earlier cached-reading records are superseded; source changes have not been deployed.

OCTOBER 8, 2026: HOST BATTERY-VOLTAGE MEASUREMENT
- User authorized adding host-requested battery measurement and specified volts rather than raw ADC output. Added unused command N24 and CMD_VoltageMeasurement_xxx0 declaration/implementation. It takes a fresh reading through the existing voltage driver, formats three decimal places using dtostrf, and replies {H_value} without changing functional mode.
- Existing ADC*0.0375*1.08 conversion, periodic voltage sampling, low-voltage flag and LED warnings remain unchanged. Reported volts are an unverified estimate; displayed precision does not establish accuracy.
- Host Sensors action now includes battery_v via N24. Updated README with command, units, conversion and deployment limitation.
- Verified command dispatch, declaration/implementation, existing driver conversion, host request and documentation by read-only inspection; scoped whitespace checks passed. No builds, tests, script execution, uploads, commits, pushes or hardware operations performed. N24 requires deployment of the modified UNO firmware before use.

OCTOBER 8, 2026: HOST RAW THREE-AXIS GYRO READ
- User authorized host-read capability, selected all three axes and raw values. Added N25 with CMD_GyroMeasurement_xxx0 and a MPU6050_getRawRotation wrapper around the existing six-byte getRotation transaction. Tagged reply {H_x,y,z} contains signed sensor X/Y/Z raw counts.
- Host Sensors action includes gyro_raw_xyz. README documents units/order, deployment and validity limitations. Calibration, calibration accumulator, yaw integration, and motor correction remain unchanged; no recalibration command was implemented.
- Verified declarations, wrapper/call chain, N25 dispatch, buffer capacity for three signed 16-bit values, host parser compatibility with comma-separated payload, and whitespace checks by read-only source inspection. Underlying getRotation does not propagate I2C read success; host reply is not proof of valid physical measurement. No build, tests, uploads, commits, pushes, or hardware operations performed.

OCTOBER 8, 2026: HOST RAW THREE-AXIS ACCELEROMETER READ
- User authorized adding host accelerometer read. Following the raw three-axis gyro interface, added unused command N26 with CMD_AccelerationMeasurement_xxx0 and MPU6050_getRawAcceleration wrapper around existing getAcceleration. Reply {H_x,y,z} contains signed raw sensor X/Y/Z counts, including gravity, without conversion/calibration/mode changes.
- Host Sensors action includes accel_raw_xyz. Updated README. Existing gyro control and initialization ranges remain unchanged; no accelerometer-based control implemented.
- Verified driver availability, declarations/wrapper/dispatch, buffer capacity and host reply compatibility, and whitespace checks by source inspection. Underlying read success is not propagated; hardware readings/axes remain unverified. No build, tests, script execution, upload, commit, push, or hardware operations performed.

OCTOBER 8, 2026: REMOVE IR REMOTE HANDLING
- User explicitly requested removal of IR remote function. Removed ApplicationFunctionSet_IRrecv implementation/declaration/loop call, AppIRrecv object and initialization, DeviceDriverSet_IRrecv class and its driver implementations/receiver globals, IRremote include and remote-code constants from the device driver files.
- Bundled IRremote library source files remain; no library or vendor artifact deletion performed. Button handling and host commands remain unchanged. README documents source-only removal.
- Verified changed source boundaries, absence of IR handling references in application/device-driver/loop files, and scoped whitespace check through read-only inspection. No build, tests, uploads, commits, pushes or hardware operations performed.

OCTOBER 8, 2026: PAN-ONLY INCREMENTAL COMMAND; REMOVE N106
- User authorized adding incremental mode excluding Y and removing N106. Added unused command N27 with signed int16 degree step in D1, pan-only driver increment, and tagged acknowledgment after driver execution. Target uses shared encapsulated last commanded pan angle, clamped 10-170 degrees; starts at startup command 90 and updates on N5 pan writes. Wide intermediate avoids signed-add overflow. No measured position feedback introduced.
- N27 waits through existing 500 ms pan driver, detaches and enters programming mode; no Y output in its call path. N5 absolute interface and existing Y support/startup remain unchanged. Removed N106 dispatch, ApplicationFunctionSet_Servo helper/declaration, and unused ten-degree Servo_controls implementation/declaration.
- Host tool exposes PanStep with PanStepDegrees default 1, validated -170 to 170. README documents protocol, limits, state semantics and deployment status.
- Verified declarations, dispatch/call chain, state initialization/N5 synchronization, removal reference search and scoped whitespace checks by source inspection. No builds, tests, scripts, uploads, commits, pushes or hardware operations performed. Deployment and physical behavior remain unverified.

OCTOBER 8, 2026: REMOVE N1, N3 AND N110
- User explicitly requested removal of N1, N3 and N110. Removed dispatch branches, both overloads of direct-motor and untimed-car handlers, their declarations/loop calls, N1 fields, dedicated enum modes, N3 motor-correction case and N110 clear-to-programming execution branch.
- Preserved existing remaining enum values by explicitly assigning timed-car mode 10 and motor-speed mode 12. N2 and N100 remain, including N2 zero-duration behavior; N4 and N102 are unchanged. Programming mode remains for other command completion paths.
- Updated README. Verified removal references, retained N2/N100 paths, header/loop changes and whitespace checks by read-only source inspection. No builds, tests, uploads, commits, pushes or hardware operations performed.

OCTOBER 8, 2026: REMOVE N4 AND N102
- User explicitly requested removal of both N4 and N102. Removed command branches, both N4 handler overloads, rocker handler, declarations/loop calls, dedicated modes/state fields, rocker motor-correction and LED cases. Preserved remaining numeric mode values with explicit CMD_inspect=5 and CMD_ServoControl=13.
- N2 timed driving and N100 stopping remain; N2 T=0 expiry bypass remains unchanged. README documents removals. Historical vendor README.txt retains its original N102 history; not rewritten as active capability.
- Verified command-switch ending, remaining references in executable application/header/loop files, and whitespace checks through read-only inspection. No build, tests, uploads, commits, pushes, or hardware operations performed.

OCTOBER 8, 2026: DIRECT PWM DRIVING WITHOUT GYRO CORRECTION
- User explicitly confirmed removal of gyro correction from driving. Replaced forward/backward correction calls with direct same-PWM motor outputs. Removed the linear correction implementation/prototype, yaw target/direction history and gain/clamp setup from movement control.
- Turning and stop driver paths remain unchanged. Requested uint8 PWM is now passed directly for forward/backward, without the former correction clamp of 10-180. N2 timing and T=0 behavior unchanged.
- Host gyro/accelerometer commands, startup gyro initialization/calibration, and unused library yaw integration method remain. No gyro I2C call remains in driving; startup calibration is not removed.
- Updated README. Verified direct motor calls, absence of correction references in application source, retained measurement/startup calls and whitespace check by read-only inspection. No build, tests, uploads, commits, pushes, or hardware operations performed.

OCTOBER 8, 2026: REMOVE HOST LED COMMANDS
- User requested removal of all discussed host LED commands N7/N8/N105. Removed their dispatch, lighting helper and handler implementations/overloads, declarations/loop calls, lighting modes/timer/color fields and host brightness state.
- Preserved automatic battery warning and standby LED behavior per earlier skip decision. LED initialization, low-level driver, N100 LED clear remain unchanged. Updated README.
- Verified source boundaries, absence of removed host-lighting references, retained RGB/battery paths and whitespace checks through read-only inspection. No build, tests, uploads, commits, pushes, or hardware operations performed.

CURRENT RESUME SUMMARY: OCTOBER 8, 2026
- Latest request: update this handoff, commit and push pending changes. Keep one commit including this record and one push; report publication outcome in chat without creating a second record commit. Current branch codex/sequential-rover-control, origin https://github.com/c-earth/hyohakusha.git. Untracked .codex/ is excluded.
- Pending source changes since 6df654a: remove line tracking/leave-ground and their floor-triggered IMU behavior; N22 fresh selected raw read, no mode change; N24 estimated battery volts; N25 raw gyro XYZ; N26 raw accelerometer XYZ; N27 signed pan-only degree increments synchronized with N5 command state; remove IR handling/N106/N1/N3/N110/N4/N102/N7/N8/N105; replace driving gyro correction with direct requested PWM. Details and evidence recorded above.
- Remaining host commands: N2 timed direct-PWM drive, N5 absolute servo, N21 ultrasound, N22 floor, N24 battery, N25 gyro, N26 accelerometer, N27 incremental pan, N100 stop-to-standby. N21 D1=1 still interprets raw pulse against unchanged threshold 20; D1=2 returns raw microseconds with host-supplied T. N2 T is milliseconds; T=0 expiry bypass remains. N5 includes existing Y support, while N27 commands only pan.
- Actual loop: watchdog refresh -> periodic battery sampling -> button handling -> automatic LEDs -> standby stop -> serial command dispatch -> pending N5 servo -> N2 drive/expiry -> N100 clear/stop. Sensors and N27 execute synchronously within dispatch. Automatic battery/LED and button behavior were explicitly skipped for removal. Startup gyro calibration and servo positioning remain.
- Accepted direction: progressively move toward host-command-driven firmware, reviewing one sensor/function at a time. Do not implement the entire loop redesign based on that plan alone. User requested step-by-step loop explanation, heard watchdog step, then redirected to this handoff/commit/push task. Resume discussion from the requested point, not an assumed authorization for more changes.
- Gyro recalibration command and accumulator reset were discussed but not implemented. Current calibration still averages Z only, and its repeated-call accumulator defect remains. Raw gyro/accelerometer replies perform no calibration or unit conversion. Camera and onboard button remain unchanged by user choice.
- Verification to date: focused read-only source/caller inspection, reference searches, reply/buffer reasoning, and git diff --check. No compilation, project scripts/tests, simulations, hardware readings, rover movement, or firmware upload performed for these changes. Nothing here establishes deployed behavior or physical stopping. All roadmap completion gates remain open.
- Before compilation/upload, obtain explicit execution/hardware scope. Preserve firmware backups; confirm target settings and report compiler results rather than assuming build success. No dependency installation authorized. Do not add cleanup/refactoring as incidental next work.

OCTOBER 8, 2026: REMOVE ONBOARD BUTTON HANDLING
- User explicitly selected button removal after clarification of the loop discussion. Removed the button loop call, application handler/declaration, object/initialization, driver class/methods, interrupt callback/registration, and button constants from active UNO source.
- Standby motor stopping, N100, watchdog, battery monitoring and automatic LEDs remain. Earlier records that button behavior remains are superseded by this removal.
- Updated README with source/deployment distinction. Verified the complete removal diff and reference search in active application/device-driver/loop source; no removed button references remain. No compilation, tests, scripts, upload, hardware operations, commit or push performed. Installed firmware is unchanged.

OCTOBER 8, 2026: REMOVE AUTOMATIC BATTERY AND LED LOOP STEPS
- User explicitly requested removal of the battery step and automatic LED step. Removed SensorDataUpdate and RGB loop calls, implementations/declarations, cached voltage, low-battery flag and threshold. Removed warning/breathing animation and its delays.
- N24 fresh estimated voltage readings, voltage driver/initialization, LED driver/initialization and N100 LED clearing remain. Standby motor stopping remains. Earlier automatic battery/LED preservation decisions are superseded.
- Current loop: watchdog refresh -> standby stop -> serial dispatch -> pending N5 servo -> N2 drive/expiry -> N100 clear/stop.
- Updated README. Verified scoped source diff, removed-reference search, retained N24/LED-clear paths and whitespace check by read-only inspection. No build, tests, project script execution, upload, hardware operation, commit or push performed; installed firmware is unchanged.

OCTOBER 8, 2026: REMOVE STANDBY LOOP STEP
- User explicitly requested removal of the discussed standby step. Removed ApplicationFunctionSet_Standby implementation/declaration and loop call. Standby mode/startup assignments remain; they no longer cause a repeated motor-stop output through this function. N100 explicit motor stopping and N2 expiry stopping remain unchanged.
- Current loop: watchdog refresh -> serial dispatch -> pending N5 servo -> N2 drive/expiry -> N100 clear/stop. Updated README; this supersedes earlier records that the standby loop stop remains.
- Verified removed-reference search, source diff, retained N100/N2 stop calls and whitespace check by read-only inspection. No compilation, tests, project scripts, upload, hardware operation, commit or push performed. Installed firmware is unchanged; startup physical behavior after this removal is unverified.

OCTOBER 8, 2026: REMOVE LED ACTIONS FROM N100 ONLY
- User explicitly requested removing LED behavior from this step, focusing on stopping. Removed FastLED.clear and the black LED driver call from CMD_ClearAllFunctions_xxx0 only. Motor stop, stored motion reset and standby selection remain unchanged. LED initialization/driver are outside this change.
- Updated README; prior records that N100 clears LEDs are superseded. Verified saved handler and whitespace check through read-only inspection. No build, tests, project scripts, upload, hardware operation, commit or push performed.

OCTOBER 8, 2026: RENUMBER REMAINING HOST COMMANDS
- User specified sequential order battery, gyro, accelerometer, drive, stop, absolute servo, incremental pan, ultrasound, floor. New IDs respectively N1-N9. Updated UNO dispatch/protocol comments, both host scripts and README. Payloads and handler behavior remain unchanged.
- Retained N100 as a stop compatibility alias because the unchanged camera source emits N100 on disconnect/heartbeat termination. Installed camera firmware has not been verified against that source. Other old IDs are not aliases. Previous records use historical numbering.
- Verification: read-only dispatch/caller/diff inspection and whitespace check. No build, tests, scripts, upload, hardware session, commit or push performed. Updated scripts require updated UNO firmware; numbering is not deployed.

OCTOBER 8, 2026: KEEP STOP AT N100; SHIFT FOLLOWING COMMANDS
- User requested moving stop to N100 and shifting the remaining commands up. Final mapping: N1 battery, N2 gyro, N3 accelerometer, N4 drive, N5 absolute servo, N6 incremental pan, N7 ultrasound, N8 floor, N100 stop.
- Updated UNO dispatch/comments, host scripts and README. Removed the intermediate stop alias branch; N100 is now the sole stop command and matches the unchanged camera source. Previous sequential N1-N9 mapping is superseded. No Git publication requested by this numbering instruction.
- Verified dispatch/caller consistency, saved documentation and whitespace through read-only inspection. No build, tests, project scripts, upload, hardware operation, commit or push performed. Updated scripts still require updated UNO firmware.

OCTOBER 8, 2026: UNUSED-CODE REVIEW TAGS AND EULER PRESERVATION
- User has tagged for later removal: ApplicationFunctionSet_Bootup, CMD_inspect_xxx0 and its mode entry, parameterized CMD_CarControlTimeLimit_xxx0 overload, DeviceDriverSet_Servo_control, and MPU6050_dveGetEulerAngles. These tags do not remove active source.
- User explicitly requested preserving the raw Euler/yaw function in a separate project Markdown file. Created euler.md with the exact current function body, source provenance and pending-removal status. Verified saved code matches the source by read-only comparison. No firmware edits, builds, tests, uploads or hardware operations in this review task.
- Next review item: unused ApplicationFunctionSet_Expression declaration, then other unused declarations, retained LED/test/library code and startup-only behavior.

OCTOBER 8, 2026: REMOVE ALL REVIEW-TAGGED UNUSED CODE
- User explicitly authorized removal of all tagged items. Removed Bootup and inspect functions/declarations and inspect enum entry, unused parameterized timed-drive overload/declaration, unused legacy servo-control method/declaration, yaw integration function/declaration, five unimplemented declarations, all six disabled driver test bodies/declarations, and IRremote.cpp/IRremote.h/IRremoteInt.h from active UNO source only.
- Preserved remaining mode numeric values by explicitly assigning programming mode 6. euler.md still preserves the exact removed yaw function. Vendor/backup IR copies remain. Untagged LED initialization/driver, application delay helper, startup gyro calibration and related state remain unchanged.
- Updated README. Verification limited to source diff/reference searches, preserved Euler comparison and whitespace check. No compilation, tests, project scripts, upload, hardware operation, commit or push performed. Installed firmware unchanged.

OCTOBER 8, 2026: COMMIT AND PUSH AUTHORIZATION
- User explicitly requested commit and push of completed pending changes. Publication scope: firmware loop simplification, final command numbering, tagged unused-code removal, host scripts, README, this handoff and euler.md. Untracked .codex/ excluded.
- Read-only pre-publication checks: current branch codex/sequential-rover-control; origin https://github.com/c-earth/hyohakusha.git; whitespace check passed. No build/upload verification added. Publication outcome will be reported in chat without a separate record commit.

OCTOBER 8, 2026: BUILD AND REPLACE SAVED UNO ARTIFACTS
- User requested firmware build, size comparison and replacement, then clarified replacement means saved build files only. Compiled current UNO source using local Arduino CLI, arduino:avr:uno and AVR core 1.8.8. Initial sandbox build failed to launch avr-g++ with a Windows DLL relocation error; approved execution outside the sandbox succeeded.
- Compiler reports 20,416 bytes program storage (63% of 32,256) and 794 bytes global RAM (38% of 2,048), leaving 1,254 bytes for stack/local variables. Counted Intel HEX data records: older active application 31,068 bytes, new application 20,416 bytes; reduction 10,652 bytes (34.29%). This compares application payloads, not the full original flash readback containing bootloader.
- Replaced rover/firmware/build/uno/flash.hex and eeprom.hex from compiler outputs. SHA-256 comparisons confirm both saved files match outputs. EEPROM output contains only the EOF record, with no EEPROM data. Original hardware backups remain unchanged.
- Current source changes are now built; prior not-built statements are historical. No upload, hardware operation or runtime test performed; installed UNO remains unchanged and host scripts still require deployment. Next applicable work is explicitly authorized upload and physical verification; no roadmap stage completed by this offline build.

OCTOBER 8, 2026: UNO USB UPLOAD
- User confirmed USB connection and explicitly authorized serial-port identification and UNO upload. Arduino CLI listed only COM3; Windows identified USB-SERIAL CH340, VID_1A86/PID_7523. The adapter itself did not identify the board model.
- Uploaded saved rover/firmware/build/uno/flash.hex using arduino:avr:uno, COM3 and --verify. Initial sandbox serial access was denied; approved execution outside the sandbox succeeded. Avrdude accepted device signature 1E 95 0F for the ATmega328P target, wrote 20,416 flash bytes, read them back and verified all 20,416 bytes; exit code 0.
- Current UNO application is now uploaded and flash-verified. Earlier undeployed statements are superseded by this record. EEPROM and camera firmware were not written. No sensor requests, commanded servo/motor checks or physical behavior verification performed. Next applicable work is separately authorized runtime protocol and physical stopping verification; roadmap safety gates remain open.

OCTOBER 8, 2026: WIFI SENSOR RESPONSE CHECK
- User confirmed Wi-Fi connection and explicitly authorized five sensor response checks, including control connection open/close and the documented camera stop-on-disconnect behavior. Ran pwsh -NoProfile -File ./src/tools/rover.ps1 -Action Sensors. Sandbox socket access was blocked; approved execution outside the sandbox succeeded with exit code 0.
- Received ultrasound_us=10817 (30,000 us requested timeout); floor_left=297, floor_middle=708, floor_right=526 (raw ADC); battery_v=8.667 (existing unverified conversion); gyro_raw_xyz=-372,60,228; accel_raw_xyz=48,52,15388 (signed raw counts).
- All seven tagged replies across five sensor categories were received using the updated command numbering. This verifies protocol responses, not sensor accuracy, mounting axes, calibration or physical stopping on disconnect. No servo or driving commands were issued. Next applicable work is separately authorized servo and bounded driving/stopping verification; physical safety gates remain open.

OCTOBER 8, 2026: FIVE-DEGREE ABSOLUTE PAN TEST
- User explicitly authorized 100 -> 105 -> 100 degree servo commands with three saved images. Executed existing FinePanTest logic with its 101-degree target changed to 105 only in memory; no controller source files changed. Sandbox socket access was blocked; approved execution outside the sandbox succeeded, exit code 0.
- All three N5 commands returned ok. Captured center.jpg, pan.jpg and return.jpg under data/captures/20261008223235046, with info.txt recording the sequence. Inspected all three images: scene features shifted right at the 105-degree command, consistent with camera pan left, and returned approximately to the initial framing at 100. This establishes visible pan and approximate return, not a measured five-degree physical rotation or exact repeatability.
- Existing test finally path sent a further 100-degree restore command and N100 stop; restore was not separately acknowledged. No driving commands issued. N6 incremental pan remains untested. Physical driving and stopping verification remains pending separate authorization.

OCTOBER 8, 2026: N6 INCREMENTAL PAN CHECK
- User explicitly authorized N6 +5 then -5 degrees with images. Reused existing pan-test connection, heartbeat and capture logic with in-memory changes only: N6 zero-step reference, +5, -5; no controller source edits. Initial sandbox socket attempt failed; approved execution outside the sandbox succeeded, exit code 0.
- All three N6 requests returned ok. Saved center.jpg, pan.jpg, return.jpg and sequence info.txt under data/captures/20261008223409165. Inspected all images: scene features shifted right after +5, consistent with camera turning left; -5 returned approximately to reference framing. Actual physical angle and exact repeatability were not measured.
- Retained finally path sent N5 absolute 100-degree restore and N100, with no separate restore acknowledgment. Return image was captured after N6 -5 and before this final restore. No driving commands issued. N6 response and visible bidirectional pan are now verified for these steps; bounded driving and physical stopping remain unverified and require separate authorization.

OCTOBER 8, 2026: FIRST BOUNDED FORWARD COMMAND
- User confirmed clear, flat floor and explicitly authorized forward PWM 60 for 200 ms followed by N100, with user observation of movement/stopping. Ran rover.ps1 -Action Move -Direction Forward -DurationMs 200 -Speed 60 -EnableMovement. Sandbox connection failed before commands; approved execution outside the sandbox succeeded, exit code 0.
- Script reports timed movement and standby commands sent: N4 forward (D1=3), PWM 60, T=200 ms, then N100 after a 300 ms host wait. Connection disposed. No command acknowledgment or physical observation collected by this script; successful send does not verify forward motion, expiry stopping or N100 stopping. Await user observation before further movement. This one trial does not independently distinguish timed expiry, explicit stop and disconnect stop.

OCTOBER 8, 2026: FORWARD OBSERVATION AND BOUNDED REVERSE COMMAND
- User reported yes when asked whether the preceding forward trial moved forward briefly and stopped. This is user-observed physical behavior; stopping time was not measured and its cause (expiry, N100 or disconnect) was not isolated.
- User confirmed space behind the rover clear and explicitly authorized backward PWM 60 for 200 ms followed by N100. Ran rover.ps1 -Action Move -Direction Backward -DurationMs 200 -Speed 60 -EnableMovement. Initial sandbox connection failed before commands; approved execution outside the sandbox succeeded, exit code 0.
- Script reports commands sent: N4 backward (D1=4), PWM 60, T=200 ms, then N100 after a 300 ms host wait, followed by connection disposal. No acknowledgment or physical observation obtained by the script. Await user observation of reverse movement and stopping; no further movement authorized by this trial.
- User subsequently confirmed that the rover reversed briefly and stopped. Forward and backward behavior are now user-observed for these individual PWM 60 / 200 ms trials. Stop timing and whether expiry, N100 or disconnect caused the stop remain unverified; turning and isolated stopping checks remain pending.

OCTOBER 8, 2026: COMBINED LEFT AND RIGHT TURN CHECK
- User requested checking remaining turns together, confirmed surrounding floor clear and explicitly authorized left and right turns, each PWM 60 / 200 ms followed by N100, with a pause between. Executed existing Move action for Left, waited three seconds, then executed Right. Each action owns and closes its TCP connection sequentially; no concurrent controllers.
- Initial sandbox connection failed before movement; approved execution outside the sandbox succeeded, exit code 0. Both actions reported timed movement and standby commands sent. These sends do not establish physical direction, stopping time or stop cause. Await user observation of both turns and stops. No additional movement or isolated stopping test authorized.
- User subsequently confirmed both turns were in the correct direction and stopped after each. All four driving directions now have user-observed movement and stopping for PWM 60 / 200 ms trials. Stop latency was not measured, and timed expiry, N100 and disconnect stopping were not isolated. These trials do not complete broader physical stopping/safety verification.

OCTOBER 8, 2026: TIMED-STOP OBSERVATION
- User explicitly authorized forward PWM 60 / 200 ms, holding the TCP connection open for two seconds before N100. Ran existing Move logic with an in-memory replacement of its usual 300 ms wait: sent heartbeats every approximately 100 ms for two seconds, then N100 and disposed the connection. No controller source changes.
- Initial sandbox socket access failed before commands; approved execution outside the sandbox succeeded, exit code 0. User reported 'Before' in response to observing whether the rover stopped before the two-second interval ended. This supports user-observed stopping before the scheduled explicit N100/disconnect in this trial, consistent with timed expiry. Exact stop latency and continuous connection health were not independently measured. Explicit N100 early-stop and disconnect stopping remain unisolated; no additional movement authorized.

OCTOBER 8, 2026: EARLY N100 STOP CHECK
- User requested a one-second timer for clarity, confirmed clear floor and explicitly authorized forward PWM 60 / T=1000 ms, N100 after a 100 ms host wait, then two seconds with the connection open. Executed existing Move logic with in-memory duration validation widened to 1000 for this single test, a 100 ms pre-stop wait, and two seconds of approximately 100 ms heartbeats after N100. Saved script and its 500 ms limit remain unchanged.
- Initial sandbox socket attempt failed before commands; approved execution outside the sandbox succeeded, exit code 0. Output confirmed the planned command sequence was sent. User reported 'before' when observing whether stopping occurred before the one-second timer ended. This supports user-observed early stopping consistent with N100 while the host kept the connection open. Exact stop latency, reception timing and continuous connection health were not measured independently.
- Timed stopping and early explicit N100 stopping now have separate user-observed trials. Disconnect/heartbeat-loss stopping remains unisolated. No further movement authorized by this test.

OCTOBER 8, 2026: PAIRED TIMER AND TCP-DISCONNECT TRIALS
- Earlier standalone disconnect trial did not run: sandbox socket access failed before commands, and the outside-sandbox permission request was rejected. User then explicitly requested a one-second trial without cutting followed by another one-second trial with cutting, within the previously confirmed clear-floor scope.
- Executed two forward PWM 60 / T=1000 ms trials with approved outside-sandbox access. Trial 1 held TCP open for two seconds with approximately 100 ms heartbeats; then closed it. After a three-second pause, trial 2 closed TCP following a 100 ms host wait. Neither trial sent host N100. Only in-memory test variants were used; saved controller duration limit remains 500 ms.
- Execution succeeded, exit code 0, and reported both sequences sent. Await user comparison of movement duration and stopping in each trial. Sends do not independently establish physical behavior, exact timing or camera-generated stop commands. Abrupt network failure and heartbeat loss were not tested.
- User confirmed the second trial stopped short compared with the first. This supports user-observed early stopping on graceful TCP close in this comparison. Exact latency and the camera's internal stop message were not measured. Abrupt Wi-Fi failure and heartbeat-loss stopping remain unverified.

OCTOBER 8, 2026: STATIONARY HEARTBEAT TIMEOUT MEASUREMENT
- Withdrew proposed one-second driving heartbeat test after inspecting camera reference source: four missed approximately one-second heartbeat checks precede disconnect, so a one-second drive would expire first. No driving trial executed for that proposal.
- User explicitly authorized opening TCP without driving or host heartbeats, observing closure for up to six seconds. Initial sandbox socket access failed; approved outside-sandbox execution succeeded. Host sent zero bytes. Received four {Heartbeat} messages and detected peer EOF after 3,029 ms from connection establishment in this single trial; exit code 0.
- This verifies peer closure without host heartbeats in the installed camera for this trial. It does not measure physical stopping, prove internal N100 transmission, or establish an invariant timeout across connections. No driving command sent. Physical heartbeat-loss stopping remains unverified; a movement test would need a separately authorized duration longer than the observed timeout or another defined bounded method.

OCTOBER 8, 2026: PHYSICAL HEARTBEAT-LOSS STOP TRIAL
- User confirmed clear flat space for up to five seconds of travel and explicitly authorized forward PWM 60 / T=5000 ms, no host heartbeats, observing whether stopping occurred around three seconds before timer expiry. Sent one N4 command and monitored peer closure for up to six seconds. No host N100 sent; no saved controller changes or duration-limit changes.
- Initial sandbox socket connection failed before commands; approved outside-sandbox execution succeeded, exit code 0. Received four camera heartbeat messages; peer EOF occurred 3,025 ms after starting the command-send timer. Host heartbeat count and host N100 count were both zero.
- User reported the rover stopped around three seconds. This supports physical heartbeat-loss stopping before the five-second drive expiry in this trial, alongside measured peer closure. Physical stop latency was estimated by the user, not instrumented; camera-generated N100 was not directly observed. Abrupt Wi-Fi loss, repeated reliability and other speeds/surfaces remain unverified. No additional movement authorized.

OCTOBER 8, 2026: STATIONARY NINE-VIEW CAMERA SWEEP
- User skipped the proposed keyboard-controller checks; they remain unperformed. User explicitly authorized stationary camera capture at 80,85,90,95,100,105,110,115,120 degrees then return to 100, with no wheel commands.
- Used existing pan/capture logic with in-memory sequence changes only. Initial sandbox connection failed before commands; approved outside-sandbox execution succeeded, exit code 0. All nine N5 commands returned ok. Saved nine JPEGs named pan080.jpg through pan120.jpg and info.txt under data/captures/20261008225316209. Confirmed all nine files exist with nonzero sizes; visually inspected 80,100,120 views, showing overlapping room content and changing framing.
- Finally path sent N5 restore 100 and N100; restore was not separately acknowledged or captured. No driving commands sent. No capture timestamps or measured poses/intrinsics were added. This is a stationary pan dataset, not validated 3D reconstruction input: no deliberate translational baseline was captured, and sufficient depth parallax is not established. Reconstruction processing, calibration and further capture remain separately authorized work.

OCTOBER 8, 2026: BEFORE/AFTER FORWARD CAPTURE PAIR
- User confirmed clear floor and explicitly authorized an image at the current position, forward PWM 60 / 200 ms, N100, then another image. Used existing capture/connection logic with in-memory changes only. Commanded pan 100 before each image; both N5 commands returned ok. Sent N4 forward T=200, waited 300 ms, sent N100, then waited 400 ms with heartbeats before the after-image servo/capture sequence. Finally sent N5 100 restore and N100.
- Initial sandbox connection failed before commands; approved outside-sandbox execution succeeded, exit code 0. Saved before.jpg, after.jpg and sequence info.txt under data/captures/20261008225505941. Viewed both images: substantial scene overlap with a visible framing change. No measured travel distance, physical camera pose, calibrated intrinsics, exposure timestamps or quantified parallax. Physical movement/stopping for this particular capture trial was not separately reported by user.
- This pair is captured for subsequent offline correspondence/parallax assessment; no reconstruction or image-analysis code executed and sufficient reconstruction geometry is not established. Next work should assess saved data before additional rover capture; processing implementation/execution needs explicit scope.

OCTOBER 8, 2026: N1-N8 AUTOMATIC OPERATION TEST
- User explicitly requested all eight rover operations, pictures to check drive response, and evaluation of execution without permission requests. Interpreted eight operations as current N1-N8 command map; included all four N4 directions and final N100 cleanup. Used existing src/tools/rover.ps1 unchanged, sequentially with one TCP owner. All executions returned exit code 0, without permission prompts or escalation requests. This verifies prompt-free execution for these commands in this session only.
- Sensors: N1 battery 8.343 V (firmware estimate); N2 gyro -339,53,245 raw counts; N3 accelerometer 40,-12,15220 raw counts; N7 ultrasound 12308 us; N8 floor left/middle/right 498/514/436 ADC. Replies verify communication, not accuracy or calibration.
- N5 PanTest 90 -> 100 -> 90 returned ok at each step. Images center/pan/return in data/captures/20261008231714783 visually show leftward pan and approximate return. N6 +5 then -5 each acknowledged; images 20261008231727222 and 20261008231738585 show corresponding shift and approximate return. Last pan command reference 90; actual physical angle unmeasured.
- Initial image: data/captures/20261008231705573/frame-000000.jpg. After pan restoration, drive baseline is 20261008231738585/frame-000000.jpg. Four N4 tests used PWM 60 / T=200 ms, each followed by the tool's N100 after its 300 ms host wait and TCP disposal. Post-forward capture: 20261008231751421; post-backward: 20261008231801683; post-left: 20261008231811710; post-right: 20261008231822771. All image directories contain frame-000000.jpg; last also contains frame-000001.jpg. Record actions saved info.txt and UTC request/receipt manifests. Visually inspected every captured image.
- Left/right produced clear opposite scene shifts consistent with turns. Forward/backward produced small framing changes, insufficient to conclusively verify translation from these pictures. Final two images appeared stable; separate final Stop action sent N100 and disposed TCP. Neither exact stopping latency nor which stop mechanism acted was isolated. No distances, physical turn angles, repeated reliability, drive calibration, reconstruction, new controller implementation or dependency installation tested. No continuing movement authorization remains from this completed request.

OCTOBER 8, 2026: IMAGE-ANALYSIS TOOL ASSESSMENT

Folder-name follow-up: user selected sessions/ for renaming and accepted logs/.
Renamed data/sessions to data/logs after verifying the source and absent target.
The retained live-sequential-check/events.jsonl had matching SHA256 before/after.
No active source/documentation references to data/sessions were found in the
focused search (vendor/tools and historical journal excluded). No rover execution.
Session-timestamp grouping and capture-script changes were not performed at that point.
- User requested the next agenda step, following a list beginning with tool assessment and distinguishing installation/execution scope. Completed read-only project inspection and official documentation review; no Python, installation, analysis program or rover operation executed.
- Re-read .venv/pyvenv.cfg: Python 3.13.13, system packages disabled. Top-level site-packages name inspection found no cv2, opencv, numpy, PIL, pillow, open3d or torch entries. This is filesystem evidence, not an import test. camera.json contains provisional pan alignment, not camera intrinsics.
- Recommend OpenCV + NumPy for an offline component, retaining PowerShell control. First proposed validation: read existing drive, pan and stationary JPEGs; produce feature-correspondence/optical-flow overlays and pixel-motion summaries with rejected-match counts and consistency checks. Treat rotation, exposure changes and near-zero motion as limitations; do not equate image displacement with metric travel or use it alone to prove translation. Installation and implementation/execution remain separately scoped work.
- Official OpenCV optical-flow and calibration documentation: https://docs.opencv.org/4.13.0/d4/dee/tutorial_optical_flow.html and https://docs.opencv.org/4.13.0/dc/dbb/tutorial_py_calibration.html . Camera calibration needs known target geometry and multiple views. Relative pose documentation https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html does not establish metric scale from unscaled two-view translation.
- Official package metadata https://pypi.org/project/opencv-python/ lists Python 3.13 and Windows wheels; local installation compatibility remains unverified. Version choice/dependency resolution should be checked during authorized installation rather than inferred from metadata alone.
- COLMAP https://colmap.github.io/tutorial.html supports later SfM/MVS; its capture guidance calls for changing camera location rather than only rotating. Defer until translated coverage is adequate. Open3D RGB-D integration https://www.open3d.org/docs/release/tutorial/pipelines/rgbd_integration.html requires RGB-D inputs; no depth camera/data established here. No reconstruction capability verified locally.

OCTOBER 8, 2026: DATA SESSION RESTRUCTURING

Follow-up configuration: user requested a pip-install approval prefix. Added
.codex/rules/pip.rules with pattern [.venv\Scripts\python.exe, -m, pip, install]
and allow decision, following existing project rule syntax and official rules
documentation. Read-back checked; no package installation or runtime rule test.
Recorded user directions to put new code under src/agent/ and track promotion
candidates in handoff. Current-session rule loading remains unverified.
- User explicitly approved moving all existing data into a previous-chat timestamp setup group and updating capture handling for future chat sessions. Prior chat metadata reports "Build and replace firmware", createdAt 1791511260; converted to New York session folder 20261008220100000. All existing captures (including this chat's tests) and logs moved under data/20261008220100000/, with root info.txt containing setup. Historical paths above are superseded by this added prefix; original relative captures/logs paths remain intact.
- Checked resolved absolute move sources within D:\projects\hyohakusha\data and absent destination. Computed SHA256 for all 74 existing files before moving and compared against their relocated counterparts: all matched. Verified final count 75 including new session info.txt. Hashes were verification values only; no checksum manifest or renamed files introduced.
- src/tools/rover.ps1 now takes SessionTimestamp and ChatName for Record/PanTest/FinePanTest. CaptureSession class validates session date/name, stores chat name in root info.txt, rejects existing missing/conflicting metadata, and creates capture timestamp subfolders. Session validation precedes TCP connection. Other operations retain their existing parameters. Caller supplies chat metadata; script cannot discover it automatically. Logs are preserved but no new runtime control logging was implemented.
- README layout, capture examples and metadata instructions updated; handoff current locations updated. Verification limited to source/documentation read-back and actual move hashes/count; no project runtime tests or rover execution authorized/performed in this restructuring step.

OCTOBER 8, 2026: VISUAL ANALYSIS PACKAGE INSTALLATION
- User explicitly requested "install useful visual analysis packages". Scope was dependency installation into the project .venv; no analysis implementation, runtime testing or rover operation was authorized or performed.
- Read project instructions, README, handoff, WORKFLOW and .venv/pyvenv.cfg. Official OpenCV and scikit-image package metadata informed selection; pip resolved compatible Windows binary wheels for the Python 3.13 environment.
- Ran .venv\Scripts\python.exe -m pip install --only-binary=:all: opencv-python numpy Pillow scipy scikit-image matplotlib. Exit code 0; pip reported successful installation without permission prompts.
- Primary packages: opencv-python 5.0.0.93, numpy 2.5.3, Pillow 12.3.0, scipy 1.18.1, scikit-image 0.26.0, matplotlib 3.11.2.
- Additional installed dependencies: contourpy 1.4.0, cycler 0.12.1, fonttools 4.66.1, imageio 2.38.1, kiwisolver 1.5.1, lazy-loader 0.6, networkx 3.7, packaging 26.3, pyparsing 3.3.3, python-dateutil 2.9.0.post0, six 1.17.0, tifffile 2026.9.20.
- Verification is limited to pip's success report and resolved wheel tags; imports and actual image-processing behavior were not tested. No pip upgrade, reconstruction engine, model weights or separate esptool environment changes. Next stage is explicitly scoped runtime verification/offline capture analysis, followed by metric drive calibration.

OCTOBER 8, 2026: OFFLINE CAPTURE ASSESSMENT
- User accepted data/<session-start>/analysis/<analysis-start>/ and explicitly answered yes to package verification and offline analysis of existing captures with saved diagnostics/summaries. No rover operation, metric calibration or reconstruction requested/performed.
- Added src/agent/analyze_captures.py with PairAnalyzer and CaptureAssessment classes. Dataset-specific plan: 2 stationary comparisons, 3 pan/return sets (6 pairs), 8 adjacent stationary sweep pairs, one forward before/after and 4 sequential drive pairs. 21 pairs use 28 distinct original 800x600 JPEGs from setup session. SIFT max 2500 features, ratio 0.75 plus mutual matching; homography RANSAC threshold 3 px. Sparse LK max 600 corners, 21x21 window, pyramid level 3, bidirectional validity and forward/backward error <=1 px. Saved retained coordinates, counts/rejections, pixel displacement, homography residuals and aligned grayscale differences.
- All six packages imported; pip check returned No broken requirements found. cv2 module version 5.0.0 corresponds to installed distribution opencv-python 5.0.0.93. Python printed Failed to find real location of D:\local\python\python_3_13_13\python.exe; all commands completed with exit code 0. Cause uninvestigated; broader runtime compatibility not claimed.
- Initial run saved diagnostics under data/20261008220100000/analysis/20261008234638721/. After adding findings and visualization, completed run saved under that directory's final/ subfolder. Both runs exited 0 and yielded identical summary metrics. Preliminary outputs preserved; final/report.md is authoritative. Final includes summary.csv, provenance.json (input SHA256, source info, versions, parameters and script SHA256), info.txt, motion_summary.png, flow_overview.png, and six files per pair (three PNG diagnostics plus match/flow CSVs and metrics JSON).
- Verified 21 summary rows, 65 PNGs readable by OpenCV, all pair coordinate CSVs present, and all 28 source SHA256 values unchanged. Viewed forward-before/after match overlay and left-turn flow overlay, then final flow contact sheet for all 21 pairs and final motion chart. No synthetic simulation or separate unit-test suite run.
- SIFT median motion: stationary comparisons 0.298/0.442 px (LK 0.165/0.196); forward-before/after 5.177 px (LK 5.330); sequential forward 3.120 px (LK 3.038), backward 7.215 px (LK 7.355). Left/right median dx +100.366/-103.603 px, opposite scene shifts. Five-degree command sweep median magnitudes 33.435-42.694 px. Three pan-return median magnitudes 0.901-3.644 px. All pairs produced homography and LK correspondences. Large turns retained fewer LK tracks and lower motion magnitudes than SIFT; retained-point bias remains relevant.
- Conclusions: offline tools produce usable diagnostics on these captures. Drive framing changes exceed the two stationary comparisons; physical translation remains unisolated, metric travel/turn angles unknown. Homography is not proof of depth or pure rotation; adequate 3D baseline remains unknown. No camera calibration, metric drive calibration or reconstruction stage complete.
- README layout now includes analysis; handoff updated with scope, result locations and next stage. Analyzer may later be promoted to src/tools/ after generalizing dataset-specific plan/report; no promotion performed. Next agenda is define metric drive calibration with known reference scale and explicit movement/session scope.

OCTOBER 8, 2026: CALIBRATION AND SAFETY PROTOCOL REVIEW
- User permits any of the nine current controls useful for the next exploration-calibration step and requests safety-protocol design. Read current handoff, relevant journal records, rover.ps1, UNO loop/dispatch/handlers, sensor/servo drivers, MPU6050 wrapper/initialization and camera alignment metadata. No rover connection, sensor execution, servo or wheel movement, firmware edit or controller implementation performed.
- Asked for permitted clear flat area's dimensions/edges/obstacles, supervision and physical stop access, ruler/tape availability. These facts remain pending; general calibration authorization does not supply instrument bounds or physical reference scale.
- Verified source contracts: N1 estimated volts from ADC * 0.0375 * 1.08; N2 signed raw gyro XYZ without bias subtraction; N3 signed raw accelerometer XYZ including gravity. Underlying wrapper does not expose I2C read success. MPU initialization sets gyro FS_250 and accel FS_2 in source; runtime register configuration and mounting axes have not been read back. No calibrated angular rate or displacement claimed.
- N4 direction 1 left, 2 right, 3 forward, 4 backward; D2 PWM, T milliseconds, zero disables expiry. Current Move waits T+100 then sends N100 and closes TCP; it does not gate on sensors, enforce clearance or measure rest. N5 absolute servo acknowledges in dispatch before driver execution; N6 increment acknowledges after driver execution, clamps pan command 10-170, uses remembered command rather than feedback. Driver waits 500 ms, detaches; both modes leave timed-drive mode. Pan+drive therefore excluded from initial protocol.
- N7 D1=2 reports pulseIn raw microseconds with host-supplied timeout, zero is timeout. Legacy boolean compares retained numeric threshold in raw units and is not chosen for safety gating. Serial dispatch precedes N4 expiry; blocking N7 can delay expiry. N8 reports selected raw floor ADC on demand without mode change or automatic stop. Sensors action samples sequentially and closes TCP; not a continuous IMU logger usable alongside separate Move.
- Proposed stationary calibration: multiple repeat samples; gyro stationary bias/noise and gravity orientation, without accelerometer double-integration for position; ultrasound measured target distances/angles and invalid-return behavior, retaining raw counts; floor normal-surface repeatability (no deliberate cliff approach); battery context with meter if available; camera forward alignment and pan return variability. Camera pan does not establish ultrasonic pointing direction. Source initialization/range is not a measured sensor calibration.
- Proposed movement calibration after area/reference facts: supervised short bounded N4 pulses, initially no more than prior tested PWM 60/200 ms and preferably shorter, but duration alone is not a safety guarantee. Measure reference-point displacement, drift, physical turn angle and post-command/expiry stopping travel, repeated trials at fixed surface and battery context; increase only within measured clearance. Live gyro integration would need timestamped sampling and verified axis/scale, not before/after stationary gyro values. No arbitrary speed, clearance or stop-latency calibration asserted.
- Proposed protocol: single controller; stop/observe/decide/short move/stop/observe. Forward gate needs fresh camera plus repeated valid N7 readings, conservatively use nearest valid echo and reject inconsistent/unknown evidence; measured clearance budget includes footprint, segment travel, stopping allowance and uncertainty. Unknown echo never means free space. Reverse restricted to recently observed and previously traversed corridor with known heading/pose and uncertainty margin; stop if that cannot be established. Turns require full swept-body clearance. Exclude drop-offs; floor ADC is not verified cliff detection. Avoid pan/ultrasound while driving; no automatic sensor-stop protection exists.
- Abort on stale/lost/invalid evidence, network/capture fault, obstacle change, unexpected motion/tilt/floor anomaly or session limit. Send N100, observe rest; operator physically disables rover if remote stop fails. Existing heartbeat-loss evidence (~3 s) is fallback and insufficient for close-obstacle braking; abrupt network loss and exact stop distance remain unverified. Calibration has not started; protocol is a proposal, not implemented enforcement. Handoff records proposal and pending area/reference facts.

OCTOBER 9, 2026: STANDING CALIBRATION SCOPE AND STATIONARY BASELINE
- User accepted safety proposal, declined calibration markers and permits sensor-native units. User-provided standing assumptions: flat/no drops, minimal obstacles at edges, roughly geometric visible objects, area within Wi-Fi. User will not navigate; intervention starts over. Scripting and tests/code execution allowed for calibration; additional packages still need explicit permission. User emphasized avoiding collisions before contact and allowed taking time. These assumptions do not establish measured clearance or calibrated sensor units.
- Initial Sensors invocation failed at parse time: CaptureSession.NewCaptureFolder local $folder collides case-insensitively with class property Folder. Renamed local to $captureFolder. Retried existing Sensors successfully: echo 8029 us, floor 345/532/474, battery estimate 8.019 V, raw gyro -356/60/254, accel -60/24/15396. No wheel/servo command.
- Added src/agent/collect_baseline.ps1 (BaselineRecorder). First network attempt failed before command due sandbox socket permissions; failed run retained under logs/20261009001043668. Escalated stationary collection approved and completed exit 0: 12 sequential sensor batches plus four JPEGs, no wheel or servo command. Source tool SHA256 and invocation-bracket UTC timestamps recorded, not individual exposure/sensor sampling times. Logs: data/20261008233756000/logs/20261009001118940/events.jsonl and sensors.json. Captures: captures/20261009001136723/frame-000000.jpg through frame-000003.jpg plus receipt manifest. Echo range 8023-8069 us, estimated volts 7.979-8.019. Viewed first frame: room visible, near-floor area poorly represented; no path-clearance claim.
- Current chat metadata: title Install visual analysis packages, createdAt 1791517076 -> New York 20261008233756000. Session info.txt uses title verbatim. Earlier offline setup-image results remain in the source setup session as previously documented.
- Added src/agent/stationary_survey.ps1 (StationarySurvey), intended pan commands 60/80/100/120/140/100/101/100 with three N7 echoes per view, tagged control log/manifest and finally N100/restore100/N100. Class refuses commands outside N5/N7/N100 plus heartbeat. Sandbox attempt failed before sending; retained empty capture/failure log directories 20261009001358249. Escalation rejected by user before process execution while shifting task to sandbox permissions. Survey has not been verified live; no pan or wheel commands executed by it.
- User asked to improve sandbox permissions first; hardware work held. Prefix requests in chat were exact collect_baseline.ps1 and stationary_survey.ps1 entrypoints; existing rover.ps1 approval did not cover those wrappers. No baseline analysis, drive calibration, movement or reconstruction completed in this phase.

OCTOBER 9, 2026: CODE NAME RESERVATIONS AND PROJECT RULES
- User explicitly requested planned future code and blank filename reservations, then requested unrestricted arguments for local .venv Python. Planned files verified absent and created at size zero under src/agent: rover_session.psm1, run_calibration.ps1, run_exploration.ps1, assess_calibration.py, map_observations.py, reconstruct_scene.py. They contain no code and were not executed. Responsibilities and proposed class boundaries recorded in handoff; no future capability claimed implemented.
- Added .codex/rules/python.rules allowing exact .venv\Scripts\python.exe with any arguments. Interpreter approval is not limited to src and does not replace task scope or explicit package-installation permission. Existing pip.rules retained.
- Updated .codex/rules/rover.rules to literal path union for current rover.ps1, keyboard-rover.ps1, collect_baseline.ps1, stationary_survey.ps1 and reserved run_calibration.ps1/run_exploration.ps1, all using pwsh -NoProfile -File ./src/... . No wildcard directory matching or general pwsh/-Command approval. New entrypoint names require rule edits/reload.
- Official OpenAI docs checked: https://learn.chatgpt.com/docs/agent-configuration/rules . Rules use literal arguments or literal unions, load at startup from trusted project layers, and support execpolicy check. Initial Python inline examples failed due backslash shell escaping; quoted interpreter tokens in examples and rechecked successfully.
- codex execpolicy check parsed final Python and PS rule files, returned allow for the exact venv interpreter and reserved calibration PS path, and returned no matchedRules for bare python or PS ./outside.ps1. Nonfatal Codex tmp/arg0 access warnings appeared; policy checks exited 0. This verifies explicit-file rule parsing/matching, not current-chat loading. Restart Codex with trusted project layer required. No calibration resumed after rule edits.

OCTOBER 9, 2026: PUBLICATION REQUEST
- User explicitly requested commit and push. Reviewed pending tracked/untracked scope, current branch codex/sequential-rover-control and origin https://github.com/c-earth/hyohakusha.git. Include pending session handling/fix, offline analyzer, baseline/survey scripts, six zero-byte reservations, README/handoff/journal and rover/pip/Python rules. Keep existing .codex/rules/git.rules local per accepted retention decision. Data and .venv remain ignored; no generated captures/reports/dependencies added. Whitespace check passed; no additional project runtime tests or rover operations performed for publication. Commit/push outcome reported in chat.
# October 9, 2026: exploration calibration procedure and stationary trials

User requested: "Perform and create calibration procedure with all rover commands
for exploration." Created `rover/calibration/procedure.md`; no firmware edits,
package installation or exploration execution. Procedure covers N1–N8/N100,
native-unit limitations, repetitions, distinct direction clearance gates and
completion requirements.

Executed collect_baseline.ps1 (12 batches), stationary_survey.ps1 (8 N5 views,
24 echo readings and stop/restore cleanup), rover.ps1 N6 +1, Record (1 frame),
N6 -1 and Stop sequentially. All invocations exited 0. Session:
`data/20261009003013000`, name `Exploration calibration`. Baseline logs:
`logs/20261009003020774`; baseline captures `captures/20261009003038476`;
survey captures/logs timestamp `20261009003134432`; N6 +1 capture timestamp
`20261009003211989`. Baseline completion log confirms 12 batches/4 frames.
Survey output confirms 8 views and cleanup; acknowledgments do not prove angles
or physical rest. N6 invocations were observed through tool output, without
per-command JSONL recording; this limits timing/provenance for that check.

Baseline battery estimated range 7.898–7.938 V (mean 7.911333 V), echo
8033–8081 us (mean 8060.416667 us), floor ADC left 344–345, middle 532–540,
right 473–474. IMU raw XYZ saved, quantitative bias assessment not performed.
Survey return echoes at command 100 included 12342/12373/8152 us; this variability
remains unresolved. No validated numeric obstacle or stopping threshold.

Inspected fresh baseline frame-000003.jpg with view_image: image shows doors,
walls and a box, with little near-floor space. No wheel command issued because
body/path/swept clearance is unknown. Requested current clear-area description
from user before dependent wheel trials. Calibration is partial; N4 motion,
stopping latency/distance, quantitative pan repeatability and fault handling
remain incomplete. Procedure read back and git diff --check passed. No new
runtime controller implemented; reserved calibration files remain empty.

# October 9, 00:35–00:44: repeated calibration and battery cutoff

The user explicitly allowed assuming a safe calibration area, then requested
best judgment within the task, stopping on severe cause or sandbox blocking.
They suggested gyro/accel together for coordinate clues and higher power.
No autonomous exploration executed. Implemented run_calibration.ps1 as a
PowerShell entry to calibration_session.py, with one Python TCP owner; existing
manual PowerShell controllers retained. assess_calibration.py computes baseline
noise, mutual-SIFT image displacement, late stability and raw IMU response.
Created test_calibration_safety.py, procedure/results docs and README usage.
No packages installed, firmware modified/flashed or subagents spawned.

Session `data/20261009003013000`, name `Exploration calibration`:

- Run 20261009003509244: 12 sensor baselines, three repeated N5/N6 pan sequences
  and 24 PWM60/T100 wheel trials. No in-motion IMU in this version.
- Run 20261009003805349: five complete PWM60/T200 trials, sixth aborted on
  250 ms gyro timeout. Delayed reply arrived ~265 ms after request during N100
  cleanup. Both cleanup N100 responses were logged. Failure/raw traffic retained.
- Applied TCP_NODELAY, reduced redundant heartbeats, raised sensor timeout to
  750 ms, kept independent host stop deadline, alternated asynchronous N2/N3.
- Run 20261009003930548: 24 complete PWM60/T200 trials, gyro/accel recording.
- Run 20261009004129863: 24 complete PWM80/T200 trials, gyro/accel recording.
- Each full wheel run: three repeats per four directions per expiry/early-stop
  mode. 72 trials across complete runs plus five completed/one aborted in the
  retained failed run. Matching captures, logs and analysis preserve evidence.

PWM80 expiry median image displacements: forward 8.182, backward 4.423,
left 148.106, right 149.711 px. Early-stop medians: 8.091, 2.468, 54.557,
47.745 px. Forward early-stop advantage is unresolved. Gyro Z signs were
positive left/negative right in tested 200 ms turns. PWM80 group median raw
gyro return estimates 247–413 ms after host stop send. Threshold is each-axis
max(5 baseline std, 50 counts), maintained to recording end for >=200 ms.
These receipt-time observations are not physical stop latency/distance, yaw or
coordinates. Accelerometer residuals/count-second gyro integrals saved without
position integration. Late-frame group medians ~0.333–0.434 px. Final images
from complete runs visually inspected. No continuous camera motion record.

N5 ±5 command-degree pan steps shifted image ~31–38 px; N6 ±5 ~34–40 px.
N6 ±1 yielded ~0.36–0.51 px, near stationary variation, so physical response
at 1 degree is unresolved. Absolute angle/return-position feedback unavailable.

User clarified low battery means N1 voltage <7.0 V. Implemented cutoff before/
after every bounded pulse: low/nonfinite reading sends N100 and raises; missing
or malformed response ends run through stop cleanup. No in-pulse battery reads.
Exactly 7.0 V is permitted. Final BatteryOnly run 20261009004436364 read 7.857 V,
sent N100 and disconnected. Three offline cutoff tests passed; live low battery
not induced. Voltage conversion accuracy still unverified.

All three complete live runs and their offline assessments exited 0. The failed
run exited 1 and remained retained. BatteryOnly exited 0. Python compilation
and git diff --check passed. Source hash logged at each live run start; installed
firmware was not re-read during this task. No held-out prediction/fused pose,
metric scale, stop distance or autonomous clearance model established. Overall
exploration calibration remains partial; tested higher PWM alone does not make
longer/higher-power exploration ready. Current summary: rover/calibration/results.md.

# October 9: time integration and recurring stationary gyro bias

User clarified "integrate over time of gyro rate" and "and accel", correcting
the initial interpretation of integration as combining camera/IMU tools. No
camera concurrency/workflow integration was implemented under that mistaken
interpretation. User then suggested regular gyro calibration; implemented host
bias refresh during stopped intervals before every future wheel trial.

Read active MPU6050.cpp/getdata source: initialize selects ±250 deg/s and ±2g.
Manufacturer search results support nominal 131 counts/(deg/s), 16384 counts/g;
PDF direct fetch failed, so no full PDF claimed read. Sources linked in report.
Live configuration registers and scale accuracy were not checked. No firmware
changes, package installation or live wheel trials in this task.

Added InertialIntegrator/IntegrationAssessment in src/agent/integrate_imu.py.
Gyro raw offset removed, trapezoidal angular increments composed as rotations;
acceleration transformed into initial sensor axes and stationary reference vector
subtracted, then integrated to velocity increment and zero-initial-velocity
displacement using exact piecewise-linear segment integration. Raw count-time
integrals retained. Restricts to observed overlap; no startup extrapolation or
end-velocity correction to force expected travel. Initial velocity/reference
gravity-bias separation, sensor scales and acquisition times remain assumptions.
Three timing hypotheses (request/midpoint/receipt) times two bias references
assessed per trial. These scenario spans are not statistical error bounds.

Computed 48 saved trials from logs/20261009003930548 and 20261009004129863.
Initial output under analysis/20261009005347000-inertial-integration retained;
final adds visualization and explanatory limit text under same name + -final.
Input trial/event SHA256 recorded in integration.json; source data untouched.
PWM80 full-turn group median nominal yaw left +15.328 deg/right -15.864 deg.
Median residual velocity increment norm 0.2476 m/s conditional, despite later
stable images: accel integration not validated travel. Median scenario yaw span
0.243 deg and displacement-component-span norm 0.0373 m; these omit unknown
calibration/initial-condition/aliasing errors. Final PNG visually inspected.

Added GyroBiasCalibrator in gyro_bias.py: five paired samples and image flow;
require >=20 valid tracks, median <=1 px, p95 <=3 px, gyro std <=50 raw counts,
accel std <=300 counts per axis. Provisional gates support rest, not proof.
run_calibration.ps1 adds GyroCalibrationOnly; runner logs fresh bias and stores
it per trial, rejects age >10 s, retains N1<7.0 V guard. integrate_imu consumes
the per-trial bias when available. Firmware offset/startup calibration unchanged.

Live stationary-only run 20261009005954541 exited 0, accepted bias
[-359.8,62.6,250.2] raw counts with N1 7.857 V. Camera/IMU gate accepted;
N100 cleanup and disconnect recorded. No N4 sent. Full wheel path with refresh
not live tested. Added six analytical tests (constant/ramp accel, bias/gravity
rest, rotation/gravity, support overlap and invalid times) and four bias-gate
tests; existing three battery tests retained. Initial gravity test encountered
SciPy Euler shape API mismatch; fixed Nx1 input, all 13 tests passed. Offline
integration exited 0; Python base-path warning seen once but no failure.
Procedure/results/handoff updated; git diff --check passed.

# October 9, 01:06–01:22: observation-driven improvements and bounded pilot

User requested solving calibration problems and allowed continued improvements
during exploration. Used existing safe-area assumption for short calibration
and local observation pilot only; no room-scale search or firmware modifications.
No dependency installs, subagents, commit/push or unrelated file changes.

Added TimedCameraRecorder (timed_camera.py): one HTTP-only worker, <=60 frames,
1.5 s request/2 MB JPEG bounds, monotonic/UTC brackets and nested frame manifest.
The sole TCP owner samples IMU one second before N4 through 1.6 s after host
N100. Requires two pre-motion frames; camera faults refuse/stop motion; all
exceptions send N100 before waiting for worker shutdown. Data gaps/exposure
timestamps remain unknown. Wrapper accepts TimedCamera/Repeats/TurnOnly/ImuPlan.

Added MotionValidation (validate_motion.py): raw/bias-corrected integration,
pre/post camera/IMU rest support, first-repeat scene-specific pixel/nominal-degree
fit and later-repeat held-out comparisons. Conditional rest-constrained constant
acceleration correction removes endpoint velocity residual only when both gates
pass; unconstrained trace preserved. This imposed endpoint is not independent
velocity measurement, distance validation or control odometry.

Runs in data/20261009003013000, Exploration calibration:
- 20261009010738515: camera p95 3.210 px >3 threshold; movement refused, no N4.
- 20261009010822507: six PWM60/T200 timed trials, then three bias-image rejections
  (medians0.206–0.258 px but p95 3.411–4.666). Quiet gyro/accel; N100 cleanup.
  Partial run and failed/rejected evidence retained; offline validation exited0.
- Updated image gate with robust partial-affine RANSAC (1 px residual), >=70%
  coherent support spanning25% width/height. Retains raw tracking statistics,
  applies original1px median/3px p95 to coherent tracks. Not simple threshold
  relaxation. Synthetic translated-image check rejects real coherent movement;
  corrupted-patch check preserves broad stationary support. Rest remains inferred.
- 20261009011141154: complete16 PWM60/T200 trials; camera/IMU rest support
  pre16/post15. Gyro/accel median gaps~93–101ms. Four held-out turns had median
  nominal vision/gyro discrepancy5.637deg; do not trust that heading model.
- 20261009011637215: implemented bounded_exploration.py subclass and PowerShell
  entry; exactly three forwardPWM60/T200 pulses (600ms total). Per-step bias,
  battery and timed recording; >20% shorter successive raw echo stop gate.
  Echo pairs12399/12312,12305/12060,12071/11918us. No power/turn/reverse increase.
  All3 pre/post rest supported. observations.json uses null metric position and
  false free-space verification. This is a local observation pilot, not room search.
- 20261009011850801: eight gyro-focused turn trials; gyro favored through turn
  and300ms after stop. Active gyro median gaps49.37–58.90ms,8–12 active samples
  versus sparse alternating data. Pre/post rest8/8; four held-out comparisons
  median0.588nominal deg. Small scene-specific consistency result, not absolute
  accuracy or a controlled causal comparison. Adaptive mode now applies this
  allocation to turns only, alternating at rest and during translations. Focus
  allocation means sparse in-motion accel; not suitable for dead reckoning.
- 20261009012243615: final stopped BatteryOnly read7.655V, N100 reply/close.

Full-run and pilot validation outputs under matching analysis/<run>-validation.
Integration of new16+pilot3 under analysis/20261009011637215-integration exited0:
median residual velocity increment norm0.2283m/s conditional. Drift persists;
endpoint-constrained values not used as measured travel. Final pilot/turn images
visually inspected. Camera/IMU/battery/floor/ultrasound raw records preserved.

Live full16/turn8/pilot3/battery check exited0; two refused/partial runs exited1.
Offline validators/integration exited0. Eighteen unittest checks passed: earlier
13 plus2 robust vision checks and3 pilot count/direction/power/duration/echo
stop checks. Compilation/whitespace checks passed. Provisional echo-change gate
is not calibrated clearance; floor thresholds/cliff protection, absolute scale,
sensor timestamps/range readbacks, camera intrinsics, physical stopping distance
and room coverage remain unestablished. README/procedure/results/handoff updated.

## Archived handoff before October 9 workflow simplification

Historical snapshot; superseded claims and authorizations are retained as evidence, not current instructions.

```text
ELEGOO rover project handoff
Updated: October 9, 2026, America/New_York
Workspace: D:\projects\hyohakusha

CURRENT RESUME POINT (October 9, latest handoff update)
- Latest authorized improvement task completed; rover last received N100 and
  disconnected. Last measured battery was 7.655 V in run20261009012243615;
  this is historical, not a current battery check. Stop whenever N1 <7.0 V.
- Calibration remains partial. Gyro bias refresh and camera/rest gates are live
  verified; absolute gyro scale/heading, accel-derived distance, battery accuracy,
  ultrasound/floor thresholds and camera intrinsics are not calibrated.
- Faster turn sampling achieved median vision/gyro disagreement0.588 nominal
  degrees on four held-out checks. Earlier alternating run gave5.637 degrees;
  different runs/scenes and small samples prevent a controlled causal claim.
- Three bounded forward observation pulses completed. This verifies the local
  pilot execution, not general autonomous exploration, clearance or metric pose.
- Latest verification:18 offline tests passed, relevant modules compiled, and
  git diff --check passed. No firmware changes or dependency installation.
- Next applicable work: independently validate heading/timing and translation
  estimates before using metric coordinates or increasing power. Keep timed
  captures, fresh stopped gyro bias and battery gates for any authorized pilot.
- Procedure/results: rover/calibration/procedure.md and results.md. Detailed
  completed-task evidence is in journal.md; no new rover operation in this update.

LATEST IMPROVEMENTS / LOCAL OBSERVATION PILOT (October 9, through 01:22)
- User asked to solve calibration gaps and permits improvement during exploration.
  Implemented timed_camera.py (HTTP-only worker), validate_motion.py and fixed
  bounded_exploration.py/run_exploration.ps1 observation pilot. One TCP owner.
- IMU/camera sample before, during and after short pulses, with host time brackets
  and per-trial stationary bias. Robust broad-support flow rejects minority
  tracking outliers; original pixel/noise gates retained. Up to three stopped
  bias attempts; persistent rejection refuses wheel movement. Raw evidence saved.
- Data session remains 20261009003013000. Run 20261009010738515 refused before
  N4; 20261009010822507 retained six trials then rejected bias checks. Full
  20261009011141154: 16 trials, rest support pre16/post15, held-out heading
  disagreement median5.637 nominal deg (four checks, alternating sampling).
- Local pilot 20261009011637215: three forward PWM60/T200 pulses, total600 ms;
  rest supported before/after all3. No reverse/turn/power increase. observations
  recorded with metric_position=null/free_space_verified=false. >20% echo
  shortening stops; this provisional gate is not validated obstacle avoidance.
- Focused turn run20261009011850801: eight trials, active gyro gaps50–59 ms;
  held-out median vision/gyro disagreement0.588 nominal deg on four checks;
  pre/post rest8/8. Scene-specific consistency, not absolute angular calibration.
  Adaptive turn sampling now favors gyro; rest/translation alternate IMU.
- Conditional zero-velocity endpoint diagnostics added only with both rest gates
  supported; never used as validated odometry. Unconstrained accel still drifts.
- Reports: matching analysis/<run>-validation; source summary in
  rover/calibration/results.md. Eighteen offline tests passed; full new paths
  live exercised. Final N1 run20261009012243615:7.655 V, N100/close.
- Next: continue small observation pilots with these gates, assess independent
  visual/IMU agreement; no unverified distance/heading model or power escalation.
  Absolute sensor accuracy, timestamp/range verification, camera intrinsics,
  stopping distance and room search/coverage remain incomplete. Firmware unchanged.

LATEST INTEGRATION / GYRO BIAS (October 9, through 00:59 New York)
- User clarified mathematical integration of gyro rate and acceleration, then
  requested regular gyro calibration. Added integrate_imu.py and gyro_bias.py.
- Offline integration of 48 existing T200 trials: bias removal, orientation
  composition, rotating accel into initial sensor frame, stationary reference
  subtraction and velocity/displacement integrals. Nominal source-based scales
  conditional; no sensor acquisition timestamps/live range-register verification.
- Final report/JSON/CSV/PNG under data/20261009003013000/analysis/
  20261009005347000-inertial-integration-final/. PWM80 median full-turn nominal
  yaw +15.328/-15.864 deg left/right; accel displacement unreliable due residual
  velocity/missed onset and timing/bias/gravity uncertainties. No coordinates.
- Runner now refreshes stopped gyro bias before every wheel trial using five
  paired IMU reads plus image stationarity gates; maximum bias age 10 s. Unknown
  rest evidence refuses motion. Host correction only; firmware unchanged.
- Stationary-only live run logs/20261009005954541 accepted bias raw XYZ
  [-359.8,62.6,250.2], N1 7.857 V, N100/close. No wheels for this task. Bias
  capture path verified; full wheel path with these gates not yet live tested.
- Thirteen integration/bias/battery tests passed. Updated procedure/results.
  Next: verify sampling/scales and integrated estimates against independent
  scene/known-motion evidence; do not promote accel integration to odometry.

LATEST CALIBRATION SESSION (October 9, 00:30–00:44 New York)
- User requested creation/performance of calibration, then explicitly allowed a
  safe-area assumption and best judgment within the task. No exploration run.
- Implemented run_calibration.ps1, calibration_session.py and assess_calibration.py;
  PowerShell entry delegates one Python TCP owner for this calibration. Existing
  manual PowerShell controllers retained. Procedure/results under rover/calibration/.
- Session data/20261009003013000, Exploration calibration: stationary baseline,
  survey, repeated N5/N6 and 72 complete drive trials covering all directions,
  expiry/early N100, PWM60/T100, PWM60/T200 and PWM80/T200. Last two record
  alternating raw gyro/accel; host timing is not sensor acquisition timing.
- Additional T200 run failed during its sixth pulse on a delayed gyro reply;
  N100 cleanup sent/replied. Five full trials/raw failed-trial traffic retained.
  Applied TCP_NODELAY, heartbeat reduction and 750 ms sensor timeout; stop
  deadline independent. Subsequent two full runs completed without that fault.
- Left/right gyro Z signs established for tested turns; image response and
  later image stability measured. PWM80 forward early stop had nearly the same
  image response as expiry; translation stopping advantage remains unresolved.
  Gyro return is low angular response, not measured physical stop distance.
- N6 ±1 image response near stationary variation; physical 1-degree response
  unresolved. ±5 and N5 5-command-degree changes visibly shifted images.
- User battery rule: stop if N1 <7.0 V. Runner enforces before/after each bounded
  pulse; invalid reading faults. Final stopped N1 check: 7.857 V. Three offline
  cutoff tests passed. No physical low-battery event induced. Rover disconnected.
- Full results/provenance paths: rover/calibration/results.md. Calibration is
  partial for exploration: metric scale/yaw, stop distance, fused pose/uncertainty,
  held-out predictive validation and automatic clearance gates unestablished.

READ FIRST
- AGENTS.md: standing working instructions and authorization requirements.
- README.md: setup, hardware, paths and usage. Some deployment statements still
  say not built/uploaded; the current build/upload evidence below supersedes them.
- WORKFLOW.md: proposed architecture, not implemented runtime behavior.
- journal.md: historical work, full test records, old findings and prior roadmap.
  Historical command numbering and superseded claims there are not current facts.
Keep this handoff concise; relocate completed detail to the journal.

CURRENT DIRECTION AND AUTHORIZATION
- Goal: AI rover control, bounded exploration and reconstruction of visible interior.
- User revised the sequence: inspect image-analysis tools, calibrate driving first,
  then bounded search while collecting information for reconstruction.
- Prior direction/stopping trials were functional checks, NOT drive calibration.
- Retain existing PowerShell manual control; calibration and local observation
  pilot have PowerShell entries sharing one Python TCP-owner implementation.
  No general search/pose runtime exists.
- User subsequently authorized package installation, runtime verification and
  offline analysis of existing captures with saved diagnostics and summaries.
  This offline task is complete. Later calibration authorization below is current;
  completed earlier trials do not themselves grant scope. Permission rules do not
  replace task authorization.
- One main agent and one owner of TCP control; no subagents unless requested.
- User permits N1-N8/N100, Python/PowerShell scripting and tests/execution for
  calibration toward exploration. No supplied markers: use sensor-native units.
  Standing user assumptions until revised: flat surface/no drops, minimal edge
  obstacles, roughly geometric visible objects, area within Wi-Fi range. These
  are user-provided assumptions, not measured environmental guarantees.
- User will not navigate; intervention starts over. Avoid hitting anything in
  the first place; do not move when path/body/stopping clearance is uncertain.
  Additional packages require explicit user permission. Keep detailed records.
- Prior permission hold ended with the latest authorized calibration. User now
  allows safe-area assumption for calibration and asks for best judgment; stop
  on severe causes or sandbox blocking. Battery N1 <7.0 V is an explicit stop.

CURRENT FIRMWARE
- UNO current source built and uploaded October 8 using arduino:avr:uno, core 1.8.8.
  COM3 was CH340; avrdude accepted target signature 1E 95 0F and read-back verified
  all 20,416 flash bytes. Port and current connectivity must be re-established.
- Program storage: 20,416 / 32,256 bytes, leaving 11,840. Global RAM: 794 / 2,048,
  leaving 1,254 for stack/local variables. Earlier app 31,068 bytes; reduction
  10,652 bytes (34.29%). Saved build/uno/flash.hex matches compiler output by hash.
  eeprom.hex matches compiler output and contains no EEPROM data.
- Command mapping: N1 battery, N2 raw gyro XYZ, N3 raw accelerometer XYZ,
  N4 timed drive, N5 absolute servo, N6 incremental pan, N7 ultrasound,
  N8 selected raw floor ADC, N100 stop. Historical IDs in journal are superseded.
- Loop: watchdog -> serial dispatch -> pending N5 servo -> N4 drive/expiry -> N100.
  Removed autonomous modes, button/IR handling, automatic battery/LED behavior,
  repeated standby stopping, gyro drive correction and reviewed unused code.
  Forward/backward use requested PWM directly. Startup gyro calibration and
  servo positioning, LED initialization and some supporting driver code remain.
- N4 T is milliseconds; T=0 bypasses expiry. N7 accepts requested timeout T in
  microseconds and D1=2 returns raw echo duration; zero is timeout, not free space.
  N8 reads fresh selected ADC without changing mode. Battery conversion and raw
  IMU readings have not been calibrated or independently validated.
- Preserve original backups at rover/backups/20261007183240988. Original UNO
  readbacks include full 32 KB flash and 1 KB EEPROM; fuse/lock backup absent.
  Camera was not flashed. Active/backup ESP32 files are full 8 MB readbacks;
  downloaded S3 source is not proven identical to installed camera firmware.
- euler.md preserves removed yaw function; do not restore it incidentally.

LIVE EVIDENCE AND LIMITS
- October 8, 23:17-23:18 New York: user-authorized N1-N8 test completed through
  existing rover.ps1, with no permission prompts or escalation requests. Sensors
  replied; N5 90/100/90 and N6 +5/-5 acknowledged and visually moved/returned.
  N4 four directions at PWM 60 / 200 ms: left/right images show opposite shifts;
  forward/backward small framing changes do not conclusively verify translation.
  Final two images appeared stable; host N100 sent and TCP closed. No metric
  calibration or isolated stopping test. Camera command reference left at 90.
  Details and capture locations in journal.md. This completed test grants no
  continuing movement scope; next stage remains image-tool assessment/calibration.
- Wi-Fi sensor replies received for all five categories using current numbering:
  ultrasound 10817 us; floor 297/708/526; estimated battery 8.667 V;
  gyro -372,60,228; accelerometer 48,52,15388. These are one-session readings,
  not present measurements or proof of accuracy/mounting axes.
- N5 100 -> 105 -> 100 and N6 +5/-5 returned ok; inspected images showed leftward
  pan and approximate return. Physical degrees and repeatability unmeasured.
- User observed forward/backward/left/right at PWM 60 / 200 ms and stopping.
- Separate user-observed trials support timed expiry, early N100 stopping and
  early stopping on graceful TCP close. Exact physical stop latency unmeasured.
- Without host heartbeats, stationary TCP closed at 3029 ms. In forward PWM 60
  / T=5000 trial, peer closed at 3025 ms and user observed stopping around 3 s.
  No host N100 was sent in that trial. Camera-generated N100 not directly logged.
- Evidence is limited to these individual trials. Abrupt Wi-Fi loss, reliability,
  other surfaces/speeds, metric travel/turning and stopping distance unverified.
  Keyboard live checks were explicitly skipped.

CONTROL TOOLS AND RULES
- Added .codex/rules/pip.rules for exact prefix .venv\Scripts\python.exe -m pip
  install, at user's request. Saved/read-back verified; current-session loading
  not verified. Packages subsequently installed under the explicit request below.
  The rule itself does not authorize dependency tasks.
- New code belongs under src/agent/ per user direction. Track candidates for
  promotion to src/tools/ or other higher-level locations with purpose/readiness;
  src/agent/analyze_captures.py now provides the offline setup-session assessment.
  Candidate for later src/tools/ promotion after removing dataset-specific plan
  and report assumptions; currently remains under src/agent/.
- src/tools/rover.ps1: Sensors, Record, Move, Stop, PanTest, FinePanTest, PanStep.
  Address default 192.168.4.1; TCP 100; HTTP capture; MJPEG port 81.
  Move requires EnableMovement; PWM 1-100. DurationMs now has NO range validator,
  remains int/default 200; removal was read-back checked, not execution-tested.
  Negative/extreme values can fail the host wait. Move waits DurationMs+100 then
  sends N100 and closes TCP. No automatic movement/sensor verification.
- src/control/keyboard-rover.ps1: existing keyboard controller; updated N4 mapping.
- .codex/rules/rover.rules allows exact prefix:
  pwsh -NoProfile -File followed by a literal union of six paths: tools/rover.ps1,
  control/keyboard-rover.ps1, agent/collect_baseline.ps1, agent/stationary_survey.ps1,
  agent/run_calibration.ps1 and agent/run_exploration.ps1 (each prefixed ./src/).
  No directory wildcard. .codex/rules/python.rules allows all arguments to exact
  .venv\Scripts\python.exe, per explicit user request; no src restriction for Python.
  Older pip rule retained. Codex execpolicy check parsed both files, confirmed
  allowed Python/planned PS examples and no match for bare python/outside.ps1.
  CLI emitted nonfatal temp-directory access warnings. Rules need Codex restart
  and trusted project configuration; active-session loading NOT verified.
- Scripts duplicate connection logic; no cross-process ownership lock, unified
  session log, localization or autonomous search implementation exists.
- Do not combine pan with active driving without resolving mode/expiry interaction.
  Synchronous sensing can delay loop handling; actual concurrent behavior untested.
  Serial framing/validation, response correlation and restoration/stop cleanup
  remain review items. Recheck current source instead of importing old findings.

CAPTURES AND CALIBRATION
- Existing data now grouped under data/20261008220100000/, using the start time
  of previous chat "Build and replace firmware" (October 8, 22:01 New York).
  Session info.txt contains setup. Includes this chat's captures as requested.
  All 74 pre-existing file SHA256 hashes matched after relocation; one new
  session info.txt added. Old per-capture folders, names and metadata preserved.
  Historical control log: logs/live-sequential-check/events.jsonl in setup folder.
- rover.ps1 capture actions now require SessionTimestamp (yyyyMMddHHmmssfff,
  New York session start) and ChatName; reuse across the chat. Session info.txt
  holds chat name; captures retain timestamped subfolders and purpose info.txt.
  A CaptureSession class owns folder creation and rejects name conflicts before
  TCP connection. README examples/layout updated. Verified by source read-back;
  no script runtime tests or rover operations performed for restructuring.
- Provisional camera alignment: command 100 forward, increasing command turns left.
  rover/calibration/camera.json is historical command state, not position feedback.
  No established motor encoders, servo feedback or calibrated camera intrinsics.
- Useful capture groups under data/20261008220100000/captures/:
  20261008223235046: N5 100/105/100, center/pan/return.jpg.
  20261008223409165: N6 0/+5/-5, center/pan/return.jpg.
  20261008225316209: nine pan080.jpg..pan120.jpg, stationary 5-degree sweep.
  20261008225505941: before.jpg/after.jpg around forward PWM 60 / 200 ms and N100.
- Each has info.txt. Pan/capture trials lack timestamp manifests and measured poses.
  Inspected images overlap; sufficient depth parallax/reconstruction geometry is
  not established. Offline quantitative analysis completed below; no reconstruction.
  Stationary sweep alone does not establish a usable translational baseline.

IMAGE-ANALYSIS ENVIRONMENT
- User requested "install useful visual analysis packages". Installed Windows
  binary wheels into .venv with pip, exit code 0: opencv-python 5.0.0.93,
  NumPy 2.5.3, Pillow 12.3.0, SciPy 1.18.1, scikit-image 0.26.0 and
  Matplotlib 3.11.2, plus dependencies. Pip reported successful installation.
  Subsequently all six imported and pip check found no broken requirements.
  SIFT, homography, sparse LK flow and Matplotlib rendering worked on this dataset.
  Python emitted "Failed to find real location" for the base interpreter path;
  commands nevertheless exited 0. Cause not investigated. No rover operations.
  Full dependency list and completed analysis evidence in journal.
  The assessment below is historical and predates this installation.
- October 8 tool assessment recommends OpenCV + NumPy for offline image matching,
  pixel-motion diagnostics and later camera calibration; this is a proposal,
  not a user-accepted installation or verified runtime. Official opencv-python
  metadata lists Python 3.13 support and Windows wheels. Local package-directory
  inspection still found no cv2/OpenCV/NumPy/Pillow/Open3D/PyTorch entries.
  Next concrete scope: install into .venv and run offline checks on existing
  N4/pan/stationary captures, saving correspondence/flow diagnostics. No rover
  motion needed. Metric drive calibration still requires a known scale; pixel
  motion alone cannot establish centimeters. Defer COLMAP until translated-view
  geometry is suitable; Open3D RGB-D integration lacks depth input here.
- .venv/pyvenv.cfg: Python 3.13.13, base D:\local\python\python_3_13_13\python.exe,
  include-system-site-packages=false. Use .venv\Scripts\python.exe for authorized
  project work; keep tools/esptool's cp312 packages separate.
- Read-only package-directory inspection found no OpenCV, NumPy, Pillow, PyTorch
  or Open3D packages. Imports/runtime availability were not tested.
- Available view_image supports visual inspection, not measured geometry.
  Tool metadata inspection found no dedicated reconstruction/metric vision tool.
- Official documentation reviewed: OpenCV calibration/optical flow; COLMAP SfM/MVS;
  Open3D reconstruction tutorial expects RGB-D. These are candidates, not verified
  project installations. No image-analysis dependency installed or code executed.

NEXT DECISIONS / PROPOSED WORK, NOT AUTHORIZATION
1. Core image-tool assessment and initial offline capture diagnostics complete.
   Results: data/20261008220100000/analysis/20261008234638721/final/report.md.
   21 pairs, 28 unchanged source JPEGs, 65 verified readable PNG outputs.
   SIFT stationary medians 0.30/0.44 px; forward pairs 3.12/5.18 px, backward
   7.21 px; left/right dx +100.37/-103.60 px. No physical scale established.
   Accepted results layout: data/<session-start>/analysis/<analysis-start>/,
   alongside captures/logs. Current run retains preliminary outputs at its root;
   final/ contains the completed report, chart, CSVs, provenance and diagnostics.
2. Repeated native-unit command calibration now recorded in session
   data/20261009003013000; see rover/calibration/results.md. Next: held-out
   response prediction, gyro/accel/image consistency and pose uncertainty before
   exploration. Metric scale and physical stop distance remain unestablished.
3. Define bounded search area, prohibited areas, supervision, movement/session
   limits, stop conditions and sufficient coverage before exploration.
4. During authorized search, collect images, sensor values, commands, replies,
   timing and calibration/firmware identifiers for later reconstruction.
5. Assess/calibrate camera geometry and reconstruct collected translated views;
   agree relative vs metric output, quality criteria and export format.
No calibration, autonomous exploration or reconstruction stage is complete.

CALIBRATION/EXPLORATION SAFETY DESIGN (PARTLY IMPLEMENTED; SEE LATEST RESULTS)
- Use stationary sensor repeatability, battery context, gyro bias/gravity axes,
  raw ultrasound/floor baselines and camera forward/return. Then gated short N4
  pulses with sensor/image response and stopping observations; repeat before
  enlarging motion. No supplied markers or navigation assistance. Report native
  units/relative geometry until a physical conversion is independently supported.
- One TCP owner; stop -> observe -> decide -> bounded move -> stop -> observe.
  Reject T=0, invalid duration and stale/missing/malformed or conflicting evidence.
  Initially no pan or ultrasound reads during active movement; their synchronous
  processing/mode changes can delay expiry or remove timed-drive mode.
- Gate forward travel on fresh camera and repeated valid ultrasound, using raw
  D1=2 replies. Zero echo is unknown, not clear. Do not use legacy N7 boolean.
  Clearance must cover robot footprint, predicted segment, measured stopping
  allowance and uncertainty. No numeric threshold validated yet.
- Reverse only within a recently verified traversed corridor with known pose,
  heading and enough uncertainty margin; otherwise stop for supervised recovery.
  Prior traversal alone is insufficient. Turns require full swept-body clearance.
- Exclude stairs/drop-offs from initial area. Floor ADC baselines are supporting
  evidence, not verified cliff protection; no rear sensor/odometry established.
- Stop on communication/capture/sensor fault, unexpected movement, tilt, floor
  anomaly, obstacle entry or exceeded session bounds. N100 send/ack is not proof
  of rest. Observe stopping before resuming; remote stop failure is unresolved
  without intervention. Do not presume an available human navigation/recovery
  fallback. Heartbeat close is fallback, not collision braking.
- Existing rover.ps1 does NOT enforce this protocol. Dedicated IMU sampling
  during movement, pose/corridor tracking and automatic clearance gates are
  proposals requiring their own implementation scope; standalone Sensors closes
  TCP, so it cannot provide a continuous turn-rate record for a separate Move.

CODE PLAN (CALIBRATION/LOCAL PILOT IMPLEMENTED; THREE RESERVATIONS EMPTY)
- src/agent/rover_session.psm1: RoverSession owns TCP, heartbeat, unique replies,
  command validation, sensor/capture timestamps, logging and best-effort stop.
  SafetyGate rejects unsafe/unknown paths and invalid/over-budget movement.
- src/agent/run_calibration.ps1: implemented PowerShell entry for the dedicated
  calibration_session.py TCP owner, fixed PWM60/80 and T100/200 trial bounds,
  stationary/pan/drive recording, stop cleanup and user N1<7.0 V cutoff.
- src/agent/assess_calibration.py: implemented baseline noise/bias, SIFT image
  response, late stability, raw IMU residuals and receipt-time gyro-return report.
- src/agent/map_observations.py: ObservationMap tracks observed/traversed areas,
  pose uncertainty and coverage; unknown space must stay distinct from free space.
- src/agent/run_exploration.ps1: implemented fixed three-forward-pulse pilot
  through bounded_exploration.py, sharing calibration/bias/battery/camera gates.
  No reverse, turn, power escalation, general room search or verified-free map.
- src/agent/reconstruct_scene.py: ReconstructionAssessment checks translated-view
  geometry and exports reconstruction only with supported quality/scale claims.
- Existing collect_baseline.ps1, stationary_survey.ps1 and analyze_captures.py
  retained. The survey is unverified live: sandbox denied connection before commands;
  escalation rejected while user switched focus to permissions. Baseline completed
  with approved network access. NewCaptureFolder local variable renamed to avoid
  PowerShell class/property name collision; Sensors/Record subsequently ran.
- User previously requested six zero-byte reservations. Calibration runner,
  assessment and local exploration entry now implemented; other three empty.
  No promotion from src/agent/ planned before implementation/evidence supports it.

ACCEPTED RETENTION AND REPOSITORY STATE
- Keep vendor package, backups, active vendor HEX/addLibrary ZIPs and accepted old
  editor paths. Do not rename capture files based on invented preferences.
- Last inspected HEAD: 7fc55ed, Simplify rover firmware and renumber host commands.
  Pending tracked edits before this consolidation: README.md, handoff.txt,
  src/tools/rover.ps1; .codex/ untracked. Generated firmware/captures/tools ignored.
  The consolidation added journal.md and updated AGENTS.md.
- This consolidation preserved the previous handoff verbatim in journal.md and
  replaced it with current state. Verified by read-back and archive comparison;
  no project code, tests, simulation or rover operations performed for this task.

PUBLICATION REQUEST
- October 9 user authorized commit and push of pending work: capture session
  handling/fix, offline analyzer, baseline/survey scripts, six empty reservations,
  README/handoff/journal and rover/pip/Python rules. Existing git.rules stays local.
  Captures, derived reports and .venv remain ignored under existing .gitignore.
- Reviewed pending diff, verified reserved files size 0, whitespace check passed.
  Publishing current codex/sequential-rover-control branch to origin; outcome
  reported in chat. No extra runtime tests or rover operations for publication.

```

## October 9: streamline documentation for the next live test

User authorized leaning out the project through updates that improve the next
live test. Work was limited to documentation and agent instructions.

- Archived the prior handoff verbatim above and replaced it with a concise
  current resume point, supported limits and one proposed next experiment.
- Rewrote README to remove superseded not-built/uploaded claims, correct the
  N6 request to N=6 and describe current tools/data without historical duplication.
- Replaced WORKFLOW with preparation, fixed acquisition, disconnected analysis
  and stage decisions; aligned the accepted calibration/search/reconstruction order.
- Added rover/calibration/next-test.md with a stopped preflight and one proposed
  eight-turn PWM60/T200 timed-camera session. Command options, pulse count and
  validator interface were checked against current source. No independent
  absolute heading claim or unestablished numeric acceptance threshold was added.
- Updated procedure references and adaptive-sampling/pilot wording. Added
  experiment discipline to AGENTS and reduced unnecessary class/docstring boilerplate.
- Verification: source inspection, document read-back/diff review and whitespace
  check. Archived handoff matched previous HEAD after line-ending normalization.
  No project Python, tests, simulation, dependency installation, firmware work,
  rover operation, commit or push. Controller behavior remains unchanged.

## October 9: organize agent source and improve experiment evidence

User requested a code/workflow review, useful skills/subagents, source cleanup,
legacy-firmware consultation and incorporation/removal of euler.md. Clarified
scope explicitly allowed targeted edits/moves/removal while preserving data,
backups and vendor files. Subsequently authorized offline unit tests, module/help
checks, PowerShell parsing and skill validation. No live session was requested.

- Reorganized Python into src/agent/runtime, analysis and tests; retained the four
  PowerShell entry paths. Calibration/pilot launchers invoke root-relative modules
  and restore the caller's location. Removed three unused zero-byte reservations.
- Extracted MotionSampler from session sequencing. It refuses start lateness
  over 50 ms, camera receipt age over 500 ms, pending sensor timeout and stale
  stopped bias at dispatch. N100 is serviced ahead of more polling/commands.
  These host thresholds are provisional and not physically calibrated.
- Send-begin/completion and socket-receipt times are recorded before event-log
  work. Checkpointed trial status/error and partial telemetry survive acquisition
  failure. Cleanup attempts N100 and closes TCP despite stop/logging faults;
  positive cleanup evidence is written after socket close.
- Timed camera returns detached metadata, records join failure, and stops new
  frame writes after a request returns if shutdown was requested.
- Separated inertial mathematics from plotting/report imports. Legacy Euler
  bias/rate integration informed full-gyro sensor-Z trapezoids, using nominal
  scale 131 and sensor-positive sign. Did not copy the 0.05-degree-per-increment
  deadband or startup-time integration. Original source survives in the backup;
  redundant euler.md removed. Existing 3D orientation/acceleration diagnostics
  retain their own common-support window.
- Validation retains unsupported/partial records and excludes incomplete or
  rest-rejected trials from fit/held-out comparisons. Missing cleanup evidence
  remains unknown. New heading method differs from historical overlap Euler yaw;
  no claimed improvement against the old 0.588-degree median. Removed unused
  all-frame-pair SIFT work from this report; raw images remain available.
- Updated workflow, next test, procedure, README and agent instructions. Created
  one instruction-only repository skill under .agents/skills/rover-experiment.
  Skill links/frontmatter reviewed, including independent source review; bundled
  quick_validate.py failed to import PyYAML, so automated skill validation is
  incomplete. No package installed. Skill discovery in the running app unverified.
- Updated rule examples/comments for module invocation. Allow patterns and
  authorization boundaries unchanged; existing local git.rules untouched.

Two subagents reviewed source within user-authorized delegation. One supplied
offline regression tests, the other reviewed final scheduling/cleanup and skill
scope. One main editor coordinated changes; nobody contacted rover hardware.

Firmware review findings (no source/build/upload changes):

- ApplicationFunctionSet_xxx0.cpp:453 overwrites CommandSerialNumber for every
  command; N4 expiry at :223 uses that global tag. Store N4's tag independently.
- N5/N6 switch modes and servo driver blocks 500 ms; active N4 expiry can be
  disabled without stopping outputs. N7 pulseIn can postpone expiry because
  serial dispatch precedes the drive timer. Keep host gates; propose firmware
  rejection while active plus expiry service before dispatch.
- MPU6050_getdata.cpp:33 has an uninitialized retry counter; initialization
  failure is ignored by ApplicationFunctionSet_xxx0.cpp:99. MPU6050.cpp raw gyro/
  accel readers discard I2C byte counts. Propose checked readiness/raw replies.
- Startup offset work is unused by current raw telemetry. Legacy straight-line
  correction changes PWM/sampling behavior and should not return incidentally.
- UNO and reference ESP32 use UART 9600. Do not change one side alone; downloaded
  camera source still lacks verified identity with the installed image.

Verification:

- .venv\Scripts\python.exe -B -m unittest discover -s src/agent/tests -t . -v:
  35 passed. Includes late/faulted dispatch, stop priority, source timestamps,
  partial records, cleanup errors, camera snapshots, report exclusions and
  gyro-only integration with shorter accel support.
- Six Python module --help invocations exited 0; 21 Python files parsed;
  both changed PowerShell launchers parsed; whitespace checks passed.
- Protected data/backups/vendor inventory matched before/after: 1,811 files with
  identical paths, lengths and last-write timestamps. This was a metadata check,
  not a byte-content audit.
- No new live evidence, firmware changes, dependencies, commit or push.
  Next stage: explicitly authorized stopped preflight and focused eight-turn
  session to verify the changed host runtime within existing bounds.

OCTOBER 9, 2026: UNO FAULT/EXPIRY CANDIDATE AND HOST COMPATIBILITY
- Authorization: user requested "perform the first 3 steps" of the proposed
  firmware sequence: implement UNO fixes, handle fault replies on the host, and
  build/check offline. Upload and live rover work were outside that request.
  Later user asked to prepare the broader source organization after firmware.
  User clarified rover sequencing: one controller, IMU readings allowed during
  motion, movement/pan actions serialized. No delegation for this task.
- Replaced application functional-mode coupling with a private DriveTimer and
  N4-owned completion tag. Expiry uses unsigned millis subtraction and >= at the
  deadline; checks run before/after dispatch, during serial receipt and after
  sensor reads. N100 writes stop output before {ok}. Explicit faults also stop
  before UART output. The loop no longer depends on a later clear-mode pass.
- N5/N6/N7 during an active N4 stop the drive and reply error_drive_busy without
  invoking their blocking drivers. N5 success now follows driver completion.
  Direct A/B PWM polarity, command IDs, sensor units, servo limits, UART 9600,
  keyboard N4 refresh and T=0 no-expiry contract are retained in source. The
  agent still uses positive bounded pulses and one pending IMU request.
- MPU6050 wrapper now checks WHO_AM_I, configuration writes/readback, register
  selection acknowledgment, full six-byte reads and Wire timeout status. Startup
  uses ten initialized attempts, preserving nominal +/-250 deg/s and +/-2g range
  settings. Wire timeout is 10,000 us per operation with bus reset; this is not
  an end-to-end timing guarantee. Read failure leaves outputs untouched and
  latches readiness false. N2/N3/N4 then refuse until successful init at restart.
  Removed unused startup offset sampling/state and its duplicate MPU object.
- Parser bounds frames at 160 characters and rejects malformed/oversized input
  with an untagged fault. Fault payloads: error_imu_not_ready, error_imu_read,
  error_drive_busy, error_drive_direction, error_bad_json, error_frame_too_long.
  Reply form is {H_error_reason}, or {error_reason} if no tag is available.
- Python FirmwareFault derives from RuntimeError, so explicit firmware failures
  bypass the ValueError-based stationarity retries. Production poll records and
  rejects faults regardless of tag, including an N4 rejection while awaiting
  IMU data. Existing acquisition cleanup attempts N100 and closes TCP.
- PowerShell uses shared src/control/rover-protocol.psm1. Manual sensor/pan reads,
  survey and keyboard detect errors; keyboard's existing catch stops/disables/
  disconnects. Manual Move now polls for fault/completion within its existing
  DurationMs+100 host window and attempts stop in finally before disconnect.
  No new DurationMs validation was introduced. Baseline inherits manual handling.
- Built arduino:avr:uno using the project Arduino CLI/config and AVR core 1.8.8:
  19,762/32,256 program bytes; 664/2,048 global RAM bytes, leaving 1,384 for local
  data/stack/heap. Compared with the uploaded 20,416/794 build: reductions 654/130
  bytes. Dynamic peak memory has not been measured.
- Candidate saved separately at
  rover/firmware/build/uno-candidate-20261009/uno.ino.hex; SHA-256:
  ddd2e5d196ebfc4506a9d82084e79dff958ff7493919c547f30d1734f041524a.
  verification.json records build limits, source hashes and actual check counts.
  Original build/uno/flash.hex identity is recorded in verification.json; its
  payload remains 20,416 bytes. Saved EEPROM has zero payload bytes. Saved UNO,
  EEPROM and camera hashes matched between the two explicit hash inspections.
  Data/backups/vendor and installed images were not modified by this task.
- Verification passed: 41 Python tests (six new tests include fragmented replies,
  unrelated drive tags, real parser/fake transport stop paths and bias retry
  exclusion); 12 PowerShell reply checks, including the actual manual Read-Rover
  function with a fake stream; four changed PS sources parsed; keyboard SelfTest;
  two runtime module --help checks; Intel HEX checksums and payload sizes; and
  whitespace checks. Help/HEX-check Python execution printed "Failed to find real
  location of D:\local\python\python_3_13_13\python.exe" but exited 0 and completed
  its checks. No environment changes were made in response.
- Ten compile-time assertions against the production DriveTimer passed under
  avr-g++ -std=gnu++11 -mmcu=atmega328p -Wall -Wextra -Werror. They cover idle,
  exact/late expiry, T=0, millis wraparound and renewed command timing.
  The sandbox blocked avr-g++ with a Windows DLL relocation error. Approved
  execution outside the sandbox succeeded for both the UNO build and assertions.
- No full firmware emulator/native harness, physical I2C fault injection, UART
  round trip or physical stop test was run. Source ordering review, compile-time
  timer evaluation and host fake transports do not verify those hardware paths.
  UNO installed firmware remains the October 8 version with the reviewed faults;
  camera was not flashed. No network/serial connection, upload, movement,
  dependency installation, commit or push occurred.
- Updated README, procedure, next-test, firmware info and handoff to distinguish
  candidate from installed firmware. Recorded the user's sequential-control
  rule in AGENTS/WORKFLOW. Repository skill is available this chat; prior PyYAML
  validator limitation remains. Prepared the requested folder plan in WORKFLOW:
  extract shared TCP ownership/motion/protocol/camera into control, retain agent
  experiment policy/evidence, and place human-facing launchers in tools. Actual
  moves/extraction remain proposed. Before candidate live calibration, separately
  scope upload/readback and initial stopped/bounded protocol/stop verification.


## 2026-10-09: shared control, complete legacy capability review and charged-session readiness

- Completed the still-open broader src organization under the earlier explicit
  targeted-edit/move and offline-check authorizations. The user reiterated the
  missing reorganization and asked to be ready for calibration/exploration after
  charging, explicitly allowing calibration while exploring a relatively safe
  prepared area. No new hardware session was inferred from that instruction.
- Extracted one RoverConnection transport base into src/control/connection.py;
  moved motion, protocol and timed_camera there. CalibrationSession inherits the
  single owner and retains experiment policy/output records. Control imports no
  agent policy or data paths. Moved four PowerShell implementations to src/tools;
  old src/agent entry paths are parameter-forwarding compatibility scripts.
- Shared control refuses overlapping movement/pan, a second pending sensor and
  another thread's TCP access. N2/N3 may observe a drive; N100 retains priority.
  MotionSampler now drains its last outstanding IMU reply before returning to
  stopped sensing. Old-firmware retagged drive 'ok' cannot release an IMU read.
  This is per-connection ownership, not a cross-process lock or physical rest proof.
- Exploration accepts a frozen 1-3 forward/left/right action plan, PWM60/T200 only;
  default remains three forward pulses. It enforces action order/count, no reverse
  or power escalation, records direction/attempted pulses, refreshes stopped bias
  and retains calibration/capture evidence. Adaptive IMU favors gyro on turns.
  Echo comparisons restart after a turn instead of comparing different headings.
  Main agent selects later segments while disconnected; no general route planner,
  cliff classifier, metric pose or full room-coverage implementation is claimed.
- Expanded firmware review beyond obstacle/cliff functions: all application modes,
  drivers and commands, supporting-library APIs/used paths, ESP32 bridge/camera
  handlers/registered routes and decoded web UI. Coverage/limits and 13 groups of
  findings are in rover/firmware/legacy-review.txt. Important leads include checked
  combined IMU bursts/device time, camera capture's unconditional 150 ms wait,
  settings/timestamp provenance, wheel asymmetry/heading correction, explicit
  stop semantics, floor/echo calibration, local stop input and bounded bridge
  framing. Generic template/disabled-platform code is not claimed formally audited.
- Source review found motor direction_void=3 passed to bool directions (zero PWM
  stop does not select that STBY-low branch), and current unused N7 D1=1 comparing
  raw microseconds with 20. Current host uses raw D1=2. Candidate source/HEX was
  deliberately preserved; these are recorded future firmware decisions.
- Host records optional HTTP X-Timestamp as camera_timestamp. Header absence or
  arbitrary text remains compatible; it is not used as host time or exposure
  proof. Source provenance now hashes control, runtime, analysis and tools.
- Updated README, workflow, procedure, next-test, agent instructions, skill and
  launcher rule paths. The next runbook permits interleaved calibration/exploration
  after fresh stopped and initial drive/stop checks. Proposed session: preflight
  and three bounded segments, first one pulse then at most three each (seven
  PWM60/T200 pulses / 1,400 ms commanded maximum). This is a proposal for later
  live authorization; it is not an automatic session after charge completion.
- Passed 53 Python unit tests (12 more than firmware-task baseline), covering
  action sequencing, pending reply drain, camera metadata, bounded mixed plans
  and retained fault evidence, all with local fake/synthetic inputs.
- Passed 12 PowerShell reply checks and keyboard SelfTest. A new launcher check
  exercised four actual compatibility forwarders against inert sibling targets;
  direct invocation and pwsh -File both preserved mixed-action/native arguments
  and chat names with spaces. The Python command was replaced by an argument
  recorder before executing those copied launcher fixtures; no network occurred.
- Parsed 27 Python sources, 13 PowerShell sources and local rule syntax. Six Python
  module --help checks passed. Basic skill frontmatter and 24 local documentation
  links passed before the final README review link was added. The bundled skill
  validator was not rerun; its prior PyYAML-missing limitation remains. Some venv
  invocations printed the existing 'Failed to find real location' base-interpreter
  warning but completed with exit 0; no environment/package changes were made.
- Protected before/after inventory matched all 2,009 file paths/sizes/modification
  times under data, backups, vendor and firmware source/build/tests. This is a
  metadata comparison, not a byte-for-byte audit of all data. Separately matched
  all 15 candidate-manifest source SHA-256 values plus candidate/installed HEX
  hashes. No firmware rebuild, upload, rover connection/movement, package install,
  commit, push or subagent use occurred during this continuation.

### Superseded handoff before this continuation

Historical snapshot; proposed steps/old paths below are not current instructions
or new authorization. Current state is in handoff.txt.

```text
ELEGOO rover project handoff
Updated: October 9, 2026, America/New_York
Workspace: D:\projects\hyohakusha

RESUME
- Read AGENTS.md, this file, then rover/calibration/next-test.md.
- Completed the first three proposed firmware steps: UNO fixes, host fault
  handling, and offline build/checks. Candidate is NOT uploaded or live-verified.
  No dependency installation, rover connection, movement, commit or push.
- User also asked to prepare the broader source organization after firmware.
  The concrete move/extraction plan is in WORKFLOW.md; those moves are not done.
- Rover execution must be sequential: one TCP owner, one movement/pan action;
  IMU reads may observe motion and HTTP camera capture stays observation-only.
  One pending sensor request; N100 has priority. This is not a ban on parallel
  offline development. No subagents used for the firmware task.

HOST CHANGES TO VERIFY NEXT
- src/agent now contains runtime/, analysis/, tests/ plus the existing PowerShell
  entry paths. Invoke Python from root with -m src.agent.<package>.<module>.
- MotionSampler refuses >50 ms late starts, >500 ms old pre-motion camera
  evidence, pending IMU timeouts and >10 s bias at dispatch. N100 takes priority
  after delayed polling. These provisional host limits do not prove clearance.
- Send/receive brackets exclude later log-write time. Partial trials/telemetry
  survive faults; TCP closes even if stop/error logging fails. Camera manifests
  are detached snapshots and explicitly mark an unfinished worker.
- Validation excludes incomplete/rest-rejected trials, reports missing support
  and requires positive cleanup evidence. Old runs may lack cleanup events.
- Heading diagnostic uses full-gyro sensor-Z integration; 3D accel-overlap
  integration remains separate. Do not compare new medians to old ones as an
  unchanged method. euler.md removed; original function remains in backup.
- Empty map/reconstruction/session reservations removed. Repository skill:
  .agents/skills/rover-experiment/SKILL.md. Links/frontmatter inspected; bundled
  validator could not run because PyYAML is absent. Skill is available this chat.
- Prior cleanup verification: 35 tests, six module --help checks, 21 Python sources parsed,
  both launchers parsed, whitespace check. Protected inventory of 1,811 files
  matched by path/size/modification time; no byte-for-byte audit claimed.

CURRENT CAPABILITIES AND EVIDENCE
- UNO command map: N1 battery, N2 gyro, N3 accel, N4 timed drive, N5 absolute
  servo, N6 incremental pan, N7 ultrasound, N8 floor ADC, N100 stop.
- October 8 upload/read-back verified 20,416 flash bytes. Camera was not flashed;
  vendor camera source has not been proven identical to installed firmware.
- PowerShell manual tools retained. Calibration and fixed three-forward-pulse
  observation pilot use one Python TCP owner. No general search/pose runtime.
- Fresh stopped gyro bias and image/IMU rest gates live exercised. Timed HTTP
  camera worker records alongside IMU; host brackets are not acquisition times.
- Focused turn run 20261009011850801: eight PWM60/T200 trials; pre/post rest
  supported 8/8, active gyro gaps about 50-59 ms. Four held-out comparisons had
  median disagreement 0.588 nominal degrees. Scene-specific consistency only.
- Pilot 20261009011637215: three PWM60/T200 forward pulses, 600 ms commanded
  total; rest supported 3/3. No metric position or verified-free-space map.
- Historical live work had 18 offline tests plus compilation/whitespace checks.
  Current host verification is listed above; no new physical observations.
- Rover last received N100 and disconnected. Last recorded battery 7.655 V in
  run 20261009012243615; current battery and connectivity are unknown.

LIMITS AND ACCEPTED RULES
- Stop on N1 <7.0 V or invalid/missing battery. Accuracy is uncalibrated.
- Calibration remains partial: absolute heading/scale, translation, stop distance,
  camera intrinsics, ultrasound/floor thresholds and pose uncertainty unresolved.
- One TCP owner. No concurrent manual controller. No pan/blocking N7 during drive.
- User-provided flat/no-drop/safe-area assumptions are not measured guarantees.
  No user navigation fallback. Unknown required clearance blocks movement.
- No power increase or metric control based on nominal integration. Accel-derived
  distance and rest-constrained endpoints remain diagnostics.
- Additional packages and firmware work need explicit task authorization.
- One main agent; subagents only when explicitly requested.

FIRMWARE CANDIDATE: BUILT, NOT UPLOADED
- Candidate: rover/firmware/build/uno-candidate-20261009/uno.ino.hex.
  SHA-256 ddd2e5d196ebfc4506a9d82084e79dff958ff7493919c547f30d1734f041524a.
  Arduino AVR core 1.8.8: flash 19,762/32,256; global RAM 664/2,048 bytes.
  Compared with installed build: 654 fewer flash bytes, 130 fewer global bytes.
  Stack/heap usage is not measured. Build/uno installed artifacts are retained.
- N100 and explicit faults stop motor output before replying. N4 owns its timer
  and completion tag; expiry is checked around serial/sensor work. N5/N6/N7
  during a drive stop it and return drive_busy instead of blocking. N5 replies
  after its driver returns. N4 renewal used by the manual keyboard is retained
  in source; no new live verification is claimed.
- IMU identity/configuration readback, transaction status and all six bytes are
  checked. Ten initialized startup attempts; 10,000 us per-Wire-operation timeout.
  A read fault latches unready until board restart and successful init. N2/N3/N4
  then refuse. Removed unused startup bias calculation. Raw units/direct PWM,
  command IDs, servo limits, T=0 no-expiry and 9600-baud UART are retained.
- Faults: {H_error_reason} or {error_reason}; reasons imu_not_ready, imu_read,
  drive_busy, drive_direction, bad_json, frame_too_long. Python poll faults even
  for an unrelated tag, bypasses bias retries, and uses stop/disconnect cleanup.
  PowerShell shares src/control/rover-protocol.psm1; manual Move polls faults,
  keyboard disables/disconnects, and survey rejects them.
- Passed: UNO build; 10 production-timer compile-time assertions (including exact
  deadline, T=0 and millis wrap); 41 Python tests; 12 PowerShell reply checks;
  four changed PS sources parsed; keyboard SelfTest; two runtime --help checks;
  Intel HEX checksums/payload counts and whitespace check. See verification.json
  in the candidate folder and detailed journal record.
- No whole-firmware simulation or physical fault injection performed. Real I2C,
  UART/stop ordering, sensor behavior and physical stop timing remain unverified.
  The firmware currently installed still has the previously reviewed faults.

NEXT PROPOSED EXPERIMENT
- Source organization preparation is complete; implementation remains proposed
  in WORKFLOW.md. Before any candidate live experiment, separately scope its
  upload/readback and initial stopped/bounded protocol/stop verification.
- See rover/calibration/next-test.md: stopped preflight, then one focused
  eight-turn PWM60/T200 session with timed camera/adaptive IMU if authorized.
- First live run of the reorganized/fixed runtime: retain refusals and investigate
  changed timing/evidence before any additional session.
- Question: does the existing turn observation method repeat with usable timing,
  rest support and held-out consistency? No absolute calibration claim.
- Freeze settings before acquisition; analyze after disconnect. A failed gate ends
  the run; identify a specific change before retrying. Do not loosen thresholds.
- Independently validate heading/timing and translation before metric coordinates
  or larger motion. Accepted sequence: image-tool assessment (initial work done),
  drive calibration (partial), bounded search with captures, reconstruction.
  General exploration and reconstruction remain incomplete.

WHERE TO FIND DETAIL
- README.md: current setup, commands, hardware, tools and paths.
- WORKFLOW.md: scoped experiment workflow and stage decisions.
- rover/calibration/procedure.md: detailed gates and protocol.
- rover/calibration/results.md: historical quantitative results and run references.
- journal.md: completed-task records and verbatim archived handoffs.
- Data: data/20261009003013000 for calibration/pilot; data/20261008220100000 for
  earlier setup/image assessment. Keep original filenames and ignored data.
- .venv: Python 3.13.13; OpenCV/NumPy/Pillow/SciPy/scikit-image/Matplotlib imports
  previously verified. Use .venv\Scripts\python.exe; esptool stays separate.
- Rules permit selected command prefixes but do not authorize tasks. Current
  session rule loading remains unverified. Existing git.rules stays local.
```

# October 9, 2026: keyboard sensor, camera and pan panel

User authorized keyboard-controller updates for manual sensors, battery, camera
and pan, and separately authorized offline SelfTest/syntax execution. Calibration,
exploration launchers and recording were excluded by the user's clarification.
No rover connection, GUI launch, firmware change or installation performed.

Updated src/control/keyboard-rover.ps1: F5 reads N1/N2/N3/N7 D1=2 T30000 and
N8 D1=0/1/2 sequentially; F7 reads N1 alone. Sensor/pan requests stop/disarm
and share existing TCP, with unique tags, one pending reply and 2.5 s timeout.
Space/Escape cancels queued work, retaining pending reply drainage. Battery
invalid/nonfinite/below 7.0 V and firmware faults disconnect with best-effort Stop.
Battery is checked on demand. F8/F9 send signed N6 step (1-20 degrees); F10
sends N5 target (10-170 degrees). Acknowledgments are not position feedback.

F6 displays /capture JPEG, and the live checkbox repeats asynchronous HTTP-only
requests 500 ms after each completion. One request, 3 s timeout and 4 MiB response
limit; old bitmaps and decode streams are disposed. Errors stop live refresh and
label the last frame potentially stale. Images are displayed only, not saved.
Shortcut repeat suppression avoids repeated pan from one held function key.
Conflicting drive directions now disable driving as documented.

Checks actually run: pwsh -NoProfile -File ./src/control/keyboard-rover.ps1
-SelfTest passed direction/conflicting/released keys, request ordering,
pending-reply drainage and unique-tag checks. PowerShell Parser.ParseFile passed.
Source inspection matched command units and pan limits to existing tool/firmware.
These checks do not verify UI layout, HTTP image rendering or physical operation.
README and handoff updated with current usage and limits. Next check requires
separate GUI/live authorization; no calibration milestone changed.

# October 9, 2026: UNO upload attempt awaiting switch confirmation

User requested firmware upload and confirmed USB connection after UNO candidate
was identified. Detected COM3 with Arduino CLI. Candidate SHA-256 matched
ddd2e5d196ebfc4506a9d82084e79dff958ff7493919c547f30d1734f041524a.
Upload targeted arduino:avr:uno, saved uno-candidate-20261009/uno.ino.hex,
--verify --verbose. Sandbox attempt could not open COM3 (access denied).
Escalated attempt opened COM3 but failed bootloader synchronization after ten
resp=0x00 attempts, exit 1. No signature acceptance, flash write or verification
occurred. Asked user to set Upload-Cam switch to Upload before retrying.
No TCP, sensors, pan or wheel commands sent. Candidate remains undeployed.

# October 9, 2026: UNO upload completed

User confirmed Upload-Cam switch changed. Retried the same saved October 9 HEX
on COM3, arduino:avr:uno, --verify --verbose, outside sandbox with approval.
Avrdude accepted ATmega328P signature 1E 95 0F, wrote 19,762 flash bytes and
read-back verified all 19,762 bytes; exit 0. This supersedes undeployed status.
Candidate hash was verified against the manifest before the initial attempt:
ddd2e5d196ebfc4506a9d82084e79dff958ff7493919c547f30d1734f041524a.
EEPROM/camera were not written; retained the saved October 8 build and backups.
Updated README, firmware info/verification, handoff and next-test deployment facts.
No TCP sensor, pan, wheel, physical stop or fault-injection checks performed.
Next stage is separately scoped initial stopped/bounded protocol/stop validation.

# October 9, 2026: remove redundant keyboard battery control

User explicitly confirmed removal of both the Battery button and F7 shortcut.
Verified both existed before editing. Removed button construction/registration,
click handler, F7 dispatch/help and the battery-only request branch. Preserved
N1 battery reading/validation within Check sensors/F5. Updated README and handoff.
Verification: focused source read-back/reference search and whitespace inspection.
No tests, GUI restart or hardware commands performed for this removal.
