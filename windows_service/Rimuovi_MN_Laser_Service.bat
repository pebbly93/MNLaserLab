@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  Rimuovi servizio/background MN Laser Lab
echo ============================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Rimuovi_MN_Laser_Service.ps1"
