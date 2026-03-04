# Telegram Bot Setup Guide

## Overview

Add a Telegram bot interface to manage Vatican monitors directly from Telegram! Users can add, remove, and list monitors without using the web dashboard.

## Features

✅ **Add Monitors** - Add new dates via Telegram
✅ **List Monitors** - See all your active monitors
✅ **Remove Monitors** - Delete monitors you don't need
✅ **Status Check** - View system status
✅ **Notifications** - Get alerts when tickets available

---

## Setup Steps

### 1. Create Telegram Bot

1. **Open Telegram** and search for `@BotFather`

2. **Create new bot:**
   ```
   /newbot
   ```

3. **Choose name:**
   ```
   Vatican Monitor Bot
   ```

4. **Choose username:**
   ```
   vatican_monitor_bot
   (must end with 'bot')
   ```

5. **Save the token:**
   ```
   BotFather will give you a token like:
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   
   SAVE THIS TOKEN!
   ```

### 2. Configure Environment

Add the bot token to your `.env` file:

```bash
# Add to .env file
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Install Dependencies

```bash
# Add to requirements.txt
python-telegram-bot==20.7
```

Install:
```bash
pip install python-telegram-bot==20.7
```

Or in Docker:
```bash
docker-compose exec backend pip install python-telegram-bot==20.7
```

### 4. Link Your Telegram Chat

**Option A: Via Web Dashboard**
1. Go to your dashboard
2. Settings → Telegram
3. Enter your chat ID
4. Save

**Option B: Get Chat ID from Bot**
1. Start the bot: `/start`
2. Bot will show your chat ID
3. Give this to admin to link your account

**Option C: Manually in Database**
```bash
docker-compose exec backend python manage.py shell

from monitors.models import Agency
agency = Agency.objects.get(name="Agency-admin")
agency.telegram_chat_id = "YOUR_CHAT_ID"
agency.save()
```

### 5. Run the Bot

**Option A: Standalone (Development)**
```bash
python telegram_bot.py
```

**Option B: Docker Service (Production)**

Add to `docker-compose.yml`:
```yaml
telegram_bot:
  build:
    context: .
    dockerfile: Dockerfile
  command: python /app/telegram_bot.py
  volumes:
    - ./backend:/app/backend
    - ./telegram_bot.py:/app/telegram_bot.py
  environment:
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    - DJANGO_SETTINGS_MODULE=backend.core.settings
  depends_on:
    - backend
    - redis
  restart: unless-stopped
```

Start:
```bash
docker-compose up -d telegram_bot
```

---

## Usage

### Start the Bot

Open Telegram and search for your bot username (e.g., `@vatican_monitor_bot`)

Click **Start** or send:
```
/start
```

### Main Menu

You'll see these options:

```
➕ Add Monitor
📋 List Monitors
🗑️ Remove Monitor
📊 Status
❓ Help
```

### Add a Monitor

1. Click **➕ Add Monitor**
2. Enter date: `2026-04-15`
3. Enter visitors: `1`
4. Click **✅ Confirm**

Done! Monitor created.

### List Monitors

Click **📋 List Monitors** to see:

```
📋 Your Active Monitors (3)

✅ Task #21
   Date: 2026-03-16
   Visitors: 1
   Status: available
   Last Check: 15:30

❌ Task #28
   Date: 2026-04-04
   Visitors: 6
   Status: sold_out
   Last Check: 15:29

✅ Task #24
   Date: 2026-04-22
   Visitors: 1
   Status: available
   Last Check: 15:31
```

### Remove a Monitor

1. Click **🗑️ Remove Monitor**
2. Select the monitor to remove
3. Confirm deletion

### Check Status

Click **📊 Status** to see:

```
📊 System Status

Agency: Agency-admin
Plan: PRO

📋 Monitors: 8
✅ Available: 6
❌ Sold Out: 2
⏳ Checking: 0

🔄 Check Interval: 60 seconds
📡 Proxies: 14 active
⚡ Status: Running 24/7
```

---

## Commands

```
/start - Main menu
/add - Add new monitor
/list - List all monitors
/status - Show system status
/cancel - Cancel current operation
```

---

## Notifications

When tickets become available, you'll receive:

```
🎉 TICKETS AVAILABLE!

📅 Date: April 15, 2026
🎫 Ticket: Musei Vaticani - Standard Entry
👥 Visitors: 1

