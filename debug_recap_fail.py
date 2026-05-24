"""Debug why 10:30 guided tour recap fails"""
import sys, os, requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()

BASE = 'https://tickets.museivaticani.va'
H = {
    'Accept': 'application/json, text/plain, */*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/json',
    'Origin': BASE,
}

s = requests.Session()

# Search for guided tours on a failing date
r = s.get(f'{BASE}/api/search/resultPerTag', params={
    'lang': 'it', 'visitorNum': '2', 'visitDate': '07/05/2026',
    'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Visite-Guidate'
}, headers=H, timeout=8)
print(f'Search: {r.status_code}')
visits = r.json().get('visits', [])
print(f'Tickets: {len(visits)}')
for v in visits:
    print(f'  id={v["id"]} avail={v["availability"]} name={v["name"][:60]}')

print()

# Check timeavail for each ticket
for v in visits:
    r2 = s.get(f'{BASE}/api/visit/timeavail', params={
        'lang': 'it', 'visitLang': 'ENG', 'visitTypeId': str(v['id']),
        'visitorNum': '2', 'visitDate': '07/05/2026'
    }, headers=H, timeout=8)
    timetable = r2.json().get('timetable', [])
    slot_1030 = next((sl for sl in timetable if sl.get('time') == '10:30'), None)
    if slot_1030:
        print(f'Found 10:30 in ticket {v["id"]} ({v["name"][:40]})')
        print(f'  slot: {slot_1030}')
        
        # Try recap
        body = {
            'visitId': str(slot_1030['id']),
            'visitTypeId': int(v['id']),
            'visitorNum': 2,
            'lang': 'it',
            'tickets': [
                {'id': 60, 'name': 'Biglietto Intero', 'price': 20, 'quantity': '2'},
                {'id': 61, 'name': 'Biglietto Ridotto', 'price': 10, 'quantity': '0'},
            ],
            'additionalCosts': {},
            'services': []
        }
        r3 = s.post(f'{BASE}/api/visit/recap', json=body, headers=H, timeout=12)
        print(f'  Recap status: {r3.status_code}')
        print(f'  Recap response: {r3.text[:400]}')
        break
