#!/bin/bash

# Start network with 5 screen sessions using TCP sockets for communication
# Usage: ./start_network.sh <consensus_type> <scenario_type> <seed>

CONSENSUS_TYPE=${1:-pow}
SCENARIO_TYPE=${2:-delays}
SEED=${3:-42}

# Cleanup previous sessions
./scripts/utils/cleanup.sh

echo "Starting 5 node network with TCP socket communication:"
echo "Consensus: $CONSENSUS_TYPE"
echo "Scenario: $SCENARIO_TYPE"
echo "Seed: $SEED"
echo "Ports: 9000-9004 (node0-node4)"

# Start 5 screen sessions for 5 nodes using socket communication
screen -dmS "node0" bash -c "python main.py --node-id 0 --consensus $CONSENSUS_TYPE --scenario $SCENARIO_TYPE --seed $SEED"

screen -dmS "node1" bash -c "python main.py --node-id 1 --consensus $CONSENSUS_TYPE --scenario $SCENARIO_TYPE --seed $SEED"

screen -dmS "node2" bash -c "python main.py --node-id 2 --consensus $CONSENSUS_TYPE --scenario $SCENARIO_TYPE --seed $SEED"

screen -dmS "node3" bash -c "python main.py --node-id 3 --consensus $CONSENSUS_TYPE --scenario $SCENARIO_TYPE --seed $SEED"

screen -dmS "node4" bash -c "python main.py --node-id 4 --consensus $CONSENSUS_TYPE --scenario $SCENARIO_TYPE --seed $SEED"

echo "Started 5 socket-based node screen sessions for $CONSENSUS_TYPE consensus with $SCENARIO_TYPE scenario"
echo "Use 'screen -list' to see running sessions"
echo "Use 'screen -r node0' to attach to node 0 (or node1, node2, node3, node4)"
echo "Press Ctrl+A then D to detach from a screen session"
echo "Check logs/ directory for detailed logs from each node"
echo ""
echo "Network topology:"
echo "  Node 0: localhost:9000"
echo "  Node 1: localhost:9001" 
echo "  Node 2: localhost:9002"
echo "  Node 3: localhost:9003"
echo "  Node 4: localhost:9004"
