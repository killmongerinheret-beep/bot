#!/usr/bin/env python
"""Apply runtime optimizations to Vatican bot"""

import os

# 1. Optimize tasks.py - Reduce check frequency
with open('/app/backend/monitors/tasks.py', 'r') as f:
    content = f.read()

# Reduce orchestration frequency from 30s to 60s
content = content.replace('countdown=30', 'countdown=60')

# Reduce concurrency
content = content.replace('CONCURRENT_REQUESTS = 8', 'CONCURRENT_REQUESTS = 4')

with open('/app/backend/monitors/tasks.py', 'w') as f:
    f.write(content)

print("✅ Reduced check frequency to 60s")
print("✅ Reduced concurrency to 4")

# 2. Optimize god_tier_monitor.py
with open('/app/worker_vatican/god_tier_monitor.py', 'r') as f:
    content = f.read()

# Extend session cache to 6 hours
content = content.replace('CACHE_MAX_AGE_HOURS = 4', 'CACHE_MAX_AGE_HOURS = 6')

# Reduce rate limit
content = content.replace('CONCURRENT_REQUESTS = 8', 'CONCURRENT_REQUESTS = 4')
content = content.replace('RATE_LIMIT_RPS = 10', 'RATE_LIMIT_RPS = 5')

with open('/app/worker_vatican/god_tier_monitor.py', 'w') as f:
    f.write(content)

print("✅ Extended session cache to 6 hours")
print("✅ Reduced API rate limit to 5 RPS")

# 3. Optimize hydra_monitor.py - Disable screenshots
with open('/app/worker_vatican/hydra_monitor.py', 'r') as f:
    content = f.read()

# Comment out screenshot lines
content = content.replace(
    'await page.screenshot(',
    '# await page.screenshot('
)
content = content.replace(
    'os.makedirs("/app/screenshots", exist_ok=True)',
    '# os.makedirs("/app/screenshots", exist_ok=True)'
)

with open('/app/worker_vatican/hydra_monitor.py', 'w') as f:
    f.write(content)

print("✅ Disabled screenshots to save disk space")

# 4. Optimize notification cooldown
with open('/app/backend/monitors/notification_utils.py', 'r') as f:
    content = f.read()

# Optional: Reduce cooldown for testing (uncomment if needed)
# content = content.replace('timeout=3600', 'timeout=1800')  # 30 min instead of 1 hour

with open('/app/backend/monitors/notification_utils.py', 'w') as f:
    f.write(content)

print("\n🎉 All optimizations applied!")
print("\nKey improvements:")
print("- Check frequency: 30s → 60s (50% less load)")
print("- Session cache: 4h → 6h (33% fewer browser launches)")
print("- Concurrency: 8 → 4 (less memory)")
print("- Screenshots: Disabled (saves disk)")
print("- Rate limit: 10 → 5 RPS (gentler on Vatican servers)")
