from pathlib import Path
import shutil
import json

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "frontend" / "index.html"
PUBLIC = ROOT / "frontend" / "public"
LOGO = PUBLIC / "mn_laser_lab_logo.png"
DESKTOP_LOGO = ROOT / "desktop" / "assets" / "mn_laser_lab_logo.png"
SERVICE_PS1 = ROOT / "windows_service" / "Installa_MN_Laser_Service.ps1"
RUN_PS1 = ROOT / "windows_service" / "MN_Laser_Service_Run.ps1"
OPEN_BAT = ROOT / "windows_service" / "Apri_MN_Laser_Lab.bat"
README = ROOT / "windows_service" / "README_SERVIZIO_WINDOWS.txt"

def patch_index():
    PUBLIC.mkdir(parents=True, exist_ok=True)

    if not LOGO.exists() and DESKTOP_LOGO.exists():
        shutil.copyfile(DESKTOP_LOGO, LOGO)

    html = '''<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#058482" />
    <meta name="application-name" content="MN Laser Lab Manager" />
    <meta name="apple-mobile-web-app-title" content="MN Laser Lab" />
    <title>MN Laser Lab Manager</title>
    <link rel="icon" type="image/png" href="/mn_laser_lab_logo.png" />
    <link rel="shortcut icon" type="image/png" href="/mn_laser_lab_logo.png" />
    <link rel="apple-touch-icon" href="/mn_laser_lab_logo.png" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''
    INDEX.write_text(html, encoding="utf-8")
    print("frontend/index.html aggiornato con titolo e favicon/logo.")

def patch_service_runner():
    RUN_PS1.write_text(r'''$ErrorActionPreference = "Stop"

$AppRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $env:LOCALAPPDATA "MN Laser Lab Manager\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$LogFile = Join-Path $LogDir "browser_service.log"
$Exe = Join-Path $AppRoot "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe"

if (!(Test-Path $Exe)) {
  $Exe = Join-Path $AppRoot "MN_Laser_Lab_Browser.exe"
}

if (!(Test-Path $Exe)) {
  "[$(Get-Date)] EXE non trovato in $AppRoot" | Out-File -FilePath $LogFile -Append -Encoding UTF8
  exit 1
}

$env:MN_OPEN_BROWSER = "0"
$env:MN_BACKEND_HOST = "0.0.0.0"
$env:MN_BACKEND_PORT = "8000"

"[$(Get-Date)] Avvio MN Laser Lab Browser Edition: $Exe" | Out-File -FilePath $LogFile -Append -Encoding UTF8

& $Exe *>> $LogFile
''', encoding="utf-8")
    print("Runner servizio aggiornato: niente apertura browser automatica, log su file.")

def patch_service_installer():
    SERVICE_PS1.write_text(r'''param(
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
  -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Runner`""

$Trigger = New-ScheduledTaskTrigger -AtStartup

$Principal = New-ScheduledTaskPrincipal `
  -UserId "SYSTEM" `
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
  -Description "Avvia MN Laser Lab Manager Browser Edition in background all'avvio di Windows."

Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "Servizio installato e avviato in background." -ForegroundColor Green
Write-Host "Task Scheduler: $TaskName"
Write-Host "Apri l'app dal browser su: http://127.0.0.1:8000/"
Write-Host "Da smartphone usa: http://IP_DEL_PC:8000/"
Write-Host ""
''', encoding="utf-8")
    print("Installer servizio aggiornato: avvio nascosto con Task Scheduler SYSTEM.")

def patch_open_bat():
    OPEN_BAT.write_text(r'''@echo off
start "" http://127.0.0.1:8000/
''', encoding="utf-8")
    print("Apri_MN_Laser_Lab.bat aggiornato.")

def patch_readme():
    README.write_text(r'''MN Laser Lab Manager - Browser Edition come servizio Windows
============================================================

Questa versione avvia il gestionale in background all'avvio di Windows, senza mostrare finestre CMD.

INSTALLAZIONE
-------------
1. Estrarre lo ZIP in una cartella stabile, ad esempio:
   C:\MN Laser Lab\

2. Fare tasto destro su:
   Installa_MN_Laser_Service.bat

3. Selezionare:
   Esegui come amministratore

4. Il servizio viene installato tramite Utilità di pianificazione di Windows:
   MN Laser Lab Manager Browser Service

5. Il browser NON viene aperto automaticamente all'avvio.
   Aprire manualmente:
   http://127.0.0.1:8000/

Da smartphone/tablet sulla stessa rete Wi-Fi:
   http://IP_DEL_PC:8000/

LOG
---
I log sono in:
%LOCALAPPDATA%\MN Laser Lab Manager\logs\browser_service.log

RIMOZIONE
---------
Eseguire come amministratore:
Rimuovi_MN_Laser_Service.bat
''', encoding="utf-8")
    print("README servizio aggiornato.")

def main():
    patch_index()
    patch_service_runner()
    patch_service_installer()
    patch_open_bat()
    patch_readme()
    print("Patch v42.3.1 completata.")

if __name__ == "__main__":
    main()
