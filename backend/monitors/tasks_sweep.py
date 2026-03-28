"""
April Sweep — Mass Hold System
================================
Monitors all dates in a target month constantly.
The instant any slot opens → fires parallel recap calls for visitors 1-5
to drain as much inventory as possible immediately.

Celery tasks:
  sweep_monitor_dates   — runs every 30s, checks all target dates
  sweep_hold_slot       — fires for each open slot, holds for all visitor counts
"""
import logging
import requests
import time
from datetime import datetime, timedelta
from celery import shared_task, group
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

# Visitor counts to hold per slot — covers most booking patterns
VISITOR_COUNTS = [1, 2, 3, 4, 5]

# How long to suppress re-hold attempts after a successful hold (seconds)
HOLD_COOLDOWN = 10800  # 3 hours


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


def _recap(session, slot_id, ticket_id, visitors):
    """
    POST /api/visit/recap — hold the slot.
    Returns recap data dict or None.
    """
    body = {
        "visitId": str(slot_id),
        "visitTypeId": int(ticket_id),
        "visitorNum": visitors,
        "lang": "it",
        "tickets": [{"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": visitors}],
        "additionalCosts": {},
        "services": [],
    }
    try:
        r = session.post(f'{BASE}/api/visit/recap', json=body, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.json()
        logger.debug(f"Recap {r.status_code}: {r.text[:120]}")
    except Exception as e:
        logger.warning(f"Recap exception: {e}")
    return None


@shared_task(name="sweep_hold_slot", queue="vatican")
def sweep_hold_slot(date, slot_id, slot_time, agency_id=None):
    """
    Hold a single slot for ALL visitor counts (1-5) simultaneously.
    Each visitor count gets its own fresh session.
    Saves all successful holds to HeldSlot DB.
    """
    from .models import HeldSlot, MonitorTask, Agency

    # Cooldown check — don't re-hold if already held recently
    cooldown_key = f"sweep_hold:{date}:{slot_id}"
    if cache.get(cooldown_key):
        logger.info(f"⏭️ Sweep hold cooldown active for {date} {slot_time}")
        return f"Cooldown: {date} {slot_time}"

    logger.info(f"🚀 SWEEP HOLD: {date} {slot_time} | visitors {VISITOR_COUNTS}")

    # Get agency — use first active agency or specified one
    try:
        if agency_id:
            agency = Agency.objects.get(id=agency_id)
        else:
            agency = Agency.objects.filter(is_active=True).exclude(plan='system').first()
        if not agency:
            logger.error("No agency found for sweep hold")
            return "No agency"
    except Exception as e:
        logger.error(f"Agency lookup failed: {e}")
        return f"Agency error: {e}"

    # Get or create a sweep task for this agency
    task = MonitorTask.objects.filter(
        agency=agency, site='vatican', is_active=True
    ).first()
    if not task:
        logger.error(f"No active task for agency {agency.name}")
        return "No task"

    held_count = 0
    proxy = _get_proxy()

    for visitors in VISITOR_COUNTS:
        # Fresh session per visitor count
        s, ticket_id, _ = _search_and_timeavail(date, visitors, proxy)
        if not s or not ticket_id:
            logger.warning(f"  v={visitors}: Could not get session/ticket_id")
            continue

        recap_data = _recap(s, slot_id, ticket_id, visitors)
        if not recap_data:
            logger.warning(f"  v={visitors}: Recap failed")
            continue

        jsid = s.cookies.get('JSESSIONID', '')
        ticketmv = s.cookies.get('ticketmv', '')
        total = recap_data.get('total', 0)
        recap_id = recap_data.get('recapId') or recap_data.get('id') or ''

        if not jsid:
            logger.warning(f"  v={visitors}: No JSESSIONID after recap")
            continue

        # Save to DB
        held = HeldSlot.objects.create(
            task=task,
            date=date,
            slot_id=str(slot_id),
            slot_time=slot_time,
            ticket_id=str(ticket_id),
            ticket_name="Musei Vaticani - Biglietti d'ingresso",
            visitors=visitors,
            total_price=total,
            jsessionid=jsid,
            ticketmv=ticketmv,
            recap_id=recap_id,
            status='held',
            payment_url='',  # set after save
            notes=f"Sweep hold — {visitors} visitors",
        )
        import os
        base_url = os.getenv('NGROK_DOMAIN', 'hyperkinetic-unsplendorously-jessi.ngrok-free.dev')
        held.payment_url = f"https://{base_url}/api/v1/holds/{held.id}/checkout/"
        held.save(update_fields=['payment_url'])
        held_count += 1
        logger.info(f"  ✅ v={visitors} | €{total} | recapId={recap_id} | HeldSlot #{held.id}")
        time.sleep(0.3)

    if held_count > 0:
        # Set cooldown to avoid re-holding same slot
        cache.set(cooldown_key, True, timeout=HOLD_COOLDOWN)
        logger.info(f"✅ SWEEP: Held {held_count}/{len(VISITOR_COUNTS)} visitor counts for {date} {slot_time}")

        # Notify all approved groups for this agency
        _notify_sweep_hold(task, date, slot_time, held_count)

    return f"Held {held_count} visitor counts for {date} {slot_time}"


def _notify_sweep_hold(task, date, slot_time, held_count):
    """Send Telegram notification to ALL approved groups — slots opened alert."""
    from .models import TelegramGroup, HeldSlot
    from .notification_utils import send_telegram_signal
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo('Europe/Rome')).strftime('%H:%M:%S')

    # Parse month from date (DD/MM/YYYY)
    try:
        month_num = int(date.split('/')[1])
        month_name = {4: 'April', 5: 'May', 6: 'June'}.get(month_num, date)
    except Exception:
        month_name = 'Vatican'

    # Count visitor options held
    recent_holds = HeldSlot.objects.filter(
        task=task, date=date, slot_time=slot_time, status='held'
    ).order_by('visitors')
    visitor_options = ', '.join(str(h.visitors) for h in recent_holds)

    msg = (
        f"🎉 {month_name.upper()} SLOTS JUST OPENED!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Date: {date}\n"
        f"⏰ Time: {slot_time}\n"
        f"🎫 Musei Vaticani - Standard Entry\n"
        f"👥 Available for: {visitor_options} visitors\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔒 Slots are held exclusively.\n"
        f"📩 Contact admin directly to claim your tickets.\n\n"
        f"🕐 {now} Rome time"
    )

    # Send to ALL approved groups across all agencies
    all_groups = TelegramGroup.objects.filter(
        status='approved', notification_enabled=True
    )
    sent = 0
    for g in all_groups:
        if send_telegram_signal(g.chat_id, msg):
            sent += 1

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"📢 Alert sent to {sent}/{all_groups.count()} groups for {date} {slot_time}")


