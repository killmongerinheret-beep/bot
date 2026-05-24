#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from monitors.models import TelegramGroup
import asyncio
from telegram import Bot
from dotenv import load_dotenv
from asgiref.sync import sync_to_async

load_dotenv()

async def main():
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    
    print("=" * 80)
    print("FIXING GROUP NAMES")
    print("=" * 80)
    print()
    
    # Get groups using sync_to_async
    groups = await sync_to_async(list)(TelegramGroup.objects.all())
    
    for group in groups:
        print(f"Checking: {group.chat_title} ({group.chat_id})")
        
        try:
            chat = await bot.get_chat(group.chat_id)
            actual_title = chat.title
            
            if group.chat_title != actual_title:
                print(f"  ⚠️  Database: '{group.chat_title}'")
                print(f"  ✅ Telegram: '{actual_title}'")
                
                group.chat_title = actual_title
                group.chat_type = chat.type
                await sync_to_async(group.save)()
                
                print(f"  ✅ Updated!")
            else:
                print(f"  ✅ Correct: '{actual_title}'")
            
            if chat.type in ['group', 'supergroup']:
                members = await bot.get_chat_member_count(group.chat_id)
                print(f"     Members: {members}")
            print()
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
    
    print("=" * 80)
    print("FINAL GROUP LIST")
    print("=" * 80)
    print()
    
    groups = await sync_to_async(list)(TelegramGroup.objects.all())
    for g in groups:
        print(f"✅ {g.chat_title} ({g.chat_id})")
        print(f"   Agency: {g.agency.name if g.agency else 'None'}")
        print()

asyncio.run(main())
