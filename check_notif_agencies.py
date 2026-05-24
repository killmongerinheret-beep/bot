import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()

from monitors.models import Agency, TelegramGroup, MonitorTask

print('\n=== AGENCIES THAT WILL RECEIVE NOTIFICATIONS ===\n')
groups = TelegramGroup.objects.filter(
    status='approved', notification_enabled=True
).select_related('agency').order_by('agency__name')

if not groups.exists():
    print('NONE — no approved+notification-enabled groups in DB')
else:
    for g in groups:
        a = g.agency
        agency_name = a.name if a else '(no agency linked)'
        agency_id   = a.id   if a else 'N/A'
        active_tasks = MonitorTask.objects.filter(agency=a, is_active=True).count() if a else 0
        print(f'  Agency: {agency_name}  |  ID: {agency_id}  |  Group: "{g.chat_title}"  |  chat_id: {g.chat_id}  |  active_tasks: {active_tasks}')

print('\n=== ALL AGENCIES + GROUP STATUS ===\n')
for a in Agency.objects.all().order_by('id'):
    grps = TelegramGroup.objects.filter(agency=a)
    active_tasks = MonitorTask.objects.filter(agency=a, is_active=True).count()
    print(f'[{a.id}] {a.name}  active={a.is_active}  plan={a.plan}  active_tasks={active_tasks}')
    if not grps.exists():
        print('       (no telegram groups)')
    for g in grps:
        will_notify = g.status == 'approved' and g.notification_enabled
        print(f'       {"WILL NOTIFY" if will_notify else "WONT NOTIFY":12s}  group="{g.chat_title}"  status={g.status}  notif_enabled={g.notification_enabled}  chat_id={g.chat_id}')
