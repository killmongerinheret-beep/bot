# 🔧 Proxy Setup & Automatic Rotation Guide

## 🚨 Current Situation

Your backend is **NOT using proxies** - all 685 requests are coming from your direct IP, causing instant rate limiting.

**Logs show:**
```
⚠️ Search/timeavail error: Read timed out (8 seconds)
⚠️ Search/timeavail error: Read timed out (8 seconds)
⚠️ Search/timeavail error: Read timed out (8 seconds)
... (hundreds of timeouts)
```

**This means:** Vatican blocked your IP completely.

---

## ✅ Solution: Add Proxies with Automatic Rotation

I've added automatic proxy rotation that:
1. **Tries up to 3 different proxies** per request
2. **Detects rate limiting** (429, 503, timeouts)
3. **Puts rate-limited proxies on 15-minute cooldown**
4. **Automatically rotates** to next available proxy
5. **Logs proxy usage** for monitoring

---

## 📋 Step 1: Add Your Proxies

### Option A: Using the Script (Recommended)

1. **Edit `add_proxies.py`:**
```python
PROXIES = [
    "proxy1.example.com:8080:username1:password1",
    "proxy2.example.com:8080:username2:password2",
    "proxy3.example.com:8080:username3:password3",
    # Add all your proxies here
]
```

2. **Run the script:**
```bash
docker exec -it travelagenntbot-backend-1 sh -c "cd /app && python add_proxies.py"
```

3. **Verify:**
```bash
docker exec -it travelagenntbot-backend-1 sh -c "cd backend && python manage.py shell -c 'from monitors.models import Proxy; print(f\"Total proxies: {Proxy.objects.count()}\")'"
```

### Option B: Using Django Admin

1. **Go to:** http://localhost:8000/admin/
2. **Login** with your admin credentials
3. **Navigate to:** Monitors → Proxies
4. **Click "Add Proxy"**
5. **Fill in:**
   - IP:Port: `142.111.48.253:7030`
   - Username: `your_username`
   - Password: `your_password`
   - Is Active: ✅ Checked
6. **Save** and repeat for all proxies

### Option C: Using Django Shell

```bash
docker exec -it travelagenntbot-backend-1 sh -c "cd backend && python manage.py shell"
```

```python
from monitors.models import Proxy

# Add single proxy
Proxy.objects.create(
    ip_port="142.111.48.253:7030",
    username="user123",
    password="pass456",
    is_active=True
)

# Add multiple proxies
proxies = [
    ("proxy1.com:8080", "user1", "pass1"),
    ("proxy2.com:8080", "user2", "pass2"),
    ("proxy3.com:8080", "user3", "pass3"),
]

for ip_port, username, password in proxies:
    Proxy.objects.create(
        ip_port=ip_port,
        username=username,
        password=password,
        is_active=True
    )

# Check count
print(f"Total proxies: {Proxy.objects.count()}")
```

---

## 📊 Step 2: Verify Proxy Setup

### Check Proxy Count
```bash
docker exec -it travelagenntbot-backend-1 sh -c "cd backend && python manage.py shell -c 'from monitors.models import Proxy; print(f\"Active: {Proxy.objects.filter(is_active=True).count()}\")'"
```

### List All Proxies
```bash
docker exec -it travelagenntbot-backend-1 sh -c "cd backend && python manage.py shell -c 'from monitors.models import Proxy; [print(f\"{p.ip_port} - Active: {p.is_active}\") for p in Proxy.objects.all()]'"
```

### Test Single Proxy
```bash
docker exec -it travelagenntbot-backend-1 sh -c "cd backend && python manage.py shell"
```

```python
from worker_vatican.search_api_monitor import VaticanSearchAPIMonitor

# Test with proxy
monitor = VaticanSearchAPIMonitor(proxy_str="http://user:pass@proxy.com:8080")
tickets = monitor.resolve_ticket_ids("17/06/2026", 1, 0)
print(f"Found {len(tickets)} tickets")
```

---

## 🔄 Step 3: Restart Backend

After adding proxies, restart the backend:

```bash
# Stop backend
docker-compose stop

# Wait 2-4 hours for Vatican to forget your IP
# (or use proxies immediately if you have many)

# Start backend
docker-compose up -d
```

---

## 📈 Step 4: Monitor Proxy Usage

### Watch Logs for Proxy Rotation
```bash
docker logs -f travelagenntbot-worker_vatican-1 | grep -E "proxy|Proxy|PROXY|cooldown|rotation"
```

**You should see:**
```
🔄 Attempt 1/3 using proxy: 142.111.48.253:7030
✅ 15 slots for Musei Vaticani 17/06/2026
🔄 Attempt 1/3 using proxy: 142.111.48.254:7030
⚠️ RATE LIMITED on attempt 1: Timeout
🔒 Proxy 142.111.48.254:7030 on cooldown for 15 minutes
🔄 Retrying with different proxy...
🔄 Attempt 2/3 using proxy: 142.111.48.255:7030
✅ 12 slots for Musei Vaticani 18/06/2026
```

### Check Proxy Cooldowns
```bash
docker exec -it travelagenntbot-backend-1 sh -c "cd backend && python manage.py shell -c 'from monitors.models import Proxy; from django.utils import timezone; [print(f\"{p.ip_port} - Cooldown: {p.cooldown_until}\") for p in Proxy.objects.filter(cooldown_until__gt=timezone.now())]'"
```

---

## 🎯 How Automatic Rotation Works

### 1. Request Starts
```python
# Backend picks random active proxy not on cooldown
proxy_str, proxy_obj = get_proxy_str('vatican')
# Returns: "http://user:pass@142.111.48.253:7030"
```

