#!/usr/bin/env python3
"""Debug actual API response to see availability values"""

import asyncio
import json
import sys
sys.path.insert(0, '/app')

async def test_with_browser():
    """Use Playwright to get a real session and check API"""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to get session
        await page.goto("https://tickets.museivaticani.va/home", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Get cookies
        cookies = await context.cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}
        print(f"Cookies: {cookie_dict}")
        
        # Get ticket IDs first
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
        for i, t in enumerate(ids[:5]):
            print(f"  {i}: ID={t['id']}, Name={t['name']}")
        
        if ids:
            # Test API call with first ticket
            test_id = ids[0]['id']
            test_date = "28/02/2026"
            
            url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId={test_id}&visitorNum=3&visitDate={test_date}"
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
                print(f"\nTotal slots: {len(timetable)}")
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
                other_statuses = set(t.get('availability') for t in timetable if t.get('availability') != 'SOLD_OUT')
                print(f"Other availability values found: {other_statuses}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_with_browser())
