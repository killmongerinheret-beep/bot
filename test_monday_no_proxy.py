#!/usr/bin/env python3
"""
Test Monday extraction WITHOUT proxy to isolate network issue
"""
import asyncio
import time
from playwright.async_api import async_playwright

async def test_no_proxy():
    print("=" * 80)
    print("TESTING MARCH 23 (MONDAY) - NO PROXY")
    print("=" * 80)
    
    url = "https://tickets.museivaticani.va/home/fromtag/1/1774220400000/MV-Biglietti/1"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    
    try:
        start_time = time.time()
        print(f"\n⏱️ Starting navigation...")
        
        # Navigate with shorter timeout
        await page.goto(url, timeout=60000, wait_until="networkidle")
        nav_time = time.time() - start_time
        print(f"✅ Navigation complete: {nav_time:.1f}s")
        
        # Wait 10 seconds
        await page.wait_for_timeout(10000)
        wait_time = time.time() - start_time
        print(f"⏱️ After 10s wait: {wait_time:.1f}s")
        
        # Extract with aggressive search
        ids = await page.evaluate('''() => {
            const results = [];
            const seenIds = new Set();
            
            const ticketContainers = document.querySelectorAll('div[id^="ticket_"]');
            
            ticketContainers.forEach(container => {
                const containerId = container.getAttribute('id');
                const ticketId = containerId ? containerId.replace('ticket_', '') : null;
                
                if (!ticketId || ticketId.startsWith('dx_') || seenIds.has(ticketId)) return;
                
                // AGGRESSIVE TITLE SEARCH
                let titleEl = null;
                
                // Strategy 1: Standard
                titleEl = container.querySelector('.muvaTicketTitle, h1, h2, h3, h4');
                
                // Strategy 2: Nested
                if (!titleEl || !titleEl.textContent.trim()) {
                    const detailsEl = container.querySelector('app-ticket-details');
                    if (detailsEl) {
                        titleEl = detailsEl.querySelector('.muvaTicketTitle, h1, h2, h3, h4, span[class*="title"]');
                    }
                }
                
                // Strategy 3: ANY span
                if (!titleEl || !titleEl.textContent.trim()) {
                    const allSpans = container.querySelectorAll('span');
                    for (const span of allSpans) {
                        const text = span.textContent.trim();
                        if (text.length > 10 && !text.includes('€') && !text.includes('PRENOTA')) {
                            titleEl = span;
                            break;
                        }
                    }
                }
                
                const ticketName = titleEl ? titleEl.textContent.trim() : null;
                
                if (ticketName && ticketName.length > 5) {
                    results.push({
                        id: ticketId,
                        name: ticketName
                    });
                    seenIds.add(ticketId);
                }
            });
            
            return results;
        }''')
        
        extract_time = time.time() - start_time
        print(f"⏱️ Extraction complete: {extract_time:.1f}s")
        
        print(f"\n📊 RESULTS:")
        print(f"   Total tickets: {len(ids)}")
        
        # Check for Musei Vaticani
        musei_found = False
        for item in ids:
            if 'musei' in item['name'].lower() and 'vaticani' in item['name'].lower() and 'biglietti' in item['name'].lower():
                musei_found = True
                print(f"\n✅ SUCCESS: Found Musei Vaticani!")
                print(f"   ID: {item['id']}")
                print(f"   Name: {item['name']}")
                break
        
        if not musei_found:
            print(f"\n❌ FAILED: Musei Vaticani NOT found")
        
        print(f"\n📋 All tickets:")
        for item in ids:
            marker = "✅" if 'musei' in item['name'].lower() and 'vaticani' in item['name'].lower() and 'biglietti' in item['name'].lower() else "  "
            print(f"   {marker} {item['id']}: {item['name'][:60]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_no_proxy())
