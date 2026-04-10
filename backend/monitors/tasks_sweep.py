"""
Vatican Sweep — Availability Notification System
=================================================
Monitors all dates in a target month constantly.
The instant any slot opens → sends Telegram notification with Vatican website link.

Celery tasks:
  sweep_monitor_dates   — runs every 30s, checks all target dates
  sweep_notify_slot     — fires for each open slot, sends notification
"""
import logging
import requests
import time
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

BASE = 'https://tickets.museivaticani.va'
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'Origin': BASE,
    'Content-Type': 'application/json',
}


def _get_proxy():
    """Get best available proxy."""
    try:
        from .models import Proxy
        from django.db import models as dm
        now = timezone.now()
        p = Proxy.objects.filter(is_active=True).filter(
            dm.Q(cooldown_until__isnull=True) | dm.Q(cooldown_until__lte=now)
        ).order_by('?').first()
        if p:
            user = p.username
            if 'oxylabs' in (p.ip_port or '').lower():
                import random
                user = f"{p.username}-session-{random.randint(10000,99999)}"
            if user and p.password:
                return f"http://{user}:{p.password}@{p.ip_port}"
            return f"http://{p.ip_port}"
    except Exception:
        pass
    return None


def _search_and_timeavail(date, visitors, proxy=None):
    """
    Step 1+2: Search API → fresh ticket_id + JSESSIONID
    Then timeavail → list of open slots.
    Returns (session, ticket_id, open_slots) or (None, None, [])
    """
    s = requests.Session()
    if proxy:
        s.proxies = {'http': proxy, 'https': proxy}

    try:
        r = s.get(f'{BASE}/api/search/resultPerTag', params={
            'lang': 'it', 'visitorNum': str(visitors), 'visitDate': date,
            'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
        }, headers=HEADERS, timeout=12)

        if r.status_code != 200:
            return None, None, []

        ticket = next((v for v in r.json().get('visits', [])
                      if 'musei vaticani' in v.get('name', '').lower()
                      and 'ingresso' in v.get('name', '').lower()
                      and v.get('availability') == 'AVAILABLE'), None)
        if not ticket:
            return None, None, []

        ticket_id = ticket['id']

        r2 = s.get(f'{BASE}/api/visit/timeavail', params={
            'lang': 'it', 'visitLang': '',
            'visitTypeId': str(ticket_id),
            'visitorNum': str(visitors),
            'visitDate': date,
        }, headers=HEADERS, timeout=12)

        if r2.status_code != 200:
            return None, None, []

        open_slots = [t for t in r2.json().get('timetable', [])
                     if t.get('availability') not in ('SOLD_OUT',)]
        return s, ticket_id, open_slots

    except Exception as e:
        logger.warning(f"Search/timeavail error for {date} v={visitors}: {e}")
        return None, None, []


def _notify_slot_available(date, slot_time):
    """Send simple availability notification to ALL approved groups (ONCE per date per day)."""
    from .models import TelegramGroup
    from .notification_utils import send_telegram_signal
    from datetime import datetime
    from zoneinfo import ZoneInfo

    # Check if we already notified for this date today
    notify_key = f"sweep_notified:{date}"
    if cache.get(notify_key):
        logger.debug(f"Already notified for {date} today — skipping")
        return

    now = datetime.now(ZoneInfo('Europe/Rome')).strftime('%H:%M:%S')

    # Parse month from date (DD/MM/YYYY)
    try:
        month_num = int(date.split('/')[1])
        month_name = {4: 'April', 5: 'May', 6: 'June'}.get(month_num, date)
    except Exception:
        month_name = 'Vatican'

    msg = (
        f"🎉 {month_name.upper()} TICKETS AVAILABLE!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Date: {date}\n"
        f"⏰ Time: {slot_time}\n"
        f"🎫 Musei Vaticani - Standard Entry\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 Book now:\n"
        f"https://tickets.museivaticani.va/\n\n"
        f"⚡ Act fast — slots fill quickly!\n\n"
        f"🕐 Detected: {now} Rome time"
    )

    # Send to ALL approved groups across all agencies (ONCE per date)
    all_groups = TelegramGroup.objects.filter(
        status='approved', notification_enabled=True
    )
    sent = 0
    for g in all_groups:
        if send_telegram_signal(g.chat_id, msg):
            sent += 1

    # Set cache to prevent re-notification for this date (expires at midnight)
    from datetime import datetime as dt
    now_dt = dt.now(ZoneInfo('Europe/Rome'))
    midnight = now_dt.replace(hour=23, minute=59, second=59)
    seconds_until_midnight = int((midnight - now_dt).total_seconds())
    cache.set(notify_key, True, timeout=max(seconds_until_midnight, 3600))

    logger.info(f"📢 Availability alert sent to {sent}/{all_groups.count()} groups for {date}")


