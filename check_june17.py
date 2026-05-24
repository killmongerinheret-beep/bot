import requests, sys, os, django

# Check directly from API first (no Django needed)
BASE = 'https://tickets.museivaticani.va'
H = {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'Referer': f'{BASE}/'}
s = requests.Session()
s.get(f'{BASE}/home', headers=H, timeout=8)

print("=== Direct Vatican API check for 17/06/2026 ===\n")
for vis in [1, 2]:
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(vis), 'visitDate': '17/06/2026',
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers=H, timeout=8)
    ticket = next((v for v in r.json().get('visits', [])
                   if 'musei vaticani' in v.get('name', '').lower()
                   and 'ingresso' in v.get('name', '').lower()), None)
    if not ticket:
        print(f"v={vis}: no standard entry ticket found")
        continue
    tid = ticket['id']
    avail = ticket.get('availability')
    r2 = s.get(f'{BASE}/api/visit/timeavail', params={
        'lang': 'it', 'visitLang': '', 'visitTypeId': str(tid),
        'visitorNum': str(vis), 'visitDate': '17/06/2026'
    }, headers=H, timeout=8)
    if r2.status_code == 200:
        timetable = r2.json().get('timetable', [])
        open_slots = [sl for sl in timetable if sl.get('availability') not in ('SOLD_OUT', 'NOT_ALLOWED')]
        first = open_slots[0]['time'] if open_slots else None
        print(f"v={vis}: search={avail}, open_slots={len(open_slots)}, first={first}, ticket_id={tid}")
    else:
        print(f"v={vis}: search={avail}, timeavail={r2.status_code}")

# Now check the task in DB
print("\n=== Checking snipe task in DB ===\n")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
tasks = MonitorTask.objects.filter(is_active=True, tier='snipe')
print(f"Active snipe tasks: {tasks.count()}")
for t in tasks:
    print(f"\nTask #{t.id}:")
    print(f"  dates          = {t.dates}")
    print(f"  visitors       = {t.visitors} (adults={t.adult_count}, children={t.child_count})")
    print(f"  preferred_times= {t.preferred_times}")
    print(f"  checkout_method= {t.checkout_method}")
    print(f"  agent_target   = {t.agent_target}")
    print(f"  last_status    = {t.last_status}")
    print(f"  last_checked   = {t.last_checked}")
    print(f"  last_result    = {t.last_result_summary}")
