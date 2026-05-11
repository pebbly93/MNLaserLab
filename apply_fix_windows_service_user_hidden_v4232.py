from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_PS1 = ROOT / "windows_service" / "MN_Laser_Service_Run.ps1"
INSTALL_PS1 = ROOT / "windows_service" / "Installa_MN_Laser_Service.ps1"
REMOVE_PS1 = ROOT / "windows_service" / "Rimuovi_MN_Laser_Service.ps1"
README = ROOT / "windows_service" / "README_SERVIZIO_WINDOWS.txt"

RUN_PS1.write_text(r'''$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir = Split-Path -Parent $ScriptDir

$LogDir = Join-Path $env:LOCALAPPDATA "MN Laser Lab Manager\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir "browser_service.log"

function Write-Log($msg) {
  "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg" | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

Write-Log "============================================================"
Write-Log "Avvio runner servizio MN Laser Lab"
Write-Log "ScriptDir: $ScriptDir"
Write-Log "ParentDir: $ParentDir"

$Candidates = @(
  (Join-Path $ScriptDir "MN_Laser_Lab_Browser.exe"),
  (Join-Path $ScriptDir "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe"),
  (Join-Path $ParentDir "MN_Laser_Lab_Browser.exe"),
  (Join-Path $ParentDir "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe")
)

$Exe = $null
foreach ($c in $Candidates) {
  Write-Log "Controllo EXE: $c"
  if (Test-Path $c) {
    $Exe = $c
    break
  }
}

if (-not $Exe) {
  Write-Log "ERRORE: MN_Laser_Lab_Browser.exe non trovato."
  exit 1
}

$ExeDir = Split-Path -Parent $Exe

$env:MN_OPEN_BROWSER = "0"
$env:MN_BACKEND_HOST = "0.0.0.0"
$env:MN_BACKEND_PORT = "8000"

Write-Log "EXE trovato: $Exe"
Write-Log "Working directory: $ExeDir"
Write-Log "URL locale atteso: http://127.0.0.1:8000/"

Set-Location $ExeDir

try {
  & $Exe *>> $LogFile
  Write-Log "Processo terminato."
} catch {
  Write-Log "ECCEZIONE: $($_.Exception.Message)"
  exit 1
}
''', encoding="utf-8")

INSTALL_PS1.write_text(r'''param(
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
''', encoding="utf-8")

REMOVE_PS1.write_text(r'''param(
  [string]$TaskName = "MN Laser Lab Manager Browser Service"
)

$ErrorActionPreference = "SilentlyContinue"

if (Get-ScheduledTask -TaskName $TaskName) {
  Stop-ScheduledTask -TaskName $TaskName
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  Write-Host "Servizio rimosso: $TaskName" -ForegroundColor Green
} else {
  Write-Host "Servizio non trovato: $TaskName"
}
''', encoding="utf-8")

README.write_text(r'''MN Laser Lab Manager - Browser Edition come servizio Windows
============================================================

Questa versione avvia il gestionale in background all'accesso utente Windows, senza mostrare finestre CMD.

INSTALLAZIONE
-------------
1. Estrarre lo ZIP in una cartella stabile, ad esempio:
   C:\MN Laser Lab\

2. Fare tasto destro su:
   Installa_MN_Laser_Service.bat

3. Selezionare:
   Esegui come amministratore

4. Il servizio viene creato in Utilità di pianificazione:
   MN Laser Lab Manager Browser Service

5. Il browser NON viene aperto automaticamente.
   Aprire manualmente:
   http://127.0.0.1:8000/

Da smartphone/tablet sulla stessa rete Wi-Fi:
   http://IP_DEL_PC:8000/

LOG
---
%LOCALAPPDATA%\MN Laser Lab Manager\logs\browser_service.log

TEST RAPIDO
-----------
Aprire PowerShell:
Get-ScheduledTask | Where-Object {$_.TaskName -like "*MN Laser*"}
Get-Content "$env:LOCALAPPDATA\MN Laser Lab Manager\logs\browser_service.log" -Tail 80

RIMOZIONE
---------
Eseguire come amministratore:
Rimuovi_MN_Laser_Service.bat
''', encoding="utf-8")

print("Patch v42.3.2 applicata: servizio Windows nascosto all'accesso utente e path EXE robusto.")
