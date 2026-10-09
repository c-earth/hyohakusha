# ELEGOO rover project

This project connects a computer to an ELEGOO Smart Robot Car V4.0 for manual
control, sensor readings, camera capture, and camera pan tests. The longer-term
goal is AI-assisted exploration of an accessible surface and 3D reconstruction
of the interior visible to the camera. A fixed three-pulse forward observation
pilot is implemented. Autonomous room search, mapping, and 3D reconstruction
are not implemented yet.

## Hardware

- Arduino UNO controller, TB6612FNG motor driver, and MPU6050 IMU.
- ESP32-S3-WROOM-1 camera module, with 8 MB flash and 8 MB PSRAM.
- Forward camera and ultrasound sensor, plus downward floor/light sensors.
- Camera pan servo; no servo angle feedback or motor encoders have been established.

Camera access, sensor responses, camera pan/return, repeated short movement
responses and later image/IMU settling have been observed. Metric pose, absolute
sensor accuracy and physical stopping distance remain unverified.

## Project structure

```text
data/<session-start>/         Data grouped by chat session; info.txt is chat name
  captures/<capture-start>/   Camera images and capture metadata
  logs/                      Control logs
  analysis/<analysis-start>/ Offline diagnostics, summaries and source provenance
rover/
  calibration/camera.json      Provisional camera pan alignment
  firmware/
    info.txt                  Firmware notes and camera provenance
    src/uno/                  Modified UNO source, starting at uno.ino
    src/esp32/                Vendor S3 camera source, starting at esp32.ino
    build/uno/                flash.hex and eeprom.hex compiler outputs
    build/esp32/              flash.bin full camera flash readback
  backups/20261007183240988/
    info.txt                  Backup notes
    src/uno/                  Original vendor UNO source
    src/esp32/                Downloaded vendor S3 camera source
    build/uno/                Original UNO flash and EEPROM readbacks
    build/esp32/              Full camera flash readback
  vendor/                     ELEGOO manuals, examples, drivers, and models
src/
  control/keyboard-rover.ps1   Interactive keyboard controller
  tools/rover.ps1             Sensors, capture, movement, stop, and pan tests
tools/
  arduino/                    Local Arduino CLI, AVR core, libraries, and cache
  esptool/                    Local esptool packages and dependencies
README.md
```

## Connection setup

Use PowerShell 7 on Windows. Run the commands below from the project root.
Keyboard control uses Windows Forms and starts disconnected with driving disabled.

Connect the computer to the rover's Wi-Fi, set the Upload–Cam switch to Cam,
and close the ELEGOO control app before opening TCP control. The default rover
address is `192.168.4.1`; both scripts accept `-Address` to override it.
The downloaded camera source uses Wi-Fi channel 9.

The rover exposes HTTP `/status` and `/capture`, an MJPEG stream at
`http://192.168.4.1:81/stream`, and TCP control on port 100. The keyboard panel
does not include a camera viewer; view the stream separately.

## Keyboard driving

```powershell
pwsh -NoProfile -STA -File ./src/control/keyboard-rover.ps1
```

Click Connect, then Enable driving when the surrounding floor is clear.
Hold WASD or arrow keys to drive; release to stop. Space/Escape, losing window
focus, and closing the window stop and disable driving. Multiple directions stop.

Default motor PWM is 60, adjustable from 20 to 100. The controller renews
timed `N4`, `T=250` ms commands every 100 ms. Heartbeat loss disconnects control.
Firmware loop timing, network queues, and motor coasting affect physical stopping.
No automatic obstacle avoidance is implemented.

Check keyboard direction logic without connecting to the rover:

```powershell
pwsh -NoProfile -File ./src/control/keyboard-rover.ps1 -SelfTest
```

## Host command numbering

The modified UNO source and host scripts use this numbering:

| Command | Function |
|---|---|
| N1 | Battery voltage |
| N2 | Raw gyro XYZ |
| N3 | Raw accelerometer XYZ |
| N4 | Timed drive |
| N100 | Stop |
| N5 | Absolute servo |
| N6 | Incremental pan |
| N7 | Ultrasound |
| N8 | Floor sensor |

N100 is the stop command and matches the unchanged camera source's disconnect
command. This numbering is not built or uploaded; updated host scripts require
the updated UNO firmware. No alternate command IDs are retained.
Historical firmware records use old IDs.

## Command-line tools

```powershell
./src/tools/rover.ps1 -Action Sensors
./src/tools/rover.ps1 -Action Record -Seconds 10 -FramesPerSecond 2 -SessionTimestamp 20261008231700000 -ChatName 'Example chat'
./src/tools/rover.ps1 -Action Stop
```

