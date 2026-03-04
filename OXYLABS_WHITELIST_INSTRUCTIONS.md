# Oxylabs IP Whitelist Instructions

## Your Public IP Address

```
151.25.69.162
```

**Note:** Both your Windows machine and Docker containers use the same public IP.

---

## Why Proxies Are Failing

Oxylabs ISP proxies require IP whitelisting for authentication. Your current IP (`151.25.69.162`) is likely not whitelisted in your Oxylabs dashboard, causing all connections to timeout.

---

## Steps to Whitelist Your IP

### 1. Login to Oxylabs Dashboard
Go to: https://dashboard.oxylabs.io/

### 2. Navigate to ISP Proxies
- Click on "Proxies" in the left menu
- Select "ISP Proxies" (or "Shared ISP Proxies")

### 3. Find IP Whitelist Section
Look for one of these sections:
- "IP Whitelist"
- "Access Control"
- "Allowed IPs"
- "Authentication"

### 4. Add Your IP
```
151.25.69.162
```

**Options:**
- Add single IP: `151.25.69.162`
- Add IP range (if you have dynamic IP): `151.25.69.0/24`

### 5. Save Changes
Click "Save" or "Update" button

### 6. Wait for Propagation
- Changes take 1-2 minutes to propagate
- Some providers take up to 5 minutes

### 7. Test the Connection
```bash
python test_oxylabs_direct_vatican.py
```

---

## Alternative: Use Username/Password Authentication

If IP whitelisting doesn't work, check if Oxylabs supports username/password authentication for ISP proxies:

### Current Configuration:
```python
proxy_config = {
    "server": "http://isp.oxylabs.io:8001",
    "username": "abiilesh_2uVXW",
    "password": "Abiilesh@2005"
}
```

### Check Oxylabs Dashboard:
1. Go to ISP Proxies section
2. Look for "Authentication Method"
3. Options might be:
   - IP Whitelist only
   - Username/Password only
   - Both (IP + Username/Password)

---

## Troubleshooting

### If Still Not Working After Whitelisting:

#### 1. Verify IP is Correct
```powershell
# Windows
Invoke-RestMethod -Uri "https://api.ipify.org?format=json"

# Docker
docker-compose exec backend curl -s https://api.ipify.org
```

#### 2. Check Proxy Credentials
- Username: `abiilesh_2uVXW`
- Password: `Abiilesh@2005`
- Verify these are correct in Oxylabs dashboard

#### 3. Check Proxy Status
- Login to Oxylabs dashboard
- Check if proxies are active
- Check if subscription is valid
- Check if there are any service issues

#### 4. Test with curl
```bash
# Test proxy connectivity
curl -x http://abiilesh_2uVXW:Abiilesh@2005@isp.oxylabs.io:8001 https://api.ipify.org

# Should return the proxy's IP, not your IP
```

#### 5. Check Proxy Type
ISP proxies have different configurations:
- **Shared ISP**: Multiple users share same IPs
- **Dedicated ISP**: You have exclusive IPs
- **Rotating ISP**: IPs rotate on each request

Make sure you're using the correct proxy type and configuration.

---

## Expected Behavior After Whitelisting

### Before Whitelisting:
```
❌ FAILED: Page.goto: Timeout 45000ms exceeded.
```

### After Whitelisting:
```
✅ Browser launch: 0.23s
✅ Navigation: 12.5s (slower with proxy)
✅ Got JSESSIONID: 2639226AEF0E37F858FD...
✅ Found 9 ticket IDs
✅ SUCCESS! 11 slots available
```

**Expected timing with proxy:** 12-15 seconds (vs 9s without proxy)

---

## Alternative Solutions

### Option 1: No Proxy (Recommended for Now)
- Works perfectly: 9 seconds
- No additional cost
- Simpler setup
- Use this while fixing Oxylabs

### Option 2: Residential Proxies
If Oxylabs ISP doesn't work, consider:
- **Bright Data** (formerly Luminati)
- **Smartproxy**
- **Oxylabs Residential** (different from ISP)

These are more expensive but work better with strict sites like Vatican.

### Option 3: Rotating Proxies
- Use proxy rotation service
- Automatically switches IPs
- Better for avoiding rate limits

---

## Quick Test Command

After whitelisting, run:
```bash
python test_oxylabs_direct_vatican.py
```

Expected output:
```
✅ TOTAL TIME: 12.5s
✅ Found 9 ticket IDs
✅ SUCCESS! 11 slots available
```

---

## Contact Oxylabs Support

If issues persist:
1. Email: support@oxylabs.io
2. Live chat: https://oxylabs.io/
3. Provide:
   - Your username: `abiilesh_2uVXW`
   - Your IP: `151.25.69.162`
   - Error: "Connection timeout when using ISP proxies"
   - Target site: tickets.museivaticani.va

---

## Summary

**Your IP to whitelist:** `151.25.69.162`

**Steps:**
1. Login to Oxylabs dashboard
2. Go to ISP Proxies → IP Whitelist
3. Add: `151.25.69.162`
4. Save and wait 2 minutes
5. Test: `python test_oxylabs_direct_vatican.py`

**If it works:** You'll see 12-15 second timing (acceptable)
**If it doesn't work:** Use no proxy (9 seconds, works perfectly)
