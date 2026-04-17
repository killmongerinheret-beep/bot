import redis
import json
import base64
import time

# Configuration (matches docker-compose)
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
# This must match the api_key of the agency you want to test
# Check 'agent_config.json' for the agency_key your agent is using
AGENCY_KEY = 'wor-agency-key' 

# Use decode_responses=True to handle strings easily
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def trigger_test_browser():
    # Construct a dummy slot info
    # format: d_api|pref_time|slot_id|visitors|total|adult|child
    slot_info = "15/06/2026|09:00|2026*1234|2|?|2|0"
    slot_b64 = base64.b64encode(slot_info.encode()).decode()
    
    job = {
        'data': f'open_browser_slot:{slot_b64}',
        'user': 'Test Runner',
        'auto': True,
        'task_id': 999
    }
    
    key = f"browser_pending_{AGENCY_KEY}"
    
    # Push to list
    existing = r.get(key)
    pending = []
    if existing:
        try:
            pending = json.loads(existing)
        except:
            pending = []
            
    pending.append(job)
    r.set(key, json.dumps(pending), ex=1800)
    
    print(f"✅ Job injected into Redis key: {key}")
    print(f"Agent should pick it up within 0.5 seconds if running.")

if __name__ == "__main__":
    trigger_test_browser()
