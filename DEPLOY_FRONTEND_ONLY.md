# Deploy Frontend Only to Your Domain 🌐

**Goal:** Deploy only the frontend to your domain while backend stays local  
**Setup:** Frontend on your domain → Backend on localhost (your machine)  
**Benefits:** Users can access dashboard, you control backend locally

---

## 🎯 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID DEPLOYMENT                        │
│                                                              │
│  🌐 Frontend (Public)                                      │
│     • Deployed to your domain                               │
│     • Users access: https://yourdomain.com                  │
│     • Next.js static/server deployment                      │
│                                                              │
│  🏠 Backend (Local)                                         │
│     • Running on your machine                               │
│     • API: http://your-ip:8000                              │
│     • Docker containers locally                             │
│                                                              │
│  🔗 Connection                                              │
│     • Frontend calls your public IP                         │
│     • CORS configured for your domain                       │
│     • API proxy for security                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Options for Frontend

### Option 1: Vercel (Recommended)
**Pros:**
- ✅ Free tier generous
- ✅ Automatic deployments from Git
- ✅ Custom domain support
- ✅ Global CDN
- ✅ HTTPS automatic

### Option 2: Netlify
**Pros:**
- ✅ Free tier available
- ✅ Easy custom domain setup
- ✅ Form handling
- ✅ Edge functions

### Option 3: Your Own Server
**Pros:**
- ✅ Full control
- ✅ Use existing infrastructure
- ✅ Custom configuration

---

## 📋 Step 1: Prepare Frontend for Deployment

### Update API Configuration
```typescript
// frontend/src/lib/api.ts
const getApiUrl = () => {
    // 1. Check for environment variable first (production)
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl) {
        return envUrl.endsWith('/api/v1') ? envUrl : `${envUrl.replace(/\/$/, '')}/api/v1`;
    }

    // 2. Client-side (Browser) logic
    if (typeof window !== 'undefined') {
        // Production: Use your public IP/domain for API
        return 'http://YOUR_PUBLIC_IP:8000/api/v1';
        // Or if you have API subdomain: https://api.yourdomain.com/api/v1
    }

    // 3. Server-side fallback
    return 'http://YOUR_PUBLIC_IP:8000/api/v1';
};
```

### Create Production Environment
```bash
# frontend/.env.production
NEXT_PUBLIC_API_URL=http://YOUR_PUBLIC_IP:8000/api/v1
# Or: NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

### Build Configuration
```json
// frontend/package.json - Add build scripts
{
  "scripts": {
    "build": "next build",
    "export": "next export",
    "deploy": "npm run build && npm run export"
  }
}
```

---

## 🔧 Step 2: Configure Backend for Public Access

### Update CORS Settings
```python
# backend/core/settings.py
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "http://localhost:3000",  # Keep for local development
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Security: Only allow your domain
```

### Expose Backend Publicly
```yaml
# docker-compose.yml - Update backend service
services:
  backend:
    # ... existing config
    ports:
      - "0.0.0.0:8000:8000"  # Expose to all interfaces
    environment:
      - ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_PUBLIC_IP,yourdomain.com
```

### Get Your Public IP
```bash
# Find your public IP
curl ifconfig.me
# Or
curl ipinfo.io/ip

# Example result: 203.0.113.45
```

---

## 🌐 Step 3: Deploy Frontend to Vercel

### Method A: Vercel CLI (Recommended)
```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Navigate to frontend
cd frontend

# 3. Set production environment
echo "NEXT_PUBLIC_API_URL=http://YOUR_PUBLIC_IP:8000/api/v1" > .env.production

# 4. Deploy to Vercel
vercel --prod

# 5. Configure custom domain in Vercel dashboard
# Go to vercel.com → Your Project → Settings → Domains
# Add: yourdomain.com
```

### Method B: GitHub Integration
```bash
# 1. Push frontend to GitHub repository
git add frontend/
git commit -m "Frontend ready for deployment"
git push origin main

# 2. Connect to Vercel
# - Go to vercel.com
# - Import from GitHub
# - Select your repository
# - Set root directory to "frontend"
# - Add environment variable: NEXT_PUBLIC_API_URL

