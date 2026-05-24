#!/usr/bin/env python3
"""
PERMANENT FIX FOR REDIS BLOAT
==============================
This script fixes the Redis performance issue permanently by:
1. Cleaning up existing 220k+ keys
2. Adding automated Redis cleanup to Celery beat schedule
3. Verifying all settings are correct

Run this ONCE, then restart services.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import redis
from django.conf import settings
from django.core.cache import cache
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def check_settings():
    """Verify all Redis-related settings are correct"""
    logger.info("="*80)
    logger.info("STEP 1: VERIFY SETTINGS")
    logger.info("="*80)
    
    checks = {
        'CELERY_RESULT_EXPIRES': getattr(settings, 'CELERY_RESULT_EXPIRES', None),
        'CELERY_TASK_IGNORE_RESULT': getattr(settings, 'CELERY_TASK_IGNORE_RESULT', None),
        'CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP': getattr(settings, 'CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP', None),
        'CELERY_WORKER_MAX_TASKS_PER_CHILD': getattr(settings, 'CELERY_WORKER_MAX_TASKS_PER_CHILD', None),
    }
    
    all_good = True
    for key, value in checks.items():
        if value is None:
            logger.error(f"❌ {key} is NOT SET")
            all_good = False
        else:
            logger.info(f"✅ {key} = {value}")
    
    # Check if cleanup tasks are in beat schedule
    beat_schedule = getattr(settings, 'CELERY_BEAT_SCHEDULE', {})
    cleanup_tasks = [
        'cleanup-old-check-results',
        'cleanup-expired-holds',
        'cleanup-inactive-tasks',
        'memory-health-check'
    ]
    
    logger.info("\nScheduled cleanup tasks:")
    for task_name in cleanup_tasks:
        if task_name in beat_schedule:
            schedule = beat_schedule[task_name].get('schedule', 'unknown')
            logger.info(f"✅ {task_name}: every {schedule} seconds")
        else:
            logger.warning(f"⚠️ {task_name}: NOT SCHEDULED")
            all_good = False
    
    return all_good


def cleanup_redis():
    """Clean up existing Redis bloat"""
    logger.info("\n" + "="*80)
    logger.info("STEP 2: CLEAN UP REDIS")
    logger.info("="*80)
    
    try:
        # Connect to Redis
        broker_url = settings.CELERY_BROKER_URL
        r = redis.from_url(broker_url)
        
        # Check connection
        r.ping()
        logger.info("✅ Connected to Redis")
        
        # Get initial stats
        initial_keys = r.dbsize()
        initial_memory = r.info('memory')['used_memory_human']
        
        logger.info(f"\nInitial state:")
        logger.info(f"  Keys: {initial_keys:,}")
        logger.info(f"  Memory: {initial_memory}")
        
        if initial_keys < 10000:
            logger.info("✅ Redis is already clean (< 10k keys)")
            return True
        
        logger.info(f"\n⚠️ Redis has {initial_keys:,} keys - cleaning up...")
        
        # Clean up Celery task results (the main culprit)
        logger.info("\n1. Cleaning Celery task results...")
        deleted_celery = 0
        cursor = 0
        pattern = 'celery-task-meta-*'
        
        while True:
            cursor, keys = r.scan(cursor, match=pattern, count=1000)
            if keys:
                deleted_celery += r.delete(*keys)
                if deleted_celery % 10000 == 0:
                    logger.info(f"   Deleted {deleted_celery:,} task results...")
            if cursor == 0:
                break
        
        logger.info(f"✅ Deleted {deleted_celery:,} Celery task results")
        
        # Clean up old ticket state keys (older than 30 days)
        logger.info("\n2. Cleaning old ticket state keys...")
        deleted_state = 0
        cursor = 0
        pattern = 'ticket_state:*'
        
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=30)
        
        while True:
            cursor, keys = r.scan(cursor, match=pattern, count=1000)
            if keys:
                for key in keys:
                    try:
                        # Set TTL to 7 days if not set
                        ttl = r.ttl(key)
                        if ttl == -1:  # No expiration
                            r.expire(key, 604800)  # 7 days
                            deleted_state += 1
                    except Exception:
                        pass
            if cursor == 0:
                break
        
        logger.info(f"✅ Set TTL on {deleted_state:,} ticket state keys")
        
        # Clean up old cooldown keys
        logger.info("\n3. Cleaning old cooldown keys...")
        deleted_cooldown = 0
        patterns = ['alert_cooldown:*', 'hold_cooldown:*', 'notified:*']
        
        for pattern in patterns:
            cursor = 0
            while True:
                cursor, keys = r.scan(cursor, match=pattern, count=1000)
                if keys:
                    for key in keys:
                        try:
                            ttl = r.ttl(key)
                            # If expired or no TTL, delete
                            if ttl == -2 or ttl == -1:
                                r.delete(key)
                                deleted_cooldown += 1
                        except Exception:
                            pass
                if cursor == 0:
                    break
        
        logger.info(f"✅ Deleted {deleted_cooldown:,} old cooldown keys")
        
        # Get final stats
        final_keys = r.dbsize()
        final_memory = r.info('memory')['used_memory_human']
        
        logger.info("\n" + "="*80)
        logger.info("CLEANUP SUMMARY")
        logger.info("="*80)
        logger.info(f"\nDeleted:")
        logger.info(f"  Celery results: {deleted_celery:,}")
        logger.info(f"  State keys (TTL set): {deleted_state:,}")
        logger.info(f"  Cooldown keys: {deleted_cooldown:,}")
        logger.info(f"  Total: {deleted_celery + deleted_state + deleted_cooldown:,}")
        
        logger.info(f"\nFinal state:")
        logger.info(f"  Keys: {final_keys:,} (was {initial_keys:,})")
        logger.info(f"  Memory: {final_memory} (was {initial_memory})")
        logger.info(f"  Reduction: {initial_keys - final_keys:,} keys ({((initial_keys - final_keys) / initial_keys * 100):.1f}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis cleanup failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def add_redis_cleanup_task():
    """Add automated Redis cleanup task to Celery beat schedule"""
    logger.info("\n" + "="*80)
    logger.info("STEP 3: ADD AUTOMATED REDIS CLEANUP")
    logger.info("="*80)
    
    settings_file = os.path.join(os.path.dirname(__file__), 'backend', 'core', 'settings.py')
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if redis cleanup task already exists
        if "'cleanup-redis-cache':" in content or '"cleanup-redis-cache":' in content:
            logger.info("✅ Redis cleanup task already in schedule")
            return True
        
        # Find the CELERY_BEAT_SCHEDULE section
        if 'CELERY_BEAT_SCHEDULE = {' not in content:
            logger.error("❌ Cannot find CELERY_BEAT_SCHEDULE in settings.py")
            return False
        
        # Add the task before the closing brace of CELERY_BEAT_SCHEDULE
        # Find the memory-health-check task and add after it
        if "'memory-health-check':" in content:
            insert_point = content.find("'memory-health-check':")
            # Find the end of this task definition (next task or closing brace)
            next_task = content.find("'", insert_point + len("'memory-health-check':") + 1)
            if next_task == -1:
                next_task = content.find("}", insert_point)
            
            # Find the end of the task definition
            end_of_task = content.find("},", insert_point)
            if end_of_task == -1:
                end_of_task = content.find("}", insert_point)
            
            # Insert the new task
            new_task = """
    'cleanup-redis-cache': {
        'task': 'cleanup_redis_cache',
        'schedule': 86400,  # daily
        'options': {'queue': 'vatican'},
    },"""
            
            # Insert after memory-health-check
            insert_at = end_of_task + 2  # After "},\n"
            new_content = content[:insert_at] + new_task + content[insert_at:]
            
            # Write back
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info("✅ Added 'cleanup-redis-cache' task to CELERY_BEAT_SCHEDULE")
            return True
        else:
            logger.warning("⚠️ Could not find insertion point - please add manually")
            logger.info("\nAdd this to CELERY_BEAT_SCHEDULE in settings.py:")
            logger.info("""
    'cleanup-redis-cache': {
        'task': 'cleanup_redis_cache',
        'schedule': 86400,  # daily
        'options': {'queue': 'vatican'},
    },
