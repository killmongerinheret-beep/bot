#!/usr/bin/env python3
"""
Fix the ticket extraction logic in hydra_monitor.py
to properly handle the Vatican website's DOM structure
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def test_new_extraction():
    """Test the improved extraction logic"""
    print("\n" + "="*70)
    print("TESTING IMPROVED TICKET EXTRACTION")
    print("="*70)
    
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        # Navigate to March 16
        url = "https://tickets.museivaticani.va/home/fromtag/1/1773615600000/MV-Biglietti/1"
        print(f"\n🌐 Navigating to: {url}")
        
        await page.goto(url, timeout=60000, wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        # Wait for tickets
        try:
            await page.wait_for_selector("[data-cy^='bookTicket_']", state="visible", timeout=15000)
            print("✅ Ticket buttons found")
        except:
            print("⚠️  No ticket buttons found")
        
        # NEW IMPROVED EXTRACTION LOGIC
        # This handles the case where titles and buttons are in separate DOM structures
        tickets = await page.evaluate("""() => {
            const results = [];
            
            // Step 1: Get all ticket titles
            const titles = [];
            document.querySelectorAll('.muvaTicketTitle').forEach(el => {
                titles.push({
                    text: el.textContent.trim(),
                    element: el
                });
            });
            
            // Step 2: Get all buttons with IDs
            const buttons = [];
            document.querySelectorAll('[data-cy^="bookTicket_"]').forEach(btn => {
                const dataCy = btn.getAttribute('data-cy');
                const id = dataCy ? dataCy.replace('bookTicket_', '') : null;
                buttons.push({
                    id: id,
                    element: btn
                });
            });
            
            console.log('Found', titles.length, 'titles and', buttons.length, 'buttons');
            
            // Step 3: Try to match titles with buttons
            // Strategy A: Look for buttons within the same parent container
            titles.forEach(titleInfo => {
                const titleEl = titleInfo.element;
                let matchedButton = null;
                
                // Try to find button in same container
                let container = titleEl.closest('app-ticket-card') || 
                               titleEl.closest('.card') || 
                               titleEl.closest('.ticket-container') ||
                               titleEl.closest('[class*="ticket"]') ||
                               titleEl.closest('div[class*="muva"]');
                
                if (container) {
                    const btn = container.querySelector('[data-cy^="bookTicket_"]');
                    if (btn) {
                        const dataCy = btn.getAttribute('data-cy');
                        matchedButton = dataCy ? dataCy.replace('bookTicket_', '') : null;
                    }
                }
                
                results.push({
                    name: titleInfo.text,
                    id: matchedButton,
                    matched: !!matchedButton,
                    strategy: 'container_search'
                });
            });
            
            // Step 4: For unmatched buttons, try to find nearby text
            buttons.forEach(btnInfo => {
                // Check if this button ID is already matched
                const alreadyMatched = results.some(r => r.id === btnInfo.id);
                if (alreadyMatched) return;
                
                const btn = btnInfo.element;
                let name = 'Unknown';
                
                // Look for text in parent containers
                let parent = btn.parentElement;
                for (let i = 0; i < 10 && parent; i++) {
                    // Look for any title-like element
                    const titleEl = parent.querySelector('.muvaTicketTitle, h1, h2, h3, h4, [class*="title"], [class*="Title"]');
                    if (titleEl && titleEl.textContent.trim()) {
                        name = titleEl.textContent.trim();
                        break;
                    }
                    parent = parent.parentElement;
                }
                
                results.push({
                    name: name,
                    id: btnInfo.id,
                    matched: name !== 'Unknown',
                    strategy: 'button_search'
                });
            });
            
            return results;
        }""")
        
        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"   Total tickets extracted: {len(tickets)}")
        
        matched = [t for t in tickets if t['matched']]
        unmatched = [t for t in tickets if not t['matched']]
        
        print(f"   Matched (with ID): {len(matched)}")
        print(f"   Unmatched (no ID): {len(unmatched)}")
        
        print(f"\n🎫 MATCHED TICKETS (with booking IDs):")
        for i, ticket in enumerate(matched, 1):
            marker = "✅" if "musei vaticani" in ticket['name'].lower() and "biglietti" in ticket['name'].lower() else "📍"
            print(f"   {marker} {ticket['name']}")
            print(f"      ID: {ticket['id']}")
            print(f"      Strategy: {ticket['strategy']}")
        
        if unmatched:
            print(f"\n⚠️  UNMATCHED TICKETS (titles without booking buttons):")
            for ticket in unmatched:
                print(f"   • {ticket['name']}")
        
        # Check if we found the main ticket
        main_ticket = next((t for t in matched if "musei vaticani" in t['name'].lower() and "biglietti d'ingresso" in t['name'].lower()), None)
        
        print(f"\n🎯 MAIN TICKET CHECK:")
        if main_ticket:
            print(f"   ✅ 'Musei Vaticani - Biglietti d'ingresso' FOUND!")
            print(f"   ID: {main_ticket['id']}")
            print(f"   Strategy: {main_ticket['strategy']}")
        else:
            print(f"   ❌ 'Musei Vaticani - Biglietti d'ingresso' NOT FOUND")
            print(f"   This ticket exists in HTML but has no booking button!")
            print(f"   This means it's NOT actually bookable on this date.")
        
        await page.close()

if __name__ == '__main__':
    asyncio.run(test_new_extraction())
