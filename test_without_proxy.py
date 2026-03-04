"""
Quick test without proxy to get baseline timing
"""
import asyncio
import time
from playwright.async_api import async_playwright
from datetime import datetime
from zoneinfo import ZoneInfo

async def test_no_proxy():
    print("="*70)
    print("BASELINE TEST - NO PROXY")
    print("="*70)
    
    total_start = time.time()
    
    async with async_playwright() as p:
        # Launch
        t1 = time.time()
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        print(f"⏱️  Browser launch: {time.time() - t1:.2f}s")
        
        # Navigate
        t2 = time.time()
        await page.goto("https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1",
                       wait_until='domcontentloaded', timeout=30000)
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        print(f"⏱️  Get cookies: {time.time() - t2:.2f}s")
        print(f"✅ Cookie: {jsessionid[:30]}..." if jsessionid else "❌ No cookie")
        
        # Extract IDs
        t3 = time.time()
        try:
            await page.wait_for_selector('div[id^="ticket_"]', timeout=20000)
            print("✅ Tickets loaded")
        except:
            print("⚠️  Timeout waiting for tickets, checking anyway...")
        
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
        print(f"⏱️  Extract IDs: {time.time() - t3:.2f}s")
        print(f"✅ Found {len(tickets)} IDs")
        
        if tickets:
            # API call
            t4 = time.time()
            ticket_id = tickets[0]['id']
            api_url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum=1&visitDate=19/03/2026"
            
            response = await page.request.get(api_url, headers={
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            })
            print(f"⏱️  API call: {time.time() - t4:.2f}s")
            print(f"📡 Status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                if 'timetable' in data:
                    available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                    print(f"✅ {len(available)} slots available")
        
        await browser.close()
    
    print(f"\n⏱️  TOTAL: {time.time() - total_start:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_no_proxy())
