"""
Get your current public IP address
This is the IP you need to whitelist in Oxylabs dashboard
"""
import asyncio
from playwright.async_api import async_playwright
import requests

async def get_ip_playwright():
    """Get IP using Playwright"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto("https://api.ipify.org?format=json", timeout=10000)
            content = await page.content()
            
            await browser.close()
            
            # Extract IP from JSON
            import json
            data = json.loads(await page.evaluate("() => document.body.innerText"))
            return data.get('ip')
    except Exception as e:
        print(f"Playwright method failed: {e}")
        return None

def get_ip_requests():
    """Get IP using requests library"""
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        return response.json().get('ip')
    except Exception as e:
        print(f"Requests method failed: {e}")
        return None

async def main():
    print("="*70)
    print("GETTING YOUR PUBLIC IP ADDRESS")
    print("="*70)
    print("\nThis is the IP you need to whitelist in Oxylabs dashboard\n")
    
    # Try requests first (faster)
    print("Method 1: Using requests library...")
    ip1 = get_ip_requests()
    if ip1:
        print(f"✅ Your IP: {ip1}")
    else:
        print("❌ Failed")
    
    # Try playwright as backup
    print("\nMethod 2: Using Playwright...")
    ip2 = await get_ip_playwright()
    if ip2:
        print(f"✅ Your IP: {ip2}")
    else:
        print("❌ Failed")
    
    # Final result
    final_ip = ip1 or ip2
    
    if final_ip:
        print("\n" + "="*70)
        print("YOUR PUBLIC IP ADDRESS")
        print("="*70)
        print(f"\n  {final_ip}\n")
        print("="*70)
        print("\nSTEPS TO WHITELIST IN OXYLABS:")
        print("="*70)
        print("1. Go to: https://dashboard.oxylabs.io/")
        print("2. Login with your account")
        print("3. Navigate to: Proxies → ISP Proxies")
        print("4. Find 'IP Whitelist' or 'Access Control' section")
        print(f"5. Add this IP: {final_ip}")
        print("6. Save changes")
        print("7. Wait 1-2 minutes for changes to propagate")
        print("8. Test again with: python test_oxylabs_direct_vatican.py")
        print("="*70)
        
        # Also check if running in Docker
        print("\n⚠️  IMPORTANT:")
        print("If you're running the bot in Docker, you need to whitelist")
        print("the Docker host's IP, not the container IP!")
        print("\nTo get Docker host IP:")
        print("  docker-compose exec backend curl -s https://api.ipify.org")
        
    else:
        print("\n❌ Could not determine your IP address")
        print("Try manually visiting: https://api.ipify.org")

if __name__ == "__main__":
    asyncio.run(main())
