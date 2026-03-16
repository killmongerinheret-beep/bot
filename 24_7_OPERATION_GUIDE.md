# 24/7 Operation Guide - Vatican Ticket Monitor

## ❓ Do I Need to Keep Kiro or Docker Open?

### Short Answer: **NO - Only Docker Desktop needs to run in background**

### What Needs to Run:
- ✅ **Docker Desktop** - Must be running (can be minimized to system tray)
- ❌ **Kiro IDE** - Can be closed completely
- ❌ **Terminal/PowerShell** - Can be closed
- ❌ **Browser** - Can be closed

### How It Works:
1. Docker Desktop runs as a Windows service in the background
2. Your containers (backend, worker, telegram bot) run inside Docker
3. They keep running even if you close everything else
4. Docker Desktop starts automatically when Windows boots (if configured)

---

## 🚀 Setup for 24/7 Operation

### Step 1: Configure Docker Desktop to Start on Boot

1. Open Docker Desktop
2. Go to Settings (gear icon)
3. General tab
4. ✅ Enable "Start Docker Desktop when you log in"
5. Click "Apply & Restart"

### Step 2: Verify Services are Running

```powershell
# Check all services
docker-compose ps

# Should show all services as "Up"
```

### Step 3: Test System Restart

1. Restart your computer
2. Wait 2-3 minutes for Docker to start
3. Check services again:
```powershell
cd D:\bot\travelagenntbot
docker-compose ps
```

All services should be running automatically!

---

## 🤖 Automated Health Monitoring with Telegram

### Option 1: Manual Health Check (Run Anytime)

```powershell
cd D:\bot\travelagenntbot
python health_check_bot.py
```

This will:
- ✅ Check if all Docker services are running
- ✅ Check if API is responding
- ✅ Check if monitoring tasks ran recently
- 📱 Send Telegram alert if any issues found

### Option 2: Automated Health Check (Windows Task Scheduler)

#### Setup Instructions:

1. **Open Task Scheduler**
   - Press `Win + R`
   - Type `taskschd.msc`
   - Press Enter

2. **Create New Task**
   - Click "Create Task" (not "Create Basic Task")
   - Name: `Vatican Monitor Health Check`
   - Description: `Checks if Vatican ticket monitor is running`
   - ✅ Check "Run whether user is logged on or not"
   - ✅ Check "Run with highest privileges"

3. **Triggers Tab**
   - Click "New..."
   - Begin the task: `On a schedule`
   - Settings: `Daily`
   - Recur every: `1 days`
   - Repeat task every: `30 minutes`
   - For a duration of: `Indefinitely`
   - ✅ Check "Enabled"
   - Click OK

4. **Actions Tab**
   - Click "New..."
   - Action: `Start a program`
   - Program/script: `python`
   - Add arguments: `health_check_bot.py`
   - Start in: `D:\bot\travelagenntbot`
   - Click OK

5. **Conditions Tab**
   - ❌ Uncheck "Start the task only if the computer is on AC power"
   - ✅ Check "Wake the computer to run this task"

6. **Settings Tab**
   - ✅ Check "Allow task to be run on demand"
   - ✅ Check "Run task as soon as possible after a scheduled start is missed"
   - If the task fails, restart every: `5 minutes`
   - Attempt to restart up to: `3 times`

7. **Save the Task**
   - Click OK
   - Enter your Windows password if prompted

#### Test the Task:

```powershell
# Right-click the task in Task Scheduler
# Click "Run"
# Check your Telegram for health status
```

---

## 📱 What You'll Receive on Telegram

### When System is Healthy (No Alert):
- Health check runs silently every 30 minutes
- No messages sent (to avoid spam)

### When System Has Issues:
```
🚨 Vatican Monitor Health Alert

Status: UNHEALTHY
Time: 2026-03-09 14:30:00

Issues Found:
• Docker: Services not running: worker_vatican, beat
• Activity: No tasks checked in last 5 minutes

Action Required:
Please check the system immediately.
```

---

## 🔧 What to Do When You Get an Alert

### Step 1: Check Docker Desktop
1. Open Docker Desktop
2. Check if it's running
3. If not, start it

### Step 2: Check Services
```powershell
cd D:\bot\travelagenntbot
docker-compose ps
```

### Step 3: Restart Services if Needed
```powershell
# Restart all services
docker-compose restart

# Or restart specific service
docker-compose restart worker_vatican
docker-compose restart beat
```

