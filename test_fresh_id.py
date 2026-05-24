import requests
import time

# Step 1: Get fresh IDs
url = 'https://tickets.museivaticani.va/api/search/resultPerTag'
params = {
    'lang': 'it',
    'visitorNum': '1',
    'visitDate': '01/06/2026',
    'area': '1',
    'who': '',
    'page': '0',
    'tag': 'MV-Biglietti'
}
headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://tickets.museivaticani.va/'
}

print('Getting fresh ticket IDs...')
r = requests.get(url, params=params, headers=headers, timeout=15)
if r.status_code == 200:
    visits = r.json().get('visits', [])
    ticket = next((v for v in visits if 'Musei Vaticani - Biglietti d' in v.get('name', '')), None)
    if ticket:
        tid = ticket['id']
        print(f'Fresh ID: {tid}')
        print(f'Name: {ticket.get("name")}')
        print(f'Availability: {ticket.get("availability")}')
        
        # Step 2: Check timeavail with fresh ID
        print('\nChecking timeavail...')
        time.sleep(1)
        r2 = requests.get('https://tickets.museivaticani.va/api/visit/timeavail', params={
            'lang': 'it',
            'visitLang': '',
            'visitTypeId': str(tid),
            'visitorNum': '1',
            'visitDate': '01/06/2026'
        }, headers=headers, timeout=15)
        
        print(f'Status: {r2.status_code}')
        if r2.status_code == 200:
            timetable = r2.json().get('timetable', [])
            print(f'Total slots: {len(timetable)}')
            available = [s for s in timetable if s.get('availability') == 'AVAILABLE']
            print(f'AVAILABLE slots: {len(available)}')
            if available:
                print(f'First: {available[0].get("time")} (ID: {available[0].get("id")})')
        else:
            print(f'Error response: {r2.text[:200]}')