⏰ Available Times:
• 09:00 ✅
• 10:00 ✅
• 11:00 ✅
• 14:00 ✅
• 15:00 ✅

🔗 Book now: https://tickets.museivaticani.va/...

Checked at: 15:45
```

---

## Advanced Features

### Bulk Add Dates

You can modify the bot to accept multiple dates:

```python
# In telegram_bot.py, add a new command
async def bulk_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add multiple dates at once"""
    await update.message.reply_text(
        "Send dates separated by commas:\n"
        "Example: 2026-04-15, 2026-04-16, 2026-04-17"
    )
```

### Custom Preferred Times

Allow users to specify preferred times:

```python
# Add to conversation flow
ENTERING_TIMES = 5

async def receive_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive preferred times"""
    times_str = update.message.text.strip()
    times = [t.strip() for t in times_str.split(',')]
    context.user_data['preferred_times'] = times
```

### Different Ticket Types

Add support for guided tours:

```python
keyboard = [
    [InlineKeyboardButton("Standard Ticket", callback_data='type_0')],
    [InlineKeyboardButton("Guided Tour", callback_data='type_1')]
]
```

---

## Troubleshooting

### Bot Not Responding

**Check if bot is running:**
```bash
docker-compose ps telegram_bot
```

**Check logs:**
```bash
docker-compose logs telegram_bot
```

**Restart bot:**
```bash
docker-compose restart telegram_bot
```

### Chat ID Not Linked

**Get your chat ID:**
1. Start bot: `/start`
2. Bot shows: "Your chat ID: 123456789"
3. Link in database:
```bash
docker-compose exec backend python manage.py shell
from monitors.models import Agency
agency = Agency.objects.get(name="Your-Agency")
agency.telegram_chat_id = "123456789"
agency.save()
```

### Token Invalid

**Check token in .env:**
```bash
cat .env | grep TELEGRAM_BOT_TOKEN
```

**Update token:**
1. Get new token from @BotFather
2. Update .env file
3. Restart bot

---

## Security

### Best Practices

1. **Keep token secret** - Never commit to git
2. **Validate users** - Check chat_id before operations
3. **Rate limiting** - Prevent spam
4. **Input validation** - Sanitize all user input

### Rate Limiting

Add to bot:
```python
from telegram.ext import MessageHandler, filters
from functools import wraps
import time

# Rate limit decorator
def rate_limit(max_per_minute=10):
    min_interval = 60.0 / max_per_minute
    last_called = {}
    
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context):
            user_id = update.effective_user.id
            now = time.time()
            
            if user_id in last_called:
                elapsed = now - last_called[user_id]
                if elapsed < min_interval:
                    await update.message.reply_text(
                        "⏳ Please wait a moment before trying again."
                    )
                    return
            
            last_called[user_id] = now
            return await func(update, context)
        return wrapper
    return decorator

# Apply to handlers
@rate_limit(max_per_minute=10)
async def receive_date(update, context):
    # ... existing code
```

---

## Monitoring

### Bot Health Check

```bash
# Check if bot is running
docker-compose ps telegram_bot

# Check logs
docker-compose logs -f telegram_bot

# Check memory usage
docker stats telegram_bot
```

### Metrics

Track bot usage:
```python
# Add to bot
import logging

logger = logging.getLogger(__name__)

async def start(update, context):
    logger.info(f"User {update.effective_user.id} started bot")
    # ... rest of code
```

---

## Deployment

### Production Checklist

- [ ] Bot token in environment variable
- [ ] Docker service configured
- [ ] Auto-restart enabled
- [ ] Logs configured
- [ ] Rate limiting enabled
- [ ] Error handling added
- [ ] User validation implemented
- [ ] Monitoring set up

### Docker Compose

```yaml
telegram_bot:
  build: .
  command: python /app/telegram_bot.py
  environment:
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
  volumes:
    - ./backend:/app/backend
    - ./telegram_bot.py:/app/telegram_bot.py
  depends_on:
    - backend
    - redis
  restart: unless-stopped
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

---

## Summary

✅ **Easy Setup** - Just create bot and add token
✅ **User Friendly** - Simple menu interface
✅ **Full Control** - Add/remove/list monitors
✅ **Real-time Alerts** - Get notified instantly
✅ **24/7 Operation** - Runs in Docker

**Your users can now manage monitors directly from Telegram!** 🚀
