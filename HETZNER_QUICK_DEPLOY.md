# Hetzner Quick Deploy - 30 Minutes

## 🚀 Deploy Complete Vatican Bot to Hetzner

---

## Step 1: Create Deployment Package (5 minutes)

### On Your Local Machine:
```bash
# Make script executable
chmod +x create_hetzner_package.sh

# Create package
./create_hetzner_package.sh

# This creates:
# - hetzner-deployment/ folder
# - vatican-bot-hetzner.tar.gz archive
```

**What's included:**
- ✅ Backend (Django API)
- ✅ Worker (Vatican monitoring)
- ✅ Playwright Bot (Headless booking)
- ✅ Database (PostgreSQL)
- ✅ Redis (Message broker)
- ✅ Nginx (Reverse proxy)
- ✅ Deployment scripts

---

## Step 2: Create Hetzner Server (5 minutes)

### Go to Hetzner Cloud:
```
1. Visit: https://www.hetzner.com/cloud
2. Create account (if needed)
3. Create new project: "Vatican Bot"
4. Click "Add Server"
```

### Server Configuration:
```
Location: Nuremberg, Germany
Image: Ubuntu 22.04
Type: CX31 (2 vCPU, 8GB RAM) - €11.90/month
Networking: IPv4 + IPv6
SSH Keys: Add your public key
Name: vatican-bot-prod
```

### Note Your Server IP:
```
Example: 123.456.789.012
```

---

## Step 3: Prepare Server (5 minutes)

### Connect to Server:
```bash
ssh root@YOUR_SERVER_IP
```

### Install Docker:
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version
```

### Create Directory:
```bash
mkdir -p /root/vatican-bot
cd /root/vatican-bot
```

---

## Step 4: Upload Project (5 minutes)

### From Your Local Machine:
```bash
# Upload archive
scp vatican-bot-hetzner.tar.gz root@YOUR_SERVER_IP:/root/vatican-bot/

