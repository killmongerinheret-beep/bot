"""
Vatican Cookie Harvester using Nodriver

This worker runs a headless Chrome browser to harvest trusted session cookies
from the Vatican ticketing site. The cookies are stored in Redis for use by
the main VaticanPro bot.

Updated to follow the EXACT user navigation path from browser recording.
"""

import asyncio
import json
import logging
import time
import os

try:
    import nodriver as uc
except ImportError:
    print("ERROR: nodriver not installed. Run: pip install nodriver")
    exit(1)

import redis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Redis Configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_KEY = 'vatican_cookies'
COOKIE_TTL = 3600  # 1 hour


class VaticanHarvester:
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.browser = None
    
    def store_cookies(self, cookies, user_agent=None):
        """Store cookies and UA in Redis with TTL."""
        try:
            data = {
                "cookies": cookies,
                "user_agent": user_agent
            }
            self.redis_client.setex(
                REDIS_KEY,
                COOKIE_TTL,
                json.dumps(data)
            )
            logger.info(f"📦 Data stored in Redis (TTL: {COOKIE_TTL}s)")
            logger.info(f"   ticketmv = {cookies.get('ticketmv', 'MISSING')}")
            if user_agent:
                logger.info(f"   UA = {user_agent[:50]}...")
        except Exception as e:
            logger.error(f"Redis store failed: {e}")


async def main():
    harvester = VaticanHarvester()
    
    logger.info("🚀 Starting Harvester with EXACT User Navigation Path...")
    try:
        # Step 1: Launch Chrome with Docker-friendly flags
        # FORCE a Windows-style Chrome 124 User-Agent to match curl_cffi's 'chrome124' impersonation
        standard_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        logger.info(f"📍 Step 1: Launching Browser with UA: {standard_ua[:50]}...")
        harvester.browser = await uc.start(
            headless=True,
            browser_args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage",
                f"--user-agent={standard_ua}"
            ]
        )
        
        # Step 2: Navigate to Tag Page directly (as per new recording)
        logger.info("📍 Step 2: Navigating to Tag Page (VG-Musei)...")
        # URL from recording: https://tickets.museivaticani.va/home/fromtag/2/1769382000000/VG-Musei/1
        page = await harvester.browser.get("https://tickets.museivaticani.va/home/fromtag/2/1769382000000/VG-Musei/1")
        await asyncio.sleep(8) # Longer wait for Angular to hydrate
        
        # Step 3: Find and click ANY 'bookTicket' button (Dynamic ID)
        logger.info("📍 Step 3: Finding available ticket button...")
        ticket_btn = None
        # Target ID from recording or bot config
        target_ticket_id = "536495491" 
        
        for attempt in range(3):
            try:
                # 1. Try to find the specific target ticket first
                ticket_btn = await page.select(f"[data-cy='bookTicket_{target_ticket_id}']")
                if ticket_btn:
                    logger.info(f"   Success found TARGET ticket button {target_ticket_id}")
                    break
                
                # 2. Fallback to any bookTicket button
                ticket_btn = await page.select("[data-cy^='bookTicket_']")
                if ticket_btn:
                    logger.info(f"   Using ANY available ticket button...")
                    break
            except Exception as e:
                logger.warning(f"   Attempt {attempt+1} failed: {e}")
            await asyncio.sleep(3)

        if ticket_btn:
             # Log the actual ID we are clicking
             try:
                 # In nodriver, attributes are often available directly or via evaluate
                 btn_id = await page.evaluate(f"(el) => el.getAttribute('data-cy')", ticket_btn)
                 logger.info(f"   Clicking ticket: {btn_id}")
             except:
                 logger.info("   Clicking ticket (could not resolve ID)")
                 
             await ticket_btn.click()
             await asyncio.sleep(5)
        else:
            logger.error("❌ No ticket button found on tag page after retries!")
            return

        # Step 4: Click language dropdown and select French
        logger.info("📍 Step 4: Selecting French language...")
        try:
            lang_dropdown = await page.select("[data-cy='visitLang']")
            if lang_dropdown:
                await lang_dropdown.click()
                await asyncio.sleep(3)
                
                # Click "Francese" option - wait for dropdown to animate
                francese_opt = await page.find("Francese", best_match=True)
                if francese_opt:
                    await francese_opt.click()
                    await asyncio.sleep(3)
                else:
                    logger.warning("   'Francese' option not found textually")
            else:
                 logger.warning("   Language dropdown not found")
        except Exception as e:
            logger.warning(f"   Language selection failed: {e}")
        
        # Step 5: Harvest cookies
        logger.info("📍 Step 9: Harvesting cookies and User-Agent...")
        
        # Get User-Agent
        user_agent = await page.evaluate("navigator.userAgent")
        
        cookies = await harvester.browser.cookies.get_all()
        cookie_dict = {}
        for cookie in cookies:
            domain = getattr(cookie, 'domain', '')
            if 'museivaticani.va' in domain:
                name = getattr(cookie, 'name', '')
                value = getattr(cookie, 'value', '')
                if name and value:
                    cookie_dict[name] = value
        
        if cookie_dict:
            logger.info(f"✅ HARVEST SUCCESS! Cookies: {list(cookie_dict.keys())}")
            logger.info(f"   ticketmv = {cookie_dict.get('ticketmv', 'MISSING')}")
            harvester.store_cookies(cookie_dict, user_agent=user_agent)
        else:
            logger.warning("❌ No cookies found for domain!")
            
    except Exception as e:
        logger.error(f"💥 HARVEST CRASHED: {e}", exc_info=True)
    finally:
        if harvester.browser:
            logger.info("📍 Stopping browser...")
            try:
                harvester.browser.stop()
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())
