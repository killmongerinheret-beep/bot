"""Reset superadmin password and set up June 15 recap scanning"""
import sys, os, hashlib, secrets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()

from monitors.models import User, Agency

# ── 1. Reset superadmin password ─────────────────────────────────────────────
NEW_PASSWORD = 'HydraAdmin2026!'
user = User.objects.get(id=6)
salt = secrets.token_hex(16)
hashed = hashlib.sha256((NEW_PASSWORD + salt).encode()).hexdigest()
user.password_hash = f"{salt}${hashed}"
user.save(update_fields=['password_hash'])
print(f'✅ Superadmin password reset')
print(f'   Username: {user.username}')
print(f'   Password: {NEW_PASSWORD}')
print(f'   Login at: https://hydrabot.it  (redirects to /admin)')
print()

# ── 2. Verify June 15 is in scan range ───────────────────────────────────────
from datetime import date, timedelta
today = date.today()
june15 = date(2026, 6, 15)
days_away = (june15 - today).days
scan_end = today + timedelta(days=2 * 31)

print(f'June 15 2026: {june15.strftime("%d/%m/%Y")}')
print(f'Days away: {days_away}')
print(f'Current scan range ends: {scan_end.strftime("%d/%m/%Y")}')
print(f'June 15 in scan range: {"✅ YES" if june15 <= scan_end else "❌ NO — need to extend months"}')
print()

# ── 3. Check current held slots for June 15 ──────────────────────────────────
from monitors.models import HeldSlot, Agency
wor = Agency.objects.filter(name='WOR').first()
june15_slots = HeldSlot.objects.filter(
    task__agency=wor, date='15/06/2026', status__in=['held','paying','paid']
).order_by('slot_time')
print(f'June 15 slots currently held: {june15_slots.count()}')
for s in june15_slots:
    print(f'  {s.slot_time} | {s.ticket_name[:40]} | #{s.id}')
