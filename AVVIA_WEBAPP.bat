@echo off
start "MN Laser Lab API" cmd /k "cd /d %~dp0backend && run_backend.bat"
timeout /t 4 >nul
start "MN Laser Lab Web" cmd /k "cd /d %~dp0frontend && run_frontend.bat"
start http://127.0.0.1:5173
