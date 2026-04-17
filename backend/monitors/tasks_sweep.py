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


def _search_and_timeavail(date, visitors):
    """Search API + timeavail using a random proxy."""
    from .tasks_search_api import get_proxy_str
    proxy_str, _ = get_proxy_str('vatican')
    s = requests.Session()
    if proxy_str:
        s.proxies = {'http': proxy_str, 'https': proxy_str}

    try:
        r = s.get(f'{BASE}/api/search/resultPerTag', params={
            'lang': 'it', 'visitorNum': str(visitors), 'visitDate': date,
            'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
        }, headers=HEADERS, timeout=8)

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
        }, headers=HEADERS, timeout=8)

        if r2.status_code != 200:
            return None, None, []

        open_slots = [t for t in r2.json().get('timetable', [])
                     if t.get('availability') not in ('SOLD_OUT',)]
        return s, ticket_id, open_slots

    except Exception as e:
        logger.warning(f"Search/timeavail error for {date} v={visitors}: {e}")
        return None, None, []


def _notify_slot_available(date, slot_time):
    """Send availability notification ONLY to groups whose tasks monitor this date/time."""
    from .models import TelegramGroup, MonitorTask
    from .notification_utils import send_telegram_signal
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo('Europe/Rome')).strftime('%H:%M:%S')

    try:
        month_num = int(date.split('/')[1])
        month_name = {4: 'April', 5: 'May', 6: 'June'}.get(month_num, date)
    except Exception:
        month_name = 'Vatican'

    # Find agencies that have tasks monitoring this date
    try:
        year, month, day = date.split('/')
        date_iso = f"20{year[-2:]}-{month}-{day}" if len(year) == 2 else f"{year}-{month}-{day}"
    except Exception:
        date_iso = date

    # Get agency IDs that have active tasks for this date
    relevant_agency_ids = set(
        MonitorTask.objects.filter(
            is_active=True,
            dates__contains=[date_iso]
        ).values_list('agency_id', flat=True)
    )

    if not relevant_agency_ids:
        logger.debug(f"No tasks monitoring {date} — skipping notification")
        return

    msg = (
        f"🎉 {month_name.upper()} TICKETS AVAILABLE!\n\n"
        f"📅 Date: {date}\n"
        f"⏰ Time: {slot_time}\n"
        f"🎫 Musei Vaticani - Standard Entry\n\n"
        f"⚡ Act fast — slots fill quickly!\n"
        f"🕐 Detected: {now} Rome time"
    )

    # Only send to groups linked to relevant agencies
    groups = TelegramGroup.objects.filter(
        status='approved',
        agency_id__in=relevant_agency_ids
    )
    sent = 0
    for g in groups:
        if send_telegram_signal(g.chat_id, msg):
            sent += 1

    logger.info(f"📢 Alert sent to {sent} groups (agencies: {relevant_agency_ids}) for {date} {slot_time}")


