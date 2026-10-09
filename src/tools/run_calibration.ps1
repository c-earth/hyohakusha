<#
Run bounded native-unit calibration through one Python TCP owner.
Inputs: session timestamp/name and explicit SafeAreaAssumed switch; optional IP.
Outputs: JSONL control evidence, timestamped JPEGs and trial manifest in session.
#>
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{17}$')][string]$SessionTimestamp,
    [Parameter(Mandatory)][string]$ChatName,
    [Parameter(Mandatory)][switch]$SafeAreaAssumed,
    [string]$Address = '192.168.4.1',
    [ValidateSet(100,200)][int]$DurationMs = 100,
    [ValidateSet(60,80)][int]$Speed = 60,
    [switch]$DriveOnly,
    [switch]$BatteryOnly,
    [switch]$GyroCalibrationOnly,
    [switch]$TimedCamera,
    [ValidateRange(1,3)][int]$Repeats = 3,
    [ValidateSet('alternate','gyro-focus','adaptive')][string]$ImuPlan = 'adaptive',
    [switch]$TurnOnly,
    [switch]$ForwardOnly
)
$ErrorActionPreference = 'Stop'
if (-not $SafeAreaAssumed) { throw 'Safe-area assumption required for this calibration.' }
if ($TurnOnly -and $ForwardOnly) { throw 'TurnOnly and ForwardOnly cannot be combined.' }
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$runStamp = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMddHHmmssfff')
Push-Location -LiteralPath $root
try {
    & (Join-Path $root '.venv/Scripts/python.exe') -m src.agent.runtime.calibration_session `
        --session $SessionTimestamp --name $ChatName --address $Address --run-stamp $runStamp --duration-ms $DurationMs --pwm $Speed --drive-only ([int]$DriveOnly.IsPresent) --battery-only ([int]$BatteryOnly.IsPresent) --gyro-only ([int]$GyroCalibrationOnly.IsPresent) --timed-camera ([int]$TimedCamera.IsPresent) --repeats $Repeats --imu-plan $ImuPlan --turn-only ([int]$TurnOnly.IsPresent) --forward-only ([int]$ForwardOnly.IsPresent) --safe-area-assumed
    if ($LASTEXITCODE -ne 0) { throw "Calibration exited $LASTEXITCODE" }
} finally {
    Pop-Location
}