# 3. Configure custom domain
# - Vercel Dashboard → Domains → Add yourdomain.com
```

---

## 🔒 Step 4: Secure the Setup

### Backend Security
```python
# backend/core/settings.py
# Only allow your domain and IP
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'YOUR_PUBLIC_IP',
    'yourdomain.com',
]

# Rate limiting (install django-ratelimit)
RATELIMIT_ENABLE = True
```

### Firewall Configuration
```bash
# If using UFW (Ubuntu firewall)
sudo ufw allow 8000/tcp  # Allow API port
sudo ufw enable

# Or configure your router to forward port 8000
```

### API Proxy (Optional - More Secure)
```nginx
# If you want to proxy API through your domain
# nginx configuration for api.yourdomain.com
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://YOUR_LOCAL_IP:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📋 Step 5: Domain Configuration

### DNS Settings
```
# Add these DNS records to your domain:

A Record:
Name: @
Value: YOUR_VERCEL_IP (Vercel provides this)

CNAME Record:
Name: www
Value: yourdomain.com

# Optional: API subdomain
A Record:
Name: api
Value: YOUR_PUBLIC_IP
```

### SSL Certificate
```bash
# Vercel automatically provides HTTPS for your domain
# No additional configuration needed
```

---

## 🧪 Step 6: Test the Setup

### Test Frontend
```bash
# 1. Visit your domain
https://yourdomain.com

# 2. Should see agency selection screen
# 3. Try selecting an agency
# 4. Check browser console for API calls
```

### Test API Connection
```bash
# Test API from your domain
curl https://yourdomain.com/api/test
# Should connect to your local backend

# Test direct API access
curl http://YOUR_PUBLIC_IP:8000/api/v1/agencies/
# Should return agency data
```

---

## 🔧 Complete Setup Example

### 1. Update Frontend API URL
```typescript
// frontend/src/lib/api.ts
const getApiUrl = () => {
    // Use your public IP for API calls
    return process.env.NEXT_PUBLIC_API_URL || 'http://203.0.113.45:8000/api/v1';
};
```

### 2. Update Backend CORS
```python
# backend/core/settings.py
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

### 3. Deploy Frontend
```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=http://203.0.113.45:8000/api/v1" > .env.production
vercel --prod
# Configure yourdomain.com in Vercel dashboard
```

### 4. Restart Backend
```bash
docker-compose restart backend
```

---

## 🎯 Benefits of This Setup

### ✅ Advantages
- **Frontend publicly accessible** - Users can access from anywhere
- **Backend stays local** - You maintain full control
- **Cost effective** - Only frontend hosting costs
- **Easy updates** - Deploy frontend changes instantly
- **Security** - Backend not exposed to internet attacks

### ⚠️ Considerations
- **Your machine must stay online** - Backend needs to run 24/7
- **Public IP required** - Frontend needs to reach your backend
- **Firewall configuration** - Port 8000 must be accessible
- **Dynamic IP issues** - If your IP changes, update frontend

---

## 🚀 Quick Deployment Commands

```bash
# 1. Get your public IP
MY_IP=$(curl -s ifconfig.me)
echo "Your public IP: $MY_IP"

# 2. Update frontend environment
cd frontend
echo "NEXT_PUBLIC_API_URL=http://$MY_IP:8000/api/v1" > .env.production

# 3. Deploy to Vercel
vercel --prod

# 4. Configure your domain in Vercel dashboard
echo "Add yourdomain.com in Vercel → Settings → Domains"

# 5. Update backend CORS
echo "Update CORS_ALLOWED_ORIGINS in backend/core/settings.py"

# 6. Restart backend
cd ..
docker-compose restart backend
```

---

## 📞 What's Your Domain?

**To complete the setup, I need to know:**

1. **Your domain name** (e.g., `vatican-tickets.com`)
2. **Your public IP** (run `curl ifconfig.me`)
3. **Preferred deployment method** (Vercel recommended)

**Once you provide these, I can give you the exact commands to deploy your frontend to your domain while keeping the backend local!**

**Ready to deploy? What's your domain name?** 🌐