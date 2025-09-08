#!/bin/bash

# Cleanup script for blockchain simulation
# Stops running processes and cleans up temporary files

echo "Cleaning up blockchain simulation..."

# Kill any running Python processes related to the simulation
pkill -f "python main.py"
pkill -f "python main_single.py"
pkill -f "python main_socket.py"

# Kill blockchain simulation screen sessions (all variants)
screen -S node0 -X quit 2>/dev/null
screen -S node1 -X quit 2>/dev/null
screen -S node2 -X quit 2>/dev/null
screen -S node3 -X quit 2>/dev/null
screen -S node4 -X quit 2>/dev/null
screen -S blockchain_sim -X quit 2>/dev/null
screen -S socket_node0 -X quit 2>/dev/null
screen -S socket_node1 -X quit 2>/dev/null
screen -S socket_node2 -X quit 2>/dev/null
screen -S socket_node3 -X quit 2>/dev/null
screen -S socket_node4 -X quit 2>/dev/null

# Clean up log files (optional)
rm -f logs/*.log

# Clean up any temporary files
rm -f *.tmp
rm -f *.pid

echo "Cleanup complete."
