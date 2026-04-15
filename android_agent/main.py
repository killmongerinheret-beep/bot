"""
Vatican Android Agent
=====================
Runs on Android as a background service.
- Polls server for snipe jobs
- Holds Vatican slots via recap API (no browser needed for hold)
- Opens Chrome on Android for checkout when triggered
- Sends heartbeat so you see it in /agent status on Telegram

Install on Android:
  1. Install Termux from F-Droid (NOT Play Store)
  2. Run: pkg install python git
  3. Run: pip install requests kivy
  4. Run: python main.py --agent android-1

OR build as APK:
  See buildozer.spec in this folder
"""
import asyncio
import json
import os
import platform
import subprocess
import sys
import time
import threading
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('android-agent')

# ── Config ────────────────────────────────────────────────────────────────────
def _load_config():
    base = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(base, 'agent_config.json')
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

_cfg = _load_config()

SERVER_URL   = _cfg.get('server_url',    'https://hydrabot.it')
BOT_TOKEN    = _cfg.get('bot_token',     '')
ADMIN_CHAT   = _cfg.get('admin_chat_id', '')
AGENT_ID     = _cfg.get('agent_id',      f"android-{platform.node()}")
BASE         = 'https://tickets.museivaticani.va'
PROXIES      = {'http': None, 'https': None}
# ─────────────────────────────────────────────────────────────────────────────

IS_ANDROID = os.path.exists('/data/data/com.termux')


def send_telegram(msg: str):
    if not BOT_TOKEN or not ADMIN_CHAT:
        return
    try:
        requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            json={'chat_id': ADMIN_CHAT, 'text': msg, 'parse_mode': 'Markdown'},
            timeout=5, proxies=PROXIES
        )
    except Exception:
        pass


def heartbeat():
    """Send heartbeat to server every 30s."""
    while True:
        try:
            requests.post(
                f'{SERVER_URL}/api/v1/agent-heartbeat/',
                json={'agent_id': AGENT_ID, 'hostname': platform.node(), 'platform': 'android'},
                timeout=5, proxies=PROXIES
            )
        except Exception:
            pass
        time.sleep(30)


def get_jobs():
    """Long-poll server for jobs targeted at this agent."""
    try:
        r = requests.get(
            f'{SERVER_URL}/api/v1/browser-pending/?wait=1&agent_id={AGENT_ID}',
            timeout=12, proxies=PROXIES
        )
        if r.status_code == 200:
            return r.json().get('requests', [])
    except Exception:
        pass
    return []


# ── Vatican API ───────────────────────────────────────────────────────────────

