<#
Run a fixed three-pulse forward observation pilot in the assumed-safe area.
Inputs: session/name, explicit safe-area switch and optional IP. Outputs:
timestamped logs/images/observation JSON; no metric pose or autonomous room search.
#>
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{17}$')][string]$SessionTimestamp,
    [Parameter(Mandatory)][string]$ChatName,
    [Parameter(Mandatory)][switch]$SafeAreaAssumed,
    [string]$Address = '192.168.4.1'
)
$ErrorActionPreference = 'Stop'
if (-not $SafeAreaAssumed) { throw 'Pilot requires the user-assumed safe area.' }
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$stamp = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMddHHmmssfff')
& (Join-Path $root '.venv/Scripts/python.exe') (Join-Path $PSScriptRoot 'bounded_exploration.py') `
    --session $SessionTimestamp --name $ChatName --run-stamp $stamp --address $Address --safe-area-assumed
if ($LASTEXITCODE -ne 0) { throw "Bounded observation pilot exited $LASTEXITCODE" }
