@echo off
set "ROVER_PWSH=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe"
if not exist "%ROVER_PWSH%" (
    echo PowerShell 7 was not found at "%ROVER_PWSH%".
    pause
    exit /b 1
)
start "" "%ROVER_PWSH%" -NoProfile -STA -WindowStyle Hidden -File "%~dp0control\keyboard-rover.ps1"
