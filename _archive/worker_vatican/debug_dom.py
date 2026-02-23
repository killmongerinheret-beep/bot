
import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker_vatican.hydra_monitor import HydraBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugDOM")

async def dump_dom():
    bot = HydraBot(use_proxies=False) # Use direct connection for debugging if possible, or True if IP blocked
    
    # Target date: 2026-02-24 (from user screenshot)
    target_date = "24/02/2026"
    
    logger.info(f"🕸️ Navigating to Vatican Tickets for {target_date}...")
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        # 1. Resolve Dynamic IDs (Standard Tickets)
        # This navigates to the list page
        # We'll hijack the logic to dump HTML
        
        ticket_type = 0 # Standard
        tag_id = 1
        slug = "MV-Biglietti"
        ts = bot.get_vatican_timestamp(target_date)
        deep_url = f"https://tickets.museivaticani.va/home/fromtag/{tag_id}/{ts}/{slug}/1"
        
        logger.info(f"Navigate to: {deep_url}")
        await page.goto(deep_url, timeout=60000, wait_until="load")
        await page.wait_for_timeout(5000) # Wait for render
        
        # 2. Dump HTML of all ticket containers
        js_dump = """
        () => {
            const results = [];
            const buttons = document.querySelectorAll("[data-cy^='bookTicket_']");
            
            buttons.forEach(btn => {
                const id = btn.getAttribute("data-cy").split("_")[1];
                let html = "";
                
                // Climb up to find the main container (e.g. the card)
                let currentEl = btn;
                for (let i = 0; i < 5; i++) {
                    currentEl = currentEl.parentElement;
                    if (!currentEl) break;
                    
                    // Identify if this is the card container?
                    // Typically it has some class like 'card', 'ticket-item', etc.
                    // Or we just grab the 4th parent which is usually the card
                    if (currentEl.tagName === 'APP-TICKET-ITEM' || currentEl.classList.contains('card') || i===3) {
                         html = currentEl.outerHTML;
                         break;
                    }
                }
                
                // If we didn't find specific container, just grab 4th parent
                if (!html && btn.parentElement && btn.parentElement.parentElement && btn.parentElement.parentElement.parentElement) {
                    html = btn.parentElement.parentElement.parentElement.outerHTML;
                }
                
                results.push({id, html});
            });
            return results;
        }
        """
        
        items = await page.evaluate(js_dump)
        
        logger.info(f"✅ Found {len(items)} items. Saving to debug_dom.html...")
        
        with open("debug_dom.html", "w", encoding="utf-8") as f:
            f.write("<html><body>")
            for item in items:
                f.write(f"<hr><h2>ID: {item['id']}</h2>")
                f.write(item['html'])
            f.write("</body></html>")
            
        logger.info("✅ XML Dumped. Exiting.")

if __name__ == "__main__":
    asyncio.run(dump_dom())
