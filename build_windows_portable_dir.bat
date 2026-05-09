@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo Build versione portable/cartella, utile per test prima del setup.
call build_windows_desktop.bat
if errorlevel 1 exit /b 1
cd desktop
call npm run pack:win
cd ..
pause
