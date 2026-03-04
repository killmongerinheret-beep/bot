# Vatican Bot - Deployment Guide

## ✅ System Status: READY FOR PRODUCTION

All system checks passed successfully!

## Backend Structure

### Core Files
- ✅ `backend/manage.py` - Django management
- ✅ `backend/core/settings.py` - Configuration
- ✅ `backend/core/urls.py` - URL routing
- ✅ `backend/monitors/models.py` - Database models
- ✅ `backend/monitors/tasks.py` - Celery tasks
- ✅ `backend/monitors/views.py` - API views
- ✅ `backend/monitors/urls.py` - API endpoints
- ✅ `worker_vatican/hydra_monitor.py` - Vatican bot logic

### Key Features Implemented
- ✅ Session caching with JSESSIONID
- ✅ Direct API calls (no clicking)
- ✅ Retry logic with session regeneration
- ✅ Force refresh capability
- ✅ Comprehensive error handling
- ✅ 24/7 reliability

## Deployment Steps

### 1. Backend Deployment

#### Install Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- Django
- Celery
- Redis
- Playwright
- Requests
- python-telegram-bot
- psycopg2 (for PostgreSQL)

#### Database Setup
```bash
# Run migrations
python backend/manage.py migrate

# Create superuser
python backend/manage.py createsuperuser

# Collect static files
python backend/manage.py collectstatic
```

#### Start Services

**Terminal 1 - Django Server:**
```bash
python backend/manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - Celery Worker:**
```bash
celery -A backend.core worker -l info --pool=solo
```

**Terminal 3 - Celery Beat:**
```bash
celery -A backend.core beat -l info
```

**Terminal 4 - Redis (if local):**
```bash
redis-server
```

### 2. Frontend Deployment (Vercel)

#### Connect Repository
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Select the frontend directory (if separate)

#### Environment Variables
Set these in Vercel dashboard:

```env
NEXT_PUBLIC_API_URL=https://your-backend-url.com
NEXT_PUBLIC_APP_NAME=Vatican Ticket Monitor
```

#### Deploy
1. Click "Deploy"
2. Wait for build to complete
3. Verify deployment at your Vercel URL

### 3. Environment Configuration

#### Backend `.env` file:
```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost

# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token-here

# Proxies (optional)
USE_PROXIES=True
OXYLABS_USERNAME=your-username
OXYLABS_PASSWORD=your-password
```

## API Endpoints

### Public Endpoints

**Health Check:**
```
GET /api/health/
```

**Get Agencies:**
```
GET /api/agencies/
```

**Get Tasks:**
```
GET /api/tasks/
```

**Get Results:**
```
GET /api/results/
```

**Get Task Details:**
```
GET /api/tasks/{id}/
```

### Admin Endpoints

**Create Agency:**
```
POST /api/agencies/
{
  "name": "Agency Name",
  "telegram_chat_id": "123456789",
  "is_active": true
}
```

**Create Task:**
```
POST /api/tasks/
{
  "agency_id": 1,
  "target_date": "28/03/2026",
  "visitors": 1,
  "language": null,
  "ticket_type": 0,
  "is_active": true
}
```

## Testing

### Backend API Test
```bash
# Test health endpoint
curl http://localhost:8000/api/health/

# Test agencies endpoint
curl http://localhost:8000/api/agencies/

# Test tasks endpoint
curl http://localhost:8000/api/tasks/
```

### Frontend Test
1. Open browser to your Vercel URL
2. Verify data loads correctly
3. Check console for API errors
4. Test all pages and features

### Bot Test
```bash
# Run system check
python test_system_check.py

# Test Vatican bot directly
python -c "
import asyncio
import sys
sys.path.insert(0, 'worker_vatican')
from hydra_monitor import HydraBot

async def test():
    bot = HydraBot(use_proxies=False)
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        ids = await bot.resolve_all_dynamic_ids(
            page, ticket_type=0, target_date='2026-03-28', visitors=1
        )
        print(f'Found {len(ids)} IDs')
        await page.close()

asyncio.run(test())
"
```

## Monitoring

### Logs to Monitor

**Django Logs:**
- Request/response logs
- Error logs
- Task execution logs

**Celery Logs:**
- Task start/completion
- Retry attempts
- Failures

**Vatican Bot Logs:**
- Session caching
- ID extraction
- API calls
- Retry logic

### Key Metrics

- Task success rate
- API response times
- Session cache hit rate
- Notification delivery rate
- Error frequency

### Alerts to Set Up

1. Task failure rate > 10%
2. API response time > 30s
3. No successful checks in 1 hour
4. Database connection errors
5. Redis connection errors

## Troubleshooting

### Common Issues

**Issue: Tasks not running**
- Check Celery worker is running
- Check Celery beat is running
- Check Redis connection
- Verify task schedule in Django admin

**Issue: API returns 500 errors**
- Check Django logs
- Verify database connection
- Check environment variables
- Restart Django server

**Issue: Bot fails to extract IDs**
- Check Playwright installation
- Verify network connectivity
- Check proxy configuration
- Review bot logs for errors

**Issue: Frontend shows no data**
- Verify API_URL environment variable
- Check CORS settings in Django
- Test API endpoints directly
- Check browser console for errors

## Maintenance

### Daily
- Monitor logs for errors
- Check task success rate
- Verify notifications are sent

### Weekly
- Review performance metrics
- Check database size
- Clean old check results
- Update dependencies if needed

### Monthly
- Review and optimize queries
- Check for Vatican website changes
- Update documentation
- Backup database

## Support

For issues or questions:
1. Check logs first
2. Review this documentation
3. Test individual components
4. Check environment configuration

## Success Criteria

✅ Backend API responds correctly  
✅ Tasks execute on schedule  
✅ Bot extracts IDs successfully  
✅ API calls work for standard and guided tickets  
✅ Retry logic handles failures  
✅ Notifications are sent  
✅ Frontend displays correct data  
✅ System runs 24/7 without intervention  

## Next Steps

1. ✅ Complete deployment following this guide
2. ✅ Test all endpoints
3. ✅ Verify frontend integration
4. ✅ Set up monitoring and alerts
5. ✅ Document any custom configurations
6. ✅ Train team on system operation
