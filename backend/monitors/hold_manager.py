"""
Vatican Slot Hold Manager
=========================
Holds slots via /api/visit/recap and keeps sessions alive indefinitely.
One session per held slot — keepalive pings every 5 min.
"""
import logging
import requests
import time
from django.utils import timezone

logger = logging.getLogger(__name__)

BASE = 'https://tickets.museivaticani.va'
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'Origin': BASE,
    'Content-Type': 'application/json',
}


def _make_session(jsessionid=None, ticketmv=None):
    """Create a requests session, optionally restoring saved cookies."""
    s = requests.Session()
    if jsessionid:
        s.cookies.set('JSESSIONID', jsessionid, domain='tickets.museivaticani.va')
    if ticketmv:
        s.cookies.set('ticketmv', ticketmv, domain='tickets.museivaticani.va')
    return s


def _get_services(session, slot_id, ticket_id, visitors):
    """Fetch services (pre-sale fees) for a slot."""
    try:
        r = session.get(f'{BASE}/api/visit/services', params={
            'lang': 'it', 'visitId': slot_id,
            'visitTypeId': ticket_id, 'visitorNum': str(visitors)
        }, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get('services', [])
    except Exception as e:
        logger.warning(f"Could not fetch services: {e}")
    return []


def _build_recap_body(slot_id, ticket_id, visitors, services):
    """Build the recap POST body with correct ticket/service IDs."""
    # Standard ticket IDs from Vatican (Biglietto Intero=60, Ridotto=61, Prevendita=58)
    # These are stable across sessions
    body = {
        "visitId": slot_id,
        "visitTypeId": ticket_id,
        "visitorNum": visitors,
        "lang": "it",
        "tickets": [{"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": visitors}],
        "additionalCosts": {},
        "services": []
    }
    # Add pre-sale fee if present
    for svc in services:
        svc_id = svc.get('id', 58)
        svc_name = svc.get('name', 'Diritti di Prevendita')
        svc_price = svc.get('price', 5)
        body["additionalCosts"][f"service-0"] = {
            "id": svc_id, "name": svc_name, "price": svc_price, "quantity": visitors
        }
        body["services"].append({"id": svc_id, "name": svc_name, "price": svc_price, "quantity": visitors})
        break  # only first service
    return body


def hold_slot(task, date, slot_id, slot_time, ticket_id, ticket_name, visitors, proxy_str=None):
    """
    Hold a Vatican slot via /api/visit/recap.
    Returns HeldSlot instance or None on failure.
    """
    from .models import HeldSlot

    logger.info(f"🔒 Attempting to hold slot {slot_id} ({slot_time}) on {date} for {task.agency.name}")

    # Build fresh session
    s = requests.Session()
    req_headers = {**HEADERS}
    if proxy_str:
        s.proxies = {'http': proxy_str, 'https': proxy_str}

    # Init session via homepage
    try:
        s.get(f'{BASE}/home', headers=req_headers, timeout=10)
    except Exception as e:
        logger.warning(f"Homepage init failed: {e}")

    # Get fresh ticket_id via search API (IDs change daily)
    try:
        r = s.get(f'{BASE}/api/search/resultPerTag', params={
            'lang': 'it', 'visitorNum': str(visitors), 'visitDate': date,
            'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
        }, headers=req_headers, timeout=10)
        fresh_ticket = next(
            (t for t in r.json().get('visits', []) if 'ingresso' in t.get('name', '').lower()),
            None
        )
        if fresh_ticket:
            ticket_id = fresh_ticket['id']
            logger.info(f"  Fresh ticket_id: {ticket_id}")
    except Exception as e:
        logger.warning(f"Could not refresh ticket_id: {e}")

    # Get services
    services = _get_services(s, slot_id, ticket_id, visitors)

    # Build recap body
    body = _build_recap_body(slot_id, ticket_id, visitors, services)

    # Call recap — this is the hold
    try:
        r2 = s.post(f'{BASE}/api/visit/recap', json=body, headers=req_headers, timeout=10)
        if r2.status_code != 200:
            logger.error(f"❌ Recap failed: {r2.status_code} | {r2.text[:200]}")
            return None

        recap_data = r2.json()
        total_price = recap_data.get('total', 0)
        recap_id = recap_data.get('recapId') or recap_data.get('id') or ''
        logger.info(f"✅ Slot held! Total: €{total_price} | recapId: {recap_id} | {recap_data.get('visitDateTime')}")

    except Exception as e:
        logger.error(f"❌ Recap exception: {e}")
        return None

    # Save cookies
    jsessionid = s.cookies.get('JSESSIONID', '')
    ticketmv = s.cookies.get('ticketmv', '')

    if not jsessionid:
        logger.error("❌ No JSESSIONID after recap — hold may not be valid")
        return None

    # Build payment URL via our redirect endpoint (avoids ;jsessionid= browser warning)
    import os
    base_url = os.getenv('NGROK_DOMAIN', 'hyperkinetic-unsplendorously-jessi.ngrok-free.dev')
    payment_url = f"https://{base_url}/api/v1/holds/{{HOLD_ID}}/checkout/"  # placeholder, updated after save

    # Save to DB
    held = HeldSlot.objects.create(
        task=task,
        date=date,
        slot_id=slot_id,
        slot_time=slot_time,
        ticket_id=str(ticket_id),
        ticket_name=ticket_name,
        visitors=visitors,
        total_price=total_price,
        jsessionid=jsessionid,
        ticketmv=ticketmv,
        recap_id=recap_id,
        status='held',
        payment_url=payment_url,
    )

    # Update payment_url now that we have the hold ID
    held.payment_url = f"https://{os.getenv('NGROK_DOMAIN', 'hyperkinetic-unsplendorously-jessi.ngrok-free.dev')}/api/v1/holds/{held.id}/checkout/"
    held.save(update_fields=['payment_url'])

    logger.info(f"✅ HeldSlot #{held.id} created for {task.agency.name} | {date} {slot_time}")
    return held


def keepalive_slot(held_slot):
    """
    Ping Vatican API to keep the session alive.
    Returns True if session is still valid, False if expired.
    """
    from .models import HeldSlot

    s = _make_session(held_slot.jsessionid, held_slot.ticketmv)

    try:
        # Lightweight ping — isAgency endpoint
        r = s.get(f'{BASE}/api/config/isAgency', headers=HEADERS, timeout=10)
        if r.status_code == 200:
            held_slot.last_keepalive_at = timezone.now()
            held_slot.save(update_fields=['last_keepalive_at'])
            logger.info(f"💓 Keepalive OK for HeldSlot #{held_slot.id} ({held_slot.date} {held_slot.slot_time})")
            return True
        else:
            logger.warning(f"⚠️ Keepalive ping returned {r.status_code} for HeldSlot #{held_slot.id}")
            # Try recap again to re-establish hold
            return _re_hold(held_slot, s)
    except Exception as e:
        logger.error(f"❌ Keepalive failed for HeldSlot #{held_slot.id}: {e}")
        return False


def _re_hold(held_slot, session=None):
    """Re-call recap on existing session to refresh hold."""
    from .models import HeldSlot

    if session is None:
        session = _make_session(held_slot.jsessionid, held_slot.ticketmv)

    services = _get_services(session, held_slot.slot_id, held_slot.ticket_id, held_slot.visitors)
    body = _build_recap_body(held_slot.slot_id, held_slot.ticket_id, held_slot.visitors, services)

    try:
        r = session.post(f'{BASE}/api/visit/recap', json=body, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            held_slot.last_keepalive_at = timezone.now()
            held_slot.save(update_fields=['last_keepalive_at'])
            logger.info(f"🔄 Re-hold OK for HeldSlot #{held_slot.id}")
            return True
        else:
            logger.warning(f"⚠️ Re-hold failed {r.status_code}: {r.text[:150]}")
            return False
    except Exception as e:
        logger.error(f"❌ Re-hold exception: {e}")
        return False


def release_slot(held_slot):
    """Mark a held slot as released (session will expire naturally)."""
    from .models import HeldSlot
    held_slot.status = 'released'
    held_slot.released_at = timezone.now()
    held_slot.save(update_fields=['status', 'released_at'])
    logger.info(f"🔓 Released HeldSlot #{held_slot.id} ({held_slot.date} {held_slot.slot_time})")
