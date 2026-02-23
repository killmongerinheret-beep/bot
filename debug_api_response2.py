#!/usr/bin/env python3
"""Debug actual API response with date navigation"""

import asyncio
import json
import sys
sys.path.insert(0, '/app')

async def test_with_specific_date():
    """Navigate to specific date and check API"""
    from playwright.async_api import async_playwright
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(
            locale="it-IT",
            timezone_id="Europe/Rome"
        )
        page = await context.new_page()
        
        # Navigate to specific date deep link (like the bot does)
        target_date = "28/02/2026"
        day, month, year = target_date.split('/')
        dt_obj = datetime(int(year), int(month), int(day))
        rome = ZoneInfo("Europe/Rome")
        midnight = dt_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=rome)
        ts = int(midnight.timestamp() * 1000)
        
        # Standard ticket deep link
        deep_url = f"https://tickets.museivaticani.va/home/fromtag/3/{ts}/MV-Biglietti/1"
        print(f"Navigating to: {deep_url}")
        
        await page.goto(deep_url, timeout=45000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Get page title to see state
        title = await page.title()
        print(f"Page title: {title}")
        
        # Get ticket IDs
        ids = await page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll("[data-cy^='bookTicket_']").forEach(btn => {
                    const id = btn.getAttribute("data-cy").split("_")[1];
                    const container = btn.closest('div.card, div.row') || btn.parentElement?.parentElement;
                    let name = "Unknown";
                    if (container) {
                        const titleEl = container.querySelector('.muvaTicketTitle, h1, h2, h3, h4');
                        if (titleEl) name = titleEl.innerText.trim();
                    }
                    results.push({id, name});
                });
                return results;
            }
        """)
        print(f"\nFound {len(ids)} tickets:")
        for i, t in enumerate(ids[:10]):
            print(f"  {i}: ID={t['id']}, Name={t['name']}")
        
        if ids:
            # Test API call with first ticket
            test_id = ids[0]['id']
            
            url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId={test_id}&visitorNum=3&visitDate={target_date}"
            print(f"\n{'='*60}")
            print(f"Testing API: {url}")
            
            api_js = f"""
            async () => {{
                const response = await fetch("{url}");
                if (response.ok) {{
                    return await response.json();
                }}
                return {{error: response.status, text: await response.text()}};
            }}
            """
            
            result = await page.evaluate(api_js)
            
            if "error" in result:
                print(f"API Error: {result}")
            else:
                timetable = result.get("timetable", [])
                print(f"\nTotal slots in timetable: {len(timetable)}")
                
                if timetable:
                    print(f"\nFirst 10 slots with availability:")
                    for t in timetable[:10]:
                        avail = t.get('availability', 'UNKNOWN')
                        time = t.get('time', 'N/A')
                        print(f"  {time}: {avail}")
                    
                    # Count by availability
                    counts = {}
                    for t in timetable:
                        avail = t.get('availability', 'UNKNOWN')
                        counts[avail] = counts.get(avail, 0) + 1
                    print(f"\nAvailability breakdown:")
                    for k, v in sorted(counts.items()):
                        print(f"  {k}: {v}")
                    
                    # Show what we filter
                    not_sold_out = [t for t in timetable if t.get('availability') != 'SOLD_OUT']
                    print(f"\nSlots NOT marked 'SOLD_OUT': {len(not_sold_out)}")
                    
                    # Check if there are other values we should filter
                    other_statuses = set(t.get('availability') for t in timetable)
                    print(f"\nAll availability values found: {other_statuses}")
                    
                    # Check for potential issues
                    if 'AVAILABLE' in other_statuses or 'OPEN' in other_statuses:
                        available_count = len([t for t in timetable if t.get('availability') in ['AVAILABLE', 'OPEN']])
                        print(f"\n✅ Slots actually marked AVAILABLE/OPEN: {available_count}")
                    else:
                        print(f"\n⚠️ No slots marked as AVAILABLE or OPEN")
                        print(f"⚠️ This suggests all slots might be unavailable but using different status codes")
                else:
                    print("⚠️ No timetable data returned - tickets may be SOLD OUT")
        else:
            # Check page content for sold out message
            content = await page.content()
            if "sold out" in content.lower() or "esaurito" in content.lower() or "non disponibile" in content.lower():
                print("\n⚠️ Page shows SOLD OUT message")
            else:
                print("\n⚠️ No tickets found on page")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_with_specific_date())
