# Multi-Tenant Telegram Bot - Quick Reference Card

## 🚀 System Status
✅ **DEPLOYED AND RUNNING**  
✅ All 10 containers operational  
✅ Migration applied successfully  
✅ API endpoints working  
✅ Bot polling for updates  

---

## 📋 Quick Commands

### Check System Health
```bash
# All services status
docker-compose ps

# Test database
python test_telegram_groups.py

# Check API
curl http://localhost:8000/api/v1/telegram-groups/
```

### View Logs
```bash
# Telegram bot
docker-compose logs telegram_bot --tail 50

# Backend
docker-compose logs backend --tail 50

# Vatican worker
docker-compose logs worker_vatican --tail 50
```

### Restart Services
```bash
# Restart specific service
docker-compose restart telegram_bot
docker-compose restart backend

# Restart all
docker-compose restart
```

---

## 🌐 URLs

| Service | URL | Status |
|---------|-----|--------|
| Admin Dashboard | http://localhost:3000/admin/telegram-groups | ✅ Ready |
| Main Dashboard | http://localhost:3000 | ✅ Running |
| API Endpoint | http://localhost:8000/api/v1/telegram-groups/ | ✅ Working |
| Backend Admin | http://localhost:8000/admin/ | ✅ Available |

---

## 🔧 API Endpoints

```bash
# List all groups
GET /api/v1/telegram-groups/

# Filter by status
GET /api/v1/telegram-groups/?status=pending

# Approve group
POST /api/v1/telegram-groups/{id}/approve/
Body: {"agency_id": 1}  # optional

# Reject group
POST /api/v1/telegram-groups/{id}/reject/
Body: {"reason": "Spam group"}

# Suspend group
POST /api/v1/telegram-groups/{id}/suspend/
Body: {"reason": "Terms violation"}
```

---

## 🧪 Testing Flow

### 1. Add Bot to Group
- Open Telegram
- Add your bot to a group
- Bot sends welcome message

### 2. Verify Database
```bash
python test_telegram_groups.py
```
Should show 1 pending group

### 3. Open Dashboard
```
http://localhost:3000/admin/telegram-groups
```

### 4. Approve Group
- Click "Approve"
- Link to agency (optional)
- Confirm

### 5. Test Notification
Group receives Vatican ticket alerts

---

## 📊 Database Quick Check

```bash
# Django shell
docker-compose exec backend python backend/manage.py shell

# Check groups
>>> from monitors.models import TelegramGroup
>>> TelegramGroup.objects.all()
>>> TelegramGroup.objects.filter(status='pending').count()

# Check agencies
>>> from monitors.models import Agency
>>> Agency.objects.all()
```

---

## 🔍 Troubleshooting

### Bot Not Responding
```bash
docker-compose restart telegram_bot
docker-compose logs telegram_bot | grep -i error
```

### API Errors
```bash
docker-compose restart backend
docker-compose logs backend | grep -i error
```

### Dashboard Not Loading
```bash
docker-compose restart frontend
docker-compose logs frontend
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `backend/monitors/models.py` | TelegramGroup model |
| `backend/monitors/views.py` | API endpoints |
| `backend/monitors/urls.py` | URL routes |
| `backend/telegram_bot.py` | Bot handlers |
| `backend/monitors/notification_utils.py` | Notification filtering |
| `frontend/src/app/admin/telegram-groups/page.tsx` | Admin dashboard |
| `test_telegram_groups.py` | Test script |

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `DEPLOYMENT_STATUS.md` | Current deployment status |
| `TELEGRAM_MULTI_TENANT_COMPLETE.md` | Full technical guide |
| `DEPLOYMENT_CHECKLIST.md` | Step-by-step deployment |
| `IMPLEMENTATION_SUMMARY.md` | High-level overview |
| `QUICK_REFERENCE.md` | This file |

---

## ⚙️ Environment Variables

### Required
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
```

### Optional
```bash
ADMIN_TELEGRAM_IDS=your_id,another_id
```

---

## 🎯 Next Steps

1. ⏳ Add bot to test group
2. ⏳ Test approval workflow
3. ⏳ Verify notifications working
4. ⏳ Monitor for 24 hours
5. ⏳ Add ADMIN_TELEGRAM_IDS (optional)

---

## 📞 Support

- Run: `python test_telegram_groups.py`
- Check: `DEPLOYMENT_STATUS.md`
- Review: `TELEGRAM_MULTI_TENANT_COMPLETE.md`

---

**Last Updated:** March 10, 2026 14:31 CET  
**Status:** ✅ Production Ready
