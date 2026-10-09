<# Offline durable coordinator memory. This command never operates the rover. #>
param(
    [Parameter(Mandatory)][string]$State,
    [Parameter(Mandatory)][ValidateSet('create','status','import-run','request','update-request','worker','reserve')][string]$Action,
    [string]$Session, [string]$Objective, [int]$MaxPulses, [int]$MaxSegments,
    [string]$Deadline, [int]$MaxEchoRetries = 3,
    [string]$Run, [string]$ReservationId, [string]$Id, [string]$Description, [string]$RequestStatus = 'pending',
    [string]$Assignment, [string]$WorkerStatus = 'idle', [string]$Actions
)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$arguments = @('-m','src.agent.analysis.workflow_state','--state',$State,$Action)
switch ($Action) {
    'create' {
        $arguments += @('--session',$Session,'--objective',$Objective,'--max-pulses',"$MaxPulses",'--max-segments',"$MaxSegments",'--max-echo-retries',"$MaxEchoRetries")
        if ($Deadline) { $arguments += @('--deadline',$Deadline) }
    }
    'import-run' {
        $arguments += @('--run',$Run)
        if ($ReservationId) { $arguments += @('--reservation-id',$ReservationId) }
    }
    'request' { $arguments += @('--id',$Id,'--description',$Description,'--status',$RequestStatus) }
    'update-request' { $arguments += @('--id',$Id,'--description',$Description,'--status',$RequestStatus) }
    'worker' { $arguments += @('--id',$Id,'--assignment',$Assignment,'--status',$WorkerStatus) }
    'reserve' { $arguments += @('--id',$Id,'--actions',$Actions) }
}
Push-Location -LiteralPath $root
try {
    & (Join-Path $root '.venv/Scripts/python.exe') @arguments
    if ($LASTEXITCODE -ne 0) { throw "Offline state command exited $LASTEXITCODE" }
} finally { Pop-Location }
