# Dashboard and Telegram Bot - Complete Guide

## 📊 Dashboard Functionality

### Access
- **URL**: `http://localhost:3000` (or your deployed URL)
- **Authentication**: Agency name + API key

### Available Operations

#### ✅ Add Task
1. Click "Add Monitor" button
2. Fill in the form:
   - **Site**: Vatican Museums (only option)
   - **Dates**: List of dates to monitor (e.g., `["2026-06-15", "2026-03-23"]`)
   - **Ticket Name**: e.g., "Musei Vaticani - Biglietti d'ingresso"
   - **Visitors**: Number of visitors (1-6)
   - **Ticket Type**: 0 = Standard, 1 = Guided Tour
   - **Language**: Only for guided tours (ENG, ITA, FRA, DEU, SPA)
   - **Preferred Times**: e.g., `["08:00", "09:00", "10:00"]`
3. Click "Create"
4. Task will start monitoring immediately

#### ✅ Edit Task
1. Click on a task in the list
2. Modify any field:
   - Add/remove dates
   - Change number of visitors
   - Update preferred times
   - Change ticket type or language
3. Click "Save"
4. Changes apply immediately

#### ✅ Delete Task
1. Click on a task in the list
2. Click "Delete" button
3. Confirm deletion
4. Task stops monitoring immediately

#### ✅ View Status
- See all your active tasks
- Check last status (available/sold_out/pending)
- View last check time
- See available slots (if any)

### Dashboard API Endpoints

```
GET    /api/agencies/              - List all agencies
POST   /api/agencies/              - Create agency
GET    /api/agencies/{id}/         - Get agency details
PUT    /api/agencies/{id}/         - Update agency
DELETE /api/agencies/{id}/         - Delete agency

GET    /api/tasks/                 - List all tasks
POST   /api/tasks/                 - Create task
GET    /api/tasks/{id}/            - Get task details
PUT    /api/tasks/{id}/            - Update task
DELETE /api/tasks/{id}/            - Delete task

GET    /api/results/               - List check results
GET    /api/results/?task={id}     - Get results for specific task
```

## 🤖 Telegram Bot Functionality

### Setup
1. Start bot: `/start`
2. Bot will register your Telegram user ID
3. Link to your agency (automatic if chat_id is set)

### Available Commands

#### ✅ /start
- Shows main menu with buttons:
  - ➕ Add Monitor
  - 📋 List Monitors
  - 🗑️ Remove Monitor
  - 📊 Status
  - ❓ Help

#### ✅ /add (or click "Add Monitor")
**Interactive conversation flow:**
1. Select date method (Calendar or Manual)
2. Enter date (DD/MM/YYYY format)
3. Select number of visitors (1-6)
4. Select ticket type (Standard or Guided Tour)
5. If guided tour: Select language
6. Select preferred times (or skip)
7. Confirm and create

**Example:**
```
User: /add
Bot: How would you like to select the date?
User: [Clicks "Manual Entry"]
Bot: Please enter the date (DD/MM/YYYY):
User: 15/06/2026
Bot: How many visitors?
User: [Clicks "2"]
Bot: Select ticket type:
User: [Clicks "Standard Entry"]
Bot: Select preferred times:
User: [Clicks "08:00", "09:00", "Done"]
Bot: ✅ Monitor created!
```

#### ✅ /list (or click "List Monitors")
Shows all your active monitors with:
- Date
- Ticket name
- Visitors
- Last status
- Available slots (if any)

**Example output:**
```
📋 Your Active Monitors (2)

1️⃣ Monitor #1
📅 Date: 15/06/2026
🎫 Ticket: Musei Vaticani - Biglietti d'ingresso
👥 Visitors: 2
🔔 Status: available
✅ Available slots: 10

2️⃣ Monitor #2
📅 Date: 23/03/2026
🎫 Ticket: Musei Vaticani - Biglietti d'ingresso
👥 Visitors: 1
🔔 Status: available
✅ Available slots: 7
```

#### ✅ /remove (or click "Remove Monitor")
1. Shows list of your monitors
2. Click on the one you want to remove
3. Confirms deletion

