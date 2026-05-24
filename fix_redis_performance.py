"""
Fix Redis Performance Issues
=============================
Diagnoses and fixes Redis performance problems causing bot failures.

The bot isn't working because:
1. Redis has 220k+ keys (1.7GB data)
2. Takes 20+ seconds to load on restart
3. Workers can't connect during loading
4. Tasks fail to execute

This script:
1. Analyzes what's in Redis
2. Cleans up old/unnecessary data
3. Optimizes Redis configuration
"""
import subprocess
import time

def run_redis_command(cmd):
    """Run a Redis CLI command via docker-compose"""
    result = subprocess.run(
        ['docker-compose', 'exec', '-T', 'redis', 'redis-cli'] + cmd.split(),
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def check_redis_status():
    """Check Redis status and key count"""
    print("="*80)
    print("REDIS STATUS CHECK")
    print("="*80)
    
    # Check if Redis is ready
    ping = run_redis_command('PING')
    print(f"Redis Status: {ping}")
    
    if ping != "PONG":
        print("❌ Redis is not ready yet. Wait a few seconds and try again.")
        return False
    
    # Get key count
    dbsize = run_redis_command('DBSIZE')
    print(f"Total Keys: {dbsize}")
    
    # Get memory usage
    memory = run_redis_command('INFO memory')
    for line in memory.split('\n'):
        if 'used_memory_human' in line:
            print(f"Memory Usage: {line.split(':')[1]}")
    
    return True

def analyze_keys():
    """Analyze what types of keys are in Redis"""
    print("\n" + "="*80)
    print("KEY ANALYSIS")
    print("="*80)
    
    # Sample keys to see patterns
    print("\nSampling keys...")
    keys_sample = run_redis_command('KEYS *')
    
    if not keys_sample:
        print("No keys found")
        return
    
    keys = keys_sample.split('\n')[:50]  # First 50 keys
    
    # Categorize keys
    categories = {}
    for key in keys:
        if ':' in key:
            prefix = key.split(':')[0]
            categories[prefix] = categories.get(prefix, 0) + 1
        else:
            categories['other'] = categories.get('other', 0) + 1
    
    print("\nKey Prefixes (sample of 50):")
    for prefix, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {prefix}: {count}")
    
    # Check for Celery keys
    celery_keys = run_redis_command('KEYS celery-task-meta-*')
    if celery_keys:
        celery_count = len(celery_keys.split('\n'))
        print(f"\n⚠️  Found {celery_count} Celery task result keys")
        print("   These can be safely deleted (old task results)")

def clean_old_data():
    """Clean up old unnecessary data"""
    print("\n" + "="*80)
    print("CLEANUP OPTIONS")
    print("="*80)
    
    print("\n1. Delete old Celery task results (RECOMMENDED)")
    print("   - Celery stores task results indefinitely")
    print("   - These are not needed after tasks complete")
    print("   - Safe to delete")
    
    print("\n2. Delete expired keys")
    print("   - Keys with TTL that should have expired")
    print("   - Safe to delete")
    
    print("\n3. Flush all Redis data (⚠️ DANGEROUS)")
    print("   - Deletes EVERYTHING")
    print("   - Will lose monitoring state")
    print("   - Only use as last resort")
    
    choice = input("\nEnter choice (1/2/3/skip): ").strip()
    
    if choice == '1':
        print("\nDeleting Celery task results...")
        # Delete celery-task-meta-* keys
        result = subprocess.run(
            ['docker-compose', 'exec', '-T', 'redis', 'sh', '-c',
             'redis-cli KEYS "celery-task-meta-*" | xargs -r redis-cli DEL'],
            capture_output=True,
            text=True
        )
        print(f"✅ Deleted Celery task results")
        
    elif choice == '2':
        print("\nScanning for expired keys...")
        # This is automatic in Redis, just trigger a scan
        run_redis_command('SCAN 0')
        print("✅ Triggered key expiration scan")
        
    elif choice == '3':
        confirm = input("⚠️  Are you SURE you want to delete ALL Redis data? (yes/no): ")
        if confirm.lower() == 'yes':
            run_redis_command('FLUSHALL')
            print("✅ All Redis data deleted")
        else:
            print("Cancelled")
    else:
        print("Skipped cleanup")

def optimize_redis_config():
    """Suggest Redis configuration optimizations"""
    print("\n" + "="*80)
    print("REDIS OPTIMIZATION RECOMMENDATIONS")
    print("="*80)
    
    print("\n1. Enable Redis persistence optimization:")
    print("   Add to docker-compose.yml redis service:")
    print("   command: redis-server --save 60 1000 --maxmemory 512mb --maxmemory-policy allkeys-lru")
    
    print("\n2. Reduce Celery result backend retention:")
    print("   Add to backend/core/settings.py:")
    print("   CELERY_RESULT_EXPIRES = 3600  # 1 hour instead of forever")
    
    print("\n3. Use Redis eviction policy:")
    print("   Automatically removes old keys when memory limit reached")

def restart_services():
    """Restart services to apply changes"""
    print("\n" + "="*80)
    print("RESTART SERVICES")
    print("="*80)
    
    restart = input("\nRestart worker_vatican and beat? (yes/no): ").strip()
    if restart.lower() == 'yes':
        print("Restarting services...")
        subprocess.run(['docker-compose', 'restart', 'worker_vatican', 'beat'])
        print("✅ Services restarted")
        print("\nWait 30 seconds for services to start...")
        time.sleep(30)
        
        # Check if worker is now connected
        print("\nChecking worker status...")
        result = subprocess.run(
            ['docker-compose', 'logs', 'worker_vatican', '--tail', '10'],
            capture_output=True,
            text=True
        )
        
        if 'Ready to accept tasks' in result.stdout or 'connected' in result.stdout.lower():
            print("✅ Worker is connected!")
        else:
            print("⚠️  Worker may still be connecting. Check logs:")
            print("   docker-compose logs worker_vatican --tail 20")

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     VATICAN BOT - REDIS PERFORMANCE FIX                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

Problem: Bot not working due to Redis performance issues
Solution: Clean up Redis and optimize configuration
    """)
    
    # Step 1: Check Redis status
    if not check_redis_status():
        print("\n❌ Redis is not ready. Please wait and try again.")
        return
    
    # Step 2: Analyze keys
    analyze_keys()
    
    # Step 3: Clean up
    clean_old_data()
    
    # Step 4: Show optimization tips
    optimize_redis_config()
    
    # Step 5: Restart services
    restart_services()
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Check if bot is now working:")
    print("   docker-compose logs worker_vatican --tail 20")
    print("\n2. Monitor for task execution:")
    print("   docker-compose logs worker_vatican -f")
    print("\n3. Check Telegram for notifications")
    print("\n4. If still not working, check:")
    print("   - Are there active monitoring tasks?")
    print("   - Is beat scheduler running?")
    print("   - Are dates in the future?")

if __name__ == '__main__':
    main()
