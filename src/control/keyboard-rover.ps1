using module ./rover-protocol.psm1

param([string]$Address = '192.168.4.1', [switch]$SelfTest)
$ErrorActionPreference = 'Stop'

class KeyboardRequestQueue {
    # Owns sequential stopped requests; only the form timer sends/polls TCP.
    [Collections.Generic.Queue[hashtable]]$Items = [Collections.Generic.Queue[hashtable]]::new()
    [hashtable]$Pending = $null
    [DateTime]$SentAt
    [int]$Sequence = 0

    [void] Clear() {
        $this.Items.Clear()
        $this.Pending = $null
    }

    [void] Add([string]$label, [hashtable]$command) {
        $this.Sequence++
        $command.H = "ui$($this.Sequence)"
        $this.Items.Enqueue(@{Label=$label; Command=$command})
    }

    [bool] Busy() {
        return $null -ne $this.Pending -or $this.Items.Count -gt 0
    }
}

class KeyboardCamera {
    # HTTP-only JPEG preview; one asynchronous request, no TCP commands.
    [Net.Http.HttpClient]$Client
    [object]$Task = $null
    [DateTime]$NextAt = [DateTime]::MinValue

    KeyboardCamera() {
        $this.Client = [Net.Http.HttpClient]::new()
        $this.Client.Timeout = [TimeSpan]::FromSeconds(3)
        $this.Client.MaxResponseContentBufferSize = 4194304
    }

    [void] Capture([string]$address) {
        if ($null -eq $this.Task) {
            $this.Task = $this.Client.GetByteArrayAsync("http://$address/capture")
        }
    }

    [void] Dispose() {
        $this.Client.Dispose()
    }
}

