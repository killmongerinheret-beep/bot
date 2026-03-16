# Update Vercel Environment Variable - Quick Guide

## 🎯 What You Need to Do

Change the environment variable in Vercel from absolute URL to relative URL.

---

## 📋 Steps (2 minutes)

### 1. Go to Vercel Dashboard
https://vercel.com/dashboard

### 2. Click Your Project
Click on `bot-front` project

### 3. Go to Settings
Click "Settings" tab at the top

### 4. Click Environment Variables
In the left sidebar, click "Environment Variables"

### 5. Edit the Variable
Find: `NEXT_PUBLIC_API_URL`

**Current Value** (wrong):
```
http://151.25.69.162:8000/api/v1
```

**New Value** (correct):
```
/api/v1
```

Click the pencil icon to edit, change the value, click "Save"

### 6. Redeploy
Vercel should auto-deploy from your git push, but if not:
- Go to "Deployments" tab
- Click "Redeploy" on latest deployment

---

## ✅ After Update

Wait 2-3 minutes for deployment, then test:
- Go to: https://bot-front-beta.vercel.app
- Login with: `agency-admin` / `agency-admin`
- Should work! No more mixed content errors!

---

**Status**: Code pushed ✅ - Just update env variable in Vercel!
