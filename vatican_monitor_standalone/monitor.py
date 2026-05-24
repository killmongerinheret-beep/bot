#!/usr/bin/env python3
"""
Vatican Standalone Monitor
==========================
Lightweight replacement for worker_vatican + beat on Hetzner.
Reads MonitorTask + TelegramGroup from the same Postgres DB as the main bot.
No Celery, no Redis, no browser — just Search API + Telegram notifications.

Run:
    pip install -r requirements.txt
    python monitor.py

Env vars (same as main .env):
    DATABASE_URL          — postgres://user:pass@host:5432/db
    TELEGRAM_BOT_TOKEN    — bot token
    ADMIN_TELEGRAM_IDS    — comma-separated admin IDs
    POLL_INTERVAL_SECONDS — how often to check (default 30)
"""

import os
import asyncio
import logging
import json
import time
from datetime import datetime, date as date_type
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict, Tuple

import requests
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS      = [i.strip() for i in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",") if i.strip()]
DATABASE_URL   = os.getenv("DATABASE_URL")
POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))
NOTIFY_COOLDOWN = int(os.getenv("NOTIFY_COOLDOWN_SECONDS", "3600"))  # 1hr — same as main bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("monitor.log"),
    ]
)
log = logging.getLogger(__name__)

ROME = ZoneInfo("Europe/Rome")

# ── In-memory state (replaces Redis) ─────────────────────────────────────────
# { "ticket_state:{task_id}:{date}": "available"|"closed" }
# { "alert_cooldown:{task_id}:{date}": timestamp }
_state: Dict[str, str] = {}
_cooldowns: Dict[str, float] = {}


def state_get(key: str) -> Optional[str]:
    return _state.get(key)


def state_set(key: str, value: str):
    _state[key] = value


def cooldown_active(key: str) -> bool:
    ts = _cooldowns.get(key)
    if ts is None:
        return False
    return time.time() < ts


def cooldown_set(key: str, seconds: int):
    _cooldowns[key] = time.time() + seconds


# ── Postgres ──────────────────────────────────────────────────────────────────

def db_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def get_active_tasks() -> List[Dict]:
    """Return all active Vatican MonitorTask rows with their agency info."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    t.id, t.dates, t.visitors, t.ticket_type, t.ticket_name,
                    t.language, t.preferred_times, t.notification_mode, t.tier,
                    t.agency_id,
                    a.name AS agency_name,
                    a.telegram_chat_id AS agency_chat_id
                FROM monitors_monitortask t
                JOIN monitors_agency a ON a.id = t.agency_id
                WHERE t.is_active = TRUE AND t.site = 'vatican'
            """)
            return cur.fetchall()


def get_approved_groups(agency_id: int) -> List[Dict]:
    """Return approved TelegramGroup rows for an agency."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT chat_id, chat_title
                FROM monitors_telegramgroup
                WHERE agency_id = %s
                  AND status = 'approved'
                  AND notification_enabled = TRUE
            """, (agency_id,))
            return cur.fetchall()