`Sensors` requests raw ultrasound echo duration in microseconds and the three floor
sensor values. `-UltrasoundTimeoutUs` sets the requested timeout (1–1,000,000 µs;
default 30,000). The modified UNO source passes `T` from N7 requests directly
to the measurement handler, leaving validation to the host, and reports raw pulse duration
for `D1=2`; zero means timeout. These source changes have not been built or uploaded,
so the installed firmware still uses the earlier centimeter reply contract.
Built-in obstacle-avoidance and following modes have been removed from the
modified UNO source, including button, IR, and N101 selection paths. Line tracking
and leave-ground detection have also been removed, including N101 and N23 handlers.
N8 reads the selected floor sensor on request (`D1=0` left, `1` middle, `2` right)
and replies with its raw ADC value, leaving the current mode unchanged. Floor readings
are no longer cached or acquired each loop. Floor-triggered standby gyro calibration and heading
reference resets are removed; startup gyro calibration and direction-change heading
resets remain. These removals have not been built or uploaded.
N1 reads battery voltage on request and returns `{H_value}` in volts with three
fractional digits, leaving the current mode unchanged. It uses the existing
`ADC × 0.0375 × 1.08` conversion, whose accuracy is unverified. The Sensors action
includes this reading as `battery_v`; N1 is not yet built or uploaded.
N2 reads all three gyro axes in one register transaction and returns
`{H_x,y,z}` as signed raw counts in sensor X/Y/Z order. The Sensors action labels
this `gyro_raw_xyz`. No offset subtraction, rate conversion, calibration, yaw
integration, or mode change occurs. Sensor mounting axes and I2C read validity
are not established by this reply. N2 is not yet built or uploaded.
N3 reads all three accelerometer axes in one register transaction and returns
`{H_x,y,z}` as signed raw counts in sensor X/Y/Z order, including gravity's
contribution. The Sensors action labels this `accel_raw_xyz`. No conversion,
calibration, or mode change occurs. Mounting axes and read validity are unverified;
N3 is not yet built or uploaded.
IR remote handling has been removed from the modified UNO source: no receiver
initialization, polling, or remote command processing remains in the application.
Onboard button handling, its interrupt registration, and its driver have also been
removed from the modified UNO source. The repeated standby motor-stop loop step
has also been removed; N100 still explicitly stops the motors and selects standby.
These button changes have not been built or uploaded.
The three IRremote source/header files have been removed from active UNO source; vendor and backup copies remain. This removal has not been built
or uploaded.
The N7 status threshold retains its numeric value
and now compares raw microseconds in the modified source.
`Record` downloads JPEG frames. `Stop` sends the standby command.
The camera reference source sends standby when a TCP control connection closes,
so a sensor session may also put the rover in standby.

Short movement requires explicit enabling, a verified sensor connection, and
clear, flat floor:

```powershell
./src/tools/rover.ps1 -Action Move -Direction Forward -DurationMs 200 -Speed 60 -EnableMovement
```

Directions are `Forward`, `Backward`, `Left`, and `Right`. This tool accepts
PWM 1–100; `DurationMs` is an integer in milliseconds, defaults to 200, and has
no range validation. Firmware `T=0` bypasses timed expiry; the tool still sends
N100 after its duration wait. PWM is not measured velocity. The modified
UNO source uses `N4` for timed movement. Legacy N1 direct motor control, legacy N3 untimed
movement, and N110 clear-to-programming commands and their dedicated handlers
have been removed from the modified source; N100 stopping remains. These removals
have not been built or uploaded.
Legacy N4 independent PWM control and N102 rocker driving have also been removed,
including their handlers, mode state, and loop calls. N4 remains the host driving
command and N100 remains the stop command; N4 still bypasses expiry when `T=0`.
N4 forward/backward output now uses the requested PWM directly on both channels;
gyro correction and its 10–180 PWM clamp have been removed from driving. Host gyro
reads remain available. This source change has not been built or uploaded.
Legacy host LED commands N7, N8, and N105 and their handlers/state have been removed from
the modified UNO source. Automatic battery monitoring, low-battery warnings, and
standby LED animation have also been removed. N1 request-time battery readings,
and LED initialization remain. N100 only stops motors and selects standby; its LED clearing has been removed.
This removal has not been built or uploaded.
Heartbeat disconnect timing has not been safety-tested on the installed camera
firmware and does not replace the short movement duration.

Camera pan tests move the servo, capture three images, and attempt to restore
the starting command angle:

```powershell
./src/tools/rover.ps1 -Action PanTest -SessionTimestamp 20261008231700000 -ChatName 'Example chat'      # 90 -> 100 -> 90
./src/tools/rover.ps1 -Action FinePanTest -SessionTimestamp 20261008231700000 -ChatName 'Example chat'  # 100 -> 101 -> 100
```

## Calibration and capture data

The bounded calibration runner and its evidence requirements are documented in
[Calibration procedure](rover/calibration/procedure.md). It records repeated
N1–N8/N100 observations and short drive/early-stop trials through one TCP owner.
Run only in the safe calibration area assumed by the user. Its native-unit
measurements do not establish metric pose or autonomous exploration readiness.

