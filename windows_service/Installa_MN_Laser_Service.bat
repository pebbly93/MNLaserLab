@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  Installa MN Laser Lab come servizio/background
echo ============================================================
echo.
echo Verrà creato un Task di Windows che avvia il backend all'accesso.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Installa_MN_Laser_Service.ps1"
