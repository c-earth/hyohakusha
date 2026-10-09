# ELEGOO rover project

This project connects a computer to an ELEGOO Smart Robot Car V4.0 for manual
control, sensor readings, camera capture, and camera pan tests. The longer-term
goal is AI-assisted exploration of an accessible surface and 3D reconstruction
of the interior visible to the camera. Autonomous exploration, mapping, and
3D reconstruction are not implemented yet.

## Hardware

- Arduino UNO controller, TB6612FNG motor driver, and MPU6050 IMU.
- ESP32-S3-WROOM-1 camera module, with 8 MB flash and 8 MB PSRAM.
- Forward camera and ultrasound sensor, plus downward floor/light sensors.
- Camera pan servo; no servo angle feedback or motor encoders have been established.

Camera access, sensor responses, and camera pan/return have been verified.
Movement commands are implemented in the scripts; their physical results and
stopping behavior require verification on the rover.

## Project structure

```text
data/captures/                 Camera capture sessions
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
timed `N=2`, `T=250` ms commands every 100 ms. Heartbeat loss disconnects control.
Firmware loop timing, network queues, and motor coasting affect physical stopping.
No automatic obstacle avoidance is implemented.

Check keyboard direction logic without connecting to the rover:

```powershell
pwsh -NoProfile -File ./src/control/keyboard-rover.ps1 -SelfTest
```

## Command-line tools

```powershell
./src/tools/rover.ps1 -Action Sensors
./src/tools/rover.ps1 -Action Record -Seconds 10 -FramesPerSecond 2
./src/tools/rover.ps1 -Action Stop
```

`Sensors` requests raw ultrasound echo duration in microseconds and the three floor
sensor values. `-UltrasoundTimeoutUs` sets the requested timeout (1–1,000,000 µs;
default 30,000). The modified UNO source passes `T` from N21 requests directly
to the measurement handler, leaving validation to the host, and reports raw pulse duration
for `D1=2`; zero means timeout. These source changes have not been built or uploaded,
so the installed firmware still uses the earlier centimeter reply contract.
Built-in obstacle-avoidance and following modes have been removed from the
modified UNO source, including button, IR, and N101 selection paths. Line tracking
and leave-ground detection have also been removed, including N101 and N23 handlers.
N22 reads the selected floor sensor on request (`D1=0` left, `1` middle, `2` right)
and replies with its raw ADC value, leaving the current mode unchanged. Floor readings
are no longer cached or acquired each loop. Floor-triggered standby gyro calibration and heading
reference resets are removed; startup gyro calibration and direction-change heading
resets remain. These removals have not been built or uploaded.
N24 reads battery voltage on request and returns `{H_value}` in volts with three
fractional digits, leaving the current mode unchanged. It uses the existing
`ADC × 0.0375 × 1.08` conversion, whose accuracy is unverified. The Sensors action
includes this reading as `battery_v`; N24 is not yet built or uploaded.
N25 reads all three gyro axes in one register transaction and returns
`{H_x,y,z}` as signed raw counts in sensor X/Y/Z order. The Sensors action labels
this `gyro_raw_xyz`. No offset subtraction, rate conversion, calibration, yaw
integration, or mode change occurs. Sensor mounting axes and I2C read validity
are not established by this reply. N25 is not yet built or uploaded.
N26 reads all three accelerometer axes in one register transaction and returns
`{H_x,y,z}` as signed raw counts in sensor X/Y/Z order, including gravity's
contribution. The Sensors action labels this `accel_raw_xyz`. No conversion,
calibration, or mode change occurs. Mounting axes and read validity are unverified;
N26 is not yet built or uploaded.
IR remote handling has been removed from the modified UNO source: no receiver
initialization, polling, or remote command processing remains in the application.
The bundled IRremote library files are retained. This removal has not been built
or uploaded.
The N21 status threshold retains its numeric value
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
PWM 1–100 and duration 50–500 ms. PWM is not measured velocity. The downloaded
UNO source retains `N=2` for timed movement. N1 direct motor control, N3 untimed
movement, and N110 clear-to-programming commands and their dedicated handlers
have been removed from the modified source; N100 stopping remains. These removals
have not been built or uploaded.
N4 independent PWM control and N102 rocker driving have also been removed,
including their handlers, mode state, and loop calls. N2 remains the host driving
command and N100 remains the stop command; N2 still bypasses expiry when `T=0`.
N2 forward/backward output now uses the requested PWM directly on both channels;
gyro correction and its 10–180 PWM clamp have been removed from driving. Host gyro
reads remain available. This source change has not been built or uploaded.
Host LED commands N7, N8, and N105 and their handlers/state have been removed from
the modified UNO source. Automatic battery warnings and standby LED behavior remain.
This removal has not been built or uploaded.
Heartbeat disconnect timing has not been safety-tested on the installed camera
firmware and does not replace the short movement duration.

Camera pan tests move the servo, capture three images, and attempt to restore
the starting command angle:

```powershell
./src/tools/rover.ps1 -Action PanTest      # 90 -> 100 -> 90
./src/tools/rover.ps1 -Action FinePanTest  # 100 -> 101 -> 100
```

## Calibration and capture data

The modified UNO source adds N27 for pan-only incremental control:
`{"N":27,"D1":1,"H":"pan"}` increases the last commanded pan angle by 1 degree;
negative `D1` decreases it. The target is clamped to 10–170 degrees. Command state
starts at the startup angle (90 degrees) and is updated by N5 pan commands.
It is not position feedback. N27 waits 500 ms, detaches the servo, enters
programming mode, and sends `{H_ok}` after driver execution. N106 and its legacy
ten-degree-step handlers have been removed. N5 remains available.
The host tool exposes `-Action PanStep -PanStepDegrees 1` (default step 1;
host range -170 to 170). These changes have not been built or uploaded.

Camera pan alignment is recorded in `rover/calibration/camera.json`. The user
visually identified command 100 degrees as straight ahead; increasing command
angles turn left. This is provisional alignment, not a measured physical angle.
The recorded last command is historical and does not establish the current
servo position. Scripts do not load the calibration automatically.

Capture sessions are saved under `data/captures/yyyyMMddHHmmssfff/`, using
New York local time for folder names. Each session includes `info.txt` describing
its purpose. Recording currently produces `frame-000000.jpg`, subsequent numbered
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
