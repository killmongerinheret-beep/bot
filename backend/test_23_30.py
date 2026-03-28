import requests

headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://tickets.museivaticani.va/'
}

for date in ['23/03/2026', '30/03/2026']:
    print(f"\n{'='*60}")
    print(f"DATE: {date}")
    print('='*60)

    # Step 1: Search API - standard tickets
    session = requests.Session()
    r = session.get(
        'https://tickets.museivaticani.va/api/search/resultPerTag',
        params={'lang':'it','visitorNum':'2','visitDate':date,'area':'1','who':'','page':'0','tag':'MV-Biglietti'},
        headers=headers, timeout=20
    )
    data = r.json()
    visits = data.get('visits', [])
    jsession = session.cookies.get('JSESSIONID', 'NONE')
    print(f"Search API (standard) HTTP {r.status_code} | {len(visits)} tickets | JSESSION={jsession[:20] if jsession != 'NONE' else 'NONE'}")
    for v in visits:
        print(f"  id={v.get('id')} | {v.get('name','?')[:55]} | {v.get('availability')}")

    # Step 2: timeavail for each ticket using SAME session (has JSESSIONID)
    print(f"\nTimeavail checks (same session with JSESSIONID):")
    for v in visits[:4]:
        tid = v.get('id')
        avail = v.get('availability')
        if avail in ('SOLD_OUT', 'NOT_ALLOWED'):
            print(f"  SKIP id={tid} ({avail})")
            continue
        try:
            r2 = session.get(
                'https://tickets.museivaticani.va/api/visit/timeavail',
                params={'lang':'it','visitLang':'','visitTypeId':tid,'visitorNum':'2','visitDate':date},
                headers=headers, timeout=20
            )
            timetable = r2.json().get('timetable', [])
            available = [s['time'] for s in timetable if s.get('availability') != 'SOLD_OUT']
            print(f"  id={tid} | HTTP {r2.status_code} | {len(available)}/{len(timetable)} available | {available[:5]}")
        except Exception as e:
            print(f"  id={tid} | ERROR: {e}")
