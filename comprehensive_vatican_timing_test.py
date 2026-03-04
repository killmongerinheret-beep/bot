"""
Comprehensive Vatican Timing Test
==================================
End-to-end test measuring exact timing for:
1. Get cookies with proxy
2. Extract dynamic IDs
3. Ping time availability API
4. Complete flow analysis
"""
import asyncio
import time
import json
import os
from playwright.async_api import async_playwright
from datetime import datetime
from zoneinfo import ZoneInfo

# Load proxies
def load_proxies():
    """Load Oxylabs proxies from database or file"""
    proxies = []
    
    # Try Webshare first
    if os.path.exists("Webshare_10_proxies.txt"):
        with open("Webshare_10_proxies.txt", 'r') as f:
            for line in f:
                if line.strip() and ":" in line:
                    proxies.append(line.strip())
        print(f"✅ Loaded {len(proxies)} Webshare proxies")
        return proxies
    
    # Try Oxylabs JSON
    if os.path.exists("Proxy lists.json"):
        with open("Proxy lists.json", 'r') as f:
            data = json.load(f)
            for p in data:
                proxies.append(f"{p['entryPoint']}:{p['port']}")
        print(f"✅ Loaded {len(proxies)} Oxylabs proxies")
        return proxies
    
    print("⚠️ No proxies found")
    return []

def parse_proxy(proxy_str):
    """Convert proxy string to Playwright format"""
    parts = proxy_str.split(':')
    
    # Webshare format: ip:port:user:pass
    if len(parts) == 4:
        return {
            "server": f"http://{parts[0]}:{parts[1]}",
            "username": parts[2],
            "password": parts[3]
        }
    
    # Oxylabs format: entrypoint:port
    elif len(parts) == 2:
        if 'oxylabs' in proxy_str.lower():
            username = os.getenv('OXYLABS_USERNAME', 'abiilesh_2uVXW')
            password = os.getenv('OXYLABS_PASSWORD', 'Abiilesh@2005')
            if username and password:
                return {
                    "server": f"http://{proxy_str}",
                    "username": username,
                    "password": password
                }
        else:
            # Generic ip:port format
            return {
                "server": f"http://{proxy_str}"
            }
    
    return None

async def test_complete_flow_with_proxy(proxy_str, test_date="19/03/2026", visitors=1):
    """
    Complete end-to-end test with timing breakdown
    """
    print("\n" + "="*70)
    print(f"TESTING WITH PROXY: {proxy_str.split(':')[0]}:***")
    print("="*70)
    
    proxy_config = parse_proxy(proxy_str)
    if not proxy_config:
        print("❌ Invalid proxy format")
        return None
    
    timings = {
        "proxy": proxy_str.split(':')[0],
        "date": test_date,
        "visitors": visitors
    }
    
    total_start = time.time()
    
    try:
        async with async_playwright() as p:
            # STEP 1: Launch browser with proxy
            step1_start = time.time()
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            timings['browser_launch'] = time.time() - step1_start
            print(f"⏱️  Browser launch: {timings['browser_launch']:.2f}s")
            
            # STEP 2: Navigate to deep link and get cookies
            step2_start = time.time()
            
            # Calculate timestamp
            if "/" in test_date:
                day, month, year = test_date.split('/')
            else:
                year, month, day = test_date.split('-')
            
            rome = ZoneInfo("Europe/Rome")
            dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
            timestamp_ms = int(dt.timestamp() * 1000)
            
            deep_url = f"https://tickets.museivaticani.va/home/fromtag/{visitors}/{timestamp_ms}/MV-Biglietti/1"
            print(f"\n🌐 Navigating to: {deep_url}")
            
            await page.goto(deep_url, wait_until='domcontentloaded', timeout=30000)
            
            # Get cookies immediately
            cookies = await context.cookies()
            jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
            
            timings['get_cookies'] = time.time() - step2_start
            print(f"⏱️  Get cookies: {timings['get_cookies']:.2f}s")
            print(f"✅ JSESSIONID: {jsessionid[:30]}..." if jsessionid else "❌ No cookie!")
            
            if not jsessionid:
                await browser.close()
                return None
            
            # STEP 3: Wait for and extract dynamic IDs
            step3_start = time.time()
            print(f"\n🔍 Waiting for ticket IDs to load...")
            
            # Wait for tickets to appear (smart wait)
            try:
                await page.wait_for_selector('div[id^="ticket_"]', timeout=15000)
                print("✅ Ticket containers found")
            except:
                print("⚠️ Timeout waiting for tickets, trying anyway...")
            
            # Extract IDs
            tickets = await page.evaluate("""
                () => {
                    const results = [];
                    const containers = document.querySelectorAll('div[id^="ticket_"]');
                    
                    containers.forEach(container => {
                        const id = container.id.replace('ticket_', '');
                        
                        // Skip invalid IDs
                        if (id.startsWith('dx_') || id.length < 5) {
                            return;
                        }
                        
                        // Get ticket name
                        const titleEl = container.querySelector('.muvaTicketTitle, h1, h2, h3');
                        let name = 'Unknown';
                        if (titleEl) {
                            name = titleEl.innerText.trim();
                        }
                        
                        // Verify it's a Vatican ticket
                        const nameLower = name.toLowerCase();
                        const isVatican = nameLower.includes('musei') || 
                                         nameLower.includes('vatican') || 
                                         nameLower.includes('biglietti') ||
                                         nameLower.includes('ingresso') ||
                                         nameLower.includes('visita');
                        
                        if (isVatican) {
                            results.push({
                                id: id,
                                name: name
                            });
                        }
                    });
                    
                    return results;
                }
            """)
            
            timings['extract_ids'] = time.time() - step3_start
            print(f"⏱️  Extract IDs: {timings['extract_ids']:.2f}s")
            print(f"✅ Found {len(tickets)} ticket IDs:")
            for t in tickets[:3]:
                print(f"   {t['id']}: {t['name']}")
            
            if not tickets:
                print("❌ No tickets extracted!")
                await browser.close()
                return None
            
            # STEP 4: Call time availability API
            step4_start = time.time()
            
            # Use first standard ticket (not guided tour)
            standard_ticket = None
            for t in tickets:
                if 'biglietti' in t['name'].lower() or 'ingresso' in t['name'].lower():
                    if 'guidat' not in t['name'].lower():
                        standard_ticket = t
                        break
            
            if not standard_ticket:
                standard_ticket = tickets[0]
            
            ticket_id = standard_ticket['id']
            ticket_name = standard_ticket['name']
            
            print(f"\n🎫 Testing API with: {ticket_name}")
            print(f"   ID: {ticket_id}")
            
            api_url = (
                f"https://tickets.museivaticani.va/api/visit/timeavail"
                f"?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={test_date}"
            )
            
            response = await page.request.get(api_url, headers={
                'Accept': 'application/json, text/plain, */*',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://tickets.museivaticani.va/'
            })
            
            timings['api_call'] = time.time() - step4_start
            print(f"⏱️  API call: {timings['api_call']:.2f}s")
            
            status = response.status
            print(f"📡 API Status: {status}")
            
            if status == 200:
                data = await response.json()
                if 'timetable' in data:
                    available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                    total = len(data['timetable'])
                    print(f"✅ SUCCESS! {len(available)}/{total} slots available")
                    
                    timings['result'] = 'success'
                    timings['available_slots'] = len(available)
                    timings['total_slots'] = total
                    
                    if available:
                        print(f"   Sample times: {', '.join([s['time'] for s in available[:5]])}")
                else:
                    print(f"⚠️  No timetable in response")
                    timings['result'] = 'no_timetable'
            elif status == 500:
                print(f"❌ 500 Error - Date not released or ID invalid")
                timings['result'] = 'error_500'
            else:
                print(f"❌ Status {status}")
                timings['result'] = f'error_{status}'
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        timings['error'] = str(e)
        return None
    
    # Calculate total time
    timings['total_time'] = time.time() - total_start
    
    print(f"\n{'='*70}")
    print(f"TOTAL TIME: {timings['total_time']:.2f}s")
    print(f"{'='*70}")
    print(f"Breakdown:")
    print(f"  Browser launch: {timings.get('browser_launch', 0):.2f}s")
    print(f"  Get cookies:    {timings.get('get_cookies', 0):.2f}s")
    print(f"  Extract IDs:    {timings.get('extract_ids', 0):.2f}s")
    print(f"  API call:       {timings.get('api_call', 0):.2f}s")
    print(f"{'='*70}")
    
    return timings

