"""
Extract actual ticket IDs from March 16 page and test API
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def extract_and_test_march16():
    """Get real IDs from March 16 page and test API"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Navigate to March 16 deep link
        print("="*60)
        print("STEP 1: Navigating to March 16 deep link...")
        print("="*60)
        deep_url = "https://tickets.museivaticani.va/home/fromtag/1/1773615600000/MV-Biglietti/1"
        print(f"URL: {deep_url}")
        
        await page.goto(deep_url, wait_until='domcontentloaded', timeout=30000)
        print("Waiting for page to load...")
        await page.wait_for_timeout(8000)  # Wait longer for Angular to render
        
        # Get cookies
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        print(f"\n✅ JSESSIONID: {jsessionid[:30]}..." if jsessionid else "❌ No JSESSIONID!")
        
        # Extract ticket IDs
        print("\n" + "="*60)
        print("STEP 2: Extracting ticket IDs from page...")
        print("="*60)
        
        tickets = await page.evaluate("""
            () => {
                const results = [];
                
                // Method 1: From div containers with id="ticket_XXX"
                const containers = document.querySelectorAll('div[id^="ticket_"]');
                console.log('Found containers:', containers.length);
                
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
                            name: name,
                            source: 'container'
                        });
                    }
                });
                
                // Method 2: From buttons as fallback
                if (results.length === 0) {
                    const buttons = document.querySelectorAll('[data-cy^="bookTicket_"]');
                    console.log('Found buttons:', buttons.length);
                    
                    buttons.forEach(btn => {
                        const id = btn.getAttribute('data-cy').replace('bookTicket_', '');
                        if (!id.startsWith('dx_') && id.length >= 5) {
                            results.push({
                                id: id,
                                name: 'From button',
                                source: 'button'
                            });
                        }
                    });
                }
                
                return results;
            }
        """)
        
        if not tickets:
            print("❌ No tickets found! Let me check the HTML...")
            html = await page.content()
            # Save HTML for inspection
            with open('march16_page_source.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("Saved page source to march16_page_source.html")
            
            # Try to find any ticket-related elements
            print("\nSearching for ticket elements...")
            ticket_divs = await page.query_selector_all('div[id^="ticket_"]')
            print(f"Found {len(ticket_divs)} divs with id starting with 'ticket_'")
            
            await browser.close()
            return
        
        print(f"\n✅ Found {len(tickets)} tickets:")
        for t in tickets:
            print(f"   ID: {t['id']}")
            print(f"   Name: {t['name']}")
            print(f"   Source: {t['source']}")
            print()
        
        # Test each ticket ID with API
        print("="*60)
        print("STEP 3: Testing each ID with API...")
        print("="*60)
        
        for ticket in tickets:
            ticket_id = ticket['id']
            ticket_name = ticket['name']
            
            print(f"\nTesting ID: {ticket_id} ({ticket_name})")
            
            # Build API URL
            api_url = (
                f"https://tickets.museivaticani.va/api/visit/timeavail"
                f"?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum=1&visitDate=16/03/2026"
            )
            
            try:
                response = await page.request.get(api_url, headers={
                    'Accept': 'application/json, text/plain, */*',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': 'https://tickets.museivaticani.va/'
                })
                
                status = response.status
                print(f"   Status: {status}")
                
                if status == 200:
                    data = await response.json()
                    
                    if 'timetable' in data:
                        available_slots = [
                            t['time'] for t in data['timetable'] 
                            if t.get('availability') != 'SOLD_OUT'
                        ]
                        
                        if available_slots:
                            print(f"   ✅ AVAILABLE! Found {len(available_slots)} slots:")
                            for slot in available_slots[:5]:
                                print(f"      - {slot}")
                            if len(available_slots) > 5:
                                print(f"      ... and {len(available_slots) - 5} more")
                        else:
                            print(f"   ⚠️  SOLD OUT - All {len(data['timetable'])} slots taken")
                    else:
                        print(f"   ⚠️  No timetable in response: {data}")
                        
                elif status == 500:
                    print(f"   ❌ 500 Error - ID might be invalid or date not released")
                else:
                    text = await response.text()
                    print(f"   ❌ Error {status}: {text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        await browser.close()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total IDs extracted: {len(tickets)}")
        print(f"JSESSIONID obtained: {'Yes' if jsessionid else 'No'}")

if __name__ == "__main__":
    asyncio.run(extract_and_test_march16())
