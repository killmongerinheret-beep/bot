# Vercel Dashboard Setup Guide

## ✅ Backend Status: RUNNING

Your backend is running in Docker and accessible at:
- **Local URL**: `http://localhost:8000`
- **API Base Path**: `/api/v1/`

## Current Backend Data

### Tasks Found: 3 Active Tasks
1. **Task #19** - March 16, 2026 - Status: `sold_out` (Last checked: 12:16 PM)
2. **Task #15** - March 26, 2026 - Status: `available` (1 slot at 17:00)
3. **Task #18** - March 28, 2026 - Status: `sold_out` (Last checked: 12:16 PM)

### API Endpoints Working:
- ✅ `http://localhost:8000/api/v1/tasks/` - Returns task list
- ✅ `http://localhost:8000/api/v1/agencies/` - Returns agencies
- ✅ `http://localhost:8000/api/v1/results/` - Returns check results

## Problem: Localhost Cannot Be Used by Vercel

Your backend is running on `localhost:8000`, which is only accessible from your local machine. Vercel (hosted in the cloud) cannot reach `localhost`.

## Solution: Expose Backend Publicly

You have 3 options:

### Option 1: Use ngrok (Fastest - For Testing)

```bash
# Install ngrok (if not installed)
# Download from: https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8000
```

This will give you a public URL like:
```
https://abc123.ngrok.io
```

**Pros**: Instant, no deployment needed
**Cons**: URL changes every restart (unless you have paid plan), not for production

### Option 2: Use Cloudflare Tunnel (Free - Better for Testing)

```bash
# Install cloudflared
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# Start tunnel
cloudflared tunnel --url http://localhost:8000
```

This will give you a public URL like:
```
https://xyz-abc-123.trycloudflare.com
```

**Pros**: Free, more stable than ngrok free tier
**Cons**: Still temporary URL

### Option 3: Deploy to Production (Recommended)

Deploy your backend to a hosting service:

**Railway** (Easiest):
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

**Render** (Free tier available):
1. Connect your GitHub repo
2. Create new Web Service
3. Set build command: `docker-compose up`
4. Get URL: `https://your-app.onrender.com`

**DigitalOcean/AWS/GCP** (Most control):
- Deploy Docker container
- Get static IP or domain
- URL: `https://your-domain.com`

## Step-by-Step: Using ngrok (Quickest)

### 1. Install ngrok
Download from: https://ngrok.com/download

### 2. Start ngrok
```bash
ngrok http 8000
```

### 3. Copy the HTTPS URL
You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

Copy: `https://abc123.ngrok.io`

### 4. Update Vercel Environment Variable

Go to your Vercel dashboard:
1. Select your project
2. Go to **Settings** → **Environment Variables**
3. Add or update:
   ```
   Name: NEXT_PUBLIC_API_URL
   Value: https://abc123.ngrok.io/api/v1
   ```
4. Click **Save**

### 5. Redeploy Frontend

In Vercel:
1. Go to **Deployments**
2. Click **Redeploy** on the latest deployment
3. Wait for deployment to complete

### 6. Test Your Dashboard

Visit your Vercel URL and you should see:
- Task #15: ✅ Available (1 slot)
- Task #18: ❌ Sold Out
- Task #19: ❌ Sold Out

## Frontend Code Update

Make sure your frontend uses the correct API path:

```typescript
// config.ts or .env.local
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// api.ts
export async function fetchTasks() {
  const response = await fetch(`${API_URL}/tasks/`);
  return response.json();
}

export async function fetchAgencies() {
  const response = await fetch(`${API_URL}/agencies/`);
  return response.json();
}

export async function fetchResults(taskId: number) {
  const response = await fetch(`${API_URL}/results/?task=${taskId}`);
  return response.json();
}
```

## Expected Dashboard Display

