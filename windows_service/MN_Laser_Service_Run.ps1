$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir = Split-Path -Parent $ScriptDir

$LogDir = Join-Path $env:LOCALAPPDATA "MN Laser Lab Manager\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir "browser_service.log"

function Write-Log($msg) {
  "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg" | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

Write-Log "============================================================"
Write-Log "Avvio runner servizio MN Laser Lab"
Write-Log "ScriptDir: $ScriptDir"
Write-Log "ParentDir: $ParentDir"

$Candidates = @(
  (Join-Path $ScriptDir "MN_Laser_Lab_Browser.exe"),
  (Join-Path $ScriptDir "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe"),
  (Join-Path $ParentDir "MN_Laser_Lab_Browser.exe"),
  (Join-Path $ParentDir "MN_Laser_Lab_Browser\MN_Laser_Lab_Browser.exe")
)

$Exe = $null
foreach ($c in $Candidates) {
  Write-Log "Controllo EXE: $c"
  if (Test-Path $c) {
    $Exe = $c
    break
  }
}

if (-not $Exe) {
  Write-Log "ERRORE: MN_Laser_Lab_Browser.exe non trovato."
  exit 1
}

$ExeDir = Split-Path -Parent $Exe

$env:MN_OPEN_BROWSER = "0"
$env:MN_BACKEND_HOST = "0.0.0.0"
$env:MN_BACKEND_PORT = "8000"

Write-Log "EXE trovato: $Exe"
Write-Log "Working directory: $ExeDir"
Write-Log "URL locale atteso: http://127.0.0.1:8000/"

Set-Location $ExeDir

try {
  & $Exe *>> $LogFile
  Write-Log "Processo terminato."
} catch {
  Write-Log "ECCEZIONE: $($_.Exception.Message)"
  exit 1
}
