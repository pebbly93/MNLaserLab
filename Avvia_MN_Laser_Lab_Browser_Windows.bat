@echo off
setlocal

title MN Laser Lab Manager - Browser Edition

cd /d "%~dp0"

echo Avvio MN Laser Lab Manager Browser Edition...
echo.

if exist "MN_Laser_Lab_Browser.exe" (
    start "" "MN_Laser_Lab_Browser.exe"
    exit /b 0
)

if exist "backend\.venv\Scripts\python.exe" (
    backend\.venv\Scripts\python.exe backend\mn_laser_browser_launcher.py
    exit /b %ERRORLEVEL%
)

python backend\mn_laser_browser_launcher.py
pause
