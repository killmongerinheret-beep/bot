
import os
import sys
import redis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_queue_health():
    """Check the health of Redis queues."""
    try:
        redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        
        logger.info(f"Connected to Redis at {redis_url}")
        
        queues = ['vatican', 'colosseum', 'celery']
        
        print("\n" + "="*40)
        print("📊 QUEUE HEALTH REPORT")
        print("="*40)
        
        for q in queues:
            length = r.llen(q)
            status = "✅ HEALTHY" if length < 50 else "⚠️ WARNING" if length < 100 else "❌ CRITICAL"
            print(f"Queue '{q}': {length} tasks - {status}")
            
        print("="*40 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Failed to check queues: {e}")
        return False

if __name__ == "__main__":
    check_queue_health()
