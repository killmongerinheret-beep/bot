import requests
BASE = 'https://tickets.museivaticani.va'
H = {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'User-Agent': 'Mozilla/5.0'}
s = requests.Session()
s.get(f'{BASE}/home', headers={'User-Agent': H['User-Agent']}, timeout=10)
r = s.get(f'{BASE}/api/search/resultPerTag', params={
    'lang':'it','visitorNum':'2','visitDate':'19/06/2026',
    'area':'1','who':'','page':'0','tag':'MV-Biglietti'
}, headers=H, timeout=10)
visits = r.json().get('visits', [])
ticket = next((v for v in visits if 'musei vaticani' in v.get('name','').lower() and 'ingresso' in v.get('name','').lower()), None)
if not ticket:
    print('No ticket found'); exit()
tid = ticket['id']
print(f"ticket_id: {tid}")
r2 = s.get(f'{BASE}/api/visit/timeavail', params={
    'lang':'it','visitLang':'','visitTypeId':str(tid),'visitorNum':'2','visitDate':'19/06/2026'
}, headers=H, timeout=10)
slots = r2.json().get('timetable', [])
for sl in slots:
    marker = ' <-- TARGET' if sl.get('time') == '17:00' else ''
    print(f"  {sl.get('time')}  {sl.get('availability')}{marker}")
