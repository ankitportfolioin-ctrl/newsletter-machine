#!/bin/bash

# Database Setup Script for Newsletter Machine
# This script sets up a local PostgreSQL database for development

set -e

echo "=== Newsletter Machine Database Setup ==="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    echo "Please install Docker Desktop or Docker Engine"
    echo "Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose is not installed or not in PATH"
    echo "Please install docker-compose"
    exit 1
fi

echo "✓ Docker and docker-compose are available"
echo ""

# Start PostgreSQL container
echo "Starting PostgreSQL container..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Check if PostgreSQL is running
if ! docker-compose ps | grep -q "newsletter_db.*Up"; then
    echo "ERROR: PostgreSQL container failed to start"
    docker-compose logs postgres
    exit 1
fi

echo "✓ PostgreSQL is running"
echo ""

# Test database connection
echo "Testing database connection..."
if ! docker exec newsletter_db pg_isready -U newsletter_user -d newsletter_machine > /dev/null 2>&1; then
    echo "ERROR: Cannot connect to PostgreSQL"
    docker-compose logs postgres
    exit 1
fi

echo "✓ Database connection successful"
echo ""

echo "=== Database Setup Complete ==="
echo ""
echo "Database Details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: newsletter_machine"
echo "  User: newsletter_user"
echo "  Password: newsletter_password"
echo ""
echo "Connection String:"
echo "  postgresql://newsletter_user:newsletter_password@localhost:5432/newsletter_machine"
echo ""
echo "Next steps:"
echo "  1. Start the backend: cd server && npm run dev"
echo "  2. Start the frontend: npm run dev"
echo "  3. Open http://localhost:5173 in your browser"
echo ""
