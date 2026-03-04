"""
Test if JSESSIONID is tied to specific dates/IDs
Can we mix and match cookies from different dates?
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def get_cookie_from_date(date_str, timestamp_ms):
    """Get JSESSIONID from a specific date"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        url = f"https://tickets.museivaticani.va/home/fromtag/1/{timestamp_ms}/MV-Biglietti/1"
        await page.goto(url, wait_until='commit', timeout=10000)
        await page.wait_for_timeout(1000)
        
        cookies = await context.cookies()
        jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
        
        await browser.close()
        return jsessionid

async def test_api_with_cookie(jsessionid, ticket_id, test_date, cookie_source):
    """Test API with specific cookie and ID combination"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Set the cookie
        await context.add_cookies([{
            'name': 'JSESSIONID',
            'value': jsessionid,
            'domain': '.museivaticani.va',
            'path': '/'
        }])
        
        page = await context.new_page()
        
        api_url = (
            f"https://tickets.museivaticani.va/api/visit/timeavail"
            f"?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum=1&visitDate={test_date}"
        )
        
        try:
            response = await page.request.get(api_url, headers={
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://tickets.museivaticani.va/'
            })
            
            status = response.status
            
            if status == 200:
                data = await response.json()
                if 'timetable' in data:
                    available = [t for t in data['timetable'] if t.get('availability') != 'SOLD_OUT']
                    return f"✅ 200 OK - {len(available)} slots"
                else:
                    return f"⚠️  200 OK - No timetable"
            elif status == 500:
                return "❌ 500 Error"
            else:
                return f"❌ Status {status}"
                
        except Exception as e:
            return f"❌ Exception: {str(e)[:50]}"
        finally:
            await browser.close()

async def main():
    print("="*70)
    print("TESTING: Cookie-ID Independence")
    print("="*70)
    print("Question: Can we use ANY cookie with ANY ticket ID?")
    print()
    
    # Get cookies from different dates
    print("Step 1: Getting cookies from different dates...")
    cookie_march16 = await get_cookie_from_date("16/03/2026", 1773615600000)
    cookie_march19 = await get_cookie_from_date("19/03/2026", 1773874800000)
    cookie_march20 = await get_cookie_from_date("20/03/2026", 1773961200000)
    
    print(f"  March 16 cookie: {cookie_march16[:30]}...")
    print(f"  March 19 cookie: {cookie_march19[:30]}...")
    print(f"  March 20 cookie: {cookie_march20[:30]}...")
    
    # Fresh ID from March 19
    FRESH_ID = "161755641"  # Ingresso AREE MUSEALI Singoli
    
    print("\n" + "="*70)
    print("Step 2: Testing March 19 (has tickets) with different cookies")
    print("="*70)
    print(f"Using ID: {FRESH_ID} (from March 19)")
    print(f"Testing date: 19/03/2026")
    print()
    
    # Test March 19 with its own cookie
    result1 = await test_api_with_cookie(cookie_march19, FRESH_ID, "19/03/2026", "March 19")
    print(f"  Cookie from March 19 → {result1}")
    
    # Test March 19 with March 16 cookie
    result2 = await test_api_with_cookie(cookie_march16, FRESH_ID, "19/03/2026", "March 16")
    print(f"  Cookie from March 16 → {result2}")
    
    # Test March 19 with March 20 cookie
    result3 = await test_api_with_cookie(cookie_march20, FRESH_ID, "19/03/2026", "March 20")
    print(f"  Cookie from March 20 → {result3}")
    
    print("\n" + "="*70)
    print("Step 3: Testing March 16 (no tickets) with different cookies")
    print("="*70)
    print(f"Using ID: {FRESH_ID} (from March 19)")
    print(f"Testing date: 16/03/2026")
    print()
    
    # Test March 16 with its own cookie
    result4 = await test_api_with_cookie(cookie_march16, FRESH_ID, "16/03/2026", "March 16")
    print(f"  Cookie from March 16 → {result4}")
    
    # Test March 16 with March 19 cookie
    result5 = await test_api_with_cookie(cookie_march19, FRESH_ID, "16/03/2026", "March 19")
    print(f"  Cookie from March 19 → {result5}")
    
    # Test March 16 with March 20 cookie
    result6 = await test_api_with_cookie(cookie_march20, FRESH_ID, "16/03/2026", "March 20")
    print(f"  Cookie from March 20 → {result6}")
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    
    if "200 OK" in result1 and "200 OK" in result2 and "200 OK" in result3:
        print("✅ Cookies are INDEPENDENT of dates!")
        print("   → Can use ANY cookie with ANY date")
        print("   → Just need ONE valid JSESSIONID")
        print("   → Can cache a single cookie for all checks")
    else:
        print("❌ Cookies are DATE-SPECIFIC")
        print("   → Must get cookie from target date's deep link")
        print("   → Cannot reuse cookies across dates")
    
    if "500" in result4 and "500" in result5 and "500" in result6:
        print("\n✅ March 16 returns 500 with ALL cookies")
        print("   → Confirms March 16 tickets NOT RELEASED")
        print("   → Not a cookie issue, it's a date availability issue")

if __name__ == "__main__":
    asyncio.run(main())
