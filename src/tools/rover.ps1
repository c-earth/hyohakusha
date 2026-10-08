param(
    [ValidateSet('Sensors','Record','Move','Stop','PanTest','FinePanTest')][string]$Action = 'Sensors',
    [string]$Address = '192.168.4.1',
    [ValidateRange(1,3600)][int]$Seconds = 10,
    [ValidateRange(1,10)][int]$FramesPerSecond = 2,
    [ValidateSet('Forward','Backward','Left','Right')][string]$Direction = 'Forward',
    [ValidateRange(1,100)][int]$Speed = 60,
    [ValidateRange(50,500)][int]$DurationMs = 200,
    [switch]$EnableMovement
)
$ErrorActionPreference = 'Stop'
function New-CaptureFolder {
    $stamp = [TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow,
        [TimeZoneInfo]::FindSystemTimeZoneById('Eastern Standard Time')).ToString('yyyyMMddHHmmssfff')
    return Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) "data/captures/$stamp"
}
if ($Action -eq 'Record') {
    $folder = New-CaptureFolder
    New-Item -ItemType Directory -Path $folder | Out-Null
    Set-Content -LiteralPath (Join-Path $folder 'info.txt') -Value 'camera recording'
    $manifest = Join-Path $folder 'frames.csv'
    'file,request_utc,received_utc' | Set-Content $manifest
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $index = 0
    while ($timer.Elapsed.TotalSeconds -lt $Seconds) {
        $start = [DateTime]::UtcNow.ToString('o')
        $name = 'frame-{0:D6}.jpg' -f $index
        $path = Join-Path $folder $name
        Invoke-WebRequest -Uri "http://$Address/capture" -TimeoutSec 5 -OutFile $path
        $bytes = [IO.File]::ReadAllBytes($path)
        if ($bytes.Length -lt 4 -or $bytes[0] -ne 255 -or $bytes[1] -ne 216) { throw 'Camera did not return a JPEG.' }
        "$name,$start,$([DateTime]::UtcNow.ToString('o'))" | Add-Content $manifest
        $index++
        Start-Sleep -Milliseconds ([int](1000 / $FramesPerSecond))
    }
    Write-Output "Saved $index images to $folder (timestamps are computer receipt times, not camera exposure times)."
    return
}
if ($Action -eq 'Move' -and -not $EnableMovement) { throw 'Movement requires -EnableMovement. First verify sensor communication and clear the surrounding floor.' }
$client = [Net.Sockets.TcpClient]::new()
try {
    $pending = $client.ConnectAsync($Address,100)
    if (-not $pending.Wait(3000)) { throw 'TCP port 100 connection timed out.' }
    $stream = $client.GetStream()
    $stream.WriteTimeout = 2000
    function Send-Rover([string]$message) {
        $data = [Text.Encoding]::ASCII.GetBytes($message)
        $stream.Write($data,0,$data.Length)
    }
    function Read-Rover([string]$tag) {
        $timer = [Diagnostics.Stopwatch]::StartNew()
        $buffer = ''
        $lastHeartbeat = -1000
        while ($timer.ElapsedMilliseconds -lt 2500) {
            if ($timer.ElapsedMilliseconds - $lastHeartbeat -ge 500) {
                Send-Rover '{Heartbeat}'
                $lastHeartbeat = $timer.ElapsedMilliseconds
            }
            while ($stream.DataAvailable) {
                $value = $stream.ReadByte()
                if ($value -lt 0) { throw 'Connection closed.' }
                $buffer += [char]$value
                if ($value -eq 125) {
                    if ($buffer -match ('\{' + [regex]::Escape($tag) + '_([^}]+)\}')) { return $Matches[1] }
                    $buffer = ''
                }
            }
            Start-Sleep -Milliseconds 10
        }
        throw "No response for $tag. Installed firmware may differ from the stock reference."
    }
    if ($Action -eq 'Sensors') {
        foreach ($item in @(@('ultrasound_cm',21,2),@('floor_left',22,0),@('floor_middle',22,1),@('floor_right',22,2))) {
            $tag = [string]$item[0]
            Send-Rover (@{N=$item[1];D1=$item[2];H=$tag} | ConvertTo-Json -Compress)
            $result = Read-Rover $tag
            Write-Output "$tag=$result"
        }
    } elseif ($Action -in @('PanTest','FinePanTest')) {
        $centerAngle = if ($Action -eq 'FinePanTest') { 100 } else { 90 }
        $panAngle = if ($Action -eq 'FinePanTest') { 101 } else { 100 }
        $folder = New-CaptureFolder
        New-Item -ItemType Directory -Path $folder | Out-Null
        Set-Content -LiteralPath (Join-Path $folder 'info.txt') -Value "camera pan test $centerAngle to $panAngle to $centerAngle"
        try {
            foreach ($step in @(@('center',$centerAngle),@('pan',$panAngle),@('return',$centerAngle))) {
                $tag = [string]$step[0]
                Send-Rover (@{N=5;D1=1;D2=$step[1];H=$tag} | ConvertTo-Json -Compress)
                $ack = Read-Rover $tag
                Write-Output "Requested $($step[1]) degrees: $ack"
                if ($ack -ne 'ok') { throw 'Unexpected servo acknowledgment.' }
                Start-Sleep -Milliseconds 700
                Send-Rover '{Heartbeat}'
                Invoke-WebRequest -Uri "http://$Address/capture" -TimeoutSec 2 -OutFile (Join-Path $folder "$tag.jpg")
                Send-Rover '{Heartbeat}'
            }
        } finally {
            # Best-effort return to the authorized reference even if capture fails.
            Send-Rover (@{N=5;D1=1;D2=$centerAngle;H='restore'} | ConvertTo-Json -Compress)
            Start-Sleep -Milliseconds 700
            Send-Rover '{"N":100}'
        }
        Write-Output "Pan test images saved to $folder. Acknowledgments are not angle measurements."
    } elseif ($Action -eq 'Stop') {
        Send-Rover '{"N":100}'
        Write-Output 'Standby command sent; physical stop has not been independently verified.'
    } elseif ($Action -eq 'Move') {
        $directions = @{Left=1;Right=2;Forward=3;Backward=4}
        Send-Rover (@{N=2;D1=$directions[$Direction];D2=$Speed;T=$DurationMs;H='move'} | ConvertTo-Json -Compress)
        Start-Sleep -Milliseconds ($DurationMs + 100)
        Send-Rover '{"N":100}'
        Write-Output 'Timed movement and standby commands sent; verify the physical result.'
    }
} finally {
    # Stock camera firmware also sends standby when the TCP connection closes.
    $client.Dispose()
}
