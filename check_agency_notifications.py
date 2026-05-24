"""
Check all agencies and whether they will receive slot notifications.
Run: python check_agency_notifications.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()

from monitors.models import Agency, TelegramGroup, MonitorTask

print("\n" + "━"*75)
print("  AGENCY NOTIFICATION STATUS CHECK")
print("━"*75)

agencies = Agency.objects.filter(is_active=True).exclude(plan='system').order_by('name')

if not agencies.exists():
    print("  ❌ No active agencies found in DB!")
else:
    for agency in agencies:
        print(f"\n  🏢 Agency: {agency.name}  (plan={agency.plan}  id={agency.id})")

        # Check linked Telegram groups
        groups = TelegramGroup.objects.filter(agency=agency)
        if not groups.exists():
            print(f"     ❌ NO Telegram groups linked — will NOT receive notifications")
        else:
            for g in groups:
                approved  = g.status == 'approved'
                notif_on  = g.notification_enabled
                will_recv = approved and notif_on
                icon = "✅" if will_recv else "❌"
                reason = []
                if not approved:  reason.append(f"status='{g.status}' (needs 'approved')")
                if not notif_on:  reason.append("notification_enabled=False")
                reason_str = " | ".join(reason) if reason else "all good"
                print(f"     {icon} Group: {g.chat_title or g.chat_id}  [{reason_str}]")

        # Check active monitor tasks
        tasks = MonitorTask.objects.filter(agency=agency, is_active=True, site='vatican')
        recap_tasks = MonitorTask.objects.filter(agency=agency, is_active=False, site='vatican')
        print(f"     📋 Active monitor tasks: {tasks.count()}  |  Inactive (recap/internal): {recap_tasks.count()}")

        for t in tasks[:3]:
            silent = t.notification_mode == 'silent'
            print(f"       {'🔕' if silent else '🔔'} Task #{t.id} tier={t.tier} mode={t.notification_mode} dates={t.dates[:2]}")

print("\n" + "━"*75)
print("  SUMMARY")
print("━"*75)

total = agencies.count()
will_notify = 0
for agency in agencies:
    has_working_group = TelegramGroup.objects.filter(
        agency=agency, status='approved', notification_enabled=True
    ).exists()
    has_active_task = MonitorTask.objects.filter(
        agency=agency, is_active=True, site='vatican'
    ).exclude(notification_mode='silent').exists()
    if has_working_group and has_active_task:
        will_notify += 1

print(f"  Total active agencies : {total}")
print(f"  Will receive slot alerts: {will_notify}")
print(f"  Missing setup          : {total - will_notify}")
print("━"*75 + "\n")
