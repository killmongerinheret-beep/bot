import asyncio
import logging
import sys
import os

# Setup paths
sys.path.append('/app')
sys.path.append('/app/worker_vatican')

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VerifyFeb13")

from worker_vatican.hydra_monitor import HydraBot

async def verify():
    print("\n--- STARTING VERIFICATION FOR FEB 13 ---")
    
    bot = HydraBot(use_proxies=True)
    target_date = "13/02/2026"
    bot.target_dates = [target_date]
    
    # 1. Check Standard Tickets
    print(f"\n🎫 Checking STANDARD Tickets for {target_date}...")
    results_std = await bot.run_once(ticket_type=0, language="ENG")
    print(f"Standard Result: {results_std}")
    
    # 2. Check Guided Tours
    print(f"\n🎫 Checking GUIDED Tickets for {target_date}...")
    results_guided = await bot.run_once(ticket_type=1, language="ENG")
    print(f"Guided Result: {results_guided}")

    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(verify())
