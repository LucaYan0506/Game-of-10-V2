#!/bin/bash

echo "Setting up Redis for Django Channels..."

# Check if Redis is installed
if command -v redis-server &> /dev/null; then
    echo "Redis is already installed."
else
    echo "Installing Redis..."

    # Check the operating system
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install redis
        else
            echo "Homebrew not found. Please install Redis manually:"
            echo "Visit: https://redis.io/download"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install redis-server
        elif command -v yum &> /dev/null; then
            sudo yum install redis
        else
            echo "Package manager not found. Please install Redis manually:"
            echo "Visit: https://redis.io/download"
            exit 1
        fi
    else
        echo "Unsupported operating system. Please install Redis manually:"
        echo "Visit: https://redis.io/download"
        exit 1
    fi
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install channels_redis redis

# Start Redis server
echo "Starting Redis server..."
redis-server --daemonize yes

# Test Redis connection
echo "Testing Redis connection..."
redis-cli ping

echo "Redis setup complete! You can now run bot_vs_bot.py with real-time updates."