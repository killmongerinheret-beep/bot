import requests
BASE = 'https://tickets.museivaticani.va'
H = {'Accept': 'application/json, text/plain, */*', 'X-Requested-With': 'XMLHttpRequest',
     'Referer': BASE+'/', 'User-Agent': 'Mozilla/5.0'}

print('=== MAY 5 2026 — Full timeavail with residual ===\n')

for tag, label in [('MV-Biglietti', 'Standard'), ('MV-Visite-Guidate', 'Guided')]:
    for visitors in [1, 2, 3, 4]:
        s = requests.Session()
        r = s.get(f'{BASE}/api/search/resultPerTag',
            params={'lang':'it','visitorNum':str(visitors),'visitDate':'05/05/2026',
                    'area':'1','who':'','page':'0','tag':tag},
            headers=H, timeout=10)
        if r.status_code != 200:
            continue
        jsid = s.cookies.get('JSESSIONID','')
        visits = r.json().get('visits', [])

        for v in visits:
            avail_search = v.get('availability')
            if avail_search in ('NOT_ALLOWED',):
                continue
            name = v.get('name','')[:55]
            tid = str(v['id'])

            for lang in (['ENG','ITA'] if tag == 'MV-Visite-Guidate' else ['']):
                r2 = s.get(f'{BASE}/api/visit/timeavail',
                    params={'lang':'it','visitLang':lang,'visitTypeId':tid,
                            'visitorNum':str(visitors),'visitDate':'05/05/2026'},
                    headers={**H,'Cookie':f'JSESSIONID={jsid}'}, timeout=8)
                if r2.status_code != 200:
                    continue
                timetable = r2.json().get('timetable', [])
                available = [sl for sl in timetable if sl.get('availability') == 'AVAILABLE']
                all_slots = timetable

                if available or avail_search == 'AVAILABLE':
                    print(f'[{label}] {visitors}v [{lang or "STD"}] {name}')
                    print(f'  search_avail={avail_search}')
                    for sl in all_slots:
                        marker = '✅' if sl.get('availability') == 'AVAILABLE' else '❌'
                        print(f'  {marker} {sl["time"]} → {sl["availability"]} residual={sl.get("residual")} id={sl["id"]}')
                    print()
                    break  # found result for this ticket, skip other langs
