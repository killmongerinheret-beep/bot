#!/usr/bin/env python3
"""
Debug script to see what's actually on the Vatican page
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def debug_page():
    """Debug what elements are on the page"""
    bot = HydraBot(use_proxies=True)
    
    print("=" * 60)
    print("VATICAN PAGE DEBUG")
    print("=" * 60)
    
    test_date = "16/03/2026"
    visitors = 1
    ticket_type = 0
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        try:
            # Calculate timestamp
            ts = bot.get_vatican_timestamp(test_date)
            slug = "MV-Biglietti"
            deep_url = f"https://tickets.museivaticani.va/home/fromtag/{visitors}/{ts}/{slug}/1"
            
            print(f"Navigating to: {deep_url}")
            await page.goto(deep_url, timeout=60000, wait_until="networkidle")
            await page.wait_for_timeout(5000)
            
            print("\n" + "=" * 60)
            print("CHECKING PAGE ELEMENTS")
            print("=" * 60)
            
            # Check for muvaTicketTitle
            titles_count = await page.locator('.muvaTicketTitle').count()
            print(f"\n✅ .muvaTicketTitle elements: {titles_count}")
            
            if titles_count > 0:
                titles = await page.locator('.muvaTicketTitle').all_text_contents()
                for i, title in enumerate(titles, 1):
                    print(f"   {i}. {title}")
            
            # Check for bookTicket buttons
            buttons_count = await page.locator('[data-cy^="bookTicket_"]').count()
            print(f"\n{'✅' if buttons_count > 0 else '❌'} [data-cy^='bookTicket_'] buttons: {buttons_count}")
            
            if buttons_count > 0:
                # Get button IDs
                button_ids = await page.evaluate('''() => {
                    const buttons = document.querySelectorAll('[data-cy^="bookTicket_"]');
                    return Array.from(buttons).map(btn => btn.getAttribute('data-cy'));
                }''')
                for i, btn_id in enumerate(button_ids, 1):
                    print(f"   {i}. {btn_id}")
            
            # Check for any buttons at all
            all_buttons = await page.locator('button').count()
            print(f"\n📊 Total <button> elements: {all_buttons}")
            
            # Check page HTML structure
            print("\n" + "=" * 60)
            print("PAGE STRUCTURE ANALYSIS")
            print("=" * 60)
            
            structure = await page.evaluate('''() => {
                const info = {
                    hasAngular: !!window.ng,
                    hasTicketCards: document.querySelectorAll('app-ticket-card').length,
                    hasCards: document.querySelectorAll('.card').length,
                    hasMuvaElements: document.querySelectorAll('[class*="muva"]').length,
                    bodyClasses: document.body.className,
                    mainContent: document.querySelector('main, #main, .main-content') ? 'Found' : 'Not found'
                };
                return info;
            }''')
            
            print(f"Angular detected: {structure['hasAngular']}")
            print(f"app-ticket-card elements: {structure['hasTicketCards']}")
            print(f".card elements: {structure['hasCards']}")
            print(f"[class*='muva'] elements: {structure['hasMuvaElements']}")
            print(f"Main content: {structure['mainContent']}")
            
            # Save screenshot
            await page.screenshot(path="vatican_debug_detailed.png", full_page=True)
            print("\n📸 Full page screenshot saved: vatican_debug_detailed.png")
            
            # Save HTML
            html = await page.content()
            with open("vatican_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("📄 HTML saved: vatican_debug.html")
            
            # Try to find buttons with different selectors
            print("\n" + "=" * 60)
            print("ALTERNATIVE BUTTON SELECTORS")
            print("=" * 60)
            
            alt_selectors = [
                'button[data-cy]',
                'button[class*="book"]',
                'button[class*="prenota"]',
                'a[data-cy]',
                '[data-cy]',
                'button:has-text("PRENOTA")',
                'button:has-text("BOOK")'
            ]
            
            for selector in alt_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        print(f"✅ '{selector}': {count} elements")
                except:
                    print(f"❌ '{selector}': Error")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await page.close()

if __name__ == "__main__":
    asyncio.run(debug_page())
