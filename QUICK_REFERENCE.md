# Quick Reference Card

## 🚀 Quick Start Commands

```bash
# Start system
docker-compose up -d

# Stop system
docker-compose down

# View logs
docker-compose logs -f

# Restart service
docker-compose restart worker_vatican

# Check status
docker-compose ps
```

---

## 🔧 Common Tasks

### Create Test Slot
```bash
docker-compose exec backend python /app/create_test_slot.py
```

### Import Participants from Google Sheets
```bash
docker-compose exec backend python manage.py import_participants --agency-id 1
```

### Sync Google Sheets via API
```bash
curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
  -H "Content-Type: application/json" \
  -d '{"agency_id": 1}'
```

### Check Available Slots
```bash
curl http://localhost:8000/api/v1/available-slots/
```

### Check Database
```bash
docker-compose exec db psql -U postgres -d vatican_bot
```

---

## 🌐 URLs

- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/api/docs
- **Available Slots**: http://localhost:8000/api/v1/available-slots/

---

## 📱 Telegram Bot Commands

```
/start          - Start bot
/monitor        - Create monitoring task
/list           - View active tasks
/stop <id>      - Stop monitoring task
/help           - Show help
```

---

## 🔌 Extension Configuration

### Backend Listener Mode
```
Backend URL: http://localhost:8000
API Key: (empty for local)
Max Concurrent: 10
Hold Mode: false
Auto Pay: true
```

### Profile Data
```
First Name: John
Last Name: Doe
Email: john@example.com
Phone: +39 123456789
City: Roma
```

---

## 🐛 Troubleshooting

### Check Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker_vatican
docker-compose logs -f backend
docker-compose logs -f telegram_bot

# Last 100 lines
docker-compose logs --tail=100

# Search logs
docker-compose logs | grep "ERROR"
docker-compose logs | grep "Available"
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific
docker-compose restart worker_vatican
docker-compose restart backend
```

### Reset Database
```bash
docker-compose down -v
docker-compose up -d db redis
docker-compose run --rm backend python manage.py migrate
docker-compose up -d
```

---

## 📊 Check System Health

### Services Status
```bash
docker-compose ps
```

### Database Check
```bash
docker-compose exec db psql -U postgres -d vatican_bot -c "SELECT COUNT(*) FROM monitors_monitortask WHERE is_active=true;"
```

### Redis Check
```bash
docker-compose exec redis redis-cli KEYS "*"
```

### Worker Status
```bash
docker-compose logs worker_vatican | grep "Monitoring"
```

---

## 🔑 Environment Variables

### Required
```env
SECRET_KEY=your-secret-key
POSTGRES_PASSWORD=your-password
TELEGRAM_BOT_TOKEN=your-bot-token
```

### Optional
```env
GOOGLE_SHEETS_CREDENTIALS_JSON=path/to/credentials.json
BOKUN_API_KEY=your-bokun-key
BOKUN_API_URL=https://api.bokun.io
```

---

## 📚 Documentation Quick Links

| Topic | File |
|-------|------|
| PC Setup | `PC_SETUP_GUIDE.md` |
| Extension | `EXTENSION_COMPLETE_GUIDE.md` |
| Integration | `SYSTEM_INTEGRATION_SUMMARY.md` |
| Bokun | `BOKUN_INTEGRATION_GUIDE.md` |
| Vatican Rules | `VATICAN_BOT_RULES.md` |
| Summary | `FINAL_SUMMARY.md` |

---

## 🎯 System Flow (One Line)

```
Telegram → Backend → Worker → Vatican API → HeldSlot → Extension → Auto-Book → Done
```

---

## ✅ Pre-Flight Checklist

Before starting:
- [ ] Docker installed and running
- [ ] Repository cloned
- [ ] `.env` file configured
- [ ] Telegram bot created
- [ ] Google Sheets credentials (optional)
- [ ] Bokun API key (optional)

After starting:
- [ ] All services running (`docker-compose ps`)
- [ ] Backend accessible (http://localhost:8000)
- [ ] Worker monitoring (`docker-compose logs worker_vatican`)
- [ ] Extension installed
- [ ] Extension connected to backend
- [ ] Test slot created
- [ ] Incognito window opens

---

## 🆘 Emergency Commands

### System Not Responding
```bash
docker-compose down
docker system prune -f
docker-compose up -d --build
```

### Database Corrupted
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend python manage.py migrate
```

### Worker Stuck
```bash
docker-compose restart worker_vatican
docker-compose logs -f worker_vatican
```

### Extension Not Working
```
1. Check backend URL
2. Reload extension
3. Check browser console (F12)
4. Restart browser
```

---

## 📞 Support

1. **Check logs first**: `docker-compose logs -f`
2. **Search documentation**: Use Ctrl+F in docs
3. **Check GitHub issues**: Search existing issues
4. **Ask in Telegram**: Join support group

---

## 🎓 Key Concepts

### Vatican Bot Rules
- ✅ ALWAYS use Search API (never hardcoded IDs)
- ✅ Get fresh ticket IDs for each check
- ✅ Match tickets by NAME (not ID)
- ✅ Include visitLang parameter (empty for standard)
- ✅ Use Rome timezone for timestamps

### Extension Behavior
- ✅ Polls backend every 10 seconds
- ✅ Opens incognito windows (isolated sessions)
- ✅ Strict time selection (exact time only)
- ✅ Auto-fills with participant data
- ✅ Supports up to 10 concurrent bookings

### Data Flow
- ✅ Telegram → Backend (task creation)
- ✅ Worker → Vatican (monitoring)
- ✅ Google Sheets → Backend (participants)
- ✅ Backend → Extension (available slots)
- ✅ Extension → Vatican (booking)

---

**Keep this card handy for quick reference!** 📌

**Last Updated**: May 22, 2026
