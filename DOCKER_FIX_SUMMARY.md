# Docker Fix Summary

## Issues Found and Fixed

### 1. **Docker Services Not Running**
**Problem:** All Docker containers were stopped.

**Solution:** Started all services with `docker-compose up -d`

---

### 2. **Django Migration Conflict**
**Problem:** Backend service had conflicting migrations:
- `0002_proxy_sitecredential.py`
- `0002_remove_unused_extension_fields.py`

Both migrations had the same number (0002) and depended on `0001_initial`, creating a conflict.

**Error Message:**
```
CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph: 
(0002_remove_unused_extension_fields, 0026_add_target_total_to_bulkhold in monitors).
To fix them run 'python manage.py makemigrations --merge'
```

**Solution:** Created a merge migration file `0027_merge_migrations.py` that resolves both branches:
```python
class Migration(migrations.Migration):
    dependencies = [
        ('monitors', '0002_proxy_sitecredential'),
        ('monitors', '0002_remove_unused_extension_fields'),
        ('monitors', '0026_add_target_total_to_bulkhold'),
    ]
    operations = []
```

---

### 3. **Harvester Container Restart Loop**
**Problem:** Harvester container was continuously restarting due to Chrome browser failing to launch.

**Error Message:**
```
Exception: Failed to connect to browser
One of the causes could be when you are running as root.
In that case you need to pass no_sandbox=True
```

**Root Cause:** The harvester was running as root user in Docker, which Chrome doesn't allow for security reasons.

**Solution:** Updated `harvester/Dockerfile` to create and use a non-root user:
```dockerfile
# Create non-root user for Chrome
RUN groupadd -r harvester && useradd -r -g harvester -G audio,video harvester \
    && mkdir -p /home/harvester/Downloads \
    && chown -R harvester:harvester /app /home/harvester

# Switch to non-root user
USER harvester
```

---

## Current Status

All services are now **running successfully**:

| Service | Status | Ports |
|---------|--------|-------|
| **backend** | ✅ Up | 8000 |
| **beat** | ✅ Up | - |
| **db** (PostgreSQL) | ✅ Up | 5432 |
| **frontend** | ✅ Up | 3000 |
| **harvester** | ✅ Up | - |
| **nginx** | ✅ Up | 80, 443 |
| **redis** | ✅ Up (healthy) | 6379 |
| **solver** | ✅ Up | - |
| **telegram_bot** | ✅ Up | - |
| **worker_vatican** | ✅ Up | - |

---

## Verification Commands

Check all services:
```bash
docker-compose ps
```

Check specific service logs:
```bash
docker-compose logs --tail=50 backend
docker-compose logs --tail=50 worker_vatican
docker-compose logs --tail=50 harvester
docker-compose logs --tail=50 telegram_bot
```

Check if Vatican monitoring is working:
```bash
docker-compose logs worker_vatican | grep "SEARCH API CHECK"
```

---

## Notes

1. **Docker Compose Version Warning:** The `version` attribute in `docker-compose.yml` is obsolete and can be removed (it's just a warning, not an error).

2. **Orphan Container:** There's an orphan container `travelagenntbot-recap_scanner-1` that can be cleaned up with:
   ```bash
   docker-compose up -d --remove-orphans
   ```

3. **Worker Vatican:** The worker is actively processing Vatican ticket checks using the Search API approach (as per VATICAN_BOT_RULES.md).

4. **Telegram Bot:** Successfully connected and polling for updates.

5. **Harvester:** Now successfully launching Chrome browser and harvesting Vatican cookies.

---

## Date Fixed
May 13, 2026 at 14:27 CET
