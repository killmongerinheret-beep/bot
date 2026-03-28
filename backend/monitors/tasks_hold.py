"""
Hold Manager Celery Tasks — 3-Tier System
==========================================
Tier 1 — notify:  detect → Telegram alert → user books themselves
Tier 2 — hold:    detect → grab slot → send payment link → user pays in browser
Tier 3 — snipe:   detect → grab slot → auto-fill buyer details → auto-pay
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name="keepalive_held_slots", queue="vatican")
def keepalive_held_slots():
    """Every 5 min — ping all active holds to keep Vatican sessions alive."""
    from .models import HeldSlot
    from .hold_manager import keepalive_slot

    active_holds = HeldSlot.objects.filter(status='held')
    if not active_holds.exists():
        return "No active holds"

    logger.info(f"💓 Keepalive for {active_holds.count()} held slots")
    ok = expired = 0

    for hold in active_holds:
        cutoff = timezone.now() - timedelta(hours=3)  # 3 hour hold window
        if hold.last_keepalive_at < cutoff:
            hold.status = 'expired'
            hold.save(update_fields=['status'])
            logger.warning(f"⏰ HeldSlot #{hold.id} expired")
            expired += 1
            continue

        if keepalive_slot(hold):
            ok += 1
        else:
            hold.status = 'expired'
            hold.save(update_fields=['status'])
            expired += 1

    return f"Keepalive: {ok} alive, {expired} expired"


@shared_task(name="auto_hold_slot", queue="vatican")
def auto_hold_slot(task_id, date, slot_id, slot_time, ticket_id, ticket_name, visitors):
    """
    Triggered when a slot opens.
    Routes to correct tier based on task.tier:
      notify → just send Telegram alert
      hold   → grab slot + send payment link
      snipe  → grab slot + auto-pay with stored buyer profile
    """
    from .models import MonitorTask, HeldSlot

    try:
        task = MonitorTask.objects.select_related('agency').get(id=task_id)
    except MonitorTask.DoesNotExist:
        logger.error(f"Task {task_id} not found")
        return "Task not found"

    tier = task.tier  # 'notify', 'hold', 'snipe'
    logger.info(f"🎯 Slot opened — tier={tier} | {date} {slot_time} | {task.agency.name}")

    if tier == 'notify':
        _send_notify_alert(task, date, slot_time, ticket_name, visitors)
        return f"Notified: {date} {slot_time}"

    # hold or snipe — both need to grab the slot first
    existing = HeldSlot.objects.filter(task=task, date=date, slot_id=slot_id, status='held').first()
    if existing:
        logger.info(f"⏭️ Already held: HeldSlot #{existing.id}")
        return f"Already held: #{existing.id}"

    from .hold_manager import hold_slot
    held = hold_slot(
        task=task, date=date, slot_id=slot_id, slot_time=slot_time,
        ticket_id=ticket_id, ticket_name=ticket_name, visitors=visitors,
    )

    if not held:
        logger.error(f"❌ Hold failed — falling back to notify")
        _send_notify_alert(task, date, slot_time, ticket_name, visitors, hold_failed=True)
        return "Hold failed"

    if tier == 'hold':
        _send_hold_notification(task, held)
        return f"Held #{held.id} | {date} {slot_time}"

    if tier == 'snipe':
        _send_hold_notification(task, held)  # notify immediately
        # Then attempt auto-pay
        result = _attempt_snipe(task, held)
        return f"Snipe: {result}"

    return "Unknown tier"


def _send_notify_alert(task, date, slot_time, ticket_name, visitors, hold_failed=False):
    """Tier 1 — simple availability alert."""
    from .models import TelegramGroup
    from .notification_utils import send_telegram_signal
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo('Europe/Rome')).strftime('%H:%M:%S')
    warning = "\n⚠️ Auto-hold failed — book manually ASAP!" if hold_failed else ""

    msg = (
        f"🎉 TICKETS AVAILABLE!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Date: {date}\n"
        f"⏰ Time: {slot_time}\n"
        f"🎫 {ticket_name}\n"
        f"👥 Visitors: {visitors}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{warning}\n"
        f"🔗 Book now:\n"
        f"https://tickets.museivaticani.va/home\n\n"
        f"🕐 Detected: {now} Rome time"
    )
    _send_to_groups(task, msg)


def _send_hold_notification(task, held):
    """Tier 2 — slot held, here's your payment link."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo('Europe/Rome')).strftime('%H:%M:%S')
    import os
    base_url = os.getenv('NGROK_DOMAIN', 'hyperkinetic-unsplendorously-jessi.ngrok-free.dev')
    checkout_url = f"https://{base_url}/api/v1/holds/{held.id}/checkout/"

    msg = (
        f"🔒 SLOT HELD — PAY NOW!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Date: {held.date}\n"
        f"⏰ Time: {held.slot_time}\n"
        f"🎫 {held.ticket_name}\n"
        f"👥 Visitors: {held.visitors}\n"
        f"💶 Total: €{held.total_price}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Slot locked — nobody else can book it.\n\n"
        f"💳 Open this link to pay:\n"
        f"{checkout_url}\n\n"
        f"⚠️ Use this link directly — do NOT open Vatican site separately.\n\n"
        f"🕐 Held at: {now} Rome time | Hold ID: #{held.id}"
    )
    _send_to_groups(task, msg)


