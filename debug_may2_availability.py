#!/usr/bin/env python3
"""
Debug May 2 availability discrepancy between Telegram notifications and actual website.
"""
import requests
import json
from datetime import datetime

BASE = 'https://tickets.museivaticani.va'
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': BASE + '/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print("=" * 80)
print("DEBUGGING MAY 2, 2026 AVAILABILITY DISCREPANCY")
print("=" * 80)
print()

# Test both standard tickets and guided tours
test_configs = [
    {'tag': 'MV-Biglietti', 'label': 'Standard Entry', 'visitors': 2, 'lang': ''},
    {'tag': 'MV-Visite-Guidate', 'label': 'Guided Tour', 'visitors': 1, 'lang': 'ENG'},
    {'tag': 'MV-Visite-Guidate', 'label': 'Guided Tour', 'visitors': 1, 'lang': 'ITA'},
]

for config in test_configs:
    print(f"\n{'='*80}")
    print(f"Testing: {config['label']} - {config['visitors']} visitor(s)")
    if config['lang']:
        print(f"Language: {config['lang']}")
    print("=" * 80)
    
    # Step 1: Search API
    session = requests.Session()
    search_url = f"{BASE}/api/search/resultPerTag"
    search_params = {
        'lang': 'it',
        'visitorNum': str(config['visitors']),
        'visitDate': '02/05/2026',
        'area': '1',
        'who': '',
        'page': '0',
        'tag': config['tag']
    }
    
    print(f"\n📡 STEP 1: Search API Call")
    print(f"URL: {search_url}")
    print(f"Params: {json.dumps(search_params, indent=2)}")
    
    try:
        search_response = session.get(search_url, params=search_params, headers=HEADERS, timeout=10)
        print(f"Status: {search_response.status_code}")
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            visits = search_data.get('visits', [])
            
            print(f"\n✅ Found {len(visits)} ticket types:")
            
            # Get JSESSIONID
            jsessionid = session.cookies.get('JSESSIONID', '')
            print(f"JSESSIONID: {jsessionid[:20]}..." if jsessionid else "JSESSIONID: None")
            
            for idx, visit in enumerate(visits, 1):
                ticket_id = visit.get('id')
                ticket_name = visit.get('name', 'Unknown')
                search_availability = visit.get('availability', 'UNKNOWN')
                
                print(f"\n  [{idx}] {ticket_name}")
                print(f"      ID: {ticket_id}")
                print(f"      Search API Availability: {search_availability}")
                
                # ⚠️ KEY ISSUE: If search API says SOLD_OUT, should we even call timeavail?
                if search_availability in ('SOLD_OUT', 'NOT_ALLOWED'):
                    print(f"      ⚠️  Search API says {search_availability} - Vatican will return 500 on timeavail")
                    print(f"      ⏭️  OPTIMIZATION: Skip timeavail call (it will fail)")
                    continue
                
                # Step 2: Timeavail API (only if search says AVAILABLE)
                print(f"\n      📡 STEP 2: Timeavail API Call")
                timeavail_url = f"{BASE}/api/visit/timeavail"
                timeavail_params = {
                    'lang': 'it',
                    'visitLang': config['lang'],
                    'visitTypeId': str(ticket_id),
                    'visitorNum': str(config['visitors']),
                    'visitDate': '02/05/2026'
                }
                
                print(f"      URL: {timeavail_url}")
                print(f"      Params: {json.dumps(timeavail_params, indent=2)}")
                
                try:
                    timeavail_response = session.get(
                        timeavail_url,
                        params=timeavail_params,
                        headers={**HEADERS, 'Cookie': f'JSESSIONID={jsessionid}'},
                        timeout=8
                    )
                    print(f"      Status: {timeavail_response.status_code}")
                    
                    if timeavail_response.status_code == 200:
                        timeavail_data = timeavail_response.json()
                        timetable = timeavail_data.get('timetable', [])
                        
                        available_slots = [
                            s for s in timetable 
                            if s.get('availability') == 'AVAILABLE'
                        ]
                        
                        print(f"      ✅ Total slots: {len(timetable)}")
                        print(f"      ✅ Available slots: {len(available_slots)}")
                        
                        if available_slots:
                            print(f"\n      🎯 AVAILABLE TIMES:")
                            for slot in available_slots[:5]:  # Show first 5
                                print(f"         • {slot['time']} (residual: {slot.get('residual', 'N/A')})")
                        else:
                            print(f"      ❌ No available slots (all sold out)")
                            
                    elif timeavail_response.status_code == 500:
                        print(f"      ❌ 500 ERROR - Vatican returns this when ticket is SOLD OUT")
                        print(f"      💡 This confirms search API was correct: {search_availability}")
                    else:
                        print(f"      ⚠️  Unexpected status code")
                        
                except Exception as e:
                    print(f"      ❌ Timeavail API Error: {e}")
        else:
            print(f"❌ Search API failed with status {search_response.status_code}")
            
    except Exception as e:
        print(f"❌ Search API Error: {e}")

print("\n" + "=" * 80)
print("ANALYSIS & FINDINGS")
print("=" * 80)
print()
print("🔍 Key Issue Identified:")
print()
print("1. Search API returns 'availability' field for each ticket")
print("   - AVAILABLE: Ticket has slots available")
print("   - SOLD_OUT: All slots are sold out")
print("   - NOT_ALLOWED: Not available for this visitor count/date")
print()
print("2. When search API says SOLD_OUT:")
print("   - Timeavail API will return HTTP 500 error")
print("   - This is Vatican's way of saying 'no slots available'")
print()
print("3. OPTIMIZATION in search_api_monitor.py:")
print("   - Line ~180: Check if search API says SOLD_OUT")
print("   - If yes, skip timeavail call entirely")
print("   - This saves API calls and avoids 500 errors")
print()
print("4. Telegram Notification Issue:")
print("   - Check if monitor is using OLD ticket IDs (stale)")
print("   - Check if monitor is checking wrong date format")
print("   - Check if monitor is misinterpreting 'LOW_AVAILABILITY' as available")
print()
print("💡 Solution:")
print("   - Always use search API first to get fresh ticket IDs")
print("   - Check search API 'availability' field before calling timeavail")
print("   - If search says SOLD_OUT, treat as sold out (don't call timeavail)")
print("   - If search says AVAILABLE, then call timeavail to get specific slots")
print()
