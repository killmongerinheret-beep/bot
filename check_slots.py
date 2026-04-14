import requests
BASE = 'https://tickets.museivaticani.va'
H = {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
s = requests.Session()
s.get(f'{BASE}/home', timeout=8)

for date, vis in [('12/05/2026', 1), ('12/05/2026', 2), ('13/05/2026', 1), ('13/05/2026', 2), ('15/05/2026', 1), ('15/05/2026', 2)]:
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(vis), 'visitDate': date,
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers=H, timeout=10)
    t = next((v for v in r.json().get('visits', [])
               if 'musei vaticani' in v.get('name', '').lower()
               and 'ingresso' in v.get('name', '').lower()), None)
    if not t:
        print(f'{date} v={vis}: no ticket found')
        continue
    tid = t['id']
    avail = t.get('availability')
    r2 = s.get(f'{BASE}/api/visit/timeavail', params={
        'lang': 'it', 'visitLang': '', 'visitTypeId': str(tid),
        'visitorNum': str(vis), 'visitDate': date
    }, headers=H, timeout=10)
    if r2.status_code != 200:
        print(f'{date} v={vis}: timeavail {r2.status_code}')
        continue
    slots = [sl for sl in r2.json().get('timetable', [])
             if sl.get('availability') in ('AVAILABLE', 'LOW_AVAILABILITY')]
    first = slots[0]['time'] if slots else 'none'
    first_id = slots[0]['id'] if slots else 'none'
    print(f'{date} v={vis}: search={avail}, {len(slots)} slots, first={first} id={first_id}, tid={tid}')
