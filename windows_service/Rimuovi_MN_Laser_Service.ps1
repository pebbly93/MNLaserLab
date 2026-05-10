$TaskName = "MN Laser Lab Browser Service"

try {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "Servizio/background MN Laser Lab rimosso." -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "Errore rimozione servizio: $($_.Exception.Message)" -ForegroundColor Red
}

pause
