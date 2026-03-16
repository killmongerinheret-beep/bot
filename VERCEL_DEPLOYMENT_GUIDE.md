# Vercel Deployment Guide

## 🚀 Deploy Frontend to Vercel

### Prerequisites
- GitHub repository: https://github.com/killmongerinheret-beep/bot-front.git
- Vercel account (free tier works)
- Backend running at: http://151.25.69.162:8000

---

## 📋 Step-by-Step Deployment

### Step 1: Push Frontend Code to GitHub

```bash
# Navigate to frontend directory
cd frontend

# Initialize git if not already done
git init

# Add remote (your repository)
git remote add origin https://github.com/killmongerinheret-beep/bot-front.git

# Add all files
git add .

# Commit
git commit -m "Initial frontend deployment"

# Push to main branch
git push -u origin main
```

### Step 2: Connect to Vercel

1. Go to https://vercel.com
2. Sign in with GitHub
3. Click "Add New Project"
4. Import your repository: `killmongerinheret-beep/bot-front`
5. Configure project settings (see below)

### Step 3: Configure Environment Variables

In Vercel project settings, add these environment variables:

```
NEXT_PUBLIC_API_URL=http://151.25.69.162:8000/api/v1
```

**Important**: If you want to use HTTPS, you'll need to set up SSL on your backend first.

### Step 4: Configure Build Settings

Vercel should auto-detect Next.js, but verify:

- **Framework Preset**: Next.js
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`
- **Root Directory**: `./` (or leave empty)

### Step 5: Deploy

Click "Deploy" and wait for the build to complete.

---

## 🔧 Required Configuration Files

### 1. vercel.json (Already created below)

This file configures Vercel deployment settings.

### 2. .env.production (Already created below)

Production environment variables.

### 3. next.config.js (Update if needed)

Ensure CORS and API proxy are configured.

---

## 🌐 CORS Configuration

Since your backend is on a different domain, you need to enable CORS on the backend.

### Backend CORS Setup (Django)

Add to `backend/core/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://your-vercel-app.vercel.app",
    "http://localhost:3000",
    "http://151.25.69.162",
]

CORS_ALLOW_CREDENTIALS = True
```

---

## 📝 Post-Deployment Checklist

- [ ] Frontend deployed to Vercel
- [ ] Environment variables set
- [ ] Backend CORS configured
- [ ] Can access login page
- [ ] Can login successfully
- [ ] API calls work
- [ ] Session persists
- [ ] All features working

---

## 🔗 Expected URLs

- **Vercel Frontend**: `https://bot-front-xxx.vercel.app`
- **Backend API**: `http://151.25.69.162:8000/api/v1`
- **Login Page**: `https://bot-front-xxx.vercel.app`

---

## 🐛 Troubleshooting

### Issue: API calls fail with CORS error
**Solution**: Add Vercel domain to backend CORS_ALLOWED_ORIGINS

### Issue: Environment variables not working
**Solution**: Redeploy after adding environment variables

### Issue: Build fails
**Solution**: Check build logs in Vercel dashboard

### Issue: 404 on routes
**Solution**: Ensure Next.js routing is configured correctly

---

## 🔄 Continuous Deployment

Once connected, Vercel will automatically deploy:
- **Main branch**: Production deployment
- **Other branches**: Preview deployments
- **Pull requests**: Preview deployments

Every push to GitHub triggers a new deployment!

---

## 📊 Monitoring

Vercel provides:
- Build logs
- Runtime logs
- Analytics
- Performance metrics

Access these in the Vercel dashboard.

---

## 🎯 Next Steps After Deployment

1. Test all functionality on Vercel URL
2. Update any hardcoded URLs
3. Configure custom domain (optional)
4. Set up SSL for backend (recommended)
5. Monitor performance and errors
