import requests
BASE = 'https://tickets.museivaticani.va'
H = {'Accept': 'application/json, text/plain, */*', 'X-Requested-With': 'XMLHttpRequest',
     'Referer': BASE+'/', 'User-Agent': 'Mozilla/5.0'}

s = requests.Session()

# Check with 2 visitors
for visitors in [1, 2]:
    r = s.get(f'{BASE}/api/search/resultPerTag',
        params={'lang':'it','visitorNum':str(visitors),'visitDate':'25/04/2026',
                'area':'1','who':'','page':'0','tag':'MV-Biglietti'},
        headers=H, timeout=10)
    jsid = s.cookies.get('JSESSIONID','')
    visits = r.json().get('visits', [])
    print(f'\n=== {visitors} visitors — MV-Biglietti ===')
    for v in visits:
        name = v.get('name','')[:55]
        avail = v.get('availability')
        print(f'  {avail:<15} {name}')
        if avail not in ('SOLD_OUT','NOT_ALLOWED'):
            tid = str(v['id'])
            r2 = s.get(f'{BASE}/api/visit/timeavail',
                params={'lang':'it','visitLang':'','visitTypeId':tid,'visitorNum':str(visitors),'visitDate':'25/04/2026'},
                headers={**H,'Cookie':f'JSESSIONID={jsid}'}, timeout=8)
            for sl in r2.json().get('timetable',[]):
                print(f'    {sl["time"]} → {sl["availability"]} residual={sl.get("residual")} id={sl["id"]}')
