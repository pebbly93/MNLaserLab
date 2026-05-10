@echo off
setlocal

title MN Laser Lab Manager - Browser Edition

cd /d "%~dp0"

echo ============================================================
echo  MN Laser Lab Manager - Browser Edition
echo ============================================================
echo.

set MN_OPEN_BROWSER=1
set MN_BACKEND_HOST=0.0.0.0
set MN_BACKEND_PORT=8000

if exist "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe" (
    echo Avvio da cartella onedir...
    echo.
    "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe"
    echo.
    echo L'app si e' chiusa. Codice errore: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

if exist "MN_Laser_Lab_Browser.exe" (
    echo Avvio EXE singolo...
    echo.
    "MN_Laser_Lab_Browser.exe"
    echo.
    echo L'app si e' chiusa. Codice errore: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo ERRORE: eseguibile non trovato.
echo Cerca:
echo - MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe
echo - MN_Laser_Lab_Browser.exe
echo.
pause
exit /b 1