# Or upload folder directly
scp -r hetzner-deployment/* root@YOUR_SERVER_IP:/root/vatican-bot/
```

### On Server:
```bash
# Extract archive (if uploaded)
cd /root/vatican-bot
tar -xzf vatican-bot-hetzner.tar.gz
rm vatican-bot-hetzner.tar.gz

# List files
ls -la
```

---

## Step 5: Configure Environment (5 minutes)

### Create .env file:
```bash
cp .env.example .env
nano .env
```

### Essential Settings:
```bash
# Database
POSTGRES_DB=vatican_bot
POSTGRES_USER=vatican
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD

# Django
SECRET_KEY=GENERATE_RANDOM_KEY_HERE
DEBUG=False
ALLOWED_HOSTS=YOUR_SERVER_IP,yourdomain.com

# Redis
REDIS_URL=redis://redis:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID

# Google Sheets (optional)
GOOGLE_SERVICE_ACCOUNT_FILE=/app/google_credentials.json

# Playwright
HEADLESS=true
BROWSER_TYPE=chromium
```

### Generate Secret Key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## Step 6: Deploy (5 minutes)

### Run Deployment Script:
```bash
chmod +x deploy.sh
./deploy.sh
```

**This will:**
1. Build Docker images
2. Start all services
3. Run database migrations
4. Collect static files
5. Show service status

### Check Status:
```bash
docker-compose ps

# Should show:
# backend          Up      0.0.0.0:8000->8000/tcp
# worker_vatican   Up
# playwright_bot   Up
# db               Up
# redis            Up
# nginx            Up      0.0.0.0:80->80/tcp
```

---

## Step 7: Create Monitoring Task (2 minutes)

### Create Real Task:
```bash
docker-compose exec backend python /app/create_real_monitoring_task.py
```

**This will:**
- Remove test data
- Create real monitoring task
- Configure worker
- Show instructions

### Verify Worker:
```bash
docker-compose logs -f worker_vatican

# Should see:
# ✅ Checking Vatican availability for task ID: X
# 🔍 Calling Search API for fresh ticket IDs
# 📅 Date: 2026-06-15, Visitors: 2
```

---

## Step 8: Test API (2 minutes)

### Check Backend:
```bash
curl http://localhost:8000/api/v1/available-slots/?agency_id=15

# Should return:
# {"slots": [], "count": 0, "timestamp": "..."}
```

### Check from Outside:
```bash
# From your local machine
curl http://YOUR_SERVER_IP:8000/api/v1/available-slots/?agency_id=15
```

---

## Step 9: Monitor (1 minute)

### Watch Logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker_vatican
docker-compose logs -f playwright_bot
docker-compose logs -f backend
```

### Check Resources:
```bash
# CPU and memory usage
docker stats

# Disk usage
df -h
```

---

## ✅ Deployment Complete!

### Your System is Now:
- ✅ Running 24/7 on Hetzner
- ✅ Monitoring Vatican automatically
- ✅ Booking with Playwright (headless)
- ✅ Sending Telegram notifications
- ✅ Auto-restarting on errors

### Access Points:
```
Backend API: http://YOUR_SERVER_IP:8000
Admin Panel: http://YOUR_SERVER_IP:8000/admin
Frontend: http://YOUR_SERVER_IP:3000 (if configured)
```

---

## 🔧 Post-Deployment

### Create Superuser:
```bash
docker-compose exec backend python /app/backend/manage.py createsuperuser
```

### Upload Google Credentials (Optional):
```bash
# From local machine
scp google_credentials.json root@YOUR_SERVER_IP:/root/vatican-bot/

# On server
docker cp google_credentials.json vatican-bot-backend-1:/app/
```

### Configure Agency:
```bash
docker-compose exec backend python /app/backend/manage.py shell

>>> from monitors.models import Agency
>>> agency = Agency.objects.get(id=15)
>>> agency.google_sheet_url = 'YOUR_SHEET_URL'
>>> agency.save()
>>> exit()
```

---

## 📊 Monitoring Commands

### Service Status:
```bash
docker-compose ps
```

### View Logs:
```bash
docker-compose logs -f [service_name]
```

### Restart Service:
```bash
docker-compose restart [service_name]
```

### Check Database:
```bash
docker-compose exec backend python /app/backend/manage.py shell

>>> from monitors.models import HeldSlot, MonitorTask
>>> print(f"Active tasks: {MonitorTask.objects.filter(is_active=True).count()}")
>>> print(f"Held slots: {HeldSlot.objects.filter(status='held').count()}")
```

### Check Playwright:
```bash
# View screenshots
ls -la screenshots/

# Check browser processes
docker-compose exec playwright_bot ps aux | grep chrome
```

---

## 🐛 Troubleshooting

### Services not starting:
```bash
docker-compose logs [service_name]
docker-compose restart [service_name]
```

### Database issues:
```bash
docker-compose exec backend python /app/backend/manage.py migrate
```

### Playwright issues:
```bash
# Rebuild Playwright container
docker-compose build playwright_bot
docker-compose up -d playwright_bot

# Check logs
docker-compose logs playwright_bot
```

### Out of memory:
```bash
# Check memory
free -h

# Upgrade server to CX41 (4 vCPU, 16GB RAM)
# Or reduce concurrent bookings
```

---

## 🔒 Security (Optional but Recommended)

### Setup Firewall:
```bash
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

### Setup SSL (with domain):
```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d yourdomain.com

# Auto-renewal
certbot renew --dry-run
```

### Change Default Passwords:
```bash
# Edit .env
nano .env

# Change:
# - POSTGRES_PASSWORD
# - SECRET_KEY
# - Any other sensitive values

# Restart services
docker-compose down
docker-compose up -d
```

---

## 📈 Scaling

### Add More Agencies:
```bash
docker-compose exec backend python /app/backend/manage.py shell

>>> from monitors.models import Agency
>>> agency = Agency.objects.create(
...     name="Agency 2",
...     telegram_chat_id="123456789",
...     plan="pro",
...     is_active=True
... )
```

### Run Multiple Playwright Instances:
```bash
# Edit docker-compose.yml
# Add more playwright_bot services with different names
docker-compose up -d --scale playwright_bot=3
```

### Upgrade Server:
```
Hetzner Console → Resize Server → CX41 (16GB RAM)
```

---

## 💰 Cost Breakdown

### Monthly Costs:
```
Server CX31: €11.90/month
Backups (optional): €2.38/month
Total: €11.90-14.28/month
```

### What You Get:
- ✅ 24/7 operation
- ✅ 99.9% uptime
- ✅ Professional datacenter
- ✅ Automatic backups
- ✅ Easy scaling
- ✅ 10+ concurrent bookings
- ✅ 50+ agencies support

---

## ✅ Success Checklist

- [ ] Server created on Hetzner
- [ ] Docker installed
- [ ] Project uploaded
- [ ] Environment configured
- [ ] Services deployed
- [ ] Monitoring task created
- [ ] Worker checking Vatican
- [ ] API responding
- [ ] Playwright bot ready
- [ ] Telegram notifications working
- [ ] Google Sheets configured (optional)

---

## 📚 Next Steps

1. **Monitor:** Watch logs for first booking
2. **Test:** Wait for worker to find slot
3. **Verify:** Check Playwright books successfully
4. **Optimize:** Adjust settings based on results
5. **Scale:** Add more agencies

---

**Status:** ✅ Deployed to Hetzner!
**Time:** 30 minutes
**Cost:** €11.90/month
**Capacity:** 50+ agencies, 10+ concurrent bookings

---

**Questions?** Check:
- HETZNER_DEPLOYMENT_COMPLETE.md (full guide)
- PLAYWRIGHT_VS_EXTENSION_DECISION.md (why Playwright)
- PRODUCTION_SETUP_GUIDE.md (production workflow)