### 2. Rate Limit Detected
```python
# Monitor detects timeout or 429/503 status
except requests.exceptions.Timeout:
    logger.error("⚠️ RATE LIMITED")
    
    # Put proxy on 15-minute cooldown
    proxy_obj.cooldown_until = timezone.now() + timedelta(minutes=15)
    proxy_obj.save()
```

### 3. Retry with Different Proxy
```python
# Try up to 3 different proxies
for attempt in range(3):
    proxy_str, proxy_obj = get_proxy_str('vatican')  # Gets different proxy
    # ... try request ...
```

### 4. Success or Skip
```python
# If any proxy succeeds, continue
# If all 3 fail, skip this check and try next time
```

---

## 📊 Proxy Requirements

### Minimum Recommended
- **10-20 proxies** for light monitoring (1-10 dates)
- **50-100 proxies** for medium monitoring (10-50 dates)
- **100-200 proxies** for heavy monitoring (50+ dates)

### Proxy Types

| Type | Speed | Cost | Recommended |
|------|-------|------|-------------|
| **Residential** | Medium | High | ✅ Best (looks like real users) |
| **Datacenter** | Fast | Low | ⚠️ OK (may get blocked faster) |
| **Mobile** | Slow | Very High | ✅ Best (rarely blocked) |

### Recommended Providers
- **Oxylabs** - Residential proxies (premium)
- **Bright Data** - Residential proxies (premium)
- **Smartproxy** - Residential proxies (mid-range)
- **Webshare** - Datacenter proxies (budget)

---

## 🔧 Troubleshooting

### Issue 1: No Proxies Being Used

**Check logs:**
```bash
docker logs travelagenntbot-worker_vatican-1 --tail 50 | grep proxy
```

**If you see:**
```
⚠️ No proxies available, using direct IP
```

**Fix:**
1. Verify proxies in database: `Proxy.objects.count()`
2. Check if proxies are active: `Proxy.objects.filter(is_active=True).count()`
3. Check if all on cooldown: `Proxy.objects.filter(cooldown_until__gt=timezone.now()).count()`

### Issue 2: All Proxies on Cooldown

**Check:**
```bash
docker exec -it travelagenntbot-backend-1 sh -c "cd backend && python manage.py shell -c 'from monitors.models import Proxy; from django.utils import timezone; print(f\"On cooldown: {Proxy.objects.filter(cooldown_until__gt=timezone.now()).count()}\")'"
```

**Fix:**
1. Add more proxies
2. Reduce monitoring frequency
3. Wait for cooldowns to expire (15 minutes)

### Issue 3: Proxies Not Working

**Test proxy manually:**
```bash
curl -x http://user:pass@proxy.com:8080 https://tickets.museivaticani.va/
```

**If fails:**
- Check proxy credentials
- Check proxy is online
- Check proxy allows HTTPS
- Contact proxy provider

### Issue 4: Still Getting Timeouts

**Possible causes:**
1. **All proxies rate limited** - Add more proxies
2. **Proxies too slow** - Use faster proxies
3. **Vatican blocking proxy IPs** - Use residential proxies
4. **Too many concurrent requests** - Reduce worker count

**Fix:**
```bash
# Reduce worker concurrency
docker-compose down
# Edit docker-compose.yml: worker_vatican concurrency to 4-8
docker-compose up -d
```

---

## 📈 Monitoring Dashboard

### Check Proxy Health
```python
from monitors.models import Proxy
from django.utils import timezone

total = Proxy.objects.count()
active = Proxy.objects.filter(is_active=True).count()
on_cooldown = Proxy.objects.filter(cooldown_until__gt=timezone.now()).count()
available = active - on_cooldown

print(f"Total: {total}")
print(f"Active: {active}")
print(f"On Cooldown: {on_cooldown}")
print(f"Available: {available}")
print(f"Health: {(available/active*100):.1f}%")
```

### Reset All Cooldowns (Emergency)
```python
from monitors.models import Proxy

# Clear all cooldowns
Proxy.objects.update(cooldown_until=None)
print("✅ All cooldowns cleared")
```

---

## 🎯 Best Practices

### 1. Proxy Pool Size
- **Rule of thumb:** 1 proxy per 5-10 dates monitored
- **Example:** Monitoring 60 dates = need 10-15 proxies minimum

### 2. Rotation Strategy
- ✅ Random selection (current implementation)
- ✅ Cooldown on rate limit (15 minutes)
- ✅ Retry with different proxy (up to 3 attempts)

### 3. Monitoring Frequency
- **With proxies:** Can check every 30-60 seconds
- **Without proxies:** Must check every 5-10 minutes

### 4. Proxy Maintenance
- **Check daily:** Verify proxies still working
- **Replace dead proxies:** Remove non-responsive ones
- **Rotate credentials:** Change passwords monthly

---

## 📝 Summary

**Before (No Proxies):**
```
❌ All requests from same IP
❌ Instant rate limiting
❌ 685 timeouts
❌ No monitoring possible
```

**After (With Proxies):**
```
✅ Requests distributed across proxies
✅ Automatic rotation on rate limit
✅ 15-minute cooldown per proxy
✅ Up to 3 retry attempts
✅ Continuous monitoring possible
```

**Next Steps:**
1. ✅ Add your proxies using `add_proxies.py`
2. ✅ Verify proxies in database
3. ✅ Wait 2-4 hours for IP cooldown
4. ✅ Restart backend: `docker-compose restart`
5. ✅ Monitor logs for proxy rotation
6. ✅ Enjoy 24/7 monitoring! 🎉

---

**Last Updated:** May 2, 2026  
**Status:** Proxy rotation implemented ✅  
**Ready for:** Production use with proxies
