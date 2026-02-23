import asyncio
import os
import logging
import sys

# Ensure imports work
sys.path.append('/app')
sys.path.append('/app/worker_vatican')
try:
    from worker_vatican.hydra_monitor import HydraBot
except ImportError:
    from hydra_monitor import HydraBot

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugScan")

async def run_debug_scan(date="27/02/2026"):
    print(f"\n🕵️ DEBUG SCAN FOR DATE: {date}")
    print("="*60)
    
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        # Test Tags 1, 2, 3 to see which one works
        # User says: 1 is broken, 3 is correct.
        for tag_id in [3]:
             print(f"\n==========================================")
             print(f"--- CHECKING TAG ID: {tag_id} ---")
             print(f"==========================================")
             
             try:
                 # Construct URL
                 ts = bot.get_vatican_timestamp(date)
                 # Try Standard Slug first
                 slug = "MV-Biglietti"
                 deep_url = f"https://tickets.museivaticani.va/home/fromtag/{tag_id}/{ts}/{slug}/1"
                 print(f"🕸️ Navigating: {deep_url}")
                 
                 await page.goto(deep_url, timeout=30000, wait_until="domcontentloaded")
                 await page.wait_for_timeout(3000)
                 
                 # Extract
                 ids_js = """
                 () => {
                    const results = [];
                    const buttons = document.querySelectorAll("[data-cy^='bookTicket_']");
                    const titles = document.querySelectorAll(".muvaTicketTitle");
                    
                    buttons.forEach((btn, index) => {
                        let name = "Unknown Ticket";
                        
                        // STRATEGY 1: Index Matching (Robust for lists)
                        if (titles[index]) {
                            name = titles[index].innerText.trim();
                        }
                        
                        results.push({
                            id: btn.getAttribute("data-cy").split("_")[1],
                            name: name
                        });
                    });
                    return results;
                 }
                 """
                 try:
                     items = await page.evaluate(ids_js)
                 except:
                     items = []
                     
                 if not items:
                     print(f"❌ Tag {tag_id}: No tickets found.")
                 else:
                     print(f"✅ Tag {tag_id}: Found {len(items)} tickets!")
                     for i, item in enumerate(items):
                         print(f"   > {item['name']} (ID: {item['id']})")
                         
                         # Force check first 5 tickets regardless of name
                         if i < 5:
                             print(f"     Checking Availability for {item['id']}...")
                             
                             # API CHECK
                             slots = await bot.check_via_api(page, item['id'], date, visitors=2, language="", visit_lang="")
                             
                             if slots:
                                 print(f"     🎉 SLOTS FOUND! {slots}")
                                 import sys; sys.exit(0)
                             else:
                                 print(f"     ❌ Sold Out (0 slots)")
                             
             except Exception as e:
                 print(f"⚠️ Tag {tag_id} Error: {e}")

        print("\n❌ COMPLETE SCAN FINISHED. NO SLOTS FOUND FOR ANY TAG.")

if __name__ == "__main__":
    asyncio.run(run_debug_scan())
