#!/usr/bin/env python3
"""
Debug script to extract the EXACT HTML structure the bot sees
and compare it with what the user sees
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def extract_full_html():
    """Extract the complete HTML and ticket structure"""
    print("\n" + "="*70)
    print("EXTRACTING FULL HTML STRUCTURE FOR MARCH 16")
    print("="*70)
    
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        # Navigate to the exact URL the user provided
        url = "https://tickets.museivaticani.va/home/fromtag/1/1773615600000/MV-Biglietti/1"
        print(f"\n🌐 Navigating to: {url}")
        
        await page.goto(url, timeout=60000, wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        # Wait for tickets to load
        try:
            await page.wait_for_selector("[data-cy^='bookTicket_']", state="visible", timeout=15000)
            print("✅ Ticket buttons found")
        except:
            print("⚠️  No ticket buttons found")
        
        # Extract ALL ticket information using multiple strategies
        ticket_data = await page.evaluate("""() => {
            const results = [];
            
            // Strategy 1: Find all elements with muvaTicketTitle class
            const titleElements = document.querySelectorAll('.muvaTicketTitle');
            console.log('Found', titleElements.length, 'muvaTicketTitle elements');
            
            titleElements.forEach((titleEl, index) => {
                const name = titleEl.textContent.trim();
                
                // Find associated button
                let container = titleEl.closest('div.card') || titleEl.closest('div.row') || titleEl.closest('app-ticket-card');
                let button = null;
                let id = null;
                
                if (container) {
                    button = container.querySelector('[data-cy^="bookTicket_"]');
                    if (button) {
                        const dataCy = button.getAttribute('data-cy');
                        id = dataCy ? dataCy.replace('bookTicket_', '') : null;
                    }
                }
                
                results.push({
                    strategy: 'muvaTicketTitle',
                    index: index,
                    name: name,
                    id: id,
                    hasButton: !!button,
                    containerType: container ? container.tagName : null
                });
            });
            
            // Strategy 2: Find all book buttons and work backwards
            const buttons = document.querySelectorAll('[data-cy^="bookTicket_"]');
            console.log('Found', buttons.length, 'bookTicket buttons');
            
            buttons.forEach((btn, index) => {
                const dataCy = btn.getAttribute('data-cy');
                const id = dataCy ? dataCy.replace('bookTicket_', '') : null;
                
                let container = btn.closest('div.card') || btn.closest('div.row') || btn.closest('app-ticket-card');
                let name = 'Unknown';
                
                if (container) {
                    const titleEl = container.querySelector('.muvaTicketTitle, h1, h2, h3, h4, .card-title');
                    if (titleEl) {
                        name = titleEl.textContent.trim();
                    }
                }
                
                // Check if this ID already exists in results
                const exists = results.some(r => r.id === id);
                if (!exists) {
                    results.push({
                        strategy: 'bookTicket_button',
                        index: index,
                        name: name,
                        id: id,
                        hasButton: true,
                        containerType: container ? container.tagName : null
                    });
                }
            });
            
            // Strategy 3: Look for the specific text the user mentioned
            const allDivs = document.querySelectorAll('div');
            let foundUserTicket = false;
            
            allDivs.forEach(div => {
                const text = div.textContent;
                if (text && text.includes('Musei Vaticani - Biglietti d')) {
                    foundUserTicket = true;
                    
                    // Try to find associated button
                    let button = div.querySelector('[data-cy^="bookTicket_"]');
                    if (!button) {
                        button = div.closest('div').querySelector('[data-cy^="bookTicket_"]');
                    }
                    
                    const id = button ? button.getAttribute('data-cy').replace('bookTicket_', '') : null;
                    
                    // Check if already in results
                    const exists = results.some(r => r.name.includes('Musei Vaticani - Biglietti d'));
                    if (!exists) {
                        results.push({
                            strategy: 'text_search',
                            name: 'Musei Vaticani - Biglietti d ingresso',
                            id: id,
                            hasButton: !!button,
                            foundInDiv: true
                        });
                    }
                }
            });
            
            return {
                tickets: results,
                foundUserTicket: foundUserTicket,
                totalTitleElements: titleElements.length,
                totalButtons: buttons.length
            };
        }""")
        
        # Display results
        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"   Total .muvaTicketTitle elements: {ticket_data['totalTitleElements']}")
        print(f"   Total bookTicket buttons: {ticket_data['totalButtons']}")
        print(f"   User's ticket found in HTML: {'✅ YES' if ticket_data['foundUserTicket'] else '❌ NO'}")
        print(f"   Total unique tickets extracted: {len(ticket_data['tickets'])}")
        
        print(f"\n🎫 DETAILED TICKET LIST:")
        for i, ticket in enumerate(ticket_data['tickets'], 1):
            print(f"\n   {i}. {ticket['name']}")
            print(f"      Strategy: {ticket['strategy']}")
            print(f"      ID: {ticket.get('id', 'N/A')}")
            print(f"      Has Button: {ticket.get('hasButton', False)}")
            if 'containerType' in ticket:
                print(f"      Container: {ticket['containerType']}")
        
        # Check if "Musei Vaticani - Biglietti d'ingresso" is in the list
        musei_found = any('Musei Vaticani' in t['name'] and 'Biglietti d\'ingresso' in t['name'] 
                         for t in ticket_data['tickets'])
        
        print(f"\n🎯 TARGET TICKET CHECK:")
        print(f"   'Musei Vaticani - Biglietti d'ingresso' found: {'✅ YES' if musei_found else '❌ NO'}")
        
        if not musei_found:
            print(f"\n⚠️  THE TICKET IS NOT IN THE EXTRACTED LIST!")
            print(f"   This means the bot's JavaScript extraction is missing it.")
            print(f"   Possible reasons:")
            print(f"   1. The ticket is in a different HTML structure")
            print(f"   2. The ticket is loaded dynamically after our wait")
            print(f"   3. The ticket is hidden/grouped in a different way")
            print(f"   4. The ticket requires interaction to appear")
        
        # Save full HTML for inspection
        html_content = await page.content()
        with open('march16_full_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n💾 Full HTML saved to: march16_full_page.html")
        
        # Take screenshot
        await page.screenshot(path='march16_screenshot.png', full_page=True)
        print(f"📸 Screenshot saved to: march16_screenshot.png")
        
        # Search for the specific text in HTML
        if 'Musei Vaticani - Biglietti d\'ingresso' in html_content:
            print(f"\n✅ The text 'Musei Vaticani - Biglietti d'ingresso' EXISTS in the HTML!")
            print(f"   But the bot's JavaScript extraction is not finding it.")
            print(f"   This suggests a DOM structure issue.")
        else:
            print(f"\n❌ The text 'Musei Vaticani - Biglietti d'ingresso' is NOT in the HTML!")
            print(f"   The Vatican website is not showing this ticket on March 16.")
        
        await page.close()

if __name__ == '__main__':
    asyncio.run(extract_full_html())
