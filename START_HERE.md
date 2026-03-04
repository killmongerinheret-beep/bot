# 🚀 START HERE: Connect Your Dashboard

## Current Situation

✅ **Backend**: Running in Docker on `localhost:8000`  
✅ **API**: Working at `/api/v1/tasks/`  
✅ **Tasks**: 3 active tasks (1 available, 2 sold out)  
❌ **Dashboard**: Shows "unknown" because Vercel can't reach localhost

## The Problem

```
┌─────────────┐                    ┌─────────────┐
│   Vercel    │                    │   Docker    │
│  (Cloud)    │  ❌ Can't reach    │  (Local)    │
│             │ ─────────────────> │             │
│  Dashboard  │    localhost       │   Backend   │
└─────────────┘                    └─────────────┘
```

## The Solution

```
┌─────────────┐                    ┌─────────────┐                    ┌─────────────┐
│   Vercel    │                    │    ngrok    │                    │   Docker    │
│  (Cloud)    │  ✅ Can reach      │  (Tunnel)   │  ✅ Forwards to    │  (Local)    │
│             │ ─────────────────> │             │ ─────────────────> │             │
│  Dashboard  │  public URL        │   Proxy     │    localhost       │   Backend   │
└─────────────┘                    └─────────────┘                    └─────────────┘
```

## 3 Simple Steps

### Step 1: Install ngrok (2 minutes)

**Download**: https://ngrok.com/download

**Windows**:
1. Download the ZIP file
2. Extract to any folder
3. Done!

### Step 2: Start ngrok (1 minute)

Open terminal in the ngrok folder and run:
```bash
ngrok http 8000
```

**Copy the HTTPS URL** from the output:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8000
            ^^^^^^^^^^^^^^^^^^^^^^
            COPY THIS!
```

### Step 3: Update Vercel (2 minutes)

1. Go to https://vercel.com/dashboard
2. Select your project
3. Settings → Environment Variables
4. Add:
   ```
   NEXT_PUBLIC_API_URL = https://abc123.ngrok.io/api/v1
   ```
5. Deployments → Redeploy

**Done!** Your dashboard should now show correct status.

## Quick Test

**Before starting**, verify backend is running:
```bash
curl http://localhost:8000/api/v1/tasks/
```

Should return JSON with 3 tasks.

## What You'll See

### Before (Dashboard shows "unknown")
```
┌─────────────────────────────────────────────┐
│ Task #18                                    │
│ Status: ❓ Unknown                          │
│ Last Checked: Never                         │
└─────────────────────────────────────────────┘
```

### After (Dashboard shows real status)
```
┌─────────────────────────────────────────────┐
│ Task #18 - March 28, 2026                   │
│ Status: ✅ AVAILABLE                        │
│ Slots: 9 available                          │
│ Times: 09:30, 10:00, 10:30, 11:00...       │
│ Last Checked: 2 minutes ago                 │
└─────────────────────────────────────────────┘
```

## Troubleshooting

### "ngrok: command not found"
- Make sure you're in the ngrok folder
- Or add ngrok to your PATH

### Dashboard still shows "unknown"
1. Check environment variable is set in Vercel
2. Make sure you redeployed the frontend
3. Clear browser cache and refresh

### CORS errors
Add to `backend/core/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "https://*.ngrok.io",
]
```

Restart backend:
```bash
docker-compose restart backend
```

## Alternative: Deploy to Production

Instead of ngrok, deploy your backend to:
- **Railway**: `railway up` (easiest)
- **Render**: Connect GitHub repo
- **DigitalOcean**: Deploy Docker container

Then use the permanent URL in Vercel.

## Need Help?

Run this script to check your backend:
```bash
powershell -ExecutionPolicy Bypass -File get_backend_url.ps1
```

## More Info

- **Quick Start**: `QUICK_START_VERCEL.md`
- **Full Setup**: `VERCEL_DASHBOARD_SETUP.md`
- **Backend Details**: `BACKEND_URL_SUMMARY.md`

---

**Ready?** Install ngrok and let's get your dashboard working! 🚀
