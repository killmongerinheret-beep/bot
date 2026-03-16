# Automatic Task Cleanup Guide

## 🗑️ What is Automatic Task Cleanup?

When you create a monitoring task for a specific date (e.g., March 23, 2026), the system will automatically delete that task after the date has passed. This keeps your dashboard clean and prevents unnecessary monitoring of past dates.

---

## 🎯 How It Works

### Example Timeline:

**Today: March 9, 2026**
- ✅ Task for March 23, 2026 → **Active** (14 days remaining)
- ✅ Task for June 15, 2026 → **Active** (98 days remaining)

**March 24, 2026 (next day after March 23)**
- 🗑️ Task for March 23, 2026 → **Deleted automatically**
- ✅ Task for June 15, 2026 → **Still active** (83 days remaining)

**June 16, 2026 (next day after June 15)**
- 🗑️ Task for June 15, 2026 → **Deleted automatically**
- ✅ No more tasks (all dates passed)

---

## 🚀 Setup Instructions

### Option 1: Automatic Setup (Recommended)

1. **Right-click PowerShell** and select **"Run as Administrator"**

2. **Navigate to your project:**
   ```powershell
   cd D:\bot\travelagenntbot
   ```

3. **Run the setup script:**
   ```powershell
   .\setup_cleanup_task.ps1
   ```

4. **Done!** The cleanup will run automatically every day at 2:00 AM

### Option 2: Manual Cleanup (Run Anytime)

```powershell
cd D:\bot\travelagenntbot
python cleanup_expired_tasks.py
```

This will:
- Check all monitoring tasks
- Delete tasks with dates that have passed
- Show you which tasks were deleted
- Send Telegram notification with summary

---

## 📱 What You'll Receive on Telegram

### When Tasks Are Deleted:

```
🗑️ Expired Tasks Cleaned Up

Deleted: 2 task(s)
Remaining: 1 active task(s)

Deleted Tasks:
• 23/03/2026 - Musei Vaticani - Biglietti d'ingresso (1 days ago)
• 10/03/2026 - Guided Tour - English (14 days ago)

Active Tasks:
• 15/06/2026 - Musei Vaticani - Biglietti d'ingresso (98 days)
```

### When No Tasks Need Deletion:

No message is sent (to avoid spam). The cleanup runs silently.

---

## ⏰ When Does Cleanup Run?

### Automatic Schedule:
- **Time**: Every day at 2:00 AM
- **Frequency**: Daily
- **Action**: Deletes tasks with dates that have passed

### Why 2:00 AM?
- System is usually idle
- Won't interfere with active monitoring
- Runs after midnight, so "today" is correctly calculated

### Can I Change the Time?

Yes! Edit the scheduled task:

1. Open Task Scheduler (`taskschd.msc`)
2. Find "Vatican Monitor Task Cleanup"
3. Right-click → Properties
4. Go to "Triggers" tab
5. Edit the trigger and change the time
6. Click OK

---

## 🔍 What Gets Deleted?

### Tasks That Will Be Deleted:
- ✅ Tasks where target date < today
- ✅ Example: On March 24, task for March 23 will be deleted

### Tasks That Will NOT Be Deleted:
- ✅ Tasks where target date = today (still active)
- ✅ Tasks where target date > today (future dates)
- ✅ Example: On March 23, task for March 23 is still active

### Date Comparison:
- Uses midnight (00:00) as cutoff
- On March 23 at 11:59 PM → Task is still active
- On March 24 at 12:01 AM → Task is deleted

---

## 📊 Example Scenarios

### Scenario 1: Single Task

**Setup:**
- Task for March 23, 2026 (Vatican tickets, 2 visitors)

**Timeline:**
- March 9-22: Task is active, monitoring every 60 seconds
- March 23: Task is still active (you can still book!)
- March 24 at 2:00 AM: Task is automatically deleted
- Telegram notification: "1 task deleted"

### Scenario 2: Multiple Tasks

**Setup:**
- Task A: March 15, 2026
- Task B: March 23, 2026
- Task C: June 15, 2026

**Timeline:**
- March 16 at 2:00 AM: Task A deleted (1 day ago)
- March 24 at 2:00 AM: Task B deleted (1 day ago)
- June 16 at 2:00 AM: Task C deleted (1 day ago)

Each deletion sends a Telegram notification.

### Scenario 3: No Tasks

**Setup:**
- No monitoring tasks configured

**Timeline:**
- Daily at 2:00 AM: Cleanup runs, finds nothing, exits silently
- No Telegram notifications

