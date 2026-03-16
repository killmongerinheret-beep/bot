# Docker Storage Cleanup Guide

## Current Usage Analysis
- **Images:** 26.5GB (24.69GB reclaimable - 93%)
- **Build Cache:** 23.22GB (12.45GB reclaimable)
- **Local Volumes:** 235.5MB (93.08MB reclaimable - 39%)
- **Containers:** 68.48MB (all in use)

**Total Reclaimable:** ~37GB

---

## Safe Cleanup Steps

### Step 1: Clean Build Cache (Safe - 12.45GB)
```bash
# Remove unused build cache
docker builder prune -f

# Or more aggressive (removes all cache)
docker builder prune -a -f
```

### Step 2: Remove Unused Images (Safe - 24.69GB)
```bash
# Remove dangling images (safe)
docker image prune -f

# Remove all unused images (more aggressive)
docker image prune -a -f
```

### Step 3: Clean Unused Volumes (Careful - 93MB)
```bash
# List volumes first to check
docker volume ls

# Remove unused volumes (be careful with databases)
docker volume prune -f
```

### Step 4: Remove Stopped Containers (Safe)
```bash
# Remove all stopped containers
docker container prune -f
```

### Step 5: Complete System Cleanup (Most Aggressive)
```bash
# Clean everything unused in one command
docker system prune -a -f --volumes
```

---

## Recommended Cleanup Sequence

### Option 1: Conservative (Safe)
```bash
# 1. Clean build cache (12.45GB)
docker builder prune -f

# 2. Remove dangling images only
docker image prune -f

# 3. Remove stopped containers
docker container prune -f
```

### Option 2: Aggressive (More Space)
```bash
# Clean everything except running containers and their images
docker system prune -a -f

# Clean build cache
docker builder prune -a -f
```

### Option 3: Nuclear (Maximum Space)
```bash
# ⚠️ WARNING: This removes everything unused
docker system prune -a -f --volumes
```

---

## Before Cleanup: Backup Important Data

### 1. Export Your Database (Recommended)
```bash
# Backup your database
docker-compose exec db pg_dump -U postgres ticketbot > backup_$(date +%Y%m%d).sql
```

### 2. List Current Images (For Reference)
```bash
# See what images you have
docker images

# See what's running
docker-compose ps
```

---

## Safe Cleanup Commands (Recommended)

Run these commands in order:

```bash
# 1. Clean build cache (saves ~12GB)
echo "🧹 Cleaning build cache..."
docker builder prune -f

# 2. Remove unused images (saves ~24GB)
echo "🖼️ Removing unused images..."
docker image prune -a -f

# 3. Remove stopped containers
echo "📦 Removing stopped containers..."
docker container prune -f

# 4. Show space saved
echo "💾 Checking space usage..."
docker system df
```

---

## What NOT to Delete

### Keep These Images (Your Running System)
- `travelagenntbot-backend`
- `travelagenntbot-frontend`
- `travelagenntbot-telegram_bot`
- `travelagenntbot-worker_vatican`
- `travelagenntbot-beat`
- `travelagenntbot-solver`
- `travelagenntbot-harvester`
- `postgres:15`
- `redis:7-alpine`
- `nginx:alpine`

### Keep These Volumes (Your Data)
- `root_postgres_data` (your database)
- `root_static_volume` (static files)
- Any volume with your project data

---

## After Cleanup: Verify System

```bash
# 1. Check your containers are still running
docker-compose ps

# 2. Test your system
python test_telegram_groups.py

# 3. Check API
curl http://localhost:8000/api/v1/telegram-groups/

# 4. Check space saved
docker system df
```

---

## Emergency Recovery (If Something Breaks)

### If Containers Stop
```bash
# Restart all services
docker-compose up -d
```

### If Database is Gone
```bash
# Restore from backup
docker-compose exec -T db psql -U postgres ticketbot < backup_YYYYMMDD.sql
```

### If Images are Deleted
```bash
# Rebuild everything
docker-compose build
docker-compose up -d
```

---

## Automated Cleanup Script

Create this script for regular maintenance:

```bash
#!/bin/bash
# docker_cleanup.sh

echo "🧹 Starting Docker cleanup..."

# Backup database first
echo "💾 Backing up database..."
docker-compose exec -T db pg_dump -U postgres ticketbot > "backup_$(date +%Y%m%d_%H%M%S).sql"

# Show current usage
echo "📊 Current usage:"
docker system df

# Clean build cache
echo "🏗️ Cleaning build cache..."
docker builder prune -f

# Remove unused images
echo "🖼️ Removing unused images..."
docker image prune -a -f

# Remove stopped containers
echo "📦 Removing stopped containers..."
docker container prune -f

# Show final usage
echo "✅ Cleanup complete! New usage:"
docker system df

# Verify system is running
echo "🔍 Verifying system..."
docker-compose ps
```

---

## Quick Commands

### Check Space Usage
```bash
docker system df
```

### Safe Cleanup (Recommended)
```bash
docker builder prune -f && docker image prune -a -f && docker container prune -f
```

### Nuclear Option (Use with Caution)
```bash
docker system prune -a -f --volumes
```

### Verify System After Cleanup
```bash
docker-compose ps && python test_telegram_groups.py
```

---

## Expected Results

After cleanup, you should see:
- **Build Cache:** ~0-2GB (down from 23GB)
- **Images:** ~2-5GB (down from 26GB)
- **Total Space Saved:** ~35GB
- **System:** Still running normally

Your Vatican bot system will continue working perfectly after cleanup!