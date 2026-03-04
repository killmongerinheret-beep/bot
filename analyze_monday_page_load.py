#!/usr/bin/env python3
"""
Analyze Monday page load timing for March 23, 2026
Fetch HTML/JS and measure when Musei Vaticani ticket appears
"""
import asyncio
import time
from playwright.async_api import async_playwright

async def analyze_monday_page():
    print("=" * 80)
    print("ANALYZING MONDAY PAGE LOAD - MARCH 23, 2026")
    print("=" * 80)
    
    # March 23, 2026 = Monday, 1 visitor
    url = "https://tickets.museivaticani.va/home/fromtag/1/1774220400000/MV-Biglietti/1"
    
    print(f"\n🌐 URL: {url}")
    print(f"📅 Date: March 23, 2026 (Monday)")
    print(f"👥 Visitors: 1")
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    
    try:
        start_time = time.time()
        print(f"\n⏱️ Starting page load at {start_time:.2f}s")
        
        # Navigate and wait for network idle
        await page.goto(url, timeout=120000, wait_until="networkidle")
        after_nav = time.time() - start_time
        print(f"✅ Navigation complete after {after_nav:.1f}s")
        
        # Wait for initial render
        await page.wait_for_timeout(5000)
        after_initial = time.time() - start_time
        print(f"⏱️ After 5s wait: {after_initial:.1f}s")
        
        # Check every 2 seconds for up to 60 seconds
        max_wait = 60
        check_interval = 2
        elapsed = after_initial
        
        print(f"\n🔍 Checking for 'Musei Vaticani' ticket every {check_interval}s...")
        
        while elapsed < max_wait:
            # Count all ticket containers
            all_tickets = await page.evaluate('''() => {
                const containers = document.querySelectorAll('div[id^="ticket_"]');
                const tickets = [];
                
                containers.forEach(container => {
                    const id = container.getAttribute('id').replace('ticket_', '');
                    const titleEl = container.querySelector('.muvaTicketTitle, h1, h2, h3, h4');
                    const title = titleEl ? titleEl.textContent.trim() : 'Unknown';
                    tickets.push({id: id, title: title});
                });
                
                return tickets;
            }''')
            
            # Check if Musei Vaticani exists
            musei_found = any('musei' in t['title'].lower() and 'vaticani' in t['title'].lower() 
                             and 'biglietti' in t['title'].lower() 
                             for t in all_tickets)
            
            elapsed = time.time() - start_time
            
            if musei_found:
                print(f"\n✅ 'Musei Vaticani - Biglietti d'ingresso' FOUND after {elapsed:.1f}s!")
                print(f"\n📋 All tickets found ({len(all_tickets)}):")
                for t in all_tickets:
                    marker = "✅" if 'musei' in t['title'].lower() and 'vaticani' in t['title'].lower() and 'biglietti' in t['title'].lower() else "  "
                    print(f"   {marker} ID: {t['id']} | {t['title']}")
                break
            else:
                print(f"⏱️ {elapsed:.1f}s: Found {len(all_tickets)} tickets, but NO 'Musei Vaticani - Biglietti'")
                if all_tickets:
                    print(f"   Tickets found: {[t['title'][:40] for t in all_tickets[:3]]}")
                
                # Wait before next check
                await page.wait_for_timeout(check_interval * 1000)
                elapsed = time.time() - start_time
        
        if not musei_found:
            print(f"\n❌ 'Musei Vaticani' NOT FOUND after {elapsed:.1f}s")
            print(f"\n📋 Final tickets found ({len(all_tickets)}):")
            for t in all_tickets:
                print(f"   • ID: {t['id']} | {t['title']}")
            
            # Get raw HTML to see if it's there but hidden
            print(f"\n🔍 Checking raw HTML for hidden ticket...")
            html = await page.content()
            if 'ticket_' in html and 'Musei Vaticani' in html:
                print(f"✅ Found 'Musei Vaticani' in raw HTML - ticket is HIDDEN/COLLAPSED")
                # Find the ticket ID
                import re
                matches = re.findall(r'id="ticket_(\d+)"[^>]*>.*?Musei Vaticani.*?Biglietti', html, re.DOTALL)
                if matches:
                    print(f"   Ticket ID in HTML: {matches[0]}")
            else:
                print(f"❌ 'Musei Vaticani' NOT in raw HTML either")
        
        # Take screenshot
        await page.screenshot(path="monday_page_final.png")
        print(f"\n📸 Screenshot saved: monday_page_final.png")
        
        # Get page metrics
        metrics = await page.evaluate('''() => {
            return {
                readyState: document.readyState,
                ticketContainers: document.querySelectorAll('div[id^="ticket_"]').length,
                muvaTicketTitles: document.querySelectorAll('.muvaTicketTitle').length,
                allDivs: document.querySelectorAll('div').length,
                bodyHTML: document.body.innerHTML.length
            };
        }''')
        
        print(f"\n📊 Page Metrics:")
        print(f"   Ready State: {metrics['readyState']}")
        print(f"   Ticket Containers: {metrics['ticketContainers']}")
        print(f"   Ticket Titles: {metrics['muvaTicketTitles']}")
        print(f"   Total DIVs: {metrics['allDivs']}")
        print(f"   Body HTML Size: {metrics['bodyHTML']} chars")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()
    
    print(f"\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(analyze_monday_page())
