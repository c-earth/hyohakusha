<# Offline saved-segment review. Report creation never grants movement permission. #>
param(
    [Parameter(Mandatory)][string]$Session,
    [Parameter(Mandatory)][ValidatePattern('^\d+$')][string]$Run,
    [Parameter(Mandatory)][string]$Output
)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Push-Location -LiteralPath $root
try {
    & (Join-Path $root '.venv/Scripts/python.exe') -m src.agent.analysis.review_segment $Session --run $Run --output $Output
    if ($LASTEXITCODE -ne 0) { throw "Offline review exited $LASTEXITCODE" }
} finally {
    Pop-Location
}
