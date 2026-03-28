import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from monitors.models import MonitorTask, Agency, TelegramGroup

print('=== FINAL STATE ===\n')
agencies = Agency.objects.filter(is_active=True).exclude(plan='system')
for agency in agencies:
    tasks = MonitorTask.objects.filter(agency=agency, is_active=True)
    group = TelegramGroup.objects.filter(agency=agency, status='approved').first()
    print(f'AGENCY: {agency.name} (plan={agency.plan})')
    print(f'  Group: {group.chat_title if group else "NO GROUP LINKED"} | chat_id={group.chat_id if group else "N/A"}')
    print(f'  Tasks: {tasks.count()}')
    for t in tasks.order_by('dates'):
        print(f'    [{t.id}] {t.dates} | {t.visitors}v | type={t.ticket_type} | lang={t.language} | status={t.last_status}')
    print()

print('=== AGENCIES WITH NO TASKS ===')
for agency in agencies:
    if MonitorTask.objects.filter(agency=agency, is_active=True).count() == 0:
        print(f'  {agency.name} - no active tasks')

print('\n=== GROUPS WITH NO AGENCY ===')
for g in TelegramGroup.objects.filter(status='approved', agency__isnull=True):
    print(f'  {g.chat_title} ({g.chat_id}) - approved but no agency!')

print('\n=== SUSPENDED/PENDING GROUPS ===')
for g in TelegramGroup.objects.exclude(status='approved'):
    print(f'  {g.chat_title} ({g.chat_id}) - status={g.status}')
