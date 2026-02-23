#!/bin/bash
echo "Starting Deployment..."

# Navigate to project directory (Assuming standard location, adjust if needed)
# Since I cannot verify the remote path, I'll assume usage in current dir
# cd /root/travelagentbot/v2_enterprise || echo "Directory not found, running in current..."

echo "Pulling latest changes..."
# git pull origin main 
# NOTE: User might not have git set up or pushed.
# This script is intended to be run AFTER files are updated.

echo "Rebuilding containers..."
docker-compose down
docker-compose up --build -d

echo "Running migrations..."
docker-compose exec -T backend python manage.py migrate

echo "Restarting Scheduler..."
docker-compose restart beat

echo "Deployment Complete. Checking logs..."
docker-compose logs --tail=20 beat backend
