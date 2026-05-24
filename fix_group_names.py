#!/usr/bin/env python3
"""
Fix Telegram group names in database to match actual Telegram names
"""
import os, sys, django, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import TelegramGroup
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def fix_names():
    bot = Bot(token=BOT_TOKEN)
    
    print("=" * 80)
    print("FIXING TELEGRAM GROUP NAMES")
    print("=" * 80)
    print()
    
    groups = TelegramGroup.objects.all()
    
    for group in groups:
        print(f"Checking: {group.chat_title} ({group.chat_id})")
        
        try:
            # Get actual chat info from Telegram
            chat = await bot.get_chat(group.chat_id)
            actual_title = chat.title
            actual_type = chat.type
            
            if group.chat_title != actual_title:
                print(f"  ⚠️  Name mismatch!")
                print(f"     Database: '{group.chat_title}'")
                print(f"     Telegram: '{actual_title}'")
                print(f"  ✅ Updating...")
                
                group.chat_title = actual_title
                group.chat_type = actual_type
                group.save()
                
                print(f"  ✅ Updated to: '{actual_title}'")
            else:
                print(f"  ✅ Name correct: '{actual_title}'")
            
            # Get member count
            if chat.type in ['group', 'supergroup']:
                member_count = await bot.get_chat_member_count(group.chat_id)
                print(f"     Members: {member_count}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            print()
    
    print("=" * 80)
    print("UPDATED GROUP LIST")
    print("=" * 80)
    print()
    
    for group in TelegramGroup.objects.all():
        print(f"✅ {group.chat_title}")
        print(f"   Chat ID: {group.chat_id}")
        print(f"   Agency: {group.agency.name if group.agency else 'None'}")
        print()

asyncio.run(fix_names())

print("=" * 80)
print("NOW SEARCH FOR BIG BUS")
print("=" * 80)
print()
print("To find Big Bus group:")
print("1. Send any message in the Big Bus Telegram group")
print("2. The bot will receive an update")
print("3. Check bot logs or run /pending command")
print()
print("Or if you know the chat ID, add it manually:")
print("  python backend/manage.py shell")
print("  >>> from monitors.models import TelegramGroup, Agency")
print("  >>> agency = Agency.objects.create(name='Big Bus', plan='agency')")
print("  >>> TelegramGroup.objects.create(")
print("  ...     chat_id='-XXXXXXXXX',")
print("  ...     chat_title='Big Bus',")
print("  ...     chat_type='group',")
print("  ...     agency=agency,")
print("  ...     status='approved',")
print("  ...     notification_enabled=True")
print("  ... )")
print()
