"""
Benchmark Vatican page loading times with different strategies
Find the optimal approach for getting cookies + IDs
"""
import asyncio
from playwright.async_api import async_playwright
import time

async def strategy_1_minimal_cookie_only():
    """Strategy 1: Just get cookie, no waiting for content"""
    start = time.time()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Just navigate, don't wait for anything
        await page.goto(
            "https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1",
            wait_until='commit',  # Just wait for navigation
            timeout=10000
        )
        
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        
        await browser.close()
        
    elapsed = time.time() - start
    return elapsed, bool(jsessionid)

async def strategy_2_domcontentloaded():
    """Strategy 2: Wait for DOM to be ready"""
    start = time.time()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(
            "https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1",
            wait_until='domcontentloaded',
            timeout=30000
        )
        
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        
        await browser.close()
        
    elapsed = time.time() - start
    return elapsed, bool(jsessionid)

async def strategy_3_wait_for_tickets(wait_time):
    """Strategy 3: Wait for DOM + additional time for Angular to render"""
    start = time.time()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(
            "https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1",
            wait_until='domcontentloaded',
            timeout=30000
        )
        
        # Wait additional time for Angular
        await page.wait_for_timeout(wait_time)
        
        # Try to extract IDs
        tickets = await page.evaluate("""
            () => {
                const results = [];
                const containers = document.querySelectorAll('div[id^="ticket_"]');
                containers.forEach(c => {
                    const id = c.id.replace('ticket_', '');
                    if (!id.startsWith('dx_') && id.length > 5) {
                        results.push(id);
                    }
                });
                return results;
            }
        """)
        
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        
        await browser.close()
        
    elapsed = time.time() - start
    return elapsed, bool(jsessionid), len(tickets)

async def strategy_4_wait_for_selector():
    """Strategy 4: Wait for specific ticket selector to appear"""
    start = time.time()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(
            "https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1",
            wait_until='domcontentloaded',
            timeout=30000
        )
        
        # Wait for ticket containers to appear
        try:
            await page.wait_for_selector('div[id^="ticket_"]', timeout=15000)
            selector_found = True
        except:
            selector_found = False
        
        # Extract IDs
        tickets = await page.evaluate("""
            () => {
                const results = [];
                const containers = document.querySelectorAll('div[id^="ticket_"]');
                containers.forEach(c => {
                    const id = c.id.replace('ticket_', '');
                    if (!id.startsWith('dx_') && id.length > 5) {
                        results.push(id);
                    }
                });
                return results;
            }
        """)
        
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        
        await browser.close()
        
    elapsed = time.time() - start
    return elapsed, bool(jsessionid), len(tickets), selector_found

async def main():
    print("="*70)
    print("VATICAN PAGE LOADING BENCHMARK")
    print("="*70)
    print("Testing different strategies to find optimal approach\n")
    
    # Strategy 1: Minimal (just cookie)
    print("Strategy 1: Minimal Cookie Grab (no waiting)")
    print("-" * 70)
    times = []
    for i in range(3):
        elapsed, has_cookie = await strategy_1_minimal_cookie_only()
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.2f}s - Cookie: {'✅' if has_cookie else '❌'}")
    avg = sum(times) / len(times)
    print(f"  Average: {avg:.2f}s")
    print(f"  ✅ Gets cookie only, no IDs\n")
    
    # Strategy 2: DOM ready
    print("Strategy 2: Wait for DOM Content Loaded")
    print("-" * 70)
    times = []
    for i in range(3):
        elapsed, has_cookie = await strategy_2_domcontentloaded()
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.2f}s - Cookie: {'✅' if has_cookie else '❌'}")
    avg = sum(times) / len(times)
    print(f"  Average: {avg:.2f}s")
    print(f"  ✅ Gets cookie, HTML loaded but Angular not rendered\n")
    
    # Strategy 3: Fixed wait times
    for wait_ms in [3000, 5000, 8000, 10000]:
        print(f"Strategy 3: DOM + {wait_ms}ms wait for Angular")
        print("-" * 70)
        times = []
        ticket_counts = []
        for i in range(3):
            elapsed, has_cookie, ticket_count = await strategy_3_wait_for_tickets(wait_ms)
            times.append(elapsed)
            ticket_counts.append(ticket_count)
            print(f"  Run {i+1}: {elapsed:.2f}s - Cookie: {'✅' if has_cookie else '❌'} - IDs: {ticket_count}")
        avg = sum(times) / len(times)
        avg_tickets = sum(ticket_counts) / len(ticket_counts)
        print(f"  Average: {avg:.2f}s - Avg IDs: {avg_tickets:.1f}")
        if avg_tickets > 0:
            print(f"  ✅ Gets cookie + IDs\n")
        else:
            print(f"  ❌ No IDs extracted\n")
    
    # Strategy 4: Wait for selector
    print("Strategy 4: Wait for Ticket Selector (smart wait)")
    print("-" * 70)
    times = []
    ticket_counts = []
    for i in range(3):
        elapsed, has_cookie, ticket_count, found = await strategy_4_wait_for_selector()
        times.append(elapsed)
        ticket_counts.append(ticket_count)
        print(f"  Run {i+1}: {elapsed:.2f}s - Cookie: {'✅' if has_cookie else '❌'} - IDs: {ticket_count} - Selector: {'✅' if found else '❌'}")
    avg = sum(times) / len(times)
    avg_tickets = sum(ticket_counts) / len(ticket_counts)
    print(f"  Average: {avg:.2f}s - Avg IDs: {avg_tickets:.1f}")
    if avg_tickets > 0:
        print(f"  ✅ Gets cookie + IDs (waits only as long as needed)\n")
    else:
        print(f"  ❌ No IDs extracted\n")
    
    print("="*70)
    print("RECOMMENDATION")
    print("="*70)
    print("Based on timing results above:")
    print("  • If you only need cookies: Use Strategy 1 (~1-2s)")
    print("  • If you need cookies + IDs: Use Strategy 4 (smart wait)")
    print("  • Strategy 4 is optimal: waits only until tickets appear")

if __name__ == "__main__":
    asyncio.run(main())
