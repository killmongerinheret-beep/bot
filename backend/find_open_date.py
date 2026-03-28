import requests
from datetime import datetime, timedelta

BASE = 'https://tickets.museivaticani.va'
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
}

s = requests.Session()
print("Scanning for open dates (5 visitors, standard entry)...\n")

for days_ahead in range(1, 90):
    d = (datetime.now() + timedelta(days=days_ahead)).strftime('%d/%m/%Y')
    try:
        r = s.get(f'{BASE}/api/search/resultPerTag', params={
            'lang': 'it', 'visitorNum': '5', 'visitDate': d,
            'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
        }, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            continue
        visits = r.json().get('visits', [])
        for v in visits:
            if 'ingresso' in v.get('name', '').lower() and v.get('availability') == 'AVAILABLE':
                print(f"OPEN: {d} | [{v['id']}] {v['name']}")
    except Exception as e:
        print(f"Error on {d}: {e}")
