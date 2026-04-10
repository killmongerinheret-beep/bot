"""
Simulate a slot detection to test the WOR Bot browser button.
Finds a real available slot, creates a HeldSlot, sends the button to WOR Bot.
"""
import os, sys, django, time
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.epay_ssl import make_vatican_session
from monitors.models import Agency, MonitorTask, HeldSlot, TelegramGroup
from datetime import datetime, timedelta
import json, requests

BASE = 'https://tickets.museivaticani.va'
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TRIGGER_CHAT_ID = '-5245239270'  # WOR Bot

H_XHR = {
    'Accept': 'application/json, text/plain, */*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}
HC = {k: v for k, v in H_XHR.items() if k != 'X-Requested-With'}
HC['Referer'] = f'{BASE}/home/checkout'
HC['Content-Type'] = 'application/json'

VISITORS = 1

# ── Find available slot ───────────────────────────────────────────────────────
print("Finding available slot...")
s = make_vatican_session(use_proxy=True)
found = None

for days in range(1, 120):
    d = (datetime.now() + timedelta(days=days)).strftime('%d/%m/%Y')
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(VISITORS), 'visitDate': d,
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers=H_XHR, timeout=10)
    if r.status_code != 200: continue
    ticket = next((v for v in r.json().get('visits', [])
                   if 'musei vaticani' in v.get('name','').lower()
                   and 'ingresso' in v.get('name','').lower()
                   and v.get('availability') in ('AVAILABLE','LOW_AVAILABILITY')), None)
    if not ticket: continue
    tid = ticket['id']
    r2 = s.get(f'{BASE}/api/visit/timeavail', params={
        'lang': 'it', 'visitLang': '', 'visitTypeId': str(tid),
        'visitorNum': str(VISITORS), 'visitDate': d,
    }, headers=H_XHR, timeout=10)
    if r2.status_code != 200: continue
    slots = [sl for sl in r2.json().get('timetable', [])
             if sl.get('availability') not in ('SOLD_OUT', 'NOT_ALLOWED')]
    if slots:
        found = {'date': d, 'tid': tid, 'slot': slots[0]}
        break
    time.sleep(0.05)

if not found:
    print("No available slots"); sys.exit(1)

date, tid, slot = found['date'], found['tid'], found['slot']
slot_id, slot_time = str(slot['id']), slot['time']
print(f"Found: {date} {slot_time} (id={slot_id})")

# ── Recap to lock ─────────────────────────────────────────────────────────────
print("Recapping to lock slot...")
body = {
    "visitId": slot_id, "visitTypeId": int(tid), "visitorNum": VISITORS, "lang": "it",
    "tickets": [
        {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": str(VISITORS)},
        {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": 0},
    ],
    "additionalCosts": {"service-0": {"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": VISITORS}},
    "services": [{"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": VISITORS}],
}
rr = s.post(f'{BASE}/api/visit/recap', json=body, headers=HC, timeout=10)
if rr.status_code != 200:
    print(f"Recap failed: {rr.status_code}"); sys.exit(1)

recap_id = rr.json().get('recapId', '')
total = rr.json().get('total', 0)
print(f"✅ Locked: recapId={recap_id} €{total}")

# ── Create HeldSlot in DB ─────────────────────────────────────────────────────
agency = Agency.objects.filter(is_active=True).exclude(plan='system').first()
task = MonitorTask.objects.filter(agency=agency, is_active=True).first()

if not task:
    print("No active task found — creating a dummy one")
    task = MonitorTask.objects.create(
        agency=agency, site='vatican', area_name='Test',
        dates=[date.replace('/', '-')[::-1].replace('-','/')[::-1]],
        preferred_times=[slot_time], visitors=VISITORS,
        tier='notify', is_active=True, last_status='test'
    )

held = HeldSlot.objects.create(
    task=task, date=date, slot_id=slot_id, slot_time=slot_time,
    ticket_id=str(tid), ticket_name="Musei Vaticani - Biglietti d'ingresso",
    visitors=VISITORS, total_price=total,
    jsessionid=s.cookies.get('JSESSIONID', ''),
    ticketmv=s.cookies.get('ticketmv', ''),
    recap_id=recap_id, status='held',
    notes=json.dumps({'serverid': s.cookies.get('SERVERID', ''), 'test': True})
)
print(f"✅ HeldSlot #{held.id} created")

# ── Send button to WOR Bot ────────────────────────────────────────────────────
print(f"\nSending [🌐 Open Browser] button to WOR Bot ({TRIGGER_CHAT_ID})...")
msg = (
    f"🎫 *TEST — Slot Locked!*\n\n"
    f"📅 {date} {slot_time}\n"
    f"👥 {VISITORS} visitor | €{total}\n"
    f"🔖 recapId: `{recap_id}`\n\n"
    f"Click to open Chrome on your machine:"
)
r_tg = requests.post(
    f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
    json={
        'chat_id': TRIGGER_CHAT_ID,
        'text': msg,
        'parse_mode': 'Markdown',
        'reply_markup': json.dumps({'inline_keyboard': [[
            {'text': '🌐 Open Browser', 'callback_data': f'open_browser:{held.id}'}
        ]]})
    },
    timeout=10
)
print(f"Telegram response: {r_tg.status_code}")
if r_tg.status_code == 200:
    print(f"✅ Button sent to WOR Bot!")
    print(f"\nNow:")
    print(f"1. Run 'run_agent.bat' on your Windows machine")
    print(f"2. Click [🌐 Open Browser] in WOR Bot")
    print(f"3. Chrome will open with the form pre-filled")
    print(f"4. Solve Turnstile → click BUY")
else:
    print(f"❌ Failed: {r_tg.text[:200]}")
