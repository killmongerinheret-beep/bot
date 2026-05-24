#!/usr/bin/env python3
"""
Check which Telegram groups the bot is actually connected to (live check via API)
"""
import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set in .env file")
    exit(1)

print("=" * 80)
print("CHECKING BOT'S LIVE TELEGRAM CONNECTIONS")
print("=" * 80)
print()
print(f"Bot Token: {BOT_TOKEN[:20]}...")
print()

async def check_bot_groups():
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Get bot info
        me = await bot.get_me()
        print(f"✅ Bot Connected: @{me.username}")
        print(f"   Name: {me.first_name}")
        print(f"   ID: {me.id}")
        print()
        
        # Get updates to see recent chats
        print("=" * 80)
        print("RECENT CHATS (from bot updates)")
        print("=" * 80)
        print()
        
        updates = await bot.get_updates(limit=100)
        
        if not updates:
            print("⚠️  No recent updates found")
            print("   This means:")
            print("   - Bot hasn't received messages recently")
            print("   - Or updates were already processed")
            print()
        else:
            print(f"Found {len(updates)} recent updates\n")
            
            # Extract unique chats
            chats = {}
            for update in updates:
                if update.message and update.message.chat:
                    chat = update.message.chat
                    chats[chat.id] = {
                        'id': chat.id,
                        'title': chat.title or chat.first_name or 'Unknown',
                        'type': chat.type,
                        'username': chat.username
                    }
                elif update.my_chat_member and update.my_chat_member.chat:
                    chat = update.my_chat_member.chat
                    chats[chat.id] = {
                        'id': chat.id,
                        'title': chat.title or chat.first_name or 'Unknown',
                        'type': chat.type,
                        'username': chat.username
                    }
            
            if chats:
                print("Chats found in recent updates:")
                for chat_id, info in chats.items():
                    print(f"\n  Chat ID: {chat_id}")
                    print(f"  Title: {info['title']}")
                    print(f"  Type: {info['type']}")
                    if info['username']:
                        print(f"  Username: @{info['username']}")
            else:
                print("No chats found in updates")
        
        print()
        print("=" * 80)
        print("TEST SPECIFIC CHAT IDs")
        print("=" * 80)
        print()
        
        # Test known chat IDs
        test_chat_ids = [
            -5245239270,  # WOR
            -5284108537,  # WOR Group 2
        ]
        
        print("Testing known chat IDs from database:")
        for chat_id in test_chat_ids:
            try:
                chat = await bot.get_chat(chat_id)
                print(f"\n✅ Chat ID {chat_id}:")
                print(f"   Title: {chat.title}")
                print(f"   Type: {chat.type}")
                print(f"   Members: {await bot.get_chat_member_count(chat_id) if chat.type in ['group', 'supergroup'] else 'N/A'}")
            except TelegramError as e:
                print(f"\n❌ Chat ID {chat_id}: {e}")
        
        print()
        print("=" * 80)
        print("HOW TO FIND OTHER GROUPS")
        print("=" * 80)
        print()
        print("To find Big Bus and MV2 groups:")
        print()
        print("1. Send a message in those Telegram groups")
        print("   (any message will trigger an update)")
        print()
        print("2. Run this script again to see the chat IDs")
        print()
        print("3. Or check Telegram bot logs for incoming messages")
        print()
        print("4. Or use /start command in those groups")
        print()
        
    except TelegramError as e:
        print(f"❌ Error connecting to Telegram: {e}")
        print()
        print("Possible issues:")
        print("- Invalid bot token")
        print("- Network connection problem")
        print("- Bot was deleted/revoked")

# Run async function
asyncio.run(check_bot_groups())

print()
print("=" * 80)
print("NEXT STEPS")
print("=" * 80)
print()
print("If you know the chat IDs of Big Bus and MV2 groups:")
print()
print("1. Add them manually to database:")
print()
print("   python backend/manage.py shell")
print("   >>> from monitors.models import TelegramGroup, Agency")
print("   >>> agency = Agency.objects.create(name='Big Bus', plan='agency')")
print("   >>> TelegramGroup.objects.create(")
print("   ...     chat_id='-1234567890',  # Replace with actual ID")
print("   ...     chat_title='Big Bus',")
print("   ...     chat_type='group',")
print("   ...     agency=agency,")
print("   ...     status='approved',")
print("   ...     notification_enabled=True")
print("   ... )")
print()
print("2. Or send /start in those groups to trigger auto-registration")
print()
