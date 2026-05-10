$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "Avvio MN Laser Lab Manager - Browser Edition..." -ForegroundColor Cyan

$Exe = Join-Path $Root "MN_Laser_Lab_Browser.exe"
$VenvPython = Join-Path $Root "backend\.venv\Scripts\python.exe"
$Launcher = Join-Path $Root "backend\mn_laser_browser_launcher.py"

if (Test-Path $Exe) {
    Start-Process $Exe
    exit
}

if (Test-Path $VenvPython) {
    & $VenvPython $Launcher
    exit
}

python $Launcher
