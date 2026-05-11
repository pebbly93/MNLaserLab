param(
  [string]$TaskName = "MN Laser Lab Manager Browser Service"
)

$ErrorActionPreference = "Stop"

$ServiceDir = $PSScriptRoot
$Runner = Join-Path $ServiceDir "MN_Laser_Service_Run.ps1"

if (!(Test-Path $Runner)) {
  throw "File runner non trovato: $Runner"
}

$Action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Runner`"" `
  -WorkingDirectory "$ServiceDir"

$Trigger = New-ScheduledTaskTrigger -AtLogOn

$Principal = New-ScheduledTaskPrincipal `
  -UserId $env:USERNAME `
  -LogonType Interactive `
  -RunLevel Highest

$Settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -MultipleInstances IgnoreNew

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $Action `
  -Trigger $Trigger `
  -Principal $Principal `
  -Settings $Settings `
  -Description "Avvia MN Laser Lab Manager Browser Edition in background all'accesso Windows."

Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "MN Laser Lab Manager installato come attività nascosta all'accesso utente." -ForegroundColor Green
Write-Host "Task: $TaskName"
Write-Host "Apri manualmente: http://127.0.0.1:8000/"
Write-Host "Da smartphone: http://IP_DEL_PC:8000/"
Write-Host "Log: $env:LOCALAPPDATA\MN Laser Lab Manager\logs\browser_service.log"
Write-Host ""
