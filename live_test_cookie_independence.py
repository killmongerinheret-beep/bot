"""
Live test: Extract fresh IDs and test cookie independence immediately
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Test March 19 (known to have tickets)
        print("="*70)
        print("LIVE TEST: March 19")
        print("="*70)
        
        # Context 1: Get March 19 cookie and IDs
        context19 = await browser.new_context()
        page19 = await context19.new_page()
        
        print("\n1. Navigating to March 19...")
        await page19.goto("https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1",
                         wait_until='domcontentloaded', timeout=30000)
        
        print("2. Waiting for tickets to load (10 seconds)...")
        await page19.wait_for_timeout(10000)
        
        print("3. Extracting IDs...")
        tickets19 = await page19.evaluate("""
            () => {
                const results = [];
                const containers = document.querySelectorAll('div[id^="ticket_"]');
                containers.forEach(c => {
                    const id = c.id.replace('ticket_', '');
                    if (!id.startsWith('dx_') && id.length > 5) {
                        const title = c.querySelector('.muvaTicketTitle, h1, h2');
                        results.push({
                            id: id,
                            name: title ? title.innerText.trim() : 'Unknown'
                        });
                    }
                });
                return results;
            }
        """)
        
        if not tickets19:
            print("❌ No tickets found on March 19!")
            await browser.close()
            return
        
        print(f"✅ Found {len(tickets19)} tickets:")
        for t in tickets19[:3]:
            print(f"   {t['id']}: {t['name']}")
        
        # Get March 19 cookie
        cookies19 = await context19.cookies()
        cookie19 = next((c['value'] for c in cookies19 if c['name'] == 'JSESSIONID'), None)
        print(f"\n4. March 19 JSESSIONID: {cookie19[:30]}...")
        
        # Test with March 19's own cookie
        first_id = tickets19[0]['id']
        print(f"\n5. Testing ID {first_id} with March 19 cookie...")
        
        api_url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId={first_id}&visitorNum=1&visitDate=19/03/2026"
        
        response = await page19.request.get(api_url, headers={
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        print(f"   Status: {response.status}")
        if response.status == 200:
            data = await response.json()
            if 'timetable' in data:
                available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                print(f"   ✅ SUCCESS! {len(available)} available slots")
        
        # Now test with a DIFFERENT cookie (from March 20)
        print("\n" + "="*70)
        print("6. Getting cookie from March 20...")
        print("="*70)
        
        context20 = await browser.new_context()
        page20 = await context20.new_page()
        
        await page20.goto("https://tickets.museivaticani.va/home/fromtag/1/1773961200000/MV-Biglietti/1",
                         wait_until='commit', timeout=10000)
        await page20.wait_for_timeout(1000)
        
        cookies20 = await context20.cookies()
        cookie20 = next((c['value'] for c in cookies20 if c['name'] == 'JSESSIONID'), None)
        print(f"March 20 JSESSIONID: {cookie20[:30]}...")
        
        # Test March 19 date with March 20 cookie
        print(f"\n7. Testing March 19 ID with March 20 cookie...")
        print(f"   ID: {first_id}")
        print(f"   Date: 19/03/2026")
        print(f"   Cookie from: March 20")
        
        response2 = await page20.request.get(api_url, headers={
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        print(f"   Status: {response2.status}")
        if response2.status == 200:
            data2 = await response2.json()
            if 'timetable' in data2:
                available2 = [t for t in data2['timetable'] if t.get('availability') != 'SOLD_OUT']
                print(f"   ✅ SUCCESS! {len(available2)} available slots")
                print("\n   🎯 CONCLUSION: Cookies are INDEPENDENT!")
                print("      → Can use ANY cookie with ANY date/ID")
        elif response2.status == 500:
            print(f"   ❌ 500 Error")
            print("\n   🎯 CONCLUSION: Cookies are DATE-SPECIFIC")
            print("      → Must use cookie from same date as deep link")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
