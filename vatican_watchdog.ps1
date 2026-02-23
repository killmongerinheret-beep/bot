# ============================================
#  Vatican Bot Watchdog (PowerShell)
# ============================================
#  Continuously monitors and restarts the Vatican bot if it crashes.
#  Runs as a background process and logs everything.
#
#  USAGE:
#    powershell -ExecutionPolicy Bypass -File vatican_watchdog.ps1
#
#  TO INSTALL AS STARTUP TASK (run once):
#    powershell -ExecutionPolicy Bypass -File vatican_watchdog.ps1 -Install
#
#  TO REMOVE STARTUP TASK:
#    powershell -ExecutionPolicy Bypass -File vatican_watchdog.ps1 -Uninstall
# ============================================

param(
    [switch]$Install,
    [switch]$Uninstall
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BotScript = Join-Path $ScriptDir "run_vatican_bot.py"
$LogFile = Join-Path $ScriptDir "watchdog.log"
$TaskName = "VaticanBotWatchdog"

# --- INSTALL / UNINSTALL as Windows Scheduled Task ---
if ($Install) {
    Write-Host "Installing Vatican Bot as Windows Startup Task..." -ForegroundColor Cyan

    # Create the scheduled task action
    $Action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$($MyInvocation.MyCommand.Path)`"" `
        -WorkingDirectory $ScriptDir

    # Trigger: At logon
    $Trigger = New-ScheduledTaskTrigger -AtLogon

    # Settings: restart on failure, don't stop on idle
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 999 `
        -RestartInterval (New-TimeSpan -Minutes 1)

    # Register the task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Vatican Bot Monitor - Runs continuously and restarts on crash" `
        -RunLevel Highest `
        -Force

    Write-Host ""
    Write-Host "SUCCESS! Vatican Bot will now start automatically when you log in." -ForegroundColor Green
    Write-Host "To start it now, run: schtasks /run /tn $TaskName" -ForegroundColor Yellow
    Write-Host "To check status: schtasks /query /tn $TaskName" -ForegroundColor Yellow
    Write-Host "To remove: powershell -File vatican_watchdog.ps1 -Uninstall" -ForegroundColor Yellow
    exit 0
}

if ($Uninstall) {
    Write-Host "Removing Vatican Bot Startup Task..." -ForegroundColor Cyan
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Done! Task removed." -ForegroundColor Green
    exit 0
}

# --- WATCHDOG LOOP ---
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] $Message"
    Write-Host $logLine
    Add-Content -Path $LogFile -Value $logLine -ErrorAction SilentlyContinue
}

Write-Log "=========================================="
Write-Log "  VATICAN BOT WATCHDOG STARTED"
Write-Log "=========================================="
Write-Log "Bot script: $BotScript"
Write-Log "Log file: $LogFile"

$crashCount = 0

while ($true) {
    Write-Log "Starting Vatican Bot (attempt $($crashCount + 1))..."

    try {
        $process = Start-Process -FilePath "python" `
            -ArgumentList "`"$BotScript`"" `
            -WorkingDirectory $ScriptDir `
            -NoNewWindow `
            -PassThru `
            -RedirectStandardOutput (Join-Path $ScriptDir "vatican_bot_stdout.log") `
            -RedirectStandardError (Join-Path $ScriptDir "vatican_bot_stderr.log")

        Write-Log "Bot started with PID: $($process.Id)"

        # Wait for the process to exit
        $process.WaitForExit()
        $exitCode = $process.ExitCode

        Write-Log "Bot exited with code: $exitCode"

        if ($exitCode -eq 0) {
            Write-Log "Bot exited cleanly. Stopping watchdog."
            break
        }

        $crashCount++
        Write-Log "CRASH #$crashCount detected!"

        # Exponential backoff: 10s, 20s, 30s... up to 120s
        $waitTime = [Math]::Min(10 * $crashCount, 120)

        # After 10 consecutive crashes, do a longer cooldown
        if ($crashCount -ge 10) {
            $waitTime = 300  # 5 minutes
            Write-Log "Too many crashes ($crashCount). Extended cooldown: ${waitTime}s"
            $crashCount = 0
        }

        Write-Log "Restarting in ${waitTime}s..."
        Start-Sleep -Seconds $waitTime

    } catch {
        Write-Log "ERROR: Failed to start bot: $_"
        Start-Sleep -Seconds 30
    }
}

Write-Log "Watchdog stopped."
