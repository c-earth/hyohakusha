<# Compatibility entry; implementation lives in src/tools/run_calibration.ps1. #>
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
    [switch]$TurnOnly
)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot '../tools/run_calibration.ps1') @PSBoundParameters
