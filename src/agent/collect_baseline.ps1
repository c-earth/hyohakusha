<# Compatibility entry; implementation lives in src/tools/collect_baseline.ps1. #>
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{17}$')][string]$SessionTimestamp,
    [Parameter(Mandatory)][string]$ChatName,
    [string]$Address = '192.168.4.1',
    [ValidateRange(3,30)][int]$Samples = 12
)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot '../tools/collect_baseline.ps1') @PSBoundParameters
