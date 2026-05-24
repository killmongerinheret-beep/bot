import requests
BASE = 'https://tickets.museivaticani.va'
H = {'Accept': 'application/json, text/plain, */*', 'X-Requested-With': 'XMLHttpRequest',
     'Referer': BASE+'/', 'User-Agent': 'Mozilla/5.0'}
s = requests.Session()
r = s.get(f'{BASE}/api/search/resultPerTag',
    params={'lang':'it','visitorNum':'2','visitDate':'02/05/2026','area':'1','who':'','page':'0','tag':'MV-Visite-Guidate'},
    headers=H, timeout=10)
jsid = s.cookies.get('JSESSIONID','')
for v in r.json().get('visits',[]):
    name = v.get('name','')
    tid = str(v['id'])
    for lang in ['ITA','ENG']:
        r2 = s.get(f'{BASE}/api/visit/timeavail',
            params={'lang':'it','visitLang':lang,'visitTypeId':tid,'visitorNum':'2','visitDate':'02/05/2026'},
            headers={**H,'Cookie':f'JSESSIONID={jsid}'}, timeout=8)
        for sl in r2.json().get('timetable',[]):
            if sl.get('time') == '10:30':
                print(f'[{lang}] {name[:50]}: 10:30 -> {sl["availability"]} residual={sl.get("residual")}')
