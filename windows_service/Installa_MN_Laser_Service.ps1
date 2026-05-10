$ErrorActionPreference = "Stop"

$TaskName = "MN Laser Lab Browser Service"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Runner = Join-Path $ScriptDir "MN_Laser_Service_Run.ps1"

if (!(Test-Path $Runner)) {
    Write-Host "ERRORE: runner non trovato: $Runner" -ForegroundColor Red
    pause
    exit 1
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Runner`""

$Trigger = New-ScheduledTaskTrigger -AtLogOn

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "MN Laser Lab installato come servizio/background all'accesso Windows." -ForegroundColor Green
Write-Host "Task: $TaskName"
Write-Host ""
Write-Host "Apri l'app da browser:"
Write-Host "http://127.0.0.1:8000/"
Write-Host ""
Write-Host "Da smartphone sulla stessa rete:"
Write-Host "http://IP_DEL_PC:8000/"
Write-Host ""
pause
