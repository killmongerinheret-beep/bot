# Quick Start: Connect Vercel Dashboard to Backend

## ✅ Current Status

Your backend is **RUNNING** in Docker:
- **URL**: `http://localhost:8000`
- **API Path**: `/api/v1/`
- **Tasks**: 3 active tasks found
  - Task #15: March 26, 2026 - SOLD OUT
  - Task #18: March 28, 2026 - AVAILABLE
  - Task #19: March 16, 2026 - SOLD OUT

## ⚠️ Problem

Vercel (hosted in cloud) **CANNOT** access `localhost:8000` (your local machine).

## ✅ Solution: Expose Backend Publicly

### Option 1: ngrok (Fastest - 5 minutes)

**Step 1**: Download ngrok
```
https://ngrok.com/download
```

**Step 2**: Extract and run
```bash
ngrok http 8000
```

**Step 3**: Copy the HTTPS URL
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8000
            ^^^^^^^^^^^^^^^^^^^^^^
            Copy this URL
```

**Step 4**: Update Vercel
1. Go to Vercel Dashboard
2. Select your project
3. Settings → Environment Variables
4. Add/Update:
   ```
   NEXT_PUBLIC_API_URL = https://abc123.ngrok.io/api/v1
   ```
5. Click Save
6. Go to Deployments → Redeploy

**Step 5**: Test
Visit your Vercel app - should show tasks with correct status!

### Option 2: Cloudflare Tunnel (Free, More Stable)

**Step 1**: Download cloudflared
```
https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

**Step 2**: Run tunnel
```bash
cloudflared tunnel --url http://localhost:8000
```

**Step 3**: Copy URL and update Vercel (same as ngrok)

### Option 3: Deploy to Production (Best for 24/7)

**Railway** (Easiest):
```bash
npm install -g @railway/cli
railway login
railway up
```

**Render** (Free tier):
1. Connect GitHub repo
2. Create Web Service
3. Deploy
4. Get URL: `https://your-app.onrender.com`

**DigitalOcean/AWS/GCP**:
- Deploy Docker container
- Get static IP/domain

## 🎯 What to Update in Vercel

**Environment Variable**:
```
Name: NEXT_PUBLIC_API_URL
Value: <your-public-url>/api/v1
```

**Examples**:
- ngrok: `https://abc123.ngrok.io/api/v1`
- Cloudflare: `https://xyz.trycloudflare.com/api/v1`
- Railway: `https://your-app.railway.app/api/v1`
- Render: `https://your-app.onrender.com/api/v1`

## 🔧 Frontend Code (Verify This)

Make sure your frontend uses the environment variable:

```typescript
// In your API calls
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Fetch tasks
const response = await fetch(`${API_URL}/tasks/`);
const tasks = await response.json();

// Display status
tasks.forEach(task => {
  console.log(`Task #${task.id}: ${task.last_status}`);
  console.log(`Slots found: ${task.latest_check?.details?.slots?.length || 0}`);
});
```

## 🐛 Troubleshooting

### Dashboard still shows "unknown"

**Check 1**: Verify environment variable in Vercel
```
Settings → Environment Variables
NEXT_PUBLIC_API_URL should be set
```

**Check 2**: Test API directly
```
Open in browser: https://your-ngrok-url.ngrok.io/api/v1/tasks/
Should see JSON with tasks
```

**Check 3**: Check browser console (F12)
```
Look for:
- Network errors
- CORS errors
- API URL being used
```

### CORS Errors

Add to `backend/core/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "http://localhost:3000",
    "https://*.ngrok.io",
    "https://*.trycloudflare.com",
]
```

Restart backend:
```bash
docker-compose restart backend
```

### Tasks not updating

Check Celery workers:
```bash
docker logs travelagenntbot-worker_vatican-1 --tail 50
docker logs travelagenntbot-beat-1 --tail 50
```

## 📝 Checklist

- [ ] Backend running in Docker (`docker ps`)
- [ ] Can access `http://localhost:8000/api/v1/tasks/`
- [ ] ngrok/cloudflared installed
- [ ] Tunnel running and got public URL
- [ ] Updated `NEXT_PUBLIC_API_URL` in Vercel
- [ ] Redeployed frontend in Vercel
- [ ] Tested dashboard - shows correct status
- [ ] Tasks show "available" or "sold_out" (not "unknown")

## 🚀 Quick Commands

**Test backend locally**:
```bash
curl http://localhost:8000/api/v1/tasks/ | python -m json.tool
```

**Start ngrok**:
```bash
ngrok http 8000
```

**Start Cloudflare tunnel**:
```bash
cloudflared tunnel --url http://localhost:8000
```

**Check Docker containers**:
```bash
docker ps
docker logs travelagenntbot-backend-1 --tail 50
```

**Restart services**:
```bash
docker-compose restart backend worker_vatican beat
```

## 📚 More Info

- Full setup guide: `VERCEL_DASHBOARD_SETUP.md`
- Dashboard verification: `DASHBOARD_VERIFICATION_GUIDE.md`
- Frontend integration: `FRONTEND_UNKNOWN_FIX.md`

## 💡 Recommended Next Steps

1. **Right now**: Use ngrok for quick testing
2. **This week**: Deploy to Railway/Render for permanent URL
3. **Production**: Use custom domain with SSL

---

**Need help?** Run: `powershell -ExecutionPolicy Bypass -File get_backend_url.ps1`
