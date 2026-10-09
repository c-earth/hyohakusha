<# Compatibility entry; implementation lives in src/tools/stationary_survey.ps1. #>
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{17}$')][string]$SessionTimestamp,
    [Parameter(Mandatory)][string]$ChatName,
    [string]$Address = '192.168.4.1'
)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot '../tools/stationary_survey.ps1') @PSBoundParameters
