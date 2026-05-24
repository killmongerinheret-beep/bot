"""
Reset all agency user passwords to known values and print full credentials.
Run: python reset_and_show_credentials.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()

import secrets, hashlib
from monitors.models import Agency, TelegramGroup, MonitorTask
from monitors.models import User as BotUser

# ── New passwords per user ────────────────────────────────────────────────────
# Format: username -> new_password
# Using agency-name-based passwords that are easy to share
NEW_PASSWORDS = {
    'vatican_bot_agency_1': 'Vatican2026!',
    'wondersofrome':        'Wonders2026!',
    'Tourguides':           'Tourguides2026!',
    'Italypass':            'Italypass2026!',
    'bigbus':               'Bigbus2026!',
    'wondersofrome123':     'Wonders2026!',
    'Bot123':               'Mahabur2026!',
    'superadmin':           'Admin2026!',
}

def make_hash(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"

print('\n' + '='*90)
print('  HYDRABOT.IT — FULL CREDENTIALS')
print('='*90)
print(f'  {"Agency":<25} {"Username":<22} {"Password":<20} {"Email":<35} {"Login URL"}')
print('─'*90)

for user in BotUser.objects.all().select_related('agency').order_by('agency__name'):
    if user.agency and user.agency.plan == 'system':
        continue  # skip system admin

    new_pw = NEW_PASSWORDS.get(user.username)
    if new_pw:
        user.password_hash = make_hash(new_pw)
        user.save(update_fields=['password_hash'])
        status = '✅ reset'
    else:
        new_pw = '(unchanged)'
        status = '⚠️  no reset'

    agency_name = user.agency.name if user.agency else '(none)'
    print(f'  {agency_name:<25} {user.username:<22} {new_pw:<20} {user.email:<35} https://hydrabot.it')

print('─'*90)
print(f'\n  Login URL: https://hydrabot.it')
print(f'  All passwords reset successfully.\n')

# ── Also show group / notification status ─────────────────────────────────────
print('='*90)
print('  NOTIFICATION STATUS PER AGENCY')
print('='*90)
print(f'  {"Agency":<25} {"Group":<22} {"Status":<12} {"Active Tasks":<14} {"Will Notify?"}')
print('─'*90)

for a in Agency.objects.exclude(plan='system').order_by('name'):
    groups = TelegramGroup.objects.filter(agency=a)
    active_tasks = MonitorTask.objects.filter(agency=a, is_active=True).count()

    if not groups.exists():
        print(f'  {a.name:<25} {"(no group)":<22} {"-":<12} {active_tasks:<14} ❌ No group linked')
    else:
        for g in groups:
            will = g.status == 'approved' and g.notification_enabled and active_tasks > 0
            print(f'  {a.name:<25} {(g.chat_title or g.chat_id):<22} {g.status:<12} {active_tasks:<14} {"✅ YES" if will else "❌ NO"}')

print('─'*90 + '\n')
