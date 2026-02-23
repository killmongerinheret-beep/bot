#!/usr/bin/env python3
"""Debug scenario where all tickets are sold out"""

import asyncio
import json
import sys
sys.path.insert(0, '/app')

async def test_all_tickets():
    """Check all tickets for a date to see if any are truly available"""
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
        
        # Navigate to specific date deep link
        target_date = "28/02/2026"
        day, month, year = target_date.split('/')
        dt_obj = datetime(int(year), int(month), int(day))
        rome = ZoneInfo("Europe/Rome")
        midnight = dt_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=rome)
        ts = int(midnight.timestamp() * 1000)
        
        deep_url = f"https://tickets.museivaticani.va/home/fromtag/3/{ts}/MV-Biglietti/1"
        print(f"Navigating to: {deep_url}")
        
        await page.goto(deep_url, timeout=45000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Get all ticket IDs
        ids = await page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll("[data-cy^='bookTicket_']").forEach(btn => {
                    const id = btn.getAttribute("data-cy").split("_")[1];
                    results.push(id);
                });
                return results;
            }
        """)
        print(f"\nFound {len(ids)} tickets to check")
        
        total_available = 0
        total_sold_out = 0
        ticket_results = []
        
        for ticket_id in ids[:5]:  # Check first 5 tickets
            url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId={ticket_id}&visitorNum=3&visitDate={target_date}"
            
            api_js = f"""
            async () => {{
                const response = await fetch("{url}");
                if (response.ok) {{
                    return await response.json();
                }}
                return {{error: response.status}};
            }}
            """
            
            result = await page.evaluate(api_js)
            
            if "error" not in result:
                timetable = result.get("timetable", [])
                available = [t for t in timetable if t.get('availability') != 'SOLD_OUT']
                sold_out = [t for t in timetable if t.get('availability') == 'SOLD_OUT']
                
                total_available += len(available)
                total_sold_out += len(sold_out)
                
                status = "AVAILABLE" if available else "SOLD_OUT"
                ticket_results.append({
                    'id': ticket_id,
                    'total': len(timetable),
                    'available': len(available),
                    'sold_out': len(sold_out),
                    'status': status
                })
                
                print(f"Ticket {ticket_id}: {len(available)} available, {len(sold_out)} sold out")
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"  Total tickets checked: {len(ticket_results)}")
        print(f"  Total available slots across all tickets: {total_available}")
        print(f"  Total sold out slots across all tickets: {total_sold_out}")
        print(f"\n  Tickets with availability: {sum(1 for t in ticket_results if t['available'] > 0)}")
        print(f"  Tickets completely sold out: {sum(1 for t in ticket_results if t['available'] == 0)}")
        
        # This is what the bot reports
        if total_available > 0:
            print(f"\n⚠️ BOT WOULD REPORT: Found {total_available} slots")
            print(f"   (Even if some specific tickets are sold out)")
        else:
            print(f"\n✅ ALL SOLD OUT: No slots available")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_all_tickets())
