<# Offline saved-data summary. No rover connection or movement. #>
param(
    [Parameter(Mandatory)][string]$Session,
    [string]$LastRun,
    [string]$Output
)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Push-Location -LiteralPath $root
try {
    $briefArguments = @('-m', 'src.agent.analysis.session_brief', $Session)
    if ($LastRun) { $briefArguments += @('--last-run', $LastRun) }
    if ($Output) { $briefArguments += @('--output', $Output) }
    & (Join-Path $root '.venv/Scripts/python.exe') @briefArguments
    if ($LASTEXITCODE -ne 0) { throw "Offline session brief exited $LASTEXITCODE" }
} finally {
    Pop-Location
}
