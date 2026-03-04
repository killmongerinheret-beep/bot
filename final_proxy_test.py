"""
Final test: Complete flow with Oxylabs proxy
Get cookies, IDs, and call API successfully
"""
import asyncio
import time
from playwright.async_api import async_playwright
import os

async def complete_flow_test():
    print("="*70)
    print("COMPLETE FLOW TEST WITH OXYLABS PROXY")
    print("="*70)
    
    # Use first Oxylabs proxy
    proxy_config = {
        "server": "http://isp.oxylabs.io:8001",
        "username": "abiilesh_2uVXW",
        "password": "Abiilesh@2005"
    }
    
    total_start = time.time()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=proxy_config,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate and get cookies
        print("\n1. Getting cookies...")
        await page.goto(
            "https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1",
            timeout=30000,
            wait_until='domcontentloaded'
        )
        
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        print(f"✅ JSESSIONID: {jsessionid[:30]}...")
        
        # Extract IDs
        print("\n2. Extracting ticket IDs...")
        await page.wait_for_selector('div[id^="ticket_"]', timeout=15000)
        
        tickets = await page.evaluate("""
            () => {
                const results = [];
                document.querySelectorAll('div[id^="ticket_"]').forEach(c => {
                    const id = c.id.replace('ticket_', '');
                    if (!id.startsWith('dx_') && id.length > 5) {
                        const title = c.querySelector('.muvaTicketTitle');
                        if (title) {
                            const name = title.innerText.trim();
                            if (name.toLowerCase().includes('biglietti') || 
                                name.toLowerCase().includes('ingresso')) {
                                results.push({id: id, name: name});
                            }
                        }
                    }
                });
                return results;
            }
        """)
        
        print(f"✅ Found {len(tickets)} tickets")
        for t in tickets[:3]:
            print(f"   {t['id']}: {t['name']}")
        
        if not tickets:
            print("❌ No tickets found!")
            await browser.close()
            return
        
        # Call API - Use page.request which inherits proxy
        print("\n3. Calling time availability API...")
        ticket_id = tickets[0]['id']
        
        api_url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum=1&visitDate=19/03/2026"
        
        # The key: Use page.request.get() which automatically uses the browser's proxy
        response = await page.request.get(api_url, headers={
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://tickets.museivaticani.va/'
        })
        
        print(f"📡 API Status: {response.status}")
        
        if response.status == 200:
            data = await response.json()
            if 'timetable' in data:
                available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                print(f"✅ SUCCESS! {len(available)} slots available")
                
                if available:
                    print("\nAvailable times:")
                    for slot in available[:10]:
                        print(f"  - {slot['time']}")
        else:
            text = await response.text()
            print(f"⚠️  Status {response.status}: {text[:200]}")
        
        await browser.close()
        
        total_time = time.time() - total_start
        print(f"\n{'='*70}")
        print(f"✅ TOTAL TIME: {total_time:.2f}s")
        print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(complete_flow_test())