def _attempt_snipe(task, held):
    """
    Tier 3 — auto-pay using stored BuyerProfile.
    Needs: reCAPTCHA token (2captcha) + buyer profile.
    """
    from .models import BuyerProfile
    import requests

    # Check buyer profile exists
    try:
        profile = BuyerProfile.objects.get(agency=task.agency)
    except BuyerProfile.DoesNotExist:
        logger.error(f"❌ No BuyerProfile for {task.agency.name} — snipe aborted")
        _send_to_groups(task,
            f"⚠️ Snipe failed: No buyer profile set for {task.agency.name}.\n"
            f"Please set up buyer details to use snipe mode.\n"
            f"Hold #{held.id} is still active — pay manually via the link above."
        )
        return "No buyer profile"

    # Check card details
    if not profile.card_number:
        logger.error(f"❌ No card details for {task.agency.name} — snipe aborted")
        _send_to_groups(task,
            f"⚠️ Snipe failed: No card details stored.\n"
            f"Hold #{held.id} still active — pay manually."
        )
        return "No card details"

    # Get reCAPTCHA token
    recaptcha_token = _solve_recaptcha()
    if not recaptcha_token:
        logger.error("❌ reCAPTCHA solve failed — snipe aborted, hold still active")
        _send_to_groups(task,
            f"⚠️ Snipe failed: Could not solve reCAPTCHA.\n"
            f"Hold #{held.id} still active — pay manually via the checkout link."
        )
        return "reCAPTCHA failed"

    # Build reservation body
    BASE = 'https://tickets.museivaticani.va'
    HEADERS = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'{BASE}/',
        'Origin': BASE,
        'Content-Type': 'application/json',
    }

    s = requests.Session()
    s.cookies.set('JSESSIONID', held.jsessionid, domain='tickets.museivaticani.va')
    if held.ticketmv:
        s.cookies.set('ticketmv', held.ticketmv, domain='tickets.museivaticani.va')

    body = {
        "recaptcha": recaptcha_token,
        "lang": "it",
        "recapId": held.recap_id or '',
        "visitorNum": held.visitors,
        "visitId": held.slot_id,
        "visitTypeId": int(held.ticket_id),
        "tickets": [{"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": held.visitors}],
        "services": [{"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": held.visitors}],
        "representativeUser": profile.to_representative_user(),
        "participantUser": profile.to_participant_list(held.visitors),
        "gdpr": [{"id": 1, "check": True}, {"id": 3, "check": True}],
    }

    try:
        r = s.post(f'{BASE}/api/visit/reservation', json=body, headers=HEADERS, timeout=15)
        logger.info(f"Reservation response: {r.status_code} | {r.text[:300]}")

        if r.status_code == 200:
            res_data = r.json()
            # Vatican response: {"total":"2500","referenceOrder":"...","epay":{"url":"https://epay.catholica.va/..."}}
            epay_url = (
                res_data.get('epay', {}).get('url') or
                res_data.get('paymentUrl') or
                res_data.get('redirectUrl') or
                ''
            )
            held.status = 'paying'
            held.payment_url = epay_url or held.payment_url
            held.save(update_fields=['status', 'payment_url'])

            _send_to_groups(task,
                f"✅ RESERVATION CONFIRMED!\n\n"
                f"📅 {held.date} {held.slot_time}\n"
                f"👥 {held.visitors} visitors | €{held.total_price}\n\n"
                f"💳 Complete payment:\n{epay_url or held.payment_url}"
            )
            return f"Reservation OK — payment pending"
        else:
            logger.error(f"Reservation failed: {r.status_code} | {r.text[:200]}")
            _send_to_groups(task,
                f"⚠️ Auto-reservation failed ({r.status_code}).\n"
                f"Hold #{held.id} still active — pay manually."
            )
            return f"Reservation failed: {r.status_code}"

    except Exception as e:
        logger.error(f"Snipe exception: {e}")
        return f"Exception: {e}"


def _solve_recaptcha():
    """
    Solve Cloudflare Turnstile for Vatican checkout.
    Sitekey: 0x4AAAAAAB2Edz1zEK7o5Rj1
    Returns token string or None.
    Requires TWOCAPTCHA_API_KEY in environment.
    """
    import os, requests, time

    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    if not api_key:
        logger.warning("No TWOCAPTCHA_API_KEY set — snipe mode unavailable")
        return None

    # Vatican uses Cloudflare Turnstile (not reCAPTCHA v3)
    site_key = '0x4AAAAAAB2Edz1zEK7o5Rj1'
    page_url = 'https://tickets.museivaticani.va/home/checkout'

    try:
        # Submit Turnstile task
        r = requests.post('https://2captcha.com/in.php', data={
            'key': api_key,
            'method': 'turnstile',
            'sitekey': site_key,
            'pageurl': page_url,
            'json': 1,
        }, timeout=10)
        data = r.json()
        if data.get('status') != 1:
            logger.error(f"2captcha submit failed: {data}")
            return None

        task_id = data['request']
        logger.info(f"2captcha Turnstile task submitted: {task_id}")

        # Poll for result (up to 2 min)
        for _ in range(24):
            time.sleep(5)
            r2 = requests.get('https://2captcha.com/res.php', params={
                'key': api_key, 'action': 'get', 'id': task_id, 'json': 1
            }, timeout=10)
            res = r2.json()
            if res.get('status') == 1:
                logger.info("✅ Turnstile solved")
                return res['request']
            if res.get('request') != 'CAPCHA_NOT_READY':
                logger.error(f"2captcha error: {res}")
                return None

        logger.error("2captcha timeout")
        return None

    except Exception as e:
        logger.error(f"Turnstile solve exception: {e}")
        return None


def _send_to_groups(task, msg):
    """Send message to all approved groups for this agency."""
    from .models import TelegramGroup
    from .notification_utils import send_telegram_signal

    groups = TelegramGroup.objects.filter(
        agency=task.agency, status='approved', notification_enabled=True
    )
    for g in groups:
        send_telegram_signal(g.chat_id, msg)
