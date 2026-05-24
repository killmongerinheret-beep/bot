import requests
import sys

VATICAN_BASE = 'https://tickets.museivaticani.va'
H = {
    'Accept': 'application/json, text/plain, */*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{VATICAN_BASE}/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

date_str = '15/06/2026'
visitors = 1
EXCLUDED = ['pellegrinaggi', 'lunch', 'pranzo', 'gruppi', 'specola', 'palazzo', 'didattiche']

r = requests.get(f'{VATICAN_BASE}/api/search/resultPerTag', params={
    'lang': 'it', 'visitorNum': str(visitors), 'visitDate': date_str,
    'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
}, headers=H, timeout=8)

visits = r.json().get('visits', [])

print('Filtering logic test:')
print('=' * 80)
for v in visits:
    name = v.get('name', '').lower()
    avail = v.get('availability', '')
    
    has_musei = 'musei vaticani' in name
    has_ingresso = 'ingresso' in name
    has_excluded = any(x in name for x in EXCLUDED)
    is_available = avail == 'AVAILABLE'
    
    passes = has_musei and has_ingresso and not has_excluded and is_available
    
    print(f'{v.get("name", "")}')
    print(f'  musei: {has_musei}, ingresso: {has_ingresso}, excluded: {has_excluded}, available: {is_available}')
    print(f'  PASSES: {passes}')
    print()

# Now find the ticket
ticket = next((v for v in visits
               if 'musei vaticani' in v.get('name', '').lower()
               and 'ingresso' in v.get('name', '').lower()
               and not any(x in v.get('name', '').lower() for x in EXCLUDED)
               and v.get('availability') == 'AVAILABLE'), None)

if ticket:
    print(f'FOUND TICKET: {ticket.get("name")} (ID: {ticket.get("id")})')
    
    # Check timeavail
    tid = str(ticket['id'])
    r2 = requests.get(f'{VATICAN_BASE}/api/visit/timeavail', params={
        'lang': 'it', 'visitLang': '', 'visitTypeId': tid,
        'visitorNum': str(visitors), 'visitDate': date_str,
    }, headers=H, timeout=8)
    
    if r2.status_code == 200:
        slots = [sl for sl in r2.json().get('timetable', [])
                 if sl.get('availability') == 'AVAILABLE']
        print(f'AVAILABLE SLOTS: {len(slots)}')
        if slots:
            print(f'First slot: {slots[0].get("time")} (ID: {slots[0].get("id")})')
else:
    print('NO TICKET FOUND')
