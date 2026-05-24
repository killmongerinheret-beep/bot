"""Check live availability for all active task dates right now."""
import sys, os, requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()

from monitors.models import MonitorTask, Agency
from collections import defaultdict

BASE = 'https://tickets.museivaticani.va'
H = {'Accept': 'application/json, text/plain, */*', 'X-Requested-With': 'XMLHttpRequest',
     'Referer': BASE+'/', 'User-Agent': 'Mozilla/5.0'}

# Get all unique future dates being monitored
tasks = MonitorTask.objects.filter(is_active=True).select_related('agency')
date_visitor_map = defaultdict(set)
for t in tasks:
    for d in (t.dates or []):
        if '-' in d:
            y, m, day = d.split('-')
            date_str = f'{day}/{m}/{y}'
        else:
            date_str = d
        date_visitor_map[date_str].add(t.visitors)

print(f'\n=== LIVE AVAILABILITY CHECK — {len(date_visitor_map)} dates ===\n')

found_available = []
for date_str in sorted(date_visitor_map.keys()):
    visitors = min(date_visitor_map[date_str])  # use smallest visitor count
    s = requests.Session()
    r = s.get(f'{BASE}/api/search/resultPerTag',
        params={'lang':'it','visitorNum':str(visitors),'visitDate':date_str,
                'area':'1','who':'','page':'0','tag':'MV-Biglietti'},
        headers=H, timeout=8)
    if r.status_code != 200:
        print(f'  {date_str}: API error {r.status_code}')
        continue
    jsid = s.cookies.get('JSESSIONID','')
    visits = r.json().get('visits', [])
    
    available_tickets = [v for v in visits if v.get('availability') not in ('SOLD_OUT','NOT_ALLOWED')]
    if not available_tickets:
        print(f'  {date_str}: ALL SOLD OUT')
        continue
    
    # Check timeavail for available tickets
    for v in available_tickets:
        tid = str(v['id'])
        r2 = s.get(f'{BASE}/api/visit/timeavail',
            params={'lang':'it','visitLang':'','visitTypeId':tid,'visitorNum':str(visitors),'visitDate':date_str},
            headers={**H,'Cookie':f'JSESSIONID={jsid}'}, timeout=8)
        if r2.status_code != 200:
            continue
        slots = [sl for sl in r2.json().get('timetable',[])
                 if sl.get('availability')=='AVAILABLE' and (sl.get('residual') is None or sl.get('residual',0)>0)]
        if slots:
            times = ', '.join(sl['time'] for sl in slots[:5])
            print(f'  ✅ {date_str} {v["name"][:45]} → {len(slots)} slots: {times}')
            found_available.append((date_str, v['name'], slots))
        else:
            print(f'  {date_str} {v["name"][:45]} → SOLD OUT (residual=0)')

print(f'\n=== SUMMARY: {len(found_available)} dates with real availability ===\n')
