# Complete PC Setup Guide - Vatican Ticket Bot

This guide will help you set up the complete Vatican ticket monitoring and booking system on your own PC.

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Starting the System](#starting-the-system)
6. [Browser Extension Setup](#browser-extension-setup)
7. [Testing the Complete Flow](#testing-the-complete-flow)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

### What This System Does

1. **Monitors Vatican Website** - Checks every 5 seconds for available tickets
2. **Telegram Integration** - Users create monitoring tasks via Telegram bot
3. **Google Sheets Integration** - Reads participant data from Google Sheets
4. **Auto-Booking** - Browser extension automatically books tickets when found
5. **Bokun API** - (Optional) Integrates with Bokun for additional data

### Architecture

```
┌─────────────────┐
│  Telegram Bot   │ ← Users create monitoring tasks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Backend API    │ ← Stores tasks, manages data
│   (Django)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Worker Vatican  │ ← Monitors Vatican website (Search API)
│   (Celery)      │    Checks every 5 seconds
└────────┬────────┘
         │
         ▼ (When slots found)
┌─────────────────┐
│ Google Sheets   │ ← Reads participant data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Browser Ext.    │ ← Opens incognito windows
│ (Auto-Booking)  │    Auto-fills forms
└─────────────────┘    Completes booking
```

---

## 📦 Prerequisites

### Required Software

1. **Docker Desktop**
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - Mac: https://docs.docker.com/desktop/install/mac-install/
   - Linux: https://docs.docker.com/desktop/install/linux-install/

2. **Git**
   - Windows: https://git-scm.com/download/win
   - Mac: `brew install git`
   - Linux: `sudo apt-get install git`

3. **Google Chrome or Firefox**
   - For browser extension

### Required Accounts

1. **Telegram Account**
   - Create a bot via @BotFather
   - Get bot token

2. **Google Account** (Optional)
   - For Google Sheets integration
   - Service account credentials

3. **Bokun Account** (Optional)
   - API credentials

---

## 🚀 Installation Steps

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <your-repo-url>
cd <repo-folder>
```

### Step 2: Create Environment File

Create a `.env` file in the root directory:

```bash
# Copy example env file
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
POSTGRES_DB=vatican_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
TELEGRAM_ADMIN_ID=your-telegram-user-id

# Google Sheets (Optional)
GOOGLE_SHEETS_CREDENTIALS_JSON=path/to/credentials.json

# Bokun API (Optional)
BOKUN_API_KEY=your-bokun-api-key
BOKUN_API_URL=https://api.bokun.io

# Vatican Monitoring
VATICAN_CHECK_INTERVAL=5  # seconds
USE_PROXIES=False  # Set to True if you have proxies

# Browser Extension
BACKEND_URL=http://localhost:8000
```

### Step 3: Build Docker Containers

```bash
# Build all containers
docker-compose build

# This will build:
# - backend (Django API)
# - worker_vatican (Celery worker)
# - telegram_bot (Telegram bot)
# - db (PostgreSQL)
# - redis (Redis cache)
```

### Step 4: Initialize Database

```bash
# Run migrations
docker-compose run --rm backend python manage.py migrate

# Create superuser (optional)
docker-compose run --rm backend python manage.py createsuperuser
```

---

## ⚙️ Configuration

### 1. Telegram Bot Setup

1. **Create Bot**:
   ```
   1. Open Telegram and search for @BotFather
   2. Send /newbot
   3. Follow instructions to create bot
   4. Copy the bot token
   5. Add token to .env file
   ```

2. **Get Your Telegram ID**:
   ```
   1. Search for @userinfobot in Telegram
   2. Send /start
   3. Copy your user ID
   4. Add to .env as TELEGRAM_ADMIN_ID
   ```

### 2. Google Sheets Setup (Optional)

1. **Create Service Account**:
   ```
   1. Go to Google Cloud Console
   2. Create new project
   3. Enable Google Sheets API
   4. Create service account
   5. Download JSON credentials
   6. Save as backend/google-credentials.json
   ```

2. **Share Sheet with Service Account**:
   ```
   1. Open your Google Sheet
   2. Click Share
   3. Add service account email (from JSON file)
   4. Give Editor permissions
   ```

3. **Add Sheet URL to Agency**:
   ```bash
   # Via Django admin or API
   # Add google_sheet_url to your Agency model
   ```

### 3. Bokun API Setup (Optional)

Add Bokun credentials to `.env`:

```env
BOKUN_API_KEY=your-api-key
BOKUN_API_URL=https://api.bokun.io
```

---

## 🎬 Starting the System

### Start All Services

```bash
# Start all containers
docker-compose up -d

# Check status
docker-compose ps

# Expected output:
# NAME                STATUS
# backend             Up
# worker_vatican      Up
# telegram_bot        Up
# redis               Up
# db                  Up
```

### View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f worker_vatican
docker-compose logs -f telegram_bot
docker-compose logs -f backend
```

### Verify Services

1. **Backend API**: http://localhost:8000
2. **Admin Panel**: http://localhost:8000/admin
3. **API Docs**: http://localhost:8000/api/docs

---

## 🔌 Browser Extension Setup

### Step 1: Install Extension

#### Chrome:
```
1. Open Chrome
2. Go to chrome://extensions/
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select browser-extension folder
6. Extension icon appears in toolbar
```

#### Firefox:
```
1. Open Firefox
2. Go to about:debugging#/runtime/this-firefox
3. Click "Load Temporary Add-on"
4. Select browser-extension/manifest.json
5. Extension icon appears in toolbar
```

### Step 2: Configure Extension

1. **Click Extension Icon**
2. **Select "Backend Listener Mode"**
3. **Configure Settings**:
   ```
   Backend URL: http://localhost:8000
   API Key: (leave empty for local testing)
   Max Concurrent Bookings: 10
   ```

4. **Add Profile Data** (for auto-booking):
   ```
   First Name: Your first name
   Last Name: Your last name
   Email: your@email.com
   Phone: +39 123456789
   City: Roma
   ```

5. **Click "Start Backend Listener"**

### Step 3: Verify Connection

Check browser console (F12):
```
✅ Backend listener started - polling every 10 seconds
🔄 Checking backend for available slots...
```

---

## 🧪 Testing the Complete Flow

### Test 1: Create Monitoring Task via Telegram

1. **Open Telegram**
2. **Find Your Bot** (search by username)
3. **Send `/start`**
4. **Create Monitor**:
   ```
   /monitor
   Date: 28/03/2026
   Visitors: 2
   Ticket Type: Standard Entry
   ```

5. **Check Backend Logs**:
   ```bash
   docker-compose logs -f worker_vatican
   
   # Expected:
   # ✅ Monitoring 1 tasks
   # 🔍 Checking Vatican API...
   # ❌ No slots available (expected)
   ```

### Test 2: Import Participants from Google Sheets

```bash
# Run import command
docker-compose exec backend python manage.py import_participants --agency-id 1

# Expected output:
# ✅ Imported 5 participants for Agency 1
```

### Test 3: Create Test Slot (Simulates Finding Availability)

```bash
# Create test slot
docker-compose exec backend python manage.py shell

# In Python shell:
from monitors.models import HeldSlot, MonitorTask, Agency
agency = Agency.objects.first()
task = MonitorTask.objects.filter(agency=agency).first()

slot = HeldSlot.objects.create(
    task=task,
    slot_id='TEST-001',
    date='28/03/2026',
    slot_time='10:00',
    ticket_id='2129030053',
    ticket_name='Vatican Museums - Standard Entry',
    visitors=2,
    status='held'
)
print(f"✅ Created test slot: {slot.id}")
```

### Test 4: Verify Extension Opens Booking Window

1. **Check Extension Console** (F12 on extension popup):
   ```
   🎉 Found 1 available slots from backend!
   📋 1 new slots to process
   📦 Opening 1 incognito windows for parallel booking
   ✅ Opened incognito window #1 for 28/03/2026 10:00
   ```

2. **Incognito Window Opens**:
   - Vatican website loads
   - Extension auto-fills form
   - Booking proceeds automatically

### Test 5: Complete Booking Flow

Watch the incognito window:

```
Step 1/10: Selecting ticket... ✅
Step 2/10: Setting quantity... ✅
Step 3/10: Selecting time slot... ✅
Step 4/10: Proceeding to checkout... ✅
Step 5/10: Filling form with participants... ✅
Step 6/10: Solving Turnstile... ✅
Step 7/10: Confirming purchase... ✅
Step 8/10: Waiting for payment page... ✅
Step 9/10: Filling payment details... ✅
Step 10/10: Submitting payment... ✅
```

---

## 🔧 Troubleshooting

### Issue: Docker Containers Won't Start

**Solution**:
```bash
# Check Docker is running
docker --version

# Restart Docker Desktop
# Then try again:
docker-compose down
docker-compose up -d
```

### Issue: Backend Migration Errors

**Solution**:
```bash
# Reset database
docker-compose down -v
docker-compose up -d db redis
docker-compose run --rm backend python manage.py migrate
docker-compose up -d
```

### Issue: Worker Not Checking Vatican

**Solution**:
```bash
# Check worker logs
docker-compose logs -f worker_vatican

# Restart worker
docker-compose restart worker_vatican

# Verify tasks exist
docker-compose exec backend python manage.py shell
>>> from monitors.models import MonitorTask
>>> MonitorTask.objects.filter(is_active=True).count()
```

### Issue: Extension Not Connecting to Backend

**Solution**:
1. Check backend URL in extension settings
2. Verify backend is running: http://localhost:8000
3. Check browser console for CORS errors
4. Ensure backend allows localhost in CORS settings

### Issue: Google Sheets Import Fails

**Solution**:
```bash
# Check credentials file exists
ls backend/google-credentials.json

# Test import manually
docker-compose exec backend python manage.py import_participants --agency-id 1

# Check error message
docker-compose logs backend | grep "Google Sheets"
```

### Issue: Telegram Bot Not Responding

**Solution**:
```bash
# Check bot token is correct
docker-compose exec telegram_bot env | grep TELEGRAM

# Restart bot
docker-compose restart telegram_bot

# Check logs
docker-compose logs -f telegram_bot
```

### Issue: Extension Opens Window But Doesn't Book

**Solution**:
1. Check extension console (F12)
2. Verify participant data is loaded
3. Check if Vatican changed their website structure
4. Try manual booking to see if site is working

---

## 📊 Monitoring System Health

### Check Service Status

```bash
# All services
docker-compose ps

# Specific service health
docker-compose exec backend python manage.py check
```

### Check Database

```bash
# Connect to database
docker-compose exec db psql -U postgres -d vatican_bot

# Check tables
\dt

# Check active tasks
SELECT id, date, visitors, is_active FROM monitors_monitortask WHERE is_active=true;

# Exit
\q
```

### Check Redis

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check keys
KEYS *

# Check specific key
GET session:abc123

# Exit
exit
```

### Check Logs

```bash
# Real-time logs (all services)
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f worker_vatican

# Search logs
docker-compose logs | grep "ERROR"
docker-compose logs | grep "Available slots"
```

---

## 🎯 Next Steps

### 1. Production Deployment

- Use proper domain name
- Enable HTTPS
- Use production database (not SQLite)
- Set DEBUG=False
- Configure proper CORS settings
- Use environment-specific .env files

### 2. Add More Features

- Multiple agencies
- Payment tracking
- Booking history
- Analytics dashboard
- Email notifications
- SMS notifications

### 3. Optimize Performance

- Add database indexes
- Use Redis caching
- Optimize Vatican API calls
- Add rate limiting
- Use CDN for static files

---

## 📚 Additional Resources

- **Vatican Bot Rules**: See `VATICAN_BOT_RULES.md`
- **System Workflow**: See `COMPLETE_SYSTEM_WORKFLOW.md`
- **Extension Guide**: See `browser-extension/README.md`
- **API Documentation**: http://localhost:8000/api/docs

---

## 🆘 Getting Help

1. **Check Logs First**: `docker-compose logs -f`
2. **Search Issues**: Check GitHub issues
3. **Ask in Telegram**: Join support group
4. **Email Support**: support@example.com

---

## ✅ Quick Reference Commands

```bash
# Start system
docker-compose up -d

# Stop system
docker-compose down

# Restart service
docker-compose restart worker_vatican

# View logs
docker-compose logs -f worker_vatican

# Run command in container
docker-compose exec backend python manage.py shell

# Import participants
docker-compose exec backend python manage.py import_participants --agency-id 1

# Create test slot
docker-compose exec backend python /app/create_test_slot.py

# Check database
docker-compose exec db psql -U postgres -d vatican_bot

# Rebuild containers
docker-compose build
docker-compose up -d
```

---

**Last Updated**: May 22, 2026  
**Version**: 1.0  
**Status**: Production Ready ✅
