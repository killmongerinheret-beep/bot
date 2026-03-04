import asyncio
import os
import sys
import json
import logging
import time
import urllib.request
import ssl
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

# Setup path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "worker_vatican"))
sys.path.insert(0, SCRIPT_DIR)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
except ImportError:
    pass

from god_tier_monitor_v2 import GodTierVaticanMonitorV2

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DashboardSync")

# API Base URL
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# SSL Context for bypassing certificate verification (Telegram)
ssl_context = ssl._create_unverified_context()

def api_request(method, url, data=None):
    """Helper for API requests using urllib."""
    req = urllib.request.Request(url, method=method)
    if data:
        body = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
        req.data = body
    
    try:
        # We try with default SSL first for local API, fallback if needed
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status >= 200 and response.status < 300:
                res_body = response.read().decode('utf-8')
                return json.loads(res_body) if res_body else {}
    except Exception as e:
        logger.error(f"   API Error ({method} {url}): {e}")
    return None

def send_telegram(chat_id, message):
    """Send Telegram message using urllib with bypassed SSL cert verification."""
    if not TELEGRAM_TOKEN:
        logger.warning("⚠️ No TELEGRAM_BOT_TOKEN found in environment")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        req = urllib.request.Request(url, method="POST")
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')
        # Use the unverified SSL context
        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
            res_data = json.loads(response.read().decode())
            if response.status == 200 and res_data.get("ok"):
                logger.info(f"✅ Telegram signal sent to {chat_id}")
                return True
            else:
                logger.error(f"❌ Telegram API error: {res_data}")
                return False
    except Exception as e:
        logger.error(f"❌ Failed to send Telegram: {e}")
        return False

def get_vatican_deep_link(date_str, visitors, ticket_type):
    """Generate a direct booking link for the Vatican site."""
    try:
        if "/" in date_str:
            day, month, year = date_str.split('/')
            dt_obj = datetime(int(year), int(month), int(day))
        else:
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        rome = ZoneInfo("Europe/Rome")
        midnight = dt_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=rome)
        ts = int(midnight.timestamp() * 1000)
        slug = "MV-Biglietti" if ticket_type == 0 else "MV-Visite-Guidate"
        return f"https://tickets.museivaticani.va/home/fromtag/{visitors}/{ts}/{slug}/1"
    except Exception as e:
        logger.error(f"Error generating deep link: {e}")
        return "https://tickets.museivaticani.va/"