@shared_task(name="sweep_notify_slot", queue="vatican")
def sweep_notify_slot(date, slot_id, slot_time):
    """
    Slot detected by sweep monitor.
    1. For snipe tasks: IMMEDIATELY call recap to lock the slot (~55 min hold)
    2. Send availability notification to all groups
    3. Complete reservation (Turnstile + reservation API) within the hold window
    """
    logger.info(f"🔔 SWEEP: slot found {date} {slot_time} | slot_id={slot_id}")

    # Trigger snipe FIRST for tasks set to 'snipe' tier — recap locks the slot instantly
    try:
        from .models import MonitorTask
        from .lightning_snipe import lightning_snipe

        day, month, year = date.split('/')
        iso_date = f"{year}-{month}-{day}"

        snipe_tasks = list(MonitorTask.objects.filter(
            is_active=True, site='vatican', tier='snipe'
        ).filter(dates__contains=[iso_date]))

        for task in snipe_tasks:
            # Check preferred times match
            if task.preferred_times:
                all_times = ['09:00','09:30','10:00','10:30','11:00','11:30',
                             '12:00','12:30','13:00','13:30','14:00','14:30',
                             '15:00','15:30','16:00','16:30','17:00']
                if task.preferred_times != all_times and slot_time not in task.preferred_times:
                    logger.debug(f"  Task #{task.id}: time {slot_time} not in preferred {task.preferred_times} — skip")
                    continue

            logger.info(f"⚡ Sniping for task #{task.id} ({task.agency.name}) — recapping to lock slot")
            try:
                result = lightning_snipe(
                    task=task,
                    date=date,
                    slot_id=str(slot_id),
                    slot_time=slot_time,
                    ticket_id=task.ticket_id or '',
                    ticket_name=task.ticket_name or "Musei Vaticani - Biglietti d'ingresso",
                    visitors=task.visitors,
                )
                if result.get('success'):
                    logger.info(f"  ✅ Snipe success: ref={result.get('reference')} in {result.get('elapsed_ms')}ms")
                else:
                    logger.warning(f"  ❌ Snipe failed: {result.get('error')}")
            except Exception as e:
                logger.error(f"  Snipe exception for task #{task.id}: {e}")

    except Exception as e:
        logger.error(f"Sweep snipe trigger error: {e}")

    # Always notify (after snipe attempt so notify doesn't race)
    _notify_slot_available(date, slot_time)

    # Send browser button to configured trigger group
    try:
        from django.core.cache import cache
        from .notification_utils import send_telegram_signal
        trigger = cache.get('browser_trigger_group')
        if trigger:
            chat_id = trigger.get('chat_id')
            # Find the held slot we just created
            from .models import HeldSlot
            held = HeldSlot.objects.filter(
                date=date, slot_time=slot_time, status__in=['held','paying']
            ).order_by('-hold_started_at').first()
            if held:
                import json as _json
                msg = (
                    f"🎫 *Slot Locked — Book Now!*\n\n"
                    f"📅 {date} {slot_time}\n"
                    f"👥 {held.visitors} visitors | €{held.total_price}\n\n"
                    f"Click to open Chrome on your machine:"
                )
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                import requests as _req
                BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
                _req.post(
                    f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
                    json={
                        'chat_id': chat_id,
                        'text': msg,
                        'parse_mode': 'Markdown',
                        'reply_markup': _json.dumps({'inline_keyboard': [[
                            {'text': '🌐 Open Browser', 'callback_data': f'open_browser:{held.id}'}
                        ]]})
                    },
                    timeout=5
                )
                logger.info(f"📢 Browser button sent to group {chat_id}")
    except Exception as e:
        logger.debug(f"Browser button send error: {e}")

    return f"Notified + sniped: {date} {slot_time}"


