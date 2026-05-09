@echo off
setlocal
cd /d "%~dp0"
where powershell >nul 2>nul
if errorlevel 1 (
  echo PowerShell non trovato.
  pause
  exit /b 1
)
powershell -ExecutionPolicy Bypass -File scripts\build-windows-local.ps1
pause
