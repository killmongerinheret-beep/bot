# Setup Health Check Task in Windows Task Scheduler
# Run this script as Administrator

$TaskName = "Vatican Monitor Health Check"
$ScriptPath = "$PSScriptRoot\health_check_bot.py"
$WorkingDir = $PSScriptRoot

Write-Host "Setting up automated health check..." -ForegroundColor Cyan
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

# Check if health_check_bot.py exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ ERROR: health_check_bot.py not found at:" -ForegroundColor Red
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
    -Argument "health_check_bot.py" `
    -WorkingDirectory $WorkingDir

# Create task trigger (every 30 minutes)
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 30) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

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
        -Description "Monitors Vatican ticket bot health and sends Telegram alerts if issues detected" `
        -ErrorAction Stop | Out-Null
    
    Write-Host ""
    Write-Host "✅ SUCCESS! Health check task created" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Frequency: Every 30 minutes"
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
    Write-Host "The health check will now run automatically every 30 minutes." -ForegroundColor White
    Write-Host "You will receive Telegram alerts if any issues are detected." -ForegroundColor White
    Write-Host ""
    Write-Host "To view the task:" -ForegroundColor Yellow
    Write-Host "  1. Open Task Scheduler (taskschd.msc)"
    Write-Host "  2. Look for '$TaskName'"
    Write-Host ""
    Write-Host "To test manually:" -ForegroundColor Yellow
    Write-Host "  python health_check_bot.py"
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