def _get_day_priority(date_str):
    """
    Get priority level for a date based on day of week.
    Priority days (Friday, Saturday, Monday, Thursday) = HIGH
    Other days (Tuesday, Wednesday, Sunday) = NORMAL
    
    Returns: ('high', weekday_name) or ('normal', weekday_name)
    """
    try:
        # Parse DD/MM/YYYY
        day, month, year = date_str.split('/')
        dt = datetime(int(year), int(month), int(day))
        weekday = dt.weekday()  # 0=Monday, 6=Sunday
        weekday_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][weekday]
        
        # High priority: Friday(4), Saturday(5), Monday(0), Thursday(3)
        if weekday in [0, 3, 4, 5]:
            return 'high', weekday_name
        else:
            return 'normal', weekday_name
    except Exception:
        return 'normal', '?'


@shared_task(name="sweep_monitor_dates", queue="vatican")
def sweep_monitor_dates():
    """
    Runs every 30 seconds.
    Checks all target dates with PRIORITY-BASED SCHEDULING:
    - High priority days (Fri, Sat, Mon, Thu): Checked EVERY cycle
    - Normal priority days (Tue, Wed, Sun): Checked every OTHER cycle
    
    This gives 2x more checks to high-demand days.
    """
    import os

    # Get target dates from env or default to current + next month
    target_dates_str = os.getenv('SWEEP_TARGET_DATES', '')
    if target_dates_str:
        dates = [d.strip() for d in target_dates_str.split(',') if d.strip()]
    else:
        # Auto-generate: all days in April + May 2026
        dates = []
        for month in [4, 5]:
            for day in range(1, 32):
                try:
                    d = datetime(2026, month, day)
                    if d.date() >= datetime.now().date():
                        dates.append(d.strftime('%d/%m/%Y'))
                except ValueError:
                    pass

    # Separate dates by priority
    high_priority = []
    normal_priority = []
    
    for date in dates:
        priority, weekday = _get_day_priority(date)
        if priority == 'high':
            high_priority.append((date, weekday))
        else:
            normal_priority.append((date, weekday))

    # Get cycle counter from cache (alternates between 0 and 1)
    cycle_key = 'sweep_cycle_counter'
    cycle = cache.get(cycle_key, 0)
    cache.set(cycle_key, 1 - cycle, timeout=60)  # Toggle for next cycle

    # Build check list
    dates_to_check = []
    
    # ALWAYS check high priority days
    dates_to_check.extend(high_priority)
    
    # Check normal priority days only on even cycles (every other run)
    if cycle == 0:
        dates_to_check.extend(normal_priority)
    
    logger.info(
        f"🔍 SWEEP Cycle {cycle}: Checking {len(dates_to_check)} dates "
        f"(High: {len(high_priority)}, Normal: {len(normal_priority) if cycle == 0 else 0})"
    )
    
    new_openings = 0

    for date, weekday in dates_to_check:
        # Quick check with 2 visitors (fastest)
        s, ticket_id, open_slots = _search_and_timeavail(date, 2)
        if not open_slots:
            continue

        for slot in open_slots:
            slot_id = slot.get('id', '')
            slot_time = slot.get('time', '')

            # Check if already notified today
            notify_key = f"sweep_notified:{date}"
            if cache.get(notify_key):
                continue

            logger.info(f"🆕 NEW OPENING [{weekday}]: {date} {slot_time} | id={slot_id} | avail={slot.get('availability')}")
            new_openings += 1

            # Fire notification task immediately
            sweep_notify_slot.delay(
                date=date,
                slot_id=str(slot_id),
                slot_time=slot_time,
            )

        time.sleep(0.2)  # small delay between dates

    if new_openings:
        logger.info(f"🚀 SWEEP: Found {new_openings} new openings — notifications dispatched")
    else:
        logger.debug("SWEEP: No new openings found")

    return f"Checked {len(dates_to_check)} dates ({len(high_priority)} high priority), found {new_openings} new openings"
