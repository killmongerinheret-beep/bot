#!/usr/bin/env python3
"""
Debug script to see ALL tickets available for March 23, 2026
and understand which one should be matched.
"""

import asyncio
import sys
import os

# Add worker_vatican to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def debug_march23():
    print("\n" + "="*60)
    print("DEBUG: ALL TICKETS FOR MARCH 23, 2026")
    print("="*60)
    
    bot = HydraBot(use_proxies=True)
    
    try:
        async with bot.get_browser() as browser:
            page = await browser.new_page()
            
            # Test parameters
            ticket_type = 0  # Standard ticket
            target_date = "23/03/2026"
            visitors = 1
            
            print(f"\n📋 Parameters:")
            print(f"   Date: {target_date}")
            print(f"   Visitors: {visitors}")
            print(f"   Ticket Type: {ticket_type} (Standard)")
            
            # Resolve all dynamic IDs
            print(f"\n🔍 Resolving ALL tickets...")
            resolved_ids = await bot.resolve_all_dynamic_ids(
                page, 
                ticket_type=ticket_type,
                target_date=target_date,
                visitors=visitors
            )
            
            print(f"\n📊 Found {len(resolved_ids)} tickets:\n")
            
            # Analyze each ticket
            for i, item in enumerate(resolved_ids, 1):
                ticket_id = item['id']
                ticket_name = item['name']
                name_lower = ticket_name.lower()
                
                # Categorize
                is_standard = any(kw in name_lower for kw in ['biglietti', 'ingresso', 'admission', 'entry'])
                is_guided = any(kw in name_lower for kw in ['visita', 'guidata', 'guided', 'tour'])
                is_special = any(kw in name_lower for kw in ['lunch', 'pranzo', 'pellegrinaggi', 'gruppi', 'cupole', 'terrazze'])
                
                category = "❓ Unknown"
                if is_special:
                    category = "🎪 Special"
                elif is_guided:
                    category = "👥 Guided Tour"
                elif is_standard:
                    category = "🎫 Standard"
                
                print(f"{i}. {category}")
                print(f"   ID: {ticket_id}")
                print(f"   Name: {ticket_name}")
                
                # Check keywords
                keywords_found = []
                if 'musei' in name_lower or 'museum' in name_lower:
                    keywords_found.append('musei/museum')
                if 'palazzo' in name_lower:
                    keywords_found.append('palazzo')
                if 'specola' in name_lower:
                    keywords_found.append('specola')
                if 'biglietti' in name_lower:
                    keywords_found.append('biglietti')
                if 'ingresso' in name_lower:
                    keywords_found.append('ingresso')
                if 'admission' in name_lower or 'entry' in name_lower:
                    keywords_found.append('admission/entry')
                
                if keywords_found:
                    print(f"   Keywords: {', '.join(keywords_found)}")
                print()
            
            # Now test matching logic
            print("="*60)
            print("TESTING MATCHING LOGIC")
            print("="*60)
            
            ticket_name_to_match = "Standard Entry (Full Price)"
            print(f"\n🎯 Trying to match: '{ticket_name_to_match}'")
            
            # Strategy 1: Exact match
            print(f"\n📍 Strategy 1: Exact substring match")
            exact_match = None
            for item in resolved_ids:
                r_name = item.get('name', '').lower()
                t_name = ticket_name_to_match.lower()
                
                if t_name in r_name or r_name in t_name:
                    if "lunch" not in r_name:
                        exact_match = item
                        print(f"   ✅ Match found: {item['name']}")
                        break
            
            if not exact_match:
                print(f"   ❌ No exact match")
            
            # Strategy 2: Keyword match
            print(f"\n📍 Strategy 2: Keyword matching")
            keywords = ['musei', 'biglietti', 'ingresso', 'admission', 'entry', 'musei vaticani']
            
            best_match = None
            best_score = 0
            
            for item in resolved_ids:
                r_name = item.get('name', '').lower()
                score = sum(1 for kw in keywords if kw in r_name)
                
                # Avoid special tickets
                if any(x in r_name for x in ['lunch', 'pranzo', 'pellegrinaggi', 'gruppi', 'cupole', 'terrazze']):
                    continue
                
                if score > 0:
                    print(f"   Score {score}: {item['name']}")
                
                if score > best_score:
                    best_score = score
                    best_match = item
            
            if best_match and best_score >= 2:
                print(f"   ✅ Best match (score {best_score}): {best_match['name']}")
            else:
                print(f"   ❌ No good keyword match (best score: {best_score})")
            
            # Strategy 3: Fallback
            print(f"\n📍 Strategy 3: Fallback to first standard ticket")
            fallback_match = None
            for item in resolved_ids:
                r_name = item.get('name', '').lower()
                if 'biglietti' in r_name or 'ingresso' in r_name:
                    if not any(x in r_name for x in ['lunch', 'pranzo', 'pellegrinaggi', 'gruppi']):
                        fallback_match = item
                        print(f"   ✅ Fallback: {item['name']}")
                        break
            
            if not fallback_match:
                print(f"   ❌ No fallback found")
            
            # Final recommendation
            print(f"\n" + "="*60)
            print("RECOMMENDATION")
            print("="*60)
            
            final_match = exact_match or best_match or fallback_match
            
            if final_match:
                print(f"\n✅ Bot will use:")
                print(f"   ID: {final_match['id']}")
                print(f"   Name: {final_match['name']}")
                
                # Check if this is the right ticket
                if 'palazzo papale' in final_match['name'].lower():
                    print(f"\n⚠️  WARNING: This is 'Palazzo Papale', not 'Musei Vaticani'!")
                    print(f"   Palazzo Papale = Castel Gandolfo (Pope's summer residence)")
                    print(f"   Musei Vaticani = Vatican Museums (main attraction)")
                    print(f"\n   The bot is matching the WRONG ticket!")
                elif 'musei vaticani' in final_match['name'].lower():
                    print(f"\n✅ CORRECT: This is the Vatican Museums ticket")
                else:
                    print(f"\n❓ UNCLEAR: Check if this is the right ticket")
            else:
                print(f"\n❌ No match found!")
    
    finally:
        pass  # Browser context will close automatically

if __name__ == '__main__':
    asyncio.run(debug_march23())
