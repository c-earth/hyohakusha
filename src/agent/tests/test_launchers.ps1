<#
Verify compatibility forwarding and exploration CLI argument handling offline.
Copies forwarding scripts into a new temporary tree with inert sibling targets.
The exploration launcher is exercised only after replacing its Python command
AST with a local argument recorder. No project Python or network code executes.
#>
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$tempBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$testRoot = [IO.Path]::GetFullPath((Join-Path $tempBase ('hyohakusha-launchers-' + [Guid]::NewGuid().ToString('N'))))
if (-not $testRoot.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase)) { throw 'Temporary path escaped test root.' }
New-Item -ItemType Directory -Path (Join-Path $testRoot 'src/agent'), (Join-Path $testRoot 'src/tools') | Out-Null
try {
    foreach ($entryName in @('run_calibration.ps1','run_exploration.ps1','collect_baseline.ps1','stationary_survey.ps1')) {
        $sourcePath = Join-Path $projectRoot "src/agent/$entryName"
        $sourceText = Get-Content -LiteralPath $sourcePath -Raw
        $parseTokens = $null
        $parseErrors = $null
        $entryAst = [Management.Automation.Language.Parser]::ParseInput($sourceText, [ref]$parseTokens, [ref]$parseErrors)
        if ($parseErrors.Count) { throw ($parseErrors | Out-String) }
        $forwardPath = Join-Path $testRoot "src/agent/$entryName"
        $targetPath = Join-Path $testRoot "src/tools/$entryName"
        [IO.File]::WriteAllText($forwardPath, $sourceText)
        [IO.File]::WriteAllText($targetPath, $entryAst.ParamBlock.Extent.Text + "`n" + '$PSBoundParameters | ConvertTo-Json -Depth 4 -Compress')
        $parameters = @{SessionTimestamp='20261009000000000'; ChatName='Offline forwarding test'; Address='unused.invalid'}
        if ($entryName -like 'run_*') { $parameters.SafeAreaAssumed = $true }
        if ($entryName -eq 'run_calibration.ps1') {
            $parameters.TimedCamera = $true
            $parameters.ForwardOnly = $true
            $parameters.Repeats = 2
            $parameters.DurationMs = 200
        }
        if ($entryName -eq 'run_exploration.ps1') { $parameters.Actions = 'Forward,Left,Forward' }
        if ($entryName -eq 'collect_baseline.ps1') { $parameters.Samples = 3 }
        $received = & $forwardPath @parameters | ConvertFrom-Json -AsHashtable
        foreach ($parameterName in $parameters.Keys) {
            $value = $received[$parameterName]
            if ($value -is [System.Collections.IDictionary] -and $value.Contains('IsPresent')) { $value = $value.IsPresent }
            if ([string]$value -cne [string]$parameters[$parameterName]) { throw "Forwarding lost $parameterName in $entryName" }
        }
    }

    $launcherText = Get-Content -LiteralPath (Join-Path $projectRoot 'src/tools/run_exploration.ps1') -Raw
    $launcherAst = [Management.Automation.Language.Parser]::ParseInput($launcherText, [ref]$parseTokens, [ref]$parseErrors)
    $pythonCalls = @($launcherAst.FindAll({param($node) $node -is [Management.Automation.Language.CommandAst] -and $node.Extent.Text.Contains('-m src.agent.runtime.bounded_exploration')}, $true))
    if ($pythonCalls.Count -ne 1) { throw 'Expected exactly one Python launch to replace.' }
    $callText = $pythonCalls[0].Extent.Text
    # Keep the real native argument list, including splatting and parameter order.
    $executableText = $pythonCalls[0].CommandElements[0].Extent.Text
    $recordingCall = $callText.Replace($executableText, 'Record-Arguments')
    $launcherText = $launcherText.Replace($callText, $recordingCall)
    $recorderFunction = 'function Record-Arguments { $global:LASTEXITCODE = 0; ConvertTo-Json -InputObject @($args) -Compress }'
    $launcherText = $launcherText.Replace("`$ErrorActionPreference = 'Stop'", "$recorderFunction`n`$ErrorActionPreference = 'Stop'")
    if ($launcherText.Contains('python.exe')) { throw 'Refuse test with an executable path still present.' }
    $testLauncher = Join-Path $testRoot 'src/tools/run_exploration.ps1'
    [IO.File]::WriteAllText($testLauncher, $launcherText)
    $beforePath = (Get-Location).Path
    $direct = & $testLauncher -SessionTimestamp '20261009000000000' -ChatName 'Argument test' -SafeAreaAssumed -Actions 'Forward,Left,Forward' | ConvertFrom-Json
    if ((Get-Location).Path -cne $beforePath) { throw 'Launcher failed to restore working directory.' }
    $native = & pwsh -NoProfile -File $testLauncher -SessionTimestamp '20261009000000000' -ChatName 'Argument test' -SafeAreaAssumed -Actions 'Forward,Left,Forward' | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw 'pwsh -File launcher test failed.' }
    foreach ($receivedArgs in @(@{Values=$direct}, @{Values=$native})) {
        $values = @($receivedArgs.Values)
        $index = [array]::IndexOf($values, '--actions')
        if ($index -lt 0 -or ($values[($index+1)..($values.Count-1)] -join ',') -cne 'forward,left,forward') { throw 'Action argument expansion failed.' }
        if ($values[[array]::IndexOf($values, '--name')+1] -cne 'Argument test') { throw 'Chat name with spaces was split.' }
    }
    $calibrationText = Get-Content -LiteralPath (Join-Path $projectRoot 'src/tools/run_calibration.ps1') -Raw
    $calibrationAst = [Management.Automation.Language.Parser]::ParseInput($calibrationText, [ref]$parseTokens, [ref]$parseErrors)
    if ($parseErrors.Count) { throw ($parseErrors | Out-String) }
    $calibrationCalls = @($calibrationAst.FindAll({param($node) $node -is [Management.Automation.Language.CommandAst] -and $node.Extent.Text.Contains('-m src.agent.runtime.calibration_session')}, $true))
    if ($calibrationCalls.Count -ne 1) { throw 'Expected one calibration Python command.' }
    $calibrationCall = $calibrationCalls[0]
    $calibrationText = $calibrationText.Replace($calibrationCall.Extent.Text, $calibrationCall.Extent.Text.Replace($calibrationCall.CommandElements[0].Extent.Text, 'Record-Arguments'))
    $calibrationText = $calibrationText.Replace("`$ErrorActionPreference = 'Stop'", "$recorderFunction`n`$ErrorActionPreference = 'Stop'")
    if ($calibrationText.Contains('python.exe')) { throw 'Calibration Python command replacement incomplete.' }
    $calibrationPath = Join-Path $testRoot 'src/tools/run_calibration.ps1'
    [IO.File]::WriteAllText($calibrationPath, $calibrationText)
    $values = & $calibrationPath -SessionTimestamp '20261009000000000' -ChatName 'Forward stop test' -SafeAreaAssumed -ForwardOnly -DriveOnly -TimedCamera -Repeats 1 -Speed 60 -DurationMs 200 | ConvertFrom-Json
    foreach ($pair in @(@('--forward-only','1'), @('--turn-only','0'), @('--drive-only','1'), @('--timed-camera','1'), @('--repeats','1'), @('--pwm','60'), @('--duration-ms','200'))) {
        if ($values[[array]::IndexOf($values, $pair[0])+1] -cne $pair[1]) { throw "Calibration argument mismatch: $($pair[0])" }
    }
    $conflictRejected = $false
    try { & $calibrationPath -SessionTimestamp '20261009000000000' -ChatName 'Conflict test' -SafeAreaAssumed -ForwardOnly -TurnOnly | Out-Null }
    catch { if ($_.Exception.Message -notlike '*cannot be combined*') { throw }; $conflictRejected = $true }
    if (-not $conflictRejected) { throw 'Calibration accepted conflicting direction options.' }
    Write-Output 'Four compatibility forwarders, exploration launch forms and forward calibration arguments/exclusivity passed offline.'
} finally {
    $resolvedTestRoot = [IO.Path]::GetFullPath($testRoot)
    if (-not $resolvedTestRoot.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase) -or
        (Split-Path $resolvedTestRoot -Leaf) -notlike 'hyohakusha-launchers-*') { throw 'Refuse cleanup outside temporary test tree.' }
    Remove-Item -LiteralPath $resolvedTestRoot -Recurse -Force
}
