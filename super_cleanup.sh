#!/bin/bash
echo "🔥 SCORCHED EARTH PROTOCOL INITIATED 🔥"

echo "1. Stopping all containers..."
docker-compose down --remove-orphans

echo "2. Nuking all project containers..."
docker rm -f $(docker ps -aq) 2>/dev/null

echo "3. Nuking all project images (Forces Full Rebuild)..."
# Try to delete images associated with the project
docker rmi -f $(docker images -q) 2>/dev/null

echo "4. Pruning everything else..."
docker system prune -f

echo "5. REBUILDING FROM ASHES..."
docker-compose up -d --build

echo "✅ Phoenix has risen."
