"""
Verify the frontend data matches reality
Test the dates that show different statuses
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from zoneinfo import ZoneInfo

async def quick_check(date_str, visitors):
    """Quick check of a specific date"""
    print(f"\n{'='*70}")
    print(f"Checking: {date_str} ({visitors} visitors)")
    print(f"{'='*70}")
    
    # Parse date
    year, month, day = date_str.split('-')
    rome = ZoneInfo("Europe/Rome")
    dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
    timestamp_ms = int(dt.timestamp() * 1000)
    
    deep_url = f"https://tickets.museivaticani.va/home/fromtag/{visitors}/{timestamp_ms}/MV-Biglietti/1"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(deep_url, timeout=30000, wait_until='domcontentloaded')
            
            # Get cookies
            cookies = await page.context.cookies()
            jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
            
            if not jsessionid:
                print("❌ No JSESSIONID")
                await browser.close()
                return
            
            print(f"✅ Got JSESSIONID")
            
            # Try to extract IDs
            await page.wait_for_timeout(5000)
            
            tickets = await page.evaluate("""
                () => {
                    const results = [];
                    document.querySelectorAll('div[id^="ticket_"]').forEach(c => {
                        const id = c.id.replace('ticket_', '');
                        if (!id.startsWith('dx_') && id.length > 5) {
                            const title = c.querySelector('.muvaTicketTitle');
                            if (title) {
                                results.push({id: id, name: title.innerText.trim()});
                            }
                        }
                    });
                    return results;
                }
            """)
            
            if tickets:
                print(f"✅ Found {len(tickets)} tickets")
                ticket_id = tickets[0]['id']
                
                # Test API
                date_formatted = f"{day}/{month}/{year}"
                api_url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={date_formatted}"
                
                response = await page.request.get(api_url, headers={
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                })
                
                print(f"📡 API Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    if 'timetable' in data:
                        available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                        total = len(data['timetable'])
                        print(f"✅ AVAILABLE: {len(available)}/{total} slots")
                        if available:
                            print(f"   Sample: {', '.join([s['time'] for s in available[:5]])}")
                    else:
                        print(f"⚠️  No timetable")
                elif response.status == 500:
                    print(f"❌ NOT RELEASED (500 error)")
                else:
                    print(f"⚠️  Status {response.status}")
            else:
                print(f"❌ No tickets found on page")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await browser.close()

async def main():
    print("="*70)
    print("VERIFYING FRONTEND DATA")
    print("="*70)
    print("Checking dates that show different statuses in database\n")
    
    # Test dates from database
    tests = [
        ("2026-03-16", 1, "sold_out"),  # Task 21
        ("2026-03-26", 4, "available"),  # Task 22
        ("2026-04-22", 1, "sold_out"),  # Task 24
        ("2026-03-10", 1, "available"),  # Task 25
    ]
    
    for date, visitors, expected_status in tests:
        await quick_check(date, visitors)
        await asyncio.sleep(2)
    
    print(f"\n{'='*70}")
    print("VERIFICATION COMPLETE")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(main())
