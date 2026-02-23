import os
import django
import sys
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import CheckResult, MonitorTask, Agency

def run_diagnostics():
    print("--- DIAGNOSTICS START ---")
    
    # 1. Check recent errors (Last 24h)
    time_threshold = timezone.now() - timedelta(hours=24)
    errors = CheckResult.objects.filter(status='error', check_time__gte=time_threshold).order_by('-check_time')[:10]
    
    print(f"\n[RECENT ERRORS] Found: {errors.count()} (Showing last 10)")
    for err in errors:
        print(f" - {err.task.agency.name} | Task {err.task.id} | {err.check_time.strftime('%H:%M:%S')} | {err.error_message}")

    # 2. Check Failed Tasks (State)
    failed_tasks = MonitorTask.objects.filter(last_status='error')
    print(f"\n[FAILED TASKS] Found: {failed_tasks.count()}")
    for t in failed_tasks:
        print(f" - Task {t.id} ({t.agency.name}): {t.last_result_summary}")

    # 3. Check Agency Limits vs Active
    print("\n[AGENCY USAGE]")
    for agency in Agency.objects.filter(is_active=True):
        count = MonitorTask.objects.filter(agency=agency, is_active=True).count()
        print(f" - {agency.name} ({agency.plan}): {count} Active Tasks")

    print("\n--- DIAGNOSTICS END ---")

if __name__ == "__main__":
    run_diagnostics()
