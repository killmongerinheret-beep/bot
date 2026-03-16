#!/usr/bin/env python3
"""Test cache persistence for Vatican monitoring"""
import os
import sys
import django

sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.cache import cache
from monitors.models import MonitorTask

print("=" * 80)
print("CACHE PERSISTENCE TEST")
print("=" * 80)

# Get active tasks
tasks = MonitorTask.objects.filter(is_active=True).order_by('id')[:3]

print(f"\nTesting cache for {tasks.count()} tasks...\n")

for task in tasks:
    date = task.dates[0] if task.dates else "N/A"
    
    # Check current state
    state_key = f"ticket_state:{task.id}:{date}"
    current_state = cache.get(state_key)
    
    print(f"Task #{task.id} ({date}):")
    print(f"  State Key: {state_key}")
    print(f"  Current Cache Value: {current_state}")
    
    # Try to set a test value
    test_value = "test_available"
    cache.set(state_key, test_value, timeout=3600)
    
    # Read it back immediately
    read_back = cache.get(state_key)
    print(f"  Test Write: {test_value}")
    print(f"  Test Read: {read_back}")
    print(f"  Cache Working: {'✅ YES' if read_back == test_value else '❌ NO'}")
    
    # Check cooldown key
    cooldown_key = f"alert_cooldown:{task.id}:{date}"
    cooldown_value = cache.get(cooldown_key)
    print(f"  Cooldown Key: {cooldown_key}")
    print(f"  Cooldown Value: {cooldown_value}")
    print()

print("=" * 80)
print("REDIS CONNECTION TEST")
print("=" * 80)

try:
    # Test basic Redis operations
    cache.set('test_key', 'test_value', timeout=60)
    result = cache.get('test_key')
    print(f"Redis Test: {'✅ WORKING' if result == 'test_value' else '❌ FAILED'}")
    print(f"  Set: test_key = test_value")
    print(f"  Get: {result}")
except Exception as e:
    print(f"❌ Redis Error: {e}")

print("\n" + "=" * 80)
