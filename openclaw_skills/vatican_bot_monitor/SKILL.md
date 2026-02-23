---
name: vatican_bot_monitor
description: Monitor and manage the Vatican ticket bot running on this machine
---

# Vatican Bot Monitor Skill

## Overview
This skill monitors the Vatican ticket bot process and can restart it if it crashes or becomes unresponsive.

## Commands

### Check Bot Status
```
Check if the Vatican bot is running
```
Run this command to check status:
```bash
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*run_vatican_bot*' } | Format-Table Id, CPU, WorkingSet64, StartTime"
```

If no output, the bot is NOT running. Start it with:
```bash
cd d:\bot\travelagenntbot && start /b python run_vatican_bot.py
```

### Check Bot Logs
```
Show me the Vatican bot logs
```
Read the last 50 lines of the log:
```bash
powershell -Command "Get-Content 'd:\bot\travelagenntbot\vatican_bot.log' -Tail 50"
```

### Restart Bot
```
Restart the Vatican bot
```
1. Kill existing process:
```bash
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*run_vatican_bot*' } | Stop-Process -Force"
```
2. Wait 3 seconds, then restart:
```bash
cd d:\bot\travelagenntbot && start /b python run_vatican_bot.py
```

### Check Crash Count
```
How many times has the Vatican bot crashed?
```
Search the log for crash entries:
```bash
powershell -Command "(Select-String -Path 'd:\bot\travelagenntbot\vatican_bot.log' -Pattern 'CRASH' | Measure-Object).Count"
```

### Check Last Error
```
What was the last Vatican bot error?
```
```bash
powershell -Command "Select-String -Path 'd:\bot\travelagenntbot\vatican_bot.log' -Pattern 'ERROR|CRASH|💥' | Select-Object -Last 5"
```

### Fix Session Expired
```
Fix Vatican bot session
```
Delete the cached session so the bot refreshes it:
```bash
del d:\bot\travelagenntbot\worker_vatican\vatican_session.json
```
Then restart the bot (see Restart Bot above).

### Check Watchdog Status
```
Is the Vatican watchdog running?
```
```bash
schtasks /query /tn VaticanBotWatchdog
```

### Install Watchdog
```
Install the Vatican bot watchdog so it starts on boot
```
```bash
powershell -ExecutionPolicy Bypass -File "d:\bot\travelagenntbot\vatican_watchdog.ps1" -Install
```
