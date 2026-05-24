import requests
BASE = 'https://tickets.museivaticani.va'
H = {'Accept': 'application/json, text/plain, */*', 'X-Requested-With': 'XMLHttpRequest',
     'Referer': BASE+'/', 'User-Agent': 'Mozilla/5.0'}

print('=== May 2 2026 — Full availability check ===\n')

for visitors in [1, 2, 3, 4, 5]:
    s = requests.Session()
    r = s.get(f'{BASE}/api/search/resultPerTag',
        params={'lang':'it','visitorNum':str(visitors),'visitDate':'02/05/2026',
                'area':'1','who':'','page':'0','tag':'MV-Visite-Guidate'},
        headers=H, timeout=10)
    jsid = s.cookies.get('JSESSIONID','')
    visits = r.json().get('visits',[])

    for v in visits:
        name = v.get('name','')
        if 'triumphalis' not in name.lower() and 'via' not in name.lower():
            continue
        tid = str(v['id'])
        avail_search = v.get('availability')
        for lang in ['ITA','ENG']:
            r2 = s.get(f'{BASE}/api/visit/timeavail',
                params={'lang':'it','visitLang':lang,'visitTypeId':tid,
                        'visitorNum':str(visitors),'visitDate':'02/05/2026'},
                headers={**H,'Cookie':f'JSESSIONID={jsid}'}, timeout=8)
            for sl in r2.json().get('timetable',[]):
                if sl.get('time') == '10:30':
                    print(f'{visitors}v [{lang}] {name[:45]}: search={avail_search} timeavail={sl["availability"]} residual={sl.get("residual")} id={sl["id"]}')

print('\n=== Standard tickets (MV-Biglietti) ===\n')
for visitors in [2]:
    s = requests.Session()
    r = s.get(f'{BASE}/api/search/resultPerTag',
        params={'lang':'it','visitorNum':str(visitors),'visitDate':'02/05/2026',
                'area':'1','who':'','page':'0','tag':'MV-Biglietti'},
        headers=H, timeout=10)
    jsid = s.cookies.get('JSESSIONID','')
    for v in r.json().get('visits',[]):
        print(f'  {v.get("name","")[:60]} -> {v.get("availability")}')
