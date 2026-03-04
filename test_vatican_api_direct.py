#!/usr/bin/env python3
"""
Test Vatican API directly to get ticket IDs without parsing HTML
"""
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# Test parameters
date_str = "16/03/2026"
visitors = 1

# Parse date and convert to Rome timezone timestamp
day, month, year = date_str.split('/')
rome = ZoneInfo("Europe/Rome")
dt = datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome)
timestamp_ms = int(dt.timestamp() * 1000)

print("=" * 60)
print("VATICAN API DIRECT TEST")
print("=" * 60)
print(f"Date: {date_str}")
print(f"Timestamp: {timestamp_ms}")
print(f"Visitors: {visitors}")
print()

# Vatican uses this API to get available tickets for a date
# This is what the Angular app calls
api_url = f"https://tickets.museivaticani.va/api/search/resultPerTag"

params = {
    'lang': 'it',
    'visitorNum': visitors,
    'visitDate': date_str,
    'volumeId': 1,
    'tag': 'MV-Biglietti'  # Standard tickets
}

print(f"API URL: {api_url}")
print(f"Params: {params}")
print()

try:
    response = requests.get(api_url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        
        if 'visits' in data:
            print(f"✅ Found {len(data['visits'])} tickets:")
            print()
            
            for visit in data['visits']:
                ticket_id = visit.get('id')
                name = visit.get('name', 'Unknown')
                availability = visit.get('availability', 'Unknown')
                
                print(f"  ID: {ticket_id}")
                print(f"  Name: {name}")
                print(f"  Availability: {availability}")
                print()
        else:
            print("❌ No 'visits' key in response")
            print(f"Response: {data}")
    else:
        print(f"❌ API returned status {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("CONCLUSION")
print("=" * 60)
print("We can get ticket IDs directly from the API without parsing HTML!")
print("The bot should use this API endpoint instead of scraping the page.")
