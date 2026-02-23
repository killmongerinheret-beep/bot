#!/bin/bash
# Server Maintenance Script
# Run this daily via cron to keep the server healthy

echo "=== Daily Maintenance: $(date) ==="

# Clean up old Docker containers, images, and volumes
echo "Cleaning Docker..."
docker system prune -f --volumes 2>/dev/null

# Clean up old log files (keep last 7 days)
echo "Cleaning logs..."
find /var/log -name "*.log.*" -mtime +7 -delete 2>/dev/null
find /var/log -name "*.gz" -mtime +7 -delete 2>/dev/null

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is at ${DISK_USAGE}%"
    # Clean up more aggressively
    docker system prune -af --volumes 2>/dev/null
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "WARNING: Memory usage is at ${MEM_USAGE}%"
fi

# Restart containers that are not running
# (docker-compose restart doesn't work well with manual containers)
# Instead, we just ensure restart policies are set

# Verify critical containers are running
for container in travelagentbot-db-1 travelagentbot-redis-1 travelagentbot-backend-1 travelagentbot-worker_vatican-1; do
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "ERROR: $container is not running!"
        # Try to start it if it exists
        docker start "$container" 2>/dev/null || echo "Failed to start $container"
    fi
done

echo "=== Maintenance Complete ==="
