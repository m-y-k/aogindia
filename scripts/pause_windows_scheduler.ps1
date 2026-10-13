# =============================================================================
# AOG India Esports - Pause Windows Scheduled Tasks
# =============================================================================
# Run this script with PowerShell (as Administrator) to disable all AOG India
# scheduled email sending tasks on your Windows machine.
# =============================================================================

$Tasks = Get-ScheduledTask -TaskName "AOGIndia_*" -ErrorAction SilentlyContinue

if ($Tasks) {
    $Tasks | Disable-ScheduledTask | Out-Null
    Write-Host "[OK] The following AOG India scheduled tasks are now PAUSED (Disabled):" -ForegroundColor Yellow
    foreach ($t in $Tasks) {
        Write-Host "     - $($t.TaskName)" -ForegroundColor Cyan
    }
} else {
    Write-Host "[INFO] No AOGIndia_* tasks were registered in Windows Task Scheduler." -ForegroundColor Green
}

Write-Host ""
Write-Host "[STATUS] Automated email dispatch is completely PAUSED on this machine." -ForegroundColor Yellow
