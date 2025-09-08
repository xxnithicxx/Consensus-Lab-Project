#!/bin/bash

# Screen session manager for blockchain simulation
# Usage: ./screen_manager.sh <action> [node_id]

ACTION=${1:-list}
NODE_ID=${2:-}

case $ACTION in
    list)
        echo "Active blockchain node sessions:"
        screen -list | grep node
        ;;
    
    attach)
        if [ -z "$NODE_ID" ]; then
            echo "Usage: ./screen_manager.sh attach <node_id>"
            echo "Available nodes: node0, node1, node2, node3, node4"
            exit 1
        fi
        echo "Attaching to $NODE_ID session..."
        echo "Press Ctrl+A then D to detach"
        screen -r "$NODE_ID"
        ;;
    
    kill)
        if [ -z "$NODE_ID" ]; then
            echo "Killing all blockchain node sessions..."
            screen -S node0 -X quit 2>/dev/null
            screen -S node1 -X quit 2>/dev/null
            screen -S node2 -X quit 2>/dev/null
            screen -S node3 -X quit 2>/dev/null
            screen -S node4 -X quit 2>/dev/null
            echo "All sessions terminated."
        else
            echo "Killing $NODE_ID session..."
            screen -S "$NODE_ID" -X quit
            echo "$NODE_ID session terminated."
        fi
        ;;
    
    status)
        echo "Blockchain simulation status:"
        echo "Screen sessions:"
        screen -list | grep node | wc -l | xargs echo "  Active sessions:"
        echo "Python processes:"
        pgrep -f "python main.py" | wc -l | xargs echo "  Running processes:"
        ;;
    
    help)
        echo "Screen Manager for Blockchain Simulation"
        echo ""
        echo "Usage: ./screen_manager.sh <action> [node_id]"
        echo ""
        echo "Actions:"
        echo "  list          - List all active node sessions"
        echo "  attach <node> - Attach to a specific node session (node0-node4)"
        echo "  kill [node]   - Kill specific node or all sessions"
        echo "  status        - Show simulation status"
        echo "  help          - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./screen_manager.sh list"
        echo "  ./screen_manager.sh attach node0"
        echo "  ./screen_manager.sh kill node2"
        echo "  ./screen_manager.sh kill"
        ;;
    
    *)
        echo "Unknown action: $ACTION"
        echo "Use './screen_manager.sh help' for available actions"
        exit 1
        ;;
esac
