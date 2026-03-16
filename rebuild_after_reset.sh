#!/bin/bash
# Rebuild script after Docker reset

echo "🏗️ Rebuilding your Vatican monitoring system..."

# Build all containers
echo "📦 Building containers..."
docker-compose build

# Start all services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to start..."
sleep 30

# Apply database migrations
echo "🗄️ Setting up database..."
docker-compose exec backend python backend/manage.py migrate

# Create admin user (optional)
echo "👤 Creating admin user..."
docker-compose exec backend python backend/create_admin.py

# Test the system
echo "🧪 Testing system..."
python test_telegram_groups.py

echo "✅ System rebuilt successfully!"
echo "🎉 Your multi-tenant Telegram bot is ready!"