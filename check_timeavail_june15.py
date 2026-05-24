import requests
BASE = 'https://tickets.museivaticani.va'
H = {
    'Accept': 'application/json, text/plain, */*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

s = requests.Session()

# Step 1: Search API — 20 visitors, June 15
r = s.get(f'{BASE}/api/search/resultPerTag', params={
    'lang': 'it', 'visitorNum': '20', 'visitDate': '15/06/2026',
    'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Visite-Guidate'
}, headers=H, timeout=10)
print(f'Search: {r.status_code}')
visits = r.json().get('visits', [])
jsessionid = s.cookies.get('JSESSIONID', '')
print(f'JSESSIONID: {jsessionid[:20]}...')
print(f'Tickets: {len(visits)}')
print()

# Step 2: timeavail for each available ticket
for v in visits:
    avail = v.get('availability')
    name = v.get('name', '')[:55]
    tid = str(v['id'])
    if avail in ('SOLD_OUT', 'NOT_ALLOWED'):
        print(f'  SKIP [{avail}] {name}')
        continue
    for lang in ['ENG', 'ITA']:
        r2 = s.get(f'{BASE}/api/visit/timeavail', params={
            'lang': 'it', 'visitLang': lang, 'visitTypeId': tid,
            'visitorNum': '20', 'visitDate': '15/06/2026'
        }, headers={**H, 'Cookie': f'JSESSIONID={jsessionid}'}, timeout=8)
        timetable = r2.json().get('timetable', [])
        slot = next((sl for sl in timetable if sl.get('time') == '09:30'), None)
        if slot:
            print(f'  [{lang}] {name}')
            print(f'    09:30 → {slot["availability"]}  id={slot["id"]}  residual={slot.get("residual")}')
