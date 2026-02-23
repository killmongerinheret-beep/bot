#!/usr/bin/env python3
"""
Vatican Bot Launcher for Windows
=================================
Runs the God-Tier Vatican Monitor continuously with automatic crash recovery.

Usage:
    python run_vatican_bot.py
    python run_vatican_bot.py --dates 01/03/2026 02/03/2026
    python run_vatican_bot.py --type guided --interval 45
"""

import asyncio
import sys
import os
import logging
import signal
import time
from datetime import datetime

# Ensure the worker_vatican directory is in the path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKER_DIR = os.path.join(SCRIPT_DIR, "worker_vatican")
sys.path.insert(0, WORKER_DIR)
sys.path.insert(0, SCRIPT_DIR)

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
except ImportError:
    pass

from god_tier_monitor_v2 import GodTierVaticanMonitorV2

# Configure logging to both console and file
LOG_FILE = os.path.join(SCRIPT_DIR, "vatican_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
    ]
)
logger = logging.getLogger("VaticanLauncher")


# Default dates to monitor (update these!)
DEFAULT_DATES = [
    "01/03/2026",
    "02/03/2026",
    "03/03/2026",
    "04/03/2026",
    "05/03/2026",
]


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Vatican Bot Launcher")
    parser.add_argument("--dates", nargs="+", default=DEFAULT_DATES, help="Dates to monitor (DD/MM/YYYY)")
    parser.add_argument("--type", choices=["standard", "guided"], default="standard", help="Ticket type")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    return parser.parse_args()


async def run_bot(args):
    """Main bot loop with crash recovery using V2 monitor."""
    ticket_type = 0 if args.type == "standard" else 1
    crash_count = 0
    max_crashes = 50  # Max consecutive crashes before longer cooldown

    logger.info("=" * 70)
    logger.info("🏛️  VATICAN BOT V2 - WINDOWS CONTINUOUS MODE")
    logger.info("=" * 70)
    logger.info(f"📅 Dates: {', '.join(args.dates)}")
    logger.info(f"🎫 Type: {args.type.title()}")
    logger.info(f"⏱️  Interval: {args.interval}s")
    logger.info(f"📝 Log file: {LOG_FILE}")
    logger.info("=" * 70)

    while True:
        try:
            monitor = GodTierVaticanMonitorV2()
            logger.info(f"🌐 Proxies loaded: {len(monitor.proxies)}")

            cycle = 0
            while True:
                cycle += 1
                logger.info(f"\n📍 Cycle {cycle} | {time.strftime('%H:%M:%S')}")
                start_time = time.time()

                for date in args.dates:
                    results = await monitor.check_availability(
                        date_str=date,
                        ticket_type=ticket_type
                    )

                    if results:
                        logger.info(f"✅ {date}: Found availability!")
                        for r in results:
                            slots_str = ", ".join([s['time'] for s in r['slots'][:5]])
                            if len(r['slots']) > 5:
                                slots_str += f" (+{len(r['slots']) - 5} more)"
                            logger.info(f"   🎫 {r['ticket_name']} ({r['language']}): {slots_str}")
                    else:
                        logger.info(f"❌ {date}: No availability")

                elapsed = time.time() - start_time
                sleep_time = max(0, args.interval - elapsed)
                if sleep_time > 0:
                    logger.info(f"💤 Sleeping {sleep_time:.1f}s...")
                    await asyncio.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("👋 Bot stopped by user (Ctrl+C)")
            break
        except Exception as e:
            crash_count += 1
            logger.error(f"💥 CRASH #{crash_count}: {e}")

            if crash_count >= max_crashes:
                cooldown = 300  # 5 minutes
                logger.warning(f"🛑 Too many crashes ({crash_count}). Cooling down for {cooldown}s...")
                await asyncio.sleep(cooldown)
                crash_count = 0
            else:
                # Exponential backoff: 5s, 10s, 15s... up to 60s
                wait_time = min(5 * crash_count, 60)
                logger.info(f"♻️ Restarting in {wait_time}s...")
                await asyncio.sleep(wait_time)

            logger.info("🔄 Restarting bot...")


def main():
    args = parse_args()
    try:
        asyncio.run(run_bot(args))
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")


if __name__ == "__main__":
    main()
