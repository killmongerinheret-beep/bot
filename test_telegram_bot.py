"""
Quick test to verify Telegram bot token and connection
"""
import os
import sys

# Get token from .env
token = None
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('TELEGRAM_BOT_TOKEN='):
            token = line.split('=', 1)[1].strip()
            break

if not token:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env")
    sys.exit(1)

print(f"✅ Token found: {token[:20]}...")

# Test connection
try:
    import requests
    
    # Get bot info
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            bot_info = data.get('result', {})
            print(f"\n✅ Bot is ACTIVE!")
            print(f"   Name: {bot_info.get('first_name')}")
            print(f"   Username: @{bot_info.get('username')}")
            print(f"   ID: {bot_info.get('id')}")
            
            # Check for pending updates
            url2 = f"https://api.telegram.org/bot{token}/getUpdates"
            response2 = requests.get(url2)
            
            if response2.status_code == 200:
                updates = response2.json().get('result', [])
                print(f"\n📬 Pending messages: {len(updates)}")
                
                if updates:
                    print("\nRecent messages:")
                    for update in updates[-3:]:  # Show last 3
                        msg = update.get('message', {})
                        text = msg.get('text', 'N/A')
                        from_user = msg.get('from', {}).get('first_name', 'Unknown')
                        print(f"   - {from_user}: {text}")
            
            print("\n✅ Bot connection is working!")
            print("\nNext: Make sure bot is running and try /start in Telegram")
        else:
            print(f"❌ Bot API error: {data}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure 'requests' is installed:")
    print("   pip install requests")