async def sync_loop(interval=30):
    """Main loop to sync bot results with the backend dashboard."""
    monitor = GodTierVaticanMonitorV2()
    
    logger.info("=" * 70)
    logger.info("🛰️  VATICAN DASHBOARD SYNCHRONIZER + ALERTS (v2.1)")
    logger.info("=" * 70)
    logger.info(f"🔗 Target API: {API_BASE}")
    logger.info(f"⏱️  Sync Interval: {interval}s")
    logger.info(f"🤖 Telegram: {'Configured' if TELEGRAM_TOKEN else 'MISSING'}")
    if TELEGRAM_TOKEN:
        logger.info(f"🆔 Bot Token: {TELEGRAM_TOKEN[:10]}...")
    logger.info("=" * 70)

    # State tracking for notifications
    last_known_status = {}
    last_known_slots = {}

    while True:
        try:
            # 1. Fetch active tasks from backend
            logger.info("📥 Fetching active tasks from backend...")
            tasks = api_request("GET", f"{API_BASE}/tasks/?is_active=True")
            
            if tasks is None:
                logger.error("❌ Failed to fetch tasks.")
                await asyncio.sleep(10)
                continue
            
            # Filter for Vatican tasks
            vatican_tasks = [t for t in tasks if t.get('site') == 'vatican']
            if not vatican_tasks:
                logger.info("💤 No active Vatican tasks found.")
                await asyncio.sleep(interval)
                continue
            
            # 2. Group tasks by date AND visitors to optimize checks
            group_to_tasks = {}
            for task in vatican_tasks:
                visitors = task.get('visitors', 2)
                for date in task.get('dates', []):
                    key = (date, visitors)
                    if key not in group_to_tasks:
                        group_to_tasks[key] = []
                    group_to_tasks[key].append(task)
            
            # 3. Perform availability checks
            for (date_str, v_count), group in group_to_tasks.items():
                # Convert ISO date (2026-03-28) to DD/MM/YYYY for the bot
                bot_date = date_str
                if "-" in date_str and len(date_str) == 10:
                    parts = date_str.split("-")
                    bot_date = f"{parts[2]}/{parts[1]}/{parts[0]}"
                
                logger.info(f"🔍 Checking availability for {date_str} (bot: {bot_date}) (visitors: {v_count}) ({len(group)} tasks)...")
                
                types_needed = set(t.get('ticket_type', 0) for t in group)
                results_by_type = {}
                for t_type in types_needed:
                    results = await monitor.check_availability(
                        date_str=bot_date,
                        ticket_type=t_type,
                        visitors=v_count
                    )
                    results_by_type[t_type] = results or []
                
                # 4. Push results back to backend for each task
                for task in group:
                    t_id_match = str(task.get('ticket_id')) if task.get('ticket_id') else None
                    t_name_raw = task.get('ticket_name', '').lower()
                    t_type = task.get('ticket_type', 0)
                    
                    # 1. Harvest all IDs known to the monitor for this date
                    # This helps us identify the ticket even if it's currently sold out
                    id_cache = monitor.session_cache.get("ids_cache", {})
                    all_harvested = id_cache.get(bot_date, id_cache.get("__ALL__", []))

                    # Fuzzy match keywords for this task
                    keywords = []
                    # Standard / Entry
                    if any(x in t_name_raw for x in ["standard", "entry", "biglietti", "admission", "ingresso"]):
                        keywords.append("biglietti d'ingresso")
                        keywords.append("admission tickets")
                    
                    # Guided
                    if any(x in t_name_raw for x in ["guided", "visite guidate"]):
                        keywords.append("visite guidate")
                        keywords.append("guided tours")
                    
                    if "singoli" in t_name_raw or "individuals" in t_name_raw:
                        keywords.append("singoli")
                        keywords.append("individuals")
                    
                    if "gruppi" in t_name_raw or "groups" in t_name_raw:
                        keywords.append("gruppi")
                        keywords.append("groups")

                    # 2. Find matches among ALL harvested IDs (for status reporting)
                    matches = []
                    match_method = "None"
                    matched_ids = []
                    
                    for h in all_harvested:
                        h_id = str(h.get('id', ''))
                        h_name = h.get('name', '').lower()
                        
                        is_match = False
                        if t_id_match and t_id_match == h_id:
                            is_match = True
                            match_method = "ID"
                        else:
                            for kw in keywords:
                                if kw in h_name:
                                    is_match = True
                                    match_method = "Keyword"
                                    break
                        
                        if is_match:
                            matches.append(h)
                            matched_ids.append(h_id)

                    # 3. Sum available slots from actual results
                    found_slots = []
                    results_for_type = results_by_type.get(t_type, [])
                    for r in results_for_type:
                        if str(r.get('ticket_id', '')) in matched_ids:
                            found_slots.extend(r.get('slots', []))
                    
                    status = "available" if found_slots else "sold_out"
                    
                    if status == "sold_out":
                        logger.info(f"   \u2705 Task {task['id']} ({date_str}): SOLD_OUT (0 slots) [Match: {match_method}]")
                    else:
                        logger.info(f"   \u2705 Task {task['id']} ({date_str}): AVAILABLE ({len(found_slots)} slots) [Match: {match_method}]")
                    
                    unique_slots = []
                    seen = set()
                    for s in found_slots:
                        t = s.get('time', s) if isinstance(s, dict) else s
                        if t not in seen:
                            seen.add(t)
                            unique_slots.append({'time': t, 'availability': 'AVAILABLE'})
                    
                    # Sort slots chronologically to avoid false "changed" detections
                    slot_times = sorted([s['time'] for s in unique_slots])
                    
                    current_status = 'available' if unique_slots else 'sold_out'
                    task_id = task['id']
                    
                    # 5. Handle Notifications on state change or slot change
                    prev_status = last_known_status.get(task_id, task.get('last_status', 'unknown'))
                    prev_slots = last_known_slots.get(task_id, [])
                    
                    slots_changed = slot_times != prev_slots
                    
                    if current_status == 'available' and (prev_status != 'available' or slots_changed):
                        logger.info(f"🚀 [ALERT] Task {task_id} notification trigger (new={current_status}, changed={slots_changed})")
                        chat_id = "-5245239270"
                        
                        visitors = task.get('visitors', 2)
                        deep_link = get_vatican_deep_link(date_str, visitors, t_type)
                        
                        msg = f"🎉 *VATICAN TICKETS FOUND!*\n\n"
                        msg += f"📅 *Date:* {date_str}\n"
                        msg += f"👤 *Visitors:* {visitors}\n"
                        msg += f"🎫 *Ticket:* {task.get('ticket_name')}\n"
                        msg += f"🕐 *Slots:* {', '.join(slot_times)}\n"
                        msg += f"\n🔗 [Book Directly]({deep_link})"
                        
                        if send_telegram(chat_id, msg):
                            last_known_slots[task_id] = slot_times
                    
                    if current_status == 'sold_out':
                        last_known_slots[task_id] = [] # Clear so next availability always notifies
                    
                    last_known_status[task_id] = current_status
                    
                    # 6. Push to DB
                    patch_data = {
                        "last_status": current_status,
                        "last_checked": datetime.utcnow().isoformat() + "Z"
                    }
                    api_request("PATCH", f"{API_BASE}/tasks/{task_id}/", patch_data)
                    
                    result_data = {
                        "task": task_id,
                        "status": current_status,
                        "details": {
                            "date": date_str,
                            "slots": unique_slots,
                            "ticket_name": task.get('ticket_name'),
                            "check_method": "sync_bot_v2_fix"
                        }
                    }
                    api_request("POST", f"{API_BASE}/results/", result_data)
                    
                    logger.info(f"   ✅ Task {task_id} ({date_str}): {current_status.upper()} ({len(unique_slots)} slots)")

            logger.info(f"⌛ Cycle complete. Sleeping {interval}s...")
            await asyncio.sleep(interval)
            
        except Exception as e:
            logger.error(f"💥 Error in sync loop: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    # Test chat ID
    test_chat = "-5245239270"
    logger.info(f"🔔 Sending startup test notification to {test_chat}...")
    success = send_telegram(test_chat, "🚀 *Vatican Sync Bot (Fix Applied)!*\nIf you see this, SSL and Env issues are resolved.")
    
    if not success:
        logger.error("❌ TEST NOTIFICATION FAILED. Check logs above.")
    
    asyncio.run(sync_loop())
