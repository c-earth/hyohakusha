<#
Run up to three sequential PWM60/T200 observations in the assumed-safe area.
Inputs: session/name, explicit safe-area switch and optional IP. Outputs:
timestamped logs/images/observation JSON; no metric pose or autonomous room search.
#>
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{17}$')][string]$SessionTimestamp,
    [Parameter(Mandatory)][string]$ChatName,
    [Parameter(Mandatory)][switch]$SafeAreaAssumed,
    [string]$Address = '192.168.4.1',
    [ValidatePattern('(?i)^(forward|left|right)(,(forward|left|right)){0,2}$')][string]$Actions = 'forward,forward,forward'
)
$ErrorActionPreference = 'Stop'
if (-not $SafeAreaAssumed) { throw 'Pilot requires the user-assumed safe area.' }
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$stamp = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMddHHmmssfff')
$actionNames = $Actions.ToLowerInvariant().Split(',')
Push-Location -LiteralPath $root
try {
    & (Join-Path $root '.venv/Scripts/python.exe') -m src.agent.runtime.bounded_exploration `
        --session $SessionTimestamp --name $ChatName --run-stamp $stamp --address $Address --safe-area-assumed --actions @actionNames
    if ($LASTEXITCODE -ne 0) { throw "Bounded observation pilot exited $LASTEXITCODE" }
} finally {
    Pop-Location
}
