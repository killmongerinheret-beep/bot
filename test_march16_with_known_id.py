"""
Test March 16 using known working ID from March 20
This proves whether March 16 has tickets or not
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test_with_known_id():
    """Use March 20's working ID to check March 16"""
    
    # Known working ID from March 20
    STANDARD_TICKET_ID = "459172131"  # Musei Vaticani - Biglietti d'ingresso
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Step 1: Get cookies from March 16 deep link
        print("Step 1: Getting cookies for March 16...")
        deep_url = "https://tickets.museivaticani.va/home/fromtag/1/1773615600000/MV-Biglietti/1"
        await page.goto(deep_url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)
        
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        print(f"JSESSIONID: {jsessionid[:20]}..." if jsessionid else "No JSESSIONID!")
        
        # Step 2: Call API with known ID
        print(f"\nStep 2: Calling API with known ID {STANDARD_TICKET_ID}...")
        api_url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId={STANDARD_TICKET_ID}&visitorNum=1&visitDate=16/03/2026"
        
        response = await page.request.get(api_url, headers={
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://tickets.museivaticani.va/'
        })
        
        status = response.status
        print(f"API Status: {status}")
        
        if status == 200:
            data = await response.json()
            print(f"\nResponse: {json.dumps(data, indent=2)}")
            
            if 'timetable' in data:
                available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                print(f"\n✅ Found {len(available)} available slots!")
                for slot in available[:5]:
                    print(f"   {slot['time']}")
            else:
                print("❌ No timetable in response")
        else:
            text = await response.text()
            print(f"Error response: {text[:200]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_with_known_id())
