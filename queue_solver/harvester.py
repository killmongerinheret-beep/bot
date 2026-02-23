import asyncio
import nodriver as uc
import redis
import json
import os
import signal
import sys

# CONFIG
# specific event URL or the general ticketing landing page
TARGET_URL = "https://ticketing.colosseo.it/en/event/parco-colosseo-24h/" 
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

async def force_kill_chrome():
    """Nuclear option to ensure no zombie processes eat RAM"""
    try:
        os.system("pkill -f chrome")
        os.system("pkill -f chromium")
    except:
        pass

async def solve_queue_and_harvest():
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    
    while True:
        browser = None
        try:
            print("🚀 Launching Stealth Browser (XVFB mode)...")
            
            # CRITICAL: nodriver arguments for stability in Docker
            browser = await uc.start(
                headless=False, # MUST BE FALSE for stealth
                browser_args=[
                    "--no-sandbox", 
                    "--disable-gpu", 
                    "--window-size=1920,1080",
                    "--start-maximized",
                    "--no-first-run",
                    "--no-default-browser-check"
                ]
            )

            page = await browser.get(TARGET_URL)
            print("🛡️ Hit the page. Analyzing...")

            # --- THE QUEUE LOOP ---
            # We stay in this loop as long as we are in the queue.
            # We do NOT close the browser, or we lose our spot.
            in_queue = True
            start_time = asyncio.get_event_loop().time()
            
            while in_queue:
                try: 
                    content = await page.get_content()
                    title = await page.title()
                except:
                     await asyncio.sleep(5)
                     continue
                
                # 1. Check if we passed (Success Criteria)
                # Look for the calendar, or "Available", or the specific Colosseum header
                if "calendar-wrapper" in content or "data-event-id" in content or "parco-colosseo-24h" in page.url:
                    if "queue-it" not in content.lower():
                        print("✅ QUEUE PASSED! We are inside.")
                        in_queue = False
                        break
                
                # 2. Check if we are still in Queue
                if "queue-it" in content.lower() or "queue-it" in title.lower():
                    elapsed = int(asyncio.get_event_loop().time() - start_time)
                    if elapsed % 60 == 0:
                        print(f"⏳ Still in Queue... Elapsed: {elapsed}s")
                    await asyncio.sleep(10) # Wait 10s before checking again
                    
                    # Safety: If stuck for > 4 hours, kill it.
                    if elapsed > 14400: 
                        raise Exception("Timed out in queue (4 hours)")
                    continue
                
                # 3. Handle "Soft Blocks" or errors
                if "access denied" in content.lower():
                    raise Exception("Detected Soft Block / 403")

                # If unsure, wait a bit (page might be loading)
                await asyncio.sleep(5)

            # --- EXTRACTION ---
            if not in_queue:
                print("🍪 Extracting Cookies...")
                cookies = await browser.cookies.get_all()
                
                # Filter for the important ones (Queue-it token + Incapsula)
                cookie_dict = {c.name: c.value for c in cookies}
                
                if not cookie_dict:
                    print("⚠️ Warning: No cookies found?")
                else:
                    # Save to Redis (TTL 10 mins)
                    r.set('colosseum_session', json.dumps(cookie_dict), ex=600)
                    print(f"💾 Saved {len(cookie_dict)} cookies to Redis.")

        except Exception as e:
            print(f"❌ Harvester Error: {e}")
        
        finally:
            print("🧹 Cleaning up browser...")
            try:
                if browser:
                    browser.stop()
            except:
                pass
            await force_kill_chrome() # Kill zombies
            
            # Wait 9 minutes before refreshing. 
            # The cookie lasts ~10 mins. We refresh just before it expires.
            print("💤 Sleeping 9 minutes...")
            await asyncio.sleep(540) 

if __name__ == "__main__":
    # Ensure we run in a loop handle
    try:
        asyncio.run(solve_queue_and_harvest())
    except KeyboardInterrupt:
        pass
