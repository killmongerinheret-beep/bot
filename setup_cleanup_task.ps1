# Setup Automatic Task Cleanup in Windows Task Scheduler
# Run this script as Administrator
# This will delete monitoring tasks automatically when their date has passed

$TaskName = "Vatican Monitor Task Cleanup"
$ScriptPath = "$PSScriptRoot\cleanup_expired_tasks.py"
$WorkingDir = $PSScriptRoot

Write-Host "Setting up automatic task cleanup..." -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python or add it to PATH" -ForegroundColor Yellow
    pause
    exit 1
}

# Check if cleanup_expired_tasks.py exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ ERROR: cleanup_expired_tasks.py not found at:" -ForegroundColor Red
    Write-Host "   $ScriptPath" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ Script found: $ScriptPath" -ForegroundColor Green
Write-Host ""

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "⚠️  Existing task found. Removing..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "✅ Old task removed" -ForegroundColor Green
}

# Create task action
$action = New-ScheduledTaskAction `
    -Execute "python" `
    -Argument "cleanup_expired_tasks.py" `
    -WorkingDirectory $WorkingDir

# Create task trigger (daily at 2 AM)
$trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At 2:00AM

# Create task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Create task principal (run with highest privileges)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Automatically deletes Vatican ticket monitoring tasks when their target date has passed" `
        -ErrorAction Stop | Out-Null
    
    Write-Host ""
    Write-Host "✅ SUCCESS! Automatic cleanup task created" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Frequency: Daily at 2:00 AM"
    Write-Host "  Script: $ScriptPath"
    Write-Host "  Working Directory: $WorkingDir"
    Write-Host ""
    
    # Test the task
    Write-Host "Testing the task now..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    
    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Host "✅ Task executed. Last run: $($taskInfo.LastRunTime)" -ForegroundColor Green
    Write-Host "   Last result: $($taskInfo.LastTaskResult) (0 = Success)" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "🎉 Setup Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "What happens now:" -ForegroundColor White
    Write-Host "  • Every day at 2:00 AM, the system will check all monitoring tasks" -ForegroundColor White
    Write-Host "  • Tasks with dates that have passed will be automatically deleted" -ForegroundColor White
    Write-Host "  • You'll receive a Telegram notification when tasks are deleted" -ForegroundColor White
    Write-Host "  • Active tasks (future dates) will remain untouched" -ForegroundColor White
    Write-Host ""
    Write-Host "To view the task:" -ForegroundColor Yellow
    Write-Host "  1. Open Task Scheduler (taskschd.msc)"
    Write-Host "  2. Look for '$TaskName'"
    Write-Host ""
    Write-Host "To test manually:" -ForegroundColor Yellow
    Write-Host "  python cleanup_expired_tasks.py"
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ ERROR: Failed to create task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

pause
