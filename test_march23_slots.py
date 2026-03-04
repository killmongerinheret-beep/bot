#!/usr/bin/env python3
"""
Test script to check what slots are available for March 23, 2026
and compare with what the bot is reporting.
"""

import asyncio
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Add worker_vatican to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def test_march23():
    print("\n" + "="*60)
    print("TESTING MARCH 23, 2026 AVAILABILITY")
    print("="*60)
    
    bot = HydraBot(use_proxies=True)
    
    try:
        async with bot.get_browser() as browser:
            page = await browser.new_page()
            
            # Test parameters for Task 26
            ticket_type = 0  # Standard ticket
            target_date = "23/03/2026"
            visitors = 1
            language = None
            
            print(f"\n📋 Test Parameters:")
            print(f"   Ticket Type: {ticket_type} (Standard)")
            print(f"   Date: {target_date}")
            print(f"   Visitors: {visitors}")
            print(f"   Language: {language}")
            
            # Step 1: Resolve dynamic IDs
            print(f"\n🔍 Step 1: Resolving dynamic ticket IDs...")
            resolved_ids = await bot.resolve_all_dynamic_ids(
                page, 
                ticket_type=ticket_type,
                target_date=target_date,
                visitors=visitors
            )
            
            print(f"   Found {len(resolved_ids)} tickets:")
            for item in resolved_ids:
                print(f"      - {item['id']}: {item['name']}")
            
            # Step 2: Match ticket by name
            print(f"\n🎯 Step 2: Matching ticket by name...")
            ticket_name = "Standard Entry (Full Price)"
            fresh_id = None
            
            # Try exact match
            for item in resolved_ids:
                r_name = item.get('name', '').lower()
                t_name = ticket_name.lower()
                if t_name in r_name or r_name in t_name:
                    fresh_id = item['id']
                    print(f"   ✅ Exact match: {item['name']}")
                    break
            
            if not fresh_id:
                # Try keyword match
                keywords = ['biglietti', 'ingresso', 'admission', 'entry', 'musei vaticani']
                best_score = 0
                for item in resolved_ids:
                    r_name = item.get('name', '').lower()
                    score = sum(1 for kw in keywords if kw in r_name)
                    if score > best_score and score >= 2:
                        best_score = score
                        fresh_id = item['id']
                        print(f"   ✅ Keyword match: {item['name']} (score: {score})")
            
            if not fresh_id:
                print("   ❌ No match found!")
                return
            
            # Step 3: Call API
            print(f"\n🌐 Step 3: Calling availability API...")
            print(f"   Ticket ID: {fresh_id}")
            
            # Get JSESSIONID from cookies
            cookies = await page.context.cookies()
            jsessionid = None
            for cookie in cookies:
                if cookie['name'] == 'JSESSIONID':
                    jsessionid = cookie['value']
                    break
            
            if not jsessionid:
                print("   ❌ No JSESSIONID found!")
                return
            
            # Build API URL
            visit_lang = ""  # Empty for standard tickets
            api_url = (
                f"https://tickets.museivaticani.va/api/visit/timeavail"
                f"?lang=it&visitLang={visit_lang}&visitTypeId={fresh_id}"
                f"&visitorNum={visitors}&visitDate={target_date}"
            )
            
            print(f"   URL: {api_url}")
            
            # Make API request
            response = await page.request.get(
                api_url,
                headers={
                    'Accept': 'application/json, text/plain, */*',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': 'https://tickets.museivaticani.va/',
                    'Cookie': f'JSESSIONID={jsessionid}'
                }
            )
            
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                timetable = data.get('timetable', [])
                
                print(f"\n📊 Results:")
                print(f"   Total slots: {len(timetable)}")
                
                available = []
                sold_out = []
                
                for slot in timetable:
                    time = slot.get('time')
                    avail = slot.get('availability')
                    
                    if avail == 'SOLD_OUT':
                        sold_out.append(time)
                    else:
                        available.append(time)
                
                print(f"   Available: {len(available)}")
                print(f"   Sold Out: {len(sold_out)}")
                
                if available:
                    print(f"\n✅ Available Times:")
                    for time in available:
                        print(f"      • {time}")
                
                if sold_out:
                    print(f"\n❌ Sold Out Times:")
                    for time in sold_out:
                        print(f"      • {time}")
                
                # Check if bot is reporting correctly
                print(f"\n🤖 Bot Verification:")
                print(f"   Bot reported: 8 available slots")
                print(f"   Actual available: {len(available)} slots")
                
                if len(available) == 8:
                    print(f"   ✅ Bot is CORRECT!")
                else:
                    print(f"   ⚠️  Mismatch detected!")
                    print(f"   Difference: {abs(len(available) - 8)} slots")
                
            else:
                print(f"   ❌ API Error: {response.status}")
                text = await response.text()
                print(f"   Response: {text[:200]}")
    
    finally:
        await bot.close()

if __name__ == '__main__':
    asyncio.run(test_march23())