@shared_task(name="sweep_notify_slot", queue="snipe")
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
        from .models import MonitorTask, HeldSlot
        from .epay_ssl import make_vatican_session

        day, month, year = date.split('/')
        iso_date = f"{year}-{month}-{day}"

        snipe_tasks = list(MonitorTask.objects.filter(
            is_active=True, site='vatican', tier='snipe'
        ).filter(dates__contains=[iso_date]))

        for task in snipe_tasks:
            # Check preferred times match
            if task.preferred_times:
                all_times = ['08:00','08:30','09:00','09:30','10:00','10:30',
                             '11:00','11:30','12:00','12:30','13:00','13:30',
                             '14:00','14:30','15:00','15:30','16:00','16:30',
                             '17:00','17:30']
                if task.preferred_times != all_times and slot_time not in task.preferred_times:
                    logger.debug(f"  Task #{task.id}: time {slot_time} not in preferred {task.preferred_times} — skip")
                    continue

            logger.info(f"⚡ Snipe task #{task.id} ({task.agency.name}) — recapping to lock slot")

            # RECAP IMMEDIATELY — locks slot for ~55 min, no token needed
            try:
                import time as _time
                s = make_vatican_session(use_proxy=True)

                # Get fresh ticket_id
                H_XHR = {'Accept':'application/json','X-Requested-With':'XMLHttpRequest','Referer':f'https://tickets.museivaticani.va/'}
                r = s.get('https://tickets.museivaticani.va/api/search/resultPerTag', params={
                    'lang':'it','visitorNum':str(task.visitors),'visitDate':date,
                    'area':'1','who':'','page':'0','tag':'MV-Biglietti'
                }, headers=H_XHR, timeout=8)
                tid = None
                if r.status_code == 200:
                    t = next((v for v in r.json().get('visits',[])
                               if 'musei vaticani' in v.get('name','').lower()
                               and 'ingresso' in v.get('name','').lower()), None)
                    if t: tid = t['id']

                if not tid:
                    logger.warning(f"  Could not get ticket_id for recap")
                    continue

                recap_body = {
                    "visitId": str(slot_id), "visitTypeId": int(tid),
                    "visitorNum": int(task.visitors), "lang": "it",
                    "tickets": [
                        {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": str(task.adult_count)},
                        {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": str(task.child_count)},
                    ],
                    "additionalCosts": {"service-0": {"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": int(task.visitors)}},
                    "services": [{"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": int(task.visitors)}],
                }
                HC = {'Accept':'application/json','Content-Type':'application/json',
                      'Referer':'https://tickets.museivaticani.va/home/checkout',
                      'Origin':'https://tickets.museivaticani.va'}
                rr = s.post('https://tickets.museivaticani.va/api/visit/recap', json=recap_body, headers=HC, timeout=10)

                if rr.status_code == 200:
                    rd = rr.json()
                    recap_id = rd.get('recapId','')
                    total = rd.get('total', 0)
                    logger.info(f"  🔒 Slot locked! recapId={recap_id} €{total}")

                    # Save HeldSlot
                    held = HeldSlot.objects.create(
                        task=task, date=date, slot_id=str(slot_id), slot_time=slot_time,
                        ticket_id=str(tid), ticket_name=task.ticket_name or "Musei Vaticani - Biglietti d'ingresso",
                        visitors=task.visitors, 
                        adult_count=task.adult_count,
                        child_count=task.child_count,
                        total_price=total,
                        jsessionid=s.cookies.get('JSESSIONID',''),
                        ticketmv=s.cookies.get('ticketmv',''),
                        recap_id=recap_id, status='held',
                        notes=__import__('json').dumps({'serverid': s.cookies.get('SERVERID',''), 'participants': __import__('json').loads(task.participants_json or '[]')})
                    )
                    logger.info(f"  HeldSlot #{held.id} created")

                    # ACTION: Choose checkout method
                    checkout_method = getattr(task, 'checkout_method', 'api')
                    
                    if checkout_method == 'api':
                        # Trigger FAST API SNIPE immediately (server-side)
                        logger.info(f"  ⚡ Triggering API Snipe for task #{task.id}...")
                        from .lightning_snipe import lightning_snipe_task
                        lightning_snipe_task.delay(held.id)
                    else:
                        # Push to browser_pending for local Playwright agent
                        import base64 as _b64
                        slot_info = _b64.b64encode(
                            f"{date}|{slot_time}|{slot_id}|{task.visitors}|{total}|{task.adult_count}|{task.child_count}".encode()
                        ).decode()
                        from django.core.cache import cache as _cache
                        job = {
                            'data': f'open_browser:{held.id}:{slot_info}',
                            'user': f'Auto-snipe task #{task.id}',
                            'auto': True,
                        }
                        # Route to specific agent if task has one set
                        agent_target = getattr(task, 'agent_target', None)
                        if agent_target:
                            key = f'browser_pending_{agent_target}'
                            q = _cache.get(key, [])
                            q.append(job)
                            _cache.set(key, q, timeout=1800)
                            logger.info(f"  📲 Browser open queued for agent '{agent_target}'")
                        else:
                            pending = _cache.get('browser_pending', [])
                            pending.append(job)
                            _cache.set('browser_pending', pending, timeout=1800)
                            logger.info(f"  📲 Browser open queued for any agent")
                else:
                    logger.warning(f"  Recap failed: {rr.status_code} {rr.text[:100]}")
            except Exception as e:
                logger.error(f"  Recap exception for task #{task.id}: {e}")

    except Exception as e:
        logger.error(f"Sweep snipe trigger error: {e}")

    # Always notify (after snipe attempt so notify doesn't race)
    _notify_slot_available(date, slot_time)

    # Send browser button to WOR Bot for ALL detected slots
    # This fires regardless of tier — any slot detection triggers the button
    try:
        from django.core.cache import cache
        import json as _json
        import requests as _req
        trigger = cache.get('browser_trigger_group')
        if trigger:
            chat_id = trigger.get('chat_id')
            BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

            # Try to find a HeldSlot (created by snipe tasks)
            from .models import HeldSlot
            held = HeldSlot.objects.filter(
                date=date, slot_time=slot_time, status__in=['held','paying']
            ).order_by('-hold_started_at').first()

            if held:
                # Snipe task created a hold — button opens browser for this specific hold
                # Embed slot info in callback so agent doesn't need to fetch it
                import base64 as _b64
                slot_info = _b64.b64encode(
                    f"{held.date}|{held.slot_time}|{held.slot_id}|{held.visitors}|{held.total_price}".encode()
                ).decode()
                msg = (
                    f"🎫 *Slot Locked — Book Now!*\n\n"
                    f"📅 {date} {slot_time}\n"
                    f"👥 {held.visitors} visitors | €{held.total_price}\n\n"
                    f"Click to open Chrome on your machine:"
                )
                button_data = f'open_browser:{held.id}:{slot_info}'
            else:
                # Notify-only task — no hold, but still send button to open browser
                # Browser agent will do the full flow (search → recap → checkout)
                msg = (
                    f"🎫 *Slot Available — Open Browser to Book!*\n\n"
                    f"📅 {date} {slot_time}\n"
                    f"🎫 Musei Vaticani - Standard Entry\n\n"
                    f"Click to open Chrome and book now:"
                )
                # Encode date+time+slot_id for the agent
                import base64
                slot_info = base64.b64encode(
                    f"{date}|{slot_time}|{slot_id}".encode()
                ).decode()
                button_data = f'open_browser_slot:{slot_info}'

            _req.post(
                f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
                json={
                    'chat_id': chat_id,
                    'text': msg,
                    'parse_mode': 'Markdown',
                    'reply_markup': _json.dumps({'inline_keyboard': [[
                        {'text': '🌐 Open Browser', 'callback_data': button_data}
                    ]]})
                },
                timeout=5
            )
            logger.info(f"📢 Browser button sent to {trigger.get('title')} ({chat_id})")
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

    # Get target dates from env or auto-generate from active snipe tasks
    target_dates_str = os.getenv('SWEEP_TARGET_DATES', '')
    if target_dates_str:
        dates = [d.strip() for d in target_dates_str.split(',') if d.strip()]
    else:
        # Auto-generate from active snipe/notify tasks — covers ALL task dates
        from .models import MonitorTask
        task_dates = set()
        for task in MonitorTask.objects.filter(is_active=True).only('dates'):
            for d in (task.dates or []):
                try:
                    # Convert YYYY-MM-DD to DD/MM/YYYY
                    dt = datetime.strptime(d, '%Y-%m-%d')
                    if dt.date() >= datetime.now().date():
                        task_dates.add(dt.strftime('%d/%m/%Y'))
                except Exception:
                    pass
        dates = sorted(task_dates)

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
        # Check with visitor counts from actual tasks for this date
        from .models import MonitorTask
        visitor_counts = set()
        for task in MonitorTask.objects.filter(is_active=True, dates__contains=[
            datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')
        ]).only('visitors'):
            visitor_counts.add(task.visitors)
        if not visitor_counts:
            visitor_counts = {1}  # fallback

        all_open_slots = []
        for vis in visitor_counts:
            s, ticket_id, open_slots = _search_and_timeavail(date, vis)
            if open_slots:                all_open_slots.extend(open_slots)

        if not all_open_slots:
            continue

        for slot in all_open_slots:
            slot_id = slot.get('id', '')
            slot_time = slot.get('time', '')

            # Check if already notified in last 5 minutes (not permanent)
            notify_key = f"sweep_notified:{date}:{slot_time}"
            if cache.get(notify_key):
                continue
            cache.set(notify_key, True, timeout=300)  # 5 min cooldown

            logger.info(f"🆕 NEW OPENING [{weekday}]: {date} {slot_time} | id={slot_id} | avail={slot.get('availability')}")
            new_openings += 1

            sweep_notify_slot.delay(
                date=date,
                slot_id=str(slot_id),
                slot_time=slot_time,
            )

        time.sleep(0.05)  # tiny gap to avoid hammering Vatican

    if new_openings:
        logger.info(f"🚀 SWEEP: Found {new_openings} new openings — notifications dispatched")
    else:
        logger.debug("SWEEP: No new openings found")

    return f"Checked {len(dates_to_check)} dates ({len(high_priority)} high priority), found {new_openings} new openings"
