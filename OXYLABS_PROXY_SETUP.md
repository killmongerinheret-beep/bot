# Oxylabs Proxy Setup Guide

## 🎯 Goal

Configure Oxylabs residential proxies for:
1. Vatican API monitoring (worker_vatican)
2. Browser extension auto-booking
3. Avoid rate limiting and IP blocks

---

## 📋 Oxylabs Proxy Types

### Residential Proxies (Recommended)
- **Endpoint**: `pr.oxylabs.io:7777`
- **Protocol**: HTTP/HTTPS
- **Rotation**: Automatic per request
- **Countries**: 195+ countries
- **Best for**: Vatican monitoring (looks like real users)

### Datacenter Proxies
- **Endpoint**: `dc.oxylabs.io:8001`
- **Protocol**: HTTP/HTTPS
- **Rotation**: Manual or automatic
- **Best for**: High-speed bulk requests

### Rotating ISP Proxies
- **Endpoint**: `isp.oxylabs.io:8001`
- **Protocol**: HTTP/HTTPS
- **Rotation**: Sticky sessions available
- **Best for**: Long sessions (booking flow)

---

## 🔧 Configuration Methods

### Method 1: Backend Worker Proxies (Recommended)

**Use Oxylabs for Vatican API monitoring**

#### Step 1: Add Proxies to Database

```bash
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import Proxy

# Add Oxylabs Residential Proxy
Proxy.objects.create(
    host='pr.oxylabs.io',
    port=7777,
    username='your-oxylabs-username',  # Replace with your username
    password='your-oxylabs-password',  # Replace with your password
    protocol='http',
    is_active=True,
    proxy_type='residential',
    country='IT'  # Italy for Vatican
)

print("✅ Oxylabs proxy added")
exit()
```

#### Step 2: Enable Proxies in Environment

Edit `.env`:
```env
# Proxy Configuration
USE_PROXIES=True
PROXY_ROTATION=True
PROXY_TIMEOUT=30
```

#### Step 3: Restart Worker

```bash
docker-compose restart worker_vatican
```

#### Step 4: Verify Proxy Usage

```bash
# Check worker logs
docker-compose logs -f worker_vatican | grep -i proxy

# Expected output:
# [INFO] Using proxy: http://pr.oxylabs.io:7777
# [INFO] Proxy rotation enabled
# [INFO] Checking Vatican API via proxy...
# [INFO] Proxy IP: xxx.xxx.xxx.xxx (IT)
```

---

### Method 2: Chrome Extension with Proxy

**Use Oxylabs for browser extension booking**

#### Option A: Proxy SwitchyOmega (Recommended)

1. **Install Extension**:
   - Chrome Web Store: Search "Proxy SwitchyOmega"
   - Install extension

2. **Configure Oxylabs**:
   ```
   Profile Name: Oxylabs
   Proxy Protocol: HTTP
   Proxy Server: pr.oxylabs.io
   Proxy Port: 7777
   
   Authentication:
   ☑ Use authentication
   Username: your-oxylabs-username
   Password: your-oxylabs-password
   ```

3. **Enable for Incognito**:
   - `chrome://extensions/`
   - Find "Proxy SwitchyOmega"
   - Enable "Allow in incognito"

4. **Set Auto Switch**:
   ```
   Rule: *.museivaticani.va/*
   Profile: Oxylabs
   ```

5. **Test**:
   - Open incognito window
   - Visit https://ip.oxylabs.io/location
   - Should show Oxylabs IP

#### Option B: Chrome Startup with Proxy

**Windows**:
```powershell
# Create shortcut with proxy
"C:\Program Files\Google\Chrome\Application\chrome.exe" --proxy-server="http://your-username:your-password@pr.oxylabs.io:7777"
```

**Mac**:
```bash
# Launch Chrome with proxy
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --proxy-server="http://your-username:your-password@pr.oxylabs.io:7777"
```

**Linux**:
```bash
# Launch Chrome with proxy
google-chrome --proxy-server="http://your-username:your-password@pr.oxylabs.io:7777"
```

---

### Method 3: Import Proxies from JSON

**If you have a proxy list JSON file**

#### Step 1: Prepare JSON File

Your `Proxy lists (2).json` should look like:
```json
[
  {
    "host": "pr.oxylabs.io",
    "port": 7777,
    "username": "your-username",
    "password": "your-password",
    "protocol": "http",
    "country": "IT",
    "type": "residential"
  },
  {
    "host": "pr.oxylabs.io",
    "port": 7777,
    "username": "your-username-2",
    "password": "your-password-2",
    "protocol": "http",
    "country": "US",
    "type": "residential"
  }
]
```

