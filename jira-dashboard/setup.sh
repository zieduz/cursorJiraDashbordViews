#!/bin/bash

# Jira Performance Dashboard Setup Script
echo "🚀 Setting up Jira Performance Dashboard..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your Jira credentials before running the application."
fi

# Build and start the application
echo "🏗️  Building and starting the application..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check if services are running
echo "🔍 Checking service status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Access the application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Documentation: http://localhost:8000/docs"
    echo ""
    echo "📊 The application includes:"
    echo "   - Mock data with 90 days of history"
    echo "   - 3 projects and 5 users"
    echo "   - Comprehensive metrics and forecasting"
    echo ""
    echo "🛠️  To stop the application:"
    echo "   docker-compose down"
    echo ""
    echo "🔄 To view logs:"
    echo "   docker-compose logs -f"
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi