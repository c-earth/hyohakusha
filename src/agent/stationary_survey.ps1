<#
Survey camera pan and raw ultrasound without wheel movement.
Inputs: session timestamp/name and optional rover address. Pan commands are
60,80,100,120,140,100,101,100 degrees (command units, not measured angles).
Outputs: capture JPEGs/manifest, timestamped control JSONL, raw echo samples.
Only N5 pan, N7 sensing, N100 stop and heartbeat writes are permitted by class.
#>
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{17}$')][string]$SessionTimestamp,
    [Parameter(Mandatory)][string]$ChatName,
    [string]$Address = '192.168.4.1'
)
$ErrorActionPreference = 'Stop'

class StationarySurvey {
    hidden [Net.Sockets.TcpClient]$Client
    hidden [Net.Sockets.NetworkStream]$Stream
    hidden [string]$EventsFile
    hidden [string]$CaptureDirectory
    hidden [string]$ManifestFile
    hidden [int]$Sequence = 0

    StationarySurvey([string]$root, [string]$timestamp, [string]$nameValue) {
        $sessionDirectory = Join-Path $root "data/$timestamp"
        $sessionInfo = Join-Path $sessionDirectory 'info.txt'
        if (-not (Test-Path -LiteralPath $sessionInfo) -or
            (Get-Content -LiteralPath $sessionInfo -Raw).TrimEnd("`r", "`n") -cne $nameValue) {
            throw 'Create/verify session metadata before survey.'
        }
        $stampValue = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId(
            [DateTimeOffset]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMddHHmmssfff')
        $this.CaptureDirectory = Join-Path $sessionDirectory "captures/$stampValue"
        $logDirectory = Join-Path $sessionDirectory "logs/$stampValue"
        New-Item -ItemType Directory -Path $this.CaptureDirectory, $logDirectory | Out-Null
        $this.EventsFile = Join-Path $logDirectory 'events.jsonl'
        $this.ManifestFile = Join-Path $this.CaptureDirectory 'frames.csv'
        'file,pan_command_degrees,request_utc,received_utc' | Set-Content -LiteralPath $this.ManifestFile
        Set-Content -LiteralPath (Join-Path $this.CaptureDirectory 'info.txt') -Value @(
            'Stationary camera-pan survey; no wheel movement.',
            'N5 pan commands 60,80,100,120,140,100,101,100; finally restore 100.',
            'Three raw N7 echoes per view. Command angle is not position feedback.',
            'Host request/receipt timing only; no measured exposure or physical pose.'
        )
        Set-Content -LiteralPath (Join-Path $logDirectory 'info.txt') -Value 'Stationary survey: N5/N7/N100/heartbeat, tagged raw replies; no N4.'
    }

    [void] Event([string]$kindValue, [hashtable]$payloadValue) {
        @{utc=[DateTime]::UtcNow.ToString('o'); kind=$kindValue; payload=$payloadValue} |
            ConvertTo-Json -Depth 6 -Compress | Add-Content -LiteralPath $this.EventsFile -Encoding utf8
    }

    [void] WriteMessage([string]$messageValue) {
        $messageBytes = [Text.Encoding]::ASCII.GetBytes($messageValue)
        $this.Stream.Write($messageBytes, 0, $messageBytes.Length)
        $this.Event('send', @{message=$messageValue})
    }

    [void] WaitWithHeartbeat([int]$milliseconds) {
        $waitTimer = [Diagnostics.Stopwatch]::StartNew()
        do {
            $this.WriteMessage('{Heartbeat}')
            Start-Sleep -Milliseconds ([Math]::Min(100, [Math]::Max(1, $milliseconds - [int]$waitTimer.ElapsedMilliseconds)))
        } while ($waitTimer.ElapsedMilliseconds -lt $milliseconds)
    }

    [string] Request([hashtable]$commandValue) {
        if ($commandValue.N -notin @(5,7,100)) { throw 'Survey refuses movement or unrelated command.' }
        $this.Sequence++
        $tagValue = "survey$($this.Sequence)"
        $commandValue.H = $tagValue
        $this.WriteMessage(($commandValue | ConvertTo-Json -Compress))
        $replyTimer = [Diagnostics.Stopwatch]::StartNew()
        $bufferValue = ''
        $heartbeatAt = -500
        while ($replyTimer.ElapsedMilliseconds -lt 2500) {
            if ($replyTimer.ElapsedMilliseconds - $heartbeatAt -ge 400) {
                $this.WriteMessage('{Heartbeat}')
                $heartbeatAt = [int]$replyTimer.ElapsedMilliseconds
            }
            if ($this.Client.Client.Poll(0, [Net.Sockets.SelectMode]::SelectRead) -and $this.Client.Available -eq 0) {
                throw 'Peer closed TCP connection.'
            }
            while ($this.Stream.DataAvailable) {
                $byteValue = $this.Stream.ReadByte()
                if ($byteValue -lt 0) { throw 'Peer closed TCP connection.' }
                $bufferValue += [char]$byteValue
                if ($byteValue -eq 125) {
                    $this.Event('receive', @{message=$bufferValue})
                    if ($commandValue.N -eq 100 -and $bufferValue -eq '{ok}') { return 'ok' }
                    if ($bufferValue -match ('\{' + [regex]::Escape($tagValue) + '_([^}]+)\}')) { return $Matches[1] }
                    $bufferValue = ''
                }
            }
            Start-Sleep -Milliseconds 5
        }
        throw "No tagged reply for command $($commandValue.N)"
    }

    [void] Run([string]$addressValue) {
        $this.Client = [Net.Sockets.TcpClient]::new()
        try {
            $pendingValue = $this.Client.ConnectAsync($addressValue, 100)
            if (-not $pendingValue.Wait(3000)) { throw 'Connection timeout.' }
            $this.Stream = $this.Client.GetStream()
            $this.Stream.WriteTimeout = 1500
            $this.Event('start', @{address=$addressValue; movement=$false})
            if ($this.Request(@{N=100}) -ne 'ok') { throw 'Unexpected stop reply.' }
            $frameIndex = 0
            foreach ($angleValue in @(60,80,100,120,140,100,101,100)) {
                if ($this.Request(@{N=5;D1=1;D2=$angleValue}) -ne 'ok') { throw 'Unexpected pan reply.' }
                $this.WaitWithHeartbeat(650)
                $echoValues = @()
                for ($sampleIndex=0; $sampleIndex -lt 3; $sampleIndex++) {
                    $echoValue = $this.Request(@{N=7;D1=2;T=30000})
                    if ($echoValue -notmatch '^\d+$' -or [long]$echoValue -gt 30000) { throw 'Invalid raw echo.' }
                    $echoValues += [long]$echoValue
                    $this.WaitWithHeartbeat(70)
                }
                $fileValue = 'view-{0:D3}-pan{1:D3}.jpg' -f $frameIndex,$angleValue
                $requestUtc = [DateTime]::UtcNow.ToString('o')
                $this.WriteMessage('{Heartbeat}')
                Invoke-WebRequest -Uri "http://$addressValue/capture" -TimeoutSec 2 -OutFile (Join-Path $this.CaptureDirectory $fileValue)
                $receivedUtc = [DateTime]::UtcNow.ToString('o')
                $this.WriteMessage('{Heartbeat}')
                $imageBytes = [IO.File]::ReadAllBytes((Join-Path $this.CaptureDirectory $fileValue))
                if ($imageBytes.Length -lt 4 -or $imageBytes[0] -ne 255 -or $imageBytes[1] -ne 216) { throw 'Invalid JPEG.' }
                "$fileValue,$angleValue,$requestUtc,$receivedUtc" | Add-Content -LiteralPath $this.ManifestFile
                $this.Event('view', @{file=$fileValue; pan_command=$angleValue; ultrasound_us=$echoValues;
                    request_utc=$requestUtc; received_utc=$receivedUtc; zero_means_unknown=$true})
                Write-Host "Pan $angleValue echoes(us): $echoValues"
                $frameIndex++
            }
            $this.Event('complete', @{frames=$frameIndex; movement=$false})
        } catch {
            $this.Event('failure', @{message=$_.Exception.Message})
            throw
        } finally {
            if ($null -ne $this.Stream) {
                try {
                    $this.Request(@{N=100}) | Out-Null
                    $this.Request(@{N=5;D1=1;D2=100}) | Out-Null
                    $this.WaitWithHeartbeat(650)
                    $this.Request(@{N=100}) | Out-Null
                    $this.Event('cleanup', @{stop_sent=$true; restore_command=100; physical_rest_verified=$false})
                } catch { $this.Event('cleanup_failure', @{message=$_.Exception.Message}) }
            }
            $this.Client.Dispose()
            Write-Host "Survey captures: $($this.CaptureDirectory)"
        }
    }
}

$projectDirectory = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$survey = [StationarySurvey]::new($projectDirectory, $SessionTimestamp, $ChatName)
$survey.Run($Address)