### Step 4: Check Logs for Errors
```powershell
# Check recent logs
docker-compose logs --tail=50 worker_vatican
docker-compose logs --tail=50 beat
docker-compose logs --tail=50 backend
```

### Step 5: Full Restart (If Nothing Works)
```powershell
# Stop everything
docker-compose down

# Start everything
docker-compose up -d

# Wait 30 seconds and check
Start-Sleep -Seconds 30
docker-compose ps
```

---

## 🎯 Quick Reference Commands

### Check System Status
```powershell
cd D:\bot\travelagenntbot

# Check all services
docker-compose ps

# Check if monitoring is working
docker-compose logs worker_vatican --tail=20

# Run manual health check
python health_check_bot.py
```

### View Logs
```powershell
# All services
docker-compose logs --tail=50

# Specific service
docker-compose logs worker_vatican --tail=50
docker-compose logs beat --tail=20
docker-compose logs telegram_bot --tail=20

# Follow logs in real-time
docker-compose logs -f worker_vatican
```

### Restart Services
```powershell
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart worker_vatican
docker-compose restart beat
```

### Stop/Start System
```powershell
# Stop everything
docker-compose down

# Start everything
docker-compose up -d
```

---

## 📊 Monitoring Dashboard

### Access Points:
- **Frontend Dashboard**: http://localhost or http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1/tasks/
- **Admin Panel**: http://localhost:8000/admin/

### What to Check:
1. **Dashboard** - Shows active tasks and recent checks
2. **API** - Returns JSON with task status
3. **Logs** - Shows real-time monitoring activity

---

## 🛡️ System Requirements for 24/7 Operation

### Windows Settings:
- ✅ Disable "Sleep" mode (or set to "Never")
- ✅ Disable "Hibernate"
- ✅ Set "Turn off display" to your preference (doesn't affect Docker)
- ✅ Ensure "Fast Startup" is disabled (can cause Docker issues)

### Docker Desktop Settings:
- ✅ Start Docker Desktop when you log in
- ✅ Use WSL 2 based engine (recommended)
- ✅ Allocate sufficient resources:
  - Memory: At least 4GB
  - CPUs: At least 2
  - Disk: At least 20GB

### Power Settings:
```powershell
# Disable sleep (run as Administrator)
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0

# Disable hibernate
powercfg /hibernate off
```

---

## 🔍 Troubleshooting Common Issues

### Issue: Docker Desktop not starting on boot
**Solution**: 
1. Open Docker Desktop settings
2. Enable "Start Docker Desktop when you log in"
3. Restart computer to test

### Issue: Services not running after restart
**Solution**:
```powershell
cd D:\bot\travelagenntbot
docker-compose up -d
```

### Issue: Health check not sending alerts
**Solution**:
1. Test manually: `python health_check_bot.py`
2. Check Telegram bot token in `.env` file
3. Verify chat ID is correct: `-5245239270`

### Issue: Computer goes to sleep
**Solution**:
1. Open Control Panel → Power Options
2. Click "Change plan settings"
3. Set "Put the computer to sleep" to "Never"

### Issue: Docker uses too much memory
**Solution**:
1. Open Docker Desktop → Settings → Resources
2. Reduce Memory limit to 4GB
3. Reduce CPUs to 2
4. Click "Apply & Restart"

---

## 📈 Expected Behavior

### Normal Operation:
- ✅ Services run 24/7 without intervention
- ✅ Monitoring checks every 60 seconds
- ✅ Telegram notifications on availability changes
- ✅ Health check every 30 minutes (silent if OK)
- ✅ Auto-restart on failures (Docker restart policy)

### Resource Usage:
- CPU: 5-15% average
- Memory: 2-4 GB
- Disk: ~10 GB
- Network: Minimal (API calls only)

### Uptime:
- Expected: 99.9% (only down during Windows updates)
- Actual: Depends on your computer's uptime

---

## 🎉 You're All Set!

Your Vatican ticket monitor is now configured for 24/7 operation with automated health monitoring!

**What happens now:**
1. ✅ System runs automatically in background
2. ✅ Monitors Vatican tickets every 60 seconds
3. ✅ Sends Telegram alerts when tickets become available
4. ✅ Health check runs every 30 minutes
5. ✅ Telegram alert if system has issues
6. ✅ Auto-restarts on failures

**You can:**
- Close Kiro IDE
- Close all terminals
- Close browser
- Minimize Docker Desktop to system tray
- Let your computer run normally

**The system will keep working!** 🚀

---

**Last Updated**: March 9, 2026
**Status**: Ready for 24/7 Operation