**Example:**
```
User: /remove
Bot: Select monitor to remove:
     [Button: 15/06/2026 - 2 visitors]
     [Button: 23/03/2026 - 1 visitor]
User: [Clicks first button]
Bot: ✅ Monitor removed successfully!
```

#### ✅ /status (or click "Status")
Shows system status:
- Total active monitors
- Last check time
- System health
- Recent notifications

#### ✅ /edit [task_id] [visitors]
**Command-line edit (limited functionality):**
```
/edit 123 2
```
Changes the number of visitors for task #123 to 2.

**Note**: For full editing (dates, times, ticket type), use the dashboard.

#### ❌ /cancel
Cancels current conversation/operation

### Telegram Bot Limitations

#### ⚠️ Limited Edit Functionality
The Telegram bot can only edit:
- ✅ Number of visitors (via `/edit` command)

Cannot edit via Telegram:
- ❌ Dates
- ❌ Ticket type
- ❌ Language
- ❌ Preferred times
- ❌ Ticket name

**Reason**: These require complex UI interactions better suited for the dashboard.

**Workaround**: Use the dashboard for full editing, or delete and recreate the task via Telegram.

#### ⚠️ No Bulk Operations
- Cannot add multiple dates at once
- Cannot edit multiple tasks simultaneously
- Cannot delete all tasks at once

**Workaround**: Use the dashboard API for bulk operations.

## 🔔 Notifications

### When You Receive Notifications

Telegram notifications are sent when:
1. ✅ **State Change**: Tickets go from SOLD_OUT → AVAILABLE
2. ✅ **First Availability**: Tickets become available for the first time (optional)
3. ❌ **Not Sent**: When tickets are still available (no change)
4. ❌ **Not Sent**: When tickets are still sold out (no change)

### Notification Content

```
🎉 TICKETS JUST OPENED!

📅 Date: 23/03/2026
🎫 Ticket: Musei Vaticani - Biglietti d'ingresso
👥 Visitors: 1
⏰ Checked at: 17:07:20 Rome time
🔍 Method: search_api

⭐ YOUR PREFERRED TIMES:
   ⭐ 08:00
   ⭐ 09:00

🕐 Other Available Times (7 total):
   • 09:30
   • 11:00
   • 12:00
   • 13:00
   • 14:00
   • 15:00
   • 16:00

🔗 Click here to book:
https://tickets.museivaticani.va/home/fromtag/1/1742947200000/MV-Biglietti/1

⚡ Act fast - tickets sell quickly!
```

### Notification Settings

- **Frequency**: Only on state change (not every check)
- **Cooldown**: 1 hour per ticket/date (prevents spam)
- **Preferred Times**: Highlighted if configured
- **Direct Link**: Includes booking URL

## 📝 Task Management Best Practices

### Adding Tasks

**Good Practice:**
```json
{
  "dates": ["2026-06-15", "2026-06-16", "2026-06-17"],
  "ticket_name": "Musei Vaticani - Biglietti d'ingresso",
  "visitors": 2,
  "ticket_type": 0,
  "preferred_times": ["08:00", "09:00", "10:00"]
}
```

**Why:**
- Multiple dates in one task (efficient)
- Clear ticket name (easy to identify)
- Preferred times set (get highlighted in notifications)

**Bad Practice:**
```json
{
  "dates": ["2026-06-15"],
  "ticket_name": "Vatican",
  "visitors": 2,
  "ticket_type": 0,
  "preferred_times": []
}
```

**Why:**
- Only one date (inefficient, create separate tasks)
- Vague ticket name (hard to match)
- No preferred times (miss important slots)

### Editing Tasks

**Dashboard (Recommended):**
- Full control over all fields
- Can add/remove multiple dates
- Can change ticket type and language
- Visual interface

**Telegram (Limited):**
- Only change visitor count
- Quick and convenient
- Good for minor adjustments

**When to Edit vs Delete/Recreate:**
- **Edit**: Minor changes (visitors, add 1-2 dates)
- **Delete/Recreate**: Major changes (ticket type, language, many dates)

### Deleting Tasks

**Via Dashboard:**
1. Click task
2. Click "Delete"
3. Confirm

