# Complete Hetzner Server Deployment Guide

## 🎯 Architecture Decision: Playwright vs Extension

### ❌ Browser Extension on Server (Won't Work)
**Problems:**
- Extensions need GUI (can't run headless properly)
- Chrome extensions require X server on Linux
- Angular/React apps need rendering (can't be truly headless)
- Hard to manage multiple instances
- Difficult to monitor/debug remotely

### ✅ Playwright on Server (Recommended)
**Benefits:**
- ✅ True headless mode (no GUI needed)
- ✅ Works with Angular/React/Vue (renders JavaScript)
- ✅ Multiple browsers (Chrome, Firefox, WebKit)
- ✅ Easy to scale (run multiple instances)
- ✅ Better error handling
- ✅ Screenshots for debugging
- ✅ Can run 24/7 without issues

---

## 🏗️ New Architecture for Hetzner

### Current (Local):
```
Backend → Worker → Finds Slots → Extension (Local Computer) → Books
```

### New (Hetzner):
```
Backend → Worker → Finds Slots → Playwright Bot (Same Server) → Books
                                        ↓
                                  Telegram Notification
                                        ↓
                                  Google Sheets Update
```

**Everything runs on one server!**

---

## Part 1: Create Playwright Booking Bot

### File Structure:
```
hetzner-deployment/
├── docker-compose.yml
├── .env
├── backend/
├── worker_vatican/
├── playwright_bot/          # NEW
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── bot.py
│   ├── vatican_booker.py
│   └── config.py
└── nginx/
```

### Playwright Bot Code:

```python
# playwright_bot/vatican_booker.py

import asyncio
from playwright.async_api import async_playwright, Page, Browser
import logging
from datetime import datetime
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

class VaticanBooker:
    """
    Headless Vatican booking bot using Playwright
    Runs on server without GUI
    """
    
    def __init__(self, headless: bool = True, browser_type: str = 'chromium'):
        """
        Args:
            headless: Run without GUI (True for server)
            browser_type: 'chromium', 'firefox', or 'webkit'
        """
        self.headless = headless
        self.browser_type = browser_type
        self.playwright = None
        self.browser = None
    
    async def start(self):
        """Start Playwright and browser"""
        self.playwright = await async_playwright().start()
        
        # Choose browser
        if self.browser_type == 'firefox':
            browser_launcher = self.playwright.firefox
        elif self.browser_type == 'webkit':
            browser_launcher = self.playwright.webkit
        else:
            browser_launcher = self.playwright.chromium
        
        # Launch browser
        self.browser = await browser_launcher.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        logger.info(f"✅ Started {self.browser_type} browser (headless={self.headless})")
    
    async def stop(self):
        """Stop browser and Playwright"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def book_slot(self, slot_data: Dict) -> Dict:
        """
        Book a Vatican slot
        
        Args:
            slot_data: {
                'date': '15/06/2026',
                'time': '09:00',
                'visitors': 2,
                'ticket_id': '2129030053',
                'profile': {...},
                'participants': [...]
            }
        
        Returns:
            {
                'success': True/False,
                'payment_url': 'https://...',
                'error': 'error message',
                'screenshot': 'path/to/screenshot.png'
            }
        """
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Build Vatican URL
            url = self._build_vatican_url(slot_data)
            logger.info(f"📍 Navigating to: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Step 1: Select ticket
            await self._select_ticket(page, slot_data)
            
            # Step 2: Set quantity
            await self._set_quantity(page, slot_data['visitors'])
            
            # Step 3: Select time
            await self._select_time(page, slot_data['time'])
            
            # Step 4: Click PROCEDI
            await self._click_procedi(page)
            
            # Step 5: Fill checkout form
            await self._fill_checkout_form(page, slot_data)
            
            # Step 6: Handle Turnstile
            await self._handle_turnstile(page)
            
            # Step 7: Click ACQUISTA
            await self._click_acquista(page)
            
            # Step 8: Wait for payment redirect
            payment_url = await self._wait_for_payment(page)
            
            # Take screenshot
            screenshot_path = f"/tmp/booking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            
            logger.info(f"✅ Booking successful! Payment URL: {payment_url}")
            
            return {
                'success': True,
                'payment_url': payment_url,
                'screenshot': screenshot_path
            }
            
        except Exception as e:
            logger.error(f"❌ Booking failed: {e}")
            
            # Take error screenshot
            screenshot_path = f"/tmp/error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            try:
                await page.screenshot(path=screenshot_path, full_page=True)
            except:
                pass
            
            return {
                'success': False,
                'error': str(e),
                'screenshot': screenshot_path
            }
            
        finally:
            await context.close()
    
    def _build_vatican_url(self, slot_data: Dict) -> str:
        """Build Vatican deep link"""
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
        # Parse date
        date_obj = datetime.strptime(slot_data['date'], '%d/%m/%Y')
        rome_tz = ZoneInfo('Europe/Rome')
        date_with_tz = date_obj.replace(hour=0, minute=0, second=0, tzinfo=rome_tz)
        timestamp = int(date_with_tz.timestamp() * 1000)
        
        visitors = slot_data['visitors']
        ticket_type = slot_data.get('ticket_type', 0)
        slug = 'MV-Visite-Guidate' if ticket_type == 1 else 'MV-Biglietti'
        
        return f"https://tickets.museivaticani.va/home/fromtag/{visitors}/{timestamp}/{slug}/1"
    
    async def _select_ticket(self, page: Page, slot_data: Dict):
        """Select ticket type"""
        logger.info("🎫 Selecting ticket...")
        
        # Wait for tickets to load
        await page.wait_for_selector('[data-cy="ticket-card"]', timeout=15000)
        
        # Click first available ticket (or match by name)
        ticket_name = slot_data.get('ticket_name', '')
        if ticket_name:
            # Try to find by name
            tickets = await page.query_selector_all('[data-cy="ticket-card"]')
            for ticket in tickets:
                text = await ticket.inner_text()
                if ticket_name.lower() in text.lower():
                    await ticket.click()
                    logger.info(f"✅ Selected ticket: {ticket_name}")
                    return
        
        # Fallback: click first ticket
        await page.click('[data-cy="ticket-card"]')
        logger.info("✅ Selected first available ticket")
    
    async def _set_quantity(self, page: Page, visitors: int):
        """Set number of visitors"""
        logger.info(f"👥 Setting quantity: {visitors}")
        
        # Wait for quantity selector
        await page.wait_for_selector('[data-cy="quantity"]', timeout=10000)
        
        # Set quantity
        await page.fill('[data-cy="quantity"]', str(visitors))
        
        logger.info(f"✅ Set quantity to {visitors}")
    
    async def _select_time(self, page: Page, time: str):
        """Select time slot"""
        logger.info(f"⏰ Selecting time: {time}")
        
        # Wait for time dropdown
        await page.wait_for_selector('[data-cy="time"]', timeout=15000)
        
        # Click dropdown
        await page.click('[data-cy="time"]')
        await asyncio.sleep(1)
        
        # Select time
        time_options = await page.query_selector_all('[data-cy="time-option"]')
        for option in time_options:
            text = await option.inner_text()
            if time in text:
                await option.click()
                logger.info(f"✅ Selected time: {time}")
                return
        
        # If exact time not found, click first available
        if time_options:
            await time_options[0].click()
            logger.warning(f"⚠️ Exact time {time} not found, selected first available")
    
    async def _click_procedi(self, page: Page):
        """Click PROCEDI button"""
        logger.info("➡️ Clicking PROCEDI...")
        
        await page.wait_for_selector('[data-cy="bookVisit"]', timeout=10000)
        await page.click('[data-cy="bookVisit"]')
        
        # Wait for navigation
        await page.wait_for_load_state('networkidle', timeout=30000)
        
        logger.info("✅ Clicked PROCEDI")
    
    async def _fill_checkout_form(self, page: Page, slot_data: Dict):
        """Fill checkout form"""
        logger.info("📝 Filling checkout form...")
        
        profile = slot_data['profile']
        participants = slot_data.get('participants', [])
        
        # Wait for form
        await page.wait_for_selector('[data-cy="managerSurname"]', timeout=30000)
        
        # Fill representative fields
        await page.fill('[data-cy="managerSurname"]', profile['last_name'])
        await page.fill('[data-cy="managerName"]', profile['first_name'])
        await page.fill('[data-cy="managerEmail"]', profile['email'])
        await page.fill('[data-cy="managerConfirmEmail"]', profile['email'])
        
        # Fill phone (remove + sign)
        phone = profile['phone'].replace('+', '').replace(' ', '')
        await page.fill('[data-cy="managerPhone"]', phone)
        
        await page.fill('[data-cy="managerCity"]', profile['city'])
        
        # Select country
        await page.click('[data-cy="managerCountry"]')
        await asyncio.sleep(0.5)
        await page.fill('#searchInput_country', 'Ital')
        await asyncio.sleep(0.5)
        await page.click('[data-cy="managerCountrySection"]')
        
        # Fill participants
        for i, participant in enumerate(participants):
            await page.fill(f'#participantSurname_{i}', participant['last_name'])
            await page.fill(f'#participantName_{i}', participant['first_name'])
        
        # Click checkboxes
        await page.click('#mat-mdc-checkbox-1-input')  # Terms
        await asyncio.sleep(1.5)
        
        # Close modal if appears
        try:
            await page.click('[data-cy="purchase-rules-close-btn"]', timeout=2000)
            await asyncio.sleep(1)
        except:
            pass
        
        await page.click('#mat-mdc-checkbox-4-input')  # Privacy
        
        logger.info("✅ Form filled")
    
    async def _handle_turnstile(self, page: Page):
        """Wait for Turnstile to be solved"""
        logger.info("🔐 Waiting for Turnstile...")
        
        try:
            # Wait for Turnstile iframe
            await page.wait_for_selector('iframe[src*="turnstile"]', timeout=5000)
            
            # Wait for Turnstile to be solved (checkmark appears)
            await page.wait_for_selector('.cf-turnstile-success', timeout=60000)
            
            logger.info("✅ Turnstile solved")
        except:
            logger.info("ℹ️ No Turnstile found or already solved")
    
    async def _click_acquista(self, page: Page):
        """Click ACQUISTA button"""
        logger.info("💳 Clicking ACQUISTA...")
        
        await page.wait_for_selector('[data-cy="buyButton"]', timeout=10000)
        
        # Wait for button to be enabled
        await page.wait_for_function(
            "document.querySelector('[data-cy=\"buyButton\"]').disabled === false",
            timeout=10000
        )
        
        await page.click('[data-cy="buyButton"]')
        
        logger.info("✅ Clicked ACQUISTA")
    
    async def _wait_for_payment(self, page: Page, timeout: int = 60000) -> Optional[str]:
        """Wait for redirect to payment page"""
        logger.info("⏳ Waiting for payment redirect...")
        
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) * 1000 < timeout:
            url = page.url
            
            if 'epay' in url or 'payment' in url:
                logger.info(f"✅ Redirected to payment: {url}")
                return url
            
            if 'error' in url or 'errore' in url:
                logger.error("❌ Error page detected")
                return None
            
            await asyncio.sleep(0.5)
        
        logger.error("❌ Timeout waiting for payment redirect")
        return None


# Example usage
async def main():
    booker = VaticanBooker(headless=True, browser_type='chromium')
    
    try:
        await booker.start()
        
        slot_data = {
            'date': '15/06/2026',
            'time': '09:00',
            'visitors': 2,
            'ticket_id': '2129030053',
            'ticket_name': 'Vatican Museums - Standard Entry',
            'profile': {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'phone': '393331234567',
                'city': 'Rome'
            },
            'participants': [
                {'first_name': 'John', 'last_name': 'Doe'},
                {'first_name': 'Jane', 'last_name': 'Doe'}
            ]
        }
        
        result = await booker.book_slot(slot_data)
        print(result)
        
    finally:
        await booker.stop()

if __name__ == '__main__':
    asyncio.run(main())
```

---

## Part 2: Docker Setup for Playwright

### Dockerfile:
```dockerfile
# playwright_bot/Dockerfile

FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium firefox webkit
RUN playwright install-deps

# Copy bot code
COPY . .

# Run bot
CMD ["python", "bot.py"]
```

### Requirements:
```txt
# playwright_bot/requirements.txt

playwright==1.40.0
asyncio
python-dotenv
requests
celery
redis
psycopg2-binary
```

### Docker Compose Update:
```yaml
# Add to docker-compose.yml

services:
  # ... existing services ...
  
  playwright_bot:
    build: ./playwright_bot
    container_name: vatican-playwright-bot
    restart: unless-stopped
    environment:
      - BACKEND_URL=http://backend:8000
      - REDIS_URL=redis://redis:6379/0
      - HEADLESS=true
      - BROWSER_TYPE=chromium
    volumes:
      - ./playwright_bot:/app
      - ./screenshots:/tmp
    depends_on:
      - backend
      - redis
    networks:
      - vatican-network
```

---

## Part 3: Integration with Worker

### Worker triggers Playwright bot:
```python
# worker_vatican/tasks.py

from celery import shared_task
import requests
import logging

logger = logging.getLogger(__name__)

@shared_task
def book_slot_with_playwright(slot_id):
    """
    Trigger Playwright bot to book a slot
    """
    from monitors.models import HeldSlot
    
    try:
        slot = HeldSlot.objects.get(id=slot_id)
        
        # Prepare slot data
        slot_data = {
            'date': slot.date,
            'time': slot.slot_time,
            'visitors': slot.visitors,
            'ticket_id': slot.ticket_id,
            'ticket_name': slot.ticket_name,
            'profile': {
                'first_name': slot.task.agency.buyer_profile.first_name,
                'last_name': slot.task.agency.buyer_profile.last_name,
                'email': slot.task.agency.buyer_profile.email,
                'phone': slot.task.agency.buyer_profile.phone,
                'city': slot.task.agency.buyer_profile.city
            },
            'participants': []  # Load from participants_json
        }
        
        # Call Playwright bot API
        response = requests.post(
            'http://playwright_bot:5000/book',
            json=slot_data,
            timeout=300  # 5 minutes
        )
        
        result = response.json()
        
        if result['success']:
            # Update slot with payment URL
            slot.payment_url = result['payment_url']
            slot.status = 'payment_ready'
            slot.save()
            
            # Send Telegram notification
            send_telegram_notification(slot, result['payment_url'])
            
            # Update Google Sheets
            update_google_sheets(slot, result['payment_url'])
            
            logger.info(f"✅ Slot {slot_id} booked successfully")
        else:
            logger.error(f"❌ Booking failed: {result['error']}")
            slot.status = 'failed'
            slot.save()
        
    except Exception as e:
        logger.error(f"Error booking slot {slot_id}: {e}")
```

---

## Part 4: Multiple Browsers Support

### Run different browsers in parallel:
```yaml
# docker-compose.yml

services:
  playwright_bot_chrome:
    build: ./playwright_bot
    environment:
      - BROWSER_TYPE=chromium
    # ... other config ...
  
  playwright_bot_firefox:
    build: ./playwright_bot
    environment:
      - BROWSER_TYPE=firefox
    # ... other config ...
  
  playwright_bot_webkit:
    build: ./playwright_bot
    environment:
      - BROWSER_TYPE=webkit
    # ... other config ...
```

**Benefits:**
- ✅ Distribute load across browsers
- ✅ Fallback if one browser fails
- ✅ Test compatibility
- ✅ Avoid detection

---

## Part 5: Hetzner Deployment Package

### Create deployment folder:
```bash
mkdir hetzner-deployment
cd hetzner-deployment

# Copy essential files
cp -r backend/ .
cp -r worker_vatican/ .
cp -r playwright_bot/ .
cp docker-compose.yml .
cp .env.example .env
cp -r nginx/ .

# Create deployment script
cat > deploy.sh << 'EOF'
#!/bin/bash
# Hetzner Deployment Script

echo "🚀 Deploying Vatican Bot to Hetzner..."

# Build and start services
docker-compose build
docker-compose up -d

# Wait for services
sleep 10

# Run migrations
docker-compose exec backend python /app/backend/manage.py migrate

# Create superuser (optional)
# docker-compose exec backend python /app/backend/manage.py createsuperuser

# Check status
docker-compose ps

echo "✅ Deployment complete!"
echo "Backend: http://YOUR_SERVER_IP:8000"
echo "Frontend: http://YOUR_SERVER_IP:3000"
EOF

chmod +x deploy.sh
```

---

## Part 6: Complete Deployment Steps

### 1. Create Hetzner Server
```
1. Go to: https://www.hetzner.com/cloud
2. Create server:
   - Type: CX31 (2 vCPU, 8GB RAM) - €11.90/month
   - Location: Nuremberg
   - Image: Ubuntu 22.04
3. Note IP address
```

### 2. Prepare Server
```bash
# Connect
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Create directory
mkdir -p /root/vatican-bot
```

### 3. Copy Project
```bash
# From local machine
cd hetzner-deployment
tar -czf vatican-bot.tar.gz .
scp vatican-bot.tar.gz root@YOUR_SERVER_IP:/root/vatican-bot/

# On server
ssh root@YOUR_SERVER_IP
cd /root/vatican-bot
tar -xzf vatican-bot.tar.gz
rm vatican-bot.tar.gz
```

### 4. Configure Environment
```bash
# Edit .env
nano .env

# Set:
# - Database credentials
# - Redis URL
# - Telegram bot token
# - Google credentials
# - Backend URL
```

### 5. Deploy
```bash
# Run deployment script
./deploy.sh

# Or manually:
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 6. Monitor
```bash
# Check all services
docker-compose ps

# Watch Playwright bot
docker-compose logs -f playwright_bot

# Watch worker
docker-compose logs -f worker_vatican

# Check backend
curl http://localhost:8000/api/v1/available-slots/?agency_id=15
```

---

## Part 7: Error Handling & Monitoring

### Auto-restart on failure:
```yaml
# docker-compose.yml

services:
  playwright_bot:
    restart: unless-stopped  # Auto-restart on crash
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:5000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Screenshot on error:
```python
# Playwright bot saves screenshots to /tmp
# Mount volume to persist:
volumes:
  - ./screenshots:/tmp
```

### Telegram alerts:
```python
# Send alert on error
def send_error_alert(error_msg, screenshot_path):
    bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"❌ Booking Error: {error_msg}"
    )
    bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=open(screenshot_path, 'rb')
    )
```

---

## Summary

### ✅ Playwright vs Extension:
- **Extension:** Needs GUI, can't run headless on server
- **Playwright:** True headless, perfect for servers

### ✅ Multiple Browsers:
- Chromium (fastest)
- Firefox (good compatibility)
- WebKit (Safari engine)

### ✅ Angular Support:
- Playwright renders JavaScript fully
- Works with Angular/React/Vue
- No issues with headless mode

### ✅ Deployment:
- Everything in one folder
- One command deployment
- Auto-restart on errors
- Screenshots for debugging

**Next:** See HETZNER_PLAYWRIGHT_SETUP.md for detailed Playwright implementation!