@shared_task(name="sweep_monitor_dates", queue="vatican")
def sweep_monitor_dates():
    """
    Runs every 30 seconds.
    Checks all target dates for any open slots.
    Fires sweep_hold_slot immediately for each new opening found.
    """
    import os
    from django.core.cache import cache

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

    logger.info(f"🔍 SWEEP: Checking {len(dates)} dates")
    new_openings = 0

    for date in dates:
        # Quick check with 2 visitors (fastest)
        s, ticket_id, open_slots = _search_and_timeavail(date, 2)
        if not open_slots:
            continue

        for slot in open_slots:
            slot_id = slot.get('id', '')
            slot_time = slot.get('time', '')

            # Check if already held
            already_held_key = f"sweep_hold:{date}:{slot_id}"
            if cache.get(already_held_key):
                continue

            # Check DB — don't re-hold if active hold exists
            from .models import HeldSlot
            if HeldSlot.objects.filter(date=date, slot_id=str(slot_id), status='held').exists():
                continue

            logger.info(f"🆕 NEW OPENING: {date} {slot_time} | id={slot_id} | avail={slot.get('availability')}")
            new_openings += 1

            # Fire hold task immediately
            sweep_hold_slot.delay(
                date=date,
                slot_id=str(slot_id),
                slot_time=slot_time,
            )

        time.sleep(0.2)  # small delay between dates

    if new_openings:
        logger.info(f"🚀 SWEEP: Found {new_openings} new openings — hold tasks dispatched")
    else:
        logger.debug("SWEEP: No new openings found")

    return f"Checked {len(dates)} dates, found {new_openings} new openings"
