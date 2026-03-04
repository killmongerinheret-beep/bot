#!/usr/bin/env python3
"""
Direct test for March 16, 2026
1. Navigate to deep link
2. Get cookies (JSESSIONID)
3. Extract ticket IDs
4. Call time availability API
"""

import asyncio
import sys
import os

# Add worker_vatican to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def test_march16_direct():
    print("\n" + "="*60)
    print("DIRECT TEST: MARCH 16, 2026")
    print("="*60)
    
    bot = HydraBot(use_proxies=True)
    
    try:
        async with bot.get_browser() as browser:
            page = await browser.new_page()
            
            # Step 1: Navigate to deep link
            deep_link = "https://tickets.museivaticani.va/home/fromtag/1/1773615600000/MV-Biglietti/1"
            print(f"\n📍 Step 1: Navigating to deep link")
            print(f"   URL: {deep_link}")
            
            await page.goto(deep_link, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Step 2: Get cookies
            print(f"\n🍪 Step 2: Extracting cookies")
            cookies = await page.context.cookies()
            
            jsessionid = None
            for cookie in cookies:
                if cookie['name'] == 'JSESSIONID':
                    jsessionid = cookie['value']
                    print(f"   ✅ JSESSIONID: {jsessionid[:20]}...")
                    break
            
            if not jsessionid:
                print(f"   ❌ No JSESSIONID found!")
                return
            
            # Step 3: Extract ticket IDs
            print(f"\n🎫 Step 3: Extracting ticket IDs")
            
            # Wait for ticket buttons
            await page.wait_for_selector('[data-cy^="bookTicket_"]', timeout=10000)
            
            # Extract IDs and names
            tickets_data = await page.evaluate("""
                () => {
                    const tickets = [];
                    const buttons = document.querySelectorAll('[data-cy^="bookTicket_"]');
                    
                    buttons.forEach(btn => {
                        const id = btn.getAttribute('data-cy').split('_')[1];
                        
                        // Look for .muvaTicketTitle specifically (main ticket name)
                        let name = "Unknown";
                        
                        // Strategy 1: Look for .muvaTicketTitle in parent container
                        const container = btn.closest('div');
                        if (container) {
                            const titleSpan = container.querySelector('.muvaTicketTitle');
                            if (titleSpan && titleSpan.innerText) {
                                name = titleSpan.innerText.trim();
                            }
                        }
                        
                        // Strategy 2: Search upwards for .muvaTicketTitle
                        if (name === "Unknown") {
                            let current = btn.parentElement;
                            for (let i = 0; i < 10 && current; i++) {
                                const titleSpan = current.querySelector('.muvaTicketTitle');
                                if (titleSpan && titleSpan.innerText) {
                                    name = titleSpan.innerText.trim();
                                    break;
                                }
                                current = current.parentElement;
                            }
                        }
                        
                        tickets.push({id: id, name: name});
                    });
                    
                    return tickets;
                }
            """)
            
            print(f"   Found {len(tickets_data)} tickets:")
            for i, ticket in enumerate(tickets_data, 1):
                print(f"   {i}. ID: {ticket['id']}")
                print(f"      Name: {ticket['name']}")
            
            # Step 4: Call time availability API for each ticket
            print(f"\n🌐 Step 4: Calling time availability API")
            
            for ticket in tickets_data:
                ticket_id = ticket['id']
                ticket_name = ticket['name']
                
                print(f"\n   Testing: {ticket_name}")
                print(f"   ID: {ticket_id}")
                
                # Build API URL (standard ticket, no language)
                api_url = (
                    f"https://tickets.museivaticani.va/api/visit/timeavail"
                    f"?lang=it&visitLang=&visitTypeId={ticket_id}"
                    f"&visitorNum=1&visitDate=16/03/2026"
                )
                
                print(f"   URL: {api_url}")
                
                # Make API request
                try:
                    response = await page.request.get(
                        api_url,
                        headers={
                            'Accept': 'application/json, text/plain, */*',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Referer': 'https://tickets.museivaticani.va/',
                            'Cookie': f'JSESSIONID={jsessionid}'
                        }
                    )
                    
                    status = response.status
                    print(f"   Status: {status}")
                    
                    if status == 200:
                        data = await response.json()
                        timetable = data.get('timetable', [])
                        
                        available = []
                        sold_out = []
                        
                        for slot in timetable:
                            time = slot.get('time')
                            avail = slot.get('availability')
                            
                            if avail == 'SOLD_OUT':
                                sold_out.append(time)
                            else:
                                available.append(time)
                        
                        print(f"   Total slots: {len(timetable)}")
                        print(f"   Available: {len(available)}")
                        print(f"   Sold out: {len(sold_out)}")
                        
                        if available:
                            print(f"   ✅ Available times: {', '.join(available[:5])}")
                            if len(available) > 5:
                                print(f"      ... and {len(available) - 5} more")
                    else:
                        text = await response.text()
                        print(f"   ❌ Error: {text[:200]}")
                
                except Exception as e:
                    print(f"   ❌ Request failed: {e}")
            
            # Summary
            print(f"\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            print(f"✅ Successfully navigated to deep link")
            print(f"✅ Extracted JSESSIONID cookie")
            print(f"✅ Found {len(tickets_data)} ticket types")
            print(f"✅ Tested API for all tickets")
            
    finally:
        pass

if __name__ == '__main__':
    asyncio.run(test_march16_direct())