def get_fresh_session_and_ticket(date: str, visitors: int):
    """Get JSESSIONID + ticket_id from Vatican Search API."""
    s = requests.Session()
    try:
        s.get(f'{BASE}/home', timeout=8, proxies=PROXIES)
    except Exception:
        pass
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(visitors), 'visitDate': date,
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers={'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}, timeout=10, proxies=PROXIES)
    if r.status_code != 200:
        return None, None, None
    ticket = next((v for v in r.json().get('visits', [])
                   if 'musei vaticani' in v.get('name', '').lower()
                   and 'ingresso' in v.get('name', '').lower()), None)
    if not ticket:
        return None, None, None
    return s, str(ticket['id']), s.cookies.get('JSESSIONID', '')


def do_recap(session, slot_id, ticket_id, visitors, adult_count, child_count):
    """Call Vatican recap API to lock a slot."""
    body = {
        "visitId": str(slot_id),
        "visitTypeId": int(ticket_id),
        "visitorNum": int(visitors),
        "lang": "it",
        "tickets": [
            {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": str(adult_count)},
            {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": str(child_count)},
        ],
        "additionalCosts": {
            "service-0": {"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": int(visitors)}
        },
        "services": [{"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": int(visitors)}]
    }
    try:
        r = session.post(f'{BASE}/api/visit/recap', json=body, headers={
            'Accept': 'application/json', 'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest', 'Referer': f'{BASE}/'
        }, timeout=15, proxies=PROXIES)
        if r.status_code == 200:
            return r.json().get('recapId') or 'ok'
    except Exception as e:
        logger.error(f"Recap error: {e}")
    return None


# ── Chrome on Android ─────────────────────────────────────────────────────────

def open_chrome_android(url: str):
    """Open a URL in Chrome on Android."""
    try:
        # Method 1: via am (Android Activity Manager) — works in Termux with root or ADB
        subprocess.run([
            'am', 'start', '-a', 'android.intent.action.VIEW',
            '-d', url,
            '-n', 'com.android.chrome/com.google.android.apps.chrome.Main'
        ], timeout=5)
        return True
    except Exception:
        pass
    try:
        # Method 2: via termux-open-url (Termux:API addon)
        subprocess.run(['termux-open-url', url], timeout=5)
        return True
    except Exception:
        pass
    try:
        # Method 3: via xdg-open (if available)
        subprocess.run(['xdg-open', url], timeout=5)
        return True
    except Exception:
        pass
    return False


def open_checkout_android(slot: dict):
    """
    Open Vatican checkout in Chrome on Android.
    Fills form via JavaScript injection after page loads.
    User solves Turnstile manually on the phone screen.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    date = slot.get('date', '')
    slot_time = slot.get('slot_time', '')
    visitors = int(slot.get('visitors', 1))
    hold_id = slot.get('id')

    rome = ZoneInfo('Europe/Rome')
    day, month, year = date.split('/')
    ts = int(datetime(int(year), int(month), int(day), 0, 0, 0, tzinfo=rome).timestamp() * 1000)
    entry_url = f'{BASE}/home/visit/{visitors}/{ts}/1'

    logger.info(f"Opening Chrome on Android: {entry_url}")
    opened = open_chrome_android(entry_url)

    if opened:
        send_telegram(
            f"📱 *Chrome opened on Android `{AGENT_ID}`*\n"
            f"📅 {date} {slot_time} | 👥 {visitors}v\n\n"
            f"Navigate to the ticket, select time, fill form.\n"
            f"Turnstile needs manual solve on phone screen."
        )
    else:
        send_telegram(
            f"❌ Could not open Chrome on `{AGENT_ID}`\n"
            f"Install Termux:API and run: `pkg install termux-api`"
        )


# ── Hold worker ───────────────────────────────────────────────────────────────

class HoldWorker(threading.Thread):
    """Holds one Vatican slot via recap heartbeat — no browser needed."""

    def __init__(self, slot: dict):
        super().__init__(daemon=True)
        self.slot = slot
        self.running = True
        self.date = slot.get('date', '')
        self.slot_time = slot.get('slot_time', '')
        self.slot_id = str(slot.get('slot_id', ''))
        self.visitors = int(slot.get('visitors', 1))
        self.adult_count = int(slot.get('adult_count', self.visitors))
        self.child_count = int(slot.get('child_count', 0))
        self.hold_id = slot.get('id')

    def run(self):
        logger.info(f"Hold worker: {self.date} {self.slot_time}")
        session, ticket_id, jsessionid = get_fresh_session_and_ticket(self.date, self.visitors)
        if not session:
            logger.error(f"Could not get Vatican session for {self.date}")
            return

        recap_id = do_recap(session, self.slot_id, ticket_id, self.visitors, self.adult_count, self.child_count)
        if not recap_id:
            logger.error(f"Initial recap failed for {self.date} {self.slot_time}")
            return

        logger.info(f"✅ HELD: {self.date} {self.slot_time} (recap={recap_id})")
        send_telegram(f"🔒 *Slot held on `{AGENT_ID}`*\n📅 {self.date} {self.slot_time} | 👥 {self.visitors}v")

        last_heartbeat = time.time()
        while self.running:
            time.sleep(5)
            if time.time() - last_heartbeat >= 240:  # 4 minutes
                # Refresh ticket_id (Vatican changes IDs)
                _, fresh_tid, _ = get_fresh_session_and_ticket(self.date, self.visitors)
                if fresh_tid:
                    ticket_id = fresh_tid
                recap_id = do_recap(session, self.slot_id, ticket_id, self.visitors, self.adult_count, self.child_count)
                if recap_id:
                    last_heartbeat = time.time()
                    logger.info(f"💓 Heartbeat OK: {self.date} {self.slot_time}")
                else:
                    logger.warning(f"Heartbeat failed — refreshing session")
                    session, ticket_id, _ = get_fresh_session_and_ticket(self.date, self.visitors)
                    if not session:
                        logger.error(f"Session refresh failed — hold lost")
                        break
                    last_heartbeat = time.time()

    def stop(self):
        self.running = False


# ── Job processor ─────────────────────────────────────────────────────────────

def process_job(job: dict):
    """Process a job from the server queue."""
    import base64
    data = job.get('data', '')
    logger.info(f"Job received: {data[:60]}")

    slot = None

    if data.startswith('open_browser:'):
        parts = data.split(':')
        hold_id = parts[1]
        if len(parts) >= 3:
            try:
                raw = base64.b64decode(parts[2]).decode()
                s = raw.split('|')
                slot = {
                    'id': hold_id,
                    'date': s[0],
                    'slot_time': s[1],
                    'slot_id': s[2] if len(s) > 2 else '',
                    'visitors': int(s[3]) if len(s) > 3 else 1,
                    'adult_count': int(s[5]) if len(s) > 5 else int(s[3]) if len(s) > 3 else 1,
                    'child_count': int(s[6]) if len(s) > 6 else 0,
                }
            except Exception as e:
                logger.error(f"Could not decode job: {e}")

    elif data.startswith('open_browser_slot:'):
        try:
            raw = base64.b64decode(data.split(':', 1)[1]).decode()
            s = raw.split('|')
            slot = {
                'id': None,
                'date': s[0], 'slot_time': s[1],
                'slot_id': s[2] if len(s) > 2 else '',
                'visitors': int(s[3]) if len(s) > 3 else 1,
                'adult_count': int(s[3]) if len(s) > 3 else 1,
                'child_count': 0,
            }
        except Exception as e:
            logger.error(f"Could not decode slot job: {e}")

    if not slot:
        logger.warning("Could not parse job — skipping")
        return

    # On Android: open Chrome for manual checkout
    # The hold is already created server-side, we just need to complete payment
    open_checkout_android(slot)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Vatican Android Agent')
    parser.add_argument('--agent', default=None, help='Agent name (default: android-hostname)')
    args = parser.parse_args()

    global AGENT_ID
    if args.agent:
        AGENT_ID = args.agent

    logger.info(f"🤖 Vatican Android Agent started")
    logger.info(f"Agent ID : {AGENT_ID}")
    logger.info(f"Server   : {SERVER_URL}")
    logger.info(f"Platform : {'Android/Termux' if IS_ANDROID else 'Desktop'}")

    send_telegram(f"🤖 Android Agent `{AGENT_ID}` started\nPlatform: {'Android' if IS_ANDROID else 'Desktop'}")

    # Start heartbeat thread
    hb = threading.Thread(target=heartbeat, daemon=True)
    hb.start()

    # Main job loop
    processed = set()
    while True:
        try:
            jobs = get_jobs()
            for job in jobs:
                job_key = job.get('data', '')[:80]
                if job_key in processed:
                    continue
                processed.add(job_key)
                # Process in background thread so we keep polling
                t = threading.Thread(target=process_job, args=(job,), daemon=True)
                t.start()
        except KeyboardInterrupt:
            logger.info("Stopped.")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(2)


if __name__ == '__main__':
    main()
