# Frontend Dashboard Not Showing Data - Fix

## Problem
The frontend dashboard at https://bot-pl2x.vercel.app/ is not showing current status/data.

## Root Cause
The frontend on Vercel doesn't know where to find the backend API. It needs the backend URL to be configured.

## Solution

### Option 1: Use Cloudflare Tunnel (Recommended)
Expose your local backend to the internet using Cloudflare Tunnel, then configure Vercel to use that URL.

#### Step 1: Start Cloudflare Tunnel
```powershell
# Install cloudflared if not already installed
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# Start tunnel to expose backend
cloudflared tunnel --url http://localhost:8000
```

This will give you a public URL like: `https://random-name.trycloudflare.com`

#### Step 2: Configure Vercel Environment Variable
1. Go to https://vercel.com/your-project/settings/environment-variables
2. Add/Update: `NEXT_PUBLIC_API_URL` = `https://random-name.trycloudflare.com`
3. Redeploy the frontend

### Option 2: Deploy Backend to Cloud
Deploy the backend to a cloud service (Railway, Render, Fly.io, etc.) and use that URL.

#### Example with Railway:
1. Push code to GitHub
2. Connect Railway to your repo
3. Deploy backend service
4. Get public URL (e.g., `https://your-app.railway.app`)
5. Set Vercel env var: `NEXT_PUBLIC_API_URL` = `https://your-app.railway.app`

### Option 3: Use ngrok (Alternative to Cloudflare)
```powershell
# Install ngrok from https://ngrok.com/download

# Start tunnel
ngrok http 8000
```

Get the public URL (e.g., `https://abc123.ngrok.io`) and set it in Vercel.

## Current Frontend API Configuration

The frontend (`frontend/src/lib/api.ts`) uses this logic:

```typescript
const getApiUrl = (): string => {
    // 1. Check environment variable first
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl) {
        return envUrl.endsWith('/api/v1') ? envUrl : `${envUrl.replace(/\/$/, '')}/api/v1`;
    }

    // 2. Client-side fallback
    if (typeof window !== 'undefined') {
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        
        // Dev mode fallback
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8000/api/v1';
        }
        
        // Subdomain/Relative fallback
        return `${protocol}//${hostname}/api/v1`;
    }
    
    // 3. Server-side (SSR) fallback
    return 'http://backend:8000/api/v1';
};
```

## Verification

### Test Backend API
```powershell
# Test that backend is working
curl http://localhost:8000/api/v1/tasks/
```

Expected: JSON response with task data

### Test Frontend Connection
1. Open browser console on https://bot-pl2x.vercel.app/
2. Check Network tab for API calls
3. Look for errors like "Failed to fetch" or "CORS error"

## Quick Test with Cloudflare Tunnel

```powershell
# Terminal 1: Start backend (if not running)
docker-compose up backend

# Terminal 2: Start Cloudflare tunnel
cloudflared tunnel --url http://localhost:8000

# Copy the public URL (e.g., https://abc-def-ghi.trycloudflare.com)

# Terminal 3: Test the public URL
curl https://abc-def-ghi.trycloudflare.com/api/v1/tasks/
```

If this works, set the URL in Vercel and redeploy.

## Vercel Deployment Steps

1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add/Update:
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://your-backend-url.com` (without /api/v1 suffix)
5. Go to Deployments
6. Click "..." on latest deployment → Redeploy

## Alternative: Deploy Everything to Same Domain

If you want to avoid CORS issues entirely, deploy both frontend and backend to the same domain:

1. Deploy backend to Railway/Render at `https://myapp.railway.app`
2. Deploy frontend to Vercel at `https://myapp.vercel.app`
3. Configure Vercel to proxy `/api/*` requests to backend
4. Add `vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://myapp.railway.app/api/:path*"
    }
  ]
}
```

## Status
⚠️ **ACTION REQUIRED** - Backend URL needs to be configured in Vercel environment variables.

Choose one of the options above and configure the frontend to connect to your backend.
