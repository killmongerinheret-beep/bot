import requests
import time
from datetime import datetime, timedelta

# Test dates in July 2026 (closer to current date)
test_dates = []
start_date = datetime(2026, 5, 1)  # Start with May
for i in range(30):
    test_dates.append((start_date + timedelta(days=i)).strftime('%d/%m/%Y'))

print('Testing Vatican API with May 2026 dates...\n')

url_search = 'https://tickets.museivaticani.va/api/search/resultPerTag'
url_time = 'https://tickets.museivaticani.va/api/visit/timeavail'
headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://tickets.museivaticani.va/'
}

for date in test_dates[:10]:
    print(f'Testing {date}...')
    
    # Get fresh ID
    r = requests.get(url_search, params={
        'lang': 'it',
        'visitorNum': '1',
        'visitDate': date,
        'area': '1',
        'who': '',
        'page': '0',
        'tag': 'MV-Biglietti'
    }, headers=headers, timeout=10)
    
    if r.status_code != 200:
        print(f'  Search API failed: {r.status_code}')
        continue
    
    visits = r.json().get('visits', [])
    ticket = next((v for v in visits 
                   if 'Musei Vaticani - Biglietti d' in v.get('name', '')
                   and v.get('availability') == 'AVAILABLE'), None)
    
    if not ticket:
        print(f'  No available tickets')
        continue
    
    tid = ticket['id']
    print(f'  Ticket ID: {tid}')
    
    # Check timeavail
    time.sleep(0.5)
    r2 = requests.get(url_time, params={
        'lang': 'it',
        'visitLang': '',
        'visitTypeId': str(tid),
        'visitorNum': '1',
        'visitDate': date
    }, headers=headers, timeout=10)
    
    print(f'  Timeavail status: {r2.status_code}')
    
    if r2.status_code == 200:
        timetable = r2.json().get('timetable', [])
        available = [s for s in timetable if s.get('availability') == 'AVAILABLE']
        print(f'  ✓ Total slots: {len(timetable)}, Available: {len(available)}')
        if available:
            print(f'    First slot: {available[0].get("time")}')
            break  # Found a working date!
    else:
        print(f'  ✗ API error')
    
    time.sleep(0.3)
