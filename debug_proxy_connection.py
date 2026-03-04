"""
Debug proxy connectivity
Test both Oxylabs and Webshare proxies
"""
import asyncio
import os
import json
from playwright.async_api import async_playwright

async def test_proxy_connection(proxy_str, proxy_type):
    """Test if proxy can connect to Vatican"""
    print(f"\n{'='*70}")
    print(f"Testing {proxy_type}: {proxy_str.split(':')[0]}:***")
    print(f"{'='*70}")
    
    # Parse proxy
    parts = proxy_str.split(':')
    proxy_config = None
    
    if len(parts) == 4:  # Webshare: ip:port:user:pass
        proxy_config = {
            "server": f"http://{parts[0]}:{parts[1]}",
            "username": parts[2],
            "password": parts[3]
        }
        print(f"Format: Webshare (ip:port:user:pass)")
    elif len(parts) == 2:  # Oxylabs: entrypoint:port
        username = os.getenv('OXYLABS_USERNAME', 'abiilesh_2uVXW')
        password = os.getenv('OXYLABS_PASSWORD', 'Abiilesh@2005')
        proxy_config = {
            "server": f"http://{proxy_str}",
            "username": username,
            "password": password
        }
        print(f"Format: Oxylabs (entrypoint:port)")
        print(f"Username: {username}")
    
    if not proxy_config:
        print("❌ Invalid proxy format")
        return False
    
    print(f"Proxy server: {proxy_config['server']}")
    
    try:
        async with async_playwright() as p:
            # Test 1: Can we launch browser with proxy?
            print("\n1. Launching browser with proxy...")
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            print("✅ Browser launched")
            
            context = await browser.new_context()
            page = await context.new_page()
            
            # Test 2: Can we reach a simple site?
            print("\n2. Testing basic connectivity (httpbin.org)...")
            try:
                await page.goto("https://httpbin.org/ip", timeout=10000)
                ip_info = await page.content()
                print(f"✅ Connected! IP response: {ip_info[:100]}")
            except Exception as e:
                print(f"❌ Failed to reach httpbin: {e}")
                await browser.close()
                return False
            
            # Test 3: Can we reach Vatican?
            print("\n3. Testing Vatican connectivity...")
            try:
                await page.goto("https://tickets.museivaticani.va/", timeout=15000)
                print("✅ Reached Vatican homepage")
            except Exception as e:
                print(f"❌ Failed to reach Vatican: {e}")
                await browser.close()
                return False
            
            # Test 4: Can we reach Vatican deep link?
            print("\n4. Testing Vatican deep link...")
            try:
                await page.goto(
                    "https://tickets.museivaticani.va/home/fromtag/1/1773874800000/MV-Biglietti/1",
                    timeout=30000,
                    wait_until='domcontentloaded'
                )
                print("✅ Reached Vatican deep link")
                
                # Check if we got cookies
                cookies = await context.cookies()
                jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
                if jsessionid:
                    print(f"✅ Got JSESSIONID: {jsessionid[:30]}...")
                else:
                    print("⚠️  No JSESSIONID cookie")
                
            except Exception as e:
                print(f"❌ Failed to reach deep link: {e}")
                await browser.close()
                return False
            
            await browser.close()
            print(f"\n✅ {proxy_type} proxy WORKS!")
            return True
            
    except Exception as e:
        print(f"\n❌ {proxy_type} proxy FAILED: {e}")
        return False

async def main():
    print("="*70)
    print("PROXY CONNECTIVITY DEBUG")
    print("="*70)
    
    # Load Oxylabs proxies
    oxylabs_proxies = []
    if os.path.exists("Proxy lists.json"):
        with open("Proxy lists.json", 'r') as f:
            data = json.load(f)
            for p in data:
                oxylabs_proxies.append(f"{p['entryPoint']}:{p['port']}")
        print(f"✅ Loaded {len(oxylabs_proxies)} Oxylabs proxies")
    
    # Load Webshare proxies
    webshare_proxies = []
    if os.path.exists("Webshare_10_proxies.txt"):
        with open("Webshare_10_proxies.txt", 'r') as f:
            for line in f:
                if line.strip() and ":" in line:
                    webshare_proxies.append(line.strip())
        print(f"✅ Loaded {len(webshare_proxies)} Webshare proxies")
    
    results = {
        "oxylabs": [],
        "webshare": []
    }
    
    # Test Oxylabs (first 2)
    if oxylabs_proxies:
        print(f"\n{'#'*70}")
        print("TESTING OXYLABS PROXIES")
        print(f"{'#'*70}")
        
        for i, proxy in enumerate(oxylabs_proxies[:2], 1):
            print(f"\n--- Oxylabs Test {i}/2 ---")
            success = await test_proxy_connection(proxy, "Oxylabs")
            results["oxylabs"].append({"proxy": proxy.split(':')[0], "success": success})
            if i < 2:
                await asyncio.sleep(2)
    
    # Test Webshare (first 2)
    if webshare_proxies:
        print(f"\n{'#'*70}")
        print("TESTING WEBSHARE PROXIES")
        print(f"{'#'*70}")
        
        for i, proxy in enumerate(webshare_proxies[:2], 1):
            print(f"\n--- Webshare Test {i}/2 ---")
            success = await test_proxy_connection(proxy, "Webshare")
            results["webshare"].append({"proxy": proxy.split(':')[0], "success": success})
            if i < 2:
                await asyncio.sleep(2)
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    oxylabs_working = sum(1 for r in results["oxylabs"] if r["success"])
    webshare_working = sum(1 for r in results["webshare"] if r["success"])
    
    print(f"\nOxylabs: {oxylabs_working}/{len(results['oxylabs'])} working")
    for r in results["oxylabs"]:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {r['proxy']}")
    
    print(f"\nWebshare: {webshare_working}/{len(results['webshare'])} working")
    for r in results["webshare"]:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {r['proxy']}")
    
    print(f"\n{'='*70}")
    print("RECOMMENDATION")
    print(f"{'='*70}")
    
    if webshare_working > 0:
        print("✅ Use Webshare proxies - they work with Vatican!")
    elif oxylabs_working > 0:
        print("✅ Use Oxylabs proxies - they work with Vatican!")
    else:
        print("⚠️  No proxies working - Vatican may be blocking them")
        print("   Consider: No proxy, or try residential proxies")

if __name__ == "__main__":
    asyncio.run(main())
