#!/bin/bash
# Vatican Bot Health Monitor
# Run this every 5 minutes via cron

# Check if workers are running
if ! docker-compose ps worker_vatican | grep -q "Up"; then
    echo "[ALERT] worker_vatican is down - restarting..."
    docker-compose restart worker_vatican
fi

# Check if beat is running
if ! docker-compose ps beat | grep -q "Up"; then
    echo "[ALERT] beat is down - restarting..."
    docker-compose restart beat
fi

# Check Redis
if ! docker-compose ps redis | grep -q "Up"; then
    echo "[ALERT] redis is down - restarting..."
    docker-compose restart redis
fi

# Check for stuck tasks (no checks in 10 minutes)
python3 << 'EOF'
import os, sys, django
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import CheckResult
from django.utils import timezone
from datetime import timedelta

ten_min_ago = timezone.now() - timedelta(minutes=10)
recent = CheckResult.objects.filter(check_time__gte=ten_min_ago).count()

if recent == 0:
    print("[ALERT] No checks in 10 minutes - workers may be stuck")
    sys.exit(1)
else:
    print(f"[OK] {recent} checks in last 10 minutes")
    sys.exit(0)
EOF

if [ $? -ne 0 ]; then
    echo "[ACTION] Restarting worker_vatican..."
    docker-compose restart worker_vatican
fi
