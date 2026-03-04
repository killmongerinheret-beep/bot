"""
Test Oxylabs proxies directly with Vatican
Skip intermediate tests - ISP proxies may have restrictions
"""
import asyncio
import os
import json
import time
from playwright.async_api import async_playwright

async def test_vatican_with_oxylabs(proxy_str):
    """Test Vatican directly with Oxylabs ISP proxy"""
    print(f"\n{'='*70}")
    print(f"Testing Oxylabs: {proxy_str}")
    print(f"{'='*70}")
    
    # Parse Oxylabs proxy
    parts = proxy_str.split(':')
    username = os.getenv('OXYLABS_USERNAME', 'abiilesh_2uVXW')
    password = os.getenv('OXYLABS_PASSWORD', 'Abiilesh@2005')
    
    proxy_config = {
        "server": f"http://{proxy_str}",
        "username": username,
        "password": password
    }
    
    print(f"Server: {proxy_config['server']}")
    print(f"Username: {username}")
    
    total_start = time.time()
    
    try:
        async with async_playwright() as p:
            # Launch with proxy
            t1 = time.time()
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            print(f"⏱️  Browser launch: {time.time() - t1:.2f}s")
            
            # Navigate to Vatican deep link
            t2 = time.time()
            print(f"\n🌐 Navigating to Vatican...")
            
            await page.goto(
                "https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1",
                timeout=45000,  # Longer timeout for proxy
                wait_until='domcontentloaded'
            )
            
            nav_time = time.time() - t2
            print(f"⏱️  Navigation: {nav_time:.2f}s")
            
            # Get cookies
            cookies = await context.cookies()
            jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
            
            if jsessionid:
                print(f"✅ Got JSESSIONID: {jsessionid[:30]}...")
            else:
                print("❌ No JSESSIONID cookie!")
                await browser.close()
                return None
            
            # Wait for and extract IDs
            t3 = time.time()
            print(f"\n🔍 Waiting for ticket IDs...")
            
            try:
                await page.wait_for_selector('div[id^="ticket_"]', timeout=20000)
                print("✅ Tickets loaded")
            except:
                print("⚠️  Timeout, checking anyway...")
            
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
            
            extract_time = time.time() - t3
            print(f"⏱️  Extract IDs: {extract_time:.2f}s")
            print(f"✅ Found {len(tickets)} ticket IDs")
            
            if tickets:
                for t in tickets[:3]:
                    print(f"   {t['id']}: {t['name']}")
                
                # Test API call
                t4 = time.time()
                ticket_id = tickets[0]['id']
                print(f"\n📡 Testing API with ID: {ticket_id}")
                
                api_url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum=1&visitDate=19/03/2026"
                
                response = await page.request.get(api_url, headers={
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                })
                
                api_time = time.time() - t4
                print(f"⏱️  API call: {api_time:.2f}s")
                print(f"📡 Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    if 'timetable' in data:
                        available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                        print(f"✅ SUCCESS! {len(available)} slots available")
            
            await browser.close()
            
            total_time = time.time() - total_start
            print(f"\n{'='*70}")
            print(f"✅ TOTAL TIME: {total_time:.2f}s")
            print(f"{'='*70}")
            print(f"Breakdown:")
            print(f"  Browser:    {time.time() - t1:.2f}s")
            print(f"  Navigation: {nav_time:.2f}s")
            print(f"  Extract:    {extract_time:.2f}s")
            if tickets:
                print(f"  API:        {api_time:.2f}s")
            
            return {
                "success": True,
                "total_time": total_time,
                "tickets_found": len(tickets)
            }
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return None

async def main():
    print("="*70)
    print("OXYLABS ISP PROXY TEST - DIRECT VATICAN")
    print("="*70)
    
    # Load Oxylabs proxies
    proxies = []
    if os.path.exists("Proxy lists.json"):
        with open("Proxy lists.json", 'r') as f:
            data = json.load(f)
            for p in data:
                proxies.append(f"{p['entryPoint']}:{p['port']}")
        print(f"✅ Loaded {len(proxies)} Oxylabs proxies\n")
    else:
        print("❌ No Proxy lists.json found")
        return
    
    # Test first 3 proxies
    results = []
    for i, proxy in enumerate(proxies[:3], 1):
        print(f"\n{'#'*70}")
        print(f"TEST {i}/3")
        print(f"{'#'*70}")
        
        result = await test_vatican_with_oxylabs(proxy)
        if result:
            results.append(result)
        
        if i < 3:
            await asyncio.sleep(2)
    
    # Summary
    if results:
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"\n✅ Successful tests: {len(results)}/3")
        
        avg_time = sum(r['total_time'] for r in results) / len(results)
        print(f"\nAverage total time: {avg_time:.2f}s")
        print(f"Average tickets found: {sum(r['tickets_found'] for r in results) / len(results):.0f}")
        
        print(f"\n🎯 CONCLUSION:")
        print(f"   Oxylabs ISP proxies {'WORK' if len(results) > 0 else 'DO NOT WORK'} with Vatican")
        print(f"   Average time with proxy: {avg_time:.2f}s")
        print(f"   vs No proxy: ~9s")
        print(f"   Overhead: {avg_time - 9:.2f}s ({((avg_time/9 - 1) * 100):.0f}% slower)")
    else:
        print(f"\n❌ All tests failed - Oxylabs proxies not working")

if __name__ == "__main__":
    asyncio.run(main())
