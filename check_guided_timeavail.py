"""Check timeavail for all active guided tour tasks and force a notification test."""
import sys, os, requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()

from monitors.models import MonitorTask, Agency, TelegramGroup
from monitors.notification_utils import send_telegram_signal

BASE = 'https://tickets.museivaticani.va'
H = {'Accept': 'application/json, text/plain, */*', 'X-Requested-With': 'XMLHttpRequest',
     'Referer': BASE+'/', 'User-Agent': 'Mozilla/5.0'}

print('\n=== GUIDED TOUR TIMEAVAIL CHECK ===\n')

tasks = MonitorTask.objects.filter(
    ticket_type=1, is_active=True
).select_related('agency').order_by('agency__name', 'id')

found_available = []

for task in tasks:
    s = requests.Session()
    # Step 1: search to get fresh IDs + JSESSIONID
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(task.visitors),
        'visitDate': task.dates[0].replace('-', '/').split('/')[::-1].__class__(task.dates[0].split('-'))
        if '-' in task.dates[0] else task.dates[0],
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Visite-Guidate'
    }, headers=H, timeout=10)

    # Normalize date
    raw = task.dates[0] if task.dates else None
    if not raw:
        continue
    if '-' in raw:
        y, m, d = raw.split('-')
        date_str = f'{d}/{m}/{y}'
    else:
        date_str = raw

    jsid = s.cookies.get('JSESSIONID', '')
    visits = r.json().get('visits', []) if r.status_code == 200 else []

    available_slots = []
    matched_ticket = None

    for v in visits:
        if v.get('availability') in ('SOLD_OUT', 'NOT_ALLOWED'):
            continue
        tid = str(v['id'])
        r2 = s.get(f'{BASE}/api/visit/timeavail', params={
            'lang': 'it', 'visitLang': task.language or '', 'visitTypeId': tid,
            'visitorNum': str(task.visitors), 'visitDate': date_str,
        }, headers={**H, 'Cookie': f'JSESSIONID={jsid}'}, timeout=8)
        if r2.status_code != 200:
            continue
        slots = [sl for sl in r2.json().get('timetable', []) if sl.get('availability') == 'AVAILABLE']
        if slots:
            available_slots = slots
            matched_ticket = v.get('name', '')
            break

    status = '✅ AVAILABLE' if available_slots else '❌ SOLD_OUT'
    times = ', '.join(sl['time'] for sl in available_slots[:5])
    print(f'  Task #{task.id} [{task.agency.name}] {date_str} {task.language} {task.visitors}v')
    print(f'    {status}  {matched_ticket[:45] if matched_ticket else "no match"}')
    if available_slots:
        print(f'    Times: {times}')
        found_available.append((task, date_str, available_slots, matched_ticket))
    print()

# Force send notification for first available guided tour
if found_available:
    task, date_str, slots, ticket_name = found_available[0]
    print(f'\n=== FORCING TEST NOTIFICATION ===')
    print(f'Sending to groups for agency: {task.agency.name}')

    groups = TelegramGroup.objects.filter(
        agency=task.agency, status='approved', notification_enabled=True
    )
    print(f'Groups: {groups.count()}')

    times_str = '\n'.join(f'   • {sl["time"]}' for sl in slots[:10])
    msg = (
        f'🎉 GUIDED TOUR AVAILABLE! (TEST)\n\n'
        f'━━━━━━━━━━━━━━━━━━━━━━\n'
        f'📅 DATE: {date_str}\n'
        f'🎫 {ticket_name}\n'
        f'🌍 Language: {task.language}\n'
        f'👥 Visitors: {task.visitors}\n'
        f'━━━━━━━━━━━━━━━━━━━━━━\n\n'
        f'⏰ Available times:\n{times_str}\n\n'
        f'🔗 https://tickets.museivaticani.va/home'
    )

    for g in groups:
        result = send_telegram_signal(g.chat_id, msg)
        print(f'  → {g.chat_title} ({g.chat_id}): {"✅ sent" if result else "❌ failed"}')

    if not groups.exists():
        print('  ❌ No approved groups for this agency!')
else:
    print('\n❌ No available guided tours found to test with.')
    print('All guided tour slots are currently sold out.')
