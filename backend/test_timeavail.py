import requests, sys, os
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://tickets.museivaticani.va/'
}

# Test timeavail for dates that had issues - use fresh session per date
test_cases = [
    ('17/03/2026', '769116437', 2, ''),   # SOLD_OUT on search
    ('18/03/2026', '769116437', 2, ''),   # SOLD_OUT on search
    ('19/03/2026', '1818211570', 2, ''),  # Different ticket name (Ingresso AREE MUSEALI)
    ('21/03/2026', '769116437', 2, ''),   # SOLD_OUT on search
    ('23/03/2026', '769116437', 2, ''),   # AVAILABLE
    ('25/03/2026', '769116437', 2, ''),   # AVAILABLE
]

print("=== TIMEAVAIL API TEST ===")
for date, ticket_id, visitors, lang in test_cases:
    session = requests.Session()
    # First get JSESSIONID via search
    session.get(
        'https://tickets.museivaticani.va/api/search/resultPerTag',
        params={'lang':'it','visitorNum':str(visitors),'visitDate':date,'area':'1','who':'','page':'0','tag':'MV-Biglietti'},
        headers=headers, timeout=15
    )
    jsession = session.cookies.get('JSESSIONID', 'NONE')

    try:
        r = session.get(
            'https://tickets.museivaticani.va/api/visit/timeavail',
            params={'lang':'it','visitLang':lang,'visitTypeId':ticket_id,'visitorNum':str(visitors),'visitDate':date},
            headers=headers,
            timeout=15
        )
        data = r.json()
        timetable = data.get('timetable', [])
        available = [s['time'] for s in timetable if s.get('availability') != 'SOLD_OUT']
        print(f"{date} | id={ticket_id} | HTTP {r.status_code} | {len(timetable)} slots total | {len(available)} available | JSESSION={jsession[:10] if jsession != 'NONE' else 'NONE'}")
        if available:
            print(f"  Available: {available[:5]}")
    except Exception as e:
        print(f"{date} | id={ticket_id} | EXCEPTION: {e}")
