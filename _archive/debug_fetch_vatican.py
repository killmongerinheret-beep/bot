import asyncio
import logging
import sys
import os
from playwright.async_api import async_playwright

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("DebugVatican")

async def debug_page():
    logger.info("🚀 Starting Debug Session...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="it-IT",
            timezone_id="Europe/Rome"
        )
        page = await context.new_page()
        
        # Target: Feb 13, 2026 Guided Tour
        # Timestamp for 13/02/2026 Midnight Rome
        # 13 Feb 2026 00:00:00 CET = 1769727600000 (Approx, checking logic)
        
        # Let's use the EXACT url from the logs
        url = "https://tickets.museivaticani.va/home/fromtag/1/1769727600000/MV-Visite-Guidate/1"
        logger.info(f"🕸️ Navigating to: {url}")
        
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000) # Wait for Vue/React to hydrate
            
            # 1. Take Screenshot
            os.makedirs("/app/debug_output", exist_ok=True)
            shot_path = "/app/debug_output/vatican_feb13_debug.png"
            await page.screenshot(path=shot_path, full_page=True)
            logger.info(f"📸 Screenshot saved to {shot_path}")
            
            # 2. Dump HTML
            html_path = "/app/debug_output/vatican_feb13_source.html"
            content = await page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"📄 HTML saved to {html_path}")
            
            # 3. List All Buttons
            logger.info("🔍 Scanning for Buttons...")
            buttons_data = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('button')).map(b => ({
                    text: b.textContent.trim(),
                    id: b.id,
                    class: b.className,
                    data_cy: b.getAttribute('data-cy'),
                    visible: !!(b.offsetWidth || b.offsetHeight || b.getClientRects().length)
                }));
            }""")
            
            found_book = False
            for b in buttons_data:
                logger.info(f"🔘 Button: Text='{b['text']}' | data-cy='{b['data_cy']}' | Visible={b['visible']}")
                if b['data_cy'] and b['data_cy'].startswith("bookTicket_"):
                    found_book = True
            
            if not found_book:
                logger.warning("⚠️ CRITICAL: No button with data-cy='bookTicket_' found!")
            else:
                logger.info("✅ SUCCESS: Found 'bookTicket' buttons.")
                
        except Exception as e:
            logger.error(f"❌ Error during debug: {e}")
            await page.screenshot(path="/app/debug_output/error_state.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page())
