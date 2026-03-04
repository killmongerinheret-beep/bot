"""
Analyze Vatican ticket ID generation pattern
Goal: Reverse-engineer the ID generation algorithm
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json

async def collect_ticket_ids_multiple_dates():
    """Collect ticket IDs from multiple dates to find patterns"""
    
    rome = ZoneInfo("Europe/Rome")
    base_url = "https://tickets.museivaticani.va/home/fromtag"
    
    # Test multiple dates
    dates_to_test = []
    start_date = datetime.now(rome).replace(hour=0, minute=0, second=0, microsecond=0)
    
    for i in range(1, 30):  # Next 30 days
        test_date = start_date + timedelta(days=i)
        dates_to_test.append(test_date)
    
    results = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        for test_date in dates_to_test:
            date_str = test_date.strftime('%d/%m/%Y')
            timestamp_ms = int(test_date.timestamp() * 1000)
            
            # Test with 1 visitor, standard ticket
            url = f"{base_url}/1/{timestamp_ms}/MV-Biglietti/1"
            
            print(f"\n{'='*60}")
            print(f"Testing: {date_str}")
            print(f"URL: {url}")
            
            try:
                page = await context.new_page()
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(5000)
                
                # Extract all ticket IDs
                tickets = await page.evaluate("""
                    () => {
                        const results = [];
                        
                        // Method 1: From div containers
                        const containers = document.querySelectorAll('div[id^="ticket_"]');
                        containers.forEach(container => {
                            const id = container.id.replace('ticket_', '');
                            const titleEl = container.querySelector('.muvaTicketTitle');
                            const name = titleEl ? titleEl.innerText.trim() : 'Unknown';
                            results.push({id: id, name: name, source: 'container'});
                        });
                        
                        // Method 2: From buttons
                        const buttons = document.querySelectorAll('[data-cy^="bookTicket_"]');
                        buttons.forEach(btn => {
                            const id = btn.getAttribute('data-cy').replace('bookTicket_', '');
                            if (!results.find(r => r.id === id)) {
                                results.push({id: id, name: 'From button', source: 'button'});
                            }
                        });
                        
                        return results;
                    }
                """)
                
                if tickets:
                    results[date_str] = {
                        'timestamp_ms': timestamp_ms,
                        'tickets': tickets,
                        'count': len(tickets)
                    }
                    print(f"✅ Found {len(tickets)} tickets:")
                    for t in tickets:
                        print(f"   ID: {t['id']} - {t['name']}")
                else:
                    results[date_str] = {
                        'timestamp_ms': timestamp_ms,
                        'tickets': [],
                        'count': 0
                    }
                    print(f"❌ No tickets found")
                
                await page.close()
                
            except Exception as e:
                print(f"❌ Error: {e}")
                results[date_str] = {
                    'timestamp_ms': timestamp_ms,
                    'error': str(e)
                }
        
        await browser.close()
    
    # Save results
    with open('ticket_id_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Analyze patterns
    print(f"\n{'='*60}")
    print("PATTERN ANALYSIS")
    print(f"{'='*60}")
    
    all_ids = []
    for date_str, data in results.items():
        if 'tickets' in data:
            for ticket in data['tickets']:
                all_ids.append({
                    'date': date_str,
                    'id': ticket['id'],
                    'name': ticket['name'],
                    'timestamp': data['timestamp_ms']
                })
    
    if all_ids:
        print(f"\nTotal IDs collected: {len(all_ids)}")
        print(f"\nSample IDs:")
        for item in all_ids[:10]:
            print(f"  {item['date']}: {item['id']} ({item['name']})")
        
        # Check if IDs are consistent across dates
        print(f"\n{'='*60}")
        print("ID CONSISTENCY CHECK")
        print(f"{'='*60}")
        
        # Group by ticket name
        by_name = {}
        for item in all_ids:
            name = item['name']
            if name not in by_name:
                by_name[name] = []
            by_name[name].append(item['id'])
        
        for name, ids in by_name.items():
            unique_ids = set(ids)
            print(f"\n{name}:")
            print(f"  Total occurrences: {len(ids)}")
            print(f"  Unique IDs: {len(unique_ids)}")
            if len(unique_ids) == 1:
                print(f"  ✅ CONSISTENT ID: {list(unique_ids)[0]}")
            else:
                print(f"  ❌ VARIES: {unique_ids}")
    
    return results

if __name__ == "__main__":
    asyncio.run(collect_ticket_ids_multiple_dates())
