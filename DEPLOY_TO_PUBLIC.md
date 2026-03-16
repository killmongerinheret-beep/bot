# Deploy Multi-Tenant Vatican Bot to Public Domain 🌐

**Goal:** Make your multi-tenant dashboard accessible to everyone on the internet  
**Current Status:** Running on localhost (only you can access)  
**Target:** Public domain with HTTPS (everyone can access)

---

## 🎯 Deployment Options

### Option 1: Railway (Recommended - Easiest)
**Pros:** 
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Easy Docker deployment
- ✅ Custom domain support
- ✅ PostgreSQL included

**Steps:**
1. Create Railway account
2. Connect GitHub repo
3. Deploy with one click
4. Get public URL like `https://your-app.railway.app`

### Option 2: Vercel + PlanetScale
**Pros:**
- ✅ Free tier generous
- ✅ Excellent for Next.js
- ✅ Global CDN
- ✅ Custom domains

**Steps:**
1. Deploy frontend to Vercel
2. Deploy backend to Railway/Render
3. Use PlanetScale for database

### Option 3: DigitalOcean Droplet
**Pros:**
- ✅ Full control
- ✅ $5/month
- ✅ Can handle high traffic
- ✅ Custom domain

**Steps:**
1. Create droplet
2. Install Docker
3. Deploy with docker-compose
4. Configure domain and SSL

### Option 4: Heroku (Simple but Paid)
**Pros:**
- ✅ Very easy deployment
- ✅ Automatic scaling
- ✅ Add-ons ecosystem

**Cons:**
- ❌ No free tier anymore
- ❌ More expensive

---

## 🚀 Quick Deploy with Railway (Recommended)

### Step 1: Prepare for Deployment
```bash
# 1. Create production docker-compose
cp docker-compose.yml docker-compose.prod.yml

# 2. Update environment variables for production
# 3. Push to GitHub repository
```

### Step 2: Railway Deployment
1. **Sign up:** Go to https://railway.app
2. **Connect GitHub:** Link your repository
3. **Deploy:** Railway auto-detects Docker and deploys
4. **Get URL:** Railway provides public URL like `https://vatican-bot-production.railway.app`

### Step 3: Configure Domain (Optional)
1. **Buy domain:** Get domain like `vatican-tickets.com`
2. **Add to Railway:** Configure custom domain in Railway dashboard
3. **SSL:** Railway automatically provides HTTPS

---

## 📋 Production Configuration

### Environment Variables for Production
```env
# Database (Railway provides PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis (Railway provides Redis)
REDIS_URL=redis://host:port

# Frontend URL
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1

# Security
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-app.railway.app

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token

# CORS for frontend
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

### Production Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
    ports:
      - "8000:8000"
    
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
    ports:
      - "3000:3000"
    
  worker_vatican:
    build: .
    command: celery -A backend.core worker -l info -Q vatican
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    
  beat:
    build: .
    command: celery -A backend.core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
```

---

## 🔧 Step-by-Step Railway Deployment

### 1. Prepare Repository
```bash
# Create production environment file
cat > .env.production << EOF
SECRET_KEY=your-production-secret-key-change-this
DEBUG=False
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
CORS_ALLOWED_ORIGINS=*
EOF

# Create railway.json for configuration
cat > railway.json << EOF
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "docker-compose -f docker-compose.prod.yml up",
    "healthcheckPath": "/api/v1/health/"
  }
}
EOF
```

### 2. Update Production Settings
```python
# backend/core/settings.py - Add production settings
import os
from pathlib import Path

# Production database
if os.getenv('DATABASE_URL'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
    }

# Production Redis
if os.getenv('REDIS_URL'):
    CELERY_BROKER_URL = os.getenv('REDIS_URL')
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }

# Production security
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
```

