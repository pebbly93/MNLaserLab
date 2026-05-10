from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVICE_DIR = ROOT / "windows_service"
WORKFLOW = ROOT / ".github" / "workflows" / "build-browser-windows.yml"

SERVICE_RUN_PS1 = r'''
$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $PSScriptRoot
$Exe = Join-Path $Root "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe"
$LogDir = Join-Path $env:LOCALAPPDATA "MN Laser Lab Manager\logs"
$LogFile = Join-Path $LogDir "service_runner.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log($msg) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$stamp | $msg"
}

Write-Log "Starting MN Laser Lab background service runner"
Write-Log "Root: $Root"
Write-Log "Exe: $Exe"

if (!(Test-Path $Exe)) {
    Write-Log "ERROR: EXE not found"
    exit 1
}

$env:MN_OPEN_BROWSER = "0"
$env:MN_BACKEND_HOST = "0.0.0.0"
$env:MN_BACKEND_PORT = "8000"

try {
    & $Exe *>> $LogFile
}
catch {
    Write-Log "EXCEPTION: $($_.Exception.Message)"
    exit 1
}
'''

INSTALL_PS1 = r'''
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
'''

INSTALL_BAT = r'''@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  Installa MN Laser Lab come servizio/background
echo ============================================================
echo.
echo Verrà creato un Task di Windows che avvia il backend all'accesso.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Installa_MN_Laser_Service.ps1"
'''

UNINSTALL_PS1 = r'''
$TaskName = "MN Laser Lab Browser Service"

try {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "Servizio/background MN Laser Lab rimosso." -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "Errore rimozione servizio: $($_.Exception.Message)" -ForegroundColor Red
}

pause
'''

UNINSTALL_BAT = r'''@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  Rimuovi servizio/background MN Laser Lab
echo ============================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Rimuovi_MN_Laser_Service.ps1"
'''

OPEN_PS1 = r'''
$ErrorActionPreference = "SilentlyContinue"

$ports = 8000..8019
$opened = $false

foreach ($p in $ports) {
    $url = "http://127.0.0.1:$p/api/health"
    try {
        $res = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1
        if ($res.StatusCode -eq 200) {
            Start-Process "http://127.0.0.1:$p/"
            $opened = $true
            break
        }
    } catch {}
}

if (-not $opened) {
    Start-Process "http://127.0.0.1:8000/"
}
'''

OPEN_BAT = r'''@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Apri_MN_Laser_Lab.ps1"
'''

README = r'''
MN Laser Lab Manager - Browser Edition - Servizio Windows

1. Avvio manuale:
   - Avvia_MN_Laser_Lab_Browser_Windows.bat

2. Installazione come servizio/background:
   - Tasto destro su Installa_MN_Laser_Service.bat
   - Esegui come amministratore

3. Apertura app:
   - Apri_MN_Laser_Lab.bat
   - oppure browser: http://127.0.0.1:8000/

4. Smartphone sulla stessa Wi-Fi:
   - http://IP_DEL_PC:8000/

5. Rimozione servizio/background:
   - Rimuovi_MN_Laser_Service.bat

Log:
C:\Users\<utente>\AppData\Local\MN Laser Lab Manager\logs
'''

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")

def patch_workflow():
    if not WORKFLOW.exists():
        print("Workflow non trovato, salto patch workflow.")
        return

    s = WORKFLOW.read_text(encoding="utf-8")

    if "Copy-Item windows_service\\*" not in s:
        s = s.replace(
            "Copy-Item Avvia_MN_Laser_Lab_Browser_Windows.ps1 package\\Avvia_MN_Laser_Lab_Browser_Windows.ps1 -ErrorAction SilentlyContinue",
            "Copy-Item Avvia_MN_Laser_Lab_Browser_Windows.ps1 package\\Avvia_MN_Laser_Lab_Browser_Windows.ps1 -ErrorAction SilentlyContinue\n          Copy-Item windows_service\\* package\\ -Recurse -Force"
        )

    WORKFLOW.write_text(s, encoding="utf-8")

def main():
    write(SERVICE_DIR / "MN_Laser_Service_Run.ps1", SERVICE_RUN_PS1)
    write(SERVICE_DIR / "Installa_MN_Laser_Service.ps1", INSTALL_PS1)
    write(SERVICE_DIR / "Installa_MN_Laser_Service.bat", INSTALL_BAT)
    write(SERVICE_DIR / "Rimuovi_MN_Laser_Service.ps1", UNINSTALL_PS1)
    write(SERVICE_DIR / "Rimuovi_MN_Laser_Service.bat", UNINSTALL_BAT)
    write(SERVICE_DIR / "Apri_MN_Laser_Lab.ps1", OPEN_PS1)
    write(SERVICE_DIR / "Apri_MN_Laser_Lab.bat", OPEN_BAT)
    write(SERVICE_DIR / "README_SERVIZIO_WINDOWS.txt", README)

    patch_workflow()

    print("Patch v42.1.0 applicata: servizio/background Windows aggiunto.")

if __name__ == "__main__":
    main()
