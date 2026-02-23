import asyncio
import logging
import sys
import os
from playwright.async_api import async_playwright

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("DeepDiag")

async def diagnose():
    logger.info("🚀 Starting Deep Diagnostic Session...")
    
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
        
        # Target: Feb 13, 2026 Guided Tour (Correct Timestamp: 1770937200000)
        url = "https://tickets.museivaticani.va/home/fromtag/1/1770937200000/MV-Visite-Guidate/1"
        logger.info(f"🕸️ Navigating to: {url}")
        
        try:
            response = await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000) # Wait for hydration
            
            # 1. Check URL & Title
            final_url = page.url
            title = await page.title()
            logger.info(f"📍 Final URL: {final_url}")
            logger.info(f"🏷️ Page Title: {title}")
            
            if final_url != url:
                logger.warning(f"⚠️ REDIRECT DETECTED! Original: {url} -> Final: {final_url}")
            
            # 2. Check Specific Elements (User Provided)
            logger.info("🔍 Checking for User's Button...")
            
            # Check by ID (data-cy)
            count_id = await page.locator("[data-cy^='bookTicket_']").count()
            logger.info(f"🔢 Buttons with data-cy='bookTicket_...': {count_id}")
            
            # Check by Text (PRENOTA)
            count_text = await page.get_by_text("PRENOTA", exact=False).count()
            logger.info(f"🔤 Elements with text 'PRENOTA': {count_text}")
            
            # Check for specific class
            count_class = await page.locator(".btn.btn-lg.btn-primary").count()
            logger.info(f"🎨 Elements with class 'btn btn-lg btn-primary': {count_class}")

            # 3. Full Page Screenshot
            os.makedirs("/app/debug_output", exist_ok=True)
            shot_path = "/app/debug_output/vatican_full_diagnostic.png"
            await page.screenshot(path=shot_path, full_page=True)
            logger.info(f"📸 Full Page Screenshot saved to {shot_path}")
            
            # 4. Dump HTML
            html_path = "/app/debug_output/vatican_full_source.html"
            content = await page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"📄 HTML saved to {html_path}")
            
        except Exception as e:
            logger.error(f"❌ Error during diagnostic: {e}")
            await page.screenshot(path="/app/debug_output/error_diagnostic.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
