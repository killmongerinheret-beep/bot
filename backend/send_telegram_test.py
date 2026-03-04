import os
import json
import urllib.parse
import urllib.request

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TEST_TELEGRAM_CHAT_ID', '-5186315205')
TEXT = os.environ.get('TEST_TELEGRAM_TEXT', 'Test from TravelAgentBot')

if not TOKEN:
    print("❌ No TELEGRAM_BOT_TOKEN in env")
    raise SystemExit(1)

def send_message(token, chat_id, text):
    base = f"https://api.telegram.org/bot{token}/sendMessage"
    qs = urllib.parse.urlencode({'chat_id': chat_id, 'text': text})
    url = f"{base}?{qs}"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("✅ Telegram response:", data.get('ok'), data.get('description'))
    except Exception as e:
        if hasattr(e, 'read'):
            body = e.read().decode('utf-8', 'ignore')
            print("❌ Telegram error body:", body)
        raise

if __name__ == "__main__":
    send_message(TOKEN, CHAT_ID, TEXT)
