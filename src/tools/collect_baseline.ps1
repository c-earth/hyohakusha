<#
Collect stationary sensor batches and JPEG frames using the existing rover tool.
Inputs: required session timestamp/name, optional address and sample count 3-30.
Outputs: timestamped JSONL events and sensor JSON under session logs; JPEGs under
captures. Each batch is sequential and owns TCP only for its invocation. No wheel
or servo command is issued. Sensor timestamps bracket a batch, not acquisition.
#>
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{17}$')][string]$SessionTimestamp,
    [Parameter(Mandatory)][string]$ChatName,
    [string]$Address = '192.168.4.1',
    [ValidateRange(3,30)][int]$Samples = 12
)
$ErrorActionPreference = 'Stop'

class BaselineRecorder {
    hidden [string]$ToolPath
    hidden [string]$SessionPath
    hidden [string]$LogPath
    hidden [string]$EventsPath

    BaselineRecorder([string]$projectRoot, [string]$timestamp, [string]$chatName) {
        [DateTime]::ParseExact($timestamp, 'yyyyMMddHHmmssfff', [Globalization.CultureInfo]::InvariantCulture) | Out-Null
        if ([string]::IsNullOrWhiteSpace($chatName)) { throw 'Chat name required.' }
        $this.ToolPath = Join-Path $projectRoot 'src/tools/rover.ps1'
        $this.SessionPath = Join-Path $projectRoot "data/$timestamp"
        $sessionInfo = Join-Path $this.SessionPath 'info.txt'
        if (Test-Path -LiteralPath $this.SessionPath) {
            if (-not (Test-Path -LiteralPath $sessionInfo) -or
                (Get-Content -LiteralPath $sessionInfo -Raw).TrimEnd("`r", "`n") -cne $chatName) {
                throw 'Existing session metadata does not match.'
            }
        } else {
            New-Item -ItemType Directory -Path $this.SessionPath | Out-Null
            Set-Content -LiteralPath $sessionInfo -Value $chatName -Encoding utf8
        }
        $runStamp = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId(
            [DateTimeOffset]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMddHHmmssfff')
        $this.LogPath = Join-Path $this.SessionPath "logs/$runStamp"
        New-Item -ItemType Directory -Path $this.LogPath | Out-Null
        $this.EventsPath = Join-Path $this.LogPath 'events.jsonl'
        Set-Content -LiteralPath (Join-Path $this.LogPath 'info.txt') -Encoding utf8 -Value @(
            'Stationary calibration baseline; no wheel or servo commands.',
            'Each Sensors batch brackets sequential N7, N8 x3, N1, N2, N3 reads.',
            'UTC timestamps bracket invocation; per-sensor acquisition times unknown.',
            'Sensor units: ultrasound us (zero timeout); floor ADC; battery estimated V; IMU raw signed XYZ.'
        )
    }

    [void] Event([string]$kind, [hashtable]$payload) {
        $entry = @{utc=[DateTime]::UtcNow.ToString('o'); kind=$kind; payload=$payload}
        Add-Content -LiteralPath $this.EventsPath -Value ($entry | ConvertTo-Json -Depth 8 -Compress) -Encoding utf8
    }

    [void] Run([string]$addressValue, [int]$sampleCount, [string]$sessionValue, [string]$nameValue) {
        $this.Event('start', @{address=$addressValue; samples=$sampleCount; movement=$false;
            tool_sha256=(Get-FileHash -LiteralPath $this.ToolPath -Algorithm SHA256).Hash})
        $batches = [Collections.Generic.List[object]]::new()
        try {
            for ($index = 0; $index -lt $sampleCount; $index++) {
                $beginUtc = [DateTime]::UtcNow.ToString('o')
                $this.Event('sensor_request', @{index=$index; action='Sensors'; ultrasound_timeout_us=30000})
                $responseLines = @(& pwsh -NoProfile -File $this.ToolPath -Action Sensors -Address $addressValue 2>&1)
                $exitValue = $LASTEXITCODE
                $endUtc = [DateTime]::UtcNow.ToString('o')
                $this.Event('sensor_response', @{index=$index; exit_code=$exitValue; output=@($responseLines | ForEach-Object {"$_"})})
                if ($exitValue -ne 0) { throw "Sensors failed at batch $index : $responseLines" }
                $values = @{}
                foreach ($responseLine in $responseLines) {
                    if ("$responseLine" -match '^([a-z_]+)=(.*)$') { $values[$Matches[1]] = $Matches[2] }
                }
                foreach ($keyValue in @('ultrasound_us','floor_left','floor_middle','floor_right','battery_v','gyro_raw_xyz','accel_raw_xyz')) {
                    if (-not $values.ContainsKey($keyValue)) { throw "Missing $keyValue" }
                }
                $batches.Add(@{index=$index; request_utc=$beginUtc; received_utc=$endUtc; readings=$values})
                Write-Output "Batch $index echo=$($values.ultrasound_us) us gyro=$($values.gyro_raw_xyz)"
                Start-Sleep -Milliseconds 150
            }
            $this.Event('capture_request', @{seconds=3; frames_per_second=2; action='Record'})
            $captureResponse = @(& pwsh -NoProfile -File $this.ToolPath -Action Record -Seconds 3 -FramesPerSecond 2 `
                -Address $addressValue -SessionTimestamp $sessionValue -ChatName $nameValue 2>&1)
            $captureExit = $LASTEXITCODE
            $this.Event('capture_response', @{exit_code=$captureExit; output=@($captureResponse | ForEach-Object {"$_"})})
            if ($captureExit -ne 0) { throw "Capture failed: $captureResponse" }
            Write-Output $captureResponse
            $this.Event('complete', @{sensor_batches=$batches.Count; movement=$false})
        } catch {
            $this.Event('failure', @{message=$_.Exception.Message; movement=$false})
            throw
        } finally {
            ConvertTo-Json -InputObject $batches.ToArray() -Depth 6 |
                Set-Content -LiteralPath (Join-Path $this.LogPath 'sensors.json') -Encoding utf8
            Write-Output "Baseline logs: $($this.LogPath)"
        }
    }
}

$projectDirectory = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$recorder = [BaselineRecorder]::new($projectDirectory, $SessionTimestamp, $ChatName)
$recorder.Run($Address, $Samples, $SessionTimestamp, $ChatName)
