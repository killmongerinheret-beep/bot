"""
Direct API test - Get cookies quickly, then ping API with known IDs
No waiting for Angular to load!
"""
import asyncio
from playwright.async_api import async_playwright
import json

# Known IDs from our previous discovery
KNOWN_IDS = {
    "459172131": "Musei Vaticani - Biglietti d'ingresso",
    "1934042052": "Ingresso AREE MUSEALI Singoli",
    "2037374249": "Musei Vaticani - Visite Guidate Singoli",
    "1078934336": "Musei Vaticani - Visite Guidate Gruppi",
}

async def quick_cookie_grab():
    """Get JSESSIONID as fast as possible"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Just hit the deep link - don't wait for anything to load
        print("Getting cookies from March 16 deep link...")
        deep_url = "https://tickets.museivaticani.va/home/fromtag/1/1773615600000/MV-Biglietti/1"
        
        await page.goto(deep_url, wait_until='commit', timeout=10000)  # Just wait for navigation
        await page.wait_for_timeout(1000)  # Minimal wait
        
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        
        await browser.close()
        return jsessionid

async def test_api_directly(jsessionid, ticket_id, ticket_name, date="16/03/2026"):
    """Ping API directly with curl-like request"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Set the cookie
        await context.add_cookies([{
            'name': 'JSESSIONID',
            'value': jsessionid,
            'domain': '.museivaticani.va',
            'path': '/'
        }])
        
        page = await context.new_page()
        
        # Build API URL
        api_url = (
            f"https://tickets.museivaticani.va/api/visit/timeavail"
            f"?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum=1&visitDate={date}"
        )
        
        print(f"\nTesting: {ticket_name}")
        print(f"ID: {ticket_id}")
        print(f"URL: {api_url}")
        
        try:
            response = await page.request.get(api_url, headers={
                'Accept': 'application/json, text/plain, */*',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://tickets.museivaticani.va/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            status = response.status
            print(f"Status: {status}")
            
            if status == 200:
                data = await response.json()
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
                
                if 'timetable' in data:
                    available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                    print(f"\n✅ SUCCESS! Found {len(available)} available slots out of {len(data['timetable'])} total")
                    
                    if available:
                        print("Available times:")
                        for slot in available[:10]:
                            print(f"  - {slot['time']}")
                    else:
                        print("⚠️  All slots SOLD OUT")
                else:
                    print("⚠️  No timetable in response")
                    
            elif status == 500:
                text = await response.text()
                print(f"❌ 500 Error: {text[:200]}")
            else:
                text = await response.text()
                print(f"❌ Status {status}: {text[:200]}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        await browser.close()

async def main():
    print("="*60)
    print("FAST API TEST - March 16, 2026")
    print("="*60)
    
    # Step 1: Quick cookie grab (1-2 seconds)
    print("\nStep 1: Getting JSESSIONID...")
    jsessionid = await quick_cookie_grab()
    
    if not jsessionid:
        print("❌ Failed to get JSESSIONID!")
        return
    
    print(f"✅ Got JSESSIONID: {jsessionid[:30]}...")
    
    # Step 2: Test all known IDs (2-3 seconds each)
    print("\n" + "="*60)
    print("Step 2: Testing known IDs with API...")
    print("="*60)
    
    for ticket_id, ticket_name in KNOWN_IDS.items():
        await test_api_directly(jsessionid, ticket_id, ticket_name)
        print()

if __name__ == "__main__":
    asyncio.run(main())
