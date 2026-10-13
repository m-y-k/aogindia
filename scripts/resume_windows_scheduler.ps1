# =============================================================================
# AOG India Esports - Resume Windows Scheduled Tasks
# =============================================================================
# Run this script with PowerShell (as Administrator) to re-enable AOG India
# scheduled tasks after you are ready to resume outreach.
# =============================================================================

$Tasks = Get-ScheduledTask -TaskName "AOGIndia_*" -ErrorAction SilentlyContinue

if ($Tasks) {
    $Tasks | Enable-ScheduledTask | Out-Null
    Write-Host "[OK] The following AOG India scheduled tasks are now RESUMED (Enabled):" -ForegroundColor Green
    foreach ($t in $Tasks) {
        Write-Host "     - $($t.TaskName)" -ForegroundColor Cyan
    }
} else {
    Write-Host "[INFO] No AOGIndia_* tasks found to enable. Run setup_windows_scheduler.ps1 to register them." -ForegroundColor Yellow
}