---

## 🛠️ Manual Testing

### Test the Cleanup Now:

```powershell
cd D:\bot\travelagenntbot
python cleanup_expired_tasks.py
```

### What You'll See:

```
============================================================
Task Cleanup - 2026-03-09 12:10:03
============================================================

📋 Fetching all monitoring tasks...
   ✅ Found 2 task(s)

   ✅ Task 2: 23/03/2026 - Active (14 days remaining)
   ✅ Task 1: 15/06/2026 - Active (98 days remaining)

============================================================
Summary:
  Active tasks: 2
  Expired tasks: 0
============================================================

✅ No expired tasks to delete

📅 Upcoming tasks:
   • 23/03/2026 - Musei Vaticani - Biglietti d'ingresso (14 days)
   • 15/06/2026 - Musei Vaticani - Biglietti d'ingresso (98 days)
```

---

## 🔧 Advanced Configuration

### Change Cleanup Schedule:

Edit `setup_cleanup_task.ps1` and change this line:

```powershell
# Current: Daily at 2:00 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

# Change to: Daily at 6:00 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM

# Change to: Every 12 hours
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 12)
```

Then run the setup script again.

### Disable Telegram Notifications:

Edit `cleanup_expired_tasks.py` and comment out the notification:

```python
# Send Telegram notification
if deleted_count > 0:
    # message = f"..."  # Comment this out
    # send_telegram_message(message)  # Comment this out
    pass
```

### Keep Tasks for X Days After Expiry:

Edit `cleanup_expired_tasks.py` and add a grace period:

```python
# Current: Delete immediately after date passes
if task_date < today:
    expired_tasks.append(...)

# Change to: Delete 7 days after date passes
grace_period = timedelta(days=7)
if task_date < (today - grace_period):
    expired_tasks.append(...)
```

---

## 📋 Verification

### Check if Cleanup Task is Scheduled:

```powershell
# List all scheduled tasks
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Vatican*"}

# Check specific task
Get-ScheduledTask -TaskName "Vatican Monitor Task Cleanup"

# View task details
Get-ScheduledTaskInfo -TaskName "Vatican Monitor Task Cleanup"
```

### View Task in Task Scheduler:

1. Press `Win + R`
2. Type `taskschd.msc`
3. Press Enter
4. Look for "Vatican Monitor Task Cleanup"

### Test Task Manually:

1. Open Task Scheduler
2. Find "Vatican Monitor Task Cleanup"
3. Right-click → Run
4. Check the "Last Run Result" (should be 0x0 for success)

---

## 🚨 Troubleshooting

### Issue: Tasks not being deleted

**Check:**
1. Is the scheduled task running?
   ```powershell
   Get-ScheduledTaskInfo -TaskName "Vatican Monitor Task Cleanup"
   ```

2. Run manually to see errors:
   ```powershell
   python cleanup_expired_tasks.py
   ```

3. Check if API is accessible:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8000/api/v1/tasks/"
   ```

### Issue: No Telegram notification

**Check:**
1. Telegram bot token in `.env` file
2. Chat ID is correct: `-5245239270`
3. Test manually:
   ```powershell
   python cleanup_expired_tasks.py
   ```

### Issue: Task runs but nothing happens

**Possible reasons:**
- No tasks have expired yet (all dates are in the future)
- API is not accessible
- Docker services are not running

**Solution:**
```powershell
# Check services
docker-compose ps

# Check API
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/tasks/"

# Run cleanup manually to see output
python cleanup_expired_tasks.py
```

---

## 📚 Files Created

### Cleanup Scripts:
- `cleanup_expired_tasks.py` - Main cleanup script
- `setup_cleanup_task.ps1` - Automated setup for Task Scheduler

### Documentation:
- `AUTO_CLEANUP_GUIDE.md` - This file

---

## 🎯 Summary

### What You Get:

1. ✅ **Automatic cleanup** - Tasks deleted when dates pass
2. ✅ **Daily schedule** - Runs at 2:00 AM every day
3. ✅ **Telegram notifications** - Know when tasks are deleted
4. ✅ **Clean dashboard** - No clutter from old tasks
5. ✅ **Manual control** - Run cleanup anytime you want

### Setup Steps:

1. Run `.\setup_cleanup_task.ps1` as Administrator
2. Done! Cleanup runs automatically every day

### Manual Usage:

```powershell
python cleanup_expired_tasks.py
```

---

**Last Updated**: March 9, 2026
**Status**: Ready to use
**Automation**: Daily at 2:00 AM