#### Step 2: Import to Database

```bash
docker-compose exec backend python manage.py shell
```

```python
import json
from monitors.models import Proxy

# Load proxy list
with open('/app/Proxy lists (2).json', 'r') as f:
    proxies = json.load(f)

# Import all proxies
for proxy_data in proxies:
    Proxy.objects.create(
        host=proxy_data['host'],
        port=proxy_data['port'],
        username=proxy_data.get('username'),
        password=proxy_data.get('password'),
        protocol=proxy_data.get('protocol', 'http'),
        is_active=True,
        proxy_type=proxy_data.get('type', 'residential'),
        country=proxy_data.get('country', 'IT')
    )

print(f"✅ Imported {Proxy.objects.count()} proxies")
exit()
```

---

## 🧪 Testing Oxylabs Proxies

### Test 1: Direct Proxy Test

```bash
# Test Oxylabs residential proxy
curl -x http://your-username:your-password@pr.oxylabs.io:7777 https://ip.oxylabs.io/location

# Expected output:
{
  "ip": "xxx.xxx.xxx.xxx",
  "country": "IT",
  "city": "Rome",
  "provider": "Residential"
}
```

### Test 2: Vatican API via Proxy

```bash
# Test Vatican Search API via proxy
curl -x http://your-username:your-password@pr.oxylabs.io:7777 \
  "https://tickets.museivaticani.va/api/search/resultPerTag?lang=it&visitorNum=1&visitDate=28/03/2026&area=1&who=&page=0&tag=MV-Biglietti"

# Should return Vatican ticket data
```

### Test 3: Worker Proxy Test

```bash
# Check worker logs for proxy usage
docker-compose logs -f worker_vatican | grep -i proxy

# Expected:
# [INFO] Using proxy: http://pr.oxylabs.io:7777
# [INFO] Proxy IP: xxx.xxx.xxx.xxx (IT)
# [INFO] Vatican API response: 200 OK
```

### Test 4: Extension Proxy Test

1. Open incognito window
2. Visit https://ip.oxylabs.io/location
3. Should show Oxylabs IP (not your real IP)
4. Visit https://tickets.museivaticani.va
5. Should load via proxy

---

## 🔄 Proxy Rotation Strategies

### Strategy 1: Per-Request Rotation (Default)

**Best for**: Vatican monitoring (appears as different users)

```python
# In worker_vatican/search_api_monitor.py
# Proxy rotates automatically on each request
response = requests.get(url, proxies=get_random_proxy())
```

### Strategy 2: Sticky Session

**Best for**: Booking flow (maintain same IP throughout)

```python
# Use same proxy for entire booking session
session = requests.Session()
session.proxies = get_random_proxy()

# All requests use same proxy
response1 = session.get(url1)
response2 = session.get(url2)
response3 = session.get(url3)
```

### Strategy 3: Country-Specific

**Best for**: Target specific countries

```python
# Use only Italian proxies for Vatican
italian_proxies = Proxy.objects.filter(country='IT', is_active=True)
proxy = random.choice(italian_proxies)
```

### Strategy 4: Fallback Chain

**Best for**: High reliability

```python
# Try proxies in order until one works
proxies = Proxy.objects.filter(is_active=True).order_by('?')

for proxy in proxies:
    try:
        response = requests.get(url, proxies=proxy.to_dict(), timeout=10)
        if response.status_code == 200:
            return response
    except:
        continue

# If all proxies fail, try without proxy
return requests.get(url)
```

---

## 🎯 Oxylabs Best Practices

### 1. Use Residential Proxies for Vatican

```python
# Residential proxies look like real users
proxy = Proxy.objects.filter(
    proxy_type='residential',
    country='IT',
    is_active=True
).first()
```

### 2. Rotate Proxies Frequently

```python
# Rotate every 5-10 requests
if request_count % 10 == 0:
    proxy = get_random_proxy()
```

### 3. Handle Proxy Failures

```python
try:
    response = requests.get(url, proxies=proxy, timeout=30)
except requests.exceptions.ProxyError:
    # Mark proxy as failed
    proxy.is_active = False
    proxy.save()
    # Try next proxy
    proxy = get_random_proxy()
```

