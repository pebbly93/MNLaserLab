$ErrorActionPreference = "Stop"

$AppRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $env:LOCALAPPDATA "MN Laser Lab Manager\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$LogFile = Join-Path $LogDir "browser_service.log"
$Exe = Join-Path $AppRoot "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe"

if (!(Test-Path $Exe)) {
  $Exe = Join-Path $AppRoot "MN_Laser_Lab_Browser.exe"
}

if (!(Test-Path $Exe)) {
  "[$(Get-Date)] EXE non trovato in $AppRoot" | Out-File -FilePath $LogFile -Append -Encoding UTF8
  exit 1
}

$env:MN_OPEN_BROWSER = "0"
$env:MN_BACKEND_HOST = "0.0.0.0"
$env:MN_BACKEND_PORT = "8000"

"[$(Get-Date)] Avvio MN Laser Lab Browser Edition: $Exe" | Out-File -FilePath $LogFile -Append -Encoding UTF8

& $Exe *>> $LogFile
