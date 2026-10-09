using module ../../control/rover-protocol.psm1

# Offline protocol checks; only the manual reply-reader function is loaded.
# Its stream and heartbeat writer are fakes; no controller or TCP is started.
$ErrorActionPreference = 'Stop'

class TestReplyStream {
    [bool]$DataAvailable
    hidden [Collections.Generic.Queue[byte]]$Bytes

    TestReplyStream([string]$Reply) {
        $this.Bytes = [Collections.Generic.Queue[byte]]::new([Text.Encoding]::ASCII.GetBytes($Reply))
        $this.DataAvailable = $this.Bytes.Count -gt 0
    }

    [int] ReadByte() {
        $value = $this.Bytes.Dequeue()
        $this.DataAvailable = $this.Bytes.Count -gt 0
        return $value
    }
}

function Send-Rover([string]$Message) {
    if ($Message -ne '{Heartbeat}') { throw 'Reply-reader test attempted a control command.' }
}

$passed = 0
foreach ($frame in @('{Heartbeat}', '{ok}', '{c1_ok}', '{c2_-32768,0,32767}', '{battery_v_7.500}')) {
    [RoverReply]::ThrowIfFault($frame)
    $passed++
}
foreach ($frame in @('{move_error_imu_not_ready}', '{gyro_raw_xyz_error_imu_read}', '{error_bad_json}', '{pan_step_error_drive_busy}')) {
    $raised = $false
    try { [RoverReply]::ThrowIfFault($frame) }
    catch {
        if ($_.Exception.Message -notlike '*Firmware fault*') { throw }
        $raised = $true
    }
    if (-not $raised) { throw "Fault accepted: $frame" }
    $passed++
}
$manualPath = Join-Path $PSScriptRoot '../../tools/rover.ps1'
$parseErrors = $null
$parseTokens = $null
$manualAst = [Management.Automation.Language.Parser]::ParseFile($manualPath, [ref]$parseTokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Manual tool parse failed.' }
$reader = $manualAst.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Read-Rover' }, $true)
if ($null -eq $reader) { throw 'Manual reply reader not found.' }
. ([scriptblock]::Create($reader.Extent.Text))

$stream = [TestReplyStream]::new('{Heartbeat}{gyro_1,2,3}')
if ((Read-Rover 'gyro' 200) -ne '1,2,3') { throw 'Manual success reply changed.' }
$passed++
foreach ($frame in @('{gyro_error_imu_read}', '{old_drive_error_imu_not_ready}')) {
    $stream = [TestReplyStream]::new($frame)
    $raised = $false
    try { Read-Rover 'gyro' 200 | Out-Null }
    catch {
        if ($_.Exception.Message -notlike '*Firmware fault*') { throw }
        $raised = $true
    }
    if (-not $raised) { throw 'Manual reader ignored a firmware fault.' }
    $passed++
}
Write-Output "$passed PowerShell reply checks passed."
