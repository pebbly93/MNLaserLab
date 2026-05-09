$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "== MN Laser Lab Manager - build locale Windows ==" -ForegroundColor Cyan

Write-Host "[1/4] Build frontend React" -ForegroundColor Yellow
Set-Location "$Root\frontend"
npm ci
npm run build

Write-Host "[2/4] Build backend FastAPI" -ForegroundColor Yellow
Set-Location "$Root\backend"
if (!(Test-Path ".venv")) { py -3.11 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
pyinstaller MN_Laser_Lab_Backend.spec --clean --noconfirm

Write-Host "[3/4] Copia risorse Electron" -ForegroundColor Yellow
Set-Location $Root
New-Item -ItemType Directory -Force desktop\resources\backend | Out-Null
New-Item -ItemType Directory -Force desktop\resources\frontend | Out-Null
Copy-Item backend\dist\MN_Laser_Lab_Backend.exe desktop\resources\backend\MN_Laser_Lab_Backend.exe -Force
Copy-Item frontend\dist\* desktop\resources\frontend -Recurse -Force

Write-Host "[4/4] Build installer Electron" -ForegroundColor Yellow
Set-Location "$Root\desktop"
npm ci
npm run dist:win -- --publish never

Write-Host "Build completata. Setup in desktop\release" -ForegroundColor Green
