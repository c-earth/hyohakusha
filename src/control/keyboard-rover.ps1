param([string]$Address = '192.168.4.1', [switch]$SelfTest)
$ErrorActionPreference = 'Stop'

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
    Write-Output 'Direction, conflicting-key, and released-key checks passed.'
    return
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$script:client = $null
$script:stream = $null
$script:held = [Collections.Generic.HashSet[string]]::new()
$script:receiving = ''
$script:lastHeartbeat = [DateTime]::MinValue
$script:sentHeartbeat = [DateTime]::MinValue
$script:wasMoving = $false

$form = [Windows.Forms.Form]::new()
$form.Text = 'ELEGOO keyboard drive'
$form.ClientSize = [Drawing.Size]::new(480,240)
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
$instructions.Text = "Hold W/A/S/D or arrow keys to drive.`nRelease to stop. Space/Escape stops and disables driving.`nLeaving this window also stops and disables driving.`nMultiple directions stop. Camera viewer should be separate.`nNo automatic obstacle avoidance in this manual controller."
$instructions.SetBounds(20,75,440,105)
$status = [Windows.Forms.Label]::new()
$status.Text = 'Disconnected. Close the ELEGOO control app before connecting.'
$status.SetBounds(20,190,440,40)
$form.Controls.AddRange(@($connect,$arm,$speed,$speedLabel,$instructions,$status))

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
    $arm.Checked = $false; $arm.Enabled = $false
    $connect.Text = 'Connect'
    $status.Text = $Reason
}
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
        $arm.Checked = $false
        try { Stop-Drive } catch { Disconnect-Drive $_.Exception.Message }
        $_.SuppressKeyPress = $true
    } elseif ($key -in 'W','A','S','D','Up','Down','Left','Right') {
        if ($arm.Checked) { [void]$script:held.Add($key) }
        $_.SuppressKeyPress = $true
    }
})
$form.Add_KeyUp({
    $key = $_.KeyCode.ToString()
    if ($key -in 'W','A','S','D','Up','Down','Left','Right') {
        [void]$script:held.Remove($key)
        try { Send-Drive '{"N":100}'; $script:wasMoving = $false } catch {
            if ($null -ne $script:client) { Disconnect-Drive $_.Exception.Message }
        }
        $_.SuppressKeyPress = $true
    }
})
$form.Add_Deactivate({
    $arm.Checked = $false
    try { Stop-Drive } catch { Disconnect-Drive $_.Exception.Message }
})
$timer = [Windows.Forms.Timer]::new()
$timer.Interval = 100
$timer.Add_Tick({
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
                if ($script:receiving -eq '{Heartbeat}') { $script:lastHeartbeat = $now }
                $script:receiving = ''
            }
            if ($script:receiving.Length -gt 256) { throw 'Malformed control response' }
        }
        if (($now - $script:lastHeartbeat).TotalSeconds -gt 2.5) { throw 'Rover heartbeat lost; reconnect to resume.' }
        if (($now - $script:sentHeartbeat).TotalMilliseconds -ge 500) {
            Send-Drive '{Heartbeat}'; $script:sentHeartbeat = $now
        }
        $direction = Get-DriveDirection $script:held
        if ($arm.Checked -and [Windows.Forms.Form]::ActiveForm -eq $form -and $direction -ne 0) {
            # Nonzero duration is mandatory: stock T=0 has no timeout.
            Send-Drive (@{N=2;D1=$direction;D2=[int]$speed.Value;T=250;H='key'} | ConvertTo-Json -Compress)
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
    Disconnect-Drive 'Closed'
    $form.Dispose()
}
