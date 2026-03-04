#!/usr/bin/env python3
"""
Compare what we see WITH proxies vs WITHOUT proxies
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker_vatican'))

from hydra_monitor import HydraBot

async def test_with_proxies():
    """Test WITH proxies (like the bot does)"""
    print("\n" + "="*60)
    print("TEST 1: WITH PROXIES (Bot's method)")
    print("="*60)
    
    bot = HydraBot(use_proxies=True)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        resolved_ids = await bot.resolve_all_dynamic_ids(
            page, 
            ticket_type=0,
            target_date="16/03/2026",
            visitors=1
        )
        
        print(f"\n🎫 Found {len(resolved_ids)} tickets:")
        for item in resolved_ids:
            marker = "✅" if "musei vaticani" in item['name'].lower() and "biglietti" in item['name'].lower() else "📍"
            print(f"   {marker} {item['name']}")
        
        has_main = any("musei vaticani" in t['name'].lower() and "biglietti d'ingresso" in t['name'].lower() for t in resolved_ids)
        
        await page.close()
        
        return has_main, resolved_ids

async def test_without_proxies():
    """Test WITHOUT proxies"""
    print("\n" + "="*60)
    print("TEST 2: WITHOUT PROXIES (Direct connection)")
    print("="*60)
    
    bot = HydraBot(use_proxies=False)
    
    async with bot.get_browser() as browser:
        page = await browser.new_page()
        
        resolved_ids = await bot.resolve_all_dynamic_ids(
            page, 
            ticket_type=0,
            target_date="16/03/2026",
            visitors=1
        )
        
        print(f"\n🎫 Found {len(resolved_ids)} tickets:")
        for item in resolved_ids:
            marker = "✅" if "musei vaticani" in item['name'].lower() and "biglietti" in item['name'].lower() else "📍"
            print(f"   {marker} {item['name']}")
        
        has_main = any("musei vaticani" in t['name'].lower() and "biglietti d'ingresso" in t['name'].lower() for t in resolved_ids)
        
        await page.close()
        
        return has_main, resolved_ids

async def main():
    print("\n" + "="*70)
    print("PROXY COMPARISON TEST - MARCH 16, 2026")
    print("="*70)
    
    # Test with proxies
    with_proxy_has_main, with_proxy_tickets = await test_with_proxies()
    
    # Test without proxies
    without_proxy_has_main, without_proxy_tickets = await test_without_proxies()
    
    # Compare
    print("\n" + "="*70)
    print("COMPARISON RESULTS")
    print("="*70)
    
    print(f"\nWITH PROXIES:")
    print(f"   Main ticket found: {'✅ YES' if with_proxy_has_main else '❌ NO'}")
    print(f"   Total tickets: {len(with_proxy_tickets)}")
    
    print(f"\nWITHOUT PROXIES:")
    print(f"   Main ticket found: {'✅ YES' if without_proxy_has_main else '❌ NO'}")
    print(f"   Total tickets: {len(without_proxy_tickets)}")
    
    if with_proxy_has_main != without_proxy_has_main:
        print(f"\n⚠️  PROXY ISSUE DETECTED!")
        print(f"   Proxies are causing the bot to see different content!")
        print(f"   Solution: Disable proxies or use different proxy provider")
    else:
        print(f"\n✅ Both methods show the same results")
        print(f"   Proxy is not the issue")

if __name__ == '__main__':
    asyncio.run(main())
