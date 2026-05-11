param(
  [string]$TaskName = "MN Laser Lab Manager Browser Service"
)

$ErrorActionPreference = "SilentlyContinue"

if (Get-ScheduledTask -TaskName $TaskName) {
  Stop-ScheduledTask -TaskName $TaskName
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  Write-Host "Servizio rimosso: $TaskName" -ForegroundColor Green
} else {
  Write-Host "Servizio non trovato: $TaskName"
}