### 4. Monitor Proxy Performance

```python
# Track proxy success rate
proxy.total_requests += 1
if response.status_code == 200:
    proxy.successful_requests += 1
proxy.success_rate = proxy.successful_requests / proxy.total_requests
proxy.save()
```

### 5. Use Geo-Targeting

```python
# Target Italian IPs for Vatican
proxies = {
    'http': 'http://username:password@pr.oxylabs.io:7777',
    'https': 'http://username:password@pr.oxylabs.io:7777'
}

# Add country parameter
headers = {
    'X-Oxylabs-Geo-Location': 'Italy'
}
```

---

## 🔐 Security Considerations

### 1. Store Credentials Securely

**Environment Variables** (Recommended):
```env
OXYLABS_USERNAME=your-username
OXYLABS_PASSWORD=your-password
```

**Django Settings**:
```python
OXYLABS_USERNAME = os.getenv('OXYLABS_USERNAME')
OXYLABS_PASSWORD = os.getenv('OXYLABS_PASSWORD')
```

### 2. Encrypt Proxy Passwords

```python
from django.conf import settings
from cryptography.fernet import Fernet

# Encrypt password before storing
cipher = Fernet(settings.SECRET_KEY[:32].encode())
encrypted_password = cipher.encrypt(password.encode())

# Decrypt when using
decrypted_password = cipher.decrypt(encrypted_password).decode()
```

### 3. Limit Proxy Access

```python
# Only allow specific IPs to use proxies
ALLOWED_PROXY_IPS = ['your-server-ip']

if request.META['REMOTE_ADDR'] not in ALLOWED_PROXY_IPS:
    raise PermissionDenied
```

---

## 📊 Monitoring Proxy Usage

### Dashboard Metrics

```python
# Get proxy statistics
from monitors.models import Proxy

proxies = Proxy.objects.filter(is_active=True)

for proxy in proxies:
    print(f"Proxy: {proxy.host}:{proxy.port}")
    print(f"  Total Requests: {proxy.total_requests}")
    print(f"  Successful: {proxy.successful_requests}")
    print(f"  Success Rate: {proxy.success_rate:.2%}")
    print(f"  Last Used: {proxy.last_used}")
```

### Logs

```bash
# Monitor proxy usage in real-time
docker-compose logs -f worker_vatican | grep -i proxy

# Count proxy requests
docker-compose logs worker_vatican | grep "Using proxy" | wc -l

# Check proxy errors
docker-compose logs worker_vatican | grep "Proxy error"
```

---

## 🆘 Troubleshooting

### Issue: Proxy Connection Failed

**Error**: `ProxyError: Cannot connect to proxy`

**Solution**:
1. Check Oxylabs credentials
2. Verify account is active
3. Test proxy manually:
   ```bash
   curl -x http://username:password@pr.oxylabs.io:7777 https://ip.oxylabs.io/location
   ```

### Issue: Proxy Authentication Failed

**Error**: `407 Proxy Authentication Required`

**Solution**:
1. Verify username and password
2. Check for special characters (URL encode if needed)
3. Test credentials:
   ```bash
   curl -x http://username:password@pr.oxylabs.io:7777 https://httpbin.org/ip
   ```

### Issue: Slow Proxy Response

**Error**: Requests timing out

**Solution**:
1. Increase timeout: `timeout=60`
2. Use datacenter proxies for speed
3. Check Oxylabs dashboard for issues

### Issue: Vatican Blocking Proxy

**Error**: Vatican returns 403 or captcha

**Solution**:
1. Switch to residential proxies
2. Rotate proxies more frequently
3. Add delays between requests
4. Use Italian geo-location

---

## 📚 Oxylabs Resources

- **Dashboard**: https://dashboard.oxylabs.io/
- **Documentation**: https://developers.oxylabs.io/
- **Support**: support@oxylabs.io
- **Status Page**: https://status.oxylabs.io/

---

## ✅ Quick Setup Checklist

- [ ] Oxylabs account active
- [ ] Credentials obtained
- [ ] Proxies added to database
- [ ] `USE_PROXIES=True` in .env
- [ ] Worker restarted
- [ ] Proxy test successful
- [ ] Vatican API test via proxy successful
- [ ] Extension proxy configured (optional)
- [ ] Monitoring proxy usage

---

**Ready to use Oxylabs proxies! Your Vatican monitoring will now use residential IPs to avoid rate limiting.** 🚀
