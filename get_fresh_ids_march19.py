"""
Get fresh IDs from March 19 page and test immediately
"""
import asyncio
from playwright.async_api import async_playwright

async def get_fresh_ids_and_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("Navigating to March 19...")
        await page.goto("https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1", 
                       wait_until='domcontentloaded', timeout=30000)
        
        print("Waiting 10 seconds for tickets to load...")
        await page.wait_for_timeout(10000)
        
        # Extract IDs
        print("\nExtracting ticket IDs...")
        result = await page.evaluate("""
            () => {
                const tickets = [];
                
                // Check all possible selectors
                const containers = document.querySelectorAll('div[id^="ticket_"]');
                console.log('Containers found:', containers.length);
                
                containers.forEach(c => {
                    const id = c.id.replace('ticket_', '');
                    if (!id.startsWith('dx_') && id.length > 5) {
                        const title = c.querySelector('.muvaTicketTitle, h1, h2');
                        tickets.push({
                            id: id,
                            name: title ? title.innerText.trim() : 'Unknown'
                        });
                    }
                });
                
                return {
                    tickets: tickets,
                    html_sample: document.body.innerHTML.substring(0, 2000)
                };
            }
        """)
        
        print(f"\nFound {len(result['tickets'])} tickets:")
        for t in result['tickets']:
            print(f"  {t['id']}: {t['name']}")
        
        if not result['tickets']:
            print("\n❌ No tickets found. HTML sample:")
            print(result['html_sample'])
            
            # Save full HTML
            html = await page.content()
            with open('march19_full_page.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("\nSaved full HTML to march19_full_page.html")
        else:
            # Test first ID
            first_ticket = result['tickets'][0]
            print(f"\nTesting first ID: {first_ticket['id']}")
            
            api_url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId={first_ticket['id']}&visitorNum=1&visitDate=19/03/2026"
            
            response = await page.request.get(api_url, headers={
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            print(f"API Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"Response keys: {data.keys()}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_fresh_ids_and_test())
