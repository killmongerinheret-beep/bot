#!/usr/bin/env python3
"""
Final debug - Check EXACTLY what's on the Monday page after 15 seconds
"""
import asyncio
import time
from playwright.async_api import async_playwright

async def final_debug():
    print("=" * 80)
    print("FINAL MONDAY DEBUG - WHAT'S ACTUALLY ON THE PAGE?")
    print("=" * 80)
    
    url = "https://tickets.museivaticani.va/home/fromtag/1/1774220400000/MV-Biglietti/1"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    
    try:
        print(f"\n🌐 URL: {url}")
        print(f"⏱️ Loading...")
        
        await page.goto(url, timeout=60000, wait_until="networkidle")
        print(f"✅ Page loaded")
        
        # Wait 15 seconds (same as bot)
        await page.wait_for_timeout(15000)
        print(f"⏱️ Waited 15 seconds")
        
        # Get ALL div[id^="ticket_"] and their content
        result = await page.evaluate('''() => {
            const containers = document.querySelectorAll('div[id^="ticket_"]');
            const tickets = [];
            
            containers.forEach(container => {
                const id = container.getAttribute('id').replace('ticket_', '');
                
                // Try ALL possible title selectors
                const selectors = [
                    '.muvaTicketTitle',
                    'h1', 'h2', 'h3', 'h4',
                    '.card-title',
                    'span[class*="title"]',
                    'span[class*="Title"]',
                    'app-ticket-details .muvaTicketTitle',
                    'app-ticket-details h1',
                    'app-ticket-details h2',
                    'app-ticket-details span'
                ];
                
                let title = null;
                let foundBy = null;
                
                for (const sel of selectors) {
                    const el = container.querySelector(sel);
                    if (el && el.textContent.trim().length > 5) {
                        title = el.textContent.trim();
                        foundBy = sel;
                        break;
                    }
                }
                
                // If still no title, get ALL text from container
                const allText = container.textContent.trim();
                
                tickets.push({
                    id: id,
                    title: title,
                    foundBy: foundBy,
                    hasMusei: allText.toLowerCase().includes('musei'),
                    hasVaticani: allText.toLowerCase().includes('vaticani'),
                    hasBiglietti: allText.toLowerCase().includes('biglietti'),
                    allText: allText.substring(0, 200)
                });
            });
            
            return tickets;
        }''')
        
        print(f"\n📊 Found {len(result)} ticket containers:")
        print(f"=" * 80)
        
        for i, ticket in enumerate(result, 1):
            print(f"\n{i}. ID: {ticket['id']}")
            print(f"   Title: {ticket['title'] if ticket['title'] else 'NOT FOUND'}")
            if ticket['foundBy']:
                print(f"   Found by: {ticket['foundBy']}")
            print(f"   Has 'musei': {ticket['hasMusei']}")
            print(f"   Has 'vaticani': {ticket['hasVaticani']}")
            print(f"   Has 'biglietti': {ticket['hasBiglietti']}")
            if not ticket['title'] and (ticket['hasMusei'] or ticket['hasVaticani']):
                print(f"   ⚠️ CONTAINS KEYWORDS BUT NO TITLE EXTRACTED!")
                print(f"   All text: {ticket['allText'][:150]}...")
        
        # Check if Musei Vaticani exists
        musei_found = any(
            t['title'] and 'musei' in t['title'].lower() and 'vaticani' in t['title'].lower() and 'biglietti' in t['title'].lower()
            for t in result
        )
        
        print(f"\n" + "=" * 80)
        if musei_found:
            print(f"✅ 'Musei Vaticani - Biglietti d'ingresso' FOUND in titles")
        else:
            print(f"❌ 'Musei Vaticani - Biglietti d'ingresso' NOT FOUND in titles")
            
            # But check if it's in the text
            has_keywords = any(
                t['hasMusei'] and t['hasVaticani'] and t['hasBiglietti']
                for t in result
            )
            if has_keywords:
                print(f"⚠️ BUT keywords exist in container text - title extraction failing!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(final_debug())