```
┌─────────────────────────────────────────────┐
│ Task #15 - Agency-admin                     │
├─────────────────────────────────────────────┤
│ Date: March 26, 2026                        │
│ Visitors: 2                                 │
│ Ticket: Musei Vaticani - Biglietti         │
│                                             │
│ Status: ✅ AVAILABLE                        │
│ Slots Found: 1                              │
│                                             │
│ Available Times:                            │
│   • 17:00                                   │
│                                             │
│ Last Checked: 2 hours ago                   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Task #18 - Agency-admin                     │
├─────────────────────────────────────────────┤
│ Date: March 28, 2026                        │
│ Visitors: 1                                 │
│ Ticket: Musei Vaticani - Biglietti         │
│                                             │
│ Status: ❌ SOLD OUT                         │
│ Slots Found: 0                              │
│                                             │
│ Last Checked: 2 hours ago                   │
└─────────────────────────────────────────────┘
```

## Troubleshooting

### Dashboard still shows "unknown"

**Check 1**: Verify API URL in Vercel
```bash
# In Vercel dashboard, check environment variables
NEXT_PUBLIC_API_URL should be set
```

**Check 2**: Test API from browser
```
Open: https://your-ngrok-url.ngrok.io/api/v1/tasks/
Should see JSON response
```

**Check 3**: Check browser console
```
F12 → Console tab
Look for CORS errors or network errors
```

### CORS Errors

If you see CORS errors, update Django settings:

```python
# backend/core/settings.py

CORS_ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "http://localhost:3000",
    "https://*.ngrok.io",  # For ngrok
]

CORS_ALLOW_CREDENTIALS = True
```

Restart backend:
```bash
docker-compose restart backend
```

### Tasks not updating

**Check Celery workers**:
```bash
docker logs travelagenntbot-worker_vatican-1 --tail 50
docker logs travelagenntbot-beat-1 --tail 50
```

**Manually trigger a check**:
```bash
docker exec -it travelagenntbot-backend-1 python manage.py shell
```

```python
from backend.monitors.tasks import run_smart_vatican_monitor

result = run_smart_vatican_monitor(
    date='28/03/2026',
    ticket_id='',
    ticket_name='Musei Vaticani - Biglietti d\'ingresso',
    language=None,
    task_ids=[18],
    visitors=1,
    ticket_type=0
)
print(result)
```

## Quick Test Commands

```bash
# Test backend is running
curl http://localhost:8000/api/v1/tasks/ | python -m json.tool

# Test ngrok tunnel
curl https://your-ngrok-url.ngrok.io/api/v1/tasks/ | python -m json.tool

# Check Docker containers
docker ps

# Check worker logs
docker logs travelagenntbot-worker_vatican-1 --tail 100

# Check beat logs
docker logs travelagenntbot-beat-1 --tail 100

# Restart services
docker-compose restart backend worker_vatican beat
```

## Summary

1. ✅ Backend is running at `http://localhost:8000`
2. ✅ API is at `/api/v1/` (not `/api/`)
3. ✅ 3 tasks are active and being checked
4. ⚠️ Need to expose backend publicly for Vercel
5. 🚀 Use ngrok for quick testing: `ngrok http 8000`
6. 🔧 Update Vercel env: `NEXT_PUBLIC_API_URL=https://abc.ngrok.io/api/v1`
7. 🔄 Redeploy frontend in Vercel
8. ✅ Dashboard should show correct status

## Next Steps

1. **Right now**: Start ngrok to get public URL
   ```bash
   ngrok http 8000
   ```

2. **Copy the HTTPS URL** from ngrok output

3. **Update Vercel**:
   - Go to Settings → Environment Variables
   - Set `NEXT_PUBLIC_API_URL` to `https://your-ngrok-url.ngrok.io/api/v1`
   - Redeploy

4. **Verify**: Visit your Vercel dashboard and check if tasks show correct status

5. **Later**: Deploy backend to Railway/Render for permanent URL
