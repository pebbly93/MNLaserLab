$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $PSScriptRoot
$Exe = Join-Path $Root "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe"
$LogDir = Join-Path $env:LOCALAPPDATA "MN Laser Lab Manager\logs"
$LogFile = Join-Path $LogDir "service_runner.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log($msg) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$stamp | $msg"
}

Write-Log "Starting MN Laser Lab background service runner"
Write-Log "Root: $Root"
Write-Log "Exe: $Exe"

if (!(Test-Path $Exe)) {
    Write-Log "ERROR: EXE not found"
    exit 1
}

$env:MN_OPEN_BROWSER = "0"
$env:MN_BACKEND_HOST = "0.0.0.0"
$env:MN_BACKEND_PORT = "8000"

try {
    & $Exe *>> $LogFile
}
catch {
    Write-Log "EXCEPTION: $($_.Exception.Message)"
    exit 1
}
