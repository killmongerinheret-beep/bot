#!/bin/bash
echo "Stopper Docker containers..."
docker rm -f $(docker ps -aq)
echo "Containers removed. Starting thorough build..."
docker-compose up -d --build
echo "Done!"