**Via Telegram:**
1. `/remove` or click "Remove Monitor"
2. Select task
3. Confirm

**Important**: Deletion is immediate and cannot be undone!

## 🧪 Testing

### Test Telegram Notifications

Run the test script:
```bash
docker-compose exec backend python /app/test_telegram_all_tasks.py
```

This sends a test notification to all agencies with active tasks.

**Expected Output:**
```
✅ Found 2 active task(s)
✅ Tasks belong to 1 agency/agencies
✅ Notification sent successfully to Elite Colosseo
```

### Test Dashboard API

```bash
# List all tasks
curl http://localhost:8000/api/tasks/

# Create task
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "agency": 1,
    "site": "vatican",
    "dates": ["2026-06-15"],
    "ticket_name": "Musei Vaticani - Biglietti d'ingresso",
    "visitors": 2,
    "ticket_type": 0,
    "preferred_times": ["08:00", "09:00"]
  }'

# Update task
curl -X PUT http://localhost:8000/api/tasks/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "visitors": 3
  }'

# Delete task
curl -X DELETE http://localhost:8000/api/tasks/1/
```

## 🔧 Troubleshooting

### Dashboard Issues

**Problem**: Cannot add task
- **Check**: Agency has available task slots (free: 1000, pro: 2000, agency: 5000)
- **Check**: All required fields filled
- **Check**: Dates in correct format (YYYY-MM-DD)

**Problem**: Task not updating
- **Check**: Click "Save" after editing
- **Check**: Refresh page to see changes
- **Check**: Check browser console for errors

**Problem**: Cannot delete task
- **Check**: You have permission (same agency)
- **Check**: Task exists (not already deleted)

### Telegram Bot Issues

**Problem**: Bot not responding
- **Check**: Bot is running (`docker-compose ps telegram_bot`)
- **Check**: Telegram token configured (TELEGRAM_BOT_TOKEN)
- **Check**: Start with `/start` command

**Problem**: Cannot add monitor
- **Check**: You're registered (run `/start` first)
- **Check**: Agency has available slots
- **Check**: Follow conversation flow (don't skip steps)

**Problem**: Not receiving notifications
- **Check**: Agency telegram_chat_id is set
- **Check**: Task is active (is_active=True)
- **Check**: Tickets actually became available (state changed)
- **Check**: Not in cooldown period (1 hour)

### Notification Issues

**Problem**: No notifications received
1. Check agency telegram_chat_id:
   ```bash
   docker-compose exec backend python manage.py shell
   >>> from monitors.models import Agency
   >>> Agency.objects.get(id=1).telegram_chat_id
   ```

2. Check task status:
   ```bash
   >>> from monitors.models import MonitorTask
   >>> task = MonitorTask.objects.get(id=1)
   >>> print(f"Active: {task.is_active}, Status: {task.last_status}")
   ```

3. Check Redis state:
   ```bash
   docker-compose exec redis redis-cli
   > KEYS ticket_state:*
   > GET ticket_state:1:1474593008:15/06/2026
   ```

4. Test notification manually:
   ```bash
   docker-compose exec backend python /app/test_telegram_all_tasks.py
   ```

## 📊 Summary

### Dashboard
- ✅ Full CRUD operations (Create, Read, Update, Delete)
- ✅ Visual interface
- ✅ Bulk operations possible
- ✅ All fields editable
- ✅ Real-time status updates

### Telegram Bot
- ✅ Add monitors (interactive)
- ✅ List monitors
- ✅ Remove monitors
- ✅ View status
- ⚠️ Limited edit (only visitors)
- ❌ No bulk operations
- ❌ Cannot edit dates/times/ticket type

### Recommendations

**For Adding Tasks**: Use Telegram bot (convenient) or Dashboard (more control)

**For Editing Tasks**: Use Dashboard (full control)

**For Deleting Tasks**: Either works (Telegram is quicker)

**For Monitoring**: Both show status, Dashboard has more details

**For Notifications**: Automatic via Telegram (no action needed)

---

**Last Updated**: March 7, 2026  
**Status**: All systems operational ✅