def update_task_checked(task_id: int, status: str, summary: str):
    """Update last_checked / last_status on the task."""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE monitors_monitortask
                SET last_checked = NOW(), last_status = %s, last_result_summary = %s
                WHERE id = %s
            """, (status, summary, task_id))
        conn.commit()


# ── Vatican API ───────────────────────────────────────────────────────────────

class VaticanAPI:
    SEARCH_URL    = "https://tickets.museivaticani.va/api/search/resultPerTag"
    TIMEAVAIL_URL = "https://tickets.museivaticani.va/api/visit/timeavail"
    HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://tickets.museivaticani.va/",
        "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
    }

    def __init__(self):
        self.session = requests.Session()

    def resolve_tickets(self, visit_date: str, visitors: int, ticket_type: int = 0) -> List[Dict]:
        tag = "MV-Biglietti" if ticket_type == 0 else "MV-Visite-Guidate"
        try:
            r = self.session.get(self.SEARCH_URL, params={
                "lang": "it", "visitorNum": str(visitors), "visitDate": visit_date,
                "area": "1", "who": "", "page": "0", "tag": tag,
            }, headers=self.HEADERS, timeout=10)
            if r.status_code != 200:
                return []
            return [
                {"id": str(t["id"]), "name": t.get("name", ""), "availability": t.get("availability", "")}
                for t in r.json().get("visits", [])
            ]
        except Exception as e:
            log.warning(f"Search API error: {e}")
            return []

    def match_ticket(self, tickets: List[Dict], ticket_type: int = 0, language: str = "") -> Optional[str]:
        if not tickets:
            return None
        skip = ["lunch", "pranzo", "pellegrinaggi", "scuole", "gruppi"]
        keywords = (
            ["musei", "vaticani", "biglietti", "ingresso"] if ticket_type == 0
            else ["visita", "guidata", "guided", "tour", language.lower()]
        )
        best_score, best_id = 0, None
        for t in tickets:
            name = t["name"].lower()
            if any(s in name for s in skip):
                continue
            score = sum(1 for kw in keywords if kw in name)
            if score > best_score:
                best_score, best_id = score, t["id"]
        if best_id:
            return best_id
        # absolute fallback
        for t in tickets:
            if not any(s in t["name"].lower() for s in ["lunch", "pranzo"]):
                return t["id"]
        return None

    def check_timeavail(self, ticket_id: str, visit_date: str, visitors: int, language: str = "") -> List[str]:
        try:
            r = self.session.get(self.TIMEAVAIL_URL, params={
                "lang": "it", "visitLang": language,
                "visitTypeId": ticket_id, "visitorNum": str(visitors), "visitDate": visit_date,
            }, headers=self.HEADERS, timeout=10)
            if r.status_code != 200:
                return []
            return [
                s["time"] for s in r.json().get("timetable", [])
                if s.get("availability") == "AVAILABLE"
            ]
        except Exception as e:
            log.warning(f"Timeavail error: {e}")
            return []

    def get_slots(self, visit_date: str, visitors: int, ticket_type: int = 0,
                  language: str = "") -> Tuple[List[str], str]:
        """Returns (slot_times, ticket_name)."""
        tickets = self.resolve_tickets(visit_date, visitors, ticket_type)
        if not tickets:
            return [], ""
        ticket_id = self.match_ticket(tickets, ticket_type, language)
        if not ticket_id:
            return [], ""
        matched = next((t for t in tickets if t["id"] == ticket_id), {})
        name = matched.get("name", "Unknown")
        if matched.get("availability") in ("SOLD_OUT", "NOT_ALLOWED"):
            return [], name
        slots = self.check_timeavail(ticket_id, visit_date, visitors, language)
        return slots, name


# ── Notification ──────────────────────────────────────────────────────────────

def build_booking_link(date: str, visitors: int, ticket_name: str) -> str:
    try:
        day, month, year = date.split("/")
        dt = datetime(int(year), int(month), int(day), tzinfo=ROME)
        ts = int(dt.timestamp() * 1000)
        slug = "MV-Visite-Guidate" if any(x in ticket_name for x in ["Guidat", "Guided"]) else "MV-Biglietti"
        return f"https://tickets.museivaticani.va/home/fromtag/{visitors}/{ts}/{slug}/1"
    except Exception:
        return "https://tickets.museivaticani.va/home"


def format_notification(date: str, ticket_name: str, slots: List[str],
                         preferred_times: List[str], visitors: int,
                         language: Optional[str]) -> str:
    preferred_set = set(preferred_times or [])
    now = datetime.now(ROME).strftime("%H:%M:%S")
    lang_info = f" ({language})" if language else ""
    link = build_booking_link(date, visitors, ticket_name)

    lines = [
        "🎉 TICKETS JUST OPENED!",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📅 DATE: {date}",
        f"🎫 TICKET: {ticket_name}{lang_info}",
        f"👥 VISITORS: {visitors}",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"⏰ Checked at: {now} Rome time",
        "",
        "⏱ Available times:",
    ]
    for s in slots:
        star = " ⭐" if s in preferred_set else ""
        lines.append(f"  • {s}{star}")
    lines += ["", f"🔗 Book now: {link}"]
    return "\n".join(lines)


def send_telegram(chat_id: str, message: str) -> bool:
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        log.error(f"Telegram send error to {chat_id}: {e}")
        return False


# ── Date helpers ──────────────────────────────────────────────────────────────

def normalize_date(raw: str) -> Optional[str]:
    """Convert any format to DD/MM/YYYY, return None if past."""
    try:
        if "-" in raw and raw[4] == "-":
            dt = datetime.strptime(raw, "%Y-%m-%d").date()
        elif "/" in raw:
            dt = datetime.strptime(raw, "%d/%m/%Y").date()
        else:
            return None
        if dt < date_type.today():
            return None
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return None


# ── Main poll loop ────────────────────────────────────────────────────────────

def run_poll_cycle(api: VaticanAPI):
    tasks = get_active_tasks()
    if not tasks:
        log.debug("No active tasks")
        return

    # Group by (date, ticket_type, language, visitors) to avoid duplicate API calls
    groups: Dict[Tuple, Dict] = {}
    for task in tasks:
        dates_raw = task["dates"] or []
        if isinstance(dates_raw, str):
            try:
                dates_raw = json.loads(dates_raw)
            except Exception:
                dates_raw = [dates_raw]

        for raw_date in dates_raw:
            date = normalize_date(raw_date)
            if not date:
                continue
            ticket_type = task["ticket_type"] or 0
            language = task["language"] or ""
            visitors = task["visitors"] or 1
            key = (date, ticket_type, language, visitors)
            if key not in groups:
                groups[key] = {
                    "date": date, "ticket_type": ticket_type,
                    "language": language, "visitors": visitors,
                    "tasks": [],
                }
            groups[key]["tasks"].append(task)

    log.info(f"🔄 Checking {len(groups)} unique date/type combos across {len(tasks)} tasks")

    for key, group in groups.items():
        date      = group["date"]
        ttype     = group["ticket_type"]
        language  = group["language"]
        visitors  = group["visitors"]

        slots, ticket_name = api.get_slots(date, visitors, ttype, language)
        is_available = len(slots) > 0

        for task in group["tasks"]:
            task_id = task["id"]
            state_key   = f"ticket_state:{task_id}:{date}"
            cooldown_key = f"alert_cooldown:{task_id}:{date}"

            prev_state   = state_get(state_key)
            is_first     = prev_state is None
            was_open     = prev_state == "available"

            # Seed first-check as closed (no alert on first run)
            if is_first:
                state_set(state_key, "available" if is_available else "closed")
                log.info(f"Task #{task_id} {date}: baseline={'open' if is_available else 'closed'}")
                update_task_checked(task_id, "available" if is_available else "sold_out", "")
                continue

            new_state = "available" if is_available else "closed"
            state_set(state_key, new_state)

            status_changed_to_open = is_available and not was_open
            should_alert = status_changed_to_open and not cooldown_active(cooldown_key)

            if should_alert:
                cooldown_set(cooldown_key, NOTIFY_COOLDOWN)
                log.info(f"🔔 Task #{task_id} {date}: CLOSED→OPEN — notifying")

                preferred = task["preferred_times"] or []
                if isinstance(preferred, str):
                    try:
                        preferred = json.loads(preferred)
                    except Exception:
                        preferred = []

                msg = format_notification(
                    date, ticket_name or "Musei Vaticani", slots,
                    preferred, visitors, language or None
                )

                # Send to all approved groups for this agency
                groups_sent = 0
                for grp in get_approved_groups(task["agency_id"]):
                    if send_telegram(grp["chat_id"], msg):
                        groups_sent += 1

                # Fallback to agency direct chat_id
                if groups_sent == 0 and task["agency_chat_id"]:
                    send_telegram(task["agency_chat_id"], msg)

                log.info(f"✅ Notified {groups_sent} groups for agency '{task['agency_name']}'")

            elif is_available and was_open:
                log.debug(f"Task #{task_id} {date}: still open, no alert")
            elif not is_available:
                log.debug(f"Task #{task_id} {date}: closed")

            update_task_checked(
                task_id,
                "available" if is_available else "sold_out",
                json.dumps({"slots": slots, "ticket": ticket_name})
            )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")

    log.info(f"🚀 Vatican Standalone Monitor starting (poll every {POLL_INTERVAL}s)")
    log.info(f"   DB: {DATABASE_URL.split('@')[-1]}")  # log host only, not creds

    api = VaticanAPI()

    while True:
        try:
            run_poll_cycle(api)
        except Exception as e:
            log.error(f"Poll cycle error: {e}", exc_info=True)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
