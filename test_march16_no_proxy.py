#!/usr/bin/env python3
"""
Test March 16 WITHOUT proxies to see if that's the issue
"""

import asyncio
from playwright.async_api import async_playwright

async def test_march16_direct():
    print("\n" + "="*60)
    print("TESTING MARCH 16 - NO PROXIES")
    print("="*60)
    
    async with async_playwright() as p:
        # Launch browser WITHOUT proxy
        browser = await p.chromium.launch(headless=False)  # Visible browser
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to March 16 deep link
            url = "https://tickets.museivaticani.va/home/fromtag/1/1773615600000/MV-Biglietti/1"
            print(f"\n📍 Navigating to: {url}")
            
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Wait for tickets to load
            await page.wait_for_selector("[data-cy^='bookTicket_']", timeout=15000)
            await page.wait_for_selector(".muvaTicketTitle", timeout=5000)
            
            # Extract ticket names
            tickets = await page.evaluate("""
                () => {
                    const results = [];
                    const titles = document.querySelectorAll('.muvaTicketTitle');
                    titles.forEach(title => {
                        results.push(title.innerText.trim());
                    });
                    return results;
                }
            """)
            
            print(f"\n🎫 Found {len(tickets)} tickets:")
            for i, name in enumerate(tickets, 1):
                marker = "✅" if "Musei Vaticani" in name and "Biglietti" in name else "📍"
                print(f"   {i}. {marker} {name}")
            
            # Check for main ticket
            has_main = any("Musei Vaticani" in t and "Biglietti d'ingresso" in t for t in tickets)
            
            print(f"\n" + "="*60)
            if has_main:
                print("✅ FOUND: Musei Vaticani - Biglietti d'ingresso")
            else:
                print("❌ NOT FOUND: Musei Vaticani - Biglietti d'ingresso")
            print("="*60)
            
            # Keep browser open for manual inspection
            print("\n⏸️  Browser will stay open for 30 seconds for manual inspection...")
            await page.wait_for_timeout(30000)
            
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_march16_direct())