async def main():
    print("="*70)
    print("COMPREHENSIVE VATICAN TIMING TEST")
    print("="*70)
    print("Testing complete flow: Cookies → IDs → API")
    print()
    
    # Load proxies
    proxies = load_proxies()
    
    if not proxies:
        print("❌ No proxies available, testing without proxy...")
        result = await test_complete_flow_with_proxy("no-proxy", "19/03/2026", 1)
        return
    
    # Test with 3 different proxies
    print(f"📊 Testing with {min(3, len(proxies))} proxies...\n")
    
    all_results = []
    
    for i, proxy in enumerate(proxies[:3], 1):
        print(f"\n{'#'*70}")
        print(f"TEST {i}/3")
        print(f"{'#'*70}")
        
        result = await test_complete_flow_with_proxy(proxy, "19/03/2026", 1)
        if result:
            all_results.append(result)
        
        # Small delay between tests
        if i < 3:
            await asyncio.sleep(2)
    
    # Summary
    if all_results:
        print(f"\n{'='*70}")
        print("SUMMARY - ALL TESTS")
        print(f"{'='*70}")
        
        successful = [r for r in all_results if r.get('result') == 'success']
        
        if successful:
            avg_total = sum(r['total_time'] for r in successful) / len(successful)
            avg_cookies = sum(r['get_cookies'] for r in successful) / len(successful)
            avg_ids = sum(r['extract_ids'] for r in successful) / len(successful)
            avg_api = sum(r['api_call'] for r in successful) / len(successful)
            
            print(f"\n✅ Successful tests: {len(successful)}/{len(all_results)}")
            print(f"\nAverage Timings:")
            print(f"  Total:       {avg_total:.2f}s")
            print(f"  Get cookies: {avg_cookies:.2f}s")
            print(f"  Extract IDs: {avg_ids:.2f}s")
            print(f"  API call:    {avg_api:.2f}s")
            
            print(f"\n🎯 OPTIMIZATION POTENTIAL:")
            print(f"  If IDs are cached: ~{avg_cookies + avg_api:.2f}s (skip ID extraction)")
            print(f"  Current full flow: ~{avg_total:.2f}s")
            print(f"  Time saved: ~{avg_ids:.2f}s ({(avg_ids/avg_total*100):.0f}%)")
        else:
            print("❌ No successful tests")
        
        # Save results
        with open('vatican_timing_results.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n💾 Results saved to vatican_timing_results.json")

if __name__ == "__main__":
    asyncio.run(main())
