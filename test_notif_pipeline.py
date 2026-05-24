import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()

from monitors.models import TelegramGroup
from monitors.notification_utils import send_telegram_signal

groups = TelegramGroup.objects.filter(status='approved', notification_enabled=True).select_related('agency')
print(f'Approved groups: {groups.count()}')
for g in groups:
    agency_name = g.agency.name if g.agency else 'no agency'
    msg = (
        f'TEST: Guided tour notification pipeline check\n'
        f'Group: {g.chat_title}\n'
        f'Agency: {agency_name}\n'
        f'Status: notifications are working correctly.'
    )
    result = send_telegram_signal(g.chat_id, msg)
    print(f'  {g.chat_title} ({agency_name}): {"sent" if result else "FAILED"}')