function Get-DriveDirection($Held) {
    $directions = @(@('W','Up',3),@('S','Down',4),@('A','Left',1),@('D','Right',2))
    $active = @($directions | Where-Object { $Held.Contains($_[0]) -or $Held.Contains($_[1]) })
    if ($active.Count -eq 1) { return [int]$active[0][2] }
    return 0 # Conflicting or multiple directions stop.
}
if ($SelfTest) {
    foreach ($case in @(@('W',3),@('S',4),@('A',1),@('D',2),@('Up',3))) {
        $held = [Collections.Generic.HashSet[string]]::new()
        [void]$held.Add($case[0])
        if ((Get-DriveDirection $held) -ne $case[1]) { throw 'Direction test failed' }
    }
    [void]$held.Add('S')
    if ((Get-DriveDirection $held) -ne 0) { throw 'Conflicting keys must stop' }
    $held.Clear()
    if ((Get-DriveDirection $held) -ne 0) { throw 'Released keys must stop' }
    $requests = [KeyboardRequestQueue]::new()
    $requests.Add('battery', @{N=1})
    $requests.Add('echo', @{N=7;D1=2;T=30000})
    if (-not $requests.Busy()) { throw 'Queued requests must block driving' }
    $requests.Pending = $requests.Items.Dequeue()
    $firstTag = $requests.Pending.Command.H
    if ($requests.Pending.Command.N -ne 1) { throw 'Request order changed' }
    $requests.Items.Clear()
    if (-not $requests.Busy()) { throw 'Stop must still drain a pending reply' }
    $requests.Clear()
    if ($requests.Busy()) { throw 'Disconnect must clear pending work' }
    $requests.Add('battery', @{N=1})
    if ($requests.Items.Peek().Command.H -eq $firstTag) { throw 'Request tags must not be reused' }
    Write-Output 'Direction, conflicting/released keys, request ordering, pending-drain and unique-tag checks passed.'
    return
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$script:client = $null
$script:stream = $null
$script:held = [Collections.Generic.HashSet[string]]::new()
$script:shortcuts = [Collections.Generic.HashSet[string]]::new()
$script:receiving = ''
$script:lastHeartbeat = [DateTime]::MinValue
$script:sentHeartbeat = [DateTime]::MinValue
$script:wasMoving = $false
$script:requests = [KeyboardRequestQueue]::new()
$script:camera = [KeyboardCamera]::new()

$form = [Windows.Forms.Form]::new()
$form.Text = 'ELEGOO keyboard drive'
$form.ClientSize = [Drawing.Size]::new(1000,610)
$form.KeyPreview = $true
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$connect = [Windows.Forms.Button]::new()
$connect.Text = 'Connect'
$connect.SetBounds(20,20,110,35)
$arm = [Windows.Forms.CheckBox]::new()
$arm.Text = 'Enable driving'
$arm.SetBounds(150,25,160,25)
$arm.Enabled = $false
$speed = [Windows.Forms.NumericUpDown]::new()
$speed.Minimum = 20; $speed.Maximum = 100; $speed.Value = 60
$speed.SetBounds(360,25,80,25)
$speedLabel = [Windows.Forms.Label]::new()
$speedLabel.Text = 'PWM'
$speedLabel.SetBounds(315,29,45,25)
$instructions = [Windows.Forms.Label]::new()
$instructions.Text = "Hold W/A/S/D or arrows; release to stop.`nSpace/Escape or leaving this window stops/disables driving.`nF5: all sensors (including battery) | F6: snapshot`nF8/F9: pan -/+ step | F10: pan target`nSensor/pan requests stop and disable driving. No obstacle avoidance."
$instructions.SetBounds(20,75,440,105)
$status = [Windows.Forms.Label]::new()
$status.Text = 'Disconnected. Close the ELEGOO control app before connecting.'
$status.SetBounds(20,550,960,45)
$sensors = [Windows.Forms.Button]::new()
$sensors.Text = 'Check sensors (F5)'; $sensors.SetBounds(20,190,210,35)
$readings = [Windows.Forms.TextBox]::new()
$readings.Multiline = $true; $readings.ReadOnly = $true
$readings.ScrollBars = 'Vertical'; $readings.SetBounds(20,240,440,205)
$readings.Text = 'No sensor readings yet. Values are raw; ultrasound zero means unknown.'
$panMinus = [Windows.Forms.Button]::new()
$panMinus.Text = 'Pan - (F8)'; $panMinus.SetBounds(20,460,110,35)
$panPlus = [Windows.Forms.Button]::new()
$panPlus.Text = 'Pan + (F9)'; $panPlus.SetBounds(140,460,110,35)
$panStep = [Windows.Forms.NumericUpDown]::new()
$panStep.Minimum = 1; $panStep.Maximum = 20; $panStep.Value = 1
$panStep.SetBounds(270,466,60,25)
$stepLabel = [Windows.Forms.Label]::new()
$stepLabel.Text = 'Step degrees'; $stepLabel.SetBounds(340,466,110,25)
$panTarget = [Windows.Forms.NumericUpDown]::new()
$panTarget.Minimum = 10; $panTarget.Maximum = 170; $panTarget.Value = 100
$panTarget.SetBounds(20,510,70,25)
$panSet = [Windows.Forms.Button]::new()
$panSet.Text = 'Pan target (F10)'; $panSet.SetBounds(110,505,160,35)
$panNote = [Windows.Forms.Label]::new()
$panNote.Text = 'Command degrees; no angle feedback.'; $panNote.SetBounds(285,505,175,40)
$snapshot = [Windows.Forms.Button]::new()
$snapshot.Text = 'Snapshot (F6)'; $snapshot.SetBounds(490,20,150,35)
$live = [Windows.Forms.CheckBox]::new()
$live.Text = 'Live JPEG preview'; $live.SetBounds(665,25,200,25)
$picture = [Windows.Forms.PictureBox]::new()
$picture.SetBounds(490,75,490,400); $picture.SizeMode = 'Zoom'; $picture.BackColor = [Drawing.Color]::Black
$cameraStatus = [Windows.Forms.Label]::new()
$cameraStatus.Text = 'Camera idle. Snapshot displays a frame without saving a file.'
$cameraStatus.SetBounds(490,490,490,50)
$form.Controls.AddRange(@($connect,$arm,$speed,$speedLabel,$instructions,$status,
    $sensors,$readings,$panMinus,$panPlus,$panStep,$stepLabel,$panTarget,$panSet,$panNote,
    $snapshot,$live,$picture,$cameraStatus))

function Send-Drive([string]$Text) {
    if ($null -eq $script:stream) { throw 'Disconnected' }
    $bytes = [Text.Encoding]::ASCII.GetBytes($Text)
    $script:stream.Write($bytes,0,$bytes.Length)
}
function Stop-Drive {
    $script:held.Clear()
    if ($null -ne $script:stream) { Send-Drive '{"N":100}' }
    $script:wasMoving = $false
}
function Disconnect-Drive([string]$Reason) {
    try { Stop-Drive } catch {}
    if ($null -ne $script:client) { $script:client.Dispose() }
    $script:client = $null; $script:stream = $null
    $script:requests.Clear()
    $arm.Checked = $false; $arm.Enabled = $false
    $connect.Text = 'Connect'
    $status.Text = $Reason
}
function Start-PanelRequest([string]$Kind) {
    if ($null -eq $script:stream) { $status.Text = 'Connect before checking sensors or commanding pan.'; return }
    if ($script:requests.Busy()) { $status.Text = 'Wait for the current sensor/pan request to finish.'; return }
    try {
        $arm.Checked = $false
        Stop-Drive
        if ($Kind -eq 'Sensors') {
            $readings.Text = "Requested $([DateTime]::Now.ToString('HH:mm:ss')); awaiting replies.`r`n"
            $script:requests.Add('Battery (estimated V)', @{N=1})
            $script:requests.Add('Gyro XYZ (raw counts)', @{N=2})
            $script:requests.Add('Accelerometer XYZ (raw counts, includes gravity)', @{N=3})
            $script:requests.Add('Ultrasound (echo us; zero = unknown)', @{N=7;D1=2;T=30000})
            $script:requests.Add('Floor left (ADC)', @{N=8;D1=0})
            $script:requests.Add('Floor middle (ADC)', @{N=8;D1=1})
            $script:requests.Add('Floor right (ADC)', @{N=8;D1=2})
        } else {
            $command = if ($Kind -eq 'PanTarget') { @{N=5;D1=1;D2=[int]$panTarget.Value} }
                elseif ($Kind -eq 'PanMinus') { @{N=6;D1=-[int]$panStep.Value} }
                else { @{N=6;D1=[int]$panStep.Value} }
            $script:requests.Add('Pan command (acknowledgment only)', $command)
        }
        $arm.Enabled = $false
    } catch { Disconnect-Drive $_.Exception.Message }
}
function Start-PanelSnapshot {
    $script:camera.Capture($Address)
    $cameraStatus.Text = 'Requesting camera JPEG...'
}
$sensors.Add_Click({ Start-PanelRequest 'Sensors' })
$panMinus.Add_Click({ Start-PanelRequest 'PanMinus' })
$panPlus.Add_Click({ Start-PanelRequest 'PanPlus' })
$panSet.Add_Click({ Start-PanelRequest 'PanTarget' })
$snapshot.Add_Click({ Start-PanelSnapshot })
$live.Add_CheckedChanged({ if ($live.Checked) { Start-PanelSnapshot } })
$connect.Add_Click({
    if ($null -ne $script:client) { Disconnect-Drive 'Disconnected'; return }
    try {
        $script:client = [Net.Sockets.TcpClient]::new()
        $script:client.NoDelay = $true
        if (-not $script:client.ConnectAsync($Address,100).Wait(2000)) { throw 'Connection timed out' }
        $script:stream = $script:client.GetStream()
        $script:stream.WriteTimeout = 100
        $script:receiving = ''
        $script:lastHeartbeat = [DateTime]::UtcNow
        $script:sentHeartbeat = [DateTime]::MinValue
        Stop-Drive
        $arm.Enabled = $true
        $connect.Text = 'Disconnect'
        $status.Text = 'Connected; driving disabled. Enable when the floor is clear.'
    } catch { Disconnect-Drive $_.Exception.Message }
})
$arm.Add_CheckedChanged({
    try { Stop-Drive } catch { Disconnect-Drive $_.Exception.Message }
})
$form.Add_KeyDown({
    $key = $_.KeyCode.ToString()
    if ($key -in 'Space','Escape') {
        # Cancel queued work but drain the one already-sent reply before rearming.
        $script:requests.Items.Clear()
        $arm.Checked = $false
        try { Stop-Drive } catch { Disconnect-Drive $_.Exception.Message }
        $_.SuppressKeyPress = $true
    } elseif ($key -in 'F5','F6','F8','F9','F10') {
        if (-not $script:shortcuts.Add($key)) { $_.SuppressKeyPress = $true; return }
        switch ($key) {
            F5 { Start-PanelRequest 'Sensors' }
            F6 { Start-PanelSnapshot }
            F8 { Start-PanelRequest 'PanMinus' }
            F9 { Start-PanelRequest 'PanPlus' }
            F10 { Start-PanelRequest 'PanTarget' }
        }
        $_.SuppressKeyPress = $true
    } elseif ($key -in 'W','A','S','D','Up','Down','Left','Right') {
        if ($arm.Checked) { [void]$script:held.Add($key) }
        $_.SuppressKeyPress = $true
    }
})
$form.Add_KeyUp({
    $key = $_.KeyCode.ToString()
    [void]$script:shortcuts.Remove($key)
    if ($key -in 'W','A','S','D','Up','Down','Left','Right') {
        [void]$script:held.Remove($key)
        try { Send-Drive '{"N":100}'; $script:wasMoving = $false } catch {
            if ($null -ne $script:client) { Disconnect-Drive $_.Exception.Message }
        }
        $_.SuppressKeyPress = $true
    }
})
$form.Add_Deactivate({
    $script:shortcuts.Clear()
    $arm.Checked = $false
    try { Stop-Drive } catch { Disconnect-Drive $_.Exception.Message }
})
$timer = [Windows.Forms.Timer]::new()
$timer.Interval = 100
$timer.Add_Tick({
    # Decode completed HTTP requests on the UI thread; never wait for network I/O.
    if ($null -ne $script:camera.Task -and $script:camera.Task.IsCompleted) {
        $imageStream = $null; $decoded = $null
        try {
            $bytes = $script:camera.Task.GetAwaiter().GetResult()
            $imageStream = [IO.MemoryStream]::new([byte[]]$bytes)
            $decoded = [Drawing.Image]::FromStream($imageStream)
            $frame = [Drawing.Bitmap]::new($decoded)
            $old = $picture.Image; $picture.Image = $frame
            if ($null -ne $old) { $old.Dispose() }
            $cameraStatus.Text = "JPEG received $([DateTime]::Now.ToString('HH:mm:ss')). Host receipt time; preview is not recorded."
        } catch {
            $live.Checked = $false
            $cameraStatus.Text = "Camera failed: $($_.Exception.Message). Displayed frame may be stale."
        } finally {
            if ($null -ne $decoded) { $decoded.Dispose() }
            if ($null -ne $imageStream) { $imageStream.Dispose() }
            $script:camera.Task = $null
            $script:camera.NextAt = [DateTime]::UtcNow.AddMilliseconds(500)
        }
    }
    if ($live.Checked -and [DateTime]::UtcNow -ge $script:camera.NextAt) { $script:camera.Capture($Address) }
    if ($null -eq $script:stream) { return }
    try {
        $now = [DateTime]::UtcNow
        $readCount = 0
        while ($script:stream.DataAvailable -and $readCount -lt 2048) {
            $value = $script:stream.ReadByte(); $readCount++
            if ($value -lt 0) { throw 'Connection closed' }
            if ($value -eq 123) { $script:receiving = '' }
            $script:receiving += [char]$value
            if ($value -eq 125) {
                [RoverReply]::ThrowIfFault($script:receiving)
                if ($script:receiving -eq '{Heartbeat}') { $script:lastHeartbeat = $now }
                $pending = $script:requests.Pending
                if ($null -ne $pending -and $script:receiving -match ('^\{' + [regex]::Escape($pending.Command.H) + '_([^}]+)\}$')) {
                    $valueText = $Matches[1]
                    $readings.AppendText("$($pending.Label): $valueText`r`n")
                    if ($pending.Command.N -in 5,6 -and $valueText -ne 'ok') { throw 'Unexpected pan acknowledgment' }
                    if ($pending.Command.N -eq 1) {
                        $volts = 0.0
                        if (-not [double]::TryParse($valueText, [Globalization.NumberStyles]::Float,
                            [Globalization.CultureInfo]::InvariantCulture, [ref]$volts) -or
                            -not [double]::IsFinite($volts) -or $volts -lt 7.0) {
                            throw 'Battery invalid or below 7.0 V; disconnected.'
                        }
                    }
                    $script:requests.Pending = $null
                }
                $script:receiving = ''
            }
            if ($script:receiving.Length -gt 256) { throw 'Malformed control response' }
        }
        if (($now - $script:lastHeartbeat).TotalSeconds -gt 2.5) { throw 'Rover heartbeat lost; reconnect to resume.' }
        if (($now - $script:sentHeartbeat).TotalMilliseconds -ge 500) {
            Send-Drive '{Heartbeat}'; $script:sentHeartbeat = $now
        }
        if ($null -ne $script:requests.Pending -and ($now - $script:requests.SentAt).TotalSeconds -gt 2.5) {
            throw "No response: $($script:requests.Pending.Label)"
        }
        if ($null -eq $script:requests.Pending -and $script:requests.Items.Count -gt 0) {
            $script:requests.Pending = $script:requests.Items.Dequeue()
            Send-Drive ($script:requests.Pending.Command | ConvertTo-Json -Compress)
            $script:requests.SentAt = $now
        }
        if ($script:requests.Busy()) { $status.Text = 'Stopped; waiting for sensor/pan replies. Driving disabled.'; return }
        $arm.Enabled = $true
        $direction = Get-DriveDirection $script:held
        if ($arm.Checked -and $script:held.Count -gt 0 -and $direction -eq 0) {
            $arm.Checked = $false
            Stop-Drive
        }
        if ($arm.Checked -and [Windows.Forms.Form]::ActiveForm -eq $form -and $direction -ne 0) {
            # Nonzero duration is mandatory: stock T=0 has no timeout.
            Send-Drive (@{N=4;D1=$direction;D2=[int]$speed.Value;T=250;H='key'} | ConvertTo-Json -Compress)
            $script:wasMoving = $true
            $status.Text = "Driving: $direction | PWM $($speed.Value) | 250 ms commands"
        } else {
            if ($script:wasMoving) { Send-Drive '{"N":100}'; $script:wasMoving = $false }
            $status.Text = 'Connected; stopped. Hold a direction key when driving is enabled.'
        }
    } catch { Disconnect-Drive $_.Exception.Message }
})
$form.Add_FormClosing({ $timer.Stop(); Disconnect-Drive 'Closed' })
try {
    $timer.Start()
    [void]$form.ShowDialog()
} finally {
    $timer.Dispose()
    $script:camera.Dispose()
    if ($null -ne $picture.Image) { $picture.Image.Dispose(); $picture.Image = $null }
    Disconnect-Drive 'Closed'
    $form.Dispose()
}
