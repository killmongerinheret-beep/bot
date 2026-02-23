#!/usr/bin/env python3
"""Test that ticket names are extracted properly"""

import asyncio
import json
import sys
sys.path.insert(0, '/app')

async def test():
    from playwright.async_api import async_playwright
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(locale="it-IT", timezone_id="Europe/Rome")
        page = await context.new_page()
        
        # Navigate to specific date
        target_date = "28/02/2026"
        day, month, year = target_date.split('/')
        dt_obj = datetime(int(year), int(month), int(day))
        rome = ZoneInfo("Europe/Rome")
        midnight = dt_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=rome)
        ts = int(midnight.timestamp() * 1000)
        
        deep_url = f"https://tickets.museivaticani.va/home/fromtag/3/{ts}/MV-Biglietti/1"
        print(f"Navigating to: {deep_url}\n")
        
        await page.goto(deep_url, timeout=45000, wait_until="domcontentloaded")
        
        # Wait for Angular to render
        print("Waiting for Angular to render ticket titles...")
        try:
            await page.wait_for_selector('.muvaTicketTitle, [class*="ticket"]', timeout=5000)
            print("✅ Ticket elements found")
        except:
            print("⚠️ Timeout waiting for ticket elements")
        
        await page.wait_for_timeout(3000)
        
        # Extract with improved method
        print("\nExtracting ticket information...")
        ids = await page.evaluate("""
            () => {
                const results = [];
                const buttons = document.querySelectorAll("[data-cy^='bookTicket_']");
                buttons.forEach(btn => {
                    const id = btn.getAttribute("data-cy").split("_")[1];
                    let title = "Unknown";
                    
                    // Strategy 1: Look in parent containers
                    let container = btn.closest('div.card, div.row, .ticket-item, [class*="ticket"]');
                    if (!container) container = btn.parentElement?.parentElement?.parentElement;
                    
                    if (container) {
                        const selectors = [
                            '.muvaTicketTitle',
                            '[class*="TicketTitle"]',
                            '[class*="ticket-title"]',
                            '.ticket-name',
                            'h1', 'h2', 'h3', 'h4', 'h5',
                            '.title',
                            '.name',
                            '[class*="title"]'
                        ];
                        for (let sel of selectors) {
                            const el = container.querySelector(sel);
                            if (el && el.innerText && el.innerText.trim().length > 3) {
                                title = el.innerText.trim();
                                break;
                            }
                        }
                    }
                    
                    // Strategy 2: Look for adjacent text
                    if (title === "Unknown") {
                        const parent = btn.parentElement;
                        if (parent) {
                            let sibling = parent.previousElementSibling;
                            while (sibling && title === "Unknown") {
                                if (sibling.innerText && sibling.innerText.trim().length > 3) {
                                    title = sibling.innerText.trim().substring(0, 100);
                                    break;
                                }
                                sibling = sibling.previousElementSibling;
                            }
                        }
                    }
                    
                    results.push({id: id, name: title});
                });
                return results;
            }
        """)
        
        print(f"\n{'='*80}")
        print(f"EXTRACTED {len(ids)} TICKETS:")
        print(f"{'='*80}")
        for i, t in enumerate(ids, 1):
            status = "✅" if t['name'] != "Unknown" else "❌"
            print(f"{status} {i:2}. ID: {t['id']} - Name: {t['name'][:60]}")
        
        # Count how many have proper names
        named = sum(1 for t in ids if t['name'] != "Unknown")
        print(f"\n{'='*80}")
        print(f"RESULT: {named}/{len(ids)} tickets have proper names")
        
        if named < len(ids):
            print("\n⚠️ Some tickets still show 'Unknown'")
            print("   This might be because:")
            print("   1. The page uses different class names")
            print("   2. Angular hasn't fully rendered")
            print("   3. The DOM structure is different")
        else:
            print("\n✅ All tickets have proper names!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
