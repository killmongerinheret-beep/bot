#!/usr/bin/env python3
"""Debug what ticket types are being checked"""

import asyncio
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
        
        target_date = "28/02/2026"
        day, month, year = target_date.split('/')
        dt_obj = datetime(int(year), int(month), int(day))
        rome = ZoneInfo("Europe/Rome")
        midnight = dt_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=rome)
        ts = int(midnight.timestamp() * 1000)
        
        deep_url = f"https://tickets.museivaticani.va/home/fromtag/3/{ts}/MV-Biglietti/1"
        print(f"Navigating to: {deep_url}\n")
        
        await page.goto(deep_url, timeout=45000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Get ticket names
        tickets = await page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll("[data-cy^='bookTicket_']").forEach((btn, index) => {
                    const id = btn.getAttribute("data-cy").split("_")[1];
                    
                    // Try to find ticket name
                    let name = "Unknown";
                    let container = btn.closest('div.card, div.row, .ticket-item, [class*="ticket"]');
                    if (!container) container = btn.parentElement?.parentElement?.parentElement;
                    
                    if (container) {
                        // Try multiple selectors for title
                        const selectors = [
                            '.muvaTicketTitle',
                            '.ticket-title', 
                            'h1', 'h2', 'h3', 'h4',
                            '.title',
                            '.name',
                            '[class*="title"]',
                            '[class*="name"]'
                        ];
                        for (let sel of selectors) {
                            const el = container.querySelector(sel);
                            if (el && el.innerText.trim()) {
                                name = el.innerText.trim();
                                break;
                            }
                        }
                    }
                    
                    results.push({index: index + 1, id, name});
                });
                return results;
            }
        """)
        
        print("Tickets found on page:")
        print("-" * 80)
        for t in tickets:
            print(f"  {t['index']:2}. ID: {t['id']} - {t['name'][:60]}")
        
        print(f"\n{'='*80}")
        print("ISSUE ANALYSIS:")
        print(f"{'='*80}")
        print("""
The bot checks ALL these ticket types for availability.

If ANY of them has slots, the bot reports "Found X slots".

But you might be looking for ONLY "Musei Vaticani - Biglietti d'ingresso"
(Standard Entry Ticket), which could be sold out while other tickets
(like Guided Tours, Audio Guides, etc.) still have availability.

SOLUTION:
The bot should ONLY check the specific ticket type requested,
not all tickets on the page.
""")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
