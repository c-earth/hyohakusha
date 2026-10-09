<# Compatibility entry; implementation lives in src/tools/run_exploration.ps1. #>
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{17}$')][string]$SessionTimestamp,
    [Parameter(Mandatory)][string]$ChatName,
    [Parameter(Mandatory)][switch]$SafeAreaAssumed,
    [string]$Address = '192.168.4.1',
    [ValidatePattern('(?i)^(forward|left|right)(,(forward|left|right)){0,2}$')][string]$Actions = 'forward,forward,forward'
)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot '../tools/run_exploration.ps1') @PSBoundParameters
