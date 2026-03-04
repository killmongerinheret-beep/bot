"""
Test March 16 with the FRESH IDs we just extracted from March 19
"""
import asyncio
from playwright.async_api import async_playwright
import json

# FRESH IDs from March 19 (just extracted)
FRESH_IDS = {
    "161755641": "Ingresso AREE MUSEALI Singoli",
    "1555548798": "Ingresso AREE MUSEALI - Gruppi",
    "714105834": "Ingresso Terrazze Panoramiche 360°",
}

async def test_march16_with_fresh_ids():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Get cookies for March 16
        print("Getting cookies for March 16...")
        await page.goto("https://tickets.museivaticani.va/home/fromtag/1/1773615600000/MV-Biglietti/1",
                       wait_until='commit', timeout=10000)
        await page.wait_for_timeout(1000)
        
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        print(f"✅ JSESSIONID: {jsessionid[:30]}...")
        
        print("\n" + "="*60)
        print("Testing March 16 with FRESH IDs from March 19")
        print("="*60)
        
        for ticket_id, ticket_name in FRESH_IDS.items():
            api_url = (
                f"https://tickets.museivaticani.va/api/visit/timeavail"
                f"?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum=1&visitDate=16/03/2026"
            )
            
            print(f"\nTesting: {ticket_name}")
            print(f"ID: {ticket_id}")
            
            try:
                response = await page.request.get(api_url, headers={
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': 'https://tickets.museivaticani.va/'
                })
                
                status = response.status
                print(f"Status: {status}")
                
                if status == 200:
                    data = await response.json()
                    
                    if 'timetable' in data:
                        available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                        total = len(data['timetable'])
                        
                        print(f"✅ SUCCESS! {len(available)}/{total} slots available")
                        
                        if available:
                            print("Available times:")
                            for slot in available[:10]:
                                print(f"  - {slot['time']}")
                        else:
                            print("⚠️  All slots SOLD OUT")
                    else:
                        print(f"Response: {json.dumps(data, indent=2)}")
                        
                elif status == 500:
                    text = await response.text()
                    print(f"❌ 500 Error: {text[:150]}")
                else:
                    text = await response.text()
                    print(f"❌ Status {status}: {text[:150]}")
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_march16_with_fresh_ids())
