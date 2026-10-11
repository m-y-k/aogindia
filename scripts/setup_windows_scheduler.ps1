# =============================================================================
# AOG India Esports - Windows Task Scheduler Auto-Setup
# =============================================================================
# Run this script ONCE as Administrator to activate hands-free automation.
# It registers two scheduled tasks:
#   1. Daily email sending Mon-Fri at 10:30 AM
#   2. Weekly brand discovery every Monday at 9:00 AM
# =============================================================================

$PythonExe      = "C:\\Python314\\python.exe"
$OutreachScript = "D:\\Drone Projects\\AOG India\\scripts\\autopilot_sponsor_outreach.py"
$ProjectRoot    = "D:\\Drone Projects\\AOG India"

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Task 1: Daily Email Sending
$DailyAction  = New-ScheduledTaskAction -Execute $PythonExe -Argument "$OutreachScript --now" -WorkingDirectory $ProjectRoot
$DailyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "10:30AM"
Register-ScheduledTask -TaskName "AOGIndia_DailyOutreach" -Action $DailyAction -Trigger $DailyTrigger -Settings $Settings -RunLevel Highest -Force | Out-Null
Write-Host "[OK] AOGIndia_DailyOutreach registered: Mon-Fri at 10:30 AM" -ForegroundColor Green

# Task 2: Weekly Brand Discovery
$WeeklyAction  = New-ScheduledTaskAction -Execute $PythonExe -Argument "$OutreachScript --weekly" -WorkingDirectory $ProjectRoot
$WeeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "9:00AM"
Register-ScheduledTask -TaskName "AOGIndia_WeeklyDiscovery" -Action $WeeklyAction -Trigger $WeeklyTrigger -Settings $Settings -RunLevel Highest -Force | Out-Null
Write-Host "[OK] AOGIndia_WeeklyDiscovery registered: Monday at 9:00 AM" -ForegroundColor Green

Write-Host ""
Write-Host "AOG India Autopilot is now FULLY AUTOMATED!" -ForegroundColor Cyan
Write-Host "Emails send daily. New brands discovered weekly. Zero manual work needed."
