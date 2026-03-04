#!/usr/bin/env python3
"""
Test Vatican API visitLang Parameter
=====================================
Tests whether standard tickets need visitLang= with empty value or not.
"""

import requests
import json

def test_api_call(url, description):
    """Test an API call and show results"""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    print(f"URL: {url}")
    
    try:
        # Note: This will fail without valid JSESSIONID, but we can see the response
        response = requests.get(url, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ SUCCESS - Got JSON response:")
                print(json.dumps(data, indent=2)[:500])
                
                if 'timetable' in data:
                    print(f"\n✅ Has timetable with {len(data['timetable'])} slots")
                    return True
            except:
                print(f"\n⚠️ Response is not JSON:")
                print(response.text[:500])
        else:
            print(f"\n❌ FAILED - Status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    
    return False

def main():
    print("=" * 80)
    print("VATICAN API visitLang PARAMETER TEST")
    print("=" * 80)
    print("\nTesting standard ticket API calls with different visitLang formats...")
    
    # Test parameters
    ticket_id = "2085325042"  # Your example ID
    visitors = "1"
    date = "28/03/2026"
    
    # Test 1: WITHOUT visitLang parameter
    url1 = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={date}"
    result1 = test_api_call(url1, "Standard Ticket WITHOUT visitLang parameter")
    
    # Test 2: WITH visitLang= (empty value)
    url2 = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={date}"
    result2 = test_api_call(url2, "Standard Ticket WITH visitLang= (empty)")
    
    # Test 3: WITH visitLang=ITA (with value)
    url3 = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=ITA&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={date}"
    result3 = test_api_call(url3, "Standard Ticket WITH visitLang=ITA (value)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Test 1 (No visitLang):     {'✅ WORKS' if result1 else '❌ FAILS'}")
    print(f"Test 2 (visitLang=):       {'✅ WORKS' if result2 else '❌ FAILS'}")
    print(f"Test 3 (visitLang=ITA):    {'✅ WORKS' if result3 else '❌ FAILS'}")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    if result2 and not result1:
        print("✅ Standard tickets REQUIRE visitLang= with empty value")
        print("   Correct format: ...&visitLang=&visitTypeId=...")
    elif result1 and not result2:
        print("✅ Standard tickets should NOT have visitLang parameter")
        print("   Correct format: ...&visitTypeId=... (no visitLang)")
    elif result1 and result2:
        print("✅ Both formats work - either is acceptable")
    else:
        print("⚠️ Need valid JSESSIONID cookie to test properly")
        print("   Run this from within the bot with active session")
    
    print("\n" + "=" * 80)
    print("\nNOTE: These tests will fail without valid JSESSIONID cookie.")
    print("To test properly, run from within the bot with an active session.")
    print("=" * 80)

if __name__ == "__main__":
    main()