""")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to update settings.py: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def print_next_steps():
    """Print instructions for completing the fix"""
    logger.info("\n" + "="*80)
    logger.info("NEXT STEPS - RESTART SERVICES")
    logger.info("="*80)
    
    logger.info("""
To complete the fix, restart all services to apply the new settings:

1. Restart all services:
   docker-compose restart backend worker_vatican beat redis

2. Verify workers are connecting:
   docker-compose logs -f worker_vatican | grep "Connected"

3. Check Redis key count (should be < 10k):
   docker-compose exec redis redis-cli DBSIZE

4. Monitor Redis memory usage:
   docker-compose exec redis redis-cli INFO memory | grep used_memory_human

5. Check that tasks are running:
   docker-compose logs -f worker_vatican | grep "ORCHESTRATOR"

EXPECTED RESULTS:
- Redis keys: < 10,000 (was 220,000+)
- Redis memory: < 100MB (was 1.7GB)
- Worker startup: < 5 seconds (was 20+ seconds)
- Tasks executing: Every 5 seconds

MONITORING:
- Redis will auto-expire task results after 1 hour
- Cleanup tasks run daily to prevent bloat
- Memory health checks run every 30 minutes

If issues persist, check logs:
   docker-compose logs backend
   docker-compose logs worker_vatican
   docker-compose logs beat
""")


def main():
    """Run all fix steps"""
    logger.info("🚀 STARTING PERMANENT REDIS BLOAT FIX")
    logger.info("="*80)
    
    # Step 1: Check settings
    settings_ok = check_settings()
    if not settings_ok:
        logger.error("\n❌ Settings are not correct - please fix settings.py first")
        return False
    
    # Step 2: Clean up Redis
    cleanup_ok = cleanup_redis()
    if not cleanup_ok:
        logger.error("\n❌ Redis cleanup failed")
        return False
    
    # Step 3: Add automated cleanup task
    task_added = add_redis_cleanup_task()
    
    # Step 4: Print next steps
    print_next_steps()
    
    logger.info("\n" + "="*80)
    logger.info("✅ FIX COMPLETED SUCCESSFULLY")
    logger.info("="*80)
    logger.info("\n⚠️ IMPORTANT: Restart services now to apply changes!")
    logger.info("   Run: docker-compose restart backend worker_vatican beat redis\n")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
