import os
import sys
import logging

# Paths and Django setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

if BASE_DIR in sys.path:
    sys.path.remove(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from typing import List, Dict, Any
from monitors.models import MonitorTask, CheckResult
from monitors.notification_utils import format_vatican_notification

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VerifyMarch26")

TARGET_DATES = {"26/03/2026", "2026-03-26"}


def task_matches_date(dates: List[str]) -> bool:
    if not dates:
        return False
    for d in dates:
        if d in TARGET_DATES:
            return True
    return False


def summarize_check(details: Dict[str, Any]) -> str:
    date = details.get("date")
    ticket_name = details.get("ticket_name")
    ticket_id = details.get("ticket_id")
    language = details.get("language")
    slots = details.get("slots") or []
    times = [s.get("time", "N/A") if isinstance(s, dict) else s for s in slots]
    return f"date={date} id={ticket_id} name={ticket_name} lang={language} slots={len(slots)} times={times[:8]}"


def main():
    logger.info("🔍 Verifying all tasks and notifications for 26 March 2026")

    tasks = [t for t in MonitorTask.objects.all() if task_matches_date(t.dates)]
    if not tasks:
        logger.warning("No tasks found for 26 March 2026")
        return

    logger.info(f"Found {len(tasks)} tasks for target date")

    for task in tasks:
        logger.info(f"\n— Task #{task.id} | agency={task.agency.name} | site={task.site} | ticket_type={task.ticket_type} | lang={task.language}")
        last_result: CheckResult = task.results.order_by("-check_time").first()
        if not last_result:
            logger.warning("  ⚠️ No CheckResult entries for this task")
            continue

        logger.info(f"  Last status: {last_result.status} at {last_result.check_time}")
        details = last_result.details or {}
        logger.info(f"  Details: {summarize_check(details)}")

        # Reconstruct the exact Telegram message that would have been sent
        try:
            msg = format_vatican_notification(
                date=details.get("date") or (task.dates[0] if task.dates else ""),
                ticket_name=details.get("ticket_name") or task.ticket_name or "Unknown",
                ticket_id=str(details.get("ticket_id") or task.ticket_id or ""),
                slots=details.get("slots") or [],
                preferred_times=getattr(task, "preferred_times", None),
                language=(details.get("language") or task.language),
                visitors=task.visitors,
                check_method="god-tier"
            )
            logger.info("  └─ Telegram message preview reconstructed successfully ✅")
        except Exception as e:
            logger.error(f"  ❌ Failed to reconstruct message: {e}")

        # Quick sanity: check for mismatch where name suggests Vatican admission but id is None or belongs to other product families
        tname = (details.get("ticket_name") or task.ticket_name or "").lower()
        tid = str(details.get("ticket_id") or task.ticket_id or "")
        if "musei vaticani" in tname and "ingresso" in tname:
            if not tid:
                logger.warning("  ⚠️ Name suggests Vatican Admission but ticket_id is missing")

    logger.info("\n✅ Verification complete. If you need live API re-check, run worker_vatican/verify_real_api_availability.py")


if __name__ == "__main__":
    main()

