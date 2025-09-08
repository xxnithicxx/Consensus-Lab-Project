#!/bin/bash

# Setup terminals for blockchain simulation
# This script prepares the terminal environment

echo "Setting up terminal environment for blockchain simulation..."

# Check if screen is available
if ! command -v screen &> /dev/null; then
    echo "Error: screen not found. Please install it: sudo apt-get install screen"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Clear any existing logs
rm -f logs/*.log

echo "Terminal environment setup complete."
echo "Ready to run blockchain simulation scripts."
echo "Note: Using screen for session management."
echo "Use 'screen -list' to see active sessions."
