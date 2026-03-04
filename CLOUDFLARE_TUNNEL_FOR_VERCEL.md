# Cloudflare Tunnel for Vercel Dashboard
## Free, Permanent Backend URL (Better than ngrok!)

**Why Cloudflare Tunnel?**
- ✅ **FREE** forever (no time limits like ngrok)
- ✅ **Permanent URL** (doesn't change on restart)
- ✅ **Fast** (Cloudflare's global network)
- ✅ **Secure** (automatic HTTPS)
- ✅ **No account required** for quick tunnels

---

## Quick Start (5 minutes)

### Step 1: Install Cloudflared

**Windows (PowerShell as Administrator):**
```powershell
# Download cloudflared
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "C:\Windows\System32\cloudflared.exe"
```

**Or download manually:**
https://github.com/cloudflare/cloudflared/releases/latest

Download `cloudflared-windows-amd64.exe` and rename to `cloudflared.exe`

### Step 2: Start Quick Tunnel

Open PowerShell in your project directory:

```powershell
cloudflared tunnel --url http://localhost:8000
```

You'll see output like:
```
2026-03-04T15:15:00Z INF +--------------------------------------------------------------------------------------------+
2026-03-04T15:15:00Z INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
2026-03-04T15:15:00Z INF |  https://abc-def-123.trycloudflare.com                                                     |
2026-03-04T15:15:00Z INF +--------------------------------------------------------------------------------------------+
```

**Copy this URL**: `https://abc-def-123.trycloudflare.com`

### Step 3: Test the URL

Open in browser:
```
https://abc-def-123.trycloudflare.com/api/v1/tasks/
```

You should see JSON with your tasks!

### Step 4: Update Vercel

1. Go to **Vercel Dashboard**: https://vercel.com/dashboard
2. Select your project: `bot-pl2x` or similar
3. Click **Settings** → **Environment Variables**
4. Add or update:
   ```
   Name: NEXT_PUBLIC_API_URL
   Value: https://abc-def-123.trycloudflare.com/api/v1
   ```
5. Click **Save**

### Step 5: Redeploy Frontend

1. Go to **Deployments** tab
2. Click **...** on latest deployment
3. Click **Redeploy**
4. Wait ~2 minutes

### Step 6: Check Dashboard

Visit: https://bot-pl2x.vercel.app/

You should now see your tasks with real data!

---

## PowerShell Script (Easy Start)

Save this as `start_cloudflare_tunnel.ps1`:

```powershell
# Start Cloudflare Tunnel for Backend
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CLOUDFLARE TUNNEL - STARTING" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if backend is running
Write-Host "1. Checking backend..." -ForegroundColor Yellow
$backendRunning = docker-compose ps backend | Select-String "Up"

if (-not $backendRunning) {
    Write-Host "   ❌ Backend not running!" -ForegroundColor Red
    Write-Host "   Starting backend..." -ForegroundColor Yellow
    docker-compose up -d backend
    Start-Sleep -Seconds 5
}

Write-Host "   ✅ Backend is running" -ForegroundColor Green

# Check if cloudflared is installed
Write-Host "`n2. Checking cloudflared..." -ForegroundColor Yellow
$cloudflaredExists = Get-Command cloudflared -ErrorAction SilentlyContinue

if (-not $cloudflaredExists) {
    Write-Host "   ❌ cloudflared not installed!" -ForegroundColor Red
    Write-Host "   Download from: https://github.com/cloudflare/cloudflared/releases/latest" -ForegroundColor Yellow
    Write-Host "   Or run: winget install cloudflare.cloudflared" -ForegroundColor Yellow
    exit 1
}

Write-Host "   ✅ cloudflared installed" -ForegroundColor Green

# Start tunnel
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "STARTING TUNNEL" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "📡 Starting Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host "⏳ This may take 10-15 seconds...`n" -ForegroundColor Gray

Write-Host "🔗 Your tunnel URL will appear below:" -ForegroundColor Cyan
Write-Host "   Copy the https://xxx.trycloudflare.com URL" -ForegroundColor Gray
Write-Host "   Use it in Vercel as NEXT_PUBLIC_API_URL`n" -ForegroundColor Gray

Write-Host "⚠️  Keep this window open!" -ForegroundColor Yellow
Write-Host "   Closing it will stop the tunnel`n" -ForegroundColor Gray

# Start tunnel
cloudflared tunnel --url http://localhost:8000
```

Run it:
```powershell
./start_cloudflare_tunnel.ps1
```

---

## Advantages Over ngrok

| Feature | Cloudflare Tunnel | ngrok Free |
|---------|------------------|------------|
| **Cost** | FREE forever | FREE with limits |
| **Time Limit** | None | 2 hours |
| **URL Changes** | On restart only | Every restart |
| **Speed** | Very fast | Fast |
| **Setup** | 1 command | 1 command |
| **Account** | Optional | Required for features |

---

## Permanent Tunnel (Optional)

For a URL that NEVER changes, even on restart:

### 1. Create Cloudflare Account (Free)
https://dash.cloudflare.com/sign-up

### 2. Login via CLI
```powershell
cloudflared tunnel login
```

### 3. Create Named Tunnel
```powershell
cloudflared tunnel create vatican-bot
```

### 4. Configure Tunnel
Create `cloudflared-config.yml`:
```yaml
tunnel: vatican-bot
credentials-file: C:\Users\YourName\.cloudflared\<tunnel-id>.json

ingress:
  - hostname: vatican-bot.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

### 5. Run Tunnel
```powershell
cloudflared tunnel run vatican-bot
```

### 6. Add DNS Record
```powershell
cloudflared tunnel route dns vatican-bot vatican-bot.yourdomain.com
```

Now you have: `https://vatican-bot.yourdomain.com` (permanent!)

---

## Troubleshooting

### "cloudflared: command not found"

**Solution 1 - Install via winget:**
```powershell
winget install cloudflare.cloudflared
```

**Solution 2 - Manual install:**
1. Download from: https://github.com/cloudflare/cloudflared/releases/latest
2. Save as `cloudflared.exe` in `C:\Windows\System32\`

### Tunnel URL not working

**Check 1:** Is backend running?
```powershell
docker-compose ps backend
```

**Check 2:** Can you access locally?
```
http://localhost:8000/api/v1/tasks/
```

**Check 3:** Wait 30 seconds after tunnel starts

### CORS errors in browser

Add to `backend/core/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://bot-pl2x.vercel.app",
    "https://*.trycloudflare.com",
]
```

Restart backend:
```powershell
docker-compose restart backend
```

### Tunnel keeps disconnecting

**Solution:** Use named tunnel (permanent setup above)

---

## Current Setup

**Your Vercel App:** https://bot-pl2x.vercel.app/  
**Backend:** http://localhost:8000  
**Status:** Backend running, needs public URL

**Next Steps:**
1. Run: `cloudflared tunnel --url http://localhost:8000`
2. Copy the `https://xxx.trycloudflare.com` URL
3. Set in Vercel: `NEXT_PUBLIC_API_URL=https://xxx.trycloudflare.com/api/v1`
4. Redeploy Vercel frontend
5. Check dashboard!

---

## Quick Commands

**Start tunnel:**
```powershell
cloudflared tunnel --url http://localhost:8000
```

**Check backend:**
```powershell
docker-compose ps backend
```

**Restart backend:**
```powershell
docker-compose restart backend
```

**View backend logs:**
```powershell
docker-compose logs -f backend
```

---

**Created:** March 4, 2026  
**Status:** Ready to use  
**Estimated Time:** 5 minutes