```powershell
pwsh -NoProfile -File ./src/agent/run_calibration.ps1 -SessionTimestamp 20261009003013000 -ChatName 'Exploration calibration' -SafeAreaAssumed
# After assessing the initial response, compare 200 ms pulses at PWM 80:
pwsh -NoProfile -File ./src/agent/run_calibration.ps1 -SessionTimestamp 20261009003013000 -ChatName 'Exploration calibration' -SafeAreaAssumed -DurationMs 200 -Speed 80 -DriveOnly
.venv\Scripts\python.exe src/agent/assess_calibration.py data/<session>/logs/<run>
```

The modified UNO source adds N6 for pan-only incremental control:
`{"N":27,"D1":1,"H":"pan"}` increases the last commanded pan angle by 1 degree;
negative `D1` decreases it. The target is clamped to 10–170 degrees. Command state
starts at the startup angle (90 degrees) and is updated by N5 pan commands.
It is not position feedback. N6 waits 500 ms, detaches the servo, enters
programming mode, and sends `{H_ok}` after driver execution. N106 and its legacy
ten-degree-step handlers have been removed. N5 remains available.
The host tool exposes `-Action PanStep -PanStepDegrees 1` (default step 1;
host range -170 to 170). These changes have not been built or uploaded.

Camera pan alignment is recorded in `rover/calibration/camera.json`. The user
visually identified command 100 degrees as straight ahead; increasing command
angles turn left. This is provisional alignment, not a measured physical angle.
The recorded last command is historical and does not establish the current
servo position. Scripts do not load the calibration automatically.

Data is grouped under `data/<session-start-timestamp>/`, using New York local time
and the format `yyyyMMddHHmmssfff`. The session's `info.txt` contains the chat name.
For Record, PanTest and FinePanTest, pass `-SessionTimestamp` and `-ChatName`;
reuse both values for every capture in that chat. A different name for an existing
session is rejected before rover connection. The script does not discover chat
metadata automatically. Captures go under `captures/<capture-start-timestamp>/`
inside the session, with their own `info.txt` describing the capture purpose.
Control logs belong under the session's `logs/` folder; the rover tool does not
currently generate control logs. Existing data is grouped under
`data/20261008220100000/`, with session name `setup`.
Recording currently produces `frame-000000.jpg`, subsequent numbered
JPEGs, and `frames.csv` with `file`, `request_utc`, and `received_utc` columns.
Existing sessions also include a first frame named `frame000000.jpg` and pan-test
images named `center.jpg`, `pan.jpg`, and `return.jpg`.

CSV timestamps are computer request/receipt times in UTC, not camera exposure
times. Actual recording rate is lower than requested because downloads take time.

## Firmware and backups

The active UNO source was modified so `N5` camera pan commands accept 1-degree
steps. It was compiled, uploaded, and verified on October 7, 2026. Built-in modes
retain their original servo interface. Active `build/uno/flash.hex` is compiled
application firmware; active `eeprom.hex` is compiler output with no EEPROM data.

The backup at `rover/backups/20261007183240988/` contains the original vendor
UNO source and actual original UNO memory readbacks: 32 KB flash including the
bootloader and 1 KB EEPROM. Fuse and lock settings were not backed up.

The camera has not been flashed by this project. Both active and backup
`build/esp32/flash.bin` contain the same full 8 MB camera readback from offset 0,
including its bootloader, partition table, application, and stored data.
The downloaded S3 camera source has not been proven to match that readback.
The UNO and camera backup reads were taken at different times.

Vendor camera build settings are recorded in `rover/firmware/info.txt`:
ESP32S3 Dev Module, USB CDC On Boot enabled, 8 MB flash, 8M with SPIFFS
(3 MB APP/1.5 MB SPIFFS), and OPI PSRAM.

## Development tools and references

Arduino CLI is at `tools/arduino/arduino-cli/arduino-cli.exe`. Its configuration
is `tools/arduino/arduino-cli.yaml`, which uses absolute paths for this checkout.
The local installation includes AVR core 1.8.8, Servo 1.3.0, and FastLED 3.2.10.
No graphical Arduino IDE is installed as part of this project.

Esptool 5.4.0 and its dependencies are installed under `tools/esptool`.
Set `PYTHONPATH` to that directory and invoke `python -m esptool` with the
compatible Python runtime. Serial port assignments can change when boards reset
or enter download mode.

The retained vendor package is
`rover/vendor/ELEGOO Smart Robot Car Kit V4.0 2023.02.01/`.
The official reference repository is
[ELEGOO Smart Robot Car Kit V4.0](https://github.com/elegooofficial/ELEGOO-Smart-Robot-Car-Kit-V4.0).