### 3. Deploy to Railway
1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for production deployment"
   git push origin main
   ```

2. **Railway Setup:**
   - Go to https://railway.app
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway automatically detects Docker and starts deployment

3. **Configure Services:**
   - **Add PostgreSQL:** Railway → Add Service → PostgreSQL
   - **Add Redis:** Railway → Add Service → Redis
   - **Set Environment Variables:** Copy from Railway database URLs

4. **Get Public URL:**
   - Railway provides URL like: `https://vatican-bot-production.railway.app`
   - Your dashboard is now publicly accessible!

---

## 🌐 Alternative: Quick Deploy with Vercel + Railway

### Frontend (Vercel)
```bash
# Deploy frontend to Vercel
npm install -g vercel
cd frontend
vercel --prod

# Get URL like: https://vatican-dashboard.vercel.app
```

### Backend (Railway)
```bash
# Deploy backend to Railway
# Railway detects backend automatically
# Get URL like: https://vatican-api.railway.app
```

### Update API URL
```typescript
// frontend/src/lib/api.ts
const getApiUrl = () => {
  return process.env.NEXT_PUBLIC_API_URL || 'https://vatican-api.railway.app/api/v1';
};
```

---

## 🔒 Security for Production

### 1. Environment Variables
```env
# Strong secret key
SECRET_KEY=your-256-bit-secret-key-here

# Database credentials
DATABASE_URL=postgresql://user:password@host:port/database

# API keys
TELEGRAM_BOT_TOKEN=your-bot-token
```

### 2. CORS Configuration
```python
# backend/core/settings.py
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend.vercel.app",
    "https://vatican-dashboard.com",
]

CORS_ALLOW_CREDENTIALS = True
```

### 3. HTTPS Enforcement
```python
# Force HTTPS in production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

---

## 📊 Cost Estimation

### Railway (Recommended)
- **Hobby Plan:** $5/month
- **Includes:** 512MB RAM, PostgreSQL, Redis, Custom domain, HTTPS
- **Perfect for:** Small to medium traffic

### Vercel + Railway
- **Vercel:** Free (generous limits)
- **Railway:** $5/month (backend + database)
- **Total:** $5/month

### DigitalOcean
- **Droplet:** $5/month (1GB RAM)
- **Domain:** $12/year
- **Total:** ~$6/month

---

## 🎯 Recommended Deployment Plan

### Phase 1: Quick Launch (Today)
1. **Deploy to Railway** (5 minutes)
2. **Get public URL** like `https://vatican-bot.railway.app`
3. **Test multi-tenant dashboard** publicly accessible
4. **Share URL** with users

### Phase 2: Custom Domain (This Week)
1. **Buy domain** like `vatican-tickets.com`
2. **Configure DNS** to point to Railway
3. **Enable HTTPS** (automatic)
4. **Professional branding**

### Phase 3: Scale (Next Month)
1. **Monitor usage** and performance
2. **Upgrade plan** if needed
3. **Add CDN** for global speed
4. **Implement analytics**

---

## 🚀 Let's Deploy Now!

### Option A: Railway (Easiest)
```bash
# 1. Push your code to GitHub
git add .
git commit -m "Ready for production"
git push origin main

# 2. Go to railway.app and deploy
# 3. Get your public URL
# 4. Share with users!
```

### Option B: Manual VPS Setup
```bash
# 1. Get DigitalOcean droplet
# 2. Install Docker
# 3. Clone repository
# 4. Run docker-compose
# 5. Configure domain
```

---

## 📞 Next Steps

**Choose your deployment method:**

1. **🚀 Railway (Recommended):** Fastest, easiest, $5/month
2. **⚡ Vercel + Railway:** Best performance, $5/month  
3. **🛠️ DigitalOcean:** Full control, $5/month
4. **💼 Custom VPS:** Maximum flexibility, varies

**I can help you with any of these options! Which would you prefer?**

Once deployed, your multi-tenant Vatican monitoring dashboard will be accessible to anyone in the world at a public URL like:
- `https://vatican-tickets.railway.app`
- `https://your-custom-domain.com`

**Ready to make it public? Let me know which deployment option you'd like to use!** 🌐