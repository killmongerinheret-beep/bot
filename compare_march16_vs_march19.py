"""
Compare March 16 vs March 19 using same IDs
This will prove whether March 16 is released or not
"""
import asyncio
from playwright.async_api import async_playwright
import json

KNOWN_IDS = {
    "459172131": "Musei Vaticani - Biglietti d'ingresso",
    "1934042052": "Ingresso AREE MUSEALI Singoli",
}

async def test_date(date_str, timestamp_ms, test_name):
    """Test a specific date with known IDs"""
    
    print("\n" + "="*60)
    print(f"TESTING: {test_name} ({date_str})")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Get cookies
        deep_url = f"https://tickets.museivaticani.va/home/fromtag/1/{timestamp_ms}/MV-Biglietti/1"
        print(f"Getting cookies from: {deep_url}")
        
        await page.goto(deep_url, wait_until='commit', timeout=10000)
        await page.wait_for_timeout(1000)
        
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        print(f"JSESSIONID: {jsessionid[:30]}..." if jsessionid else "No cookie!")
        
        if not jsessionid:
            await browser.close()
            return
        
        # Test each known ID
        for ticket_id, ticket_name in KNOWN_IDS.items():
            api_url = (
                f"https://tickets.museivaticani.va/api/visit/timeavail"
                f"?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum=1&visitDate={date_str}"
            )
            
            print(f"\n  Testing ID {ticket_id} ({ticket_name})...")
            
            try:
                response = await page.request.get(api_url, headers={
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': 'https://tickets.museivaticani.va/'
                })
                
                status = response.status
                
                if status == 200:
                    data = await response.json()
                    if 'timetable' in data:
                        available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                        total = len(data['timetable'])
                        print(f"    ✅ 200 OK - {len(available)}/{total} slots available")
                        if available:
                            print(f"       Sample times: {', '.join([s['time'] for s in available[:3]])}")
                    else:
                        print(f"    ⚠️  200 OK but no timetable")
                elif status == 500:
                    print(f"    ❌ 500 Error - Date not released or ID invalid")
                else:
                    print(f"    ❌ Status {status}")
                    
            except Exception as e:
                print(f"    ❌ Exception: {e}")
        
        await browser.close()

async def main():
    print("="*60)
    print("COMPARISON TEST: March 16 vs March 19")
    print("="*60)
    print("Using same IDs to test both dates")
    print("This will prove if March 16 tickets are released")
    
    # Test March 16 (suspected not released)
    await test_date("16/03/2026", 1773615600000, "March 16 (Sunday)")
    
    # Test March 19 (known to have tickets)
    await test_date("19/03/2026", 1773874800000, "March 19 (Wednesday)")
    
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    print("If March 16 returns 500 but March 19 returns 200:")
    print("  → March 16 tickets NOT RELEASED by Vatican yet")
    print("\nIf both return 200:")
    print("  → March 16 tickets ARE AVAILABLE")

if __name__ == "__main__":
    asyncio.run(main())
